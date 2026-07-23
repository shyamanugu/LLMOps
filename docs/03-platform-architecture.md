# Platform Architecture

## Purpose and Design Principles

This document defines the reference architecture for AFNI's enterprise GenAI **framework**, built on **Microsoft Foundry** (formerly Azure AI Foundry / Azure AI Studio). The architecture is owned by the **AFNI Office of GenAI Architecture** and is internal and confidential to AFNI.

The platform is deliberately framed as a **reusable, enterprise GenAI framework** — a platform-as-a-product that lets AFNI onboard *any* future GenAI use case quickly, safely, and cost-effectively, and continuously ride the frontier of models. It is **not** three bespoke applications. The three flagship initiatives are the **first three proof-point use cases** onboarded via the framework's paved road:

- **Voice Agent** — real-time voice automation and agent-assist.
- **Performance Intelligence Index (PI Index)** — explainable scoring of 100% of interactions.
- **Hiring Intelligence** — fair, high-volume recruitment.

Any use case (subrogation triage, knowledge assistant, next-best-offer, document intelligence) builds on the *same* layers, gateway, guardrails, observability, and GenAIOps described here — inheriting security, compliance, and observability by default. The onboarding golden path is detailed in `17-reusable-framework-onboarding.md`.

The design follows five principles (the full set is in `16-design-principles.md`):

- **Platform as a product; build the factory, not the feature.** A shared, multi-tenant-capable foundation with per-use-case isolation. The 4th, 10th, and 40th use case reuse the same paved road; time-to-value drops from quarters to weeks.
- **Model-agnostic and frontier-ready.** Pin to capabilities via the **Model Router** and evaluations, not to a single model version, so AFNI adopts each new frontier model without rewrites.
- **Deterministic controls around probabilistic components.** Guardrails, gateways, and policy layers wrap non-deterministic model calls.
- **Security and governance by default.** Private networking, managed identity, least-privilege access, and Responsible AI are baseline, not add-ons.
- **Everything as code.** Infrastructure, prompts, agents, and evaluations are versioned and promoted through CI/CD.

## Layered Reference Architecture

The reusable platform is organized into nine logical layers. Each layer has a clear responsibility, a defined Azure/Foundry service mapping, and controlled interfaces to adjacent layers. Every onboarded use case composes its solution from these layers rather than standing up its own stack.

```
+===========================================================================+
|  9. SECURITY & GOVERNANCE (cross-cutting)                                 |
|     Entra ID · Key Vault · Defender for Cloud + Defender for AI ·         |
|     Purview · Content Safety (prompt shields, groundedness, PII)          |
+===========================================================================+
|  8. OBSERVABILITY & FinOps (cross-cutting)                                |
|     Unified OpenTelemetry tracing (model/tool/sub-agent/handoff)          |
|     · Foundry evaluations (rubric evaluators) · Azure Monitor · showback  |
+---------------------------------------------------------------------------+
|  1. EXPERIENCE / CHANNELS                                                 |
|     Voice (CCaaS/SIP, Azure Communication Services, Voice Live) · Web/    |
|     Chat · Teams / M365 Copilot · Candidate portal · Agent-assist desktop |
+---------------------------------------------------------------------------+
|  2. ORCHESTRATION / AGENTS                                                |
|     Microsoft Agent Framework 1.0 · Foundry Agent Service (durable,       |
|     hosted) · orchestrator + specialists · memory · MCP tools · A2A       |
+---------------------------------------------------------------------------+
|  3. MODEL SERVING & AI GATEWAY                                            |
|     Azure API Management (token metering, quotas, caching, routing)       |
|     + Model Router (quality-aware, cheapest-model routing, prompt cache)  |
+---------------------------------------------------------------------------+
|  4. MODELS & AI SERVICES                                                  |
|     Model catalog · GPT-5.5 / 5.4 / 5.2 / 5 · GPT-5.5 Instant ·           |
|     gpt-realtime-1.5 / gpt-audio-1.5 · embeddings · open-weight (Llama,   |
|     Phi) · Content Safety · fine-tune / distill                           |
+---------------------------------------------------------------------------+
|  5. KNOWLEDGE / RAG                                                       |
|     Azure AI Search (hybrid + semantic ranker, integrated vectorization)  |
|     · Document Intelligence · grounding & citations                       |
+---------------------------------------------------------------------------+
|  6. DATA PLATFORM (at scale)                                             |
|     Microsoft Fabric / OneLake lakehouse · Cosmos DB (agent state/memory, |
|     vector) · Azure SQL · Event Hubs / Stream Analytics (streaming)       |
+---------------------------------------------------------------------------+
|  7. TOOLS & INTEGRATION                                                   |
|     MCP servers wrapping CRM/HRIS/ATS/billing/systems-of-record ·         |
|     APIM gateway · Azure Functions · connectors to CCaaS                  |
+---------------------------------------------------------------------------+
|  8'. GenAIOps / DevOps                                                    |
|     Declarative agents-as-code (YAML) · prompt/model registry ·           |
|     evaluation-in-CI · GitHub Actions / Azure DevOps · IaC · Container    |
|     Apps / AKS                                                            |
+===========================================================================+
```

