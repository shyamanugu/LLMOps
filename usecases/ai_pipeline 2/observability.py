"""LLMOps observability integration (Phase 1 — thin adapter).

Emits one platform ``StepEvent`` per LLM call and one ``PipelineEvent`` per run
using the AFNI LLMOps Observability service (platform component 05), plus per
-call cost via ``observability.cost.compute_cost``.

Design:
* **Non-invasive.** Per-run and per-step attribution flow through ``contextvars``
  so step logic doesn't need new function parameters. ``services.query`` reads
  this module; steps set their step context in one line at entry.
* **Fail-open.** If the platform packages aren't importable, every entry point
  here becomes a no-op and the pipeline runs unchanged — mirroring the
  platform's own ``NullTracer``/``PassthroughGuardrail`` philosophy.
* **Tracer choice via env** ``AI_PIPELINE_TRACER`` = ``memory`` (default) |
  ``null`` | ``azure`` (Azure Monitor; needs ``APPLICATIONINSIGHTS_CONNECTION_STRING``
  and ``opencensus-ext-azure``).
"""
from __future__ import annotations

import contextvars
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from ai_pipeline import _platform_bootstrap  # noqa: F401  (side effect: sys.path)
from ai_pipeline.logging_config import get_logger

logger = get_logger("observability")

_DEFAULT_TRACE_FILE = Path(__file__).resolve().parent / "traces" / "trace.jsonl"

# ── Platform import (fail-open) ──────────────────────────────────────────────
try:
    from observability.tracer import InMemoryTracer, NullTracer
    from observability.types import PipelineEvent, StepEvent
    from observability.cost import compute_cost

    _PLATFORM = True
except Exception as exc:  # pragma: no cover - exercised only when platform absent
    logger.warning("LLMOps platform observability unavailable (%s) — tracing disabled", exc)
    _PLATFORM = False

