# Implementation Roadmap

## Purpose

This roadmap sequences Afni's GenAI program as a disciplined **Crawl / Walk / Run** journey across roughly 9–12 months, beginning with a four-week foundations sprint. Each phase states its objectives, workstreams, key deliverables, exit criteria, and the use-case capabilities that land. The sequencing deliberately front-loads governance, security, and evaluation so that speed in later phases never outruns control — the same rigor Afni applies to running contact centers.

## Phase Overview

| Phase | Timeline | Theme | Headline outcome |
| --- | --- | --- | --- |
| **Phase 0** | Weeks 0–4 | Foundations & Discovery | Secure landing zone + validated pilots |
| **Phase 1 (Crawl)** | Months 1–3 | Platform MVP + first pilots | Agent-assist copilot + HR screening pilots live |
| **Phase 2 (Walk)** | Months 4–7 | Autonomy + scale-up | Scoped autonomous voice agent; HR voice pre-screen; CoE stood up |
| **Phase 3 (Run)** | Months 8–12 | Scale + flywheel | Multi-program/geo, subrogation & QA analytics, full governance |

## Phase 0 — Foundations & Discovery (Weeks 0–4)

**Objectives:** Establish the secure Azure foundation, agree success metrics, and validate the two flagship pilots against real Afni data and constraints.

**Workstreams:**
- Azure landing zone: subscriptions, hub-and-spoke VNet, private endpoints, Entra ID/RBAC, Key Vault, Defender for Cloud baseline.
- AI Foundry hub/project structure and model-catalog access (GPT-4o, GPT-4o-mini, gpt-realtime, embeddings).
- Use-case intake and risk-tiering for Voice AI and HR; success-metric definition; data-access and residency mapping.
- Discovery: current AHT/QA/containment and hiring-funnel baselines to replace illustrative figures.

**Key deliverables:** Landing zone + security baseline; reference architecture; intake + risk-tier register; KPI baselines; Phase 1 backlog.

**Exit criteria:** Secure environment operational; two pilots scoped and risk-tiered; data access confirmed; governance cadence initiated.

## Phase 1 — Crawl (Months 1–3)

**Objectives:** Ship a platform MVP and prove value with two low-risk, human-in-the-loop pilots.

**Workstreams:**
- Platform MVP: shared multi-agent pattern (supervisor + intent/RAG/action/compliance agents), prompt/agent registry, Azure AI Search RAG, Content Safety guardrails.
- LLMOps baseline: offline evaluation harness (golden sets + LLM-as-judge + human review), CI/CD with test gates, observability baseline (OpenTelemetry + App Insights).
- **Voice AI capability landed:** agent-assist copilot pilot on one contact-center program (live transcription, next-best-action, knowledge surfacing, sentiment, auto-summary).
- **HR capability landed:** resume screening/ranking pilot + JD generation, under the fairness monitor (assistive only).

**Key deliverables:** Platform MVP; two live pilots; offline eval harness; observability dashboards; model/system cards for piloted systems.

**Exit criteria:** Pilots meet quality/safety gates; measurable lift vs. baseline; no Sev-1 safety incidents; promotion process exercised.

## Phase 2 — Walk (Months 4–7)

**Objectives:** Introduce scoped autonomy, extend HR, harden operations, and stand up the CoE as a durable function.

**Workstreams:**
- **Voice AI capability landed:** autonomous voice agent for pre-approved containable call types (FAQs, payment reminders, verification) with sub-second turn latency via gpt-realtime; escalation/handoff with warm transfer; PCI pause-and-mask.
- **HR capability landed:** conversational voice pre-screen (reusing the voice platform) + scheduling agent (ATS/calendar); candidate Q&A concierge.
- Online evaluation: A/B and shadow testing; drift monitoring.
- Hardening: FinOps (token metering via API Management, showback, model right-sizing, caching), guardrail red-teaming, security posture review.
- **CoE stood up** with roles, RACI, and intake operating steadily.

**Key deliverables:** Scoped autonomous voice agent; HR voice pre-screen + scheduling; online eval/A-B framework; FinOps dashboards + budgets; CoE operational; Tier 3 bias audit for HR scoring assist.

**Exit criteria:** Autonomous agent hits containment/latency SLOs within guardrails; CoE running intake/governance cadence; FinOps budgets and alerts active; red-team findings remediated.

## Phase 3 — Run (Months 8–12)

**Objectives:** Scale across programs and geographies, add new use cases, and close the continuous-improvement flywheel under full governance.

**Workstreams:**
- Scale Voice AI and HR to multiple programs across US/Mexico/Philippines with residency-aware deployment.
- **New capabilities landed:** subrogation support agents (P&C insurance) and post-call QA analytics (100% call QA vs. sampled today, coaching).
- Full governance: quarterly Governance Board, complete audit trails, recurring red-teaming, compliance evidence automation.
- Resilience: disaster recovery / multi-region failover; capacity planning.
- Continuous-improvement flywheel: feedback (thumbs, QA, incidents) → dataset → re-evaluation → promotion.

**Key deliverables:** Multi-program/geo deployment; subrogation + QA analytics use cases; DR runbook; full governance operating; self-sustaining improvement loop.

**Exit criteria:** Multiple programs in production against outcome KPIs; DR tested; governance and FinOps steady-state; Afni CoE operating with Evoke in advisory mode.

## Milestone Table

| Milestone | Target | Phase |
| --- | --- | --- |
| Secure landing zone live | Week 4 | 0 |
| Platform MVP + eval harness | Month 2 | 1 |
| Agent-assist copilot + HR screening pilots live | Month 3 | 1 |
| Autonomous voice agent (scoped) in production | Month 5 | 2 |
| HR voice pre-screen + scheduling live | Month 6 | 2 |
| CoE + FinOps + online eval operational | Month 7 | 2 |
| Subrogation + QA analytics use cases live | Month 10 | 3 |
| DR tested; full governance steady-state | Month 12 | 3 |

## Dependencies & Staffing Ramp

- **Dependencies:** Phase 0 landing zone and data access gate everything; CCaaS/telephony integration access gates autonomous voice (Phase 2); ATS/HRIS integration gates HR scheduling; client contractual approvals gate any regulated-program scale-up; bias audit gates HR Tier 3 promotion.
- **Staffing ramp:** Evoke leads with a lean senior team in Phase 0 (architect, LLMOps, security, RAI). The team expands in Phase 1–2 with prompt/agent and data engineers and embedded ops/HR SMEs as spokes activate. Through Phase 3, capability transfer shifts delivery ownership to Afni's CoE, with Evoke moving to an advisory footprint — matching the enablement plan in the operating model.

## Guiding Principle

Each phase is a gate, not just a calendar marker: value is proven, controls are in place, and only then does scope expand. This is how Afni captures near-term productivity gains while building a durable, Responsible-AI-compliant capability rather than a fragile collection of pilots. All financial and percentage figures elsewhere in this proposal remain illustrative until validated against Afni actuals during Phase 0 discovery.
