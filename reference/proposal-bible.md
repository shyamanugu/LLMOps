# Proposal Bible — AFNI Enterprise GenAI Framework (single source of truth)

> Every document (`docs/`, PPTX, DOCX, HTML, diagrams) must stay consistent with this file.
> **Internal AFNI document. NO mention of any external vendor or staffing party. All authorship is AFNI-internal
> ("AFNI · Office of GenAI Architecture").**

## 0. What changed (v3 — framework elevation)
This is no longer a proposal for three apps. It is a proposal for an **enterprise, reusable GenAI framework** — an
internal platform-as-a-product that lets AFNI onboard *any* future GenAI use case quickly, safely, and cost-effectively,
and continuously ride the frontier of models. The three initiatives (Voice Agent, Performance Intelligence Index,
Hiring Intelligence) are recast as the **first three proof-point use cases** onboarded via the framework's paved road.
GenAI is treated as far broader than chatbots. Content is grounded in current (2026) capabilities — see §12 sources.

## 1. Framing (tell this story)
- **Thesis:** "Don't build AI features — build the *factory* that produces them." AFNI stands up one governed platform +
  operating model so the 4th, 10th, and 40th use case reuse the same paved road. Time-to-value drops from quarters to weeks;
  risk and cost are controlled by construction.
- **Vision:** "Give AFNI one secure, governed platform to build, evaluate, deploy, govern and continuously improve fleets of
  cooperating AI agents — with the same operational rigor AFNI already applies to running contact centers."
- **Owner/brand:** AFNI, Inc. · Office of GenAI Architecture. Internal & confidential. No external vendor references.

## 2. AFNI context (unchanged facts)
Global BPO & customer engagement, founded 1936, HQ Bloomington IL, ~3,400+ staff across US (IL/AZ/KY/TX/MO/AL), Mexico,
the Philippines + AFNI@Home. Service lines: Acquisition & Growth; Care & Retention; Collections; P&C Insurance (subrogation);
Gainshare commercial model. Industries: insurance, financial services, telecom, healthcare, fitness, media.

## 3. Current technology grounding (2026 — use these exact names)
**Platform = Microsoft Foundry** (formerly Azure AI Foundry / Azure AI Studio):
- **Foundry Agent Service** — hosted, durable agents (sandboxed sessions, state, filesystem, framework flexibility);
  publish agents to Microsoft Teams / M365 Copilot; **Voice Live** real-time voice path. Reaching GA through mid-2026.
- **Model Router** — automatically routes each request to the cheapest model that meets a *measured* quality bar; prompt caching.
- **Unified tracing + evaluation** — one **OpenTelemetry** pipeline captures every model call, tool invocation, sub-agent hop,
  and handoff; evaluations link back to the exact trace. **Auto-generated rubric evaluators** score agent quality vs context-aware rubrics.
- **Memory in Agent Service** — procedural, user, and session memory. **Toolboxes** for curated tool sets.
- **Model catalog** — frontier + open-weight models; fine-tuning, distillation, evaluations, Content Safety.

**Models (latest, 2026):** OpenAI **GPT-5.5** (frontier: deep long-context reasoning, reliable agentic execution, improved
computer-use, token efficiency), **GPT-5.4 / GPT-5.2 / GPT-5** (272k-context reasoning), **GPT-5.5 Instant** (`gpt-chat-latest`,
low-latency), **gpt-realtime-1.5** + **gpt-audio-1.5** (speech-to-speech, multilingual, tool calling); reasoning "o-series"
(o3-mini, o1) in catalog; embeddings (text-embedding-3-large); open-weight (Llama, Phi) for cost/edge tiers.
**Principle: pin to capabilities via the router + evals, not to a single model version — so AFNI adopts each new frontier model without rewrites.**

**Orchestration = Microsoft Agent Framework 1.0** (GA April 2026; convergence of **AutoGen** + **Semantic Kernel**; Python & .NET):
- Orchestration patterns: **sequential, concurrent, group-chat, handoff, Magentic** (complex task decomposition).
- **Durable workflows** — streaming, checkpointing, human-in-the-loop approvals, pause/resume for long-running processes.
- **Declarative agents & workflows in version-controlled YAML** (instructions, tools, memory, topology as code).
- **Process Framework** (GA ~Q2 2026) for deterministic business-workflow orchestration.

