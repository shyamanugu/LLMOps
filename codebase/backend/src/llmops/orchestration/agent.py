"""Agent — a single reasoning unit within a sequential pipeline.

An :class:`Agent` binds together a *role*, a *prompt* (by id, resolved from the prompt registry),
a *model alias* (resolved to a deployment by the model router at call time), and a set of *tool
names* it may use. ``run`` renders the prompt with the current context, calls the model client,
and returns an :class:`AgentResult`.

This is **not** an agent-to-agent (A2A) framework: agents do not call each other. They are composed
sequentially by :class:`~llmops.orchestration.pipeline.Pipeline`. Each ``run`` is wrapped in an
agent span so the request > agent > model/tool hierarchy is observable.

The prompt loader (``llmops.prompts.loader``) and model client (``llmops.models.client``) are built
by other modules; they are imported defensively so that, until they are wired, the agent degrades
to a deterministic dev echo rather than failing at import time.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from llmops.common.logging import get_logger
from llmops.common.types import Usage
from llmops.orchestration.context import PipelineContext

_logger = get_logger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterator
    from contextlib import contextmanager

    @contextmanager
    def span(name: str, **attrs: Any) -> Iterator[Any]:
        """Typing stub for the tracing span."""
        yield None

    def load_prompt(prompt_id: str, label: str = "prod") -> Any:
        """Typing stub for the prompt loader."""
        ...

    class ModelClient:  # noqa: D401 - typing stub
        """Typing stub for the model client."""

        async def chat(self, *, alias: str, messages: list[dict[str, Any]], **kw: Any) -> Any:
            """Typing stub for the chat call."""
            ...
else:
    try:
        from llmops.observability.tracing import span
    except Exception:  # noqa: BLE001 - observability built separately
        from contextlib import contextmanager

        @contextmanager
        def span(name, **attrs):  # type: ignore[no-redef]
            """No-op fallback span until observability is wired."""
            yield None

    try:
        from llmops.prompts.loader import load_prompt  # type: ignore[no-redef]
    except Exception:  # noqa: BLE001 - prompts package built separately
        load_prompt = None  # type: ignore[assignment]

    try:
        from llmops.models.client import ModelClient  # type: ignore[no-redef]
    except Exception:  # noqa: BLE001 - models package built separately
        ModelClient = None  # type: ignore[assignment,misc]


class AgentResult(BaseModel):
    """Outcome of a single agent run.

    Attributes:
        agent: The agent's name.
        output: The agent's text output.
        model: The resolved deployment used (empty when the dev fallback ran).
        usage: Token usage for the model call.
        cost_usd: Cost attributed to the call.
        tool_calls: Names of tools the agent invoked during the run.
        latency_ms: Wall-clock duration of the run.
        raw: Optional provider-specific payload for debugging.
    """

    agent: str
    output: str = ""
    model: str = ""
    usage: Usage = Field(default_factory=Usage)
    cost_usd: float = 0.0
    tool_calls: list[str] = Field(default_factory=list)
    latency_ms: int = 0
    raw: dict[str, Any] | None = None


class Agent(BaseModel):
    """A prompt-driven reasoning unit.

    Attributes:
        name: Unique agent name within a pipeline.
        role: Human-readable role (used in the dev fallback and logs).
        prompt_id: Prompt registry id to render for this agent.
        model_alias: Task alias (``reason`` | ``bulk`` | ``judge`` | ...) resolved by the router.
        tools: Names of tools this agent is permitted to use.
        temperature: Sampling temperature for the model call.
        prompt_label: Registry label to resolve the prompt at (``prod`` | ``staging`` | ...).
    """

    name: str
    role: str = ""
    prompt_id: str = ""
    model_alias: str = "reason"
    tools: list[str] = Field(default_factory=list)
    temperature: float = 0.2
    prompt_label: str = "prod"

    async def run(
        self,
        ctx: PipelineContext,
        *,
        model_client: ModelClient | None = None,
    ) -> AgentResult:
        """Render the prompt, call the model, and return the result.

        Args:
            ctx: The shared pipeline context.
            model_client: Optional injected model client. When ``None`` and the models package is
                unavailable, the agent runs a deterministic dev fallback.

        Returns:
            An :class:`AgentResult`.
        """
        started = time.perf_counter()
        with span(f"agent.{self.name}", agent=self.name, role=self.role, model_alias=self.model_alias):
            prompt_text = self._render_prompt(ctx)
            client = model_client or (ModelClient() if ModelClient is not None else None)

            if client is None:
                result = self._dev_fallback(ctx, prompt_text)
            else:
                messages = [{"role": "user", "content": prompt_text}]
                chat = await client.chat(
                    alias=self.model_alias,
                    messages=messages,
                    prompt_id=self.prompt_id or None,
                    temperature=self.temperature,
                )
                result = AgentResult(
                    agent=self.name,
                    output=getattr(chat, "text", str(chat)),
                    model=getattr(chat, "model", ""),
                    usage=getattr(chat, "usage", Usage()),
                    cost_usd=float(getattr(chat, "cost_usd", 0.0)),
                )

        result.latency_ms = int((time.perf_counter() - started) * 1000)
        _logger.info(
            "agent completed",
            agent=self.name,
            trace_id=ctx.trace_id,
            model=result.model or "dev-fallback",
            latency_ms=result.latency_ms,
        )
        return result

    def _render_prompt(self, ctx: PipelineContext) -> str:
        """Resolve and render the agent's prompt, degrading gracefully if unavailable."""
        if self.prompt_id and load_prompt is not None:
            try:
                spec = load_prompt(self.prompt_id, self.prompt_label)
                variables = {**ctx.inputs, **ctx.memory}
                return str(spec.render(**variables))
            except Exception as exc:  # noqa: BLE001 - fall back rather than crash the run
                _logger.warning(
                    "prompt render failed; using role fallback",
                    agent=self.name,
                    prompt_id=self.prompt_id,
                    error=str(exc),
                )
        # TODO(wiring): once llmops.prompts.loader is available this fallback is only hit in dev.
        return f"[{self.role or self.name}] inputs={ctx.inputs} memory_keys={sorted(ctx.memory)}"

    def _dev_fallback(self, ctx: PipelineContext, prompt_text: str) -> AgentResult:
        """Deterministic result used when no model client is wired (dev/tests)."""
        _logger.debug("agent dev fallback (no model client)", agent=self.name)
        return AgentResult(
            agent=self.name,
            output=f"[dev:{self.name}] {prompt_text}",
            model="",
            raw={"dev_fallback": True, "trace_id": ctx.trace_id},
        )
