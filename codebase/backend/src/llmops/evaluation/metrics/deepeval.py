"""Writing-quality metric via DeepEval's G-Eval.

`DeepEval <https://docs.confident-ai.com>`_ provides *G-Eval* — an LLM-graded, rubric-based
metric with chain-of-thought scoring. We use it to grade the *writing quality* of generated
answers (clarity, coherence, tone, completeness) on a normalised ``0..1`` scale — the kind
of judgement that has no reference string and that regex/BLEU cannot capture.

The DeepEval import is guarded: when the optional ``eval`` extra is not installed, or when
the underlying model client cannot be constructed, the metric degrades to a
:class:`MetricScore` carrying an ``error`` instead of raising.
"""

from __future__ import annotations

from typing import Any

from llmops.common.logging import get_logger
from llmops.evaluation.metrics.base import EvalTrace, MetricScore

_log = get_logger(__name__)

# --- Guarded optional import ------------------------------------------------
try:  # pragma: no cover - exercised only when the extra is installed
    from deepeval.metrics import GEval  # type: ignore[import-not-found]
    from deepeval.test_case import (  # type: ignore[import-not-found]
        LLMTestCase,
        LLMTestCaseParams,
    )

    _DEEPEVAL_AVAILABLE = True
except Exception:  # noqa: BLE001
    GEval = None  # type: ignore[assignment,misc]
    LLMTestCase = None  # type: ignore[assignment,misc]
    LLMTestCaseParams = None  # type: ignore[assignment,misc]
    _DEEPEVAL_AVAILABLE = False


#: The rubric criteria G-Eval reasons over. Kept declarative so it is reviewable as config.
_WRITING_RUBRIC = (
    "Evaluate the writing quality of the answer for an enterprise support context. Reward "
    "answers that are clear, well-structured, grammatically correct, appropriately concise, "
    "and professional in tone. Penalise rambling, contradictions, hedging, and unresolved "
    "placeholders."
)


class WritingQualityMetric:
    """Grades writing quality with DeepEval G-Eval (LLM-graded, rubric-based).

    Implements the :class:`llmops.evaluation.metrics.base.Metric` protocol.
    """

    name = "writing_quality"

    def __init__(self, *, model_alias: str = "judge", threshold: float = 0.7) -> None:
        """Initialise the metric.

        Args:
            model_alias: The task alias used for the grading model (defaults to ``judge``).
            threshold: DeepEval's internal pass threshold; the platform gate applies its
                own thresholds on top, so this is advisory.
        """
        self._model_alias = model_alias
        self._threshold = threshold

    async def score(self, case: Any, output: str, trace: EvalTrace) -> MetricScore:
        """Score writing quality for one case.

        Args:
            case: The golden case (its ``input`` provides the original prompt/question).
            output: The generated answer under evaluation.
            trace: The collected trace (unused; kept for protocol symmetry).

        Returns:
            A :class:`MetricScore` with ``value`` in ``0..1``; ``error`` set if DeepEval is
            unavailable or the grading model call fails.
        """
        if not _DEEPEVAL_AVAILABLE:
            return MetricScore(
                metric=self.name,
                error="deepeval not installed; run `pip install llmops-platform[eval]`",
            )

        question = getattr(case, "input", {}).get("question", "")
        try:
            # TODO(wiring): construct a DeepEval model adapter backed by ModelClient on the
            # 'judge' alias (Azure OpenAI via Managed Identity) and pass model=... below.
            metric = GEval(
                name="WritingQuality",
                criteria=_WRITING_RUBRIC,
                evaluation_params=[
                    LLMTestCaseParams.INPUT,
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                ],
                threshold=self._threshold,
            )
            test_case = LLMTestCase(input=str(question), actual_output=output)
            metric.measure(test_case)
            value = float(getattr(metric, "score", 0.0) or 0.0)
            reason = getattr(metric, "reason", None)
        except Exception as exc:  # noqa: BLE001 - grading failure must not crash CI
            _log.warning("deepeval G-Eval failed", metric=self.name, error=str(exc))
            return MetricScore(metric=self.name, error=f"deepeval error: {exc}")

        return MetricScore(
            metric=self.name,
            value=value,
            passed=value >= self._threshold,
            detail={"reason": reason, "model_alias": self._model_alias},
        )
