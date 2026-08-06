"""Reusable tool catalog — the actions agents can take.

Build a tool once here and every use case reuses it. Each tool is a plain function plus a small
description (name + what it does + inputs). The description is enough to expose the tool over MCP
(Model Context Protocol) later without changing the tool code.

Included: search_knowledge (RAG), query_sql (structured data, read-only), get_record (systems).
"""

from framework import rag
from framework.observability import record_tool_call

# --- the tools ---------------------------------------------------------------------------------


def search_knowledge(usecase: str, query: str, k: int = 3) -> list[dict]:
    """Search our documents (RAG) and return the top matches."""
    with_span = rag.retrieve(usecase, query, k)
    record_tool_call("search_knowledge", ok=True, latency_ms=0, count=len(with_span))
    return with_span


def query_sql(question: str) -> list[dict]:
    """Answer a question from structured data. READ-ONLY and allow-listed (never writes)."""
    # TODO(wiring): turn `question` into a safe SELECT over allow-listed tables, run it read-only.
    record_tool_call("query_sql", ok=True, latency_ms=0)
    return []


def get_record(system: str, record_id: str) -> dict:
    """Fetch one record from a system of record (CRM/ATS/etc.)."""
    # TODO(wiring): call the real system API.
    record_tool_call("get_record", ok=True, latency_ms=0, system=system)
    return {}


# --- the catalog (name -> {fn, description, inputs}) -------------------------------------------

CATALOG = {
    "search_knowledge": {
        "fn": search_knowledge,
        "description": "Search our own documents and return the most relevant passages (RAG).",
        "inputs": ["usecase", "query", "k"],
    },
    "query_sql": {
        "fn": query_sql,
        "description": "Answer from structured data with a safe read-only query.",
        "inputs": ["question"],
    },
    "get_record": {
        "fn": get_record,
        "description": "Fetch a single record from a system of record.",
        "inputs": ["system", "record_id"],
    },
}


def get(name: str):
    """Return a tool function by name."""
    if name not in CATALOG:
        raise KeyError(f"unknown tool: {name}")
    return CATALOG[name]["fn"]
