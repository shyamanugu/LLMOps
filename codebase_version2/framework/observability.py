"""Observability — record what happened on every request and step.

Every model call and tool call is recorded with tokens, cost, and latency, tied to one request id
(a trace). Offline this prints structured lines to the console. If Langfuse is configured, the same
records also go there for dashboards. This is how we can follow a bad answer back to the exact step
and see cost per request.
"""

import json
import time
import uuid
from contextlib import contextmanager

from framework import config

# The current request id (trace). Set once per request via start_trace().
_current_trace = {"id": None}


def start_trace(use_case: str = "") -> str:
    """Begin a new request trace and return its id."""
    _current_trace["id"] = uuid.uuid4().hex
    _emit("trace_start", use_case=use_case)
    return _current_trace["id"]


@contextmanager
def span(name: str, **attrs):
    """Record a step (a span) with a name and attributes; times it."""
    start = time.time()
    try:
        yield
    finally:
        _emit("span", name=name, latency_ms=int((time.time() - start) * 1000), **attrs)


def record_model_call(alias, model, tokens_in, tokens_out, cost_usd, latency_ms, prompt_id=None, **_):
    """Record one model call (called by model_management.chat)."""
    _emit(
        "model_call",
        alias=alias,
        model=model,
        prompt_id=prompt_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
    )


def record_tool_call(name, ok, latency_ms, expected_tool=None, **attrs):
    """Record one tool call. expected_tool (if given) lets evaluation check tool selection."""
    _emit(
        "tool_call",
        name=name,
        ok=ok,
        latency_ms=latency_ms,
        expected_tool=expected_tool,
        was_correct_tool=(None if expected_tool is None else name == expected_tool),
        **attrs,
    )


def _emit(kind: str, **fields):
    """Write one structured record. Console by default; Langfuse too if configured."""
    record = {"trace_id": _current_trace["id"], "kind": kind, **fields}
    print(json.dumps(record))  # structured line -> App Insights / Log Analytics in Azure
    if config.LANGFUSE_HOST:
        _send_langfuse(record)


def _send_langfuse(record: dict) -> None:
    """Send the record to Langfuse (self-hosted) for LLM dashboards."""
    # TODO(wiring): construct the Langfuse client from config and forward the record.
    # from langfuse import Langfuse; Langfuse(host=..., public_key=..., secret_key=...).event(...)
    pass
