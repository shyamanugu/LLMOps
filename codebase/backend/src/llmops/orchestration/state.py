"""Pipeline state persistence — checkpoint / resume.

A long-running pipeline can checkpoint its :class:`PipelineState` after each step so a crashed or
interrupted run can be resumed. The production store is Azure Cosmos DB; an in-memory store is the
default for dev and tests. Both implement the :class:`StateStore` protocol (dependency inversion),
and the Cosmos adapter's client construction is marked ``# TODO(wiring)``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings

_logger = get_logger(__name__)


class RunStatus(str, Enum):
    """Lifecycle status of a pipeline run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineState(BaseModel):
    """Persisted state of a pipeline run (a Cosmos document).

    Attributes:
        trace_id: Correlation id / document id.
        pipeline: Pipeline name.
        status: Current run status.
        current_step: Index of the next step to execute (for resume).
        completed_steps: Names of steps already completed.
        memory: Snapshot of the shared blackboard.
        error: Error message if the run failed.
        updated_at: Last-update timestamp (UTC).
    """

    trace_id: str
    pipeline: str
    status: RunStatus = RunStatus.PENDING
    current_step: int = 0
    completed_steps: list[str] = Field(default_factory=list)
    memory: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def touch(self) -> None:
        """Refresh :attr:`updated_at` to now (UTC)."""
        self.updated_at = datetime.now(UTC)


@runtime_checkable
class StateStore(Protocol):
    """Persistence backend for :class:`PipelineState`."""

    async def save(self, state: PipelineState) -> None:
        """Persist (upsert) ``state``."""
        ...

    async def load(self, trace_id: str) -> PipelineState | None:
        """Load the state for ``trace_id``, or ``None`` if absent."""
        ...


class InMemoryStateStore:
    """Non-durable state store for dev and tests."""

    def __init__(self) -> None:
        self._states: dict[str, PipelineState] = {}

    async def save(self, state: PipelineState) -> None:
        """Store a deep copy of ``state`` keyed by trace id."""
        state.touch()
        self._states[state.trace_id] = state.model_copy(deep=True)

    async def load(self, trace_id: str) -> PipelineState | None:
        """Return a copy of the stored state, or ``None``."""
        found = self._states.get(trace_id)
        return found.model_copy(deep=True) if found else None


class CosmosStateStore:
    """Durable state store backed by Azure Cosmos DB.

    Args:
        settings: Platform settings (endpoint + database). Defaults to the process singleton.
        container: Cosmos container name for pipeline state documents.
    """

    def __init__(self, settings: Settings | None = None, *, container: str = "pipeline_state") -> None:
        self._settings = settings or get_settings()
        self._container_name = container
        self._container: Any | None = None

    def _get_container(self) -> Any | None:
        """Lazily construct the Cosmos container client, or ``None`` in dev."""
        if not self._settings.cosmos_endpoint:
            return None
        if self._container is not None:
            return self._container
        # TODO(wiring): construct CosmosClient from settings / managed identity, e.g.
        #   from azure.cosmos.aio import CosmosClient
        #   from azure.identity.aio import DefaultAzureCredential
        #   client = CosmosClient(self._settings.cosmos_endpoint, DefaultAzureCredential())
        #   db = client.get_database_client(self._settings.cosmos_database)
        #   self._container = db.get_container_client(self._container_name)
        raise NotImplementedError("TODO(wiring): construct azure.cosmos.aio CosmosClient from settings")

    async def save(self, state: PipelineState) -> None:
        """Upsert the state document into Cosmos (no-op warning in dev)."""
        container = self._get_container()
        if container is None:
            _logger.debug("cosmos state store dev no-op (save)", trace_id=state.trace_id)
            return
        state.touch()
        # TODO(wiring): await container.upsert_item(
        #   body={**state.model_dump(mode="json"), "id": state.trace_id})
        raise NotImplementedError("TODO(wiring): call container.upsert_item")

    async def load(self, trace_id: str) -> PipelineState | None:
        """Read the state document from Cosmos (returns ``None`` in dev)."""
        container = self._get_container()
        if container is None:
            _logger.debug("cosmos state store dev no-op (load)", trace_id=trace_id)
            return None
        # TODO(wiring): item = await container.read_item(item=trace_id, partition_key=trace_id)
        #   return PipelineState.model_validate(item)
        raise NotImplementedError("TODO(wiring): call container.read_item")


def default_state_store(settings: Settings | None = None) -> StateStore:
    """Return a durable store when Cosmos is configured, else the in-memory store."""
    cfg = settings or get_settings()
    if cfg.cosmos_endpoint:
        return CosmosStateStore(cfg)
    return InMemoryStateStore()
