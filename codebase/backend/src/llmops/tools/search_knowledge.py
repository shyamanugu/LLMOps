"""``search_knowledge`` tool — retrieval-augmented knowledge search over RAG.

Wraps :class:`~llmops.data_access.rag.RagRetriever` so an agent can pull grounding context from
the knowledge base. The tool output is a list of chunk mappings (id, text, score, source) which
the model can cite.
"""

from __future__ import annotations

from typing import ClassVar, cast

from pydantic import BaseModel, ConfigDict, Field

from llmops.common.types import ToolResult
from llmops.data_access.rag import DEFAULT_TOP_K, RagRetriever
from llmops.tools.base import Tool


class SearchKnowledgeArgs(BaseModel):
    """Arguments for the ``search_knowledge`` tool."""

    query: str = Field(description="The natural-language query to search the knowledge base for.")
    k: int = Field(default=DEFAULT_TOP_K, ge=1, le=50, description="Number of chunks to return.")


class SearchKnowledgeTool(Tool):
    """Search the knowledge base (RAG) and return the most relevant chunks."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "search_knowledge"
    description: str = "Search the knowledge base for passages relevant to a query and return ranked chunks."
    mcp_server: str = "llmops.knowledge"
    input_schema: ClassVar[type[BaseModel]] = SearchKnowledgeArgs

    retriever: RagRetriever = Field(default_factory=lambda: RagRetriever(index="knowledge"))

    async def _run(self, payload: BaseModel) -> ToolResult:
        """Retrieve chunks for the requested query."""
        args = cast(SearchKnowledgeArgs, payload)
        chunks = await self.retriever.retrieve(args.query, args.k)
        return ToolResult(name=self.name, ok=True, output=[c.model_dump() for c in chunks])
