# End-to-End Architecture

This document puts all the individual components (source control, prompts, models, evaluation,
observability, feedback, data pipelines, guardrails, serving, agents) into one picture. It answers a
different question than the component-level docs: not "what is prompt management" but "when someone
sends a message and it gets an answer, and when an engineer changes a prompt, what actually happens,
in order, across which systems." One diagram, five flows through it.

## The full picture

```
 ============================ 1. CHANGE FLOW (source of truth) ============================
 GITHUB (monorepo)
   /prompts   /agents   /evals   /src   /pipelines   /infra   /dashboards
   Actions: pr-checks.yml (lint+unit+eval subset) -> eval-full.yml (nightly/on-merge)
            -> deploy.yml (build, gated dev->test->prod, canary, auto-rollback)
            -> index-refresh.yml (scheduled RAG re-index)
   Auth: GitHub OIDC (OpenID Connect) -> Entra ID, no stored cloud keys. Secrets from Key Vault.
        |
        | deploy.yml, gated by required reviewers per environment
        v
 -------------------------------------------------------------------------------------------
 AZURE ENVIRONMENTS (dev -> test -> prod, same topology each tier)
   Entra ID (identity) | Key Vault (secrets) | Azure API Management (APIM) as AI gateway
   [private endpoints, no public inbound to model/data services]
        |
        | inbound request, per (2. REQUEST FLOW)
        v
 -------------------------------------------------------------------------------------------
 RUNTIME (inside the APIM perimeter)
                         +-----------------------------------+
                         |   Foundry Agent Service            |
                         |   (orchestrator / supervisor)      |
                         +------------------+------------------+
                                            |
              +----------------------------+----------------------------+
              |                            |                            |
     +--------v--------+         +---------v--------+         +--------v---------+
     | Specialist agent |         | Specialist agent  |         | Specialist agent |
     | (router/intent)  |         | (retrieval/RAG)   |         | (tool/action-MCP)|
     +--------+--------+         +---------+--------+         +--------+---------+
              |                            |                            |
     +--------v--------+         +---------v--------+         +--------v---------+
     | Azure OpenAI      |         | Azure AI Search   |         | MCP tool servers |
     | (GPT-5.x models,   |         | (RAG index)        |         | (line-of-business|
     |  Model Router)     |         |                    |         |  systems, CRM)   |
     +--------------------+         +--------------------+         +------------------+
              |                            |                            |
              +----------- Content Safety guardrails (in + out) --------+
                                            |
                                   Cosmos DB (session / agent memory)
        |
        | every model call, tool call, and agent hop emits a span (3. TELEMETRY FLOW)
        v
 -------------------------------------------------------------------------------------------
 TELEMETRY
   OpenTelemetry SDK -> Application Insights (system of record, stays in tenant)
                      -> Langfuse (self-hosted on Azure Container Apps + Postgres;
                                    LLM-specific lens: sessions, prompt versions, feedback scores)
        |
        | export (diagnostic settings) + explicit feedback events (4. FEEDBACK FLOW)
        v
 -------------------------------------------------------------------------------------------
 MICROSOFT FABRIC LAKEHOUSE (OneLake)
   Analytics tables <- App Insights export + Langfuse export
   Power BI dashboard: volume, containment, p95 latency, cost/use case, quality trend, top
                        negative-feedback reasons
   Training-data curation: human-approved responses, PII-scrubbed, staged for fine-tuning
        |
        | curated cases + mined traffic, reviewed by SME
        v
 -------------------------------------------------------------------------------------------
 back to GITHUB /evals  (golden dataset gets new cases -> next PR is graded against a
                          stronger baseline -> loop closes)

 ============================ 5. DATA / KNOWLEDGE REFRESH FLOW =============================
 Sources (SharePoint, Blob, SQL, CRM/ticketing, call transcripts)
   -> ingestion (Fabric Data Factory / Logic Apps / AI Search indexers)
   -> clean + PII-scrub -> chunk -> embed (text-embedding-3-large)
   -> Azure AI Search index (blue-green via index aliases)
   -> same runtime "retrieval/RAG" agent above reads the new index automatically
```

