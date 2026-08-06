# High-Level Design (HLD) — LLMOps Platform

Working notes for an engineer who has to understand, run, defend, and extend the whole
system. Abbreviations are expanded on first use. This document is kept in sync with the
v2 deck (`../../5thAug/v2/research-brief.md`) and the build contract
(`../ARCHITECTURE_SPEC.md`).

LLMOps = Large Language Model Operations: the practices and platform that make LLM
applications releasable, observable, evaluable, safe, and cost-controlled — the same
discipline DevOps brought to ordinary software, applied to prompts, models, and agents.

## 1. Context — the problem this solves

Today the two use-case teams (APIX, Hiring) most likely: keep prompt text inline in code,
hard-code model names, ship a prompt edit like any code change with no quality gate, rely
on logs (not traces) for debugging, have little cost visibility, and check output quality
by manual spot-check. This platform replaces that with an **enterprise-grade** operating
model where every change (prompt, model, agent) flows through CI/CD, is measured against a
golden dataset by an **evaluation gate** before it can deploy, and everything that runs is
traced, costed, guarded, and improvable from feedback.

The platform is the **shared framework**. A use case adds a folder that inherits all the
machinery and supplies only its own content (prompts, agents, golden data, data sources,
guardrail tuning, dashboards).

See `diagrams/context.mmd` for the C4 system-context diagram. Key external actors: the
engineer and reviewer (via GitHub), the platform/SRE operator, the subject-matter expert
(SME) who authors golden data, and the end user of a use case. Key external systems:
Azure OpenAI, Azure AI Search, Azure AI Document Intelligence, Azure AI Content Safety,
Cosmos DB, Application Insights, API Management, Key Vault/Entra ID, GitHub, and a
self-hosted Langfuse.

## 2. Layered architecture

Read this top to bottom. Each layer depends only on the ones below it, through interfaces
(dependency inversion), so adapters (Azure clients, registries) can be swapped or mocked.

```
Channels & triggers        HTTP callers, Azure Functions (new transcript / nightly)
        |
Gateway                    API Management (quotas, throttling, routing)
        |
Serving / control plane    FastAPI api/ (health, prompts, models, evals, traces, costs,
                           feedback, agents, guardrails, usecases) + React Console
        |
Orchestration              Pipeline runtime: sequential Steps -> Agents (prompt+tools+model)
        |
   +----+-----------------------------+-----------------------------+
   |                    |             |                |            |
Prompts            Model routing   Guardrails      Data-access   Tools (MCP)
(registry+render)  (alias->deploy) (in/out checks) (RAG/SQL/docs) (search/sql/doc/record)
        |
Systems of record          Azure OpenAI, AI Search, Document Intelligence, Cosmos, SQL
        |
Cross-cutting (all layers) Observability (App Insights + Langfuse, cost) ;
                           Evaluation gate (from GitHub CI/CD) ; Feedback -> golden data ;
                           Identity & secrets (Entra ID / Managed Identity / Key Vault)
```

Container view: `diagrams/container.mmd`. Component wiring: `diagrams/component.mmd`.

## 3. The 12 components

Numbering matches the deck. Each is detailed at code level in `lld.md`.

1. **Source control & CI/CD** (`.github/`, `infra/`) — GitHub is the source of truth.
   Three workflows: `pr-checks` (lint + unit + eval subset gate on PR), `eval-full` (full
   golden run on merge/nightly), `deploy` (OIDC login, gated environments, canary,
   rollback). `CODEOWNERS` forces review on `usecases/*/prompts` and `platform/`.
2. **Prompt registry & management** (`prompts/`) — one `*.prompt.yaml` per prompt with
   `id, version, labels, model_alias, temperature, inputs, template, eval_refs,
   changelog`. Backends behind one `PromptRegistry` interface: Git (default), Langfuse,
   Foundry. `load_prompt(id, label)` is the only call site app code uses.
