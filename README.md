# AFNI Enterprise GenAI Framework

**An internal blueprint to establish a reusable, enterprise-grade, multi-agent Generative AI framework and operating model for AFNI, Inc.**

Owner: **AFNI, Inc. — Internal & Confidential**
Prepared by: **AFNI · Office of GenAI Architecture** (Senior GenAI Architect)
Status: Draft · For internal AFNI leadership and architecture review

---

## 1. Purpose

This repository is the working home for AFNI's **enterprise GenAI framework** — a reusable, governed **platform-as-a-product** that lets AFNI onboard *any* future GenAI use case quickly, safely, and cost-effectively, and continuously ride the frontier of models. The thesis is simple: **don't build AI features — build the factory that produces them.** AFNI stands up one governed platform and operating model so that the 4th, 10th, and 40th use case reuse the same paved road; time-to-value drops from quarters to weeks, while risk and cost are controlled by construction.

GenAI here is treated as far broader than chatbots — the framework supports conversational and voice copilots, autonomous agentic workflows, RAG over enterprise knowledge, document intelligence, batch summarization and analytics, structured extraction, multimodal understanding, decision support, and real-time voice.

Three flagship initiatives are the **first three proof-point use cases** onboarded through the framework's golden path — they demonstrate the platform, they are not the platform:

| # | Proof-point use case | What it is |
|---|---------------------|------------|
| 1 | **Voice Agent** | Real-time, multi-agent voice automation and agent-assist across the contact center — an autonomous voice agent for containable calls plus an agent-assist copilot for live human reps, at sub-second turn latency. |
| 2 | **Performance Intelligence Index (PI Index)** | An AI-generated, explainable composite performance score computed from **100% of interactions** (not sampled QA), rolling up per agent, team, program, and client, with driver breakdowns and targeted coaching. |
| 3 | **Hiring Intelligence** | AI-driven, fair, high-volume recruitment for AFNI's own contact-center hiring across the US, Mexico, and the Philippines — under the principle **AI assists, humans decide**. |

**How they connect.** One platform, one multi-agent pattern, three proof points. The Voice Agent generates interaction data and real-time automation; the PI Index turns 100% of that interaction data into performance intelligence; Hiring Intelligence reuses the same agents and voice stack to hire the workforce. Build the framework once; all three — plus every future use case (subrogation automation, knowledge assistant, next-best-offer) — reuse it.

## 2. What's in this repository

| Folder | Contents |
|--------|----------|
| [`presentation/`](./presentation) | **`.pptx`** executive slide deck (tight, diagram-led) used to present the framework. |
| [`proposal/`](./proposal) | **`.docx`** full written document (leadership + technical readership). |
| [`web/`](./web) | **`index.html`** — a self-contained, interactive executive overview (open in any browser; no install). |
| [`docs/`](./docs) | The framework broken into readable Markdown sections (source of truth for the deck and document). |
| [`diagrams/`](./diagrams) | Architecture and flow diagrams as **SVG** (source) and rasterized **PNG** (for Office) — now ~18 diagrams covering the layered architecture, orchestration, GenAIOps, security, data platform, and onboarding golden path. |
| [`scripts/`](./scripts) | Python and Node generators that build the deck, document, and diagrams from content so they can be regenerated as content evolves. |
| [`reference/`](./reference) | The **proposal bible** (single source of truth for terminology, structure, and positioning) and supporting AFNI business context. |

## 3. The framework at a glance

**Vision.** Give AFNI one secure, governed platform to *build, evaluate, deploy, govern, and continuously improve* fleets of cooperating AI agents — with the same operational rigor AFNI already applies to running contact centers.

**Platform spine.** **Microsoft Foundry** (model catalog + **Foundry Agent Service**), the **Model Router** for quality-aware cost routing, **gpt-realtime-1.5** speech-to-speech and the GPT-5.x frontier models, Azure AI Search (RAG), **Microsoft Fabric / OneLake** as the data platform, orchestration via **Microsoft Agent Framework 1.0** (the GA convergence of Semantic Kernel + AutoGen), **MCP** (tools) + **A2A** (agents) protocols, Content Safety guardrails, unified **OpenTelemetry** tracing and evaluation, and a full **GenAIOps** toolchain for prompts, agents, evaluation, CI/CD, observability, and FinOps.

