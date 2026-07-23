# AFNI Enterprise LLMOps Proposal

**An internal proposal to establish an enterprise-grade, multi-agent Generative AI platform and operating model for AFNI, Inc.**

Owner: **AFNI, Inc. — Internal & Confidential**
Prepared by: **AFNI · Office of GenAI Architecture** (Senior GenAI Architect)
Status: Draft · For internal AFNI leadership and architecture review

---

## 1. Purpose

This repository is the working home for AFNI's **LLMOps (Large Language Model Operations)** proposal. It defines *how* AFNI can industrialize Generative AI — moving from isolated pilots to a governed, observable, cost-controlled platform that safely runs **multi-agent systems** in production across the contact-center and back-office estate.

The proposal is organized around **three flagship initiatives**, all delivered on one shared LLMOps platform so that future use cases (subrogation automation, knowledge assistant, next-best-offer) can be added without rebuilding foundations.

| # | Flagship initiative | What it is |
|---|---------------------|------------|
| 1 | **Voice Agent** | Real-time, multi-agent voice automation and agent-assist across the contact center — an autonomous voice agent for containable calls plus an agent-assist copilot for live human reps, at sub-second turn latency. |
| 2 | **Performance Intelligence Index (PI Index)** | An AI-generated, explainable composite performance score computed from **100% of interactions** (not sampled QA), rolling up per agent, team, program, and client, with driver breakdowns and targeted coaching. |
| 3 | **Hiring Intelligence** | AI-driven, fair, high-volume recruitment for AFNI's own contact-center hiring across the US, Mexico, and the Philippines — under the principle **AI assists, humans decide**. |

**How the three connect.** One platform, one multi-agent pattern, three products. The Voice Agent generates interaction data and real-time automation; the PI Index turns 100% of that interaction data into performance intelligence; Hiring Intelligence reuses the same agents and voice stack to hire the workforce. Build the platform once; all three reuse it.

## 2. What's in this repository

| Folder | Contents |
|--------|----------|
| [`presentation/`](./presentation) | **`.pptx`** executive slide deck used to present the proposal. |
| [`proposal/`](./proposal) | **`.docx`** full written proposal document (leadership + technical readership). |
| [`web/`](./web) | **`index.html`** — a self-contained, interactive executive overview (open in any browser; no install). |
| [`docs/`](./docs) | The proposal broken into readable Markdown sections (source of truth for the deck and document). |
| [`diagrams/`](./diagrams) | Architecture and flow diagrams as **SVG** (source) and rasterized **PNG** (for Office). |
| [`scripts/`](./scripts) | Python and Node generators that build the deck, document, and diagrams from content so they can be regenerated as content evolves. |
| [`reference/`](./reference) | The **proposal bible** (single source of truth for terminology, structure, and positioning) and supporting AFNI business context. |

## 3. The proposal at a glance

**Vision.** Give AFNI one secure, governed Azure platform to *build, evaluate, deploy, govern, and continuously improve* fleets of cooperating AI agents — with the same operational rigor AFNI already applies to running contact centers.

**Platform spine.** Azure AI Foundry (model catalog + Azure AI Agent Service), Azure OpenAI (incl. **gpt-realtime** speech-to-speech), Azure AI Search (RAG), orchestration via Semantic Kernel / AutoGen (converging into the Microsoft Agent Framework), Azure AI Content Safety guardrails, and a full LLMOps toolchain for prompts, evaluation, CI/CD, observability, and FinOps.

**Multi-agent pattern.** An **orchestrator/supervisor** routes work to specialist agents (intent/router, knowledge/RAG, action/tooling, compliance/guardrail, sentiment, escalation, summarization/QA & scoring). The same pattern powers all three initiatives — **deterministic guardrails wrap probabilistic agents**.

**Operating model.** A GenAI **Center of Excellence (CoE)** with clear roles, a RACI, and a phased **Crawl → Walk → Run** roadmap over roughly 9–12 months. All roles are AFNI-internal.

**Governance first.** Responsible AI, human-in-the-loop, PII redaction, and compliance (TCPA, PCI-DSS, HIPAA, SOC 2, GDPR, and hiring-fairness law such as EEOC / NYC Local Law 144) are designed in, not bolted on.

## 4. Document map (`docs/`)

1. [Executive Summary](./docs/01-executive-summary.md)
2. [AFNI Business Context & Opportunity](./docs/02-afni-business-context.md)
3. [Platform Architecture](./docs/03-platform-architecture.md)
4. [Multi-Agent Systems Design](./docs/04-multi-agent-systems.md)
5. [Voice Agent](./docs/05-usecase-voice-ai.md)
6. [Hiring Intelligence](./docs/06-usecase-hr-recruitment.md)
7. [LLMOps Lifecycle & Toolchain](./docs/07-llmops-lifecycle.md)
8. [Responsible AI & Governance](./docs/08-responsible-ai-governance.md)
9. [Security, Privacy & Compliance](./docs/09-security-compliance.md)
10. [Observability & FinOps](./docs/10-observability-finops.md)
11. [Operating Model & Team](./docs/11-operating-model.md)
12. [Implementation Roadmap](./docs/12-roadmap.md)
13. [Business Case & ROI](./docs/13-business-case-roi.md)
14. [Risks & Mitigations](./docs/14-risks.md)
15. [Performance Intelligence Index (PI Index)](./docs/15-performance-intelligence-index.md)

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

- This proposal recommends Microsoft Azure as the primary platform based on AFNI's enterprise Microsoft footprint and the maturity of Azure AI Foundry for regulated, multi-agent workloads. Alternatives (AWS Bedrock Agents, Google Vertex AI Agent Builder) are noted where relevant.
- Business-context figures about AFNI are drawn from public sources and clearly labeled illustrative assumptions. **All ROI and financial figures are illustrative placeholders** to be replaced with AFNI actuals during discovery.

---

© 2026 AFNI, Inc. · Office of GenAI Architecture. Internal and confidential.
