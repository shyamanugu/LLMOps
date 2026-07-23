# Reusable Framework & Use-Case Onboarding

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §4, §6). Any financial or ROI figures below are **ILLUSTRATIVE** pending AFNI actuals.

## 1. The core idea: build the factory, not the feature

AFNI is not standing up three AI apps; it is standing up an **enterprise, reusable GenAI framework** — an internal platform-as-a-product with a paved road that lets *any* future use case be onboarded quickly, safely, and cost-effectively. The three initiatives (Voice Agent, Performance Intelligence Index, Hiring Intelligence) are the **first three proof points** that ride that road. The payoff compounds: the 4th, 10th, and 40th use case reuse the same building blocks, and each new one is cheaper and faster than the last.

## 2. Framework layers (what every use case inherits)

The platform is organized as nine reusable layers. A use case composes from them; it never rebuilds them.

```
 ┌───────────────────────────────────────────────────────────────┐
 │ 1  Experience & channels  voice/CCaaS · web/chat · Teams/M365  │
 │                           agent-assist · ATS/HR · batch/API    │
 ├───────────────────────────────────────────────────────────────┤
 │ 2  Orchestration & agents Agent Framework + Foundry Agent Svc  │
 │                           orchestrator + specialists · MCP·A2A │
 ├───────────────────────────────────────────────────────────────┤
 │ 3  Models & AI services   model catalog + Model Router · GPT-5.x│
 ├───────────────────────────────────────────────────────────────┤
 │ 4  Knowledge & RAG        AI Search · Doc Intelligence · citations│
 ├───────────────────────────────────────────────────────────────┤
 │ 5  Data platform          Fabric/OneLake · streaming+batch·vector│
 ├───────────────────────────────────────────────────────────────┤
 │ 6  Tools & integration    MCP servers · APIM gateway · Functions │
 ├───────────────────────────────────────────────────────────────┤
 │ 7  GenAIOps / DevOps      agents-as-code · eval-in-CI · CI/CD   │
 ├───────────────────────────────────────────────────────────────┤
 │ 8  Security & governance  Zero Trust · Purview · Defender for AI│
 ├───────────────────────────────────────────────────────────────┤
 │ 9  Observability & FinOps OpenTelemetry tracing · showback     │
 └───────────────────────────────────────────────────────────────┘
```

Layers 6–9 are the "inherited by default" layers: any use case that follows the paved road receives security, evaluation, and observability without writing new plumbing.

## 3. The paved-road golden path

Onboarding follows one repeatable, self-service path. Each step has an owner, an artifact, and a gate.

| Step | What happens | Key artifact | Gate |
|---|---|---|---|
| **1. Intake** | Sponsor submits use case via portal: problem, users, data, outcome KPIs | Intake record | Complete + sponsored |
| **2. Tier** | Score value and risk; assign risk tier, autonomy ceiling, compliance profile | Value/risk tier | Governance sign-off |
| **3. Blueprint** | Select pattern(s) from the catalog (see doc 18) | Selected blueprint | Pattern fit confirmed |
| **4. Assemble** | Compose from building blocks: agent YAML, MCP tools, prompts, guardrails, IaC | Declarative config in Git | Builds + policy-as-code passes |
| **5. Evaluate** | Run golden-dataset, groundedness, safety/red-team, cost/latency evals | Eval report | All gates green in CI |
| **6. Deploy** | Canary / blue-green behind APIM with guardrail monitors | Release + rollback plan | Canary healthy |
| **7. Operate** | Observe quality, drift, safety, latency, and cost; FinOps showback | Live dashboards | SLOs + budget held |
| **8. Improve** | Feed thumbs/QA/incident signals into golden datasets; iterate | Refreshed datasets | Regression-free promotion |

The loop is continuous: **Improve** feeds back into **Evaluate**, so the platform gets better as it runs.

## 4. Reusable building-block catalog

The catalog is the source of composition. Everything is versioned and registered.

- **Agent & workflow templates** — declarative YAML (instructions, tools, memory, topology) for orchestrator + specialist agents.
- **MCP tool/connector library** — CRM, HRIS, billing, systems-of-record wrapped as least-privilege MCP servers.
- **Prompt & policy libraries** — reviewed, versioned prompts and business-policy snippets.
- **Guardrail packs** — Content Safety prompt shields, PII redaction, output validators, groundedness checks.
- **Golden datasets + eval suites** — task-specific quality bars curated from production.
- **IaC modules** — landing zone, networking, identity, gateway, monitoring.
- **RAG ingestion templates** — chunking, integrated vectorization, per-tenant partitioning.
- **Dashboards** — quality/latency/drift/safety/cost, prewired to OpenTelemetry.

## 5. Value & risk intake tiering

Tiering at intake sets the autonomy ceiling, the eval rigor, the guardrails, and the review path. It is the single most important governance decision.

| Tier | Value signal | Risk signal (data + action) | Autonomy ceiling | Eval / guardrail rigor | Review path |
|---|---|---|---|---|---|
| **T1 — Low** | Internal productivity, bounded scope | Non-PII, read-only, reversible | Assist only (human acts) | Standard eval suite | Platform team |
| **T2 — Moderate** | Service-line efficiency | Limited PII, suggests actions | Suggest + human approve | + groundedness + PII redaction | Platform + spoke lead |
| **T3 — High** | Customer-facing / revenue | Regulated data, external comms (TCPA) | Act on low-risk, approve high-risk | + red-team + online monitors | Governance board |
| **T4 — Critical** | Consequential / irreversible | Financial, legal, or employment decisions (EEOC/LL144) | Human-in-the-loop mandatory | Full suite + continuous red-team + audit | RAI officer + exec sponsor |

## 6. Self-service and weeks-to-pilot

Because layers 6–9 are inherited and steps 3–4 compose from the catalog, a new use case reaches **pilot in weeks, not quarters**. Self-service means a spoke team can start intake, select a blueprint, and assemble a working prototype without waiting on the platform team for bespoke infrastructure — the platform team's job is to curate the road, not to hand-build each project. Security, compliance, evaluation, and observability arrive by default, so "fast" and "safe" are no longer in tension.

## 7. The three initiatives as first proof points

| Initiative | Blueprint(s) used | What it proves |
|---|---|---|
| **Voice Agent** | Real-time voice + conversational copilot + agentic workflow | The road handles low-latency, customer-facing, regulated voice with graduated autonomy |
| **Performance Intelligence Index (PI Index)** | Batch summarization & analytics + structured extraction | The road scales to 100% interaction analysis with cost-controlled, right-sized models |
| **Hiring Intelligence** | Agentic workflow + RAG + document intelligence | The road handles document-heavy, compliance-sensitive (EEOC/LL144) decision support with human-in-the-loop |

Together they exercise voice, batch analytics, and agentic document workflows — proving the paved road across the pattern space so the 4th use case is an onboarding, not a project.

## 8. Governance of the road itself

The paved road is owned, versioned, and improved like any product. The CoE curates blocks, deprecates stale ones, and publishes the roadmap; architecture exceptions are logged and revisited so that today's exception becomes tomorrow's paved feature. This keeps the framework current with the frontier (new models via the router, new patterns via the catalog) without fragmenting into one-off stacks.
