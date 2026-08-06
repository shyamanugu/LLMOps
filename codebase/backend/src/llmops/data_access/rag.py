"""RAG retriever over Azure AI Search.

Retrieves the top-``k`` most relevant knowledge :class:`~llmops.common.types.Chunk` objects for
a query. The production path uses `azure-search-documents`_ with hybrid (vector + keyword)
search and, ideally, semantic ranking. In dev (no ``azure_search_endpoint``) it returns a small
deterministic mock so pipelines and tools run end-to-end locally.

.. _azure-search-documents: https://learn.microsoft.com/azure/search/
"""

from __future__ import annotations

from typing import Any

from llmops.common.logging import get_logger
from llmops.common.types import Chunk
from llmops.config.settings import Settings, get_settings

_logger = get_logger(__name__)

DEFAULT_TOP_K = 5


class RagRetriever:
    """Retrieve knowledge chunks from an Azure AI Search index.

    Args:
        index: The search index name to query.
        search_endpoint: Azure AI Search endpoint. Falls back to ``settings.azure_search_endpoint``.
        settings: Platform settings. Defaults to the process singleton.
        vector_field: Name of the vector field for hybrid search.
        semantic_config: Optional semantic ranking configuration name.
    """

    name = "rag"

    def __init__(
        self,
        index: str,
        *,
        search_endpoint: str | None = None,
        settings: Settings | None = None,
        vector_field: str = "contentVector",
        semantic_config: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._index = index
        self._endpoint = search_endpoint or self._settings.azure_search_endpoint
        self._vector_field = vector_field
        self._semantic_config = semantic_config
        self._client: Any | None = None

    @property
    def _enabled(self) -> bool:
        """Whether a live search endpoint is configured (otherwise the dev mock is used)."""
        return bool(self._endpoint)

    def _get_client(self) -> Any | None:
        """Lazily construct the async ``SearchClient``, or ``None`` in dev."""
        if not self._enabled:
            return None
        if self._client is not None:
            return self._client
        # TODO(wiring): construct SearchClient from settings / managed identity, e.g.
        #   from azure.search.documents.aio import SearchClient
        #   from azure.identity.aio import DefaultAzureCredential
        #   self._client = SearchClient(self._endpoint, self._index, DefaultAzureCredential())
        raise NotImplementedError(
            "TODO(wiring): construct azure.search.documents.aio.SearchClient from settings"
        )

    async def retrieve(self, query: str, k: int = DEFAULT_TOP_K) -> list[Chunk]:
        """Return the top-``k`` chunks most relevant to ``query``.

        Args:
            query: The natural-language query.
            k: Number of chunks to return.

        Returns:
            A ranked list of :class:`~llmops.common.types.Chunk` (highest score first).
        """
        client = self._get_client()
        if client is None:
            return self._mock_retrieve(query, k)

        # TODO(wiring): embed the query, run hybrid search, and map results, e.g.
        #   results = await client.search(search_text=query,
        #       vector_queries=[VectorizedQuery(vector=..., fields=self._vector_field, k=k)],
        #       query_type="semantic", semantic_configuration_name=self._semantic_config, top=k)
        #   return [Chunk(id=r["id"], text=r["content"], score=r["@search.score"]) async for r in results]
        raise NotImplementedError("TODO(wiring): call SearchClient.search and map to Chunk")

    async def query(self, q: str, **kwargs: Any) -> list[Chunk]:
        """:class:`DataSource` entry point — alias for :meth:`retrieve`."""
        k = int(kwargs.get("k", DEFAULT_TOP_K))
        return await self.retrieve(q, k)

    def _mock_retrieve(self, query: str, k: int) -> list[Chunk]:
        """Deterministic dev mock so local pipelines have retrieval output."""
        _logger.debug("rag dev mock", index=self._index, k=k)
        return [
            Chunk(
                id=f"mock-{self._index}-{i}",
                text=f"[dev mock chunk {i}] relevant context for query: {query!r}",
                score=round(1.0 - i * 0.1, 3),
                source=f"mock://{self._index}/doc{i}",
                metadata={"mock": True},
            )
            for i in range(min(k, 3))
        ]
