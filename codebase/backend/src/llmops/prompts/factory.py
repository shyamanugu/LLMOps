"""Registry factory — pick a prompt backend from configuration.

The concrete backend is selected once, at the edge, from ``settings.prompt_registry``. This
is the composition root for prompts: everything downstream depends only on the
:class:`PromptRegistry` Protocol.
"""

from __future__ import annotations

from llmops.common.errors import ConfigError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.prompts.base import PromptRegistry
from llmops.prompts.foundry import FoundryPromptRegistry
from llmops.prompts.git import GitPromptRegistry
from llmops.prompts.langfuse import LangfusePromptRegistry

logger = get_logger(__name__)

_BACKENDS = {"git", "langfuse", "foundry"}


def build_registry(settings: Settings | None = None) -> PromptRegistry:
    """Build the prompt registry named by ``settings.prompt_registry``.

    Args:
        settings: Platform settings; the process singleton is used when omitted.

    Returns:
        A concrete registry implementing :class:`PromptRegistry`.

    Raises:
        ConfigError: If ``prompt_registry`` is not one of ``git|langfuse|foundry``.
    """
    settings = settings or get_settings()
    kind = settings.prompt_registry.strip().lower()
    if kind not in _BACKENDS:
        raise ConfigError(
            f"unknown prompt_registry '{settings.prompt_registry}'",
            detail={"value": settings.prompt_registry, "supported": sorted(_BACKENDS)},
        )

    logger.info("building prompt registry", backend=kind)
    if kind == "git":
        return GitPromptRegistry(settings=settings)
    if kind == "langfuse":
        return LangfusePromptRegistry(settings=settings)
    return FoundryPromptRegistry(settings=settings)
