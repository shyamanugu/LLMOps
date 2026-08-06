"""``query_sql`` tool — natural-language querying of a relational database.

Wraps :class:`~llmops.data_access.sql.SqlDataSource`, which performs NL2SQL and then executes a
*safe*, read-only, allow-listed ``SELECT``. The tool never lets a write reach the database.
"""

from __future__ import annotations

from typing import ClassVar, cast

from pydantic import BaseModel, ConfigDict, Field

from llmops.common.types import ToolResult
from llmops.data_access.sql import SqlDataSource
from llmops.tools.base import Tool


class QuerySqlArgs(BaseModel):
    """Arguments for the ``query_sql`` tool."""

    question: str = Field(description="The natural-language question to answer from the database.")
    schema_hint: str | None = Field(default=None, description="Optional schema/DDL hint to ground NL2SQL.")


class QuerySqlTool(Tool):
    """Answer a natural-language question with a safe, read-only SQL query."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "query_sql"
    description: str = "Answer a question by generating and safely executing a read-only SQL query."
    mcp_server: str = "llmops.sql"
    input_schema: ClassVar[type[BaseModel]] = QuerySqlArgs

    source: SqlDataSource = Field(default_factory=lambda: SqlDataSource(allowed_tables=[]))

    async def _run(self, payload: BaseModel) -> ToolResult:
        """Run NL2SQL then a safe read-only execution."""
        args = cast(QuerySqlArgs, payload)
        rows = await self.source.query(args.question, schema_hint=args.schema_hint)
        return ToolResult(name=self.name, ok=True, output=rows)