### 1. Experience / Channels
Entry points for callers, candidates, agents, and AFNI operations leaders. Voice traffic arrives from the existing CCaaS estate (Genesys, NICE, Five9, Amazon Connect) via SIP/APIs; **Azure Communication Services** and Foundry **Voice Live** provide the real-time speech path and greenfield voice where no incumbent exists. Agents can be published directly to **Microsoft Teams / M365 Copilot**. Web chat, the candidate portal, the agent-assist desktop, PI Index dashboards, and batch/API consumers all connect through the same orchestration APIs. New use cases attach to this layer without new plumbing.

### 2. Orchestration / Agents
The heart of the platform. **Foundry Agent Service** hosts **durable** agents — sandboxed sessions with state, filesystem, and framework flexibility, plus procedural / user / session **memory** and curated **Toolboxes**. **Microsoft Agent Framework 1.0** (the GA convergence of **Semantic Kernel** + **AutoGen**, Python and .NET) provides orchestrator/specialist logic and orchestration patterns (sequential, concurrent, group-chat, handoff, **Magentic**), **durable workflows with checkpoint/pause/resume** and human-in-the-loop approvals, and declarative agents-as-code. Agents call tools over **MCP (Model Context Protocol)** and collaborate across runtimes over **A2A (Agent-to-Agent)**; Foundry can expose any agent as an A2A endpoint. An **agent registry** versions every agent. The identical pattern serves every use case; depth is in `04-multi-agent-systems.md` and `19-enterprise-agent-orchestration.md`.

### 3. Model Serving & AI Gateway
All model traffic passes through **Azure API Management (APIM)** acting as an AI gateway, working alongside the **Model Router**:

| Capability | Function |
|---|---|
| Token metering | Per-use-case token accounting for FinOps showback |
| Quotas & rate limits | Protect capacity; enforce PTU/PAYG budgets per consumer; curb unbounded consumption |
| Semantic / prompt caching | Cache high-frequency prompts/responses to cut latency and cost |
| Model Router | Route each request to the *cheapest model that meets a measured quality bar*; prompt caching |
| Load balancing / routing | Spread load across model deployments and regions; version routing for canary/rollback |
| Central policy | Inject auth, logging, and Content Safety pre-checks uniformly |

This gateway decouples agents from concrete model deployments, enabling model upgrades and multi-region failover without agent changes — the mechanism behind the framework's frontier-readiness. Model strategy is expanded in `24-model-strategy.md`.

### 4. Models & AI Services
The Foundry **model catalog** serves frontier and open-weight models. Current (2026) defaults: **GPT-5.5** (frontier deep long-context reasoning, reliable agentic execution, improved computer-use, token efficiency); **GPT-5.4 / GPT-5.2 / GPT-5** (272k-context reasoning); **GPT-5.5 Instant** (`gpt-chat-latest`, low-latency); **gpt-realtime-1.5** and **gpt-audio-1.5** for speech-to-speech, multilingual, tool-calling voice; reasoning "o-series" (o3-mini, o1) in catalog; **text-embedding-3-large** for retrieval; open-weight (Llama, Phi) for cost/edge tiers. Selection is delegated to the Model Router plus evaluations — **capabilities, not versions**. Content Safety, fine-tuning, and distillation are available in-catalog.

### 5. Knowledge / RAG
**Azure AI Search** provides hybrid (keyword + vector) retrieval with the semantic ranker and **integrated vectorization** over AFNI policy documents, client knowledge bases, and job requisitions. **Azure AI Document Intelligence** handles ingestion and extraction from PDFs, contracts, and resumes. Every answer is grounded with citations. Vectors reside in AI Search or Cosmos DB depending on latency and co-location needs. The RAG blueprint is one of the reusable patterns in `18-genai-pattern-catalog.md`.

