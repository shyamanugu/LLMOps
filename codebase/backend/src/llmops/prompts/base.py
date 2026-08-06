"""The :class:`PromptRegistry` interface shared by all prompt backends.

This is the dependency-inversion seam: orchestration, evaluation, and the API depend only
on this Protocol, never on a concrete backend. Backends (Git, Langfuse, Foundry) are
selected at the edge by :func:`llmops.prompts.factory.build_registry`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from llmops.prompts.schema import PromptSpec


@runtime_checkable
class PromptRegistry(Protocol):
    """A source of versioned prompts.

    Implementations must be safe to construct in dev without live credentials; where a
    live client is required they degrade gracefully (see the concrete adapters).
    """

    def get(self, prompt_id: str, label: str = "prod") -> PromptSpec:
        """Return the prompt version carrying ``label`` for ``prompt_id``.

        Args:
            prompt_id: The stable prompt identifier.
            label: The deployment label to resolve (e.g. ``"prod"``, ``"latest"``).

        Returns:
            The matching :class:`PromptSpec`.

        Raises:
            PromptNotFoundError: If no version with that id/label exists.
        """
        ...

    def list(self) -> list[PromptSpec]:
        """Return every prompt version known to this registry."""
        ...

    def push(self, spec: PromptSpec) -> None:
        """Publish ``spec`` to the backing store (Git -> registry sync).

        For registries where Git is the source of truth this may write a YAML file; for
        Langfuse/Foundry it upserts the version through their client.
        """
        ...
