"""RAG quality metrics (groundedness / answer-relevance) backed by Ragas.

Wraps the `Ragas <https://docs.ragas.io>`_ library to score two things that matter for
retrieval-augmented answers:

    * **groundedness / faithfulness** — is every claim in the answer supported by the
      retrieved context? (the primary anti-hallucination gate; floor is high, e.g. 0.9)
    * **answer relevance** — does the answer actually address the question?

Ragas itself calls an LLM + embeddings under the hood. Those live clients are wired from
settings; when Ragas (or its model wiring) is unavailable — the common case in unit tests
and offline dev — the metric degrades gracefully by returning a :class:`MetricScore` with
an ``error`` set, so the gate can decide policy (skip vs. fail) without crashing.
"""

from __future__ import annotations

from typing import Any

from llmops.common.logging import get_logger
from llmops.evaluation.metrics.base import EvalTrace, MetricScore

_log = get_logger(__name__)

# --- Guarded optional import ------------------------------------------------
try:  # pragma: no cover - exercised only when the extra is installed
    from ragas import evaluate as _ragas_evaluate  # type: ignore[import-not-found]
    from ragas.metrics import (  # type: ignore[import-not-found]
        answer_relevancy as _answer_relevancy,
    )
    from ragas.metrics import (
        faithfulness as _faithfulness,
    )

    _RAGAS_AVAILABLE = True
except Exception:  # noqa: BLE001 - any import/setup failure disables the metric
    _ragas_evaluate = None  # type: ignore[assignment]
    _answer_relevancy = None  # type: ignore[assignment]
    _faithfulness = None  # type: ignore[assignment]
    _RAGAS_AVAILABLE = False


class _RagasMetricBase:
    """Shared machinery for the Ragas-backed metrics."""

    #: The Ragas metric object this evaluator maps onto.
    _ragas_metric: Any = None
    #: Key used in the Ragas result frame.
    _result_key: str = ""

    async def _run(self, case: Any, output: str, trace: EvalTrace) -> MetricScore:
        if not _RAGAS_AVAILABLE:
            return MetricScore(
                metric=self.name,  # type: ignore[attr-defined]
                error="ragas not installed; run `pip install llmops-platform[eval]`",
            )

        grading = getattr(case, "grading", {}) or {}
        question = grading.get("question") or getattr(case, "input", {}).get("question", "")
        # Prefer ground-truth contexts; fall back to what the trace actually retrieved.
        contexts = grading.get("contexts") or trace.contexts()
        reference = grading.get("reference")

        sample: dict[str, Any] = {
            "question": [str(question)],
            "answer": [output],
            "contexts": [[str(c) for c in contexts]],
        }
        if reference is not None:
            sample["ground_truth"] = [str(reference)]

        try:
            # TODO(wiring): pass an llm=/embeddings= built from Settings + Managed Identity
            # (AzureChatOpenAI on the 'judge' deployment, AzureOpenAIEmbeddings on 'embed').
            result = _ragas_evaluate(  # type: ignore[misc]
                dataset=_to_ragas_dataset(sample),
                metrics=[self._ragas_metric],
            )
            value = _extract_scalar(result, self._result_key)
        except Exception as exc:  # noqa: BLE001 - upstream/model failure must not crash CI
            _log.warning("ragas evaluation failed", metric=self.name, error=str(exc))  # type: ignore[attr-defined]
            return MetricScore(metric=self.name, error=f"ragas error: {exc}")  # type: ignore[attr-defined]

        return MetricScore(
            metric=self.name,  # type: ignore[attr-defined]
            value=float(value),
            detail={"contexts_used": len(contexts), "has_reference": reference is not None},
        )


class GroundednessMetric(_RagasMetricBase):
    """Faithfulness of the answer to the retrieved context (anti-hallucination)."""

    name = "groundedness"
    _ragas_metric = _faithfulness
    _result_key = "faithfulness"

    async def score(self, case: Any, output: str, trace: EvalTrace) -> MetricScore:
        """Score groundedness for one case (see :meth:`_RagasMetricBase._run`)."""
        return await self._run(case, output, trace)


class AnswerRelevanceMetric(_RagasMetricBase):
    """Whether the answer addresses the user's question."""

    name = "answer_relevance"
    _ragas_metric = _answer_relevancy
    _result_key = "answer_relevancy"

    async def score(self, case: Any, output: str, trace: EvalTrace) -> MetricScore:
        """Score answer relevance for one case (see :meth:`_RagasMetricBase._run`)."""
        return await self._run(case, output, trace)


def _to_ragas_dataset(sample: dict[str, Any]) -> Any:
    """Build the dataset object Ragas expects from a single-sample dict.

    Kept isolated so the import only happens when Ragas is present.
    """
    from datasets import Dataset  # type: ignore[import-not-found]

    return Dataset.from_dict(sample)


def _extract_scalar(result: Any, key: str) -> float:
    """Pull a single float score out of a Ragas result object defensively."""
    try:
        as_dict = result if isinstance(result, dict) else result.to_pandas().mean(numeric_only=True).to_dict()
        return float(as_dict.get(key, 0.0))
    except Exception:  # noqa: BLE001
        return 0.0
