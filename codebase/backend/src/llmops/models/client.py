"""Async Azure OpenAI client wrapper.

:class:`ModelClient` is the single entry point for calling a model. It:

* resolves a task alias to a deployment via :class:`~llmops.models.router.ModelRouter`;
* authenticates to Azure OpenAI with **Managed Identity** (``DefaultAzureCredential`` token
  provider), falling back to an API key only in dev;
* emits a ``model_call`` span (GenAI semantic conventions) and attaches token usage + cost;
* retries transient failures with exponential backoff via ``tenacity``;
* returns a typed :class:`~llmops.common.types.ChatResult` (text, usage, cost, latency).

When no Azure endpoint is configured (local dev), it returns a deterministic **mock**
response so the whole platform is runnable offline. The one line that builds the live SDK
client is marked ``# TODO(wiring)``.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from llmops.common.errors import UpstreamError
from llmops.common.logging import get_logger
from llmops.common.types import ChatResult, Usage
from llmops.config.models_config import ModelsConfig, load_models_config
from llmops.config.settings import Settings, get_settings
from llmops.models.pricing import cost_usd
from llmops.models.router import ModelRouter
from llmops.observability.cost import attach_cost
from llmops.observability.tracing import model_call_span, set_model_usage

logger = get_logger(__name__)

# Retry support degrades gracefully if tenacity is unavailable in a minimal dev env.
try:  # pragma: no cover - import path depends on environment
    from tenacity import (
        AsyncRetrying,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )

    _TENACITY_AVAILABLE = True
except Exception:  # noqa: BLE001
    _TENACITY_AVAILABLE = False

_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
_MAX_ATTEMPTS = 3


class ModelClient:
    """Async wrapper over Azure OpenAI with tracing, costing, and retries.

    Args:
        settings: Platform settings; the singleton is used when omitted.
        router: A pre-built router; one is constructed from ``models.yaml`` when omitted.
    """

    def __init__(self, settings: Settings | None = None, router: ModelRouter | None = None) -> None:
        self._settings = settings or get_settings()
        self._router = router or self._build_router()
        self._client: Any | None = None  # lazily constructed live SDK client
        self._mock = not bool(self._settings.azure_openai_endpoint)
        if self._mock:
            logger.warning("azure openai endpoint not set; ModelClient runs in dev mock mode")

    # -- construction helpers -------------------------------------------------------

    def _build_router(self) -> ModelRouter:
        """Load ``models.yaml`` and build a router for the configured environment."""
        config: ModelsConfig = load_models_config(self._settings.models_config_path)
        return ModelRouter(config, self._settings.environment)

    def _ensure_client(self) -> Any:
        """Return the live ``AsyncAzureOpenAI`` client, constructing it on first use.

        Raises:
            UpstreamError: If the Azure OpenAI SDK / credentials cannot be initialised.
        """
        if self._client is not None:
            return self._client
        try:
            from openai import AsyncAzureOpenAI

            if self._settings.azure_openai_api_key:
                # Dev convenience only; production uses Managed Identity.
                # TODO(wiring): remove key auth in non-dev environments.
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=self._settings.azure_openai_endpoint,
                    api_version=self._settings.azure_openai_api_version,
                    api_key=self._settings.azure_openai_api_key,
                )
            else:
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider

                # TODO(wiring): construct DefaultAzureCredential with the Container App's
                # user-assigned Managed Identity client id in Azure.
                token_provider = get_bearer_token_provider(DefaultAzureCredential(), _TOKEN_SCOPE)
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=self._settings.azure_openai_endpoint,
                    api_version=self._settings.azure_openai_api_version,
                    azure_ad_token_provider=token_provider,
                )
        except Exception as exc:  # noqa: BLE001 - surface as a platform error
            raise UpstreamError(
                "failed to initialise Azure OpenAI client",
                detail={"endpoint": self._settings.azure_openai_endpoint},
            ) from exc
        return self._client

    # -- public API -----------------------------------------------------------------

    async def chat(
        self,
        *,
        alias: str,
        messages: list[dict[str, Any]],
        prompt_id: str | None = None,
        temperature: float = 0.2,
    ) -> ChatResult:
        """Run a chat completion for a task ``alias`` and return a typed result.

        Args:
            alias: The task alias to resolve to a deployment (e.g. ``"reason"``).
            messages: OpenAI-style chat messages (``[{"role", "content"}, ...]``).
            prompt_id: Optional prompt identifier, recorded on the span for lineage.
            temperature: Sampling temperature.

        Returns:
            A :class:`ChatResult` with text, usage, cost, and latency populated.

        Raises:
            UnknownAliasError: If the alias is not defined for the environment.
            UpstreamError: If the Azure OpenAI call fails after retries.
        """
        deployment = self._router.resolve(alias)
        started = perf_counter()

        with model_call_span(alias, deployment, prompt_id=prompt_id) as span:
            if self._mock:
                text, usage, finish_reason = self._mock_response(messages)
            else:
                text, usage, finish_reason = await self._call_live(deployment, messages, temperature)

            latency_ms = int((perf_counter() - started) * 1000)
            cost = cost_usd(deployment, usage)

            set_model_usage(
                span,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                finish_reason=finish_reason,
                latency_ms=latency_ms,
            )
            attach_cost(span, cost)

        logger.info(
            "chat completed",
            alias=alias,
            deployment=deployment,
            prompt_id=prompt_id,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            mock=self._mock,
        )
        return ChatResult(
            text=text,
            model=deployment,
            usage=usage,
            cost_usd=cost,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
        )

    # -- live call + retry ----------------------------------------------------------

    async def _call_live(
        self, deployment: str, messages: list[dict[str, Any]], temperature: float
    ) -> tuple[str, Usage, str | None]:
        """Invoke Azure OpenAI with retries and normalise the response."""
        client = self._ensure_client()

        async def _once() -> tuple[str, Usage, str | None]:
            response = await client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=temperature,
            )
            choice = response.choices[0]
            usage = Usage(
                input_tokens=getattr(response.usage, "prompt_tokens", 0) if response.usage else 0,
                output_tokens=getattr(response.usage, "completion_tokens", 0) if response.usage else 0,
            )
            return (choice.message.content or "", usage, choice.finish_reason)

        try:
            if _TENACITY_AVAILABLE:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(_MAX_ATTEMPTS),
                    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
                    retry=retry_if_exception_type(self._retryable_types()),
                    reraise=True,
                ):
                    with attempt:
                        return await _once()
                raise RuntimeError("unreachable: AsyncRetrying exhausted without reraise")
            return await _once()
        except Exception as exc:  # noqa: BLE001 - wrap as a stable upstream error
            raise UpstreamError(
                "Azure OpenAI chat completion failed after retries",
                detail={"deployment": deployment, "error": str(exc)},
            ) from exc

    @staticmethod
    def _retryable_types() -> tuple[type[BaseException], ...]:
        """Return the exception types worth retrying (transient upstream failures)."""
        types: list[type[BaseException]] = [TimeoutError, ConnectionError]
        try:
            from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

            types.extend([APIConnectionError, APITimeoutError, InternalServerError, RateLimitError])
        except Exception:  # noqa: BLE001 - openai not installed in this env
            pass
        return tuple(types)

    # -- dev mock -------------------------------------------------------------------

    @staticmethod
    def _mock_response(messages: list[dict[str, Any]]) -> tuple[str, Usage, str | None]:
        """Produce a deterministic offline response for local development.

        The token counts are rough word-based estimates so cost math stays exercised even
        without a live model.
        """
        last_user = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        prompt_words = sum(len(str(m.get("content", "")).split()) for m in messages)
        text = f"[dev-mock] Acknowledged: {str(last_user)[:200]}"
        usage = Usage(input_tokens=max(1, prompt_words), output_tokens=max(1, len(text.split())))
        return text, usage, "stop"
