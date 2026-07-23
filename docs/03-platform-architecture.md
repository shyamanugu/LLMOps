# Platform Architecture

## Purpose and Design Principles

This document defines the reference architecture for AFNI's enterprise LLMOps platform, built on **Microsoft Azure AI Foundry**. The architecture is owned by the **AFNI Office of GenAI Architecture** and is designed to support AFNI's three flagship initiatives — the **Voice Agent** (real-time voice automation and agent-assist), the **Performance Intelligence Index (PI Index)** (explainable scoring of 100% of interactions), and **Hiring Intelligence** (fair, high-volume recruitment) — while remaining extensible to future service lines (Acquisition & Growth, Care & Retention, Collections, and P&C Insurance including subrogation).

The design follows five principles:

- **One governed platform, three products.** A shared, multi-tenant-capable foundation with per-initiative isolation, rather than point solutions. The Voice Agent generates interaction data and real-time automation; the PI Index turns 100% of that data into performance intelligence; Hiring Intelligence reuses the same agents and voice stack to hire the workforce.
- **Deterministic controls around probabilistic components.** Guardrails, gateways, and policy layers wrap non-deterministic model calls.
- **Security and governance by default.** Private networking, managed identity, and least-privilege access are baseline, not add-ons.
- **Everything as code.** Infrastructure, prompts, agents, and evaluations are versioned and promoted through CI/CD.
- **Cloud-portable where practical.** Azure is primary; interfaces (gateway, RAG, telephony) are abstracted so alternatives remain viable.

## Layered Reference Architecture

The platform is organized into nine logical layers. Each layer has a clear responsibility, a defined Azure service mapping, and controlled interfaces to adjacent layers.

```
+===========================================================================+
|  9. SECURITY & GOVERNANCE (cross-cutting)                                 |
|     Entra ID · Key Vault · Defender for Cloud · Purview · Content Safety  |
+===========================================================================+
|  8. OBSERVABILITY (cross-cutting)                                         |
|     Azure Monitor · App Insights · OpenTelemetry (GenAI conventions)      |
+---------------------------------------------------------------------------+
|  1. CHANNELS / EXPERIENCE                                                 |
|     Voice (CCaaS/SIP, Azure Communication Services) · Web/Chat · Teams    |
|     · Candidate portal · Agent-assist desktop · Coaching/PI dashboards    |
+---------------------------------------------------------------------------+
|  2. ORCHESTRATION / AGENTS                                                |
|     Azure AI Agent Service · Semantic Kernel / AutoGen                    |
|     (Microsoft Agent Framework) · Orchestrator + specialist agents        |
+---------------------------------------------------------------------------+
|  3. MODEL SERVING & GATEWAY                                               |
|     Azure API Management (token metering, quotas, caching, routing)       |
+---------------------------------------------------------------------------+
|  4. MODELS & AI SERVICES                                                  |
|     Azure OpenAI (GPT-4o / GPT-4o-mini / gpt-realtime) · Azure AI Speech  |
|     · embeddings (text-embedding-3-large) · open-weight (Llama, Phi)      |
+---------------------------------------------------------------------------+
|  5. KNOWLEDGE / RAG                                                       |
|     Azure AI Search (hybrid + semantic ranker) · Document Intelligence    |
+---------------------------------------------------------------------------+
|  6. DATA & STATE                                                          |
|     Cosmos DB (agent state/memory) · Fabric / Data Lake (PI Index store)  |
|     · Azure SQL                                                           |
+---------------------------------------------------------------------------+
|  7. INTEGRATION                                                           |
|     Azure Functions · Logic Apps · APIM · connectors to CRM/HRIS/ATS/CCaaS|
+---------------------------------------------------------------------------+
|  8'. PLATFORM / DEVOPS / LLMOPS                                           |
|     Azure DevOps / GitHub Actions · Bicep/Terraform · Container Apps/AKS  |
+===========================================================================+
```

### 1. Channels / Experience
Entry points for callers, candidates, agents, and AFNI operations leaders. Voice traffic arrives from the existing CCaaS estate (Genesys, NICE, Five9, Amazon Connect) via SIP/APIs; **Azure Communication Services** provides greenfield voice where no incumbent exists. Web chat, the candidate portal, the agent-assist desktop, and the PI Index coaching/analytics dashboards all connect through the same orchestration APIs.

### 2. Orchestration / Agents
The heart of the platform. **Azure AI Agent Service** hosts agents with built-in tool calling, threads, and content safety. **Semantic Kernel** and **AutoGen** (converging into the **Microsoft Agent Framework**) provide the orchestrator/specialist logic. The identical pattern serves all three initiatives; detail is in `04-multi-agent-systems.md`.

