# Enterprise LLMOps Platform for Afni

**A proposal to establish an enterprise-grade, multi-agent Generative AI platform and operating model for Afni, Inc.**

Prepared by **Evoke Technologies** · GenAI Architecture Practice
Author: Shyam (Senior GenAI Architect, embedded at Afni)
Status: Draft v1.0 · For internal Afni + Evoke review

---

## 1. Purpose

This repository is the working home for Afni's **LLMOps (Large Language Model Operations)** proposal. It defines *how* Afni can industrialize Generative AI — moving from isolated pilots to a governed, observable, cost-controlled platform that safely runs **multi-agent systems** in production across the contact-center and back-office estate.

The proposal is anchored on two flagship, high-ROI use cases and a reusable platform beneath them:

| # | Flagship use case | Why it fits Afni |
|---|-------------------|------------------|
| 1 | **Voice AI for Contact Centers** (customer-facing voice agents + real-time agent-assist) | Afni's core business is customer engagement across Care & Retention, Collections, Acquisition & Growth, and P&C Insurance. Voice is the highest-volume, highest-cost channel. |
| 2 | **AI-Driven HR Recruitment** (high-volume hiring for contact-center roles) | Afni hires and onboards thousands of agents across the US, Mexico, and the Philippines. High-volume, high-velocity recruiting is a natural, lower-risk internal proving ground. |

Both use cases are delivered on **one shared LLMOps platform** so that a third, fourth, and fifth use case (subrogation automation, QA & compliance analytics, knowledge assistant) can be added without rebuilding foundations.

## 2. What's in this repository

| Folder | Contents |
|--------|----------|
| [`presentation/`](./presentation) | **`Afni-LLMOps-Proposal.pptx`** — the executive slide deck used to present the proposal. |
| [`proposal/`](./proposal) | **`Afni-LLMOps-Proposal.docx`** — the full written proposal document (leadership + technical readership). |
| [`web/`](./web) | **`index.html`** — a self-contained, interactive executive overview with architecture diagrams (open in any browser; no install). |
| [`docs/`](./docs) | The proposal broken into readable Markdown sections (source of truth for the deck and document). |
| [`diagrams/`](./diagrams) | Architecture and flow diagrams. |
| [`scripts/`](./scripts) | Python generators (`python-pptx` / `python-docx`) that build the deck and document from content, so they can be regenerated as content evolves. |
| [`reference/`](./reference) | Notes, sources, and Afni business context used to ground the proposal. |

## 3. The proposal at a glance

**Vision.** Give Afni a single, secure, Azure-based platform to *build, evaluate, deploy, govern, and continuously improve* fleets of cooperating AI agents — with the same engineering rigor Afni already applies to contact-center operations.

**Platform spine.** Azure AI Foundry (model catalog + Agent Service), Azure OpenAI (incl. real-time speech-to-speech), Azure AI Search (RAG), orchestration via Semantic Kernel / AutoGen, Azure Content Safety guardrails, and a full LLMOps toolchain for prompts, evaluation, CI/CD, observability, and FinOps.

**Multi-agent pattern.** An **orchestrator agent** routes work to specialist agents (intent, knowledge/RAG, compliance, sentiment, action/tooling, escalation). The same pattern powers both the voice and HR use cases — proving the platform's reusability.

**Operating model.** A GenAI Center of Excellence (CoE) with clear roles, a RACI, and a phased **Crawl → Walk → Run** roadmap over ~9–12 months.

**Governance first.** Responsible AI, human-in-the-loop, PII redaction, and compliance (PCI-DSS, HIPAA, TCPA, SOC 2, GDPR, and hiring-fairness law such as EEOC / NYC Local Law 144) are designed in, not bolted on.

## 4. Document map (`docs/`)

1. [Executive Summary](./docs/01-executive-summary.md)
2. [Afni Business Context & Opportunity](./docs/02-afni-business-context.md)
3. [Platform Architecture](./docs/03-platform-architecture.md)
4. [Multi-Agent Systems Design](./docs/04-multi-agent-systems.md)
5. [Use Case 1 — Voice AI for Contact Centers](./docs/05-usecase-voice-ai.md)
6. [Use Case 2 — AI-Driven HR Recruitment](./docs/06-usecase-hr-recruitment.md)
7. [LLMOps Lifecycle & Toolchain](./docs/07-llmops-lifecycle.md)
8. [Responsible AI & Governance](./docs/08-responsible-ai-governance.md)
9. [Security, Privacy & Compliance](./docs/09-security-compliance.md)
10. [Observability & FinOps](./docs/10-observability-finops.md)
11. [Operating Model & Team](./docs/11-operating-model.md)
12. [Implementation Roadmap](./docs/12-roadmap.md)
13. [Business Case & ROI](./docs/13-business-case-roi.md)
14. [Risks & Mitigations](./docs/14-risks.md)

## 5. Regenerating the deck and document

```bash
# From the repo root, with Python available:
pip install python-pptx python-docx
python scripts/generate_pptx.py    # -> presentation/Afni-LLMOps-Proposal.pptx
python scripts/generate_docx.py    # -> proposal/Afni-LLMOps-Proposal.docx
```

## 6. Disclaimers

- This is a **vendor-neutral-leaning proposal** that recommends Microsoft Azure as the primary platform based on Afni's likely enterprise Microsoft footprint and the maturity of Azure AI Foundry for regulated, multi-agent workloads. Alternatives (AWS Bedrock Agents, Google Vertex AI Agent Builder) are noted where relevant.
- Business-context figures about Afni are drawn from public sources and clearly-labeled illustrative assumptions. **All ROI figures are illustrative placeholders** to be replaced with Afni's actuals during discovery.

---

© 2026 Evoke Technologies, prepared for Afni, Inc. Internal and confidential.
