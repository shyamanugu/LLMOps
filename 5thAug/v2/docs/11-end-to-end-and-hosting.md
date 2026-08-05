# End-to-End & Azure Hosting Plan

This document wires the whole platform together in one diagram and walks the four flows through it, lays out the Azure hosting plan as a bill of services **with indicative cost and capabilities**, states honestly what a new use case inherits versus what it must define itself, and closes with a before/after summary and what we need to proceed.

## How it all fits together (end to end)

GitHub holds everything as code and runs the gate. Azure runs it, behind one API Management front door, per environment. Telemetry flows to App Insights and Langfuse, then to a Fabric lakehouse, and feedback flows back into the `evals/` folder in GitHub — closing the loop.

```
  ┌──────────────────────────────── GitHub (source of truth) ─────────────────────────────────┐
  │  platform/ (shared)   usecases/<uc>/ (prompts·agents·evals·tools·config)   models.yaml       │
  │  Actions:  pr-checks.yml (unit + eval-subset GATE) · eval-full.yml · deploy.yml (canary)      │
  └───────────────┬──────────────────────────────────────────────────────────▲──────────────────┘
        (1) CHANGE│ OIDC login · gated envs · promotion gate · canary + rollback │ new golden cases
                  ▼                                                            (4) FEEDBACK loop
  ┌─────────────── Azure  (dev ─▶ test ─▶ prod, landing zone) ──────────────────┼──────────────────┐
  │                                                                             │                  │
  │  CHANNELS & TRIGGERS                                                         │                  │
  │   caller / app ─▶┐        events (new transcript in Blob · nightly) ─▶ Azure Functions          │
  │                  ▼                                                           │                  │
  │            API Management (APIM)  ── quotas · token metering · cache · auth (ONE entry point)    │
  │                  │                                                                               │
  │                  ▼   ORCHESTRATION / PIPELINE  (Container Apps)                                  │
  │            ┌──────────────────────────────────────────────────────────────────────────────┐    │
  │            │  orchestrator + pipeline steps (agents)                                        │    │
  │            │    ├─ AGENTS ─▶ Model Router (models.yaml) ─▶ Azure OpenAI (GPT-5.x, embed)    │    │
  │            │    ├─ DATA-ACCESS TOOLS ─▶ search_knowledge (RAG / AI Search)                  │    │
  │            │    │                     ─▶ query_sql (NL2SQL / Azure SQL, read-only)          │    │
  │            │    │                     ─▶ extract_document (Document Intelligence)           │    │
  │            │    │                     ─▶ get_record (system of record via MCP)              │    │
  │            │    └─ GUARDRAILS ─▶ Content Safety (in/out) + PII redaction                    │    │
  │            └───────────────┬──────────────────────────────────────────────┬─────────────────┘    │
  │                            │ writes / reads                                │ authoritative reads  │
  │                            ▼                                               ▼                      │
  │                   Cosmos DB / Azure SQL (runs, outputs, scores)     SYSTEMS OF RECORD              │
  │                                                                                                   │
  │  ── cross-cutting ─────────────────────────────────────────────────────────────────────────────  │
  │  (3) OBSERVABILITY: OpenTelemetry spans ─▶ Application Insights (record) + Langfuse (LLM lens)     │
  │      EVAL GATE:     from GitHub CI/CD — blocks any change that regresses the golden set            │
  │      FEEDBACK:      App Insights + Langfuse ─▶ Fabric lakehouse ─▶ triage ─▶ golden cases ─────────┘
  └───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### The four flows

1. **Change flow (build/deploy).** An author edits a prompt, model alias, agent design, tool, or eval config in GitHub. `pr-checks.yml` runs unit/contract tests and the **evaluation gate** (golden-set subset vs baseline). On merge, `eval-full.yml` runs the full golden set. `deploy.yml` promotes dev → test → prod through the **promotion gate** (approver + `eval-full` pass) and releases with a **10% canary** watched against SLOs, auto-rolling-back on regression.

2. **Request flow (runtime).** A caller hits APIM, or a Function fires on a new transcript / nightly schedule and calls the orchestrator. The orchestrator runs the pipeline steps; agents resolve their model through the router, pull data through the data-access tools (RAG, SQL, documents, records), and pass through guardrails on the way in and out. Outputs and run state land in Cosmos DB / Azure SQL; authoritative live values come from systems of record via `get_record`.

3. **Telemetry flow (observability).** Every model call, tool call, and agent step emits an OpenTelemetry span carrying tokens, cost, prompt id/version, tool name, and tool-correctness. The same span goes to **Application Insights** (system of record for querying and alerts) and **Langfuse** (ready-made LLM/cost dashboards). Both feed the **Fabric lakehouse**.

4. **Feedback flow (improvement).** Thumbs, coach edits, and overrides — tied to the trace id — land as events, are triaged in Fabric by cause (bad retrieval, wrong tool, weak prompt, missing data), and the confirmed bad cases become new golden cases committed back to `usecases/<uc>/evals/` in GitHub. The gate gets stricter each cycle.

## Onboarding a new use case — what it inherits vs what it must define

It is tempting to say a new use case is "just add four files." That is not honest, and it sets the wrong expectation. A new use case **inherits** a large shared platform, but it genuinely has to **define its own** substance, because every use case differs in its data, its task, and its definition of a good answer.

**What a new use case inherits (built once, reused — the shared platform):**

- Source control, CI/CD, the evaluation gate, OIDC, and gated environments.
- Prompt registry and loader, model catalog and router.
- Observability and tracing, FinOps/cost metering.
- The guardrails engine, the data-access framework, and the **reusable tool catalog** (`search_knowledge`, `query_sql`, `extract_document`, `get_record`).
- Orchestration/pipeline runtime, the APIM gateway, identity and secrets, feedback capture and analytics.

**What a new use case must define itself (new every time):**

- **Prompts** — the actual prompt content and structure for its task.
- **Agent / pipeline design** — the ordered steps, what each step does, how they hand off.
- **Data sources + connectors** — where its data lives and how we connect to it.
- **Retrieval / index setup** — its own AI Search index, chunking rules, filters (for the RAG parts).
- **Tools** — reuse from the catalog where they fit, **and build new ones** where its data access is genuinely different.
- **Guardrail policy** — which guardrails apply and how they are tuned for its content and risk.
- **Golden dataset + thresholds** — its own ground truth and its own pass/fail bars.
- **Eval config** — which metrics and evaluators run for it.
- **Dashboards** — the views its owners watch.
- **Integration / UI** — often a use-case-specific surface or system integration.

So the honest message is: the **machinery** is shared and does not get rebuilt, but the **substance** — prompts, design, data, retrieval, tools, guardrail policy, golden data, eval config, dashboards, and usually integration — is real work that differs each time. A use case is not a copy-paste of four files; it is new content and design sitting on top of a platform that saves it from rebuilding the plumbing.

## Azure hosting plan — cost and capabilities

Grouped by layer, so it is clear what each service does, how it is priced, and roughly what it costs. **All figures are indicative — confirm at a sizing exercise.** The one thing to hold onto: **model tokens dominate the bill**; the rest is modest, mostly fixed, cost.

| Service | Capability | Pricing model | Indicative /mo |
|---|---|---|---|
| **Azure OpenAI** | The models (chat + embeddings) | Per token; or reserved Provisioned Throughput Units (PTU) for sustained load | GPT-5.5 ≈ $5 in / $30 out per 1M tokens (cached input ≈ $0.50); mini/nano far cheaper (nano ≈ $0.05/$0.40); **PTU ≈ $2,448/mo** sustained. **Biggest, usage-driven variable.** |
| **Azure AI Search** | RAG index (vector + keyword) | Per search unit / tier | Basic ≈ **$74/mo**; Standard S1 ≈ **$245/mo** |
| **Azure Container Apps** | Run the pipeline services | Consumption, scale-to-zero | ~tens of $/mo (small) |
| **Azure Functions** | Event triggers | Per execution | ~negligible at low volume |
| **Cosmos DB / Azure SQL** | State, outputs, scores | Serverless / provisioned | ~tens of $/mo (small) |
| **App Insights / Log Analytics** | Observability | Per GB ingested | ~tens of $/mo (volume-dependent) |
| **Langfuse (self-hosted)** | LLM observability + prompt management | MIT-licensed software (free) + infra to self-host | ≈ **$50–150/mo** infra |
| **Azure AI Content Safety** | Guardrails | Per 1,000 records | minor |
| **API Management** | Gateway | Tiered / consumption | Basic/Standard ~$/mo |

**Reading the table:** everything except Azure OpenAI is a modest, fairly predictable fixed cost — a few tens to low hundreds of dollars a month per service. Azure OpenAI is the one that moves with usage, and within it the model tokens (input + output) are the driver. That is why the platform meters cost per call (`app.cost_usd` on every span) and why a model swap goes through the evaluation gate: cost control is mostly about token control. For sustained, predictable load, PTU (≈ $2,448/mo) trades per-token billing for reserved throughput. Reconcile monthly against Azure Cost Management (the actual invoice). Again: **indicative, confirm at sizing.**

## Shared platform vs per-use-case (at a glance)

| Shared platform (built once, reused) | Per-use-case (defined new each time) |
|---|---|
| CI/CD workflows, OIDC, environments, evaluation gate | Prompt content (`usecases/<uc>/prompts/*.prompt.yaml`) |
| `platform/common/` — prompt loader, model router, tracing, guardrails | Agent / pipeline design (`usecases/<uc>/agents/`) |
| Reusable tool catalog (`search_knowledge`, `query_sql`, `extract_document`, `get_record`) | Use-case tools: reuse from catalog **or build new** |
| APIM gateway, landing zone, networking | Its data sources + connectors; its retrieval/index + chunking |
| Container Apps env, deploy/canary/promotion machinery | Its guardrail policy tuning |
| Azure OpenAI resource, `models.yaml` structure, model router | Its golden dataset + thresholds; its eval config |
| Content Safety, PII redaction, Cosmos DB, feedback capture | Its dashboards; often its integration / UI |

The rule: a new use case is new **content and design** on top of shared **infrastructure** — not new plumbing, but genuinely more than four files.

## Summary — before vs after

| Dimension | Today | With this LLMOps setup |
|---|---|---|
| Release safety | Replace-all deploy; roll back by hand | 10% canary watched on SLOs; automatic rollback; promotion gate (approver + eval-full) |
| Prompt changes | Prompt text buried in code; ships like any code, no check | Versioned YAML prompt; evaluation gate on every change; rollback/compare by version |
| Quality visibility | Manual spot-checks | Golden-dataset evaluation as a gate at every change; groundedness/tool-selection tracked |
| Cost visibility | Guesswork from the invoice | Cost metered per call on every span; per model / prompt / use case; reconciled to Azure Cost Management |
| Debugging a bad answer | Read plain logs, guess | One trace id end-to-end: model calls, tool calls, tokens, retrieval, tool-correctness |
| Adding a use case | Re-solve everything from scratch | Inherit the shared platform; define its own prompts, design, data, tools, guardrails, golden set, dashboards |
| Swapping a model | Edit hard-coded model names in agent code | One-line change in `models.yaml`, reviewed, must pass the evaluation gate |
| Guardrails | Little or none | Content Safety in/out + PII redaction as a fixed step around every model call; policy tuned per use case |
| Data access | Direct reads; keyword search; structured data stuffed into the prompt | RAG for text, read-only NL2SQL for structured facts, Document Intelligence for files, `get_record` for live systems |

**The value line:** the same pipelines the teams run today, but every change is evaluated before it ships, every request is traced and costed, every bad answer becomes a permanent test, and the next use case reuses the platform instead of rebuilding it. That is the difference between "prompts in Git" and enterprise-grade LLMOps.

## What we need to proceed

No dates — just the inputs that unblock the build:

- **Azure subscription and landing-zone access** with rights to create the resource groups and services in the bill above, and to register the GitHub OIDC federated credential.
- **Confirmation of the "today" assumptions** per component — especially how APIX prompts and model choices are set now, so the migration steps are accurate.
- **A GitHub organisation/repo** for the monorepo, with the ability to set branch protection, CODEOWNERS, and GitHub Environments with required reviewers.
- **Access to the APIX data sources** — the transcript blob container / SQL table and metadata, plus the tables to allow-list for `query_sql` — for the first indexer and the first structured tool.
- **SME time** to author the first golden datasets for APIX (telesales and one more program), the seed the whole gate depends on.
- **A named reviewer** for the test and prod environment approvals.
- **Sign-off on the indicative recurring cost** (model tokens dominate; the rest is modest fixed cost) and on self-hosted Langfuse and (later, if adopted) Foundry prompt assets — all to be confirmed at a sizing exercise.
