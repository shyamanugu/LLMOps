"""Evaluations router — recent gate reports and triggering a gate run."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

from llmops.common.ids import new_id
from llmops.common.logging import get_logger
from llmops.evaluation.gate import EvaluationGate

_log = get_logger(__name__)
router = APIRouter(prefix="/evaluations")


class RunGateRequest(BaseModel):
    """Body for triggering a gate run."""

    usecase: str
    scope: Literal["full", "changed", "smoke"] = "changed"


class RunGateAccepted(BaseModel):
    """Ack for an asynchronously-started gate run."""

    task_id: str = Field(default_factory=lambda: new_id("task_"))
    usecase: str
    scope: str
    status: str = "accepted"


async def _run_gate_task(usecase: str, scope: Literal["full", "changed", "smoke"]) -> None:
    """Background task that runs the gate and logs its report."""
    try:
        report = await EvaluationGate().run(usecase, scope)
        _log.info("background gate run finished", usecase=usecase, scope=scope, passed=report.passed)
        # TODO(wiring): persist GateReport to store (Cosmos/App Insights) for GET /evaluations.
    except Exception as exc:  # noqa: BLE001
        _log.error("background gate run failed", usecase=usecase, error=str(exc))


@router.get("", summary="Recent gate reports")
async def list_evaluations(usecase: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Return recent evaluation gate reports.

    Reports are produced in CI and by ``POST /evaluations/run``; durable history requires
    the eval-history store, so this returns a labelled placeholder until that is wired.
    """
    # TODO(wiring): read recent GateReports from the eval-history store (Cosmos/App Insights).
    return {"source": "placeholder", "usecase": usecase, "limit": limit, "items": []}


@router.post("/run", status_code=202, response_model=RunGateAccepted, summary="Run gate (async)")
async def run_evaluation(request: RunGateRequest, background: BackgroundTasks) -> RunGateAccepted:
    """Kick off a gate run for a use-case as a background task.

    Returns immediately with a task id; the run executes asynchronously so the request does
    not block on a full evaluation sweep.
    """
    ack = RunGateAccepted(usecase=request.usecase, scope=request.scope)
    background.add_task(_run_gate_task, request.usecase, request.scope)
    _log.info("evaluation run accepted", task_id=ack.task_id, usecase=request.usecase, scope=request.scope)
    return ack
