# Data Access (RAG, structured data, and documents)

The models in these pipelines are only as good as the data we put in front of them, and that data does not all look alike. Some of it is free text (call transcripts, notes). Some of it is structured rows in a database (agent records, program metadata, scores). Some of it arrives as files (PDF contracts, scanned forms, images). Retrieval-Augmented Generation (RAG) — fetching the right facts and putting them in front of the model at answer time — is the right approach for the free-text part, but it is the wrong tool for the rest. So what we build is not "a RAG pipeline"; it is a **data-access layer** with a small set of reusable tools, and RAG is one of them.

This is worth stating plainly because it is a common mistake: teams put everything through RAG, including structured data, and then wonder why the model gives a "roughly right" number instead of the exact one. Structured data does **not** go through RAG. It goes through a read-only Structured Query Language (SQL) tool that returns exact rows. RAG is for meaning; SQL is for facts.

## Today

**Today (assumption — to confirm):** whatever code needs data reads the source directly. Transcripts are pulled from blob storage and pasted into the prompt whole. If a number is needed (a score, a count, a date), either it is hard-coded into a query buried in the agent code, or the whole table is dumped into the prompt and the model is asked to "find" it — which is slow, expensive, and sometimes wrong. Files like PDFs are either skipped or handled by a one-off script. There is no cleaning or Personally Identifiable Information (PII) redaction before text reaches a model, no chunking, and no vector index — retrieval, where it exists at all, is a keyword or `LIKE` query. When source data changes, nothing re-indexes automatically; someone re-runs a script by hand. There is no shared set of data tools, so each use case re-solves data access from scratch.

## Our setup

One **data-access layer** that every use case draws on, built as a small catalog of reusable tools. Each kind of data has one right way in:

| Data type | Approach | Azure service | Reusable tool |
|---|---|---|---|
| Unstructured text (transcripts, notes, articles) | RAG: clean → chunk → embed → hybrid search, pass retrieved passages to the model | Azure AI Search | `search_knowledge` |
| Structured data (rows: scores, records, metadata) | Natural-Language-to-SQL (NL2SQL): a SQL agent turns the ask into a read-only, parameterised query against allow-listed tables; returns exact rows | Azure SQL Database / Cosmos DB | `query_sql` |
| Documents and files (PDF, scans, forms, images) | Extract structure and text first, then either RAG the text or pull named fields as structured data | Azure AI Document Intelligence | `extract_document` |
| Systems of record (live business systems) | Fetch a specific record by key through a governed connector | Line-of-business API via MCP / connector | `get_record` |

The message: structured data does not go through RAG. It uses `query_sql`, which returns exact values under tight guardrails. RAG (`search_knowledge`) is only for unstructured text. Documents are first turned into text or fields by `extract_document`, and only then do they flow into one of the other two paths.

### The reusable predefined tool catalog

These four tools are built **once**, in `platform/tools/`, and every use case composes them. A use case does not write its own database client or its own search client; it declares which tools its agents can call, points them at its own index and its own allow-listed tables, and the shared tool does the rest. When a new kind of data access comes up, we add a tool to the catalog and every later use case inherits it. This is the "reusable tool catalog" the platform doc refers to; here is what each tool does.

```
platform/tools/
├── search_knowledge/     # RAG over Azure AI Search — retrieve passages for a query
├── query_sql/            # NL2SQL / parameterised read-only SQL over allow-listed tables
├── extract_document/     # Azure AI Document Intelligence — file -> text + fields
└── get_record/           # fetch one record from a system of record by key (via MCP)
```

**`search_knowledge` (RAG).** Takes a natural-language query plus optional filters (for example `program = telesales`), runs hybrid vector + keyword retrieval against an Azure AI Search index, and returns the top passages with their source ids so the model can cite them. This is the tool the coaching-report step calls to pull the exact evidence quotes it must ground its output in.

**`query_sql` (structured / NL2SQL).** Takes a question about structured data and produces an answer from exact rows, not from the model's memory. It is deliberately narrow and safe:

- **Read-only.** It can only issue `SELECT`. No writes, ever.
- **Allow-listed tables and columns.** It can see only the tables and columns a use case has explicitly registered. It cannot query anything else in the database.
- **Parameterised.** Values are bound as parameters, never string-concatenated into SQL, so a crafted input cannot inject a different query.
- **NL2SQL under guardrails.** The model proposes the SQL; the tool validates it against the allow-list and the read-only rule before it runs, and rejects anything outside those bounds. A row/time limit caps how much comes back.

