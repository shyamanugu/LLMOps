"""Structured, JSON-friendly logging for the platform.

We never use ``print``. Logs are emitted as key=value structured records so they are
queryable in Azure Log Analytics. In production the OpenTelemetry logging exporter
(configured in ``llmops.observability.exporters``) ships these to Application Insights,
and each record is automatically correlated with the active trace/span.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

_CONFIGURED = False


class _KeyValueFormatter(logging.Formatter):
    """Render records as ``ts level logger msg key=value ...``."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        base = f"{self.formatTime(record)} {record.levelname:<7} {record.name} {record.getMessage()}"
        extra = getattr(record, "context", None)
        if extra:
            kv = " ".join(f"{k}={v!r}" for k, v in extra.items())
            base = f"{base} {kv}"
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger once. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_KeyValueFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    _CONFIGURED = True


class _ContextLogger(logging.LoggerAdapter):
    """Logger adapter that lets callers pass structured context via ``**kwargs``."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        context = kwargs.pop("context", {})
        # allow logger.info("msg", trace_id=..., cost=...) style
        reserved = {"exc_info", "stack_info", "stacklevel", "extra"}
        loose = {k: kwargs.pop(k) for k in list(kwargs) if k not in reserved}
        context = {**context, **loose}
        kwargs.setdefault("extra", {})["context"] = context
        return msg, kwargs


def get_logger(name: str) -> _ContextLogger:
    """Return a context-aware logger for ``name`` (usually ``__name__``)."""
    if not _CONFIGURED:
        configure_logging()
    return _ContextLogger(logging.getLogger(name), {})