**Agent interoperability = the protocol stack:** **MCP (Model Context Protocol)** = agent→tools (de facto tool standard);
**A2A (Agent-to-Agent, v1.0, Linux Foundation)** = agent→agent across runtimes; **WebMCP** = web access. Foundry can expose any
agent as an A2A endpoint. Use MCP for tools/connectors and A2A for cross-team/cross-runtime agent collaboration.

**Supporting Azure services:** Azure OpenAI; Azure AI Search (hybrid + semantic ranker, integrated vectorization); AI Document
Intelligence; Content Safety (prompt shields, groundedness, PII, protected material); **Microsoft Fabric** + OneLake / Data Lake;
Cosmos DB (agent state/memory, vector); Azure SQL; **API Management** as the AI gateway (token metering, quotas, caching, routing);
Container Apps / AKS; Functions; Event Hubs / Stream Analytics (streaming); Entra ID; Key Vault; **Microsoft Purview**
(governance, lineage, DLP, data-security posture for AI); Defender for Cloud + **Defender for AI**; Azure Monitor + App Insights;
GitHub Actions / Azure DevOps; Azure Communication Services + CCaaS (Genesys/NICE/Five9) integration.

## 4. The framework — layers (the reusable platform)
1. **Experience & channels** — voice/CCaaS + ACS + Voice Live, web/chat, agent-assist desktop, Teams/M365 Copilot, ATS/HR, batch/API.
2. **Orchestration & agents** — Agent Framework + Foundry Agent Service; orchestrator + specialist agents; durable workflows;
   memory; MCP tool layer; A2A interop; agent registry.
3. **Models & AI services** — model catalog + **Model Router**; GPT-5.x + realtime; Content Safety; fine-tune/distill.
4. **Knowledge & RAG** — AI Search (hybrid+semantic), Document Intelligence, integrated vectorization, grounding & citations.
5. **Data platform (at scale)** — Fabric/OneLake lakehouse, streaming (Event Hubs) + batch, vector stores, feature/knowledge pipelines, Purview lineage.
6. **Tools & integration** — MCP servers wrapping CRM/HRIS/billing/systems-of-record; APIM gateway; Functions; connectors.
7. **GenAIOps / DevOps** — declarative agents-as-code, prompt/model registry, evaluation-in-CI, CI/CD, canary/rollback, IaC.
8. **Security & governance** — Zero Trust, Entra ID, Key Vault, private networking, Content Safety, Purview, Defender for AI, RAI.
9. **Observability & FinOps** — unified OpenTelemetry tracing, quality/groundedness/latency/drift/safety/cost, showback, budgets.

## 5. GenAI pattern catalog (beyond chatbots — reusable blueprints)
Each pattern is a paved-road blueprint (reference arch + eval suite + guardrail pack + IaC):
- **Conversational assistant / copilot** (chat & voice).
- **Autonomous / agentic workflow** (multi-step, tool-using, durable; e.g., subrogation triage).
- **Retrieval-augmented generation (RAG)** over enterprise knowledge.
- **Document intelligence** — extraction, classification, validation of forms/claims/contracts.
- **Batch summarization & analytics** — 100% interaction analysis (PI Index), call/QA analytics.
- **Structured data extraction & entity resolution** from unstructured text/audio.
- **Multimodal** — audio (speech), image/scan understanding, document + voice.
- **Decision support & forecasting** — next-best-action, propensity, scenario analysis (LLM + analytics).
- **Code & developer assist** — internal tooling, test generation, migration.
- **Real-time voice** — speech-to-speech agents & agent-assist.
The three initiatives map to patterns: Voice Agent = real-time voice + copilot + agentic; PI Index = batch summarization/analytics
+ structured extraction; Hiring Intelligence = agentic workflow + RAG + document intelligence.

