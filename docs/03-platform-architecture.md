# Platform Architecture

## Purpose and Design Principles

This document defines the reference architecture for Afni's enterprise LLMOps platform, built on **Microsoft Azure AI Foundry**. The architecture is designed to support Afni's two flagship use cases — **Voice AI for contact centers** and **AI-driven HR recruitment** — while remaining extensible to future service lines (Acquisition & Growth, Care & Retention, Collections, P&C Insurance including subrogation).

The design follows five principles:

- **One governed platform, many use cases.** A shared, multi-tenant-capable foundation with per-use-case isolation, rather than point solutions.
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
|     · Candidate portal · Agent-assist desktop                             |
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
|     Cosmos DB (agent state/memory) · Data Lake / Fabric · Azure SQL       |
+---------------------------------------------------------------------------+
|  7. INTEGRATION                                                           |
|     Azure Functions · Logic Apps · APIM · connectors to CRM/HRIS/ATS/CCaaS|
+---------------------------------------------------------------------------+
|  8'. PLATFORM / DEVOPS                                                    |
|     Azure DevOps / GitHub Actions · Bicep/Terraform · Container Apps/AKS  |
+===========================================================================+
```

### 1. Channels / Experience
Entry points for callers, candidates, and Afni employees. Voice traffic arrives from the existing CCaaS estate (Genesys, NICE, Five9, Amazon Connect) via SIP/APIs; **Azure Communication Services** provides greenfield voice where no incumbent exists. Web chat, the candidate portal, and the agent-assist desktop connect through the same orchestration APIs.

### 2. Orchestration / Agents
The heart of the platform. **Azure AI Agent Service** hosts agents with built-in tool calling, threads, and content safety. **Semantic Kernel** and **AutoGen** (converging into the **Microsoft Agent Framework**) provide the orchestrator/specialist logic. This layer is detailed in `04-multi-agent-systems.md`.

### 3. Model Serving & Gateway
All model traffic passes through **Azure API Management (APIM)** acting as an AI gateway. APIM provides:

| Capability | Function |
|---|---|
| Token metering | Per-app/per-use-case token accounting for FinOps chargeback |
| Quotas & rate limits | Protect capacity; enforce PTU/PAYG budgets per consumer |
| Semantic caching | Cache high-frequency prompts/responses to cut latency and cost |
| Load balancing / routing | Spread load across Azure OpenAI deployments and regions |
| Central policy | Inject auth, logging, and Content Safety pre-checks uniformly |

This gateway decouples agents from concrete model deployments, enabling model upgrades and multi-region failover without agent changes.

### 4. Models & AI Services
**Azure OpenAI** serves GPT-4o (reasoning/orchestration), GPT-4o-mini (cost-efficient routing/classification), and **gpt-realtime** for sub-second speech-to-speech in voice scenarios. **Azure AI Speech** (STT/TTS, custom neural voice) provides a hybrid/fallback path. **text-embedding-3-large** powers retrieval. Open-weight models (Llama, Phi) from the Foundry catalog are available for cost-sensitive or data-residency-constrained workloads.

### 5. Knowledge / RAG
**Azure AI Search** provides hybrid (keyword + vector) retrieval with the semantic ranker over Afni policy documents, knowledge bases, and HR job requisitions. **Azure AI Document Intelligence** handles ingestion and extraction from PDFs, contracts, and resumes. Vectors reside in AI Search or Cosmos DB depending on latency and co-location needs.

### 6. Data & State
**Cosmos DB** stores agent state and conversation memory (low-latency, globally distributed). **Azure Data Lake / Microsoft Fabric** holds analytics, evaluation datasets, and interaction transcripts. **Azure SQL** serves relational needs (dispositions, structured HR records).

### 7. Integration
**Azure Functions** provide event glue; **Logic Apps** and APIM-fronted connectors reach systems of record — CRM, billing, and HRIS/ATS — through secure, audited tool endpoints. The integration layer is deliberately generic to avoid coupling to a specific CCaaS or ATS incumbent.

### 8. Platform / DevOps
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

All PaaS services (Azure OpenAI, AI Search, Cosmos DB, Key Vault, Storage) are deployed with **Private Endpoints** into a hub-and-spoke **VNet**; public network access is disabled. Traffic between agents, gateway, and models stays on the Microsoft backbone. Ingress is fronted by **Azure Front Door / Application Gateway with WAF**; egress is controlled via **Azure Firewall**. Private DNS zones resolve private endpoints. This satisfies PCI-DSS, HIPAA, and GDPR isolation expectations for regulated Afni client workloads.

## Cloud Alternatives

Azure is recommended as primary given Microsoft's enterprise footprint, integrated agent + safety + governance stack, and regulated-workload maturity. For completeness: **AWS Bedrock Agents** (Bedrock models, Knowledge Bases, Guardrails) and **Google Vertex AI Agent Builder** offer comparable capabilities. The gateway, RAG, and telephony abstractions in this architecture preserve the option to adopt these providers for specific workloads without re-platforming.
