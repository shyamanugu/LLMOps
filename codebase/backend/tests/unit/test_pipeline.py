"""Unit tests for the sequential pipeline runtime.

Covers a two-step pipeline built from mock agents: verifies ordered execution, blackboard
threading between steps, checkpointing to the in-memory state store, and graceful failure
handling (a step raising an :class:`~llmops.common.errors.LLMOpsError` yields ``ok=False`` rather
than propagating).
"""

from __future__ import annotations

import pytest

from llmops.common.errors import LLMOpsError
from llmops.orchestration.agent import AgentResult
from llmops.orchestration.context import PipelineContext
from llmops.orchestration.pipeline import Pipeline
from llmops.orchestration.state import InMemoryStateStore, RunStatus
from llmops.orchestration.step import Step


class MockAgent:
    """A minimal agent double conforming to the ``AgentLike`` protocol."""

    def __init__(self, name: str, reply: str) -> None:
        self.name = name
        self._reply = reply
        self.calls = 0

    async def run(self, ctx: PipelineContext) -> AgentResult:
        """Record the call and echo a reply that references prior memory."""
        self.calls += 1
        prior = sorted(ctx.memory)
        return AgentResult(agent=self.name, output=f"{self._reply}|seen={prior}")


@pytest.mark.asyncio
async def test_two_step_pipeline_runs_in_order_and_threads_memory() -> None:
    """A 2-step pipeline runs both agents in order and shares the blackboard."""
    first = MockAgent("first", "hello")
    second = MockAgent("second", "world")
    store = InMemoryStateStore()
    pipeline = Pipeline(
        "demo",
        steps=[Step("first", agent=first), Step("second", agent=second)],
        state_store=store,
    )

    result = await pipeline.run({"question": "hi"})

    assert result.ok is True
    assert [s.name for s in result.steps] == ["first", "second"]
    assert first.calls == 1 and second.calls == 1

    # The second agent must have observed the first agent's output on the blackboard.
    second_output = result.outputs["second"].output
    assert "seen=['first']" in second_output

    # State was checkpointed and marked completed.
    state = await store.load(result.trace_id)
    assert state is not None
    assert state.status is RunStatus.COMPLETED
    assert state.completed_steps == ["first", "second"]


@pytest.mark.asyncio
async def test_callable_step_output_is_published_to_blackboard() -> None:
    """A callable step publishes its return value under the step name."""

    def transform(ctx: PipelineContext) -> str:
        return ctx.inputs["text"].upper()

    pipeline = Pipeline("cb", steps=[Step("upper", fn=transform)], state_store=InMemoryStateStore())
    result = await pipeline.run({"text": "abc"})

    assert result.ok is True
    assert result.outputs["upper"] == "ABC"


@pytest.mark.asyncio
async def test_pipeline_reports_failure_without_raising() -> None:
    """A failing step yields ok=False and records FAILED state, not an exception."""

    def boom(ctx: PipelineContext) -> None:
        raise LLMOpsError("boom")

    store = InMemoryStateStore()
    pipeline = Pipeline("fail", steps=[Step("boom", fn=boom)], state_store=store)

    result = await pipeline.run({})

    assert result.ok is False
    assert result.error == "boom"
    state = await store.load(result.trace_id)
    assert state is not None
    assert state.status is RunStatus.FAILED


def test_step_requires_exactly_one_of_agent_or_fn() -> None:
    """Constructing a Step with neither/both agent and fn is rejected."""
    with pytest.raises(LLMOpsError):
        Step("bad")
    with pytest.raises(LLMOpsError):
        Step("bad", agent=MockAgent("a", "x"), fn=lambda ctx: None)
