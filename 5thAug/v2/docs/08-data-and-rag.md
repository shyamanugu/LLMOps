# Data & RAG Pipeline

Retrieval-Augmented Generation (RAG) means we fetch the right facts from your own data and put them in front of the model at answer time, instead of trusting the model to remember them. For APIX that data is call transcripts plus their metadata; for Hiring Intelligence it is job descriptions and scoring rubrics. This document shows the concrete pipeline that gets that data from its source into an Azure AI Search index the pipeline steps can query.

## Today

**Today (assumption — to confirm):** transcripts and documents sit in blob storage or a database and are read directly by whatever code needs them. There is no cleaning or Personally Identifiable Information (PII) redaction step before text reaches a model, no chunking strategy, and no vector index — retrieval, where it exists at all, is a keyword or `LIKE` query. When source data changes, nothing re-indexes automatically; someone re-runs a script by hand.

## Our setup

One ingest-to-index pipeline, the same shape for both use cases, only the source and the chunking rules differ. Every stage is a named, testable step, and the whole thing is defined in code under `src/` and `infra/`, not clicked together in a portal.

```
 SOURCES                INGEST                  PROCESS                    INDEX
 ┌──────────────┐   ┌──────────────────┐   ┌──────────────────────┐   ┌─────────────────┐
 │ APIX:        │   │ Azure AI Search  │   │ clean (strip markup, │   │ Azure AI Search │
 │  transcripts │──▶│ built-in indexer │──▶│  normalise)          │──▶│ index           │
 │  + metadata  │   │  (blob / SQL)    │   │ PII redaction        │   │  (vector +      │
 │              │   │        OR        │   │ chunk (+ overlap)    │   │   keyword +     │
 │ Hiring:      │   │ Fabric Data      │   │ embed via 'embed'    │   │   metadata      │
 │  JDs+rubrics │   │ Factory pipeline │   │  alias (text-embed-  │   │   filters)      │
 └──────────────┘   └──────────────────┘   │   ding-3-large)      │   └────────┬────────┘
                                            └──────────────────────┘            │
                    refresh: schedule + change-data-capture (CDC)      alias ───┘
                    blue-green re-index behind an index alias
```

**Sources.** APIX transcripts land in Azure Blob Storage as JSON, one file per call, with metadata (program, agent name, call date, dimension scores) either in the same file or in an Azure SQL table keyed by `transcript_id`. Hiring job descriptions and rubrics land the same way. Nothing reads a source directly at answer time — the source only feeds the pipeline.

**Ingest.** We use the built-in **Azure AI Search indexer** for the straightforward case: point it at the blob container or SQL table and it pulls new and changed rows on a schedule. For the heavier transforms (joining a transcript to its metadata table, or fanning one document into many rubric sections) we run a **Microsoft Fabric Data Factory** pipeline that writes cleaned records into a staging container, and the AI Search indexer reads from there. Rule of thumb: if a single indexer with a skillset can do it, use the indexer; reach for Fabric only when the shape of the data needs real transformation first.

**Clean and redact.** Before any text is chunked we strip transcription markup and normalise whitespace, then run PII redaction — the same `pii_redact` step used around model calls elsewhere in the platform — so personal data (customer names, phone numbers, card fragments spoken on a call) never enters the index. This runs as an Azure AI Search **custom skill** (a small container the skillset calls) or as a step in the Fabric pipeline, depending on which ingest path a source uses.

**Chunk.** We split cleaned text into overlapping chunks so a retrieved passage carries enough surrounding context to be useful. APIX transcripts are chunked by speaker turn groups (roughly 400 tokens, 80-token overlap) so a quote keeps its lead-in and response. Hiring documents are chunked by section (one rubric criterion per chunk, small overlap) because the natural unit is the criterion. Chunk size and overlap are config, not code, so we can tune them per source without a rebuild.

**Embed.** Each chunk is embedded with **text-embedding-3-large**, resolved through the `embed` alias in `models.yaml` — the same indirection the rest of the platform uses, so the embedding model is never hard-coded and a swap is a reviewed config change that must clear the evaluation gate.

