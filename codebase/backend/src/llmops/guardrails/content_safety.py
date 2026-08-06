"""Azure AI Content Safety guard — harmful-content categories + Prompt Shields.

This adapter wraps `Azure AI Content Safety`_. It covers the four moderation categories
(Hate, SelfHarm, Sexual, Violence), each scored 0..7 in severity, and — on the input path —
`Prompt Shields`_ for jailbreak / prompt-injection detection.

In dev (no ``content_safety_endpoint`` configured) the guard **degrades to allow** so local
development is never blocked by an absent Azure resource. The live client construction is
marked ``# TODO(wiring)`` and uses Managed Identity in Azure.

.. _Azure AI Content Safety: https://learn.microsoft.com/azure/ai-services/content-safety/
.. _Prompt Shields: https://learn.microsoft.com/azure/ai-services/content-safety/concepts/jailbreak-detection
"""

from __future__ import annotations

from typing import Any, Final

from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.guardrails.base import GuardResult

_logger = get_logger(__name__)

#: The moderation categories reported by Azure AI Content Safety.
CATEGORIES: Final[tuple[str, ...]] = ("Hate", "SelfHarm", "Sexual", "Violence")

#: Default per-category severity block threshold (0=safe .. 7=most severe).
DEFAULT_SEVERITY_THRESHOLD: Final[int] = 4


class ContentSafetyGuard:
    """Block text whose Content Safety severity meets or exceeds a threshold.

    Args:
        settings: Platform settings (endpoint + auth). Defaults to the process singleton.
        severity_threshold: Inclusive severity at which a category triggers a block.
        check_prompt_shields: Whether to run Prompt Shields on the input path.
    """

    name = "azure_content_safety"

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        severity_threshold: int = DEFAULT_SEVERITY_THRESHOLD,
        check_prompt_shields: bool = True,
    ) -> None:
        self._settings = settings or get_settings()
        self._severity_threshold = severity_threshold
        self._check_prompt_shields = check_prompt_shields
        self._client: Any | None = None

    @property
    def _enabled(self) -> bool:
        """Whether a live endpoint is configured (otherwise the dev mock is used)."""
        return bool(self._settings.content_safety_endpoint)

    def _get_client(self) -> Any | None:
        """Lazily construct the Content Safety client, or ``None`` in dev.

        Returns:
            An ``azure.ai.contentsafety.aio.ContentSafetyClient`` when configured, else ``None``.
        """
        if not self._enabled:
            return None
        if self._client is not None:
            return self._client
        # TODO(wiring): construct ContentSafetyClient from settings / managed identity, e.g.
        #   from azure.ai.contentsafety.aio import ContentSafetyClient
        #   from azure.identity.aio import DefaultAzureCredential
        #   self._client = ContentSafetyClient(self._settings.content_safety_endpoint,
        #                                       DefaultAzureCredential())
        raise NotImplementedError(
            "TODO(wiring): construct azure.ai.contentsafety ContentSafetyClient from settings"
        )

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Analyse inbound text for harmful categories and (optionally) jailbreak attempts."""
        if self._check_prompt_shields:
            shield = await self._analyze_prompt_shield(text)
            if not shield.allowed:
                return shield
        return await self._analyze_text(text)

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Analyse outbound model text for harmful categories."""
        return await self._analyze_text(text)

    async def _analyze_text(self, text: str) -> GuardResult:
        """Score ``text`` against the moderation categories and apply the threshold."""
        client = self._get_client()
        if client is None:  # dev mock — fail-safe allow
            _logger.debug("content-safety dev mock: allow", chars=len(text))
            return GuardResult.allow()

        # TODO(wiring): call the live analyze API and map the response, e.g.
        #   from azure.ai.contentsafety.models import AnalyzeTextOptions
        #   resp = await client.analyze_text(AnalyzeTextOptions(text=text))
        #   scores = {c.category: float(c.severity) for c in resp.categories_analysis}
        raise NotImplementedError("TODO(wiring): call ContentSafetyClient.analyze_text")

    async def _analyze_prompt_shield(self, text: str) -> GuardResult:
        """Run Prompt Shields (jailbreak / injection) on inbound text."""
        client = self._get_client()
        if client is None:  # dev mock — fail-safe allow
            return GuardResult.allow()

        # TODO(wiring): call the Prompt Shields API and inspect attackDetected, e.g.
        #   resp = await client.detect_jailbreak(...)  # or shield_prompt on newer SDKs
        raise NotImplementedError("TODO(wiring): call Content Safety Prompt Shields API")

    def _evaluate_scores(self, scores: dict[str, float]) -> GuardResult:
        """Map category severities to an allow/block decision (shared by live + tests)."""
        breaches = {c: s for c, s in scores.items() if s >= self._severity_threshold}
        if breaches:
            worst = max(breaches, key=lambda c: breaches[c])
            return GuardResult.block(
                category=worst.lower(),
                detail=f"content safety severity {breaches[worst]} >= {self._severity_threshold}",
                scores=scores,
            )
        return GuardResult(allowed=True, scores=scores)