## Flow 1 — Change flow

Every prompt, agent definition, model alias, or golden-dataset edit starts as a pull request in GitHub.
`pr-checks.yml` runs lint, unit tests, and a small evaluation subset scoped to whatever changed. If a
blocking metric regresses, the pull request is blocked — nothing further happens. On merge to the main
branch, `eval-full.yml` runs the complete golden set and posts a scorecard. `deploy.yml` then builds the
container and walks it through GitHub Environments: dev, then test, then production, each gate requiring
an approving reviewer, with a canary slice taking traffic first in production and an automatic rollback if
health checks or evaluation scores alarm. Authentication from GitHub to Azure uses OpenID Connect (OIDC)
federated credentials — there is no long-lived cloud key sitting in a repository secret.

## Flow 2 — Request flow

A user request arrives through Azure API Management, the single front door for every environment. APIM
enforces quotas, applies caching where safe, and forwards the request inside the private network to the
Foundry Agent Service orchestrator. The orchestrator (a router/supervisor agent) decides which specialist
agent handles the request — retrieval, a tool/action call over the Model Context Protocol (MCP), or a
direct model response — and specialist agents call Azure OpenAI models, Azure AI Search for retrieval-
augmented generation (RAG), or external systems through MCP tool servers. Every input and output passes
through Content Safety guardrails before it reaches the user. Session and agent memory persist in Cosmos
DB so a multi-turn conversation or a paused, resumable workflow can pick up where it left off.

## Flow 3 — Telemetry flow

Every model call, every tool call, and every agent hop emits an OpenTelemetry span: prompt, completion,
token counts, cost, latency, model and version, prompt version, use-case tag, session and user identifiers.
Application Insights is the system of record — the data never leaves the tenant. The same spans also flow
to Langfuse (self-hosted on Azure Container Apps with a Postgres database), which gives the team an
LLM-specific view: per-session traces, prompt-version comparisons, and a place to attach user feedback
scores next to the trace that produced them.

## Flow 4 — Feedback / improvement flow

Users leave explicit signals (thumbs up/down and a reason, message edits, escalation to a human agent) and
the system logs implicit ones (retries, session length, abandonment). Both write to Application Insights
custom events and to Langfuse scores, tagged with the trace id of the response they refer to. On a set
cadence, negative feedback and low-scoring traces are triaged, labeled, stripped of personally identifiable
information (PII), and — after a subject matter expert (SME) confirms what the right answer should have
been — added to the golden dataset in `/evals` back in GitHub. The next pull request is graded against a
dataset that now includes the failure that was just fixed, so the same mistake cannot silently come back.

## Flow 5 — Data / knowledge refresh flow

For RAG use cases, source documents (SharePoint, Blob Storage, SQL, CRM/ticketing systems, call
transcripts) are ingested on a schedule or via change-data-capture, cleaned, scrubbed of PII, chunked, and
embedded, then written to an Azure AI Search index. Index aliases allow a blue-green swap — a new index
version is built and validated before the alias is flipped, so a bad re-index never reaches production
traffic. `index-refresh.yml` in GitHub is what triggers the scheduled run; the retrieval agent in the
runtime layer simply reads whichever index the alias currently points to, so no code change is needed to
pick up refreshed knowledge.

## Environment and network note

All four flows run inside a private network boundary, not over the public internet. Azure OpenAI, Azure
AI Search, Cosmos DB, and the Foundry Agent Service runtime sit behind private endpoints, reachable only
from inside the virtual network or through APIM. Entra ID (Microsoft's identity platform) is the single
identity authority for both humans (portal access, approvals) and workload identities (the app's own
service principal, agent-to-agent calls). Key Vault holds every secret and connection string; nothing is
stored in application configuration files or repository secrets. GitHub's connection to Azure uses OIDC
federated credentials scoped per environment, so a compromised dev credential cannot reach production. The
same pattern (private endpoints, Entra ID, Key Vault, OIDC) is identical across dev, test, and production —
only the resource names and scale differ, which is what makes promoting a change between environments a
configuration change rather than a rebuild.
