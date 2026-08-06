"""Unit tests for the custom tool-selection metric (trace-driven, no external deps)."""

from __future__ import annotations

import pytest

from llmops.evaluation.metrics.base import EvalTrace, SpanRecord
from llmops.evaluation.metrics.tool_selection import (
    ToolSelectionMetric,
    aggregate_tool_selection,
)

pytestmark = pytest.mark.asyncio


def _case(case_id: str, grading: dict) -> object:
    """Build a minimal object with the attributes the metric reads."""

    class _Case:
        id = case_id

        def __init__(self) -> None:
            self.grading = grading
            self.input = {"question": "q"}

    return _Case()


def _trace(tool: str | None, args: dict | None = None) -> EvalTrace:
    spans = []
    if tool is not None:
        attrs = {"tool.name": tool}
        if args is not None:
            attrs["tool.args"] = args
        spans.append(SpanRecord(name=f"tool:{tool}", kind="tool", attributes=attrs))
    return EvalTrace(trace_id="t", output_text="", spans=spans)


async def test_correct_tool_scores_one() -> None:
    metric = ToolSelectionMetric()
    score = await metric.score(_case("c1", {"expected_tool": "get_record"}), "", _trace("get_record"))
    assert score.value == 1.0
    assert score.detail["is_correct_tool"] is True
    assert score.detail["wrong_tool"] is False
    assert score.detail["missing_tool"] is False


async def test_wrong_tool_scores_zero_and_flags() -> None:
    metric = ToolSelectionMetric()
    score = await metric.score(_case("c1", {"expected_tool": "get_record"}), "", _trace("query_sql"))
    assert score.value == 0.0
    assert score.detail["wrong_tool"] is True
    assert score.detail["missing_tool"] is False
    assert score.detail["chosen_tool"] == "query_sql"


async def test_missing_tool_scores_zero_and_flags() -> None:
    metric = ToolSelectionMetric()
    score = await metric.score(_case("c1", {"expected_tool": "get_record"}), "", _trace(None))
    assert score.value == 0.0
    assert score.detail["missing_tool"] is True
    assert score.detail["wrong_tool"] is False


async def test_no_tool_expected_and_none_used_passes() -> None:
    metric = ToolSelectionMetric()
    score = await metric.score(_case("c1", {}), "", _trace(None))
    assert score.value == 1.0


async def test_no_tool_expected_but_one_used_is_wrong() -> None:
    metric = ToolSelectionMetric()
    score = await metric.score(_case("c1", {}), "", _trace("query_sql"))
    assert score.value == 0.0
    assert score.detail["wrong_tool"] is True


async def test_arg_correctness_full_match_passes() -> None:
    metric = ToolSelectionMetric()
    grading = {"expected_tool": "get_record", "expected_args": {"id": "42", "system": "crm"}}
    trace = _trace("get_record", {"id": "42", "system": "crm"})
    score = await metric.score(_case("c1", grading), "", trace)
    assert score.value == 1.0
    assert score.detail["arg_correctness"] == 1.0


async def test_arg_correctness_partial_match_fails_case() -> None:
    metric = ToolSelectionMetric()
    grading = {"expected_tool": "get_record", "expected_args": {"id": "42", "system": "crm"}}
    trace = _trace("get_record", {"id": "99", "system": "crm"})
    score = await metric.score(_case("c1", grading), "", trace)
    # Right tool but wrong argument value -> strict case failure, arg_correctness 0.5.
    assert score.value == 0.0
    assert score.detail["arg_correctness"] == 0.5
    assert score.detail["is_correct_tool"] is True
    assert any("id" in m for m in score.detail["arg_mismatches"])


async def test_span_name_fallback_when_no_attribute() -> None:
    metric = ToolSelectionMetric()
    trace = EvalTrace(spans=[SpanRecord(name="tool:search_knowledge", kind="tool")])
    score = await metric.score(_case("c1", {"expected_tool": "search_knowledge"}), "", trace)
    assert score.value == 1.0


async def test_aggregate_accuracy_and_per_tool_precision_recall() -> None:
    metric = ToolSelectionMetric()
    scores = [
        await metric.score(_case("c1", {"expected_tool": "get_record"}), "", _trace("get_record")),
        await metric.score(_case("c2", {"expected_tool": "get_record"}), "", _trace("query_sql")),
        await metric.score(_case("c3", {"expected_tool": "query_sql"}), "", _trace("query_sql")),
        await metric.score(_case("c4", {"expected_tool": "search_knowledge"}), "", _trace(None)),
    ]
    agg = aggregate_tool_selection(scores)
    # 2 of 4 correct.
    assert agg["accuracy"] == pytest.approx(0.5)
    assert agg["count"] == 4
    assert agg["missing_tool"] == 1
    assert agg["wrong_tool"] == 1
    # query_sql: 1 true positive, 1 false positive (from c2) -> precision 0.5, recall 1.0.
    assert agg["per_tool"]["query_sql"]["precision"] == pytest.approx(0.5)
    assert agg["per_tool"]["query_sql"]["recall"] == pytest.approx(1.0)
    # get_record: 1 TP, 1 FN (c2 missed) -> recall 0.5.
    assert agg["per_tool"]["get_record"]["recall"] == pytest.approx(0.5)


async def test_aggregate_empty_is_safe() -> None:
    agg = aggregate_tool_selection([])
    assert agg["accuracy"] == 0.0
    assert agg["count"] == 0
