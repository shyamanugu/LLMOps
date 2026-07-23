# Operating Model & Team

## Purpose

Technology alone does not sustain an enterprise GenAI capability — an operating model does. Afni needs a durable structure that concentrates scarce expertise, enforces standards consistently, and still lets business units move fast on their own use cases. This document defines the **GenAI Center of Excellence (CoE)**, the **federated hub-and-spoke** model, roles and responsibilities, a lifecycle RACI, the use-case intake process, and the skills/enablement plan that ramps Afni toward self-sufficiency.

## The GenAI Center of Excellence (CoE)

The CoE is the hub: a small, senior, cross-functional team that owns the **platform and the standards** — Azure AI Foundry, the shared agent patterns, guardrails, evaluation gates, CI/CD, observability, and Responsible AI policy. It does not own every use case. Instead, it enables business units ("spokes") to build use cases safely and repeatably on the shared foundation.

**CoE mandate:**
- Own and operate the LLMOps platform and reference architecture.
- Set and enforce Responsible AI, security, and evaluation standards.
- Curate reusable assets: agent templates, prompt registry, golden datasets, connectors.
- Run intake, risk-tiering, and promotion gates.
- Provide enablement, office hours, and peer review to the spokes.

## Federated Hub-and-Spoke Model

```
                 +---------------------------+
                 |   GenAI CoE (the Hub)     |
                 | platform + standards +    |
                 | guardrails + eval + RAI   |
                 +------------+--------------+
                              |
        +---------------------+---------------------+
        |                     |                     |
   +----v----+          +-----v-----+         +-----v-----+
   | Contact  |          |    HR /   |         |  Future   |
   | Center   |          | Recruiting|         |  programs |
   | (spoke)  |          |  (spoke)  |         |  (spokes) |
   +----------+          +-----------+         +-----------+
   owns Voice AI         owns HR use case      own their use cases
```

The hub provides leverage and consistency; the spokes provide domain ownership and speed. This is precisely why the platform-first approach compounds: each new spoke reuses the shared multi-agent pattern (supervisor/orchestrator routing to intent, RAG, action, compliance, sentiment, escalation, and summarization agents) rather than rebuilding it.

## Roles & Responsibilities

| Role | Home | Core responsibilities |
| --- | --- | --- |
| **Executive Sponsor** | Afni leadership | Funds and mandates the program; chairs the AI Governance Board; removes barriers. |
| **AI Product Owner** | Hub / business | Owns the use-case portfolio, prioritization, and outcome KPIs. |
| **GenAI Architect (lead)** | Hub | Owns reference architecture, agent patterns, and technical standards; author of the platform design. |
| **Prompt / Agent Engineers** | Hub + spokes | Build and version prompts and agents; tune orchestration and tools. |
| **LLMOps Engineers** | Hub | CI/CD, evaluation harness, serving, observability, FinOps tooling. |
| **Data Engineers** | Hub | Knowledge curation, RAG ingestion, dataset pipelines, lineage. |
| **RAI / Governance Officer** | Hub | Risk-tiering, bias audits, model/system cards, incident response, governance cadence. |
| **Security Engineer** | Hub | Identity, network isolation, secrets, Defender posture, compliance evidence. |
| **Ops & HR SMEs** | Spokes | Domain requirements, must-say/do-not-say rules, human-decision workflows, validation. |

## Lifecycle RACI

R = Responsible, A = Accountable, C = Consulted, I = Informed.

| Lifecycle activity | AI Product Owner | GenAI Architect | Prompt/Agent Eng | LLMOps Eng | Data Eng | RAI Officer | Security | Ops/HR SME |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Use-case intake & risk-tiering | A | C | I | I | I | R | C | C |
| Data & knowledge curation | I | C | I | I | R/A | C | C | C |
| Prompt/agent engineering | C | A | R | C | C | C | I | C |
| Evaluation & gates | C | C | C | R | C | A | I | C |
| CI/CD & promotion | I | A | C | R | I | C | C | I |
| Serving & observability | I | C | I | R/A | I | I | C | I |
| Security & compliance | I | C | I | C | C | C | R/A | I |
| Responsible AI & audits | C | C | I | I | I | R/A | C | C |
| Business validation & sign-off | R/A | I | I | I | I | C | I | R |
| Incident response | I | C | C | R | I | A | C | C |

## Use-Case Intake Process

1. **Submit** — Business unit files an intake form (owner, decision impact, data classes, affected populations, expected KPIs).
2. **Triage & risk-tier** — RAI officer assigns a tier (see doc 08); AI product owner prioritizes against the portfolio.
3. **Shape** — GenAI architect maps the use case to the shared agent pattern; identifies reuse and net-new components.
4. **Build** — Spoke + hub engineers develop against platform standards, with hub peer review.
5. **Gate** — Evaluation, safety, and security gates must pass before promotion; Tier 3 requires bias audit and board review.
6. **Operate & improve** — Observability, FinOps, and the feedback loop drive continuous improvement.

## Skills & Enablement Plan

Because Evoke staffs and leads early, a deliberate **capability-transfer** path moves Afni toward self-sufficiency:

- **Foundations (Phase 0–1):** Azure AI Foundry, prompt engineering, and Responsible AI fundamentals for the initial CoE and spoke engineers; paired delivery with Evoke.
- **Practitioner (Phase 2):** Agent orchestration (Semantic Kernel / AutoGen / Microsoft Agent Framework), evaluation design, and LLMOps tooling; Afni engineers lead features with Evoke shadowing.
- **Sustained (Phase 3):** Communities of practice, office hours, internal certification, and a reusable-asset library; Afni owns operations with Evoke advisory.
- **Ongoing:** Role-based enablement for ops/HR SMEs (how to write compliance rules, validate outputs, and own human decisions) and for leadership (governance, FinOps literacy).

## Why This Model Works for Afni

The hub-and-spoke CoE mirrors how Afni already runs contact centers: centralized standards and quality assurance, with delivery ownership at the program level. It concentrates rare GenAI expertise where it creates the most leverage, enforces Responsible AI and security uniformly, and scales to new programs and geographies without reinventing the platform each time — turning GenAI from a series of projects into a durable, governed Afni capability.
