"""Pipeline — a sequential composition of steps (NOT agent-to-agent).

A :class:`Pipeline` runs its :class:`~llmops.orchestration.step.Step` list **in order**, threading a
single :class:`PipelineContext` through them and checkpointing :class:`PipelineState` after each step
so a run can be resumed. Agents never call each other; all composition is explicit and sequential —
this keeps runs deterministic, observable, and easy to evaluate.

Pipelines are config-as-code: :meth:`from_yaml` loads a definition from
``usecases/<uc>/agents/pipeline.agent.yaml`` (see :meth:`from_usecase`).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel, Field

from llmops.common.errors import ConfigError, GuardrailBlocked, LLMOpsError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.orchestration.agent import Agent
from llmops.orchestration.context import PipelineContext
from llmops.orchestration.state import (
    PipelineState,
    RunStatus,
    StateStore,
    default_state_store,
)
from llmops.orchestration.step import Step, StepResult

_logger = get_logger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterator
    from contextlib import contextmanager

    @contextmanager
    def span(name: str, **attrs: Any) -> Iterator[Any]:
        """Typing stub for the tracing span."""
        yield None
else:
    try:
        from llmops.observability.tracing import span
    except Exception:  # noqa: BLE001 - observability built separately
        from contextlib import contextmanager

        @contextmanager
        def span(name, **attrs):  # type: ignore[no-redef]
            """No-op fallback span until observability is wired."""
            yield None


class PipelineResult(BaseModel):
    """Outcome of a full pipeline run.

    Attributes:
        pipeline: The pipeline name.
        trace_id: Correlation id for the run.
        ok: Whether every step completed successfully.
        outputs: Final blackboard snapshot (``{step_name: output}``).
        steps: Per-step results, in execution order.
        error: Error message when the run failed or was blocked.
        latency_ms: Total wall-clock duration.
    """

    pipeline: str
    trace_id: str
    ok: bool = True
    outputs: dict[str, Any] = Field(default_factory=dict)
    steps: list[StepResult] = Field(default_factory=list)
    error: str | None = None
    latency_ms: int = 0


class Pipeline:
    """A sequential pipeline of steps.

    Args:
        name: Pipeline name.
        steps: Ordered steps to execute.
        settings: Platform settings. Defaults to the process singleton.
        state_store: Checkpoint store. Defaults to Cosmos when configured, else in-memory.
    """

    def __init__(
        self,
        name: str,
        steps: list[Step],
        *,
        settings: Settings | None = None,
        state_store: StateStore | None = None,
    ) -> None:
        self.name = name
        self.steps = steps
        self._settings = settings or get_settings()
        self._state_store = state_store or default_state_store(self._settings)

    async def run(self, input: dict[str, Any]) -> PipelineResult:  # noqa: A002 - matches spec signature
        """Execute all steps in order, checkpointing after each.

        Args:
            input: The pipeline inputs.

        Returns:
            A :class:`PipelineResult`. On a guardrail block or step failure, ``ok`` is ``False``
            and ``error`` is populated (the run does not raise for these expected conditions).
        """
        ctx = PipelineContext(inputs=dict(input), settings=self._settings)
        state = PipelineState(trace_id=ctx.trace_id, pipeline=self.name, status=RunStatus.RUNNING)
        started = time.perf_counter()
        results: list[StepResult] = []

        with span(f"pipeline.{self.name}", pipeline=self.name, trace_id=ctx.trace_id):
            await self._state_store.save(state)
            for index, step in enumerate(self.steps):
                state.current_step = index
                try:
                    result = await step.run(ctx)
                except (GuardrailBlocked, LLMOpsError) as exc:
                    return await self._finalise_failure(ctx, state, results, exc, started)

                results.append(result)
                state.completed_steps.append(step.name)
                state.memory = dict(ctx.memory)
                await self._state_store.save(state)

            state.status = RunStatus.COMPLETED
            state.current_step = len(self.steps)
            await self._state_store.save(state)

        latency_ms = int((time.perf_counter() - started) * 1000)
        _logger.info(
            "pipeline completed",
            pipeline=self.name,
            trace_id=ctx.trace_id,
            steps=len(results),
            latency_ms=latency_ms,
        )
        return PipelineResult(
            pipeline=self.name,
            trace_id=ctx.trace_id,
            ok=True,
            outputs=dict(ctx.memory),
            steps=results,
            latency_ms=latency_ms,
        )

    async def _finalise_failure(
        self,
        ctx: PipelineContext,
        state: PipelineState,
        results: list[StepResult],
        exc: LLMOpsError,
        started: float,
    ) -> PipelineResult:
        """Persist a failed state and build a non-raising failure result."""
        state.status = RunStatus.FAILED
        state.error = exc.message
        await self._state_store.save(state)
        latency_ms = int((time.perf_counter() - started) * 1000)
        _logger.warning(
            "pipeline failed",
            pipeline=self.name,
            trace_id=ctx.trace_id,
            error=exc.message,
            code=exc.code,
        )
        return PipelineResult(
            pipeline=self.name,
            trace_id=ctx.trace_id,
            ok=False,
            outputs=dict(ctx.memory),
            steps=results,
            error=exc.message,
            latency_ms=latency_ms,
        )

    # ------------------------------------------------------------------ loaders

    @classmethod
    def from_usecase(
        cls,
        usecase: str,
        *,
        settings: Settings | None = None,
        state_store: StateStore | None = None,
    ) -> Pipeline:
        """Load the pipeline for ``usecase`` from its ``pipeline.agent.yaml``.

        Args:
            usecase: Use-case directory name under ``settings.usecases_dir``.
            settings: Platform settings. Defaults to the process singleton.
            state_store: Optional checkpoint store.

        Returns:
            A constructed :class:`Pipeline`.
        """
        cfg = settings or get_settings()
        path = Path(cfg.usecases_dir) / usecase / "agents" / "pipeline.agent.yaml"
        return cls.from_yaml(path, settings=cfg, state_store=state_store)

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        settings: Settings | None = None,
        state_store: StateStore | None = None,
    ) -> Pipeline:
        """Construct a pipeline from a ``pipeline.agent.yaml`` definition.

        The YAML shape is::

            name: hiring_screen
            steps:
              - name: screen
                agent: { role: screener, prompt_id: hiring/screen, model_alias: reason,
                         tools: [search_knowledge], temperature: 0.1 }

        Args:
            path: Path to the YAML file.
            settings: Platform settings.
            state_store: Optional checkpoint store.

        Returns:
            A constructed :class:`Pipeline`.

        Raises:
            ConfigError: If the file is missing or malformed.
        """
        cfg = settings or get_settings()
        p = Path(path)
        if not p.exists():
            raise ConfigError(f"pipeline definition not found at {p}", detail={"path": str(p)})
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"failed to parse pipeline yaml: {exc}", detail={"path": str(p)}) from exc

        name = raw.get("name") or p.parent.parent.name
        steps: list[Step] = []
        for entry in raw.get("steps", []):
            step_name = entry.get("name")
            if not step_name:
                raise ConfigError("each pipeline step requires a 'name'", detail={"path": str(p)})
            agent_cfg = entry.get("agent")
            if agent_cfg is None:
                raise ConfigError(
                    f"step '{step_name}' has no 'agent' (YAML pipelines compose agents)",
                    detail={"path": str(p)},
                )
            agent = Agent(name=step_name, **agent_cfg)
            steps.append(Step(step_name, agent=agent))

        return cls(name, steps, settings=cfg, state_store=state_store)
