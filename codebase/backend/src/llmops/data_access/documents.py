"""Document extraction via Azure AI Document Intelligence.

Turns a raw document (PDF, image, Office file) into a structured :class:`ExtractedDoc` — plain
text plus pages, tables, and key/value pairs — using `Azure AI Document Intelligence`_
(prebuilt-layout / prebuilt-document models). In dev (no endpoint) it returns a small mock so
downstream steps run locally.

.. _Azure AI Document Intelligence: https://learn.microsoft.com/azure/ai-services/document-intelligence/
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings

_logger = get_logger(__name__)


class ExtractedTable(BaseModel):
    """A table extracted from a document."""

    row_count: int = 0
    column_count: int = 0
    cells: list[dict[str, Any]] = Field(default_factory=list)


class ExtractedDoc(BaseModel):
    """Structured result of a document extraction.

    Attributes:
        content: The full extracted text content.
        pages: Per-page metadata (page number, dimensions, line counts).
        tables: Extracted tables.
        key_value_pairs: Extracted form fields as ``{label: value}``.
        model_id: The Document Intelligence model used.
        metadata: Free-form extraction metadata.
    """

    content: str = ""
    pages: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[ExtractedTable] = Field(default_factory=list)
    key_value_pairs: dict[str, str] = Field(default_factory=dict)
    model_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentExtractor:
    """Extract structured content from documents using Document Intelligence.

    Args:
        settings: Platform settings. Defaults to the process singleton.
        model_id: The prebuilt (or custom) model id to invoke.
    """

    name = "documents"

    def __init__(self, settings: Settings | None = None, *, model_id: str = "prebuilt-layout") -> None:
        self._settings = settings or get_settings()
        self._model_id = model_id
        self._client: Any | None = None

    @property
    def _enabled(self) -> bool:
        """Whether a live Document Intelligence endpoint is configured."""
        return bool(self._settings.document_intelligence_endpoint)

    def _get_client(self) -> Any | None:
        """Lazily construct the async ``DocumentIntelligenceClient``, or ``None`` in dev."""
        if not self._enabled:
            return None
        if self._client is not None:
            return self._client
        # TODO(wiring): construct DocumentIntelligenceClient from settings / managed identity, e.g.
        #   from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
        #   from azure.identity.aio import DefaultAzureCredential
        #   self._client = DocumentIntelligenceClient(endpoint, DefaultAzureCredential())
        raise NotImplementedError(
            "TODO(wiring): construct azure.ai.documentintelligence client from settings"
        )

    async def extract(self, content: bytes, *, content_type: str = "application/pdf") -> ExtractedDoc:
        """Extract structured content from ``content`` bytes.

        Args:
            content: Raw document bytes.
            content_type: MIME type of the document.

        Returns:
            An :class:`ExtractedDoc`.
        """
        client = self._get_client()
        if client is None:
            return self._mock_extract(content)

        # TODO(wiring): call begin_analyze_document(self._model_id, body=content, ...), await the
        #   poller, then map result.content / result.pages / result.tables / result.key_value_pairs
        #   onto ExtractedDoc.
        raise NotImplementedError("TODO(wiring): call Document Intelligence analyze and map result")

    def _mock_extract(self, content: bytes) -> ExtractedDoc:
        """Deterministic dev mock so local pipelines have an extraction result."""
        _logger.debug("document-intelligence dev mock", bytes=len(content))
        return ExtractedDoc(
            content=f"[dev mock] extracted {len(content)} bytes",
            pages=[{"page_number": 1, "lines": 1}],
            model_id=self._model_id,
            metadata={"mock": True},
        )