So when APIX needs "the average sales dimension score for agent X on the telesales program last week," it does not dump the scores table into the prompt — it calls `query_sql`, which runs one bounded `SELECT` and returns the exact number.

**`extract_document` (files).** Takes a PDF, scan, form, or image and runs **Azure AI Document Intelligence** to extract layout-aware text and named fields (tables, key-value pairs, signatures). The output then goes down one of the other paths: the extracted text is chunked and indexed for RAG, or the named fields become structured data. This is what lets a scanned form or a contract become answerable at all — nothing tries to feed a raw image to a text model.

**`get_record` (systems of record).** Fetches one specific record from a live business system by key through a governed Model Context Protocol (MCP) connector — for example, pulling the current status of a candidate or an agent's profile. It returns the authoritative live value rather than a possibly-stale copy in the index.

Every one of these calls is traced (tool name, arguments redacted, status) through the same `tracing.py` path as everything else, and tool selection itself is evaluated — did the agent reach for `query_sql` when the ask was about a number, rather than trying to RAG it? That is exactly what the custom tool-selection evaluator checks (doc 06).

### The RAG ingestion pipeline (behind `search_knowledge`)

The unstructured-text path needs data prepared before `search_knowledge` can retrieve it. That preparation is one ingest-to-index pipeline, the same shape for both use cases; only the source and the chunking rules differ. Every stage is a named, testable step defined in code under `src/` and `infra/`, not clicked together in a portal.

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

**Sources.** APIX transcripts land in Azure Blob Storage as JSON, one file per call, with metadata (program, agent name, call date, dimension scores) either in the same file or in an Azure SQL table keyed by `transcript_id`. Hiring job descriptions and rubrics land the same way. Nothing reads a source directly at answer time — the source only feeds the pipeline (for RAG) or is queried through `query_sql` (for structured facts).

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

## Data type → approach → service → tool

| Data type | Approach | Azure service | Reusable tool |
|---|---|---|---|
| Unstructured text | Clean → chunk → embed → hybrid retrieval; pass passages to model (RAG) | Azure AI Search | `search_knowledge` |
| Structured data | NL2SQL → read-only, parameterised, allow-listed `SELECT`; exact rows back | Azure SQL Database / Cosmos DB | `query_sql` |
| Documents / files (PDF, scans, forms, images) | Extract text + fields, then RAG the text or take named fields as structured data | Azure AI Document Intelligence | `extract_document` |
| Systems of record | Fetch one record by key through a governed connector | Line-of-business API via MCP | `get_record` |
| (Behind RAG) source of record | Feed the ingest pipeline; not read directly at answer time | Azure Blob Storage / Azure SQL | — |
| (Behind RAG) heavy transform / join | Transform before indexing | Microsoft Fabric Data Factory | — |
| (Behind RAG) retrieval quality scoring | Score groundedness / context recall in the gate | Ragas, in the evaluation gate (doc 06) | — |

## What changes

**What changes:** data access stops being "read the source and hope," and becomes a shared layer of four governed tools. The biggest single correction is that **structured data no longer goes through RAG or the prompt** — it goes through `query_sql`, which returns exact rows under a read-only, parameterised, allow-listed guardrail. Free text becomes governed hybrid retrieval (`search_knowledge`) over a cleaned, PII-redacted, chunked, embedded index instead of a keyword `LIKE`. Files stop being skipped: `extract_document` turns PDFs, scans, and forms into text or fields first. Live business data comes through `get_record` instead of a stale copy. And because all four tools live in `platform/tools/`, the next use case composes them instead of rebuilding data access. Refresh becomes automatic (schedule + CDC) and re-indexing becomes a safe blue-green alias swap with instant rollback.

**Migration step:** stand up one indexer against the existing APIX blob container, add the clean/redact/chunk/embed skill, publish behind an alias, and point APIX's `search_knowledge` at it. In parallel, register APIX's scores/metadata tables (read-only, allow-listed) behind `query_sql` so the scoring and reporting steps pull exact numbers through the tool instead of the prompt. The source data does not move — we put the data-access layer in front of it. Retrieval and tool selection then flow through the same golden-dataset gate as everything else (Ragas metrics plus the tool-selection evaluator in doc 06), so a data-access change cannot ship if it drops groundedness, context recall, or tool-selection accuracy past baseline.
