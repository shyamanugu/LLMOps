"""Tool registry — the platform's MCP-compatible tool catalog.

The registry maps tool *names* to concrete :class:`~llmops.tools.base.Tool` instances. It is
seeded from the built-in tool set and enriched from ``platform/tools/registry.yaml`` (descriptions
and MCP-server attribution), so tool metadata is config-as-code and reviewable in a pull request.
If the YAML is missing (fresh checkout) the registry still works with the built-in defaults.

Typical usage::

    registry = ToolRegistry.from_config()
    tool = registry.get("search_knowledge")
    result = await tool.run(query="reset my password", k=3)
    mcp_descriptions = registry.list_mcp()   # feed to an MCP-aware model client
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmops.common.errors import ConfigError, ToolError
from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.tools.base import Tool
from llmops.tools.extract_document import ExtractDocumentTool
from llmops.tools.get_record import GetRecordTool
from llmops.tools.query_sql import QuerySqlTool
from llmops.tools.search_knowledge import SearchKnowledgeTool

_logger = get_logger(__name__)

#: Default registry path relative to the repo root.
DEFAULT_REGISTRY_PATH = "platform/tools/registry.yaml"


def _builtin_tools() -> dict[str, Tool]:
    """Construct the built-in tool instances keyed by name."""
    tools: list[Tool] = [
        SearchKnowledgeTool(),
        QuerySqlTool(),
        ExtractDocumentTool(),
        GetRecordTool(),
    ]
    return {t.name: t for t in tools}


class ToolRegistry:
    """A name-indexed catalog of tools with MCP-compatible descriptions.

    Args:
        tools: Initial tools keyed by name. Defaults to the built-in set.
    """

    def __init__(self, tools: dict[str, Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = tools if tools is not None else _builtin_tools()

    @classmethod
    def from_config(
        cls,
        path: str | Path | None = None,
        *,
        settings: Settings | None = None,
    ) -> ToolRegistry:
        """Build a registry from the built-in tools, enriched by ``registry.yaml``.

        Args:
            path: Path to ``registry.yaml``. Defaults to :data:`DEFAULT_REGISTRY_PATH`.
            settings: Platform settings (unused today; reserved for per-env tool config).

        Returns:
            A populated :class:`ToolRegistry`.
        """
        _ = settings or get_settings()
        registry = cls(_builtin_tools())
        registry._apply_yaml(Path(path) if path else Path(DEFAULT_REGISTRY_PATH))
        return registry

    def _apply_yaml(self, path: Path) -> None:
        """Overlay descriptions / mcp_server attribution from ``registry.yaml`` if present."""
        if not path.exists():
            _logger.info("tools registry.yaml not found; using built-in defaults", path=str(path))
            return
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"failed to parse tools registry: {exc}", detail={"path": str(path)}) from exc

        for entry in raw.get("tools", []):
            name = entry.get("name")
            tool = self._tools.get(name) if name else None
            if tool is None:
                _logger.warning("registry.yaml references unknown tool; skipping", tool=name)
                continue
            if "description" in entry:
                tool.description = entry["description"]
            if "mcp_server" in entry:
                tool.mcp_server = entry["mcp_server"]

    def register(self, tool: Tool) -> None:
        """Add or replace a tool in the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Return the tool registered under ``name``.

        Raises:
            ToolError: If no such tool exists.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise ToolError(
                f"unknown tool: {name!r}",
                detail={"name": name, "known": sorted(self._tools)},
            )
        return tool

    def names(self) -> list[str]:
        """Return the sorted names of all registered tools."""
        return sorted(self._tools)

    def list_tools(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def list_mcp(self) -> list[dict[str, Any]]:
        """Return MCP-compatible descriptions for every registered tool."""
        return [t.to_mcp() for t in self._tools.values()]
