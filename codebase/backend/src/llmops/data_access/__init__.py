"""Data-access layer — retrieval backends behind a uniform :class:`DataSource` protocol.

Public surface:
    * :class:`DataSource` — the protocol every backend implements (``base``).
    * :class:`RagRetriever` — Azure AI Search retrieval (``rag``).
    * :class:`SqlDataSource` — NL2SQL + safe read-only execution (``sql``).
    * :class:`DocumentExtractor` / :class:`ExtractedDoc` — Document Intelligence (``documents``).
    * :class:`RecordClient` / :class:`Record` — systems of record (``records``).

Adapters requiring live Azure clients degrade to deterministic dev mocks and are marked
``# TODO(wiring)``.
"""

from llmops.data_access.base import DataSource
from llmops.data_access.documents import DocumentExtractor, ExtractedDoc
from llmops.data_access.rag import RagRetriever
from llmops.data_access.records import Record, RecordClient
from llmops.data_access.sql import SqlDataSource, UnsafeSqlError

__all__ = [
    "DataSource",
    "RagRetriever",
    "SqlDataSource",
    "UnsafeSqlError",
    "DocumentExtractor",
    "ExtractedDoc",
    "RecordClient",
    "Record",
]
