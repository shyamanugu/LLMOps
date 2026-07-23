# Voice Agent

> **Confidential — AFNI, Inc. Internal.** Prepared by the AFNI Office of GenAI Architecture.
> All metrics in this document are **ILLUSTRATIVE placeholders** pending discovery with AFNI actuals.

## Overview

The **Voice Agent** is AFNI's real-time, multi-agent voice automation and agent-assist capability for the contact center. It is one of AFNI's three flagship LLMOps initiatives and the primary generator of interaction data for the other two: transcripts and signals feed the **Performance Intelligence Index (PI Index)**, and the same speech stack is reused for **Hiring Intelligence** voice pre-screens.

The Voice Agent operates in **three complementary modes** on one platform:

```
+=====================================================================+
|                        AFNI VOICE AGENT                             |
+=====================================================================+
|                                                                     |
|   MODE A                 MODE B                 MODE C              |
|   Agent-Assist           Autonomous             Post-Call          |
|   Copilot                Voice Agent            Analytics          |
|   (human in loop)        (containable calls)    (100% of calls)    |
|        |                      |                      |             |
|        v                      v                      v             |
|   Live rep hears/        Bot handles FAQs,      Every transcript   |
|   sees next-best-        verification,          scored + mined     |
|   action, KB, sentiment  reminders; warm        --> feeds          |
|   compliance nudges      handoff to human       PI INDEX           |
|                                                                     |
+=====================================================================+
        Sub-second speech-to-speech (gpt-realtime) · Azure fallback
```

All three modes reuse the shared multi-agent pattern: an **Orchestrator/Supervisor** routes to specialist agents — **Intent/Router, Knowledge/RAG, Action/Tooling, Compliance/Guardrail, Sentiment, Escalation/Handoff, and Summarization/QA & Scoring**. Deterministic guardrails wrap the probabilistic agents.

---

## Mode A — Agent-Assist Copilot

**Problem.** Live human reps carry heavy cognitive load: searching knowledge, remembering compliance language, disposition-coding after each call, and de-escalating frustrated callers. New-hire ramp is slow, quality is uneven, and after-call work inflates handle time.

**Solution.** A real-time copilot that listens to the live call, transcribes both channels, and surfaces guidance in the agent desktop: next-best-action, knowledge snippets (grounded via RAG), live sentiment, compliance nudges (e.g., required disclosures), and an auto-drafted summary and disposition at wrap-up. The human agent remains fully in control.

**Agents involved.** Intent/Router (classifies caller need) → Knowledge/RAG (retrieves grounded answers from Azure AI Search) → Compliance/Guardrail (prompts required disclosures, flags risky language) → Sentiment (tracks trajectory, cues de-escalation) → Summarization/QA (auto-summary + disposition).

**Systems touched.** CCaaS media stream (SIP/APIs), Azure AI Speech (STT), gpt-realtime, Azure AI Search + Document Intelligence (knowledge), CRM (customer context, disposition write-back), agent-assist desktop.

**KPIs.** After-call work time, agent ramp time, knowledge-lookup rate, compliance-nudge adherence, CSAT.

---

## Mode B — Autonomous Voice Agent

**Problem.** A meaningful share of inbound/outbound volume is routine and containable — FAQs, identity verification, appointment scheduling, balance and payment reminders — yet consumes trained-agent capacity during peak load.

**Solution.** An autonomous, sub-second speech-to-speech agent that handles **containable call types** end to end, with a **warm human handoff** whenever intent falls outside scope, sentiment degrades, or a compliance boundary is reached. Scope is deliberately narrow at launch and expanded only after evaluation gates pass.

**Agents involved.** Intent/Router → Action/Tooling (executes verification, scheduling, payment intents via secure APIs) → Compliance/Guardrail (TCPA consent checks, PCI pause/mask) → Escalation/Handoff (warm transfer with full context) → Summarization/QA.

**Systems touched.** Telephony (generic CCaaS integration layer; **Azure Communication Services** for greenfield outbound/inbound), gpt-realtime speech-to-speech, Azure AI Speech (custom neural voice, TTS/STT fallback), CRM/billing/scheduling APIs (via APIM), Azure AI Content Safety.

**KPIs.** Containment/deflection rate, contained-call AHT, First Contact Resolution (FCR), successful-handoff rate, compliance adherence, CSAT.

