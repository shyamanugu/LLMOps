"""Guardrails router — configured guards and recent guardrail events."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from llmops.api.deps import GuardrailEngineDep
from llmops.common.logging import get_logger

_log = get_logger(__name__)
router = APIRouter(prefix="/guardrails")


@router.get("", summary="Configured guardrails + last events")
async def list_guardrails(engine: GuardrailEngineDep) -> dict[str, Any]:
    """Return the ordered guardrail configuration and recent block/redaction events.

    The configured guard list comes from the guardrail engine; recent *events* live in
    App Insights, so that portion is a labelled placeholder until the query is wired.
    """
    guards: list[dict[str, Any]] = []
    if engine is not None:
        for guard in getattr(engine, "guards", []):
            guards.append(
                {
                    "name": getattr(guard, "name", type(guard).__name__),
                    "kind": type(guard).__name__,
                }
            )
    # TODO(wiring): read recent guardrail events (blocks/redactions) from App Insights.
    return {
        "guards": guards,
        "guards_source": "engine" if engine is not None else "placeholder",
        "events": {"source": "placeholder", "items": []},
    }
