"""Feedback data model (ARCHITECTURE_SPEC §3).

A :class:`FeedbackEvent` captures a human signal about a specific traced interaction —
a thumbs up/down, an edit to the model's answer, or a human override of an agent decision.
These events close the improvement loop: they feed dashboards, and high-signal ones become
golden-dataset candidates (see :mod:`llmops.feedback.service`).

Privacy: we never store raw user identity. The originating user is reduced to an opaque
``user_hash`` upstream; free-text ``reason`` is treated as potentially sensitive and is
subject to the same guardrails/PII handling as any other user content.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from llmops.common.ids import new_id


class FeedbackKind(StrEnum):
    """The kind of feedback signal."""

    THUMBS = "thumbs"
    EDIT = "edit"
    OVERRIDE = "override"


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class FeedbackEvent(BaseModel):
    """A single unit of human feedback tied to a trace.

    Attributes:
        id: Stable feedback id (``fb_...``).
        trace_id: The trace/interaction this feedback refers to.
        kind: ``thumbs`` | ``edit`` | ``override``.
        value: Signal payload. For ``thumbs`` a bool/±1; for ``edit`` the corrected text;
            for ``override`` the chosen alternative (tool, answer, decision).
        reason: Optional free-text rationale from the user or reviewer.
        user_hash: Opaque, non-reversible user identifier (never raw PII).
        usecase: Owning use-case (for routing and analytics), when known.
        span_id: Optional specific span the feedback targets (e.g. a tool call).
        ts: Event timestamp (UTC).
        metadata: Free-form context (surface, prompt_id, model, etc.).
    """

    id: str = Field(default_factory=lambda: new_id("fb_"))
    trace_id: str
    kind: FeedbackKind
    value: Any = None
    reason: str | None = None
    user_hash: str | None = None
    usecase: str | None = None
    span_id: str | None = None
    ts: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_positive(self) -> bool:
        """Best-effort interpretation of a thumbs signal as positive."""
        if self.kind is not FeedbackKind.THUMBS:
            return False
        return self.value in (True, 1, "up", "positive", "+1")
