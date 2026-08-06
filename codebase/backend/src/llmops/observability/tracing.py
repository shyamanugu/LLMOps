"""OpenTelemetry tracing with GenAI semantic conventions.

Spans nest to mirror execution: an inbound ``request`` span contains ``agent`` spans, each
of which contains ``model`` and ``tool`` spans. We annotate model and tool spans using the
OpenTelemetry *GenAI* semantic conventions (``gen_ai.*``) so any conformant backend (App
Insights, Langfuse, Jaeger) renders them consistently, plus a few platform extensions:

* ``app.cost_usd`` — USD cost of a model call (attached by :mod:`llmops.observability.cost`).
* ``eval.expected_tool`` / ``eval.was_correct_tool`` — tool-selection evaluation signal.

The module is import-safe without the OpenTelemetry SDK: if the packages are missing (some
dev machines), it falls back to a no-op tracer so nothing crashes. Wiring the exporters is
delegated to :mod:`llmops.observability.exporters`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

from llmops.common.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - typing only
    from opentelemetry.trace import Span, Tracer

logger = get_logger(__name__)

# ---------------------------------------------------------------------------------------
# GenAI semantic-convention attribute keys (stable string constants).
# ---------------------------------------------------------------------------------------
GEN_AI_SYSTEM = "gen_ai.system"
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
GEN_AI_TOOL_NAME = "gen_ai.tool.name"

# Platform extensions.
APP_COST_USD = "app.cost_usd"
APP_PROMPT_ID = "app.prompt.id"
APP_PROMPT_VERSION = "app.prompt.version"
APP_MODEL_ALIAS = "app.model.alias"
APP_LATENCY_MS = "app.latency_ms"
APP_MCP_SERVER = "app.mcp.server"
EVAL_EXPECTED_TOOL = "eval.expected_tool"
EVAL_WAS_CORRECT_TOOL = "eval.was_correct_tool"

_SYSTEM_AZURE_OPENAI = "az.ai.openai"

_TRACING_READY = False

# Try to bind the real OpenTelemetry API; fall back to no-ops if unavailable.
try:  # pragma: no cover - import path depends on environment
    from opentelemetry import trace as _otel_trace
    from opentelemetry.trace import Status, StatusCode

    _OTEL_AVAILABLE = True
except Exception:  # noqa: BLE001 - degrade gracefully in minimal dev envs
    _otel_trace = None  # type: ignore[assignment]
    Status = StatusCode = None  # type: ignore[assignment,misc]
    _OTEL_AVAILABLE = False


def init_tracing(settings: Any) -> None:
    """Initialise the global tracer provider and exporters.

    Idempotent: safe to call once per process (e.g. from the FastAPI lifespan). When OTel is
    unavailable or disabled via ``settings.otel_enabled`` this becomes a logged no-op.

    Args:
        settings: The platform :class:`~llmops.config.settings.Settings`.
    """
    global _TRACING_READY
    if _TRACING_READY:
        return
    if not getattr(settings, "otel_enabled", True):
        logger.info("tracing disabled via settings.otel_enabled")
        _TRACING_READY = True
        return
    if not _OTEL_AVAILABLE:
        logger.warning("opentelemetry not installed; tracing runs in no-op mode")
        _TRACING_READY = True
        return

    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    resource = Resource.create(
        {
            "service.name": getattr(settings, "service_name", "llmops-platform"),
            "deployment.environment": getattr(settings, "environment", "dev"),
        }
    )
    provider = TracerProvider(resource=resource)

    # Exporter wiring (App Insights + Langfuse) lives in exporters.py and no-ops in dev.
    from llmops.observability.exporters import configure_exporters

    configure_exporters(settings, provider)

    _otel_trace.set_tracer_provider(provider)
    _TRACING_READY = True
    logger.info("tracing initialised", service=getattr(settings, "service_name", "llmops-platform"))


def get_tracer() -> "Tracer":
    """Return the platform tracer (a no-op tracer if OTel is unavailable)."""
    if not _OTEL_AVAILABLE:
        return _NoOpTracer()  # type: ignore[return-value]
    return _otel_trace.get_tracer("llmops")


@contextmanager
def span(name: str, **attrs: Any) -> "Iterator[Span]":
    """Start a span named ``name``, set ``attrs``, record exceptions, and end it.

    Args:
        name: Span name (e.g. ``"request"``, ``"agent:triage"``).
        **attrs: Attributes to set on the span. ``None`` values are skipped.

    Yields:
        The active span, so callers can set further attributes.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as current:
        _set_attrs(current, attrs)
        try:
            yield current
        except Exception as exc:  # noqa: BLE001 - record then re-raise
            _record_exception(current, exc)
            raise


