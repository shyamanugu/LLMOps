# Proposal Bible — shared context for all Afni LLMOps documents

> This file is the single source of truth for terminology, numbers, architecture, and positioning.
> Every document in `docs/`, the PPTX, the DOCX, and the HTML must stay consistent with it.

## Who / what
- **Client:** Afni, Inc. — global Business Process Outsourcing (BPO) & customer engagement provider. Founded 1936, HQ Bloomington, Illinois. ~3,400+ employees. Sites across US (IL, AZ, KY, TX, MO, AL), Mexico, and the Philippines, plus an **Afni@Home** remote workforce program.
- **Afni service lines:** Acquisition & Growth; Care & Retention; Collections; P&C Insurance (including **subrogation**); delivered under a partnership/**Gainshare** commercial model. Industries served: insurance, financial services, telecom, healthcare, fitness, media.
- **Vendor:** Evoke Technologies (staffing + delivery partner). **Author:** Shyam, Senior GenAI Architect embedded at Afni; background in multi-agent systems on Azure AI Foundry.
- **Ask:** A proposal to stand up **enterprise-grade LLMOps** enabling **multi-agent GenAI systems**, end-to-end, with two flagship use cases: (1) **Voice AI for contact centers**, (2) **AI-driven HR recruitment**.

## Positioning / vision statement
"Give Afni one secure, governed Azure platform to build, evaluate, deploy, govern, and continuously improve fleets of cooperating AI agents — with the same operational rigor Afni already applies to running contact centers."

## Primary cloud & tooling recommendation (be specific and consistent)
- **Core platform:** Microsoft **Azure AI Foundry** (formerly Azure AI Studio) — model catalog, **Azure AI Agent Service**, project/hub structure, evaluations, content safety.
- **Models:** Azure **OpenAI** GPT-4o / GPT-4o-mini / **gpt-realtime (speech-to-speech / realtime API)**; Azure **AI Speech** (STT/TTS, custom neural voice) as fallback/hybrid; embeddings (text-embedding-3-large). Note open-weight options in catalog (Llama, Phi) for cost/on-prem-ish scenarios.
- **Orchestration frameworks:** **Semantic Kernel** and/or **AutoGen** (converging into the Microsoft Agent Framework); Azure AI Agent Service for hosted agents + tool calling.
- **RAG / knowledge:** Azure **AI Search** (hybrid + semantic ranker), vectors in AI Search / Cosmos DB; document ingestion via Azure AI Document Intelligence.
- **Data & state:** Azure Cosmos DB (agent state, conversation memory), Azure Data Lake / Fabric (analytics), Azure SQL where relational.
- **Compute & serving:** Azure Container Apps / AKS; Azure API Management (gateway, quotas, token metering); Azure Functions for event glue.
- **Telephony / contact center:** integrate with existing CCaaS (e.g., Genesys, NICE, Five9, Amazon Connect) via SIP/APIs; **Azure Communication Services** for greenfield voice. Do not assume a specific incumbent — keep integration-layer generic.
- **Guardrails/safety:** Azure **AI Content Safety** (prompt shields, groundedness detection, protected material, PII), plus policy-layer guardrails.
- **LLMOps toolchain:** Prompt flow / prompt registry; Azure AI evaluation SDK (offline + online eval); **Azure DevOps / GitHub Actions** CI/CD; **Azure Monitor + Application Insights + OpenTelemetry (GenAI semantic conventions)** for tracing/observability; **Microsoft Purview** for data governance/lineage; **Microsoft Entra ID** for identity; **Azure Key Vault** for secrets; **Microsoft Defender for Cloud** for posture.
- **Alternatives to acknowledge briefly:** AWS Bedrock Agents; Google Vertex AI Agent Builder. Recommend Azure as primary (Microsoft enterprise footprint, regulated-workload maturity, integrated agent + safety + governance).

## The multi-agent pattern (reused across both use cases)
Orchestrator/Supervisor agent routes to specialist agents:
- **Intent/Router agent** — classify caller/candidate intent, route.
- **Knowledge/RAG agent** — retrieve grounded answers from policies/KB.
- **Action/Tooling agent** — call systems of record (CRM, HRIS/ATS, billing) via secure tools/APIs.
- **Compliance/Guardrail agent** — enforce disclosures, PII redaction, do-not-say / must-say, TCPA, fairness.
- **Sentiment/Emotion agent** — detect frustration/escalation cues.
- **Escalation/Handoff agent** — warm transfer to a human with full context.
- **Summarization/QA agent** — post-interaction summary, disposition, QA scoring.
Patterns to name: supervisor-orchestrator, sequential, concurrent, hand-off, human-in-the-loop, reflection/critic. Emphasize **deterministic guardrails around probabilistic agents**.

## Use case 1 — Voice AI for Contact Centers
- **Modes:** (a) *Autonomous voice agent* for containable calls (FAQs, payment reminders/collections IVR-plus, appointment/verification, simple care); (b) *Agent-assist copilot* for live human reps (real-time transcription, next-best-action, knowledge surfacing, sentiment, compliance nudges, auto-summary/disposition); (c) *Post-call analytics & QA* (100% call QA vs. sampled today, coaching).
- **KPIs:** containment/deflection rate, Average Handle Time (AHT), first-contact resolution (FCR), CSAT, QA coverage & score, compliance adherence, agent ramp time, collections promise-to-pay rate.
- **Compliance:** TCPA (outbound/consent), PCI-DSS (payment capture — pause/mask), HIPAA (healthcare clients), call recording/consent, disclosure requirements.
- **Latency target:** sub-second turn latency for natural voice; use realtime speech-to-speech.

## Use case 2 — AI-Driven HR Recruitment (Afni's own high-volume hiring)
- **Agents:** JD-generation agent; sourcing/screening agent (resume parse + rank vs. structured criteria); conversational screening agent (chat + optional voice pre-screen, reuses voice platform); scheduling agent (calendar/ATS); candidate-Q&A concierge bot; structured-interview scoring agent (assist, human-decided); fairness/adverse-impact monitor.
- **KPIs:** time-to-fill, cost-per-hire, funnel conversion, recruiter hours saved, candidate experience/NPS, offer-accept rate, 90-day attrition, interview-to-hire quality.
- **Fairness/compliance (critical):** EEOC, **NYC Local Law 144** (bias audit for automated employment decision tools), Illinois AI Video Interview Act, EU AI Act (high-risk employment), GDPR. **Principle: AI assists, humans decide.** No autonomous rejection; bias audits; explainability; candidate notice/consent.

## LLMOps lifecycle (the operational backbone)
Data & knowledge curation → Prompt/agent engineering (versioned) → Evaluation (offline golden sets + LLM-as-judge + human review; online A/B & shadow) → CI/CD (test gates, canary/blue-green, rollback) → Serving (gateway, quotas, caching) → Observability (tracing, token/cost, quality, drift, groundedness) → Feedback loop (thumbs, QA, incident → dataset). Governance & Responsible AI wrap the whole loop. Model/prompt registry + evaluation gates are mandatory before promotion.

## Governance & Responsible AI
Microsoft Responsible AI pillars: fairness, reliability & safety, privacy & security, inclusiveness, transparency, accountability. Add: human-in-the-loop for consequential decisions; content safety + groundedness; PII detection/redaction (Purview + Content Safety); model cards & system cards; AI use-case intake + risk tiering; audit trails; incident response for AI; red-teaming.

## Operating model
GenAI **Center of Excellence (CoE)**: exec sponsor, AI product owner, GenAI architect (lead), prompt/agent engineers, MLOps/LLMOps engineers, data engineers, RAI/governance officer, security, SMEs from ops & HR. Federated hub-and-spoke: CoE owns platform + standards; business units own use cases. Include a RACI.

## Roadmap — Crawl / Walk / Run (≈9–12 months)
- **Phase 0 (Weeks 0–4) Foundations & Discovery:** landing zone, security baseline, use-case intake, success metrics, data access.
- **Phase 1 (Crawl, Months 1–3):** platform MVP + agent-assist copilot pilot (1 contact-center program) + HR screening pilot; offline eval harness; observability baseline.
- **Phase 2 (Walk, Months 4–7):** autonomous voice agent for scoped call types; expand HR to voice pre-screen + scheduling; online eval/A-B; FinOps + guardrail hardening; CoE stood up.
- **Phase 3 (Run, Months 8–12):** scale to multiple programs/geos; add subrogation & QA analytics use cases; full governance, DR, and continuous-improvement flywheel.

## Business case (ALL ILLUSTRATIVE — mark clearly as placeholders)
Levers: AHT reduction (e.g., 15–25%), call containment (e.g., 20–40% of eligible call types), QA coverage 5–10% → 100%, agent ramp time reduction, recruiter time savings (e.g., 30–50% screening effort), time-to-fill reduction, attrition reduction. Present as ranges with a note that Afni actuals replace them in discovery. Include illustrative investment vs. return and payback (e.g., 9–15 months) — clearly hypothetical.

## Tone & style
Enterprise, consulting-grade, confident but not hype. Concrete Azure service names. Diagrams described in text/ASCII where helpful. American English. Avoid inventing specific Afni private data or client names. Always flag assumptions.
