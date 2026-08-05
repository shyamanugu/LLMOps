# LLMOps Implementation Overview

This is an implementation document, not an options paper. It describes the concrete Large Language Model Operations (LLMOps) setup we are putting in place for your Azure and GitHub environment, using the APIX pipeline as the running example and Hiring Intelligence as a second, lighter case. It is enterprise-grade, and it is reusable: the same components serve any future use case without a rebuild.

## How to read this

Every component document follows the same three-part shape:

- **Today** — what the APIX and Hiring teams already do (some of this is assumption, to confirm with you).
- **Our setup** — the concrete files, code, and configuration we put in place.
- **What changes** — the specific delta and the small migration step to get there.

We lead with the delta on purpose. The point of these documents is not to describe LLMOps in the abstract; it is to show exactly what is different from how the teams work now, and why that difference matters. Where an alternative tool or approach is worth naming, it gets a one-line footnote, not a comparison table.

## Two pipelines, one platform

Both APIX and Hiring Intelligence are **sequential agent pipelines** — an ordered set of steps, each step running a prompt against a model, some steps calling tools. They are not agents talking to other agents. That keeps the runtime predictable and makes each step separately testable and evaluable.

APIX (contact-center coaching) is the worked example throughout: it takes call transcripts, scores them on dimensions, and produces a coaching report. Hiring Intelligence (job descriptions, rubrics, candidate scoring) reuses the exact same platform components; it is still being scoped, so we keep it light here.

## Most of the machinery is shared

This is the point to take away before any detail: **the platform is built once and reused by every use case.** A new use case does not get its own infrastructure, its own pipeline code, its own evaluation engine, or its own gateway. It gets a folder that holds its own prompt text, its own agent design, its own golden dataset, and its own data connections — and it inherits everything else.

The table below lists every component and marks whether it is **shared** (built once, reused by all use cases) or **per-use-case** (new content each time a use case is added). The shared column is deliberately long and the per-use-case column deliberately short. That ratio is the value of the platform.

### Shared platform (built once, reused by every use case)

| Component | Shared or per-use-case | Note |
|---|---|---|
| Source control & CI/CD | Shared | One monorepo and one set of GitHub Actions workflows run every use case's changes through the same gate. |
| Prompt registry & management | Shared | The loader, the versioning scheme, and the registry mechanism are common; only the prompt text is per use case. |
| Model catalog & routing | Shared | One `models.yaml` maps task aliases to Azure OpenAI deployments; every agent resolves models through the same router. |
| Evaluation engine & gate | Shared | Ragas, DeepEval, and the custom tool-selection harness run for all use cases; only thresholds and datasets differ. |
| Golden-dataset framework | Shared | The record format, the sourcing method, and the runner are common; the dataset *contents* are per use case. |
| Observability & tracing | Shared | One `tracing.py` emits the same OpenTelemetry spans for every use case into App Insights and Langfuse. |
| FinOps / cost metering | Shared | Cost is computed once per model-call span and aggregated the same way across all use cases. |
| Guardrails engine | Shared | The Content Safety, PII-redaction, and validation machinery is common; only the policy tuning is per use case. |
| Data-access & RAG framework | Shared | The ingest-to-index pipeline and the retrieval layer are built once; each use case points them at its own sources. |
| Reusable tool catalog (MCP tools) | Shared | `search_knowledge`, `query_sql`, `extract_document`, `get_record` are built once in `platform/tools/` and composed by any use case. |
| Orchestration / pipeline runtime | Shared | The engine that runs an ordered pipeline of prompt-and-tool steps is common; each use case supplies the step list. |
| Serving & gateway | Shared | Azure Container Apps hosting and Azure API Management (APIM) front every use case. |
| Identity & secrets | Shared | OpenID Connect (OIDC) federation, managed identities, and Key Vault are set up once for the whole platform. |
| Feedback capture & analytics | Shared | The feedback API, the App Insights/Langfuse events, and the Fabric lakehouse are common; only the reason codes vary. |
| Agent templates / blueprints | Shared | A new pipeline starts from a common blueprint (step shape, tracing, guardrails wired in) rather than a blank file. |

### Per use case (new content each time)

| Component | Shared or per-use-case | Note |
|---|---|---|
| Prompt content | Per-use-case | The actual prompt text, variables, and changelog — one YAML file per prompt under the use case's folder. |
| Agent / pipeline design | Per-use-case | The ordered steps and which prompt and tools each step uses. |
| Golden dataset content + thresholds | Per-use-case | The ground-truth cases and the metric floors the gate enforces for this use case. |
| Data sources & connectors | Per-use-case | Which transcripts, job descriptions, tables, or systems of record this use case reads. |
| Use-case-specific tools | Per-use-case | Any tool this use case needs that is not already in the shared catalog (then it is added to the catalog and reused). |
| Guardrail policy tuning | Per-use-case | Which categories to block, redaction rules, and thresholds appropriate to this use case's content. |
| Dashboards | Per-use-case | The views and alerts that matter for this use case's owners. |

The shared list has fifteen entries; the per-use-case list has seven, and every one of them is content that lives inside a single folder. Standing up the platform is the large piece of work, done once. Onboarding the Nth use case is filling in that folder.

## The order we onboard components

The first thing we set up is source control and Continuous Integration / Continuous Deployment (CI/CD). Everything else plugs into it. Then we onboard the remaining components one at a time, each landing in the same repository and flowing through the same pipeline:

1. **Source control and CI/CD** — the monorepo and the GitHub Actions workflows. The backbone. Every change to a prompt, a model choice, or an agent step flows through here and must pass the evaluation gate before it can deploy.
2. **Prompt management** — one YAML file per prompt, versioned, with an evaluation gate on every change and a runtime registry for rollback and comparison.
3. **Model management** — a single `models.yaml` mapping task aliases to Azure OpenAI deployments, so a model swap is a reviewed config change.
4. **Evaluation** — golden datasets plus concrete scoring mechanisms (Ragas, DeepEval, and custom Python for tool selection), wired into the gate.
5. **Observability** — OpenTelemetry spans capturing every model call, tool call, and agent session, exported to Azure Application Insights and Langfuse.
6. **Guardrails and safety** — Azure Content Safety checks and Personally Identifiable Information (PII) redaction, placed around each model call.
7. **Data and Retrieval-Augmented Generation (RAG)** — the ingest-to-index pipeline feeding Azure AI Search, plus the reusable tool catalog for structured data and documents.
8. **Serving and deployment** — Azure Container Apps hosting each pipeline step behind Azure API Management (APIM), with canary release and automatic rollback.
9. **Feedback and improvement** — capturing real usage, triaging it into the golden set, fixing, and re-evaluating.

The evaluation gate is the thread running through all of this: no prompt, model, or agent change reaches production without being scored against a golden dataset and clearing its thresholds. That single rule is what makes the setup enterprise-grade rather than a collection of scripts.

## The monorepo backbone

Everything lives in one repository, split into a `platform/` half that is shared and a `usecases/` half where each use case gets one folder of the same shape. The next document covers this layout in full. The short version: the shared machinery is written once under `platform/`, and adding a use case means adding a folder under `usecases/` — not new infrastructure.

The next document goes into this layout and the CI/CD workflows in detail, because that is the first thing we stand up. Read the rest in the order above; each one names what changes from today first.
