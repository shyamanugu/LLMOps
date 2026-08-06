"""Metric protocol and the shared evaluation value types.

Every evaluator in :mod:`llmops.evaluation.metrics` implements the :class:`Metric`
protocol: it exposes a stable ``name`` and an async ``score`` coroutine that grades a
single golden case against the pipeline ``output`` and the collected ``trace``.

Design principles applied:
    * Separation of concerns — metrics are pure scorers; thresholds/gating live elsewhere.
    * Dependency inversion — the runner depends on this Protocol, not concrete metrics.
    * Fail-safe defaults — a metric that cannot run returns a :class:`MetricScore` with an
      ``error`` set rather than raising, so one flaky metric never crashes the gate.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Trace view consumed by metrics
# ---------------------------------------------------------------------------


class SpanRecord(BaseModel):
    """A single span extracted from a pipeline run.

    Mirrors the OpenTelemetry GenAI spans emitted by ``llmops.observability.tracing``
    (``request`` > ``agent`` > ``model``/``tool``) but flattened into a plain, serialisable
    record so metrics can inspect a run without an OTel dependency.

    Attributes:
        name: Span name (e.g. ``"tool:search_knowledge"``).
        kind: One of ``request | agent | model | tool | internal``.
        attributes: Span attributes (GenAI semantic-convention keys where applicable).
        status: ``ok`` or ``error``.
        duration_ms: Wall-clock duration of the span in milliseconds.
    """

    name: str
    kind: str = "internal"
    attributes: dict[str, Any] = Field(default_factory=dict)
    status: str = "ok"
    duration_ms: int = 0


class EvalTrace(BaseModel):
    """The trace collected for a single golden-case run.

    Attributes:
        trace_id: UUID4 hex id of the run.
        output_text: Final natural-language output of the pipeline.
        spans: Flattened span list for the run.
        raw: Opaque original result object kept for debugging (never serialised to CI).
    """

    trace_id: str = ""
    output_text: str = ""
    spans: list[SpanRecord] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    def tool_spans(self) -> list[SpanRecord]:
        """Return spans that represent tool invocations, in call order."""
        return [s for s in self.spans if s.kind == "tool"]

    def model_spans(self) -> list[SpanRecord]:
        """Return spans that represent model calls, in call order."""
        return [s for s in self.spans if s.kind == "model"]

    def contexts(self) -> list[str]:
        """Return retrieved RAG contexts recorded on tool spans (best effort)."""
        contexts: list[str] = []
        for span in self.tool_spans():
            chunks = span.attributes.get("rag.contexts") or span.attributes.get("contexts")
            if isinstance(chunks, list):
                contexts.extend(str(c) for c in chunks)
        return contexts


class MetricScore(BaseModel):
    """The normalised result of scoring one case with one metric.

    Attributes:
        metric: The metric name (matches :attr:`Metric.name`).
        value: Primary score, normalised to ``0.0..1.0`` where higher is better. For
            count-style metrics (e.g. ``pii_leak``) the raw count is in ``detail`` and
            ``value`` carries the count so absolute floors can be applied directly.
        passed: Optional per-metric pass flag if the metric self-asserts; the gate uses
            :mod:`llmops.evaluation.thresholds` for the authoritative decision.
        detail: Structured, log-safe breakdown (sub-scores, counts, offending items).
        error: Set when the metric could not be computed (missing dep, upstream failure).
    """

    metric: str
    value: float = 0.0
    passed: bool | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        """True when the metric produced a value (no computation error)."""
        return self.error is None


@runtime_checkable
class Metric(Protocol):
    """Protocol every evaluator implements.

    Implementations must be side-effect free and safe to run concurrently.
    """

    #: Stable, unique metric name used as the key in gate reports and thresholds.
    name: str

    async def score(self, case: Any, output: str, trace: EvalTrace) -> MetricScore:
        """Score a single case.

        Args:
            case: The :class:`~llmops.evaluation.golden.GoldenCase` being graded.
            output: The pipeline's final natural-language output.
            trace: The collected :class:`EvalTrace` for the run.

        Returns:
            A :class:`MetricScore`; never raises for expected failure modes.
        """
        ...
