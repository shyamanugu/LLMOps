"""Observability: OpenTelemetry tracing, cost attribution, and exporters.

Everything the platform does is observable. A single request produces a trace whose spans
nest ``request > agent > model|tool``. Spans carry GenAI semantic-convention attributes
(model, tokens, finish reason) plus platform extensions (``app.cost_usd``,
``eval.was_correct_tool``). Traces are exported to Azure Application Insights and Langfuse.

Public surface:
    init_tracing, get_tracer, span, model_call_span, tool_call_span   (tracing.py)
    attach_cost, aggregate_costs                                       (cost.py)
    configure_exporters                                               (exporters.py)
"""

from __future__ import annotations

from llmops.observability.cost import aggregate_costs, attach_cost
from llmops.observability.tracing import (
    get_tracer,
    init_tracing,
    model_call_span,
    span,
    tool_call_span,
)

__all__ = [
    "init_tracing",
    "get_tracer",
    "span",
    "model_call_span",
    "tool_call_span",
    "attach_cost",
    "aggregate_costs",
]
