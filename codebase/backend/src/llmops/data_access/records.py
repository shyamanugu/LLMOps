"""Records client — fetch a single record from a system of record.

A thin, uniform adapter over external systems (CRM, ERP, ATS, ticketing, ...). Each *system*
is identified by a short key (e.g. ``"crm"``, ``"ats"``) mapped to a base URL / connector.
``get_record(system, id)`` returns a normalised :class:`Record`. Live HTTP/SDK wiring is marked
``# TODO(wiring)``; dev returns a deterministic mock.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from llmops.common.errors import ToolError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings

_logger = get_logger(__name__)


class Record(BaseModel):
    """A normalised record fetched from a system of record."""

    system: str
    id: str
    data: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None


class RecordClient:
    """Fetch records from configured systems of record.

    Args:
        systems: Mapping of ``system key -> base URL / connector string``. When empty, the
            client operates in dev-mock mode.
        settings: Platform settings. Defaults to the process singleton.
    """

    name = "records"

    def __init__(self, systems: dict[str, str] | None = None, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._systems = systems or {}
        self._http: Any | None = None

    async def get_record(self, system: str, id: str) -> Record:  # noqa: A002 - matches spec signature
        """Fetch a single record identified by ``id`` from ``system``.

        Args:
            system: The system key (must be configured unless in dev-mock mode).
            id: The record identifier within that system.

        Returns:
            A :class:`Record`.

        Raises:
            ToolError: If ``system`` is unknown while systems are configured.
        """
        if not self._systems:
            return self._mock_record(system, id)

        base_url = self._systems.get(system)
        if base_url is None:
            raise ToolError(
                f"unknown system of record: {system!r}",
                detail={"system": system, "known": list(self._systems)},
            )

        # TODO(wiring): construct an authenticated httpx.AsyncClient (managed identity / API key
        #   from Key Vault) and GET f"{base_url}/records/{id}", then map the payload onto Record.
        raise NotImplementedError("TODO(wiring): call the system-of-record connector and map to Record")

    async def query(self, q: str, **kwargs: Any) -> Record:
        """:class:`DataSource` entry point — ``q`` is the record id; ``system`` via kwargs."""
        system = str(kwargs.get("system", "default"))
        return await self.get_record(system, q)

    def _mock_record(self, system: str, id: str) -> Record:
        """Deterministic dev mock so local pipelines have a record to work with."""
        _logger.debug("records dev mock", system=system, id=id)
        return Record(
            system=system,
            id=id,
            data={"id": id, "status": "mock", "name": f"Mock record {id}"},
            source=f"mock://{system}/{id}",
        )
