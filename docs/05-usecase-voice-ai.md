# Use Case 1 — Voice AI for Contact Centers

## Executive summary

Afni's core business is voice. Millions of inbound and outbound interactions flow through Afni's contact centers each year across Acquisition & Growth, Care & Retention, Collections, and P&C Insurance. This use case applies Evoke's proposed multi-agent LLMOps platform — built on Microsoft **Azure AI Foundry** — to that voice channel in three complementary modes. The design goal is not to replace agents wholesale, but to **contain the calls that can be safely automated, make every human agent measurably better in real time, and turn 100% of calls into structured quality and coaching signal.**

All three modes reuse the same governed platform, the same **supervisor-orchestrator** agent pattern, and the same deterministic guardrails wrapped around probabilistic agents. This is what makes the investment compounding rather than one-off.

## The three operating modes

### Mode A — Autonomous voice agent (containable calls)

- **Problem:** A large share of call volume is repetitive and low-complexity — balance and status inquiries, payment reminders and promise-to-pay capture, appointment and identity verification, simple Care requests. These calls consume agent capacity, drive staffing cost, and create long queues at peaks, yet rarely need human judgment.
- **Solution:** A **speech-to-speech** autonomous agent (Azure OpenAI **gpt-realtime**) handles the full call for scoped, pre-approved call types, with sub-second turn latency for natural conversation. It authenticates the caller, retrieves grounded answers, executes transactions through secure tools, and **warm-transfers to a human** the moment the interaction leaves its approved scope or a compliance/sentiment trigger fires.
- **Agents involved:** Orchestrator/Supervisor, Intent/Router, Knowledge/RAG, Action/Tooling, Compliance/Guardrail, Sentiment/Emotion, Escalation/Handoff, Summarization/QA.
- **Data/systems touched:** CRM, billing/payment systems, scheduling systems, knowledge base (via Azure **AI Search**, hybrid + semantic ranker), conversation state in **Cosmos DB**.
- **KPIs:** containment/deflection rate, promise-to-pay rate (Collections), transaction success rate, handoff quality, compliance adherence.

### Mode B — Real-time agent-assist copilot

- **Problem:** Human agents juggle multiple screens, dense policy content, and strict compliance scripting while managing an emotional caller. Ramp time for new hires is long, and quality is uneven.
- **Solution:** A live copilot that transcribes the call in real time, surfaces **next-best-action** and grounded knowledge snippets, detects rising frustration, delivers **must-say / do-not-say compliance nudges**, and auto-drafts the summary and disposition at wrap. The agent stays in control; the copilot advises.
- **Agents involved:** Knowledge/RAG, Action/Tooling (suggested, agent-confirmed), Compliance/Guardrail, Sentiment/Emotion, Summarization/QA. Orchestrator coordinates streaming context.
- **Data/systems touched:** Real-time transcription stream, knowledge base, CRM (read + agent-confirmed write), agent desktop overlay.
- **KPIs:** AHT, FCR, agent ramp time, CSAT, after-call-work time, compliance adherence.

### Mode C — Post-call analytics & QA

- **Problem:** Today QA is sampled — typically 5–10% of calls (illustrative; Afni actuals confirmed in discovery) — leaving most interactions unreviewed and coaching reactive.
- **Solution:** Every call is transcribed, summarized, scored against the QA rubric, and screened for compliance breaches and coaching opportunities. **LLM-as-judge** scoring is calibrated against human QA and routed for human review on low-confidence or high-stakes items.
- **Agents involved:** Summarization/QA, Compliance/Guardrail, Sentiment/Emotion.
- **Data/systems touched:** Call recordings, transcripts, QA scorecard system, **Fabric / Data Lake** for analytics, Purview for lineage.
- **KPIs:** QA coverage (→100%), QA score, compliance breach detection rate, coaching cycle time.

## End-to-end call flow

```
                          +-----------------------------+
  Caller (PSTN/SIP) ----> |  Telephony / CCaaS          |
                          |  Genesys / NICE / Five9 /   |
                          |  Amazon Connect  OR          |
                          |  Azure Communication Services|
                          +--------------+--------------+
                                         | media stream (SIP/WebRTC)
                                         v
                          +-----------------------------+
                          |  Realtime Speech Layer      |
                          |  gpt-realtime (S2S)         |
                          |  Azure AI Speech (fallback) |
                          +--------------+--------------+
                                         | text + audio + events
                                         v
                          +-----------------------------+
                          |  ORCHESTRATOR / SUPERVISOR  |
                          |  (Semantic Kernel/AutoGen)  |
                          +---+------+------+------+----+
                              |      |      |      |
                 +------------+  +---+--+  +-+----+ +-----------+
                 v               v      v  v      v             v
          +-----------+  +-----------+  +-----------+  +----------------+
          | Intent/   |  | Knowledge/|  | Action/   |  | Compliance/    |
          | Router    |  | RAG       |  | Tooling   |  | Guardrail      |
          +-----------+  +-----+-----+  +-----+-----+  +--------+-------+
                               |              |                 |
                               v              v                 |
                        +-------------+  +-----------+          |
                        | Azure AI    |  | Systems of|          |
                        | Search (KB) |  | Record:   |          |
                        +-------------+  | CRM/billing|         |
                                         | HRIS/sched |         |
                                         +-----------+          |
                              +----------------+----------------+
                              v                v
                       +-----------+    +----------------+
                       | Sentiment |    | Escalation/    |
                       | /Emotion  +--->| Handoff (warm  +---> Human agent
                       +-----------+    | transfer +ctx) |     (Mode B copilot)
                                        +----------------+
                                         |
                                         v
                                 +----------------+
                                 | Summarization/ |---> QA store / Fabric
                                 | QA (Mode C)    |     (analytics + coaching)
                                 +----------------+
```

