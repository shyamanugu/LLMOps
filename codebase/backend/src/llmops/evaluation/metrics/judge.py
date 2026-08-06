"""LLM-as-judge metric using a rubric and the ``judge`` model alias.

A general-purpose evaluator that asks a small, cheap model (the ``judge`` alias in
``platform/models.yaml``) to score an answer against a rubric and — when available — a
gold reference. It returns a normalised ``0..1`` score plus the judge's rationale.

This is the most broadly applicable metric: it covers correctness/helpfulness for cases
that have no retrieval context (so Ragas does not apply) and no pure writing rubric. The
judge is driven through :class:`llmops.models.client.ModelClient`, so it emits its own
tracing span and cost like any other model call. The client import is guarded so the
module loads even before the models package or a live Azure client is present.
"""

from __future__ import annotations

import json
import re
from typing import Any

from llmops.common.logging import get_logger
from llmops.evaluation.metrics.base import EvalTrace, MetricScore

_log = get_logger(__name__)

# --- Guarded optional import of the sibling model client --------------------
try:
    from llmops.models.client import ModelClient  # type: ignore[import-not-found]

    _MODEL_CLIENT_AVAILABLE = True
except Exception:  # noqa: BLE001 - sibling package/runtime client may be absent in dev
    ModelClient = None  # type: ignore[assignment,misc]
    _MODEL_CLIENT_AVAILABLE = False

# Optional: load a versioned rubric prompt from the registry when present.
try:
    from llmops.prompts.loader import load_prompt  # type: ignore[import-not-found]

    _PROMPTS_AVAILABLE = True
except Exception:  # noqa: BLE001
    load_prompt = None  # type: ignore[assignment,misc]
    _PROMPTS_AVAILABLE = False


_DEFAULT_RUBRIC = (
    "You are a strict evaluation judge. Score the ANSWER for correctness and helpfulness "
    "with respect to the QUESTION and, if present, the REFERENCE answer. Use a 0-10 scale "
    "where 10 is fully correct and complete, and 0 is wrong or off-topic. Respond ONLY with "
    'a compact JSON object: {"score": <int 0-10>, "reason": "<one sentence>"}.'
)


class JudgeMetric:
    """LLM-as-judge scorer.

    Implements the :class:`llmops.evaluation.metrics.base.Metric` protocol.
    """

    name = "judge_score"

    def __init__(
        self,
        *,
        client: Any | None = None,
        model_alias: str = "judge",
        rubric_prompt_id: str | None = None,
    ) -> None:
        """Initialise the judge.

        Args:
            client: An optional pre-built :class:`ModelClient`. If omitted, one is
                constructed lazily on first use (and degrades to an error score if the
                models package / Azure client is unavailable).
            model_alias: The task alias for the judge model (defaults to ``judge``).
            rubric_prompt_id: Optional prompt-registry id for a versioned rubric; falls
                back to the built-in rubric when absent.
        """
        self._client = client
        self._model_alias = model_alias
        self._rubric_prompt_id = rubric_prompt_id

    def _ensure_client(self) -> Any | None:
        """Return a usable model client, constructing one if possible."""
        if self._client is not None:
            return self._client
        if not _MODEL_CLIENT_AVAILABLE:
            return None
        try:
            # TODO(wiring): construct ModelClient from get_settings() + Managed Identity.
            self._client = ModelClient()  # type: ignore[call-arg]
        except Exception as exc:  # noqa: BLE001
            _log.warning("could not construct judge ModelClient", error=str(exc))
            self._client = None
        return self._client

    def _rubric(self) -> str:
        """Return the rubric text, preferring a registered prompt when configured."""
        if self._rubric_prompt_id and _PROMPTS_AVAILABLE:
            try:
                spec = load_prompt(self._rubric_prompt_id)  # type: ignore[misc]
                return spec.template
            except Exception as exc:  # noqa: BLE001
                _log.warning("could not load rubric prompt; using default", error=str(exc))
        return _DEFAULT_RUBRIC

    async def score(self, case: Any, output: str, trace: EvalTrace) -> MetricScore:
        """Score an answer with the LLM judge.

        Args:
            case: The golden case; ``case.grading`` may carry a per-case ``rubric`` and a
                ``reference`` answer.
            output: The answer to grade.
            trace: The collected trace (unused; kept for protocol symmetry).

        Returns:
            A :class:`MetricScore` with ``value`` normalised to ``0..1``; ``error`` set if
            the judge model is unavailable or its response cannot be parsed.
        """
        client = self._ensure_client()
        if client is None:
            return MetricScore(
                metric=self.name,
                error="judge ModelClient unavailable (dev/offline)",
            )

        grading = getattr(case, "grading", {}) or {}
        rubric = grading.get("rubric") or self._rubric()
        question = getattr(case, "input", {}).get("question", "")
        reference = grading.get("reference")

        user_content = _build_user_message(str(question), output, reference)
        messages = [
            {"role": "system", "content": rubric},
            {"role": "user", "content": user_content},
        ]

        try:
            result = await client.chat(
                alias=self._model_alias,
                messages=messages,
                prompt_id=self._rubric_prompt_id,
                temperature=0.0,
            )
        except Exception as exc:  # noqa: BLE001 - upstream failure must not crash CI
            _log.warning("judge model call failed", error=str(exc))
            return MetricScore(metric=self.name, error=f"judge call error: {exc}")

        parsed = _parse_judgement(getattr(result, "text", "") or "")
        if parsed is None:
            return MetricScore(
                metric=self.name,
                error="could not parse judge response as JSON",
                detail={"raw": getattr(result, "text", "")[:500]},
            )

        raw_score, reason = parsed
        value = max(0.0, min(1.0, raw_score / 10.0))
        return MetricScore(
            metric=self.name,
            value=value,
            detail={
                "raw_score": raw_score,
                "reason": reason,
                "model": getattr(result, "model", None),
                "cost_usd": getattr(result, "cost_usd", None),
            },
        )


def _build_user_message(question: str, answer: str, reference: str | None) -> str:
    """Assemble the judge's user message from the case fields."""
    parts = [f"QUESTION:\n{question}", f"ANSWER:\n{answer}"]
    if reference:
        parts.append(f"REFERENCE:\n{reference}")
    return "\n\n".join(parts)


def _parse_judgement(text: str) -> tuple[float, str] | None:
    """Parse ``{"score": n, "reason": "..."}`` out of the judge's reply.

    Tolerates surrounding prose/markdown fences by extracting the first JSON object.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
        score = float(obj.get("score", 0))
        reason = str(obj.get("reason", ""))
        return score, reason
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
