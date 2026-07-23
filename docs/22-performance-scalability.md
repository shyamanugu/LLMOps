# Performance & Scalability Engineering

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §9).

## 1. Performance is a design constraint, not a tuning afterthought

A voice agent that answers correctly in three seconds has failed — the caller has already talked over it. The framework engineers performance as an explicit, budgeted, tested property inherited by every use case. Two workload shapes dominate AFNI and pull in opposite directions:

- **Interactive / real-time (Voice Agent):** optimize for *tail latency* — a sub-second, natural voice turn.
- **Bulk / throughput (PI Index):** optimize for *cost per unit at volume* — scoring 100% of interactions economically.

The same platform serves both by making latency budgets, caching, routing, and scaling first-class, observable, and SLO-governed.

## 2. Latency budget: the sub-second voice turn

A natural spoken turn must complete in roughly a second. The framework decomposes that budget across the pipeline so each stage has an owned, measurable target. A blown stage is visible in per-hop OpenTelemetry tracing and attributable to a component.

| Stage | Component | Budget (ILLUSTRATIVE) |
|---|---|---|
| Speech-to-text | gpt-realtime-1.5 / Voice Live streaming STT | ~150 ms |
| Retrieval | AI Search hybrid + semantic (partitioned index) | ~120 ms |
| Inference | Router → GPT-5.5 Instant / gpt-realtime-1.5 (streamed) | ~350 ms |
| Guardrails | Content Safety prompt shields + output check | ~80 ms |
| Text-to-speech | gpt-audio-1.5 streaming synthesis | ~150 ms |
| **Orchestration overhead** | routing, memory, spans | ~50 ms |
| **Total (p50 target)** | end-to-end perceived turn | **~900 ms** |

```
 caller speaks
      │  STT 150ms
      ▼
 ┌─────────┐  retrieval 120ms   ┌──────────┐  inference 350ms  ┌──────────┐
 │  STT    │──────────────────▶ │ Retrieve │─────────────────▶ │ Inference│
 └─────────┘                    │ (partition│                   │ (stream) │
                                │  vector)  │                   └────┬─────┘
                                └──────────┘   guardrails 80ms       │
                                                    ┌──────────┐     ▼
 caller hears  ◀── TTS 150ms ──  ┌──────────┐  ◀────│ Guardrail│◀── first tokens
                                 │   TTS    │        └──────────┘   stream out
                                 └──────────┘
        ────────────────  ~900 ms perceived turn (p50)  ────────────────
```

Streaming is essential: STT streams into inference, and inference streams first tokens into TTS, so stages overlap rather than sum serially. The budget assumes overlap, not strict sequence.

## 3. Layered caching

Caching removes work before it hits a model:

| Layer | What it caches | Effect |
|---|---|---|
| **Semantic cache** | Answers to semantically-equivalent queries (embedding match) | Skip inference for repeat questions |
| **Prompt cache** | Stable prefixes: system prompts, retrieved policy, few-shot | Router prompt caching — not re-billed, faster TTFT |
| **Response cache** | Deterministic tool/lookups by key | Avoid redundant tool + model calls |

Illustrative effect: a 25–40% semantic-cache hit rate on high-frequency intents removes those turns from the model entirely, cutting both latency and cost — *validate per workload*.

## 4. Model Router for cost-latency-quality

The **Model Router** (see model strategy doc) is also a performance lever: it routes trivial turns to **GPT-5.5 Instant** (low latency) and reserves frontier reasoning for hard turns, so the common path is fast and cheap while quality is preserved where it matters. Prompt caching further reduces time-to-first-token on cached prefixes.

## 5. Capacity: PTU vs pay-as-you-go

| Mode | Characteristics | Use for |
|---|---|---|
| **Provisioned Throughput (PTU)** | Reserved capacity, predictable low latency, no noisy-neighbor | Critical path — live Voice Agent, SLO-bound interactive traffic |
| **Pay-as-you-go** | Elastic, per-token, variable latency under load | Bursty, batch, and non-critical workloads (PI Index passes, dev/test) |

The framework runs a **hybrid**: PTU floors the interactive critical path for predictable tail latency; pay-as-you-go absorbs bursts and bulk. Right-sizing PTU is a FinOps decision reviewed against measured utilization.

## 6. Autoscaling, async, and streaming

- **Autoscaling** — stateless agent/orchestrator services run on **Azure Container Apps / AKS**, scaling on concurrency and queue depth (including scale-to-zero for spiky use cases). Durable-workflow state lives in Cosmos DB, so scale events never lose in-flight work.
- **Async + streaming** — interactive responses stream token-by-token (perceived latency ≈ time-to-first-token, not full completion). Long-running work runs as durable async workflows that pause/resume rather than holding connections.

## 7. Batching for bulk (PI Index)

The PI Index optimizes throughput, not per-request latency. Interactions are grouped into high-throughput batches scored on distilled/open-weight cost-tier models, parallelized across domain/tenant partitions, with frontier models reserved only for flagged anomalies. This is what makes 100%-of-interactions scoring economical at scale (see data platform doc).

## 8. Concurrency, backpressure, graceful degradation

At scale the system must fail safe, not fall over:

- **Concurrency + backpressure** — bounded concurrency per model/tool; APIM enforces token metering, quotas, and rate limits; queues apply backpressure so upstream slows rather than the system collapsing (mitigates OWASP LLM10 Unbounded Consumption).
- **Graceful degradation + fallback models** — on model timeout or throttling, the router fails over to a fallback tier (e.g., frontier → instant → cached/canned response). Retrieval degrades to a smaller index or cached answer rather than erroring. The user gets a slightly less rich answer, never a dead turn.
- **Circuit breakers** — repeated downstream failures trip a breaker to a degraded mode, protecting the tail.

## 9. Service-level objectives

| Workload | Metric | SLO (ILLUSTRATIVE) |
|---|---|---|
| Voice turn | p50 perceived latency | ≤ 900 ms |
| Voice turn | p95 perceived latency | ≤ 1500 ms |
| Chat/assist | p95 time-to-first-token | ≤ 700 ms |
| Interactive availability | monthly | ≥ 99.9% |
| PI Index | interactions scored | 100% within freshness window |
| PI Index | throughput | ≥ N k interactions/hour (set to AFNI volume) |
| Guardrail overhead | added p95 latency | ≤ 100 ms |

## 10. Load, soak, and continuous validation against SLOs

Performance is proven, not assumed:

- **Load testing** — ramp to peak concurrency to confirm SLOs and find the scaling knee before production.
- **Soak testing** — sustained multi-hour runs to catch memory leaks, connection exhaustion, cache decay, and cost drift.
- **Spike/burst testing** — validate autoscaling, backpressure, and fallback under sudden surges.
- **Continuous SLO monitoring** — Azure Monitor + App Insights track latency/throughput/error budgets; breaches page and can auto-trigger degradation. Cost and latency are release criteria in evaluation-in-CI, so a regression fails the pipeline before it ships.

```
 Load/soak/spike ─▶ measure p50/p95, throughput, cost ─▶ compare to SLO table
        │                                                      │
        └────────── fail: block release / tune ◀───────────────┘
                     pass: promote (canary) + monitor online
```

*All latency budgets, SLO targets, cache hit rates, and throughput figures in this document are ILLUSTRATIVE and must be replaced with AFNI-measured actuals.*