---

## Mode C — Post-Call Analytics (Feeds the PI Index)

**Problem.** Traditional QA samples only 2–10% of interactions, so most calls are never reviewed, coaching is slow and subjective, and risk surfaces late.

**Solution.** Every completed interaction — whether handled by a human (Mode A) or the autonomous agent (Mode B) — is transcribed, redacted, and analyzed. The output does not stop at a summary: it becomes structured **signals** that feed the **PI Index** (see `15-performance-intelligence-index.md`), where seven analysis agents score 100% of interactions and roll them up into a single explainable index per agent, team, program, and client.

**Agents involved.** Summarization/QA & Scoring produces the analytic record; the PI Index scoring pipeline consumes it. Compliance/Guardrail applies PII detection and redaction before storage.

**Systems touched.** Azure AI Speech (batch transcription), Content Safety + Microsoft Purview (PII detection/redaction, lineage), Microsoft Fabric / Data Lake (PI Index store), CRM dispositions and outcomes.

**KPIs.** QA coverage (target 100%), coaching cycle time, anomaly/compliance-risk lead time.

---

## Technology and Latency

- **Speech-to-speech:** Azure **OpenAI gpt-realtime** for sub-second turn latency; **Azure AI Speech** (STT/TTS, custom neural voice) as hybrid/fallback and for batch transcription.
- **Orchestration:** Azure AI Agent Service with Semantic Kernel / AutoGen (converging into the Microsoft Agent Framework).
- **Gateway:** Azure API Management for token metering, quotas, caching, and model routing.
- **Telephony:** integrate the existing CCaaS estate (Genesys, NICE, Five9, Amazon Connect) via SIP/APIs; the integration layer is kept **generic**. **Azure Communication Services** provides greenfield voice.

## Compliance

- **TCPA** — consent capture and honoring for outbound; calling-window and DNC enforcement.
- **PCI-DSS** — automatic **pause/mask** of audio and transcript during card capture; no card data persisted in agent context.
- **HIPAA** — for healthcare clients: minimum-necessary handling, PHI redaction, BAA-aligned data flows.
- **Call recording & consent** — jurisdiction-aware disclosures, recording notices, and consent logging.
- Deterministic guardrails (Content Safety prompt shields, groundedness checks, PII detection) wrap every model call.

## KPI Table (ILLUSTRATIVE)

| KPI | Baseline (illustrative) | Target (illustrative) | Mode(s) |
|---|---|---|---|
| Containment / deflection (eligible calls) | — | 20–40% | B |
| Average Handle Time (AHT) | — | −15–25% | A, B |
| First Contact Resolution (FCR) | — | +5–10 pts | A, B |
| CSAT | — | +3–8 pts | A, B |
| Compliance adherence | — | 99%+ | A, B, C |
| Agent ramp time | — | −20–30% | A |
| QA coverage | 2–10% | 100% | C |

## Implementation Approach and Pilot Scope

1. **Foundations (Weeks 0–4).** Landing zone, security baseline, CCaaS media-stream integration, PII redaction, consent/recording controls, evaluation golden sets.
2. **Crawl pilot (Months 1–3).** Deploy **Mode A agent-assist** on **one program**; stand up **Mode C post-call analytics** feeding the PI Index MVP (offline scoring of historical interactions).
3. **Walk (Months 4–7).** Introduce **Mode B autonomous** handling for a **narrow set of containable call types** with warm handoff; add online evaluation (A/B, shadow), FinOps token metering, and near-real-time analytics.
4. **Run (Months 8–12).** Scale across programs and geographies; expand containable scope; extend custom neural voice; harden disaster recovery.

**Pilot success criteria (illustrative):** containment and AHT targets met on scoped call types; compliance adherence ≥ 99%; agent-assist CSAT lift on the pilot program; 100% of pilot interactions scored by the PI Index.

## Synergy Across the Three Initiatives

- **→ PI Index:** Voice Agent transcripts and signals are the primary data source; Mode C makes 100% scoring possible.
- **→ Hiring Intelligence:** the same gpt-realtime + Azure AI Speech stack powers optional **candidate voice pre-screens**, reusing orchestration, guardrails, and telephony rather than rebuilding them.

Build the voice platform once; all three flagship initiatives — and future use cases such as subrogation — reuse it.
