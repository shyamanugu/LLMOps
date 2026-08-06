"""Azure AI Foundry prompt registry adapter.

Azure AI Foundry (formerly Azure AI Studio) can host prompt assets alongside model
deployments and evaluations. This adapter presents Foundry prompts through the common
:class:`PromptRegistry` interface. The live client construction is marked with
``# TODO(wiring)`` and the adapter degrades gracefully to a no-op in dev.
"""

from __future__ import annotations

from typing import Any

from llmops.common.errors import PromptNotFoundError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.prompts.schema import PromptSpec

logger = get_logger(__name__)


class FoundryPromptRegistry:
    """Serve prompts from an Azure AI Foundry project.

    Args:
        settings: Platform settings (Foundry uses the Azure OpenAI / project endpoint and
            Managed Identity).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Any | None = self._build_client()

    def _build_client(self) -> Any | None:
        """Construct the Foundry project client, or ``None`` in dev when unconfigured."""
        if not self._settings.azure_openai_endpoint:
            logger.info("azure foundry endpoint not configured; registry runs in dev no-op mode")
            return None
        # TODO(wiring): construct the Foundry/AI Projects client from settings via
        #   DefaultAzureCredential, e.g.
        #   from azure.ai.projects import AIProjectClient
        #   from azure.identity import DefaultAzureCredential
        #   return AIProjectClient(endpoint=self._settings.azure_openai_endpoint,
        #                          credential=DefaultAzureCredential())
        logger.warning("azure foundry client wiring not implemented; running in no-op mode")
        return None

    @staticmethod
    def _to_spec(asset: Any) -> PromptSpec:
        """Translate a Foundry prompt asset into a :class:`PromptSpec`."""
        meta: dict[str, Any] = getattr(asset, "metadata", {}) or {}
        return PromptSpec(
            id=asset.name,
            version=int(getattr(asset, "version", 1)),
            labels=list(meta.get("labels", [])),
            model_alias=meta.get("model_alias", "reason"),
            temperature=float(meta.get("temperature", 0.2)),
            inputs=list(meta.get("inputs", [])),
            template=getattr(asset, "template", ""),
            eval_refs=list(meta.get("eval_refs", [])),
            changelog=list(meta.get("changelog", [])),
        )

    def get(self, prompt_id: str, label: str = "prod") -> PromptSpec:
        """Return the labelled prompt version from Foundry.

        Raises:
            PromptNotFoundError: In dev no-op mode, or when the asset/label is absent.
        """
        if self._client is None:
            raise PromptNotFoundError(
                "foundry registry is in dev no-op mode; use the git registry locally",
                detail={"prompt_id": prompt_id, "label": label},
            )
        # TODO(wiring): resolve the asset by name+label through the Foundry client.
        raise PromptNotFoundError(
            "foundry get wiring not implemented",
            detail={"prompt_id": prompt_id, "label": label},
        )

    def list(self) -> list[PromptSpec]:
        """Return all prompt assets from Foundry (empty in dev no-op mode)."""
        if self._client is None:
            return []
        # TODO(wiring): enumerate prompt assets in the Foundry project and map via _to_spec.
        return []

    def push(self, spec: PromptSpec) -> None:
        """Upsert ``spec`` into the Foundry project as a new asset version."""
        if self._client is None:
            logger.info("foundry push skipped (dev no-op)", prompt_id=spec.id)
            return
        # TODO(wiring): create/update the Foundry prompt asset from ``spec``.
        logger.warning("foundry push wiring not implemented", prompt_id=spec.id)
