# Data Platform & Handling Data at Scale

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §4 layer 5, §9).

## 1. Why the data platform is the framework's foundation

GenAI quality is bounded by data quality, freshness, and governance. A model that cannot retrieve the right, current, permitted fact will hallucinate confidently. The framework therefore treats the data platform as a first-class, reusable layer — not per-use-case plumbing. Every initiative (Voice Agent, PI Index, Hiring Intelligence) draws from one governed lakehouse, one vectorization pipeline, and one lineage/DLP spine, so knowledge, grounding, and analytics are consistent and auditable across the enterprise.

The substrate is **Microsoft Fabric / OneLake** as the unified lakehouse, **Azure AI Search** and **Cosmos DB** as the vector stores, **Event Hubs / Stream Analytics** for streaming, and **Microsoft Purview** for lineage, DLP, and retention. All model I/O and retrieved content is treated as untrusted and passes redaction/classification before it lands.

## 2. Lakehouse: Fabric / OneLake

OneLake is the single logical data lake for AFNI GenAI. Structured (CRM, HRIS, billing), semi-structured (call metadata, ATS events), and unstructured (transcripts, documents, audio) sources land in a **medallion architecture**:

| Zone | Contents | Purpose |
|---|---|---|
| **Bronze (raw)** | Verbatim ingested data, immutable | Replay, audit, reprocessing |
| **Silver (cleansed)** | Deduped, PII-tagged, conformed schema | Trusted analytics + chunking source |
| **Gold (curated)** | Domain marts, golden datasets, features | RAG grounding, evals, dashboards |

Because every domain shares OneLake, a new use case onboards against curated Gold data instead of building a bespoke pipeline — the paved-road principle applied to data.

## 3. Ingestion: batch + streaming

The platform ingests on two paths that meet in the lakehouse:

- **Batch** — scheduled and CDC loads from systems of record (CRM, HRIS, billing, ATS) via Fabric Data Factory pipelines. Used for bulk backfills and the nightly/hourly PI Index passes.
- **Streaming** — **Event Hubs** captures live interaction events (call events, transcript segments, dispositions); **Stream Analytics** performs windowed enrichment and routes to Bronze in near-real-time. This is what lets the PI Index consume interactions as they happen rather than only in overnight batch.

```
 Sources                 Ingestion            Lakehouse (OneLake)         Serving
 ┌──────────┐  batch/CDC ┌──────────┐        ┌───────────────────┐   ┌──────────────┐
 │ CRM/HRIS │──────────▶ │  Data    │──────▶ │ Bronze → Silver → │   │ AI Search    │
 │ billing  │            │  Factory │        │ Gold (medallion)  │─▶ │ vector index │─▶ RAG / agents
 │ ATS      │            └──────────┘        │                   │   └──────────────┘
 └──────────┘                                │  chunk + integrated│   ┌──────────────┐
 ┌──────────┐  stream    ┌──────────┐        │  vectorization     │─▶ │ Cosmos DB    │─▶ agent memory
 │ voice/   │──────────▶ │ Event Hubs│─────▶ │                   │   │ vector/state │
 │ chat/     │           │ + Stream  │        └─────────┬─────────┘   └──────────────┘
 │ interact. │           │ Analytics │                  │ lineage/DLP
 └──────────┘            └──────────┘                   ▼
                                              ┌───────────────────┐
                                              │ Microsoft Purview │  lineage · classification · retention
                                              └───────────────────┘
```

## 4. Chunking + integrated vectorization

Documents and transcripts are chunked (structure-aware: sections, turns, speaker boundaries) and embedded with **text-embedding-3-large** via Azure AI Search **integrated vectorization** — the split-embed-index pipeline is managed, not hand-coded. Chunk metadata carries domain, tenant, source, timestamp, and sensitivity label so retrieval can filter by permission and freshness. Re-embedding is triggered by CDC on the source, keeping vectors current.

## 5. Vector indexes: partitioned per domain / tenant

