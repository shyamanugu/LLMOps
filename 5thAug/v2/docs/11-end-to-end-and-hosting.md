# End-to-End & Azure Hosting Plan

This document wires the whole platform together in one diagram, then lays out the Azure hosting plan as a bill of services, states what is shared across use cases versus what is per-use-case, and consolidates the "today → our setup → what changes" delta for every component in one table. It closes with what we need from you to proceed.

## The end-to-end wiring

GitHub holds everything as code and runs the gate. Azure runs it, behind one API Management front door, per environment. Telemetry flows to App Insights and Langfuse, then to a Fabric lakehouse, and feedback flows back into the `/evals` folder in GitHub — closing the loop.

```
  ┌─────────────────────────────── GitHub (source of truth) ───────────────────────────────┐
  │  prompts/  agents/  evals/  models.yaml  src/  infra/  dashboards/                        │
  │  Actions:  pr-checks.yml (unit + eval-subset GATE)  ·  eval-full.yml  ·  deploy.yml       │
  └───────────────┬──────────────────────────────────────────────────────▲──────────────────┘
                  │ OIDC federated login · gated envs · canary + rollback  │ new golden cases
                  ▼                                                        │ (feedback -> /evals)
  ┌──────────────────────── Azure  (dev ─▶ test ─▶ prod, landing zone) ────┼──────────────────┐
  │                                                                        │                  │
  │   caller ─▶  API Management  ── quotas · token metering · cache · auth (one entry point)   │
  │                    │                                                                       │
  │   events ─▶ Azure Functions (new transcript / new candidate)                               │
  │                    ▼                                                                       │
  │            Container Apps                                                                   │
  │            ┌───────────────┐   calls    ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
  │            │ orchestrator  │──────┬────▶ │ Azure      │  │ Azure AI   │  │ Content Safety│  │
  │            │ + pipeline    │      ├────▶ │ OpenAI     │  │ Search     │  │ + PII redact  │  │
  │            │ agents (steps)│      └────▶ │ (models)   │  │ (RAG index)│  └───────────────┘  │
  │            └───────┬───────┘             └────────────┘  └────────────┘                     │
  │                    │ state / traces                                                         │
  │                    ├──────────────▶ Cosmos DB (runs, outputs, trace ids)                    │
  │                    ▼                                                                        │
  │            OpenTelemetry spans ─▶ Application Insights (system of record)                    │
  │                                 ─▶ Langfuse (LLM lens, self-hosted container)                │
  │                                          │                                                   │
  │                                          ▼                                                   │
  │                                 Microsoft Fabric lakehouse  ── traces + feedback + cost ─────┘
  │                                          │  triage -> label -> golden cases
  └──────────────────────────────────────────┘  (back to GitHub /evals, top of diagram)
```

Read it as one sentence: a change enters GitHub, must pass the evaluation gate, deploys through OIDC into the right Azure environment behind APIM, runs on Container Apps against Azure OpenAI / AI Search / Content Safety with state in Cosmos DB, emits traces to App Insights and Langfuse and then to Fabric, where feedback is triaged into new golden cases that go back to `/evals` — and the gate gets stricter each cycle.

## Azure hosting plan — bill of services

Grouped by layer, so it is clear what each service is for and where each piece runs.

| Layer | Azure service | Purpose |
|---|---|---|
| Source & CI/CD | GitHub + GitHub Actions | Repo of record; the three workflows; OIDC to Azure, no stored keys |
| Landing zone | Management groups, resource groups, VNet | Three isolated environments (dev/test/prod), network boundary |
| Gateway | API Management (APIM) | One entry point; quotas, rate limits, token metering, response caching, auth |
| Compute — pipeline | Azure Container Apps | Each pipeline step a scale-to-zero container; revisions for canary/rollback |
| Compute — triggers | Azure Functions | Event triggers (new transcript, new candidate) |
| Models | Azure OpenAI | Chat + embedding deployments, resolved via `models.yaml` aliases |
| Retrieval / RAG | Azure AI Search | Vector + keyword index, indexers, index aliases (blue-green) |
| Data ingest | Microsoft Fabric Data Factory + Blob Storage / SQL | Sources of record; heavy transforms before indexing |
| Guardrails | Azure AI Content Safety | Input/output category checks around every model call |
| State | Azure Cosmos DB | Pipeline runs, outputs, trace ids |
| Observability | Application Insights (Azure Monitor) + self-hosted Langfuse | System of record for traces/events; LLM lens + prompt registry |
| Analytics & feedback | Microsoft Fabric lakehouse | Joins traces, cost, feedback; source of golden-set enrichment |
| Secrets & identity | Key Vault + Managed Identity / Entra ID | Secrets, federated credentials, service-to-service auth |
| Infra as code | Bicep (in `infra/`) | Every service above provisioned from the repo |