### 6. Data Platform (at scale)
**Microsoft Fabric / OneLake** is the lakehouse for analytics, evaluation datasets, interaction transcripts, and the **PI Index score store** (dimension scores, trends, driver breakdowns). **Cosmos DB** stores agent state and conversation memory (low-latency, globally distributed) and vector indexes. **Azure SQL** serves relational needs. Streaming is handled by **Event Hubs / Stream Analytics**; **Microsoft Purview** provides lineage, retention, classification, and DLP. Depth is in `21-data-platform-scale.md`.

### 7. Tools & Integration
Systems of record are reached through **MCP servers** wrapping CRM, billing, HRIS/ATS, and QA/coaching platforms — a curated, reusable tool/connector library. **Azure Functions** provide event glue; APIM fronts every tool endpoint with auth and audit. Least-privilege tool scopes are enforced per agent. The integration layer is deliberately generic to avoid coupling to a specific CCaaS or ATS incumbent, so a new use case reuses existing MCP servers rather than building bespoke integrations.

### 8. GenAIOps / DevOps
Declarative **agents and workflows are version-controlled YAML** (instructions, tools, memory, topology as code); prompts and model deployments are registered artifacts. PRs trigger **evaluation-in-CI** with gates; infrastructure is defined as code (Bicep/Terraform) and deployed via **GitHub Actions or Azure DevOps**. Runtime hosting uses **Azure Container Apps** for most agent workloads, with **AKS** for high-scale needs. See `07-llmops-lifecycle.md` and `23-genaiops-cicd.md`.

### 9. Security & Governance (cross-cutting)
**Microsoft Entra ID** for workforce and workload identity (managed identities, no secrets in code); **Azure Key Vault** for secrets and keys; **Microsoft Defender for Cloud + Defender for AI** for posture management and AI-specific threat protection; **Microsoft Purview** for data lineage, classification, DLP, and data-security posture for AI; **Azure AI Content Safety** for prompt shields, groundedness detection, protected-material, and PII controls. Design is mapped to the **OWASP Top 10 for LLM Applications (2025)** — see `20-security-deep-dive.md`.

### Observability & FinOps (cross-cutting)
A **single, unified OpenTelemetry pipeline** captures every model call, tool invocation, sub-agent hop, and handoff, with **GenAI semantic conventions**. **Foundry evaluations** — including **auto-generated rubric evaluators** that score agent quality against context-aware rubrics — link scores back to the exact trace. **Azure Monitor + Application Insights** surface quality, groundedness, latency, drift, safety, and cost; APIM token metering drives FinOps showback and budgets by use case. See `10-observability-finops.md` and `25-evaluation-framework.md`.

## Environments and Landing Zone

The platform is deployed into an **Azure landing zone** aligned to the Cloud Adoption Framework, with a dedicated management group hierarchy for AI workloads and policy guardrails (Azure Policy) enforcing tagging, region, and SKU constraints.

Three promotion environments are maintained, each an isolated Foundry hub/project with its own network, identities, and quotas:

| Environment | Purpose | Data |
|---|---|---|
| **Dev** | Prompt/agent engineering, experimentation | Synthetic / masked |
| **Test** | Automated evaluation, integration, UAT, red-teaming | Masked + curated golden sets |
| **Prod** | Live traffic, canary/blue-green rollouts | Live, fully governed |

## Network Isolation

All PaaS services (Foundry, Azure OpenAI, AI Search, Cosmos DB, Key Vault, Storage, Fabric endpoints) are deployed with **Private Endpoints** into a hub-and-spoke **VNet**; public network access is disabled. Traffic between agents, gateway, and models stays on the Microsoft backbone. Ingress is fronted by **Azure Front Door / Application Gateway with WAF**; egress is controlled via **Azure Firewall**. Private DNS zones resolve private endpoints. This satisfies PCI-DSS, HIPAA, and GDPR isolation expectations for regulated AFNI client workloads.

## Cloud Alternatives

Microsoft Foundry is recommended as primary given Microsoft's enterprise footprint, integrated agent + safety + governance stack, and regulated-workload maturity. For completeness: **AWS Bedrock Agents** (Bedrock models, Knowledge Bases, Guardrails) and **Google Vertex AI Agent Builder** offer comparable capabilities. The gateway, RAG, telephony, and **MCP/A2A** protocol abstractions in this architecture preserve the option to adopt these providers for specific workloads without re-platforming.
