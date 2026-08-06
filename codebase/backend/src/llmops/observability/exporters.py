"""Exporter wiring for Application Insights and Langfuse.

Two sinks receive traces:

* **Azure Application Insights** via ``azure-monitor-opentelemetry`` — the operational
  home for latency, cost, and reliability dashboards.
* **Langfuse** — LLM-native trace viewing (prompt, completion, scores) for debugging and
  evaluation review.

Both are wired here and guarded so the platform runs cleanly in dev with neither
configured: the functions become logged no-ops rather than raising.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from llmops.common.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - typing only
    from opentelemetry.sdk.trace import TracerProvider

logger = get_logger(__name__)


def configure_exporters(settings: Any, provider: "TracerProvider") -> None:
    """Attach span processors/exporters to ``provider`` based on ``settings``.

    Args:
        settings: Platform settings carrying connection strings and Langfuse keys.
        provider: The OpenTelemetry ``TracerProvider`` to configure.
    """
    _configure_app_insights(settings, provider)
    _configure_langfuse(settings, provider)


def _configure_app_insights(settings: Any, provider: "TracerProvider") -> None:
    """Wire the Azure Monitor (Application Insights) exporter, or no-op in dev."""
    conn = getattr(settings, "applicationinsights_connection_string", "")
    if not conn:
        logger.info("app insights connection string absent; skipping azure monitor exporter")
        return
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        # TODO(wiring): confirm the connection string is sourced from Key Vault via Managed
        # Identity in Azure rather than an env var, and add sampling config if needed.
        exporter = AzureMonitorTraceExporter(connection_string=conn)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("azure monitor trace exporter configured")
    except Exception as exc:  # noqa: BLE001 - never let telemetry wiring break startup
        logger.warning("failed to configure azure monitor exporter", error=str(exc))


def _configure_langfuse(settings: Any, provider: "TracerProvider") -> None:
    """Wire the Langfuse OTel exporter, or no-op in dev."""
    if not (getattr(settings, "langfuse_host", "") and getattr(settings, "langfuse_secret_key", "")):
        logger.info("langfuse not configured; skipping langfuse exporter")
        return
    try:
        # TODO(wiring): construct the Langfuse OpenTelemetry exporter from settings, e.g.
        #   from langfuse.opentelemetry import LangfuseSpanExporter
        #   from opentelemetry.sdk.trace.export import BatchSpanProcessor
        #   exporter = LangfuseSpanExporter(host=settings.langfuse_host,
        #                                   public_key=settings.langfuse_public_key,
        #                                   secret_key=settings.langfuse_secret_key)
        #   provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.warning("langfuse exporter wiring not implemented; skipping")
    except Exception as exc:  # noqa: BLE001
        logger.warning("failed to configure langfuse exporter", error=str(exc))
