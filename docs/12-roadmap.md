# Implementation Roadmap

## Purpose

This roadmap sequences AFNI's GenAI program as a disciplined **Crawl / Walk / Run** journey across roughly 9–12 months, beginning with a four-week foundations sprint. Each phase states its objectives, workstreams, key deliverables, exit criteria, and the capabilities that land for the three flagship initiatives — the **Voice Agent**, the **Performance Intelligence Index (PI Index)**, and **Hiring Intelligence**. The sequencing deliberately front-loads governance, security, and evaluation so that speed in later phases never outruns control — the same rigor AFNI applies to running contact centers.

## Phase Overview

| Phase | Timeline | Theme | Headline outcome |
| --- | --- | --- | --- |
| **Phase 0** | Weeks 0–4 | Foundations & Discovery | Secure landing zone + three validated pilots scoped |
| **Phase 1 (Crawl)** | Months 1–3 | Platform MVP + first pilots | Voice Agent copilot + PI Index MVP + Hiring screening pilot live |
| **Phase 2 (Walk)** | Months 4–7 | Autonomy + scale-up | Autonomous Voice Agent; PI Index live/coaching; Hiring voice pre-screen; CoE stood up |
| **Phase 3 (Run)** | Months 8–12 | Scale + flywheel | Multi-program/geo, subrogation & knowledge, full governance |

## Phase 0 — Foundations & Discovery (Weeks 0–4)

**Objectives:** Establish the secure Azure foundation, agree success metrics, and validate the three flagship pilots against real AFNI data and constraints.

**Workstreams:**
- Azure landing zone: subscriptions, hub-and-spoke VNet, private endpoints, Entra ID/RBAC, Key Vault, Defender for Cloud baseline.
- AI Foundry hub/project structure and model-catalog access (GPT-4o, GPT-4o-mini, gpt-realtime, embeddings).
- Use-case intake and risk-tiering for the Voice Agent, PI Index, and Hiring Intelligence; success-metric definition; data-access and residency mapping (US/Mexico/Philippines).
- Discovery: current AHT/QA-sampling/containment, scoring baselines, and hiring-funnel baselines to replace illustrative figures.

**Key deliverables:** Landing zone + security baseline; reference architecture; intake + risk-tier register (PI Index scoring and Hiring flagged Tier 3); KPI baselines; Phase 1 backlog.

**Exit criteria:** Secure environment operational; three pilots scoped and risk-tiered; data access confirmed; governance cadence initiated.

## Phase 1 — Crawl (Months 1–3)

**Objectives:** Ship a platform MVP and prove value with three low-risk, human-in-the-loop pilots.

**Workstreams:**
- Platform MVP: shared multi-agent pattern (supervisor + intent/RAG/action/compliance/summarization-scoring agents), prompt/agent registry, Azure AI Search RAG, Content Safety guardrails.
- LLMOps baseline: offline evaluation harness (golden sets + LLM-as-judge + human review), CI/CD with test gates, observability baseline (OpenTelemetry + App Insights).
- **Voice Agent capability landed:** agent-assist copilot pilot on one contact-center program (live transcription, next-best-action, knowledge surfacing, sentiment, auto-summary).
- **PI Index capability landed:** MVP offline scoring on historical interactions — dimension scores and composite index computed on a back-catalog of transcripts, validated against human QA calibration.
- **Hiring Intelligence capability landed:** resume screening/ranking pilot + JD generation, under the fairness monitor (assistive only; humans decide).

**Key deliverables:** Platform MVP; three live pilots; offline eval harness; observability dashboards; model/system cards for piloted systems.

**Exit criteria:** Pilots meet quality/safety gates; PI Index scores agree with human calibration within threshold; measurable lift vs. baseline; no Sev-1 safety incidents; promotion process exercised.

## Phase 2 — Walk (Months 4–7)

**Objectives:** Introduce scoped autonomy, take the PI Index live, extend Hiring, harden operations, and stand up the CoE as a durable function.

