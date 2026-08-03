# Data Pipelines & the Warehouse Question

## The question we keep getting asked

"If we're doing LLMOps (large language model operations), do we still need the data warehouse?" Yes. LLMOps does
not replace a data warehouse or a lakehouse — it connects to one on both sides. Data flows in (source systems feed
the knowledge pipeline that grounds the model) and data flows out (every model call, every tool call, every piece
of feedback is telemetry that lands back in the warehouse for analysis and for building the next training set).
The warehouse is not optional infrastructure sitting next to the AI system; it is one of the two directions the AI
system talks to.

For a client already on Microsoft Fabric, this is simpler than it sounds: **Fabric with OneLake can BE the
lakehouse/warehouse**. There is no separate "AI data platform" to stand up — the same OneLake that already holds
CRM extracts, billing data, and call metadata is where the knowledge base gets built and where the usage telemetry
lands.

## Two pipelines, one platform

There are two distinct pipelines running on the same underlying platform, and it helps to keep them mentally
separate because they run on different schedules and serve different purposes:

1. **The knowledge pipeline (RAG)** — turns source documents and records into a searchable index the model can
   retrieve from at answer time. RAG stands for Retrieval-Augmented Generation: instead of trusting the model's
   internal memory, we retrieve the relevant facts first and hand them to the model as context.
2. **The telemetry pipeline** — captures every request/response, cost, latency, and feedback signal and routes it
   into the warehouse for dashboards, drift analysis, and curating the next round of training/eval data.

Both pipelines use the same Fabric tenant, the same governance layer (Purview), and the same landing zone
(OneLake). They are two data flows through one platform, not two platforms.

## Where the data comes from

Before any pipeline runs, name the actual source systems. For a contact-center enterprise these are typically:

| Source system | What it contains | How it is reached |
|---|---|---|
| **SharePoint / OneDrive** | Policy documents, SOPs (standard operating procedures), training decks, FAQs | Microsoft Graph connector / AI Search SharePoint indexer |
| **Azure Blob Storage** | PDFs, scanned forms, exported reports, archived transcripts | AI Search blob indexer, or Fabric Data Factory copy activity |
| **SQL databases** | Product catalog, policy tables, claims/billing records, customer master data | Fabric Data Factory (CDC-enabled connectors) or direct AI Search SQL indexer |
| **CRM / ticketing (Salesforce, ServiceNow)** | Case history, resolution notes, knowledge articles, ticket macros | Native connectors in Fabric Data Factory; Salesforce CDC (Change Data Capture) for near-real-time |
| **Call transcripts (contact-center platform: Genesys, NICE, Five9, etc.)** | Speech-to-text transcripts, call metadata, dispositions | Export/webhook into Blob or Event Hubs, then picked up by the same ingestion path |

Every one of these is a live system with its own owner, its own access model, and its own change rate. The
pipeline has to reach into each one on its own terms — nightly export for a legacy SQL table, webhook for a live
CRM case, streaming for call events — and normalize it into one place before anything gets chunked or embedded.

## The knowledge pipeline, step by step

```
 Sources                         Ingest                    Prepare                          Index
 ─────────────────────           ─────────────────         ──────────────────────────       ─────────────────────
 SharePoint / Blob      ───▶     Fabric Data Factory  ───▶  Clean text                 ───▶  Chunk (500-800 tokens,
 SQL databases                   pipeline  OR                (strip boilerplate,             10-15% overlap)
 CRM / ticketing                 Logic Apps connector         headers/footers, HTML)               │
 Call transcripts                OR                                │                              ▼
 (via Blob / Event Hubs)         AI Search built-in           PII scrub                     Embed with
                                 indexer (pull model,          (Content Safety /             text-embedding-3-large
                                 scheduled crawl)               Purview classifiers,               │
                                       │                        redact before it is                ▼
                                       ▼                        ever embedded)              Azure AI Search index
                                 Land in OneLake                                             (hybrid + semantic +
                                 Bronze zone (raw,                                            integrated vectorization)
                                 immutable copy)
```

Walking through each step:

1. **Ingest.** Three ways to pull data in, and most estates use a mix: **Fabric Data Factory** pipelines for
   scheduled/CDC loads out of SQL, CRM, and ticketing systems; **Logic Apps** for lightweight event-driven
   connectors (a SharePoint file changed, a ServiceNow case closed); or **Azure AI Search's own built-in
   indexers**, which can crawl Blob Storage, SharePoint, and SQL directly without a separate Data Factory hop.
   The built-in indexer is the fastest path to a working index; Data Factory earns its keep when the source needs
   transformation logic or CDC before the document is even chunk-worthy.
2. **Clean.** Strip HTML, headers/footers, boilerplate, and duplicate content. A policy PDF exported from
   SharePoint carries a lot of noise (page numbers, revision stamps, navigation text) that pollutes chunk quality
   if left in.
3. **PII-scrub.** Personally identifiable information (PII) — account numbers, social security numbers, medical
   record numbers, phone numbers — gets detected and redacted *before* the text is chunked and embedded, not
   after. Once PII is embedded into a vector, it is effectively baked into the index; scrubbing after the fact
   means re-indexing everything.
4. **Chunk with overlap.** Split documents into passages small enough to fit usefully in the model's context
   window but large enough to preserve meaning — a common starting point is 500-800 tokens with 10-15% overlap
   between consecutive chunks, so a fact that straddles a chunk boundary is not lost. Chunking should respect
   document structure (section breaks, call-transcript turn boundaries) rather than cutting at a fixed character
   count.
