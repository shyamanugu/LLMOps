"""Evaluation runner — execute a pipeline over a golden set and score every case.

For each :class:`~llmops.evaluation.golden.GoldenCase` the runner:

    1. runs the use-case :class:`~llmops.orchestration.pipeline.Pipeline` on ``case.input``,
    2. collects the run's trace (spans + final output) as an
       :class:`~llmops.evaluation.metrics.base.EvalTrace`,
    3. scores it with every configured metric (concurrently),
    4. aggregates per-case scores into corpus-level metric values.

The aggregate values are what :mod:`llmops.evaluation.thresholds` gates on. The runner is
resilient: a failing case or a failing metric is recorded as an error and does not abort
the run. The pipeline and tracing imports are guarded so the module loads (and a dev stub
runs) even before the orchestration package or a live Azure client exists.
"""

from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any, Protocol

from pydantic import BaseModel, Field

from llmops.common.ids import new_trace_id
from llmops.common.logging import get_logger
from llmops.evaluation.golden import GoldenCase
from llmops.evaluation.metrics import default_metrics
from llmops.evaluation.metrics.base import EvalTrace, Metric, MetricScore, SpanRecord
from llmops.evaluation.metrics.tool_selection import aggregate_tool_selection

_log = get_logger(__name__)

# --- Guarded optional imports ----------------------------------------------
try:
    from llmops.orchestration.pipeline import Pipeline  # type: ignore[import-not-found]

    _PIPELINE_AVAILABLE = True
except Exception:  # noqa: BLE001 - orchestration package may not be present yet
    Pipeline = None  # type: ignore[assignment,misc]
    _PIPELINE_AVAILABLE = False


class PipelineLike(Protocol):
    """Minimal structural type the runner needs from a pipeline."""

    name: str

    async def run(self, input: dict[str, Any]) -> Any:  # noqa: A002 - mirrors spec signature
        """Run the pipeline and return a result object."""
        ...


class CaseResult(BaseModel):
    """Outcome of evaluating a single golden case."""

    case_id: str
    trace_id: str
    output: str = ""
    scores: list[MetricScore] = Field(default_factory=list)
    error: str | None = None
    latency_ms: int = 0


class RunResult(BaseModel):
    """Aggregate outcome of an evaluation run over a golden set."""

    usecase: str
    total: int = 0
    errors: int = 0
    aggregate: dict[str, float] = Field(default_factory=dict)
    tool_selection: dict[str, Any] = Field(default_factory=dict)
    cases: list[CaseResult] = Field(default_factory=list)


