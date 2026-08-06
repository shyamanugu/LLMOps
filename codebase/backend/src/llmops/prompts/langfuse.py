"""Langfuse-backed prompt registry adapter.

Langfuse offers hosted prompt management with labels, versions, and analytics. This adapter
maps our :class:`PromptSpec` onto Langfuse's prompt objects. The *structure* is real; the
single line that constructs the live Langfuse client is marked with ``# TODO(wiring)`` and
the adapter degrades gracefully to a no-op (dev) when credentials are absent.
"""

from __future__ import annotations

from typing import Any

from llmops.common.errors import PromptNotFoundError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.prompts.schema import PromptSpec

logger = get_logger(__name__)


class LangfusePromptRegistry:
    """Serve prompts from a Langfuse project.

    Args:
        settings: Platform settings carrying the Langfuse host and keys.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Any | None = self._build_client()

    def _build_client(self) -> Any | None:
        """Construct the Langfuse client, or ``None`` in dev when unconfigured."""
        if not (self._settings.langfuse_host and self._settings.langfuse_secret_key):
            logger.info("langfuse not configured; registry runs in dev no-op mode")
            return None
        # TODO(wiring): construct Langfuse client from settings / managed identity, e.g.
        #   from langfuse import Langfuse
        #   return Langfuse(host=self._settings.langfuse_host,
        #                   public_key=self._settings.langfuse_public_key,
        #                   secret_key=self._settings.langfuse_secret_key)
        logger.warning("langfuse client wiring not implemented; running in no-op mode")
        return None

    # -- conversion helpers ---------------------------------------------------------

    @staticmethod
    def _to_spec(prompt: Any) -> PromptSpec:
        """Translate a Langfuse prompt object into a :class:`PromptSpec`.

        The Langfuse ``config`` dict is expected to carry our platform metadata
        (``model_alias``, ``inputs``, ``eval_refs``); the ``prompt`` field is the template.
        """
        config: dict[str, Any] = getattr(prompt, "config", {}) or {}
        return PromptSpec(
            id=prompt.name,
            version=int(getattr(prompt, "version", 1)),
            labels=list(getattr(prompt, "labels", []) or []),
            model_alias=config.get("model_alias", "reason"),
            temperature=float(config.get("temperature", 0.2)),
            inputs=list(config.get("inputs", [])),
            template=getattr(prompt, "prompt", ""),
            eval_refs=list(config.get("eval_refs", [])),
            changelog=list(config.get("changelog", [])),
        )

    @staticmethod
    def _to_langfuse_payload(spec: PromptSpec) -> dict[str, Any]:
        """Translate a :class:`PromptSpec` into Langfuse ``create_prompt`` kwargs."""
        return {
            "name": spec.id,
            "prompt": spec.template,
            "labels": spec.labels,
            "config": {
                "model_alias": spec.model_alias,
                "temperature": spec.temperature,
                "inputs": spec.inputs,
                "eval_refs": spec.eval_refs,
                "changelog": spec.changelog,
            },
        }

    # -- registry interface ---------------------------------------------------------

    def get(self, prompt_id: str, label: str = "prod") -> PromptSpec:
        """Return the prompt version carrying ``label`` from Langfuse.

        Raises:
            PromptNotFoundError: Always in dev no-op mode, or when Langfuse has no such
                prompt/label.
        """
        if self._client is None:
            raise PromptNotFoundError(
                "langfuse registry is in dev no-op mode; use the git registry locally",
                detail={"prompt_id": prompt_id, "label": label},
            )
        # TODO(wiring): prompt = self._client.get_prompt(prompt_id, label=label)
        raise PromptNotFoundError(
            "langfuse get_prompt wiring not implemented",
            detail={"prompt_id": prompt_id, "label": label},
        )

    def list(self) -> list[PromptSpec]:
        """Return all prompts from Langfuse (empty in dev no-op mode)."""
        if self._client is None:
            return []
        # TODO(wiring): page through self._client prompt listing and map via _to_spec.
        return []

    def push(self, spec: PromptSpec) -> None:
        """Upsert ``spec`` into Langfuse as a new prompt version."""
        payload = self._to_langfuse_payload(spec)
        if self._client is None:
            logger.info("langfuse push skipped (dev no-op)", prompt_id=spec.id)
            return
        # TODO(wiring): self._client.create_prompt(**payload)
        logger.warning("langfuse push wiring not implemented", prompt_id=spec.id, keys=list(payload))