Vectors live in **Azure AI Search** (hybrid + semantic ranker) for enterprise knowledge and **Cosmos DB** for agent-state/memory vectors. Indexes are **partitioned per domain and per tenant**:

| Partitioning axis | Reason |
|---|---|
| **Per tenant** | Enforce data isolation; a client's data never retrieved for another (least privilege on vectors) |
| **Per domain** | Keep retrieval precise and small; billing knowledge ≠ hiring knowledge |
| **Per sensitivity** | Route PII-bearing partitions through stricter access + local-model paths |

Partitioning also bounds index size, which keeps retrieval latency inside the voice latency budget (see performance doc) and limits blast radius of any single partition.

## 6. Incremental / CDC refresh and freshness

Full re-indexing does not scale to AFNI volumes. The platform uses **change data capture**: only changed source rows/documents are re-chunked and re-embedded, on a schedule tied to each source's volatility. Freshness is an explicit SLO per domain:

| Domain | Freshness target (ILLUSTRATIVE) | Refresh mechanism |
|---|---|---|
| Policy / knowledge base | < 1 hour | CDC on doc store |
| Customer interaction state | Near-real-time | Event Hubs stream |
| Hiring requisitions | < 15 min | ATS webhook → CDC |
| Historical analytics marts | Nightly | Batch |

## 7. Governance: Purview lineage, DLP, retention, PII

**Microsoft Purview** provides the governance spine every dataset inherits:

- **Lineage** — end-to-end map from source → Bronze → Silver → Gold → vector index → the agent response that cited it. This is what makes a GenAI answer auditable back to its source data.
- **Classification + DLP** — automatic sensitivity labeling; DLP policies block prohibited data from leaving a boundary or entering a lower-trust store.
- **Retention** — per-domain retention and deletion honoring TCPA/HIPAA/GDPR; supports data-subject deletion across lakehouse and vector stores.
- **PII handling** — detection and redaction (Purview + Content Safety) at Silver, before chunking, so PII is not embedded into vectors or memory unless explicitly permitted and scoped.

## 8. Golden datasets

Curated **golden datasets** in Gold are the evaluation source of truth. They are assembled from production feedback — QA reviews, thumbs, escalations, and PI Index outputs — and version-controlled. They feed evaluation-in-CI, model-router quality bars, and the frontier-adoption loop, closing the loop from production back into quality gates.

## 9. Large-scale considerations

At AFNI volumes the design must hold on four axes:

| Axis | Design response |
|---|---|
| **Throughput** | Streaming ingestion (Event Hubs) + partitioned parallel writes; batch scoring parallelized across partitions |
| **Partitioning** | Domain/tenant/sensitivity partitions bound index size, isolate tenants, and enable parallel refresh |
| **Cost** | Tiered storage (hot/cool), CDC-only re-embedding, distilled/open-weight models for bulk passes, prompt caching |
| **Freshness** | Per-domain freshness SLOs enforced by CDC + stream, monitored like any other SLO |

## 10. How the PI Index consumes 100% of interactions at scale

Traditional QA samples 5–10% of interactions. The framework's data platform makes **100% coverage** economical:

1. **Stream in** — every interaction's transcript/metadata lands via Event Hubs in near-real-time (no sampling).
2. **Batch score** — interactions are grouped and scored in high-throughput batches using distilled/open-weight models (right-sized in the model strategy), with frontier models reserved for flagged anomalies.
3. **Persist + partition** — scores write back to Gold, partitioned per program/tenant, feeding dashboards and golden datasets.
4. **Govern** — PII redaction at Silver and Purview lineage make full-population analysis compliant, not a privacy liability.

The result (ILLUSTRATIVE): QA coverage moves from ~5–10% sampled to ~100% of interactions, with per-interaction cost low enough to run continuously because bulk scoring is batched on cost-tier models rather than frontier per-call inference. Replace percentages and unit costs with AFNI actuals.

*All throughput, freshness, coverage, and cost figures in this document are ILLUSTRATIVE and must be replaced with AFNI-measured actuals.*