class _DevEchoPipeline:
    """Deterministic dev/offline stand-in used when orchestration is unavailable.

    It returns the case's expected reference (if any) as output and synthesises a tool span
    from ``grading.expected_tool`` so the wiring can be exercised end-to-end without Azure.
    Clearly a placeholder — real runs inject the use-case Pipeline.
    """

    name = "dev-echo"

    async def run(self, input: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
        """Echo a placeholder result shaped like a real pipeline output."""
        return {"output": input.get("_reference", ""), "spans": input.get("_spans", [])}


def _coerce_spans(raw_spans: Any) -> list[SpanRecord]:
    """Convert arbitrary span-like objects from a pipeline result into SpanRecords."""
    spans: list[SpanRecord] = []
    if not isinstance(raw_spans, (list, tuple)):
        return spans
    for item in raw_spans:
        try:
            if isinstance(item, SpanRecord):
                spans.append(item)
            elif isinstance(item, dict):
                spans.append(SpanRecord.model_validate(item))
            else:  # duck-type an object with attributes
                spans.append(
                    SpanRecord(
                        name=getattr(item, "name", "span"),
                        kind=getattr(item, "kind", "internal"),
                        attributes=dict(getattr(item, "attributes", {}) or {}),
                        status=getattr(item, "status", "ok"),
                        duration_ms=int(getattr(item, "duration_ms", 0) or 0),
                    )
                )
        except Exception:  # noqa: BLE001 - skip malformed spans defensively
            continue
    return spans


def result_to_trace(result: Any, trace_id: str) -> EvalTrace:
    """Adapt a ``PipelineResult`` (or dict) into an :class:`EvalTrace`.

    Attribute access is defensive because the concrete ``PipelineResult`` type is owned by
    the orchestration package and may evolve.

    Args:
        result: The object returned by ``Pipeline.run``.
        trace_id: The trace id assigned to this case run.

    Returns:
        A populated :class:`EvalTrace`.
    """
    if isinstance(result, dict):
        output = str(result.get("output") or result.get("text") or "")
        raw_spans = result.get("spans") or result.get("trace", {})
        if isinstance(raw_spans, dict):
            raw_spans = raw_spans.get("spans", [])
    else:
        output = str(getattr(result, "output", None) or getattr(result, "text", "") or "")
        raw_spans = getattr(result, "spans", None)
        if raw_spans is None:
            trace_obj = getattr(result, "trace", None)
            raw_spans = getattr(trace_obj, "spans", []) if trace_obj is not None else []

    return EvalTrace(trace_id=trace_id, output_text=output, spans=_coerce_spans(raw_spans))


class EvaluationRunner:
    """Runs a pipeline over golden cases and scores them with a metric suite."""

    def __init__(
        self,
        *,
        pipeline: PipelineLike | None = None,
        metrics: list[Metric] | None = None,
        concurrency: int = 4,
    ) -> None:
        """Initialise the runner.

        Args:
            pipeline: The pipeline to evaluate. If ``None``, a dev echo stand-in is used
                (offline mode) and a warning is logged.
            metrics: The metric suite. Defaults to :func:`default_metrics`.
            concurrency: Max cases scored in parallel.
        """
        self._pipeline: PipelineLike = pipeline or _DevEchoPipeline()
        if pipeline is None:
            _log.warning("no pipeline provided; using dev echo stand-in (offline mode)")
        self._metrics = metrics if metrics is not None else default_metrics()
        self._sem = asyncio.Semaphore(max(1, concurrency))

    async def _run_case(self, case: GoldenCase) -> CaseResult:
        """Execute and score a single case, capturing any failure as an error."""
        trace_id = new_trace_id()
        start = time.perf_counter()
        async with self._sem:
            try:
                pipeline_input = dict(case.input)
                # Feed the dev echo stand-in enough context to be useful; ignored by real ones.
                if isinstance(self._pipeline, _DevEchoPipeline):
                    pipeline_input["_reference"] = case.reference or ""
                    if case.expected_tool:
                        pipeline_input["_spans"] = [
                            {"name": f"tool:{case.expected_tool}", "kind": "tool",
                             "attributes": {"tool.name": case.expected_tool}}
                        ]
                result = await self._pipeline.run(pipeline_input)
                trace = result_to_trace(result, trace_id)
            except Exception as exc:  # noqa: BLE001 - one bad case must not abort the run
                latency = int((time.perf_counter() - start) * 1000)
                _log.warning("pipeline run failed for case", case_id=case.id, error=str(exc))
                return CaseResult(
                    case_id=case.id, trace_id=trace_id, error=str(exc), latency_ms=latency
                )

            scores = await self._score_case(case, trace)
            latency = int((time.perf_counter() - start) * 1000)
            return CaseResult(
                case_id=case.id,
                trace_id=trace_id,
                output=trace.output_text,
                scores=scores,
                latency_ms=latency,
            )

    async def _score_case(self, case: GoldenCase, trace: EvalTrace) -> list[MetricScore]:
        """Score one case with every metric concurrently, isolating metric failures."""

        async def _one(metric: Metric) -> MetricScore:
            try:
                return await metric.score(case, trace.output_text, trace)
            except Exception as exc:  # noqa: BLE001 - defensive; metrics should not raise
                _log.warning("metric raised", metric=metric.name, error=str(exc))
                return MetricScore(metric=metric.name, error=str(exc))

        return list(await asyncio.gather(*(_one(m) for m in self._metrics)))

    async def run(self, cases: list[GoldenCase], *, usecase: str) -> RunResult:
        """Run the full evaluation over ``cases``.

        Args:
            cases: The golden cases to evaluate.
            usecase: The use-case name (recorded on the result).

        Returns:
            A :class:`RunResult` with per-case detail and corpus-level aggregate scores.
        """
        _log.info("evaluation run starting", usecase=usecase, cases=len(cases))
        case_results = list(await asyncio.gather(*(self._run_case(c) for c in cases)))
        aggregate, tool_summary = self._aggregate(case_results)
        errors = sum(1 for c in case_results if c.error)
        result = RunResult(
            usecase=usecase,
            total=len(case_results),
            errors=errors,
            aggregate=aggregate,
            tool_selection=tool_summary,
            cases=case_results,
        )
        _log.info(
            "evaluation run complete",
            usecase=usecase,
            total=result.total,
            errors=errors,
            aggregate=aggregate,
        )
        return result

    @staticmethod
    def _aggregate(case_results: list[CaseResult]) -> tuple[dict[str, float], dict[str, Any]]:
        """Aggregate per-case metric scores into mean values, with tool-selection detail."""
        by_metric: dict[str, list[MetricScore]] = {}
        for cr in case_results:
            for score in cr.scores:
                by_metric.setdefault(score.metric, []).append(score)

        aggregate: dict[str, float] = {}
        for metric, scores in by_metric.items():
            usable = [s.value for s in scores if s.ok]
            if usable:
                aggregate[metric] = float(statistics.fmean(usable))

        # Tool selection gets special aggregation (accuracy + per-tool P/R) and a stable
        # gate key so thresholds can reference ``tool_selection_accuracy``.
        tool_summary: dict[str, Any] = {}
        if "tool_selection" in by_metric:
            tool_summary = aggregate_tool_selection(by_metric["tool_selection"])
            aggregate["tool_selection_accuracy"] = float(tool_summary.get("accuracy", 0.0))
        return aggregate, tool_summary
