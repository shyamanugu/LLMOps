# RAG (Retrieval)

**What it is** — Fetching our own data from **more than one source** and searching it by relevance,
so the model answers from retrieved context. Add a source by adding a loader; the search call
doesn't change.

**When to use** — Any use case that answers from a knowledge base, records, or documents. Retrieval
feeds groundedness, so it directly affects the evaluation gate.

**How it works here** — `framework/rag.py`:
- `load_sources(usecase)` fetches from ALL sources and returns docs shaped `{id, text, source}`.
  Source 1 is `usecases/<uc>/knowledge.json` (unstructured); Source 2 is an inline example to show
  "multiple sources". Add a loader here (Azure AI Search, SQL, SharePoint) — it just appends docs.
- `retrieve(usecase, query, k=3)` returns the top-k docs across all sources, shaped
  `{id, text, source, score}`. Offline it ranks by keyword overlap; when `AZURE_SEARCH_ENDPOINT` is
  set it calls `_azure_search` (hybrid + semantic) instead. **Keep this signature and return shape
  stable** — use cases and the evaluator depend on it.

Tools wrap retrieval: `tools.search_knowledge` calls `retrieve` and records a tool call. For
structured data use `query_sql` (read-only, allow-listed); for a single record use `get_record`.

**Key files** — `framework/rag.py`, `framework/tools.py`, `usecases/<uc>/knowledge.json`,
`framework/config.py` (`AZURE_SEARCH_*`).

**Example — add a loader (keep `retrieve()` unchanged):**
```python
def load_sources(usecase: str) -> list[dict]:
    docs = []
    # ... existing sources ...
    for row in _fetch_from_crm(usecase):          # new source
        docs.append({"id": row["id"], "text": row["summary"], "source": "crm"})
    return docs
```

**Pitfalls**
- Changing `retrieve()`'s signature or its `{id, text, source, score}` shape — breaks use cases and
  scoring. Extend with a loader or an optional kwarg instead.
- Putting use-case knowledge or business rules in `framework/rag.py` — sources are generic; the data
  lives in `usecases/<uc>/`.
- Building SQL retrieval that isn't read-only / allow-listed.
- Leaving `_azure_search` a stub in production — it returns `[]` until wired (`# TODO(wiring)`).