## Shared platform vs per-use-case

| Shared platform (built once, reused) | Per-use-case (a subfolder / config) |
|---|---|
| GitHub Actions workflows, OIDC, environments | `prompts/<use-case>/*.prompt.yaml` |
| `src/common/` — prompt loader, model router, tracing | `agents/<use-case>/pipeline.agent.yaml` |
| APIM gateway, landing zone, networking | `evals/<use-case>/golden.*.jsonl` + `evaluators.yaml` |
| Container Apps environment, deploy/canary machinery | Its Azure AI Search index + indexer + chunking config |
| Azure OpenAI resource, `models.yaml` structure | The environment aliases it uses in `models.yaml` |
| Content Safety, PII redaction, Cosmos DB | Its ingest source (transcripts vs JDs/rubrics) |
| App Insights, Langfuse, Fabric lakehouse | Its feedback capture points (coach edit vs recruiter override) |

The rule: a new use case (a third or fourth beyond APIX and Hiring) is new content under `prompts/`, `agents/`, `evals/`, and one AI Search index — **not** new infrastructure. Everything in the left column is stood up once.

## Consolidated: Today → Our setup → What changes

| Component | Today (to confirm) | Our setup | What changes |
|---|---|---|---|
| Source control & CI/CD | Code in Git; a prompt edit ships like any code change, no gate | Monorepo + three GitHub Actions workflows; OIDC; gated environments | Every change passes the evaluation gate before deploy |
| Prompts | Prompt text buried in code files | One versioned YAML per prompt (`id, version, template, eval_refs`) + runtime registry | New YAML artifact; eval gate on every change; rollback/compare by version |
| Models | Model names hard-coded per agent | `models.yaml` task-alias → deployment; resolver in code | Model swap becomes a reviewed config change through the gate; one shared config |
| Evaluation | Manual spot-checks | Golden datasets + Ragas + DeepEval + custom `tool_selection.py`, thresholds in `evaluators.yaml` | Evaluation runs as a release gate at every change, not ad hoc |
| Observability | Plain logs | OpenTelemetry spans per model/tool/agent call → App Insights + Langfuse | Every request traced end to end with tokens, cost, tool correctness |
| Guardrails | Little or none | Content Safety in/out + PII redaction around each model call | Safety and PII handling become a fixed step, not optional |
| Data & RAG | Direct reads; keyword search; manual re-index | Ingest → clean/redact → chunk → embed → AI Search index; schedule + CDC; index aliases | Governed hybrid retrieval; automatic refresh; blue-green re-index |
| Serving | One process; direct calls; replace-all deploys | Container Apps per step behind APIM; Functions for triggers | Independent scaling, one governed front door, canary + auto-rollback |
| Feedback | Anecdotal, untied to responses | Trace id + `/feedback` → App Insights/Langfuse → Fabric → golden set → gate | A defined improvement loop; production failures become permanent tests |

## What we need to proceed

No dates — just the inputs that unblock the build:

- **Azure subscription and landing-zone access** with rights to create the resource groups and services in the bill above, and to register the GitHub OIDC federated credential.
- **Confirmation of the "today" assumptions** per component — especially how APIX prompts and model choices are set now, so the migration steps are accurate.
- **A GitHub organisation/repo** for the monorepo, with the ability to set branch protection, CODEOWNERS, and GitHub Environments with required reviewers.
- **Access to the APIX data sources** — the transcript blob container / SQL table and metadata — for the first indexer.
- **SME time** to author the first golden datasets for APIX (telesales and one more program), the seed the whole gate depends on.
- **A named reviewer** for the test and prod environment approvals.
- **Sign-off on the minor recurring cost** for self-hosted Langfuse and (later, if adopted) Foundry prompt assets.