## Multi-agent breakdown

| Agent | Responsibility | Pattern | Key Azure services |
|---|---|---|---|
| Orchestrator/Supervisor | Owns the turn; routes, sequences, and arbitrates specialist agents; enforces scope | Supervisor-orchestrator | Azure AI Agent Service, Semantic Kernel / AutoGen |
| Intent/Router | Classifies caller intent and call type; decides containment vs. handoff | Sequential | GPT-4o-mini |
| Knowledge/RAG | Retrieves grounded, cited answers from policy/KB | Concurrent | Azure AI Search, embeddings |
| Action/Tooling | Executes transactions against systems of record via secure tools | Hand-off | Azure Functions, APIM, Key Vault |
| Compliance/Guardrail | Enforces disclosures, PCI pause/mask, TCPA, must-say/do-not-say | Deterministic wrapper | Azure AI Content Safety, policy layer |
| Sentiment/Emotion | Detects frustration/escalation cues; triggers handoff | Concurrent/reflection | GPT-4o, Speech prosody |
| Escalation/Handoff | Warm transfer with full context packet to a human | Human-in-the-loop | CCaaS APIs, Cosmos DB |
| Summarization/QA | Post-call summary, disposition, QA score | Reflection/critic | GPT-4o, LLM-as-judge |

The defining principle is **deterministic guardrails around probabilistic agents**: the Compliance/Guardrail agent and the policy layer can force, block, or redirect any turn regardless of what the language model proposes.

## Latency, telephony, and compliance

**Latency.** Natural voice requires sub-second turn latency. Mode A uses realtime **speech-to-speech** (gpt-realtime) to avoid the STT → LLM → TTS round-trip penalty; Azure **AI Speech** (with custom neural voice) serves as a hybrid/fallback path and for languages or controls the realtime model does not cover. Barge-in, endpointing, and streaming partials are handled at the speech layer.

**Telephony integration.** The integration layer is deliberately **generic**: Afni's existing CCaaS (Genesys, NICE, Five9, Amazon Connect, etc.) connects via SIP/media-streaming APIs, while **Azure Communication Services** is recommended for any greenfield or overflow voice. No single incumbent is assumed; the orchestrator and agents are decoupled from the carrier/CCaaS.

**Compliance (non-negotiable).**

| Regime | Control in the platform |
|---|---|
| TCPA | Consent verification and calling-window enforcement on outbound; opt-out honored by Compliance agent |
| PCI-DSS | Automatic **pause/mask** of card capture; audio and transcript redaction; agent never "hears" full PAN |
| HIPAA | PHI handling for healthcare clients; BAA-aligned data flows; least-privilege tool access |
| Recording/consent | Disclosure playback and consent capture logged with immutable audit trail |
| Disclosures | Must-say scripting enforced deterministically before transaction completion |

PII detection/redaction is delivered through **Content Safety + Microsoft Purview**; all flows carry audit trails and lineage.

## KPI framework

| KPI | Baseline (illustrative) | Target impact | Mode |
|---|---|---|---|
| Containment / deflection | — | 20–40% of eligible call types | A |
| Average Handle Time (AHT) | — | 15–25% reduction | A, B |
| First-Contact Resolution (FCR) | — | +5–15 pts | B |
| CSAT | — | +3–8 pts | A, B |
| QA coverage | 5–10% | 100% | C |
| Compliance adherence | — | measurable uplift, fewer breaches | A, B, C |
| Agent ramp time | — | 20–40% faster | B |
| Promise-to-pay (Collections) | — | uplift on reminder calls | A |

All figures are illustrative placeholders; Afni actuals replace them during Phase 0 discovery.

## Implementation approach

1. **Discovery & scoping** — inventory call types, rank by containment potential and risk; capture baselines; define guardrail policies per client/regulatory context.
2. **Copilot first (lowest risk)** — deploy Mode B agent-assist on one program with a human always in control; build the offline eval harness and observability baseline.
3. **Autonomous, tightly scoped** — introduce Mode A on 1–2 low-risk call types behind canary/shadow deployment with automatic handoff.
4. **QA at scale** — turn on Mode C across the pilot program; calibrate LLM-as-judge against human QA.
5. **Harden & expand** — online A/B and shadow eval, FinOps token metering via APIM, guardrail hardening, then scale to additional programs and geos.

## Suggested pilot scope

- **One contact-center program**, single line of business (recommend Care & Retention or Collections reminders).
- **Mode B copilot** for all agents on that program + **Mode A** on 1–2 clearly containable call types + **Mode C** QA across 100% of the program's calls.
- **8–12 week pilot**, success gated on containment, AHT, QA coverage, and zero compliance regressions before promotion, consistent with the Crawl→Walk roadmap.
