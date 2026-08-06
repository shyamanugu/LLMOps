"""Cost attribution and aggregation.

Every model call attaches its USD cost to the active span as ``app.cost_usd``. Because cost
rides on the trace, the same data powers the ``/costs`` API, the console's cost dashboard,
and per-use-case budget alerts — one source of truth, no separate metering pipeline.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Iterable

from pydantic import BaseModel, Field

from llmops.observability.tracing import APP_COST_USD

if TYPE_CHECKING:  # pragma: no cover - typing only
    from opentelemetry.trace import Span


def attach_cost(current: "Span", cost_usd: float) -> None:
    """Attach ``app.cost_usd`` to an open span.

    Args:
        current: The active model span.
        cost_usd: The computed cost in USD.
    """
    setter = getattr(current, "set_attribute", None)
    if setter is not None:
        setter(APP_COST_USD, float(cost_usd))


class CostRecord(BaseModel):
    """A single billable event, flattened for aggregation.

    Attributes:
        usecase: Owning use case (e.g. ``"apix"``); ``"_platform"`` if unattributed.
        model: Resolved Azure deployment name.
        day: ISO date (``YYYY-MM-DD``) the cost was incurred.
        cost_usd: Cost in USD.
        requests: Number of calls represented (defaults to 1).
    """

    usecase: str = "_platform"
    model: str = "unknown"
    day: str = ""
    cost_usd: float = 0.0
    requests: int = 1


class CostBucket(BaseModel):
    """An aggregated cost total for a grouping key."""

    key: str
    cost_usd: float = Field(default=0.0)
    requests: int = 0


def aggregate_costs(records: Iterable[CostRecord], by: str = "usecase") -> list[CostBucket]:
    """Aggregate cost records by one of ``usecase``, ``model``, or ``day``.

    Args:
        records: The cost records to fold.
        by: The grouping dimension.

    Returns:
        Buckets sorted by descending cost.

    Raises:
        ValueError: If ``by`` is not a supported dimension.
    """
    if by not in {"usecase", "model", "day"}:
        raise ValueError(f"unsupported aggregation dimension: {by!r}")

    totals: dict[str, list[float | int]] = defaultdict(lambda: [0.0, 0])
    for record in records:
        key = getattr(record, by)
        totals[key][0] = float(totals[key][0]) + record.cost_usd
        totals[key][1] = int(totals[key][1]) + record.requests

    buckets = [
        CostBucket(key=key, cost_usd=round(float(cost), 6), requests=int(reqs))
        for key, (cost, reqs) in totals.items()
    ]
    buckets.sort(key=lambda b: b.cost_usd, reverse=True)
    return buckets


def total_cost(records: Iterable[CostRecord]) -> float:
    """Return the summed USD cost across ``records`` (rounded to 6 dp)."""
    return round(sum(r.cost_usd for r in records), 6)


def cost_record_from_result(result: Any, *, usecase: str = "_platform", day: str = "") -> CostRecord:
    """Build a :class:`CostRecord` from a :class:`~llmops.common.types.ChatResult`.

    Args:
        result: A ChatResult-like object exposing ``model`` and ``cost_usd``.
        usecase: The owning use case for attribution.
        day: ISO date string of the event.

    Returns:
        A populated cost record.
    """
    return CostRecord(
        usecase=usecase,
        model=getattr(result, "model", "unknown"),
        day=day,
        cost_usd=float(getattr(result, "cost_usd", 0.0)),
        requests=1,
    )
