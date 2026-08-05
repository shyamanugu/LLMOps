# Infrastructure & Azure Hosting (Proposed)

This is the target Azure setup for running the two pipelines — APIX (Afni
Performance Intelligence Index) and Hiring Intelligence — plus the operational
layer around them. Both are agent pipelines (sequential steps), not agent-to-agent
systems, so the hosting is built around pipeline services and event triggers. This
is the proposed shape; there are **no timelines** here — sequencing lives at the
end and in the activities section, without dates.

## Hosting the pipelines — compare, then recommend

| Option | Fit | Note |
|---|---|---|
| Azure Container Apps | Each agent / pipeline step as a container or microservice; scale-to-zero; KEDA autoscale; Dapr optional | Best general fit for the pipeline services |
| Azure Functions | Event-driven steps — "new transcript arrives → analyze", "new candidate → screen" | Great for APIX batch/event triggers and Hiring intake |
| Foundry Agent Service | Managed hosted agents; less infrastructure to run and patch | Consider for hosted agents as the service matures |

**Recommendation:** run the pipeline services on **Azure Container Apps** and use
**Azure Functions for the event triggers** (a new call recording, a new
candidate). Container Apps gives us one container per agent step, independent
scaling, and scale-to-zero so idle steps cost nothing — which suits APIX's bursty
"thousands of calls/day" batch load. Functions handle the "something arrived, kick
off the pipeline" edge cheaply. We can adopt **Foundry Agent Service** later for
specific hosted agents once it fits, without changing the rest of the platform.

## Bill of services (grouped)

| Layer | Azure service | Purpose |
|---|---|---|
| Models / AI | Azure OpenAI / Azure AI Foundry model deployments | The LLMs behind every agent step |
| Models / AI | Azure AI Content Safety | Unsafe-content and policy checks (guardrails) |
| Models / AI | Azure AI Document Intelligence (if needed) | Parse résumés / documents into structured text |
| Knowledge / RAG | Azure AI Search | Hiring RAG index (job descriptions, rubric, policy); optional transcript search for APIX |
| Data / state | Azure Cosmos DB | Agent state and intermediate pipeline results |
| Data / state | Azure SQL Database | APIX scores and KPIs the dashboard reads |
| Data / state | Azure Blob Storage | Transcripts, résumés, golden datasets |
| Data / state | Microsoft Fabric / OneLake | Telemetry lake, analytics, training-data curation (later) |
| Gateway / compute | Azure API Management | Gateway in front of models and services: quotas, metering, keys |
| Gateway / compute | Azure Container Apps + Azure Functions | Pipeline services + event triggers |
| Observability | Azure Monitor + Application Insights + Log Analytics | System-of-record telemetry, traces stay in tenant |
| Observability | Self-hosted Langfuse (Container Apps + Azure Database for PostgreSQL) | LLM-specific lens: cost per model, prompt versions, per-trace scores, datasets |
| Observability | Power BI / Azure Managed Grafana | Operational and quality dashboards |
| Web app (APIX dashboard) | Azure App Service or Static Web Apps + API | Serves the APIX performance-intelligence dashboard to managers and coaches |
| Security / identity | Entra ID, Key Vault, Private Endpoints / VNet, Microsoft Purview, Defender for Cloud | Identity, secrets, network isolation, data governance, security posture |
| CI/CD | GitHub + GitHub Actions + OIDC federation to Azure | Build, evaluate, deploy — no stored cloud keys |

Grouping keeps the bill readable: models and knowledge produce the answers; data
and state hold inputs and results; gateway and compute run the code;
observability watches it; the web app surfaces APIX; security and CI/CD wrap
everything.

## Environments

We run **dev, test, and prod** as separate subscriptions/resource groups under an
Azure **landing zone** (the standard enterprise-scale baseline: management group
hierarchy, policy, networking, identity). Each environment is identical in shape,
sized differently, and fully isolated — prod data never touches dev. Promotion
between them goes through the CI/CD gate, including the evaluation gate, so nothing
reaches prod without passing golden-dataset checks. OIDC (OpenID Connect)
federation lets GitHub Actions deploy into each environment without any stored
secrets.

## Infrastructure diagram

```
                         Entra ID  |  Key Vault  |  Private Endpoints / VNet
                         ------------------------------------------------------
 Triggers                     Gateway                 Pipeline compute
 --------                     -------                 ----------------
 new call ---> [Azure      [Azure API      ------> [Azure Container Apps]
 recording]    Functions]  Management] ---.          agent 1 -> agent 2 -> ... -> agent N
 new                                      |            |            |
 candidate --> [Azure                     |            v            v
               Functions]                 |     [Azure OpenAI /  [Azure AI Search]
                                          |      Foundry models]  (Hiring RAG)
                                          |            |
                                          |            v
                                          |     [Content Safety]  (guardrails)
                                          |
              Data / state                v            Observability
              ------------          ------------       -------------
              [Blob Storage]        [Cosmos DB]        every span -> OpenTelemetry
              transcripts,          agent state             |
              resumes, evals        [Azure SQL]             +--> [App Insights + Log Analytics]
                                     APIX scores             |         (system of record)
                                          |                  +--> [Langfuse + PostgreSQL]
                                          v                  |         (LLM lens, scores)
                                  [APIX dashboard]           +--> [Power BI / Grafana]
                                  App Service / SWA                    (dashboards)

              [Microsoft Fabric / OneLake]  <-- telemetry lake + analytics (later)

 CI/CD:  GitHub -> GitHub Actions -(OIDC)-> dev -> test -> prod   (eval gate between stages)
```

## Shared platform vs per-use-case

Most of the stack is a **shared platform** built once and used by both pipelines,
and by any future use case: API Management, observability (App Insights, Log
Analytics, Langfuse), Entra ID and Key Vault, the model deployments, the CI/CD
pipeline, and the landing zone with its three environments. Standing this up once
is the whole point — the operational layer is common.

**Per-use-case** pieces are the parts that reflect what each pipeline actually
does: the agent containers and their prompts; the Hiring RAG index in Azure AI
Search and its ingestion; the APIX SQL score store and the dashboard web app; and
the golden datasets, which are kept per use case and per program (APIX Telesales
and WCC — the contact-center program — differ). A new use case reuses the shared
platform and adds only its own agents, data, and datasets.

## Sequencing (what to stand up first — no dates)

Stand up the **landing zone, identity (Entra ID), and Key Vault** first — nothing
else is safe without them. Then the **shared platform**: model deployments behind
API Management, and observability (App Insights + Langfuse) so every later step is
traced from day one. Next the **compute plane**: Container Apps and Functions,
wired to the CI/CD pipeline with the evaluation gate. Then layer in the
**per-use-case** pieces — Hiring's AI Search index and APIX's SQL store and
dashboard — and finally the **later additions** such as Fabric/OneLake for the
telemetry lake and Foundry Agent Service for hosted agents. This is an ordering,
not a schedule — **no dates**.
