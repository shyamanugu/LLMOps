# The Current Azure AI Stack (and Where Each Piece Fits)

## Why this doc exists

The Azure AI portfolio has a lot of moving parts, and product names keep changing (Azure AI Foundry became
Microsoft Foundry; Azure AI Studio folded into it). This is a practical map: for each piece, what it actually is
in one sentence, which part of the LLMOps (large language model operations) component map it implements, and the
maturity level (Level 0 baseline, Level 1 managed, Level 2 production-grade, Level 3 scaled — see the maturity
levels doc) at which a team typically first needs it. The goal is to be able to look at any Azure AI product name
in a meeting and immediately know what it is for and whether it is needed yet.

## Build, orchestrate, and run agents

| Service | What it is | LLMOps component | When you need it |
|---|---|---|---|
| **Microsoft Foundry** | The portal and SDK for building, evaluating, deploying, and governing models and agents — projects, model catalog, evaluation runs, tracing, in one place | Model management + evaluation + observability | Level 0 — this is where the first project gets created |
| **Foundry Agent Service** | Hosted runtime for agents: sandboxed sessions, managed state and memory, real-time voice through Voice Live | Multi-agent orchestration (hosting layer) | Level 2 — once agents need durable, hosted execution instead of a script running locally |
| **Model Router** | Automatically routes a request to the cheapest model that still meets a measured quality bar | Model management | Level 3 — once enough traffic and enough model options exist that manual routing leaves money on the table |
| **Azure OpenAI models (GPT-5.5 / 5.4 / 5.2, GPT-5.5 Instant, o-series, embeddings, open-weight Llama/Phi)** | The actual language, reasoning, and embedding models available through Azure OpenAI, plus open-weight models for cases needing on-box or licensing flexibility | Model management | Level 0 — a model deployment is the first thing every use case needs |
| **gpt-realtime-1.5** | Speech-to-speech model for low-latency voice conversations with tool-calling | Model management (voice channel) | Level 2 — when a voice channel use case goes to production |
| **Microsoft Agent Framework** | Orchestration library (Semantic Kernel + AutoGen convergence) for building multi-agent workflows with durable execution, in .NET or Python | Multi-agent orchestration | Level 2 — first real multi-agent workflow beyond a two-step chain |
| **MCP (Model Context Protocol)** | Open standard for connecting an agent to tools/systems of record | Multi-agent orchestration (tool layer) | Level 1 — as soon as an agent needs to call a real system, not just retrieve text |
| **A2A (Agent-to-Agent protocol)** | Open standard for agent-to-agent communication across teams or runtimes | Multi-agent orchestration (cross-team layer) | Level 3 — once more than one team is building agents independently |

## Knowledge and retrieval

| Service | What it is | LLMOps component | When you need it |
|---|---|---|---|
| **Azure AI Search** | Search service with hybrid (keyword + vector) retrieval, a semantic ranker, and integrated vectorization for building RAG (Retrieval-Augmented Generation) indexes | Data pipelines & knowledge | Level 1 — the first RAG-grounded use case |
| **AI Document Intelligence** | Extracts structured data from forms, scanned documents, and contracts | Data pipelines & knowledge (source ingestion) | Level 1 — when source documents are scanned/structured forms, not clean text |

## Safety and governance

| Service | What it is | LLMOps component | When you need it |
|---|---|---|---|
| **Content Safety** | Detects and blocks harmful content, prompt injection attempts, and can check groundedness/PII on outputs | Guardrails & safety | Level 1 — guardrails are a Level 1 requirement, not an afterthought |
| **Microsoft Purview** | Data governance: classification, lineage, retention, data-loss-prevention policies | Data pipelines & knowledge; security & identity | Level 1 for basic classification; Level 2 for full lineage tracing an answer back to its source |
| **Defender for Cloud + Defender for AI** | Cloud security posture management, extended with AI-specific threat detection (jailbreak attempts, anomalous model use) | Security & identity | Level 2 — once the system is handling production traffic worth actively defending |

## Data platform

