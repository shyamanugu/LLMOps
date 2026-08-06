"""Guardrail primitives: the :class:`GuardResult` value object and :class:`Guard` protocol.

Guards are the atomic safety checks that the :class:`~llmops.guardrails.engine.GuardrailEngine`
composes into an ordered pipeline. Each guard inspects a piece of text (a user input or a
model output) and returns a :class:`GuardResult` describing whether the text is allowed and,
optionally, a redacted rewrite (e.g. PII scrubbing).

Design principles applied:
    * **Dependency inversion** — the engine depends on the :class:`Guard` protocol, not on any
      concrete Azure / Presidio adapter.
    * **Fail-safe defaults** — adapters degrade to *allow* in dev when no live client is wired,
      never silently to *deny* (which would break local development) nor to a false *allow* in
      production (production requires wiring; see the ``# TODO(wiring)`` markers in each adapter).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class GuardResult(BaseModel):
    """Outcome of a single guard check.

    Attributes:
        allowed: ``True`` when the text may proceed; ``False`` when it must be blocked.
        category: Machine-readable reason category (e.g. ``"hate"``, ``"pii"``, ``"jailbreak"``)
            or ``None`` when allowed with no findings.
        detail: Human-readable explanation safe for structured logging (never contains secrets).
        redacted_text: A sanitised rewrite of the input when the guard performs redaction
            (e.g. PII masking). ``None`` when no rewrite was applied.
    """

    allowed: bool = True
    category: str | None = None
    detail: str | None = None
    redacted_text: str | None = None
    scores: dict[str, float] = Field(default_factory=dict)

    @classmethod
    def allow(cls, *, redacted_text: str | None = None, detail: str | None = None) -> GuardResult:
        """Return an allowing result, optionally carrying a redacted rewrite."""
        return cls(allowed=True, redacted_text=redacted_text, detail=detail)

    @classmethod
    def block(cls, category: str, detail: str, *, scores: dict[str, float] | None = None) -> GuardResult:
        """Return a blocking result tagged with ``category`` and an explanation."""
        return cls(allowed=False, category=category, detail=detail, scores=scores or {})


@runtime_checkable
class Guard(Protocol):
    """Protocol implemented by every guardrail adapter.

    A guard is directional: it may treat inbound user text (``check_input``) differently from
    outbound model text (``check_output``). Implementations must be idempotent and side-effect
    free so the engine can run them in any composition and retry safely.
    """

    #: Short, stable identifier used in logs, spans, and the ``/guardrails`` API.
    name: str

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Check inbound user text before it reaches the model.

        Args:
            text: The user-supplied text (possibly already redacted by an earlier guard).
            ctx: Free-form request context (trace id, use-case, locale, ...).

        Returns:
            A :class:`GuardResult`.
        """
        ...

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Check outbound model text before it reaches the user.

        Args:
            text: The model-generated text (possibly already redacted by an earlier guard).
            ctx: Free-form request context.

        Returns:
            A :class:`GuardResult`.
        """
        ...
