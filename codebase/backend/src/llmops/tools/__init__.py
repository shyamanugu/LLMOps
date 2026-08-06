"""Reusable, MCP-compatible tool catalog.

Public surface:
    * :class:`Tool` — the tool base class (``base``).
    * :class:`ToolRegistry` — the name-indexed catalog (``registry``).
    * Built-in tools: :class:`SearchKnowledgeTool`, :class:`QuerySqlTool`,
      :class:`ExtractDocumentTool`, :class:`GetRecordTool`.

Tools wrap the data-access layer so orchestration never touches an Azure SDK directly, and each
tool exposes an MCP description via :meth:`Tool.to_mcp`.
"""

from llmops.tools.base import Tool
from llmops.tools.extract_document import ExtractDocumentTool
from llmops.tools.get_record import GetRecordTool
from llmops.tools.query_sql import QuerySqlTool
from llmops.tools.registry import ToolRegistry
from llmops.tools.search_knowledge import SearchKnowledgeTool

__all__ = [
    "Tool",
    "ToolRegistry",
    "SearchKnowledgeTool",
    "QuerySqlTool",
    "ExtractDocumentTool",
    "GetRecordTool",
]
