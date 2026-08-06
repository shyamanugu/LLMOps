"""Orchestration — the sequential pipeline runtime.

Public surface:
    * :class:`PipelineContext` — per-run shared state (``context``).
    * :class:`Agent` / :class:`AgentResult` — a prompt-driven reasoning unit (``agent``).
    * :class:`Step` / :class:`StepResult` — an agent/callable wrapper that records a span (``step``).
    * :class:`Pipeline` / :class:`PipelineResult` — sequential composition of steps (``pipeline``).
    * :class:`PipelineState` + state stores — checkpoint/resume (``state``).

Pipelines are sequential (NOT agent-to-agent): agents never call each other; the
:class:`Pipeline` composes them in order.
"""

from llmops.orchestration.agent import Agent, AgentResult
from llmops.orchestration.context import PipelineContext
from llmops.orchestration.pipeline import Pipeline, PipelineResult
from llmops.orchestration.state import (
    CosmosStateStore,
    InMemoryStateStore,
    PipelineState,
    RunStatus,
    StateStore,
    default_state_store,
)
from llmops.orchestration.step import Step, StepResult

__all__ = [
    "PipelineContext",
    "Agent",
    "AgentResult",
    "Step",
    "StepResult",
    "Pipeline",
    "PipelineResult",
    "PipelineState",
    "RunStatus",
    "StateStore",
    "InMemoryStateStore",
    "CosmosStateStore",
    "default_state_store",
]
