"""Evaluation metrics package.

Each metric implements the :class:`llmops.evaluation.metrics.base.Metric` protocol:
    * :class:`~llmops.evaluation.metrics.ragas.GroundednessMetric`,
      :class:`~llmops.evaluation.metrics.ragas.AnswerRelevanceMetric` — RAG quality (Ragas).
    * :class:`~llmops.evaluation.metrics.deepeval.WritingQualityMetric` — G-Eval (DeepEval).
    * :class:`~llmops.evaluation.metrics.tool_selection.ToolSelectionMetric` — custom,
      trace-driven; the flagship agentic evaluator.
    * :class:`~llmops.evaluation.metrics.judge.JudgeMetric` — LLM-as-judge on the ``judge``
      alias.

The heavy metrics import optional third-party / sibling packages lazily and are re-exported
here defensively so that importing this package never fails in an offline dev environment.
"""

from __future__ import annotations

from llmops.evaluation.metrics.base import EvalTrace, Metric, MetricScore, SpanRecord
from llmops.evaluation.metrics.tool_selection import (
    ToolSelectionMetric,
    aggregate_tool_selection,
)

__all__ = [
    "Metric",
    "MetricScore",
    "SpanRecord",
    "EvalTrace",
    "ToolSelectionMetric",
    "aggregate_tool_selection",
    "GroundednessMetric",
    "AnswerRelevanceMetric",
    "WritingQualityMetric",
    "JudgeMetric",
    "default_metrics",
]


def default_metrics() -> list[Metric]:
    """Return the default metric suite, tolerating absent optional dependencies.

    Metrics whose backing library is missing are still included — they self-report an
    ``error`` at score time, which the gate treats per policy — so the suite is stable
    across environments. Import failures for a metric module are skipped entirely.

    Returns:
        A list of instantiated metrics implementing :class:`Metric`.
    """
    metrics: list[Metric] = [ToolSelectionMetric()]
    try:
        from llmops.evaluation.metrics.ragas import (
            AnswerRelevanceMetric,
            GroundednessMetric,
        )

        metrics.extend([GroundednessMetric(), AnswerRelevanceMetric()])
    except Exception:  # noqa: BLE001
        pass
    try:
        from llmops.evaluation.metrics.deepeval import WritingQualityMetric

        metrics.append(WritingQualityMetric())
    except Exception:  # noqa: BLE001
        pass
    try:
        from llmops.evaluation.metrics.judge import JudgeMetric

        metrics.append(JudgeMetric())
    except Exception:  # noqa: BLE001
        pass
    return metrics


def __getattr__(name: str) -> object:  # noqa: D401 - lazy re-export
    """Lazily import the heavy metric classes on attribute access."""
    if name in {"GroundednessMetric", "AnswerRelevanceMetric"}:
        from llmops.evaluation.metrics import ragas

        return getattr(ragas, name)
    if name == "WritingQualityMetric":
        from llmops.evaluation.metrics.deepeval import WritingQualityMetric

        return WritingQualityMetric
    if name == "JudgeMetric":
        from llmops.evaluation.metrics.judge import JudgeMetric

        return JudgeMetric
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
