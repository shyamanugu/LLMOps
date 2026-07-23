# Observability & FinOps

## Purpose

Probabilistic multi-agent systems fail differently than traditional software: they degrade in quality, drift as data and models change, and consume cost non-deterministically per interaction. AFNI therefore needs observability purpose-built for GenAI and a FinOps discipline that keeps token spend predictable and attributable. This document defines what to observe, how tracing and dashboards are implemented on Azure, the service-level objectives (SLOs) the platform commits to, and the FinOps controls that keep unit economics healthy — essential in a Gainshare model where AI cost directly affects shared margin. The controls apply across all three flagship initiatives — the **Voice Agent**, the **Performance Intelligence Index (PI Index)**, and **Hiring Intelligence**.

## What to Observe

GenAI observability spans four dimensions — quality, performance, safety, and cost — each with concrete signals.

| Signal category | Metrics | Source |
| --- | --- | --- |
| **Quality** | Groundedness score, relevance, answer correctness (LLM-as-judge + human), task success/containment, PI Index scoring agreement, thumbs feedback | Azure AI evaluation (online), feedback loop |
| **Performance** | End-to-end latency, per-agent/tool latency, turn latency (voice), throughput | OpenTelemetry traces, App Insights |
| **Reliability** | Error rate, tool-call failures, timeouts, fallback/escalation rate | App Insights, Azure Monitor |
| **Drift** | Input distribution shift, embedding drift, eval-score decay, PI Index score drift over time | Eval pipeline, Monitor workbooks |
| **Safety** | Content Safety triggers, prompt-shield (injection) hits, PII-redaction events, guardrail blocks, fairness signals | Content Safety logs, audit trail |
| **Cost** | Prompt/completion/total tokens, cost per interaction, per model, cache hit rate | API Management, Azure OpenAI metrics |

## Tracing & Instrumentation

- The platform standardizes on **OpenTelemetry GenAI semantic conventions**, capturing spans for each agent hop, model call (with token counts and model name), retrieval step, tool invocation, and guardrail check within a single distributed trace.
- Traces and metrics flow to **Application Insights** and **Azure Monitor** (Log Analytics), giving a unified view from the orchestrator down to individual tool calls — critical for debugging a supervisor routing across specialist agents.
- Prompt/response payloads are captured with PII redaction applied before storage; sampling is configurable per risk tier (full capture for Tier 3, which includes PI Index scoring and Hiring Intelligence).
- Evaluation results (offline golden-set runs and online scoring) are correlated to the same trace IDs so quality regressions can be traced to a specific prompt or model version.

## Dashboards, SLOs & Alerting

Role-based dashboards are published in Azure Monitor workbooks: an **executive/FinOps** view (cost, adoption, outcome KPIs), an **operations** view (latency, errors, escalation), and a **quality/safety** view (groundedness, eval scores, PI Index agreement, safety triggers).

### Example SLO Table (targets ILLUSTRATIVE)

| Service / capability | SLI | Target SLO |
| --- | --- | --- |
| Voice Agent turn latency | p95 turn latency | < 1.0 s (sub-second) |
| Agent-assist copilot | p95 response latency | < 2.0 s |
| PI Index scoring freshness | interaction → score latency | < 5 min (near-real-time) |
| Platform API availability | Successful requests / total | 99.9% monthly |
| Groundedness (RAG answers) | % answers above threshold | ≥ 95% |
| Safety | Unblocked harmful outputs | < 0.1% of interactions |
| Escalation integrity | Correct warm-transfer w/ context | ≥ 99% |

- **Alerting:** Azure Monitor alerts fire on SLO burn-rate (latency/availability), quality-score decay, drift thresholds, safety-trigger spikes, and cost-budget breaches, routed to on-call via the incident runbook (doc 08).

## FinOps: Controlling GenAI Unit Economics

### Token Metering & Cost Allocation

- **Azure API Management** fronts all model traffic as the token-metering gateway, tagging every request with **initiative** (Voice Agent, PI Index, Hiring Intelligence), business unit/program, and environment. This enables **showback/chargeback** — allocating cost per initiative and by client program, which aligns directly with Gainshare accounting.
- Quotas and rate limits per consumer prevent runaway spend and noisy-neighbor effects. The PI Index, which scores 100% of interactions, is metered and budgeted explicitly given its high-volume batch/near-real-time profile.

### Model Right-Sizing

Not every task needs a frontier model. The platform routes by task complexity:

| Model class | Use for | Rationale |
| --- | --- | --- |
| **GPT-4o / gpt-realtime** | Complex reasoning, live voice, high-stakes summarization, PI Index dimension scoring | Quality and latency where it matters |
| **GPT-4o-mini** | Routing, classification, simple Q&A, high-volume candidate screening | ~10x cheaper; sufficient quality |
| **Open-weight (Llama, Phi)** | Cost-sensitive or bulk offline processing (e.g., historical PI Index backfill) | Lower marginal cost, deployment flexibility |

Right-sizing is validated against evaluation gates so cost reductions never silently degrade quality.

### Efficiency Levers

- **Caching:** Semantic/response caching at the gateway and prompt-caching for stable system prompts and retrieved context cut repeated token spend on common queries (FAQs, standard disclosures, shared scoring rubrics).
- **Prompt compression:** Trim and template system prompts, summarize long conversation memory, and retrieve top-k tightly to reduce input tokens.
- **Retrieval discipline:** Rerank and limit RAG context to what is grounded and necessary.

### Budget Guardrails

- Per-initiative and per-business-unit **budgets** are set in Azure Cost Management with alerts at 50/80/100% of forecast.
- Hard quotas at API Management enforce ceilings; overage triggers throttling or model down-shift rather than uncontrolled spend.
- A monthly **FinOps review** (part of the CoE cadence) tracks cost per interaction, cost per scored interaction (PI Index), cost per screened candidate (Hiring), cache-hit trends, and model-mix, feeding right-sizing decisions back into the platform.

> All cost figures, SLO targets, and unit economics in this document are **ILLUSTRATIVE** placeholders, to be replaced with AFNI actuals during Phase 0 discovery.

## Closing the Loop

Observability and FinOps are two views of the same telemetry stream. Quality and safety signals feed the Responsible AI cadence and the evaluation dataset; cost and performance signals feed right-sizing and capacity planning. Together they make AFNI's agent fleet measurable, tunable, and economically predictable — so that AI-driven productivity converts cleanly into shared Gainshare value rather than unmanaged cloud spend.