**Index.** Chunks plus their vectors and metadata land in an Azure AI Search index configured for hybrid retrieval (vector + keyword) with metadata filters, so a query can be scoped (for example, `program = telesales` for APIX, or `role = backend-engineer` for Hiring) before ranking.

Here is the chunk-and-embed skill, the part that is ours rather than built in:

```python
# src/pipelines/common/index_skill.py  — called per record by the AI Search skillset
def process(record, env):
    text = normalise(strip_markup(record["content"]))
    text = pii_redact(text)                                  # same redactor as the model path
    chunks = chunk(text, size=400, overlap=80,               # config per source
                   split_on=record["meta"].get("split", "turn"))
    out = []
    for i, ch in enumerate(chunks):
        vector = embed(ch, alias="embed", env=env)           # -> text-embedding-3-large
        out.append({
            "id": f'{record["id"]}::{i}',
            "content": ch,
            "vector": vector,
            "program": record["meta"].get("program"),        # metadata for filtered retrieval
            "transcript_id": record["id"],
            "source": record["meta"].get("source"),
        })
    return out
```

And the indexer schedule and change tracking, defined in infrastructure:

```jsonc
// infra/search/apix-indexer.json  (deployed via Bicep/az CLI, not the portal)
{
  "name": "apix-transcripts-indexer",
  "dataSourceName": "apix-blob",
  "targetIndexName": "apix-transcripts-v7",     // physical index; alias points here
  "schedule": { "interval": "PT30M" },          // scheduled pull every 30 minutes
  "parameters": { "configuration": { "dataChangeDetectionPolicy": {
      "@odata.type": "#Microsoft.Azure.Search.HighWaterMarkChangeDetectionPolicy",
      "highWaterMarkColumnName": "last_modified" // change-data-capture: only new/changed rows
  }}}
}
```

**Refresh.** Two mechanisms, both automatic. A **schedule** (every 30 minutes above) catches routine additions. **Change-data-capture (CDC)** — the high-water-mark policy — means the indexer only processes rows whose `last_modified` moved, so a scheduled run is cheap and near-real-time rather than a full re-scan.

**Blue-green re-index with index aliases.** When we change chunking, the embedding model, or the index schema, we do not mutate the live index. We build a new physical index (`apix-transcripts-v8`) alongside the old one, let it finish and pass a retrieval sanity check, then repoint the **alias** (`apix-transcripts`, what the application actually queries) from v7 to v8 in one atomic switch. If retrieval quality regresses, we point the alias back. The application only ever knows the alias name, so re-indexing is invisible to it and rollback is instant.

## Pipeline step → Azure service

| Pipeline step | Azure service |
|---|---|
| Source of record (transcripts, JDs, rubrics) | Azure Blob Storage / Azure SQL Database |
| Scheduled + CDC pull | Azure AI Search indexer |
| Heavy transform / join before indexing | Microsoft Fabric Data Factory pipeline |
| Clean + PII redaction | Azure AI Search custom skill (container) / Fabric step |
| Chunk + embed | Custom skill calling Azure OpenAI (`embed` → text-embedding-3-large) |
| Vector + keyword index, metadata filters | Azure AI Search index |
| Stable query target, blue-green swap | Azure AI Search index alias |
| Retrieval quality scoring | Ragas, in the evaluation gate (see doc 06) |

## What changes

**What changes:** direct reads of raw source data are replaced by queries against a governed Azure AI Search index that has already been cleaned, PII-redacted, chunked with overlap, and embedded. Retrieval becomes hybrid vector + keyword with metadata filters instead of keyword-only. Refresh becomes automatic (schedule + CDC) instead of a hand-run script, and re-indexing becomes a safe blue-green alias swap with instant rollback. **Migration step:** stand up one indexer against the existing APIX blob container, add the clean/redact/chunk/embed skill, publish behind an alias, and point the APIX retrieval step at the alias — the source data does not move, we only put the pipeline in front of it. Retrieval quality then flows through the same golden-dataset gate as everything else (Ragas metrics in doc 06), so an index change cannot ship if it drops groundedness or context recall past baseline.
