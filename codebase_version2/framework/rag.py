"""RAG (Retrieval-Augmented Generation) — fetch our own data, then search it by relevance.

The point of this file: knowledge can come from MORE THAN ONE source. Here we load documents from
two example sources (a JSON knowledge file and an in-line "records" source) and search across all of
them. Swap in Azure AI Search / a SQL database / SharePoint by adding a loader function — the search
call does not change.

Offline: a simple keyword-overlap score ranks the documents (no embeddings needed). When Azure AI
Search is configured, retrieve() calls it instead.
"""

import json
import re

from framework import config


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def load_sources(usecase: str) -> list[dict]:
    """Fetch documents from ALL sources for a use case. Each doc = {id, text, source}.

    Source 1: usecases/<uc>/knowledge.json (unstructured knowledge).
    Source 2: a second example source (kept inline to show 'multiple sources').
    Add more loaders here (Azure AI Search, SQL, SharePoint) — they just append docs.
    """
    docs: list[dict] = []

    # Source 1 — a JSON knowledge file in the repo.
    kpath = config.ROOT / "usecases" / usecase / "knowledge.json"
    if kpath.exists():
        for i, d in enumerate(json.loads(kpath.read_text(encoding="utf-8"))):
            docs.append({"id": f"kb-{i}", "text": d["text"], "source": "knowledge.json"})

    # Source 2 — a second source (illustrative). In real life this might be a database table
    # via a SQL query, or a systems-of-record API. TODO(wiring): replace with a real connector.
    for i, d in enumerate(_SECONDARY_SOURCE):
        docs.append({"id": f"rec-{i}", "text": d, "source": "records"})

    return docs


# Illustrative second source so the demo shows retrieval across more than one place.
_SECONDARY_SOURCE = [
    "Refunds are processed within 5 business days after the return is received.",
    "Support hours are 9am to 6pm on weekdays.",
]


def retrieve(usecase: str, query: str, k: int = 3) -> list[dict]:
    """Return the top-k relevant documents across all sources for the query."""
    if config.AZURE_SEARCH_ENDPOINT:
        return _azure_search(query, k)

    docs = load_sources(usecase)
    q = _tokens(query)
    scored = []
    for d in docs:
        overlap = len(q & _tokens(d["text"]))
        if overlap:
            scored.append({**d, "score": overlap})
    scored.sort(key=lambda d: d["score"], reverse=True)
    return scored[:k]


def _azure_search(query: str, k: int) -> list[dict]:
    """Retrieve from Azure AI Search (hybrid + semantic) when configured."""
    # TODO(wiring): construct SearchClient from config and run a hybrid/semantic query.
    # Return the same shape: [{"id","text","source","score"}].
    return []
