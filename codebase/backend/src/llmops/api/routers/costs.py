"""Costs router — cost aggregates by use-case / day / model."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter

from llmops.api.deps import SettingsDep
from llmops.common.logging import get_logger

_log = get_logger(__name__)
router = APIRouter(prefix="/costs")

GroupBy = Literal["usecase", "day", "model"]


@router.get("", summary="Cost aggregates by usecase/day/model")
async def get_costs(
    settings: SettingsDep,
    group_by: GroupBy = "day",
    usecase: str | None = None,
) -> dict[str, Any]:
    """Return aggregated LLM spend.

    Costs are attached to model-call spans (``app.cost_usd``) by
    :mod:`llmops.observability.cost` and aggregated from App Insights. Until that query is
    wired this returns a labelled placeholder with a stable shape for the console charts.
    """
    # TODO(wiring): aggregate app.cost_usd from App Insights custom metrics grouped by
    # the requested dimension; return series suitable for the /costs page charts.
    configured = bool(settings.applicationinsights_connection_string)
    return {
        "source": "placeholder",
        "backend_configured": configured,
        "group_by": group_by,
        "usecase": usecase,
        "currency": "USD",
        "series": [],
        "total_usd": 0.0,
    }