# ── Per-run / per-step context ───────────────────────────────────────────────
class _JsonlTracer:
    """A zero-Azure tracer that keeps events in memory (for the RUN SUMMARY) AND
    appends each as a JSON line to a file. This is how observability is captured
    when Azure Monitor can't be deployed — the JSONL feeds the demo UI exporter."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.step_events: list = []
        self.pipeline_events: list = []
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def _append(self, kind: str, event) -> None:
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"kind": kind, **asdict(event)}) + "\n")
        except Exception as exc:  # never break a run on a trace write
            logger.debug("trace write failed: %s", exc)

    def record_step(self, event) -> None:
        self.step_events.append(event)
        self._append("step", event)

    def record_pipeline(self, event) -> None:
        self.pipeline_events.append(event)
        self._append("pipeline", event)


_run_id: contextvars.ContextVar[str] = contextvars.ContextVar("llmops_run_id", default="")
_program: contextvars.ContextVar[str] = contextvars.ContextVar("llmops_program", default="")
_environment: contextvars.ContextVar[str] = contextvars.ContextVar("llmops_env", default="dev")
_step_name: contextvars.ContextVar[str] = contextvars.ContextVar("llmops_step", default="")
_model_alias: contextvars.ContextVar[str] = contextvars.ContextVar("llmops_alias", default="")

_TRACER: Optional[Any] = None


def current_environment() -> str:
    """The pipeline environment (dev|test|prod), from ``AI_PIPELINE_ENV``."""
    return os.environ.get("AI_PIPELINE_ENV", "dev").strip() or "dev"


def init_tracer(environment: Optional[str] = None) -> Any:
    """Create the process-wide tracer once. Safe to call if platform is absent."""
    global _TRACER
    if not _PLATFORM:
        _TRACER = None
        return None
    if _TRACER is not None:
        return _TRACER

    choice = os.environ.get("AI_PIPELINE_TRACER", "memory").strip().lower()
    if choice == "null":
        _TRACER = NullTracer()
    elif choice == "jsonl":
        trace_file = os.environ.get("AI_PIPELINE_TRACE_FILE", "").strip() or str(_DEFAULT_TRACE_FILE)
        _TRACER = _JsonlTracer(trace_file)
        logger.info("Observability: JSONL tracer active -> %s", trace_file)
    elif choice == "azure":
        try:
            from observability.azure_monitor_tracer import AzureMonitorTracer

            _TRACER = AzureMonitorTracer()
            logger.info("Observability: AzureMonitorTracer active")
        except Exception as exc:
            logger.warning("Azure tracer unavailable (%s) — falling back to InMemoryTracer", exc)
            _TRACER = InMemoryTracer()
    else:
        _TRACER = InMemoryTracer()
    return _TRACER


def get_tracer() -> Any:
    return _TRACER


def set_run_context(run_id: str, program: str, environment: str) -> None:
    _run_id.set(run_id or "")
    _program.set(program or "")
    _environment.set(environment or "dev")


def set_step_context(step_name: str, model_alias: str = "") -> None:
    """Attribute subsequent LLM calls (and the tasks they spawn) to a step.

    Call once at the top of a step's ``run_*`` function. Concurrent per-row
    tasks created afterwards inherit this context automatically.
    """
    _step_name.set(step_name or "")
    _model_alias.set(model_alias or "")


def record_llm_call(
    *,
    deployment: str,
    result: Optional[dict],
    latency_ms: float,
    error: Optional[str] = None,
    guardrail_allowed: bool = True,
    guardrail_reason: str = "",
) -> float:
    """Emit a ``StepEvent`` for one LLM call. Returns the computed cost (USD).

    ``result`` is the dict returned by ``services.query`` (may be ``None`` when
    the call raised). Token fields are read defensively.
    """
    if not _PLATFORM or _TRACER is None:
        return 0.0

    result = result or {}
    input_tokens = int(result.get("prompt_tokens", 0) or 0)
    output_tokens = int(result.get("completion_tokens", 0) or 0)
    status = result.get("status")

    try:
        cost = compute_cost(deployment, input_tokens, output_tokens)
    except Exception:
        cost = 0.0

    event = StepEvent(
        session_id=_run_id.get(),
        step_name=_step_name.get() or "unknown",
        model_alias=_model_alias.get() or None,
        provider=None,
        deployment=deployment,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
        guardrail_allowed=guardrail_allowed,
        guardrail_reason=guardrail_reason,
        error=error or (None if status == "ok" else _status_error(status, result)),
    )
    try:
        _TRACER.record_step(event)
    except Exception as exc:  # never let tracing break the pipeline
        logger.debug("record_step failed: %s", exc)
    return cost


def _status_error(status: Any, result: dict) -> Optional[str]:
    """Map a non-ok query status into the event's error field for visibility."""
    if status in (None, "ok"):
        return None
    msg = result.get("message")
    return f"{status}: {msg}" if msg else str(status)


def record_pipeline(step_count: int, total_latency_ms: float, error: Optional[str] = None) -> None:
    if not _PLATFORM or _TRACER is None:
        return
    try:
        _TRACER.record_pipeline(
            PipelineEvent(
                session_id=_run_id.get(),
                pipeline_name=f"ai_pipeline:{_program.get() or 'unknown'}",
                step_count=step_count,
                total_latency_ms=total_latency_ms,
                error=error,
            )
        )
    except Exception as exc:
        logger.debug("record_pipeline failed: %s", exc)


def run_totals() -> Optional[dict]:
    """When using ``InMemoryTracer``, summarise the run for the RUN SUMMARY log.

    Returns None for tracers that don't retain events (Null/Azure)."""
    if not _PLATFORM or _TRACER is None:
        return None
    events = getattr(_TRACER, "step_events", None)
    if not events:
        return None
    return {
        "llm_calls": len(events),
        "input_tokens": sum(e.input_tokens for e in events),
        "output_tokens": sum(e.output_tokens for e in events),
        "cost_usd": round(sum(e.cost_usd for e in events), 6),
        "errors": sum(1 for e in events if e.error),
    }
