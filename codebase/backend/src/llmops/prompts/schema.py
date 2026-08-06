"""The :class:`PromptSpec` model — the typed mirror of a ``*.prompt.yaml`` file.

Design principles applied: config-as-code (prompts live in versioned YAML), fail-safe
defaults (rendering refuses to emit a partially-filled template), separation of concerns
(the spec knows how to render itself but nothing about where it is stored).
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from llmops.common.errors import PromptRenderError

# Matches ``{{ var }}`` with arbitrary surrounding whitespace and captures the name.
_PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


class PromptSpec(BaseModel):
    """A single versioned prompt, mirroring its ``.prompt.yaml`` representation.

    Attributes:
        id: Stable, dotted prompt identifier (e.g. ``"apix.triage.system"``).
        version: Monotonic integer version; higher is newer.
        labels: Deployment labels attached to this version (e.g. ``["prod", "latest"]``).
        model_alias: Task alias the prompt targets (resolved via the model router).
        temperature: Default sampling temperature for calls using this prompt.
        inputs: Names of the template variables that MUST be supplied at render time.
        template: The prompt body containing ``{{ var }}`` placeholders.
        eval_refs: Identifiers of golden datasets / evaluators guarding this prompt.
        changelog: Human-readable notes, newest last.
    """

    id: str
    version: int = Field(ge=1)
    labels: list[str] = Field(default_factory=list)
    model_alias: str
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    inputs: list[str] = Field(default_factory=list)
    template: str
    eval_refs: list[str] = Field(default_factory=list)
    changelog: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_not_blank(cls, value: str) -> str:
        """Reject empty ids early so registries never key on ``""``."""
        if not value or not value.strip():
            raise ValueError("prompt id must be a non-empty string")
        return value

    def declared_placeholders(self) -> set[str]:
        """Return the set of ``{{ var }}`` names actually present in the template."""
        return set(_PLACEHOLDER_RE.findall(self.template))

    def render(self, **variables: Any) -> str:
        """Render the template, substituting every declared input.

        All names listed in :attr:`inputs` must be provided; extra variables are ignored.
        The method fails closed: if any declared input is missing, or if the template
        still contains an unresolved placeholder after substitution, it raises rather than
        emitting a half-filled prompt to a model.

        Args:
            **variables: Values for the template placeholders, keyed by name.

        Returns:
            The fully-rendered prompt string.

        Raises:
            PromptRenderError: If a required input is missing or a placeholder is left
                unresolved.
        """
        missing = [name for name in self.inputs if name not in variables]
        if missing:
            raise PromptRenderError(
                f"missing required inputs for prompt '{self.id}': {missing}",
                detail={"prompt_id": self.id, "missing": missing, "required": self.inputs},
            )

        def _replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in variables:
                # A placeholder in the body that was never declared as an input.
                raise PromptRenderError(
                    f"template of prompt '{self.id}' references undeclared variable '{name}'",
                    detail={"prompt_id": self.id, "variable": name, "declared": self.inputs},
                )
            return str(variables[name])

        return _PLACEHOLDER_RE.sub(_replace, self.template)