**Multi-agent pattern.** An **orchestrator/supervisor** routes work to specialist agents (intent/router, knowledge/RAG, action/tooling via MCP, compliance/guardrail, sentiment, escalation, summarization/QA & scoring). The same pattern powers every use case — **deterministic guardrails wrap probabilistic agents**, with durable workflows (checkpoint/pause/resume) and tiered memory.

**Reusable onboarding.** A self-service **golden path** (intake → value/risk tiering → blueprint selection → assemble from building blocks → evaluate → deploy → operate → improve), backed by a **GenAI pattern catalog** and a capability catalog of agent/workflow templates, MCP connectors, prompt/policy libraries, guardrail packs, golden datasets, and IaC modules.

**Operating model.** A GenAI **Center of Excellence (CoE)** with clear roles, a RACI, and a phased **Crawl → Walk → Run → Fly** roadmap. All roles are AFNI-internal.

**Governance first.** Responsible AI, human-in-the-loop, PII redaction, Defender for AI, and compliance (TCPA, PCI-DSS, HIPAA, SOC 2, GDPR, and hiring-fairness law such as EEOC / NYC Local Law 144), mapped to the **OWASP Top 10 for LLM Applications (2025)** — designed in, not bolted on.

## 4. Document map (`docs/`)

1. [Executive Summary](./docs/01-executive-summary.md)
2. [AFNI Business Context & Opportunity](./docs/02-afni-business-context.md)
3. [Platform Architecture](./docs/03-platform-architecture.md)
4. [Multi-Agent Systems Design](./docs/04-multi-agent-systems.md)
5. [Voice Agent](./docs/05-usecase-voice-ai.md)
6. [Hiring Intelligence](./docs/06-usecase-hr-recruitment.md)
7. [GenAIOps Lifecycle & Toolchain](./docs/07-llmops-lifecycle.md)
8. [Responsible AI & Governance](./docs/08-responsible-ai-governance.md)
9. [Security, Privacy & Compliance](./docs/09-security-compliance.md)
10. [Observability & FinOps](./docs/10-observability-finops.md)
11. [Operating Model & Team](./docs/11-operating-model.md)
12. [Implementation Roadmap](./docs/12-roadmap.md)
13. [Business Case & ROI](./docs/13-business-case-roi.md)
14. [Risks & Mitigations](./docs/14-risks.md)
15. [Performance Intelligence Index (PI Index)](./docs/15-performance-intelligence-index.md)
16. [Design Principles](./docs/16-design-principles.md)
17. [Reusable Framework & Onboarding](./docs/17-reusable-framework-onboarding.md)
18. [GenAI Pattern Catalog](./docs/18-genai-pattern-catalog.md)
19. [Enterprise Multi-Agent Orchestration](./docs/19-enterprise-agent-orchestration.md)
20. [Security Deep-Dive](./docs/20-security-deep-dive.md)
21. [Data Platform & Scale](./docs/21-data-platform-scale.md)
22. [Performance & Scalability](./docs/22-performance-scalability.md)
23. [GenAIOps CI/CD](./docs/23-genaiops-cicd.md)
24. [Model Strategy](./docs/24-model-strategy.md)
25. [Evaluation Framework](./docs/25-evaluation-framework.md)
26. [Tech Stack BOM](./docs/26-tech-stack-bom.md)
27. [Maturity Model](./docs/27-maturity-model.md)

## 5. Regenerating the deck, document, and diagrams

```bash
# From the repo root, with Python and Node available:
pip install python-pptx python-docx
python scripts/generate_pptx.py     # -> presentation/*.pptx
python scripts/generate_docx.py     # -> proposal/*.docx

# Diagrams: build the SVGs, then rasterize to PNG for Office
python scripts/build_diagrams.py    # -> diagrams/*.svg
node scripts/rasterize.js           # -> diagrams/*.png
```

## 6. Disclaimers

- This framework recommends **Microsoft Foundry** as the primary platform based on AFNI's enterprise Microsoft footprint and the maturity of Foundry for regulated, multi-agent workloads. Alternatives (AWS Bedrock Agents, Google Vertex AI Agent Builder) are noted where relevant; the gateway, RAG, telephony, and MCP/A2A abstractions preserve that optionality.
- Business-context figures about AFNI are drawn from public sources and clearly labeled illustrative assumptions. **All ROI and financial figures are illustrative placeholders** to be replaced with AFNI actuals during discovery.

---

© 2026 AFNI, Inc. · Office of GenAI Architecture. Internal and confidential.