| Service | What it is | LLMOps component | When you need it |
|---|---|---|---|
| **Microsoft Fabric / OneLake** | Unified lakehouse — can serve as the lakehouse/warehouse itself, with Bronze/Silver/Gold zones and built-in pipeline tooling | Data pipelines & knowledge | Level 1 — for the RAG source pipeline; Level 2 for the telemetry-to-BI loop |
| **Azure Cosmos DB** | Low-latency database used here for agent state, checkpoints, and vector/memory storage | Multi-agent orchestration (state); data pipelines (vector option) | Level 2 — once agents need durable state (pause/resume, memory across turns) |
| **Azure Event Hubs** | High-throughput event ingestion for streaming data | Data pipelines & knowledge (streaming sources) | Level 2 — when a source (like live call events) needs near-real-time ingestion rather than batch |

## Serving, integration, and compute

| Service | What it is | LLMOps component | When you need it |
|---|---|---|---|
| **Azure API Management (APIM)** | API gateway used here as the "AI gateway" — token metering, quotas, caching, canary routing, rate limiting in front of model endpoints | Serving & gateway | Level 1 — once more than one app/team calls the models and needs one enforcement point |
| **Azure Container Apps / AKS (Azure Kubernetes Service)** | Container hosting for orchestrators, MCP servers, and custom services, with autoscaling | Serving & gateway | Level 1 for Container Apps (simpler); Level 2-3 for AKS if scale/complexity demands it |
| **Azure Functions** | Serverless compute for lightweight tools, connectors, and event handlers | Serving & gateway; multi-agent orchestration (simple tools) | Level 0-1 — often the fastest way to stand up a first MCP tool |

## Identity, security, and governance backbone

| Service | What it is | LLMOps component | When you need it |
|---|---|---|---|
| **Entra ID** | Identity platform — authentication, authorization, managed identities | Security & identity | Level 0 — the landing zone is built on it from day one |
| **Key Vault** | Secrets, keys, and certificate storage, referenced rather than inlined | Security & identity | Level 0 — no application should hold a raw API key |
| **Azure Monitor / Application Insights / OpenTelemetry** | Unified tracing and metrics standard, capturing every model call, tool call, and agent hop as a span | Observability | Level 0 for basic tracing; Level 2 for full per-hop tracing linked to evaluation scores |

## CI/CD (continuous integration / continuous deployment) and channels

| Service | What it is | LLMOps component | When you need it |
|---|---|---|---|
| **Azure DevOps / GitHub Actions** | Pipeline tooling for everything-as-code: prompt/agent changes, evaluation gates, infrastructure deploys | Source control & Ops backbone | Level 0 — the repo and its first pipeline exist before the first use case ships |
| **Azure Communication Services (ACS)** | Voice/telephony integration layer, connecting to contact-center platforms (Genesys, NICE, Five9) | Serving & gateway (voice channel) | Level 2 — when a voice use case goes live, not before |

## Reading the stack as one picture

```
 Channels        ACS (voice) · web/chat · CRM/ticketing UI
      │
      ▼
 Gateway         APIM  (quotas · canary · caching · metering)
      │
      ▼
 Orchestration   Agent Framework (patterns) + Foundry Agent Service (hosting)
      │                │                          │
      │                ▼ MCP                       ▼ A2A
      │           Tools/systems of record      Other teams' agents
      ▼
 Models          Model Router → Azure OpenAI (GPT-5.x, gpt-realtime-1.5, embeddings, open-weight)
      │
      ▼
 Knowledge       Azure AI Search (hybrid+semantic) ← Fabric/OneLake ← source systems
      │
      ▼
 Guardrails      Content Safety (input/output checks, every hop)
      │
      ▼
 Observability   OpenTelemetry → Azure Monitor / App Insights → Foundry tracing/eval
      │
      ▼
 Governance      Purview (lineage/classification/retention) + Defender for Cloud/AI (posture/threat)
      │
      ▼
 Identity/CI-CD  Entra ID + Key Vault (foundation) · GitHub Actions/Azure DevOps (delivery)
```

## A practical way to use this doc

When a new product name shows up in a briefing or a vendor deck, run it through three questions using the tables
above: which row is it in (what does it actually do), which of the thirteen LLMOps components does it implement,
and does the current maturity level actually need it yet. A lot of stack sprawl comes from adopting a Level 3
tool (Model Router, A2A, fine-tuning pipelines) while still operating at Level 0 — the tables here are meant to
keep that sequencing honest: build the landing zone and one working use case first, and add the rest of the stack
only as the level actually calls for it.
