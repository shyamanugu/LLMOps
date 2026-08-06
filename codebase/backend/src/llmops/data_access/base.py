"""Data-access abstraction — the :class:`DataSource` protocol.

Every retrieval backend (RAG index, SQL warehouse, document service, system of record) is
exposed to the rest of the platform through this single, minimal protocol. Orchestration and
tools depend on the protocol, never on a concrete Azure SDK — the classic dependency-inversion
seam that keeps the framework portable and testable.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DataSource(Protocol):
    """A queryable data backend.

    Implementations wrap a concrete service (Azure AI Search, a SQL database, Document
    Intelligence, an ERP/CRM) and expose a uniform async ``query`` entry point. Richer,
    type-specific methods (e.g. ``retrieve`` on the RAG source) are provided in addition to
    ``query`` for callers that need them.
    """

    #: Stable identifier for logs, spans, and the tool registry.
    name: str

    async def query(self, q: str, **kwargs: Any) -> Any:
        """Execute a query against the backend.

        Args:
            q: The query string (natural language, SQL, an id, or a search term depending on
                the concrete source).
            **kwargs: Source-specific options (e.g. ``k`` for RAG top-k).

        Returns:
            A source-specific result payload.
        """
        ...
