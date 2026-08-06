"""Feedback persistence — Application Insights custom events + Cosmos DB.

Feedback is written to two sinks:
    * **Application Insights** as a ``Feedback`` *custom event* so it shows up alongside
      traces/metrics for correlation and dashboarding.
    * **Cosmos DB** as the durable system-of-record queried by the console and the
      golden-candidate promotion job.

Both live clients are wired from :class:`~llmops.config.settings.Settings` using Managed
Identity. Until that wiring is present (or in local dev), the store transparently falls
back to an in-memory list so the API and tests work end-to-end without Azure.
"""

from __future__ import annotations

from typing import Protocol

from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.feedback.models import FeedbackEvent

_log = get_logger(__name__)


class FeedbackSink(Protocol):
    """Structural type for a feedback persistence backend."""

    async def save(self, event: FeedbackEvent) -> None:
        """Persist a single event."""
        ...

    async def list_recent(self, *, usecase: str | None = None, limit: int = 100) -> list[FeedbackEvent]:
        """Return recent events, most-recent first."""
        ...


class InMemoryFeedbackSink:
    """Process-local sink used in dev/tests. Not durable."""

    def __init__(self) -> None:
        """Initialise an empty in-memory event buffer."""
        self._events: list[FeedbackEvent] = []

    async def save(self, event: FeedbackEvent) -> None:
        """Append the event to the in-memory buffer."""
        self._events.append(event)

    async def list_recent(self, *, usecase: str | None = None, limit: int = 100) -> list[FeedbackEvent]:
        """Return the most recent events (optionally filtered by use-case)."""
        items = [e for e in self._events if usecase is None or e.usecase == usecase]
        return list(reversed(items))[:limit]


class FeedbackStore:
    """Facade over the feedback sinks with graceful dev degradation.

    In production ``save`` fans out to App Insights (custom event) and Cosmos; reads come
    from Cosmos. When neither client can be constructed, an in-memory sink is used and a
    single warning is logged.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise the store, constructing live clients when configured."""
        self._settings = settings or get_settings()
        self._memory = InMemoryFeedbackSink()
        self._cosmos = self._init_cosmos()
        self._telemetry = self._init_telemetry()

    def _init_cosmos(self) -> object | None:
        """Construct the Cosmos client, or ``None`` for the in-memory fallback."""
        if not self._settings.cosmos_endpoint:
            _log.warning("cosmos_endpoint unset; feedback persisted in-memory only (dev)")
            return None
        try:
            # TODO(wiring): construct azure.cosmos.aio.CosmosClient from cosmos_endpoint
            # using DefaultAzureCredential (Managed Identity), select database/container.
            raise NotImplementedError("TODO(wiring): Cosmos client construction")
        except Exception as exc:  # noqa: BLE001
            _log.warning("cosmos client unavailable; using in-memory sink", error=str(exc))
            return None

    def _init_telemetry(self) -> object | None:
        """Construct the App Insights telemetry client, or ``None`` in dev."""
        if not self._settings.applicationinsights_connection_string:
            _log.warning("app insights unset; feedback custom events disabled (dev)")
            return None
        try:
            # TODO(wiring): emit a 'Feedback' custom event via the OpenTelemetry logger /
            # azure-monitor exporter configured in llmops.observability.exporters.
            raise NotImplementedError("TODO(wiring): App Insights custom-event emitter")
        except Exception as exc:  # noqa: BLE001
            _log.warning("app insights emitter unavailable", error=str(exc))
            return None

    async def save(self, event: FeedbackEvent) -> None:
        """Persist an event to all configured sinks (always to memory as a mirror).

        Args:
            event: The feedback event to persist.
        """
        await self._memory.save(event)
        if self._telemetry is not None:
            # TODO(wiring): telemetry.track_event("Feedback", event.model_dump(mode="json"))
            pass
        if self._cosmos is not None:
            # TODO(wiring): await container.upsert_item(event.model_dump(mode="json"))
            pass
        _log.info(
            "feedback stored",
            feedback_id=event.id,
            trace_id=event.trace_id,
            kind=event.kind.value,
            durable=self._cosmos is not None,
        )

    async def list_recent(self, *, usecase: str | None = None, limit: int = 100) -> list[FeedbackEvent]:
        """Return recent feedback events, most-recent first.

        Args:
            usecase: Optional use-case filter.
            limit: Maximum number of events to return.
        """
        if self._cosmos is not None:
            # TODO(wiring): query Cosmos ordered by ts desc with the usecase filter.
            pass
        return await self._memory.list_recent(usecase=usecase, limit=limit)
