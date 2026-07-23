# Proposal Bible — shared context for all AFNI LLMOps documents

> Single source of truth for terminology, structure, and positioning.
> Every document (`docs/`, PPTX, DOCX, HTML) must stay consistent with it.
> **This is an internal AFNI document. There is NO mention of any external vendor or staffing party anywhere.**

## Ownership & branding
- **Owner:** AFNI, Inc. — internal, confidential.
- **Prepared by:** AFNI · Office of GenAI Architecture (Senior GenAI Architect).
- **Do NOT reference** any staffing vendor or external party. All authorship is AFNI-internal.

## Who / what
- **AFNI, Inc.** — global Business Process Outsourcing (BPO) & customer-engagement provider. Founded 1936, HQ Bloomington, Illinois. ~3,400+ employees. Sites across US (IL, AZ, KY, TX, MO, AL), Mexico, and the Philippines, plus an **AFNI@Home** remote workforce program.
- **Service lines:** Acquisition & Growth; Care & Retention; Collections; P&C Insurance (incl. **subrogation**); delivered under a partnership/**Gainshare** commercial model. Industries served: insurance, financial services, telecom, healthcare, fitness, media.
- **Ask:** stand up **enterprise-grade LLMOps** to build, govern, and scale **multi-agent GenAI systems**, anchored on three flagship initiatives.

## Positioning / vision
"Give AFNI one secure, governed platform to build, evaluate, deploy, govern, and continuously improve fleets of cooperating AI agents — with the same operational rigor AFNI already applies to running contact centers."

## THE THREE FLAGSHIP INITIATIVES (realigned — these drive the whole story)

### 1. AFNI Performance Intelligence Index (PI Index)
An AI-generated, explainable **composite performance score** computed from **100% of interactions** (not sampled QA). Multi-agent analysis of every voice/chat interaction produces dimension scores that roll up into a single index per agent, team, program, and client.
- **Analysis dimensions (each an agent):** compliance adherence, communication & empathy, resolution / FCR, script & process adherence, sentiment trajectory, efficiency (AHT/silence/holds), business outcome (sale, promise-to-pay, retention).
- **Outputs:** the PI Index score + driver breakdown + trends + anomaly alerts + targeted coaching recommendations; feeds QA calibration, coaching workflows, and Gainshare/performance reporting.
- **Value:** replaces ~2–10% sampled QA with 100% coverage; objective, consistent, explainable scoring; faster coaching; earlier risk detection.
- **Governance:** score explainability, fairness across agents/sites, human calibration & appeals, model cards. (Careful: "PI Index", never abbreviate to "PII" which means Personally Identifiable Information.)

### 2. Hiring Intelligence
AI-driven, fair, high-volume recruitment for AFNI's own contact-center hiring across US/Mexico/Philippines. Agents span the funnel: JD generation; sourcing & résumé ranking; conversational screening (chat + optional voice pre-screen, reusing the Voice Agent platform); scheduling; structured interview-scoring **assist**; a **Candidate Fit** signal; and a continuous fairness/adverse-impact monitor.
- **Principle:** **AI assists, humans decide** — no autonomous rejection.
- **Value:** 30–50% less recruiter screening effort; shorter time-to-fill; lower cost-per-hire; better matching → lower 90-day attrition; better candidate experience.
- **Fairness/compliance (critical):** EEOC, **NYC Local Law 144** (bias audit for automated employment decision tools), Illinois AI Video Interview Act, EU AI Act (high-risk employment), GDPR; candidate notice/consent, explainability, bias audits.

### 3. Voice Agent
Real-time, multi-agent voice automation and agent-assist across the contact center.
- **Modes:** (a) *Agent-assist copilot* for live human reps (real-time transcription, next-best-action, knowledge surfacing, sentiment, compliance nudges, auto-summary/disposition); (b) *Autonomous voice agent* for containable call types (FAQs, verification, appointments, payment reminders) with warm human handoff.
- **Latency:** sub-second turn latency; **gpt-realtime** speech-to-speech; Azure AI Speech as hybrid/fallback.
- **Compliance:** TCPA (consent/outbound), PCI-DSS (payment pause/mask), HIPAA (healthcare clients), call recording/consent, disclosures.
- **KPIs:** containment/deflection, AHT, FCR, CSAT, compliance adherence, agent ramp.
- **Synergy:** Voice Agent transcripts + signals feed the **PI Index**; the Voice Agent platform is reused for Hiring Intelligence voice pre-screens. The three initiatives reinforce each other.

## How the three connect (tell this story)
One platform, one multi-agent pattern, three products. Voice Agent generates the interaction data and real-time automation; the PI Index turns 100% of that interaction data into performance intelligence; Hiring Intelligence reuses the same agents + voice stack to hire the workforce. Build the platform once; all three (and future use cases like subrogation) reuse it.

## Primary cloud & tooling (be specific and consistent)
- **Core platform:** Microsoft **Azure AI Foundry** — model catalog, **Azure AI Agent Service**, hubs/projects, evaluations, content safety.
- **Models:** Azure **OpenAI** GPT-4o / GPT-4o-mini / **gpt-realtime (speech-to-speech)**; Azure **AI Speech** (STT/TTS, custom neural voice); embeddings (text-embedding-3-large); open-weight options (Llama, Phi) for cost tiers.
- **Orchestration:** **Semantic Kernel** / **AutoGen** (converging into the **Microsoft Agent Framework**); Azure AI Agent Service for hosted agents + tool calling.
- **RAG/knowledge:** Azure **AI Search** (hybrid + semantic ranker); **AI Document Intelligence**; vectors in AI Search / Cosmos DB.
- **Data & state:** Azure **Cosmos DB** (agent state/memory); **Microsoft Fabric** / Data Lake (analytics, PI Index store); Azure SQL.
- **Compute & serving:** Azure **Container Apps** / **AKS**; **Azure API Management** as the AI gateway (token metering, quotas, caching, routing); **Functions** for event glue.
- **Telephony / contact center:** integrate existing CCaaS (Genesys, NICE, Five9, Amazon Connect) via SIP/APIs; **Azure Communication Services** for greenfield. Keep integration-layer generic.
- **Guardrails/safety:** Azure **AI Content Safety** (prompt shields, groundedness, protected material, PII).
- **LLMOps toolchain:** Prompt flow / prompt registry; **Azure AI evaluation SDK** (offline + online); **Azure DevOps / GitHub Actions** CI/CD; **Azure Monitor + Application Insights + OpenTelemetry (GenAI conventions)**; **Microsoft Purview** (governance/lineage); **Microsoft Entra ID** (identity); **Azure Key Vault** (secrets); **Microsoft Defender for Cloud** (posture).
- **Alternatives to note briefly:** AWS Bedrock Agents; Google Vertex AI Agent Builder. Azure recommended as primary.

## The multi-agent pattern (reused across all three initiatives)
Orchestrator/Supervisor routes to specialist agents: **Intent/Router, Knowledge/RAG, Action/Tooling, Compliance/Guardrail, Sentiment, Escalation/Handoff, Summarization/QA & Scoring.** Patterns: supervisor-orchestrator, sequential, concurrent, hand-off, group-chat, reflection/critic, human-in-the-loop. **Deterministic guardrails wrap probabilistic agents.**

## LLMOps lifecycle
Data/knowledge curation → prompt/agent engineering (versioned) → evaluation (offline golden sets + LLM-as-judge + human review; online A/B & shadow; red-teaming) → CI/CD (registry, canary/blue-green, rollback, regression gates) → serving (gateway, quotas, caching) → observability (tracing, token/cost, quality, drift, groundedness) → feedback loop. Governance & Responsible AI wrap the loop.

## Governance & Responsible AI
Microsoft RAI pillars: fairness, reliability & safety, privacy & security, inclusiveness, transparency, accountability. Plus: human-in-the-loop for consequential decisions; content safety + groundedness; PII detection/redaction (Purview + Content Safety); model/system cards; AI use-case intake + risk-tiering; audit trails; AI incident response; red-teaming; AI governance board.

## Operating model
AFNI **GenAI Center of Excellence (CoE)**: exec sponsor, AI product owner, GenAI architect (lead), prompt/agent engineers, LLMOps/MLOps engineers, data engineers, RAI/governance officer, security, ops & HR SMEs. Federated hub-and-spoke: CoE owns platform + standards; business units own use cases. Include a RACI. (All roles are AFNI-internal.)

## Roadmap — Crawl / Walk / Run (≈9–12 months)
- **Phase 0 (Weeks 0–4) Foundations & Discovery:** landing zone, security baseline, use-case intake, metrics, data access.
- **Phase 1 (Crawl, Months 1–3):** platform MVP + Voice Agent agent-assist pilot (1 program) + PI Index MVP (offline scoring on historical interactions) + Hiring Intelligence screening pilot.
- **Phase 2 (Walk, Months 4–7):** autonomous Voice Agent for scoped calls; PI Index live/near-real-time + coaching workflows; Hiring Intelligence voice pre-screen + scheduling; online eval, FinOps, CoE stood up.
- **Phase 3 (Run, Months 8–12):** scale across programs/geos; add subrogation & knowledge assistant; full governance, DR, continuous-improvement flywheel.

## Business case (ALL ILLUSTRATIVE — mark clearly as placeholders)
Levers: PI Index → QA coverage 5–10% → 100%, faster coaching, attrition reduction; Voice Agent → AHT 15–25%, containment 20–40% of eligible calls; Hiring Intelligence → recruiter time −30–50%, shorter time-to-fill, lower attrition. Payback ~9–15 months (illustrative). Replace with AFNI actuals in discovery.

## Design direction for diagrams (IMPORTANT)
Documents should be **diagram-led: minimal text, strong graphics.** Use the shared palette below. Every major concept gets a clean, professional diagram (SVG → rasterized PNG for Office; inline SVG for web). Prefer boxes-with-icons, layered stacks, fl#ows with arrows, and index/score visuals over paragraphs.

### Palette
- Navy `#121F3D` (primary), Indigo `#1B3A6B` (secondary), Teal `#00A6A6` (accent), Cyan `#2EC4D3`, Amber `#F5A623` (highlight), Green `#2E9E5B`, Light `#F4F6FA`, Gray `#5A6474`, Ink `#1C2433`, Line `#E1E6F0`, White `#FFFFFF`. Font: Segoe UI.

## Tone & style
Enterprise, consulting-grade, confident, not hype. Concrete Azure service names. American English. No external-vendor references. Always flag illustrative numbers.
