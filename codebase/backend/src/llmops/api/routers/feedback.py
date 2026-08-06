"""Feedback router — capture a FeedbackEvent and read recent feedback."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from llmops.api.deps import FeedbackServiceDep
from llmops.common.logging import get_logger
from llmops.feedback.models import FeedbackEvent

_log = get_logger(__name__)
router = APIRouter(prefix="/feedback")


@router.post("", status_code=201, summary="Capture a FeedbackEvent")
async def capture_feedback(event: FeedbackEvent, service: FeedbackServiceDep) -> dict[str, Any]:
    """Persist a feedback event and report whether it yields a golden candidate.

    Edits/overrides carry a human-supplied correct signal and are surfaced as
    golden-dataset candidates for review (the improvement loop).
    """
    stored = await service.capture(event)
    candidate = service.to_golden_candidate(stored)
    return {
        "id": stored.id,
        "trace_id": stored.trace_id,
        "golden_candidate_id": candidate.id if candidate else None,
    }


@router.get("", summary="Recent feedback events")
async def list_feedback(
    service: FeedbackServiceDep,
    usecase: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Return recent feedback events (from the durable store; in-memory in dev)."""
    items = await service.list_recent(usecase=usecase, limit=limit)
    return {"items": [e.model_dump(mode="json") for e in items], "count": len(items)}