3. **Model catalog & routing** (`models/`, `platform/models.yaml`) — task alias ->
   deployment name per environment; `ModelRouter.resolve(alias)`; an async `ModelClient`
   over Azure OpenAI that emits a tracing span + cost; a price table in `pricing.py`.
4. **Evaluation engine & gate** (`evaluation/`, `evals/run.py`) — golden datasets, metric
   groups (RAG via Ragas, writing quality via DeepEval, agent/tool behaviour via custom
   Python, LLM-as-judge), thresholds (baseline-relative + absolute floors), and the CI
   gate that blocks a release on regression.
5. **Observability & tracing (+ cost)** (`observability/`) — OpenTelemetry with GenAI
   semantic conventions; spans nest request -> agent -> model/tool; cost computed once at
   emit and exported to both Application Insights (system of record) and Langfuse (LLM
   lens). Answers: what is tracked per request, model call, tool call, agent session.
6. **Guardrails engine** (`guardrails/`) — an ordered list of `Guard`s run as input checks
   (before the model) and output checks (before returning/storing): Content Safety, PII
   redaction, JSON/schema validation, prompt-injection (Prompt Shields).
7. **Data-access (RAG/SQL/docs)** (`data_access/`) — beyond RAG: `RagRetriever` (Azure AI
   Search), `SqlDataSource` (read-only, parameterised NL2SQL over allow-listed tables),
   `DocumentExtractor` (Document Intelligence), `RecordClient` (systems of record).
   RAG = Retrieval-Augmented Generation; NL2SQL = natural language to SQL.
8. **Reusable tool catalog (MCP)** (`tools/`, `platform/tools/registry.yaml`) — four
   reusable tools (`search_knowledge`, `query_sql`, `extract_document`, `get_record`) with
   MCP-compatible descriptions; use cases compose these and add their own.
9. **Orchestration / pipeline runtime** (`orchestration/`) — `Pipeline` runs an ordered
   list of `Step`s (each wraps an `Agent`), loaded from `pipeline.agent.yaml`. Sequential,
   not agent-to-agent (see ADR 0004). State can checkpoint to Cosmos.
10. **Serving & gateway** (`api/`, `platform/gateway/`) — FastAPI control-plane behind API
    Management; hosted on Azure Container Apps (autoscale, scale-to-zero); Functions for
    event/scheduled triggers.
11. **Feedback capture & analytics** (`feedback/`) — capture thumbs/edits/overrides tied
    to a trace id; land as events in App Insights + Cosmos; triage negatives; promote
    confirmed bad cases to golden candidates.
12. **Console** (`frontend/`) — React 18 + TypeScript LLMOps Console: dashboard, prompts,
    models, evaluations, traces, costs, agents, guardrails, feedback, onboarding.

## 4. The four flows

### 4.1 Change flow (a prompt/model/agent edit reaches production)
Author edits a YAML/config -> pull request -> peer + CODEOWNER review -> automated checks
(lint, unit, contract) -> **evaluation gate** (golden-set metrics vs baseline; blocks on
regression) -> merge -> promotion gates (dev auto; test and prod need an approver +
`eval-full` pass) -> canary (~10% traffic, watch SLOs 15 min) -> full rollout or
auto-rollback. Diagram: `diagrams/sequence-prompt-change.mmd`.

### 4.2 Request flow (an end-user request is served)
Caller -> API Management -> FastAPI -> `Pipeline.run` (new trace id) -> input guardrails
-> for each step: load prompt, render, optionally call a tool, call the model (router
resolves alias -> deployment; span records tokens + cost) -> output guardrails -> response.
Diagram: `diagrams/sequence-pipeline-run.mmd`.

