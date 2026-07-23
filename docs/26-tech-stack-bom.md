# Reference Tech Stack (Bill of Materials)

> Internal AFNI reference. Owner: **AFNI · Office of GenAI Architecture** · Internal & confidential.
> Source of truth: `reference/proposal-bible.md` §3, §4. Product names are the current (2026) Microsoft/Azure names.

This document is the canonical **Bill of Materials (BOM)** for the AFNI GenAI framework: each platform capability/layer mapped to the specific Microsoft/Azure product that implements it, with purpose and notes. It exists so every use case onboarded via the paved road assembles from the *same* approved, governed building blocks — no bespoke stacks. The architectural principle is **pin to capabilities, not versions**: the Model Router and eval harness let AFNI adopt each new frontier model without rewrites.

## 1. Capability → product map

| Layer / Capability | Product | Purpose | Notes |
|--------------------|---------|---------|-------|
| **AI platform** | **Microsoft Foundry** (formerly Azure AI Foundry) | Unified build/eval/deploy/govern surface for agents & models | Model catalog, tracing, evaluation, Content Safety, fine-tune/distill |
| **Agent runtime** | **Foundry Agent Service** | Hosted, durable agents (sandboxed sessions, state, filesystem) | Publish to Teams / M365 Copilot; **Voice Live** real-time path; memory + toolboxes |
| **Orchestration** | **Microsoft Agent Framework 1.0** | Multi-agent orchestration (sequential/concurrent/group-chat/handoff/Magentic) | GA April 2026; AutoGen + Semantic Kernel convergence; Python & .NET; declarative YAML |
| **Model selection** | **Model Router** | Route each request to cheapest model meeting a measured quality bar | Prompt caching; cost-latency-quality optimization |
| **Frontier models** | **Azure OpenAI GPT-5.x** (5.5 / 5.4 / 5.2 / 5) | Deep long-context reasoning, agentic execution | Pin to capability via router + evals, not a fixed version |
| **Realtime voice** | **gpt-realtime-1.5 / gpt-audio-1.5** | Speech-to-speech, multilingual, tool calling | Sub-second voice turns; agent-assist |
| **Retrieval / RAG** | **Azure AI Search** | Hybrid + semantic ranking, integrated vectorization | Per-domain/tenant partitioned vector indexes |
| **Document AI** | **AI Document Intelligence** | Extraction/classification of forms, claims, contracts | Feeds RAG + document-intelligence pattern |
| **Safety** | **Azure AI Content Safety** | Prompt shields, groundedness, PII, protected material | Input + output guardrails |
| **Data platform** | **Microsoft Fabric / OneLake** | Lakehouse: batch + knowledge pipelines | Feature/knowledge stores; Purview lineage |
| **Agent state / vector** | **Azure Cosmos DB** | Agent state, memory, vector store | Low-latency; partitioned per tenant |
| **Streaming** | **Azure Event Hubs / Stream Analytics** | Real-time ingestion & event processing | PI Index streaming analytics |
| **AI gateway** | **Azure API Management** | Token metering, quotas, caching, routing, throttling | Enforcement point for canary/blue-green + rate limits |
| **Compute** | **Azure Container Apps / AKS** | Host orchestrators, MCP servers, custom services | Autoscaling; provisioned throughput for critical paths |
| **Event compute** | **Azure Functions** | Lightweight tools, connectors, event handlers | Serverless glue |
| **Identity** | **Microsoft Entra ID** | Authn/z, managed identities, least privilege | No standing secrets |
| **Secrets** | **Azure Key Vault** | Keys, secrets, certs | Referenced, never inlined in prompts |
| **Governance** | **Microsoft Purview** | Lineage, DLP, classification, data-security posture for AI | PII handling, retention, audit |
| **Security** | **Defender for Cloud + Defender for AI** | Posture + runtime threat protection for AI workloads | Jailbreak/anomaly detection; IR integration |
| **Observability** | **Azure Monitor / App Insights / OpenTelemetry** | Unified tracing of every model call, tool, sub-agent hop | Evals link back to exact trace; FinOps/showback |
| **CI/CD** | **GitHub Actions / Azure DevOps** | Everything-as-code pipelines + eval gates | Blocking evaluation gates |
| **Voice channel** | **Azure Communication Services (ACS)** | Voice/telephony + CCaaS integration | With Genesys/NICE/Five9 |
| **Tool protocol** | **MCP (Model Context Protocol)** | Agent→tools standard | Wrap CRM/HRIS/billing systems-of-record |
| **Agent protocol** | **A2A (Agent-to-Agent v1.0)** | Agent→agent across runtimes | Linux Foundation; Foundry exposes agents as A2A endpoints |

## 2. Framework layer → BOM rollup

```
 Experience  → ACS + Voice Live, Teams/M365 Copilot, web/chat, APIM
 Orchestration → Agent Framework 1.0 + Foundry Agent Service (MCP tools, A2A interop)
 Models      → Model Router + Azure OpenAI GPT-5.x + gpt-realtime-1.5 + Content Safety
 Knowledge   → AI Search (hybrid+semantic) + Document Intelligence + integrated vectorization
 Data        → Fabric/OneLake + Event Hubs + Cosmos DB vectors + Purview lineage
 Tools/Integ → MCP servers + Functions + APIM gateway
 GenAIOps    → GitHub Actions/Azure DevOps + prompt/model registry + eval-in-CI + IaC
 Security    → Entra ID + Key Vault + private networking + Purview + Defender for AI
 Observability → OpenTelemetry + Azure Monitor/App Insights + FinOps showback
```

## 3. Open-source & open-standard components

The framework is open where openness reduces lock-in and increases interoperability:

- **Microsoft Agent Framework** — open-source orchestration (Python & .NET); declarative YAML agents/workflows are portable, version-controlled artifacts.
- **MCP (Model Context Protocol)** — open, de-facto standard for agent→tool connectivity; AFNI's MCP tool/connector library is reusable across use cases.
- **A2A (Agent-to-Agent v1.0)** — open, Linux Foundation-governed protocol for cross-runtime, cross-team agent collaboration.
- **OpenTelemetry** — open observability standard underpinning unified tracing, so telemetry is not locked to a single backend.

## 4. Alternatives considered

| Platform | Assessment | Why not primary |
|----------|-----------|-----------------|
| **AWS Bedrock + AgentCore** | Capable managed agent runtime and strong model breadth | AFNI is a Microsoft-centric enterprise (Entra ID, M365, Fabric, Purview); Foundry's unified tracing + evaluation and native Teams/Copilot publishing give lower integration cost and one governance plane |
| **Google Vertex AI Agent Builder** | Strong models and grounding | Same integration-cost argument; weaker fit with AFNI's existing Microsoft identity, data governance (Purview), and security (Defender) estate |

**Decision: Microsoft Foundry is the primary platform.** The deciding factors are (1) native alignment with AFNI's existing Entra ID / M365 / Fabric / Purview / Defender estate — one identity, governance, and security plane; (2) **unified OpenTelemetry tracing + evaluation** with evals linked to exact traces; (3) the **Model Router + capability-pinning** strategy that decouples AFNI from any single model or even provider; and (4) open standards (Agent Framework, MCP, A2A, OpenTelemetry) that preserve portability. The open-standard core means a future multi-cloud or model-provider shift is a configuration and integration effort, not a rewrite — consistent with the framework's model-agnostic, frontier-ready design principle.
