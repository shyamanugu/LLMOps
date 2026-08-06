"""Shared pytest fixtures and path setup for the backend test suite.

Ensures ``src`` is importable (so ``import llmops`` works without an editable install) and
provides small, dependency-free fixtures used across unit and integration tests.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# Make the ``src`` layout importable for the whole test session.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llmops.evaluation.golden import GoldenCase  # noqa: E402
from llmops.evaluation.metrics.base import EvalTrace, SpanRecord  # noqa: E402


@pytest.fixture
def make_case() -> Any:
    """Return a factory that builds a :class:`GoldenCase` with sensible defaults."""

    def _factory(
        case_id: str = "c1",
        *,
        input: dict[str, Any] | None = None,  # noqa: A002 - mirrors model field name
        grading: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> GoldenCase:
        return GoldenCase(
            id=case_id,
            input=input or {"question": "hello"},
            grading=grading or {},
            meta=meta or {},
        )

    return _factory


@pytest.fixture
def make_trace() -> Any:
    """Return a factory that builds an :class:`EvalTrace` with optional tool spans."""

    def _factory(
        *,
        output: str = "",
        tool: str | None = None,
        tool_args: dict[str, Any] | None = None,
    ) -> EvalTrace:
        spans: list[SpanRecord] = []
        if tool is not None:
            attributes: dict[str, Any] = {"tool.name": tool}
            if tool_args is not None:
                attributes["tool.args"] = tool_args
            spans.append(SpanRecord(name=f"tool:{tool}", kind="tool", attributes=attributes))
        return EvalTrace(trace_id="t1", output_text=output, spans=spans)

    return _factory
