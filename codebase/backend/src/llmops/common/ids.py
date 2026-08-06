"""Identifier helpers.

Trace and span identifiers are UUID4 hex strings so they are globally unique and safe to
put in URLs, logs, and correlation headers.
"""

from __future__ import annotations

import uuid


def new_trace_id() -> str:
    """Return a new 32-char hex trace id (one per inbound request/pipeline run)."""
    return uuid.uuid4().hex


def new_span_id() -> str:
    """Return a new 16-char hex span id (one per step within a trace)."""
    return uuid.uuid4().hex[:16]


def new_id(prefix: str = "") -> str:
    """Return a short unique id, optionally prefixed (e.g. ``fb_...`` for feedback)."""
    core = uuid.uuid4().hex[:12]
    return f"{prefix}{core}" if prefix else core
