"""Pipeline step — wraps an agent or a plain callable and records a span.

A :class:`Step` is the unit of sequencing. It either runs an :class:`~llmops.orchestration.agent.Agent`
or an arbitrary (sync or async) callable over the :class:`PipelineContext`, publishes its output to
the shared blackboard under the step name, and returns a :class:`StepResult`. Each step runs inside
a span so per-step latency and failures are observable.
"""

from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel

from llmops.common.errors import LLMOpsError
from llmops.common.logging import get_logger
from llmops.orchestration.agent import AgentResult
from llmops.orchestration.context import PipelineContext

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


@runtime_checkable
class AgentLike(Protocol):
    """Minimal structural type an agent must satisfy to be wrapped by a :class:`Step`."""

    name: str

    async def run(self, ctx: PipelineContext) -> AgentResult:
        """Run the agent over ``ctx`` and return its result."""
        ...


#: A callable step: receives the context, returns any output (sync or awaitable).
StepCallable = Callable[[PipelineContext], "Any | Awaitable[Any]"]


class StepResult(BaseModel):
    """Outcome of a single step."""

    name: str
    ok: bool = True
    output: Any = None
    error: str | None = None
    latency_ms: int = 0


class Step:
    """A single pipeline step wrapping an agent or a callable.

    Exactly one of ``agent`` / ``fn`` must be provided.

    Args:
        name: Step name; also the blackboard key its output is published under.
        agent: An agent to run (mutually exclusive with ``fn``).
        fn: A callable to run (mutually exclusive with ``agent``).
    """

    def __init__(
        self,
        name: str,
        *,
        agent: AgentLike | None = None,
        fn: StepCallable | None = None,
    ) -> None:
        if (agent is None) == (fn is None):
            raise LLMOpsError("a Step requires exactly one of 'agent' or 'fn'")
        self.name = name
        self._agent = agent
        self._fn = fn

    @property
    def kind(self) -> str:
        """Return ``"agent"`` or ``"callable"`` describing this step."""
        return "agent" if self._agent is not None else "callable"

    async def run(self, ctx: PipelineContext) -> StepResult:
        """Execute the step, publish its output to the blackboard, and return a result.

        Raises:
            LLMOpsError: Propagated from the wrapped agent/callable (after being recorded).
        """
        started = time.perf_counter()
        with span(f"step.{self.name}", step=self.name, kind=self.kind):
            try:
                output = await self._invoke(ctx)
            except LLMOpsError:
                _logger.warning("step failed", step=self.name, trace_id=ctx.trace_id)
                raise
            except Exception as exc:  # noqa: BLE001 - normalise unexpected errors
                _logger.exception("unexpected step failure", step=self.name)
                raise LLMOpsError(f"step '{self.name}' failed: {exc}") from exc

        ctx.remember(self.name, output)
        latency_ms = int((time.perf_counter() - started) * 1000)
        _logger.debug("step completed", step=self.name, latency_ms=latency_ms)
        return StepResult(name=self.name, ok=True, output=output, latency_ms=latency_ms)

    async def _invoke(self, ctx: PipelineContext) -> Any:
        """Dispatch to the wrapped agent or callable, awaiting coroutines as needed."""
        if self._agent is not None:
            return await self._agent.run(ctx)
        assert self._fn is not None  # noqa: S101 - guaranteed by constructor invariant
        result = self._fn(ctx)
        if inspect.isawaitable(result):
            return await result
        return result
