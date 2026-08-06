"""``extract_document`` tool — structured extraction from documents.

Wraps :class:`~llmops.data_access.documents.DocumentExtractor` (Azure AI Document Intelligence).
Accepts base64-encoded document bytes so the tool is transport-agnostic (MCP/JSON friendly).
"""

from __future__ import annotations

import base64
import binascii
from typing import ClassVar, cast

from pydantic import BaseModel, ConfigDict, Field

from llmops.common.types import ToolResult
from llmops.data_access.documents import DocumentExtractor
from llmops.tools.base import Tool


class ExtractDocumentArgs(BaseModel):
    """Arguments for the ``extract_document`` tool."""

    content_base64: str = Field(description="Base64-encoded document bytes.")
    content_type: str = Field(default="application/pdf", description="Document MIME type.")


class ExtractDocumentTool(Tool):
    """Extract text, tables, and key/value pairs from a document."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "extract_document"
    description: str = "Extract structured content (text, tables, key/value pairs) from a document."
    mcp_server: str = "llmops.documents"
    input_schema: ClassVar[type[BaseModel]] = ExtractDocumentArgs

    extractor: DocumentExtractor = Field(default_factory=DocumentExtractor)

    async def _run(self, payload: BaseModel) -> ToolResult:
        """Decode the document and run extraction."""
        args = cast(ExtractDocumentArgs, payload)
        try:
            content = base64.b64decode(args.content_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            return ToolResult(name=self.name, ok=False, error=f"invalid base64 content: {exc}")
        doc = await self.extractor.extract(content, content_type=args.content_type)
        return ToolResult(name=self.name, ok=True, output=doc.model_dump())