### 4.3 Telemetry flow (what is recorded)
Every request opens one trace; child spans nest agent -> model/tool. Each model-call span
records `gen_ai.*` attributes plus `app.prompt_id`, `app.prompt_version`, input/output
tokens, and `app.cost_usd` (computed once). Each tool span records `tool.name`,
`tool.mcp_server`, redacted args, status, and — when an expected tool is known —
`eval.was_correct_tool`. The same spans export to Application Insights (KQL/Workbook
aggregation) and Langfuse (ready-made dashboards). Reconcile monthly with Azure Cost
Management.

### 4.4 Feedback flow (bad answers become tests)
Capture feedback (thumbs + reason, coach edits, overrides) tied to the trace id -> land as
scores/events -> triage negatives by cause (bad retrieval? wrong tool? weak prompt?
missing data?) -> promote confirmed cases to the golden dataset with the correct expected
answer -> fix (prompt/retrieval/agent) and re-run the gate -> ship.

## 5. Technology choices

- **Backend**: Python 3.11, FastAPI, pydantic v2, async I/O, OpenTelemetry.
- **Frontend**: React 18 + TypeScript, Vite, React Query, React Router v6, served by nginx.
- **Models**: Azure OpenAI (aliases `reason`/`bulk`/`judge`/`voice`/`embed`).
- **Retrieval**: Azure AI Search; **documents**: Azure AI Document Intelligence.
- **Safety**: Azure AI Content Safety (incl. Prompt Shields, groundedness, protected
  material) + Presidio/Azure AI Language for PII.
- **State/feedback**: Cosmos DB (serverless in dev).
- **Observability**: Application Insights / Log Analytics + self-hosted Langfuse.
- **Gateway**: API Management. **Hosting**: Azure Container Apps (+ Functions for triggers).
- **Identity/secrets**: Entra ID + Managed Identity + Key Vault (no keys in code).
- **Source + CI/CD**: GitHub + GitHub Actions with OIDC federated login and Environments.
- **Evaluation**: Ragas + DeepEval + custom Python + LLM-as-judge (small `judge` model).

Decisive stance (per the v2 brief): these are *the* choices, not a menu. Rationale for the
load-bearing ones is in `adr/`.

## 6. Non-functional requirements

- **Security** (see `security.md`): Zero Trust; Entra ID + Managed Identity for all Azure
  access; secrets only in Key Vault; API Management enforces quotas/throttling; guardrails
  on every input and output; OWASP LLM Top 10 mapped to concrete controls; PII detected
  and redacted before storage/return; least-privilege data-access (read-only,
  allow-listed SQL tables).
- **Scale**: Container Apps autoscale and scale-to-zero for bursty/idle load; Functions
  for event/scheduled work; stateless API with state in Cosmos so instances scale
  horizontally; CI scopes work to changed paths so evals stay fast.
- **Cost** (FinOps): cost metered per model call (`app.cost_usd`), aggregated by use
  case/day/model; the biggest driver is model tokens (mitigate with a small `judge` model,
  eval subset on PR + full nightly, cached inputs, `bulk` alias for simple steps); other
  services are modest fixed cost. Indicative figures (label "confirm at sizing"): Azure
  OpenAI GPT-5.5 ~ $5 in / $30 out per 1M tokens (cached input ~ $0.50), mini/nano far
  cheaper; AI Search Basic ~ $74/mo, S1 ~ $245/mo; Langfuse self-host infra ~ $50-150/mo;
  Container Apps/Functions consumption (low); Content Safety per-1k-records (minor).
- **Availability**: gated promotions (dev -> test -> prod) with an approver + eval pass;
  canary release with SLO watch (latency, errors, groundedness) and auto-rollback;
  stateless services behind the gateway; graceful degradation to mocks in dev where a live
  client is not wired.
- **Maintainability/observability**: everything typed, structured-logged, and traced;
  config-as-code for models and evaluators; ADRs record why.

## 7. Environments

`dev` (auto-deploy, cheaper models, mocks allowed), `test` (approver + eval-full),
`prod` (approver + eval-full, canary + rollback). `models.yaml` differs per environment so
prod can use a stronger `reason` model without any code change.
