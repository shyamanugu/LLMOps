"""Traces router — recent traces read-through from App Insights / Langfuse."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from llmops.api.deps import SettingsDep
from llmops.common.logging import get_logger

_log = get_logger(__name__)
router = APIRouter(prefix="/traces")


@router.get("", summary="Recent traces (App Insights/Langfuse read-through)")
async def list_traces(settings: SettingsDep, usecase: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Return recent request/agent traces.

    Traces live in Application Insights (and mirrored in Langfuse). This is a read-through
    endpoint; until the query client is wired it returns a clearly-labelled placeholder so
    the console can render its empty/mock state without crashing.
    """
    # TODO(wiring): query App Insights (dependencies/requests) or Langfuse for recent
    # traces, projecting span trees for the console's SpanTree viewer.
    configured = bool(settings.applicationinsights_connection_string or settings.langfuse_host)
    return {
        "source": "placeholder",
        "backend_configured": configured,
        "usecase": usecase,
        "limit": limit,
        "items": [],
    }


@router.get("/{trace_id}", summary="Single trace with span tree")
async def get_trace(trace_id: str, settings: SettingsDep) -> dict[str, Any]:
    """Return a single trace and its nested spans (``request > agent > model/tool``)."""
    # TODO(wiring): fetch the full span tree for trace_id from App Insights/Langfuse.
    return {"source": "placeholder", "trace_id": trace_id, "spans": []}
