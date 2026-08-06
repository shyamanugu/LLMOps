"""Feedback service — capture events and promote high-signal ones to golden candidates.

This is the application-facing entry point used by the ``/feedback`` API. It validates and
persists feedback via :class:`~llmops.feedback.store.FeedbackStore`, and converts qualifying
feedback (edits and overrides — where a human supplied the *correct* answer/decision) into
:class:`~llmops.evaluation.golden.GoldenCase` candidates that can be reviewed and merged into
a use-case's golden dataset. That is the concrete "feedback -> evaluation" improvement loop
from the deck.
"""

from __future__ import annotations

from typing import Any

from llmops.common.logging import get_logger
from llmops.evaluation.golden import GoldenCase
from llmops.feedback.models import FeedbackEvent, FeedbackKind
from llmops.feedback.store import FeedbackStore

_log = get_logger(__name__)


class FeedbackService:
    """Captures feedback and derives golden-dataset candidates from it."""

    def __init__(self, store: FeedbackStore | None = None) -> None:
        """Initialise the service.

        Args:
            store: The persistence store. A default :class:`FeedbackStore` is created when
                omitted (in-memory in dev).
        """
        self._store = store or FeedbackStore()

    async def capture(self, event: FeedbackEvent) -> FeedbackEvent:
        """Validate and persist a feedback event.

        Args:
            event: The event to capture (already a validated pydantic model).

        Returns:
            The stored event (with server-assigned id/timestamp).
        """
        await self._store.save(event)
        return event

    async def list_recent(self, *, usecase: str | None = None, limit: int = 100) -> list[FeedbackEvent]:
        """Return recent feedback events (delegates to the store)."""
        return await self._store.list_recent(usecase=usecase, limit=limit)

    def to_golden_candidate(self, event: FeedbackEvent) -> GoldenCase | None:
        """Convert a feedback event into a golden-case candidate, when applicable.

        Only ``edit`` and ``override`` events carry a human-supplied *correct* signal, so
        only those yield candidates. ``thumbs`` events inform metrics/dashboards but do not
        become goldens on their own.

        Args:
            event: The feedback event.

        Returns:
            A :class:`GoldenCase` marked ``meta.source = "feedback"`` and
            ``meta.status = "candidate"`` (pending human review before it enters a suite),
            or ``None`` if the event is not promotable.
        """
        if event.kind is FeedbackKind.THUMBS:
            return None

        meta: dict[str, Any] = {
            "source": "feedback",
            "status": "candidate",
            "feedback_id": event.id,
            "trace_id": event.trace_id,
        }
        grading: dict[str, Any] = {}
        original_input = event.metadata.get("input", {})

        if event.kind is FeedbackKind.EDIT:
            # The human-corrected answer becomes the reference the case must match.
            grading["reference"] = event.value
            if event.reason:
                grading["rubric"] = event.reason
        elif event.kind is FeedbackKind.OVERRIDE:
            # A human overrode an agent decision — capture the corrected tool/decision.
            grading["expected_tool"] = event.value
            if event.reason:
                meta["override_reason"] = event.reason

        candidate = GoldenCase(
            id=f"cand-{event.id}",
            input=original_input if isinstance(original_input, dict) else {"value": original_input},
            grading=grading,
            meta=meta,
        )
        _log.info(
            "derived golden candidate from feedback",
            feedback_id=event.id,
            kind=event.kind.value,
            candidate_id=candidate.id,
        )
        return candidate
