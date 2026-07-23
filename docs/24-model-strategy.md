# Model Strategy & Lifecycle

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §3, §10).

## 1. The core principle: pin to capabilities, not versions

AFNI does not standardize on "GPT-5.5" or any single model. Models are commodities that change monthly; the durable asset is the **capability contract + eval suite** a task requires. Every agent binds to a *capability profile* (e.g., `reasoning-fast`, `voice-realtime`, `extraction-cheap`) plus a golden-dataset quality bar. The **Model Router** resolves that profile to a concrete model at request time. Consequence: when a new frontier model lands, AFNI adopts it by re-running evals and letting the router promote it — **no application rewrite, no re-integration**.

## 2. The Model Router

The Model Router is the enterprise cost-control and quality mechanism. For each request it selects the **cheapest model that meets a measured quality bar** for that task class, with **prompt caching** to avoid re-billing stable context (system prompts, retrieved policy, few-shot exemplars).

- **Input:** task class, capability profile, required quality threshold, latency SLO, cost ceiling.
- **Behavior:** routes simple/deterministic turns to small/instant models; escalates hard, high-stakes turns to frontier reasoning models.
- **Effect (ILLUSTRATIVE):** blended cost per interaction can fall 40–70% versus routing everything to a frontier model, at equal or better measured quality, because most turns do not need frontier reasoning.

```
Request ─▶ Router: meets quality bar at lowest cost?
             ├─ trivial/format  ─▶ GPT-5.5 Instant / Phi        (cheap, fast)
             ├─ standard RAG     ─▶ GPT-5.2 (272k reasoning)
             ├─ hard/agentic     ─▶ GPT-5.5 frontier
             └─ voice turn       ─▶ gpt-realtime-1.5
           + prompt cache on stable context
```

## 3. The model catalog

The Foundry **model catalog** gives the framework a tiered fleet. Right-sizing means matching task to tier, not defaulting to the biggest model.

| Tier | Models (2026) | Strengths | Typical AFNI tasks |
|---|---|---|---|
| **Frontier** | **GPT-5.5** | Deep long-context reasoning, reliable agentic execution, improved computer-use, token efficiency | Subrogation triage, complex multi-tool workflows, ambiguous escalations |
| **Reasoning (272k)** | **GPT-5.4 / GPT-5.2 / GPT-5** | Strong reasoning, large context | RAG synthesis, candidate scoring, QA scoring |
| **Instant** | **GPT-5.5 Instant** (`gpt-chat-latest`) | Low latency, high throughput | Intent classification, short chat turns, guardrail pre-checks |
| **Realtime / audio** | **gpt-realtime-1.5**, **gpt-audio-1.5** | Speech-to-speech, multilingual, tool calling | Live voice agent, agent-assist |
| **o-series** | o3-mini, o1 | Deliberate reasoning at lower cost | Batch analytical passes |
| **Open-weight** | **Llama, Phi** | Cost/edge tiers, self-hosted, private | High-volume PI Index scoring, PII-sensitive local passes |
| **Embeddings** | text-embedding-3-large | Retrieval | Vectorization for all RAG |
| **Fine-tuned / distilled** | Custom on any base | Domain accuracy at small-model cost | AFNI disposition taxonomy, house scoring rubric |

## 4. Right-sizing by task

| Task class | Right-sized tier | Why |
|---|---|---|
| Intent/route, format, classify | Instant / open-weight | Deterministic-ish, latency-sensitive, huge volume |
| Grounded Q&A over KB | Reasoning 272k | Needs context + faithful synthesis |
| 100% interaction scoring (PI Index) | Distilled / open-weight, batched | Cost dominates at full-volume scale |
| Real-time voice turn | gpt-realtime-1.5 | Sub-second speech-to-speech |
| Open-ended agentic workflow | Frontier GPT-5.5 | Planning, tool reliability, long context |

## 5. The frontier-adoption loop

The framework is engineered to ride the frontier continuously rather than migrate in painful, occasional projects.

```
New model in catalog
      │
      ▼
Eval vs GOLDEN SETS  ── fails quality/cost/latency ──▶ shelve, re-test next release
      │ passes
      ▼
SHADOW  (mirror live traffic, no user impact, compare traces)
      │ stable + better/cheaper
      ▼
Router PROMOTES for eligible task classes (canary %)
      │ online eval holds
      ▼
ADOPTED — with NO application rewrite (capability binding unchanged)
```

Because agents bind to capability profiles (§1), promotion is a router/registry change gated by evals, not a code change. This is the mechanism behind the framework's "frontier-ready" design principle.

## 6. Fine-tuning vs RAG vs prompt engineering

Choose the *cheapest technique that closes the measured gap*, in this order:

| Technique | Use when | Cost/effort | Risk |
|---|---|---|---|
| **Prompt engineering** | Behavior is achievable with better instructions, examples, structure | Lowest | Prompt drift; manage as versioned artifact |
| **RAG** | Model lacks *knowledge* (fresh, proprietary, citable facts) | Low–medium | Retrieval quality; needs grounding evals |
| **Fine-tuning / distillation** | Need *behavior/format/style* consistency, a domain taxonomy, or a small cheap model matching a big one | Highest; needs data + eval discipline | Staleness, data governance, re-train on base updates |

Decision guidance:
- **Knowledge problem → RAG**, not fine-tuning. Facts change; retrieval stays current, cites sources, and is cheaper to keep fresh.
- **Behavior/format/cost problem → fine-tune or distill.** Encode AFNI's disposition taxonomy or scoring rubric; distill a frontier "teacher" into an open-weight "student" for full-volume PI Index economics.
- **Default first move → prompt + retrieval.** Fine-tune only when evals prove prompt+RAG cannot meet the bar. Combine freely (a fine-tuned model still uses RAG + guardrails).

## 7. Cost / quality / latency tradeoffs

Every model decision optimizes a three-way tradeoff, made explicit and measurable:

| Lever | Cost | Quality | Latency |
|---|---|---|---|
| Route to smaller model | ↓↓ | ↓ (guard with quality bar) | ↓↓ |
| Prompt caching | ↓↓ | = | ↓ |
| Frontier for hard turns only | ↓ (targeted spend) | ↑↑ where it matters | ↑ on those turns |
| Distill frontier → open-weight | ↓↓ at scale | ≈ (validated) | ↓ |
| PTU on critical path | ↑ fixed | = | ↓↓ predictable |
| Larger context / more reasoning | ↑↑ | ↑ | ↑↑ |

The router encodes these tradeoffs as policy so they are enforced automatically per task class, and every choice is observable in unified tracing with token-level cost attribution for FinOps showback.

## 8. Governance of the model fleet

- **Golden datasets** per task class are the source of truth for "good enough"; they grow from production feedback (thumbs, QA, PI Index).
- **Evaluation-in-CI** gates any model or prompt change; nothing ships without passing quality, safety, cost, and latency budgets.
- **Registry** pins the exact model/prompt/capability binding per deployment for reproducibility and instant rollback.
- **Content Safety** (prompt shields, groundedness, PII) wraps every model regardless of tier.

*All cost, quality, and latency figures in this document are ILLUSTRATIVE and must be replaced with AFNI-measured actuals.*
