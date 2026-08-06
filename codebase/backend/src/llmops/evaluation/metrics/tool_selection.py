"""Custom tool-selection evaluator — the platform's flagship agentic metric.

Agents fail most often not by writing prose badly but by *choosing the wrong tool* (or
none), or by calling the right tool with the wrong arguments. This evaluator reads the
tool span(s) the agent actually emitted from the collected trace and compares them to the
golden expectation, producing:

    * ``accuracy``           — fraction of cases where the chosen tool matched (per-case: 1/0)
    * ``precision``/``recall`` per tool (aggregated by the runner across cases)
    * ``wrong_tool`` / ``missing_tool`` flags for triage
    * ``arg_correctness``    — fraction of expected arguments present and equal

It has **no external dependencies** — pure Python over the trace — so it always runs, in
CI and in dev alike. The runner aggregates the per-case scores into the corpus-level
``tool_selection_accuracy`` metric that :mod:`llmops.evaluation.thresholds` gates on.
"""

from __future__ import annotations

from typing import Any

from llmops.common.logging import get_logger
from llmops.evaluation.metrics.base import EvalTrace, MetricScore, SpanRecord

_log = get_logger(__name__)

#: GenAI/attribute keys the tracer may use for the selected tool name and arguments.
_TOOL_NAME_KEYS = ("gen_ai.tool.name", "tool.name", "name")
_TOOL_ARGS_KEYS = ("gen_ai.tool.arguments", "tool.arguments", "tool.args", "args", "arguments")


def _extract_tool_name(span: SpanRecord) -> str | None:
    """Return the tool name recorded on a span, checking known attribute keys."""
    for key in _TOOL_NAME_KEYS:
        val = span.attributes.get(key)
        if val:
            return str(val)
    # Fall back to a ``tool:<name>`` span-name convention.
    if span.name.startswith("tool:"):
        return span.name.split(":", 1)[1]
    return None


