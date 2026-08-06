"""Tool base class — the MCP-compatible unit of capability.

A :class:`Tool` is a named, self-describing, async-invokable capability with a typed pydantic
input schema. Tools are the actions an :class:`~llmops.orchestration.agent.Agent` can take; they
wrap the data-access layer (RAG, SQL, documents, records) so orchestration never touches an
Azure SDK directly.

Every ``run`` is wrapped in a tool span (``llmops.observability.tracing.tool_call_span``) so tool
selection and latency are observable. The tracing module is developed independently; if it is not
importable at runtime we fall back to a no-op span so tools keep working.

The :meth:`Tool.to_mcp` method emits a description in the shape the Model Context Protocol expects
(``name`` / ``description`` / ``inputSchema``), so the same catalog can be surfaced to MCP clients.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from llmops.common.errors import ToolError
from llmops.common.logging import get_logger
from llmops.common.types import ToolResult

_logger = get_logger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from llmops.observability.tracing import tool_call_span
else:
    try:
        from llmops.observability.tracing import tool_call_span
    except Exception:  # noqa: BLE001 - observability package built separately
        from collections.abc import Iterator
        from contextlib import contextmanager

        @contextmanager
        def tool_call_span(  # type: ignore[no-redef]
            name: str,
            mcp_server: str | None = None,
            args: dict[str, Any] | None = None,
            expected_tool: str | None = None,
        ) -> Iterator[None]:
            """No-op fallback tool span used until observability is wired."""
            yield None


class _EmptyArgs(BaseModel):
    """Default (argument-less) input schema."""


class Tool(BaseModel, ABC):
    """Base class for all platform tools.

    Subclasses set :attr:`input_schema` to a pydantic model and implement :meth:`_run`. The
    public :meth:`run` validates keyword arguments against the schema, opens a tool span, times
    the call, and normalises the outcome into a :class:`~llmops.common.types.ToolResult`.

    Attributes:
        name: Stable, unique tool name (also the MCP tool name).
        description: One-line description used by the model to decide when to call the tool.
        mcp_server: Logical MCP server this tool belongs to (for span attribution).
        input_schema: Pydantic model describing the tool's arguments (class-level).
    """

    name: str
    description: str
    mcp_server: str = "llmops"

    #: Class-level pydantic schema for the tool's arguments.
    input_schema: ClassVar[type[BaseModel]] = _EmptyArgs

    async def run(self, **kwargs: Any) -> ToolResult:
        """Validate arguments, execute the tool within a span, and return a result.

        Args:
            **kwargs: Arguments matching :attr:`input_schema`.

        Returns:
            A :class:`~llmops.common.types.ToolResult` (``ok=False`` with ``error`` on failure).
        """
        try:
            payload = self.input_schema.model_validate(kwargs)
        except Exception as exc:  # noqa: BLE001 - surface as a structured tool error
            _logger.warning("tool argument validation failed", tool=self.name, error=str(exc))
            return ToolResult(name=self.name, ok=False, error=f"invalid arguments: {exc}")

        started = time.perf_counter()
        with tool_call_span(self.name, mcp_server=self.mcp_server, args=payload.model_dump()):
            try:
                result = await self._run(payload)
            except ToolError as exc:
                latency_ms = int((time.perf_counter() - started) * 1000)
                _logger.warning("tool error", tool=self.name, error=exc.message)
                return ToolResult(name=self.name, ok=False, error=exc.message, latency_ms=latency_ms)
            except Exception as exc:  # noqa: BLE001 - never leak raw stack to callers
                latency_ms = int((time.perf_counter() - started) * 1000)
                _logger.exception("unexpected tool failure", tool=self.name)
                return ToolResult(name=self.name, ok=False, error=str(exc), latency_ms=latency_ms)

        result.latency_ms = result.latency_ms or int((time.perf_counter() - started) * 1000)
        return result

    @abstractmethod
    async def _run(self, payload: BaseModel) -> ToolResult:
        """Execute the tool with a validated ``payload``.

        Args:
            payload: A validated instance of :attr:`input_schema`.

        Returns:
            A :class:`~llmops.common.types.ToolResult`.
        """
        raise NotImplementedError

    def to_mcp(self) -> dict[str, Any]:
        """Return an MCP-compatible tool description.

        Returns:
            A mapping with ``name``, ``description``, and JSON-Schema ``inputSchema`` keys.
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema.model_json_schema(),
        }