## 6. Use-case onboarding — the golden path (self-service, paved road)
Intake → Value & Risk tiering → Blueprint selection (from §5) → Assemble from reusable building blocks → Evaluate (gates) →
Deploy (canary) → Operate (observe/FinOps) → Improve (feedback → datasets). **Reusable building blocks / capability catalog:**
agent & workflow templates (YAML), MCP tool/connector library, prompt & policy libraries, guardrail packs, golden datasets +
eval suites, IaC modules, RAG ingestion templates, dashboards. Target: a new use case reaches pilot in weeks using paved roads,
with security/compliance/observability inherited by default.

## 7. Enterprise multi-agent orchestration (must read as enterprise-grade)
Supervisor/orchestrator routes to specialist agents: **Intent/Router, Knowledge/RAG, Action/Tooling (via MCP), Compliance/Guardrail,
Sentiment, Escalation/Handoff, Summarization/QA & Scoring.** Enterprise properties: **durable execution** (checkpoint/pause/resume,
retries, idempotency, sagas/compensation), **memory** (session/user/procedural), **agent registry & versioning**, **MCP** for tools +
**A2A** for cross-runtime agents, **deterministic guardrails wrapping probabilistic agents**, **graduated autonomy** (human approval for
high-risk/irreversible actions), **least-privilege tool scopes**, full tracing per hop. Patterns: sequential/concurrent/group-chat/handoff/Magentic.

## 8. Security — highest level (design for hostile inputs)
**Zero Trust + defense-in-depth**, mapped to the **OWASP Top 10 for LLM Applications (2025):**
LLM01 Prompt Injection (direct+indirect) · LLM02 Sensitive Information Disclosure · LLM03 Supply Chain · LLM04 Data & Model Poisoning ·
LLM05 Improper Output Handling · LLM06 Excessive Agency · LLM07 System-Prompt Leakage · LLM08 Vector & Embedding Weaknesses ·
LLM09 Misinformation · LLM10 Unbounded Consumption.
**Controls:** treat ALL model I/O + retrieved content as untrusted; prompt shields + input/output filtering; strict role/instruction
separation of untrusted content; least-privilege tools + human approval for sensitive/irreversible actions (curb excessive agency);
groundedness/citation to fight misinformation; per-tenant/per-source access control on vectors; rate/cost limits (unbounded consumption);
AI-BOM / model & dependency provenance (supply chain); PII detection/redaction (Purview + Content Safety); private networking (VNet,
private endpoints, no public egress); Entra ID least-privilege + managed identities; Key Vault; Defender for Cloud + **Defender for AI**;
adversarial **red-teaming** + continuous eval; audit trails; AI incident response. Compliance: PCI-DSS, HIPAA, TCPA, SOC 2, GDPR,
EEOC/NYC LL144, EU AI Act.

## 9. Data at scale · Performance · GenAIOps CI/CD (the ops core)
**Data at scale:** Fabric/OneLake lakehouse; batch + streaming (Event Hubs/Stream Analytics); scalable ingestion + chunking +
**integrated vectorization**; vector indexes (AI Search/Cosmos) partitioned per domain/tenant; incremental/CDC refresh; Purview
lineage, retention, DLP; PII handling; golden datasets curated from production feedback.
**Performance & scalability:** explicit **latency budgets** (sub-second voice turns); layered caching (semantic/prompt/response);
**Model Router** for cost-latency-quality; provisioned throughput (PTU) for critical paths; autoscaling (Container Apps/AKS); async +
streaming responses; batching for bulk (PI Index); load & soak testing; concurrency/backpressure; graceful degradation + fallback models.
**GenAIOps / LLMOps CI/CD (with proper validations):** everything-as-code (declarative YAML agents, versioned prompts, IaC) →
PR triggers **evaluation-in-CI** (unit + prompt/regression + groundedness + safety/red-team + cost/latency budgets as gates) →
promote to model/prompt registry → **canary / blue-green** deploy behind APIM → **online eval** (A/B, shadow) + guardrail monitors →
auto-rollback on regression → feedback (thumbs, QA, incidents, PI Index) flows back into golden datasets. Distinguish **LLMOps vs MLOps
vs DevOps** (non-determinism, prompts as artifacts, eval of generative output, novel failure modes, token cost/latency as release criteria).