5. **Embed.** Each chunk is converted to a vector with **text-embedding-3-large**. The embedding model choice
   matters for retrieval quality; it should be pinned in config the same way generation models are, not
   hard-coded in application code.
6. **Index.** Vectors and their source text land in an **Azure AI Search** index configured for hybrid retrieval
   (keyword + vector) with the semantic ranker on top. If AI Search's integrated vectorization feature is used,
   steps 4-6 collapse into one managed pipeline — the split-embed-index sequence runs inside the service instead
   of being hand-coded.

## Keeping the index fresh: refresh strategies

A RAG index that goes stale is worse than no RAG at all — it will confidently retrieve last year's policy. Two
refresh models, usually combined:

| Strategy | How it works | Use for |
|---|---|---|
| **Scheduled (batch)** | Full or incremental re-crawl on a timer (nightly, hourly) | Slow-moving content: training decks, historical archives, reference docs |
| **Event-driven / CDC** | A change in the source (row updated, file saved, case closed) fires a targeted re-index of just that document | Fast-moving content: active policy pages, live CRM knowledge articles, anything with a same-day accuracy requirement |

For a full rebuild — new embedding model, new chunking strategy, or a schema change to the index — use **index
aliases** for a blue-green cutover: build the new index under a new physical name, point traffic at it through the
alias only after validation passes, and keep the old index available for instant rollback if the new one
underperforms. This avoids ever serving a half-built index to production traffic.

## The telemetry pipeline

The second pipeline runs in the other direction. Every model call already emits structured telemetry through
Application Insights (see the observability doc); the telemetry pipeline is what happens to that data next:

```
App Insights (traces, tokens, latency, cost, feedback events)
        │  diagnostic settings export
        ▼
Fabric lakehouse (OneLake) — Bronze (raw export) → Silver (cleaned/joined) → Gold (curated marts)
        │                                                    │
        ▼                                                    ▼
  Power BI dashboards                             Training-data curation
  (volume, cost, latency, quality trend)          (accepted responses → eval sets → fine-tuning pairs)
```

App Insights diagnostic settings export raw trace and log data continuously into the Fabric lakehouse. From there
it goes through the same medallion pattern as any other data (Bronze raw, Silver cleaned, Gold curated) and feeds
two consumers: Power BI dashboards for humans watching the system, and a curation step that turns high-quality,
human-approved production responses into new golden-dataset rows or fine-tuning pairs. This is the mechanism
described in the feedback-and-analytics doc — it only works because the telemetry pipeline lands the raw data
in a governed place first.

## Governance: Purview on both pipelines

Both pipelines carry data that is regulated, sensitive, or both, so **Microsoft Purview** governs both:

- **Classification** — automatic sensitivity labeling on data as it lands in Bronze, so a document containing
  account numbers or health information is tagged before it is chunked.
- **Lineage** — an end-to-end map from source system through Bronze/Silver/Gold to the vector index to the actual
  model response that cited it. When a compliance reviewer asks "where did this answer's fact come from," the
  answer is a traceable path, not a guess.
- **Retention** — per-source retention and deletion rules (a call transcript might need to be purged after a
  regulatory window; a policy document might need version history kept indefinitely), applied consistently across
  the lakehouse and the vector index so a deletion request does not leave orphaned copies in the index.

## Pipeline components → Azure service

| Component | Azure service | Notes |
|---|---|---|
| Document/file ingestion | Fabric Data Factory, Logic Apps, or AI Search built-in indexers | Pick based on whether transformation logic is needed before chunking |
| Structured/CDC ingestion | Fabric Data Factory (CDC connectors) | SQL, Salesforce, ServiceNow change feeds |
| Streaming ingestion (call events) | Event Hubs + Stream Analytics | Near-real-time transcript/metadata capture |
| Lakehouse / landing zone | Microsoft Fabric / OneLake | Bronze/Silver/Gold medallion zones |
| PII detection/redaction | Content Safety + Purview classifiers | Applied at Silver, before chunking |
| Chunking + embedding | Azure AI Search integrated vectorization (or custom code with text-embedding-3-large) | Managed path preferred over hand-rolled scripts |
| Vector index | Azure AI Search | Hybrid + semantic ranking |
| Index refresh orchestration | Fabric Data Factory pipeline + AI Search indexer schedule, or CDC webhook | Scheduled for slow content, event-driven for fast content |
| Telemetry export | Application Insights diagnostic settings | Continuous export to lakehouse |
| Analytics/BI | Power BI (on Fabric) | Dashboards over Gold-zone marts |
| Governance | Microsoft Purview | Classification, lineage, retention across both pipelines |

## Where this sits in the maturity plan

At Level 0, the knowledge pipeline is often a manual one-time load — someone exports a folder of PDFs and runs a
script. At Level 1, the AI Search RAG pipeline with scheduled refresh becomes part of the first production use
case. Level 2 adds event-driven/CDC refresh, index aliases for safe re-indexing, and the telemetry pipeline
feeding a real analytics dashboard on Fabric. Level 3 closes the loop fully: the warehouse becomes the source for
curated training data, and onboarding a new use case means pointing it at existing Gold-zone data rather than
building a bespoke pipeline from scratch.