### 3. Model Serving & Gateway
All model traffic passes through **Azure API Management (APIM)** acting as an AI gateway:

| Capability | Function |
|---|---|
| Token metering | Per-initiative token accounting for FinOps showback (Voice Agent, PI Index, Hiring) |
| Quotas & rate limits | Protect capacity; enforce PTU/PAYG budgets per consumer |
| Semantic caching | Cache high-frequency prompts/responses to cut latency and cost |
| Load balancing / routing | Spread load across Azure OpenAI deployments and regions |
| Central policy | Inject auth, logging, and Content Safety pre-checks uniformly |

This gateway decouples agents from concrete model deployments, enabling model upgrades and multi-region failover without agent changes.

### 4. Models & AI Services
**Azure OpenAI** serves GPT-4o (reasoning/orchestration and PI Index scoring), GPT-4o-mini (cost-efficient routing/classification and high-volume screening), and **gpt-realtime** for sub-second speech-to-speech in Voice Agent scenarios. **Azure AI Speech** (STT/TTS, custom neural voice) provides a hybrid/fallback path. **text-embedding-3-large** powers retrieval. Open-weight models (Llama, Phi) from the Foundry catalog are available for cost-sensitive or data-residency-constrained workloads.

### 5. Knowledge / RAG
**Azure AI Search** provides hybrid (keyword + vector) retrieval with the semantic ranker over AFNI policy documents, client knowledge bases, and job requisitions. **Azure AI Document Intelligence** handles ingestion and extraction from PDFs, contracts, and resumes. Vectors reside in AI Search or Cosmos DB depending on latency and co-location needs.

### 6. Data & State
**Cosmos DB** stores agent state and conversation memory (low-latency, globally distributed). **Microsoft Fabric / Azure Data Lake** holds analytics, evaluation datasets, interaction transcripts, and the **PI Index score store** (dimension scores, trends, driver breakdowns). **Azure SQL** serves relational needs (dispositions, structured HR records).

### 7. Integration
**Azure Functions** provide event glue; **Logic Apps** and APIM-fronted connectors reach systems of record — CRM, billing, HRIS/ATS, and QA/coaching platforms — through secure, audited tool endpoints. The integration layer is deliberately generic to avoid coupling to a specific CCaaS or ATS incumbent.

### 8. Platform / DevOps / LLMOps
Infrastructure is defined as code (Bicep/Terraform) and deployed via **Azure DevOps or GitHub Actions**. Runtime hosting uses **Azure Container Apps** for most agent workloads, with **AKS** reserved for high-scale or specialized needs. See `07-llmops-lifecycle.md` for the full pipeline.

### 9. Security & Governance (cross-cutting)
**Microsoft Entra ID** for workforce and workload identity (managed identities, no secrets in code); **Azure Key Vault** for secrets and keys; **Microsoft Defender for Cloud** for posture management; **Microsoft Purview** for data lineage, classification, and DLP; **Azure AI Content Safety** for prompt shields, groundedness detection, protected-material, and PII controls.

## Environments and Landing Zone

The platform is deployed into an **Azure landing zone** aligned to the Cloud Adoption Framework, with a dedicated management group hierarchy for AI workloads and policy guardrails (Azure Policy) enforcing tagging, region, and SKU constraints.

Three promotion environments are maintained, each an isolated Foundry hub/project with its own network, identities, and quotas:

| Environment | Purpose | Data |
|---|---|---|
| **Dev** | Prompt/agent engineering, experimentation | Synthetic / masked |
| **Test** | Automated evaluation, integration, UAT, red-teaming | Masked + curated golden sets |
| **Prod** | Live traffic, canary/blue-green rollouts | Live, fully governed |

## Network Isolation

All PaaS services (Azure OpenAI, AI Search, Cosmos DB, Key Vault, Storage) are deployed with **Private Endpoints** into a hub-and-spoke **VNet**; public network access is disabled. Traffic between agents, gateway, and models stays on the Microsoft backbone. Ingress is fronted by **Azure Front Door / Application Gateway with WAF**; egress is controlled via **Azure Firewall**. Private DNS zones resolve private endpoints. This satisfies PCI-DSS, HIPAA, and GDPR isolation expectations for regulated AFNI client workloads.

## Cloud Alternatives

Azure is recommended as primary given Microsoft's enterprise footprint, integrated agent + safety + governance stack, and regulated-workload maturity. For completeness: **AWS Bedrock Agents** (Bedrock models, Knowledge Bases, Guardrails) and **Google Vertex AI Agent Builder** offer comparable capabilities. The gateway, RAG, and telephony abstractions in this architecture preserve the option to adopt these providers for specific workloads without re-platforming.