## 10. Design principles (the CTO's non-negotiables)
1. Platform as a product; paved roads / golden paths; self-service. 2. Reuse over rebuild; composable building blocks.
3. Model-agnostic & frontier-ready (router + evals; no single-model lock-in). 4. Evaluation-driven everything — nothing ships without passing evals.
5. Deterministic guardrails around probabilistic components. 6. Zero Trust & least privilege; treat all model I/O as untrusted.
7. Human-in-the-loop for consequential actions; graduated autonomy. 8. Observability & cost are first-class (every trace, every token).
9. Privacy & data minimization by design. 10. Secure-/compliant-by-default templates. 11. Fail safe: fallbacks & graceful degradation.
12. Everything-as-code & reproducible. 13. Grounded & cited over confident-but-wrong. 14. Measure business outcomes, not model vanity metrics.

## 11. Operating model, roadmap, business case
- **CoE (hub-and-spoke, all AFNI-internal):** exec sponsor, AI product owner (platform), GenAI architect (lead), prompt/agent engineers,
  GenAIOps/MLOps engineers, data engineers, RAI/governance officer, security engineer, FinOps, + Ops/HR SMEs in spokes. Platform team owns
  paved roads & standards; spokes own use cases. RACI across lifecycle.
- **Roadmap (Crawl→Walk→Run→Fly, ~9–12 mo + scale):** Phase 0 (Wks 0–4) foundations/landing zone/security/intake; Phase 1 Crawl (M1–3)
  platform MVP + paved-road v1 + Voice Agent copilot + PI Index MVP + Hiring screening pilot + eval harness; Phase 2 Walk (M4–7) autonomous
  voice + PI Index live + Hiring voice pre-screen + GenAIOps CI/CD + FinOps + CoE + onboard 2 new use cases via paved road; Phase 3 Run (M8–12)
  scale programs/geos, subrogation + knowledge assistant, full governance/DR/security hardening; **Fly** — self-service onboarding at scale, agent marketplace, A2A ecosystem.
- **Maturity model:** Ad-hoc → Repeatable (paved road) → Governed → Optimized → Self-service/Autonomous.
- **Business case (ILLUSTRATIVE — mark clearly):** platform amortizes across use cases (each new one cheaper/faster); PI Index QA 5–10%→100%;
  Voice Agent AHT −15–25%, containment 20–40%; Hiring recruiter time −30–50%; payback ~9–15 months; Gainshare improves shared margin. Replace with AFNI actuals.

## 12. Sources (cite where relevant; label public-source vs illustrative)
Microsoft Foundry / Agent Service, Model Router, tracing/eval, memory (Microsoft Learn & Foundry blog, 2026); GPT-5.5/5.4/5.2/5 &
gpt-realtime-1.5 (Microsoft Azure blog / Foundry model catalog, 2026); Microsoft Agent Framework 1.0 (devblogs, 2026); MCP + A2A protocol
stack (Linux Foundation A2A v1.0; MCP); OWASP Top 10 for LLM Applications (2025); MLOps→LLMOps→GenAIOps practice literature (2025). Full URLs live in `docs/` where cited.

## 13. Palette & style (diagrams must use this)
Navy `#121F3D`, Indigo `#1B3A6B`, Teal `#00A6A6`, Cyan `#2EC4D3`, Amber `#F5A623`, Green `#2E9E5B`, Purple `#7A4FB5`, Rose `#D65A7A`,
Light `#F4F6FA`, Gray `#5A6474`, Ink `#1C2433`, Line `#E1E6F0`. Font Segoe UI. **Diagram-led: minimal text, strong graphics.**
Enterprise, consulting/CTO-grade tone. American English. Always flag illustrative numbers. No external-vendor references.

## Deliverable split (per latest direction)
- **PPTX = only required content** (tight, diagram-led, executive; detail lives in docs).
- **DOCX = detailed** (full framework, every section, all diagrams embedded).
- **HTML = interactive executive overview** (framework-first).
- **docs/ = detailed** reference sections. **diagrams/ = all diagrams** (SVG + PNG).
