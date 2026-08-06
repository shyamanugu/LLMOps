"""Convenience loader used across the platform to fetch a prompt by id/label.

Call sites (agents, evaluation, the API) use :func:`load_prompt` rather than constructing a
registry themselves, so the configured backend is honoured everywhere.
"""

from __future__ import annotations

from llmops.config.settings import get_settings
from llmops.prompts.factory import build_registry
from llmops.prompts.schema import PromptSpec


def load_prompt(prompt_id: str, label: str = "prod") -> PromptSpec:
    """Load a prompt spec from the configured registry.

    Args:
        prompt_id: The stable prompt identifier.
        label: The deployment label to resolve (default ``"prod"``).

    Returns:
        The resolved :class:`PromptSpec`.

    Raises:
        PromptNotFoundError: If the id/label cannot be resolved.
    """
    registry = build_registry(get_settings())
    return registry.get(prompt_id, label=label)