@contextmanager
def model_call_span(
    alias: str,
    deployment: str,
    prompt_id: str | None = None,
    prompt_version: int | None = None,
) -> "Iterator[Span]":
    """Open a ``model`` span pre-populated with GenAI request attributes.

    The caller is expected to set usage and cost on the yielded span once the response is
    known (see :func:`set_model_usage` and :func:`llmops.observability.cost.attach_cost`).

    Args:
        alias: The task alias requested (e.g. ``"reason"``).
        deployment: The resolved Azure deployment name.
        prompt_id: Prompt identifier, when the call is driven by a registered prompt.
        prompt_version: Prompt version, when known.

    Yields:
        The active model span.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("model_call") as current:
        _set_attrs(
            current,
            {
                GEN_AI_SYSTEM: _SYSTEM_AZURE_OPENAI,
                GEN_AI_OPERATION_NAME: "chat",
                GEN_AI_REQUEST_MODEL: deployment,
                APP_MODEL_ALIAS: alias,
                APP_PROMPT_ID: prompt_id,
                APP_PROMPT_VERSION: prompt_version,
            },
        )
        try:
            yield current
        except Exception as exc:  # noqa: BLE001
            _record_exception(current, exc)
            raise


@contextmanager
def tool_call_span(
    name: str,
    mcp_server: str,
    args: dict[str, Any] | None = None,
    expected_tool: str | None = None,
) -> "Iterator[Span]":
    """Open a ``tool`` span and, when ``expected_tool`` is given, record correctness.

    This span is the source of the tool-selection evaluation metric: if the orchestrator
    knows which tool *should* have been chosen for a golden case, ``eval.was_correct_tool``
    captures whether the agent picked it.

    Args:
        name: The tool actually invoked.
        mcp_server: The MCP server / provider hosting the tool.
        args: Tool arguments (recorded as a string; keep them non-sensitive).
        expected_tool: The tool the golden case expects, if evaluating.

    Yields:
        The active tool span.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("tool_call") as current:
        attrs: dict[str, Any] = {
            GEN_AI_TOOL_NAME: name,
            APP_MCP_SERVER: mcp_server,
        }
        if args is not None:
            attrs["app.tool.args"] = str(args)
        if expected_tool is not None:
            attrs[EVAL_EXPECTED_TOOL] = expected_tool
            attrs[EVAL_WAS_CORRECT_TOOL] = name == expected_tool
        _set_attrs(current, attrs)
        try:
            yield current
        except Exception as exc:  # noqa: BLE001
            _record_exception(current, exc)
            raise


def set_model_usage(
    current: "Span",
    *,
    input_tokens: int,
    output_tokens: int,
    finish_reason: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """Record GenAI usage attributes on an open model span.

    Args:
        current: The span returned by :func:`model_call_span`.
        input_tokens: Prompt tokens consumed.
        output_tokens: Completion tokens produced.
        finish_reason: The response finish reason, if any.
        latency_ms: Wall-clock latency of the call, if measured.
    """
    _set_attrs(
        current,
        {
            GEN_AI_USAGE_INPUT_TOKENS: input_tokens,
            GEN_AI_USAGE_OUTPUT_TOKENS: output_tokens,
            GEN_AI_RESPONSE_FINISH_REASONS: [finish_reason] if finish_reason else None,
            APP_LATENCY_MS: latency_ms,
        },
    )


# ---------------------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------------------
def _set_attrs(current: "Span", attrs: dict[str, Any]) -> None:
    """Set non-``None`` attributes on a span, tolerating no-op spans."""
    setter = getattr(current, "set_attribute", None)
    if setter is None:
        return
    for key, value in attrs.items():
        if value is None:
            continue
        setter(key, value)


def _record_exception(current: "Span", exc: BaseException) -> None:
    """Record an exception and mark the span as errored, if supported."""
    recorder = getattr(current, "record_exception", None)
    if recorder is not None:
        recorder(exc)
    if _OTEL_AVAILABLE and Status is not None:
        status_setter = getattr(current, "set_status", None)
        if status_setter is not None:
            status_setter(Status(StatusCode.ERROR, str(exc)))


class _NoOpSpan:
    """Minimal stand-in span used when OpenTelemetry is not installed."""

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: D102
        return None

    def record_exception(self, exc: BaseException) -> None:  # noqa: D102
        return None

    def set_status(self, *args: Any, **kwargs: Any) -> None:  # noqa: D102
        return None

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _NoOpTracer:
    """Tracer that yields :class:`_NoOpSpan` instances."""

    @contextmanager
    def start_as_current_span(self, name: str) -> Iterator[_NoOpSpan]:  # noqa: D102
        yield _NoOpSpan()
