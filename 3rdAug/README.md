# LLMOps Research Package (3rd Aug)

## Purpose

This folder is a research-phase package on LLMOps (large language model operations): what it actually
is, tool by tool, and how to stand it up on the Azure stack without building everything on day one. Every
document answers "what exactly do we set up and with which tool," not "why AI matters." There is no
marketing language or client-specific branding; where sizing needs an anchor, the docs refer generically
to "a contact-center business process outsourcing (BPO) enterprise."

The idea running through every document is **start small, go big**: four maturity levels (Level 0 –
Baseline, Level 1 – Managed, Level 2 – Production-grade, Level 3 – Scaled/self-service), each additive —
nothing built at an earlier level gets rebuilt later.

`research-brief.md` in this folder is the source of truth for the whole package. If a document here and
the brief ever disagree, the brief wins.

## Document map

| Doc | Title | What it covers |
|---|---|---|
| 01 | LLMOps Fundamentals | What LLMOps is, how it differs from DevOps/MLOps, the thirteen-component map, what is built once vs. rebuilt per use case, the maturity levels at a glance |
| 02 | Source Control & Ops Backbone | GitHub repo layout, branching, Actions pipelines, environments, OpenID Connect (OIDC) to Azure |
| 03 | Prompt Management | Where prompt text lives, versioning, the registry (Langfuse/Foundry), A/B testing |
| 04 | Model Management | The model catalog, task-alias config pattern, Model Router, the new-model adoption loop |
| 05 | Evaluation & Golden Datasets | Building and sourcing golden datasets, the metrics catalog, evaluator tools compared, the CI gate, eval-overfitting mitigation |
| 06 | Observability | Tracing every model/tool/agent call, provider comparison, what to instrument |
| 07 | Feedback & Analytics | Capturing user and implicit signals, the analytics dashboard, the improvement loop, the fine-tuning path |
| 08 | Data Pipelines & Knowledge | Ingestion, chunking, embedding, index refresh for retrieval-augmented generation (RAG), warehouse relationship |
| 09 | Guardrails & Safety | Input/output filtering, personally identifiable information (PII) handling, policy enforcement |
| 10 | Serving, Gateway & Multi-Agent Orchestration | API Management as the AI gateway, quotas/caching/canary, agent frameworks, agent types, workflow patterns |
| 11 | End-to-End Architecture | One diagram covering the full cycle — change, request, telemetry, feedback, and data-refresh flows — plus the network/identity model |
| 12 | Phased Roadmap & Maturity | The Level 0→3 plan: duration, what gets set up, what it unlocks, exit criteria, what is deliberately deferred at each level |
| 13 | Team, Timeline, Assumptions & Risks | Core team, illustrative timeline, assumptions the plan depends on, and a risk register |

Security/identity, financial operations (FinOps) for cloud cost, and environments/infrastructure as code
are cross-cutting rather than standalone documents — they show up inside the architecture, roadmap, and
team docs wherever relevant, which matches how they actually get handled in practice.

## Presentation

The `presentation/` folder holds the slide version of this material: a short deck (roughly 18–20 slides,
editable native shapes only, no images, speaker notes, simple two-color design) that walks through the
same start-small-go-big story without reading thirteen documents. The `scripts/` folder holds any
supporting automation used to generate or check package content.

## How this relates to the parent repository

The parent `LLMOps/` repository is the strategic framework — the business case, architecture narrative,
and proof-point use cases for the enterprise GenAI program. This `3rdAug/` package sits under it as the
practical, how-to layer: instead of arguing why the platform matters, it specifies which service, which
repository folder, and which Actions workflow implements each piece of the framework the parent
repository describes. Read the parent repository first for the "why"; read this package for the "how."
