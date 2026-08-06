"""``get_record`` tool — fetch a single record from a system of record.

Wraps :class:`~llmops.data_access.records.RecordClient`.
"""

from __future__ import annotations

from typing import ClassVar, cast

from pydantic import BaseModel, ConfigDict, Field

from llmops.common.types import ToolResult
from llmops.data_access.records import RecordClient
from llmops.tools.base import Tool


class GetRecordArgs(BaseModel):
    """Arguments for the ``get_record`` tool."""

    system: str = Field(description="The system-of-record key (e.g. 'crm', 'ats').")
    record_id: str = Field(description="The record identifier within that system.")


class GetRecordTool(Tool):
    """Fetch a single record from a configured system of record."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "get_record"
    description: str = "Fetch a single record by id from a named system of record (CRM/ERP/ATS/...)."
    mcp_server: str = "llmops.records"
    input_schema: ClassVar[type[BaseModel]] = GetRecordArgs

    client: RecordClient = Field(default_factory=RecordClient)

    async def _run(self, payload: BaseModel) -> ToolResult:
        """Fetch the requested record."""
        args = cast(GetRecordArgs, payload)
        record = await self.client.get_record(args.system, args.record_id)
        return ToolResult(name=self.name, ok=True, output=record.model_dump())