**Workstreams:**
- **Voice Agent capability landed:** autonomous voice agent for pre-approved containable call types (FAQs, payment reminders, verification) with sub-second turn latency via gpt-realtime; escalation/handoff with warm transfer; PCI pause-and-mask.
- **PI Index capability landed:** live / near-real-time scoring of 100% of interactions; coaching-recommendation workflows, anomaly alerts, and QA calibration/appeals in production.
- **Hiring Intelligence capability landed:** conversational voice pre-screen (reusing the Voice Agent platform) + scheduling agent (ATS/calendar); candidate Q&A concierge.
- Online evaluation: A/B and shadow testing; drift monitoring.
- Hardening: FinOps (token metering via API Management, showback per initiative, model right-sizing, caching), guardrail red-teaming, security posture review.
- **CoE stood up** with AFNI-internal roles, RACI, and intake operating steadily.

**Key deliverables:** Autonomous Voice Agent; PI Index live + coaching workflows; Hiring voice pre-screen + scheduling; online eval/A-B framework; FinOps dashboards + budgets; CoE operational; Tier 3 bias audit for PI Index scoring and Hiring scoring assist.

**Exit criteria:** Autonomous agent hits containment/latency SLOs within guardrails; PI Index live at scale with fairness checks passing; CoE running intake/governance cadence; FinOps budgets and alerts active; red-team findings remediated.

## Phase 3 — Run (Months 8–12)

**Objectives:** Scale across programs and geographies, add new use cases, and close the continuous-improvement flywheel under full governance.

**Workstreams:**
- Scale the Voice Agent, PI Index, and Hiring Intelligence to multiple programs across US/Mexico/Philippines with residency-aware deployment.
- **New capabilities landed:** subrogation support agents (P&C insurance) and a knowledge assistant, both reusing the shared multi-agent pattern.
- Full governance: quarterly Governance Board, complete audit trails, recurring red-teaming, compliance evidence automation.
- Resilience: disaster recovery / multi-region failover; capacity planning.
- Continuous-improvement flywheel: feedback (thumbs, QA, PI Index calibration, incidents) → dataset → re-evaluation → promotion.

**Key deliverables:** Multi-program/geo deployment; subrogation + knowledge-assistant use cases; DR runbook; full governance operating; self-sustaining improvement loop.

**Exit criteria:** Multiple programs in production against outcome KPIs; DR tested; governance and FinOps steady-state; AFNI CoE operating the platform end to end.

## Milestone Table

| Milestone | Target | Phase |
| --- | --- | --- |
| Secure landing zone live | Week 4 | 0 |
| Platform MVP + eval harness | Month 2 | 1 |
| Voice Agent copilot + PI Index MVP + Hiring screening pilot live | Month 3 | 1 |
| Autonomous Voice Agent (scoped) in production | Month 5 | 2 |
| PI Index live + coaching; Hiring voice pre-screen + scheduling | Month 6 | 2 |
| CoE + FinOps + online eval operational | Month 7 | 2 |
| Subrogation + knowledge assistant live | Month 10 | 3 |
| DR tested; full governance steady-state | Month 12 | 3 |

## Dependencies & Staffing Ramp

- **Dependencies:** Phase 0 landing zone and data access gate everything; historical transcript access gates the PI Index MVP (Phase 1); CCaaS/telephony integration access gates autonomous voice and PI Index near-real-time scoring (Phase 2); ATS/HRIS integration gates Hiring scheduling; client contractual approvals gate any regulated-program scale-up; bias audit gates PI Index and Hiring Tier 3 promotion.
- **Staffing ramp:** A lean senior AFNI CoE team (architect, LLMOps, security, RAI) leads Phase 0. The team expands in Phase 1–2 with prompt/agent and data engineers and embedded ops/HR SMEs as spokes activate. Through Phase 3, AFNI's CoE owns delivery and operations end to end — matching the enablement plan in the operating model.

## Guiding Principle

Each phase is a gate, not just a calendar marker: value is proven, controls are in place, and only then does scope expand. This is how AFNI captures near-term productivity gains while building a durable, Responsible-AI-compliant capability rather than a fragile collection of pilots. All financial and percentage figures in this proposal are **ILLUSTRATIVE** and remain so until validated against AFNI actuals during Phase 0 discovery.