def _extract_tool_args(span: SpanRecord) -> dict[str, Any]:
    """Return the argument mapping recorded on a span (best effort)."""
    for key in _TOOL_ARGS_KEYS:
        val = span.attributes.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _score_args(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[float, list[str]]:
    """Score argument correctness as the fraction of expected keys matched by value.

    Returns:
        A ``(fraction, mismatches)`` tuple. ``fraction`` is ``1.0`` when no arguments are
        expected (nothing to get wrong).
    """
    if not expected:
        return 1.0, []
    mismatches: list[str] = []
    matched = 0
    for key, want in expected.items():
        got = actual.get(key, _MISSING)
        if got is _MISSING:
            mismatches.append(f"{key}: missing")
        elif got != want:
            mismatches.append(f"{key}: {got!r} != {want!r}")
        else:
            matched += 1
    return matched / len(expected), mismatches


_MISSING = object()


class ToolSelectionMetric:
    """Grades whether the agent selected the expected tool with correct arguments.

    Implements the :class:`llmops.evaluation.metrics.base.Metric` protocol.
    """

    name = "tool_selection"

    async def score(self, case: Any, output: str, trace: EvalTrace) -> MetricScore:
        """Score tool selection for a single case.

        Args:
            case: The golden case. ``case.grading`` may contain ``expected_tool`` (str),
                ``expected_tools`` (list[str]), and ``expected_args`` (dict).
            output: The final pipeline output (unused; kept for protocol symmetry).
            trace: The collected trace; tool spans are read from it.

        Returns:
            A :class:`MetricScore` whose ``value`` is ``1.0`` on a correct selection and
            ``0.0`` otherwise, with a full breakdown in ``detail`` for aggregation.
        """
        grading = getattr(case, "grading", {}) or {}
        expected_tool: str | None = grading.get("expected_tool")
        if not expected_tool:
            tools = grading.get("expected_tools")
            expected_tool = str(tools[0]) if isinstance(tools, list) and tools else None
        expected_args: dict[str, Any] = grading.get("expected_args", {}) or {}

        tool_spans = trace.tool_spans()
        chosen_tools = [t for t in (_extract_tool_name(s) for s in tool_spans) if t]
        chosen = chosen_tools[0] if chosen_tools else None

        # Case where no tool was expected: correct iff the agent also called none.
        if expected_tool is None:
            correct = not chosen_tools
            return MetricScore(
                metric=self.name,
                value=1.0 if correct else 0.0,
                passed=correct,
                detail={
                    "expected_tool": None,
                    "chosen_tool": chosen,
                    "chosen_tools": chosen_tools,
                    "wrong_tool": bool(chosen_tools),
                    "missing_tool": False,
                    "arg_correctness": 1.0,
                },
            )

        matched_span = next(
            (s for s in tool_spans if _extract_tool_name(s) == expected_tool), None
        )
        is_correct_tool = matched_span is not None
        missing_tool = not chosen_tools
        wrong_tool = bool(chosen_tools) and not is_correct_tool

        arg_correctness = 0.0
        arg_mismatches: list[str] = []
        if matched_span is not None:
            arg_correctness, arg_mismatches = _score_args(
                expected_args, _extract_tool_args(matched_span)
            )

        # A case counts as fully correct only when the right tool is chosen AND its
        # arguments are correct; the aggregate accuracy uses this strict definition.
        correct = is_correct_tool and arg_correctness >= 1.0
        value = 1.0 if correct else 0.0

        detail = {
            "expected_tool": expected_tool,
            "expected_args": expected_args,
            "chosen_tool": chosen,
            "chosen_tools": chosen_tools,
            "is_correct_tool": is_correct_tool,
            "wrong_tool": wrong_tool,
            "missing_tool": missing_tool,
            "arg_correctness": arg_correctness,
            "arg_mismatches": arg_mismatches,
        }
        if not correct:
            _log.info(
                "tool selection incorrect",
                case_id=getattr(case, "id", "?"),
                expected=expected_tool,
                chosen=chosen,
                wrong_tool=wrong_tool,
                missing_tool=missing_tool,
                arg_correctness=arg_correctness,
            )
        return MetricScore(metric=self.name, value=value, passed=correct, detail=detail)


def aggregate_tool_selection(scores: list[MetricScore]) -> dict[str, Any]:
    """Aggregate per-case tool-selection scores into corpus-level metrics.

    Computes overall accuracy plus per-tool precision/recall from the ``detail`` payloads.

    Args:
        scores: The per-case :class:`MetricScore` objects produced by
            :class:`ToolSelectionMetric`.

    Returns:
        A dict with ``accuracy``, ``arg_correctness`` (mean), ``wrong_tool`` /
        ``missing_tool`` counts, and ``per_tool`` precision/recall/F1.
    """
    usable = [s for s in scores if s.ok]
    total = len(usable)
    if total == 0:
        return {"accuracy": 0.0, "arg_correctness": 0.0, "per_tool": {}, "count": 0}

    correct = sum(1 for s in usable if s.value >= 1.0)
    wrong = sum(1 for s in usable if s.detail.get("wrong_tool"))
    missing = sum(1 for s in usable if s.detail.get("missing_tool"))
    arg_mean = sum(float(s.detail.get("arg_correctness", 0.0)) for s in usable) / total

    # Per-tool confusion tallies for precision/recall.
    tp: dict[str, int] = {}
    fp: dict[str, int] = {}
    fn: dict[str, int] = {}
    for s in usable:
        expected = s.detail.get("expected_tool")
        chosen = s.detail.get("chosen_tool")
        if expected == chosen and expected is not None:
            tp[expected] = tp.get(expected, 0) + 1
        else:
            if chosen is not None:
                fp[chosen] = fp.get(chosen, 0) + 1
            if expected is not None:
                fn[expected] = fn.get(expected, 0) + 1

    per_tool: dict[str, dict[str, float]] = {}
    for tool in set(tp) | set(fp) | set(fn):
        t, f_p, f_n = tp.get(tool, 0), fp.get(tool, 0), fn.get(tool, 0)
        precision = t / (t + f_p) if (t + f_p) else 0.0
        recall = t / (t + f_n) if (t + f_n) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_tool[tool] = {"precision": precision, "recall": recall, "f1": f1}

    return {
        "accuracy": correct / total,
        "arg_correctness": arg_mean,
        "wrong_tool": wrong,
        "missing_tool": missing,
        "per_tool": per_tool,
        "count": total,
    }
