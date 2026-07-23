# LLMOps Lifecycle & Toolchain

## Overview

LLMOps is the operational backbone that lets Afni build, evaluate, deploy, govern, and continuously improve fleets of cooperating AI agents with the same rigor Afni already applies to running contact centers. This document defines the end-to-end lifecycle, the evaluation and CI/CD disciplines that make it trustworthy, and the mapping of each lifecycle stage to concrete Azure services.

Governance and Responsible AI wrap the entire loop. **A model/prompt registry entry and passing evaluation gates are mandatory before any promotion to production.**

## The Lifecycle

```
        +----------------------------------------------------------+
        |            GOVERNANCE & RESPONSIBLE AI (wraps all)        |
        |     Purview · Content Safety · RAI review · audit         |
        +----------------------------------------------------------+
          |                                                    ^
          v                                                    |
  +----------------+   +----------------------+   +----------------------+
  | 1. DATA &      |-->| 2. PROMPT / AGENT    |-->| 3. EVALUATION        |
  | KNOWLEDGE      |   | ENGINEERING          |   | offline (golden sets,|
  | CURATION       |   | (versioned prompts,  |   | LLM-judge) + online  |
  | ingest·label   |   | agents, tools)       |   | (A/B, shadow)        |
  +----------------+   +----------------------+   +----------+-----------+
          ^                                                  |
          |                                          [regression gate]
          |                                                  v
  +----------------+   +----------------------+   +----------------------+
  | 6. FEEDBACK    |<--| 5. OBSERVABILITY     |<--| 4. CI/CD             |
  | thumbs·QA·     |   | tracing·cost·quality |   | registry·canary·     |
  | incidents ->   |   | ·drift·groundedness  |   | blue-green·rollback  |
  | dataset        |   +----------------------+   +----------------------+
  +----------------+            |                          |
          ^                     v                          v
          +-----------------  SERVING (APIM gateway, quotas, caching) 
```

### 1. Data & Knowledge Curation
Source documents (policies, KBs, job requisitions, transcripts) are ingested via **Azure AI Document Intelligence**, chunked, embedded with **text-embedding-3-large**, and indexed in **Azure AI Search**. Curated datasets, golden sets, and evaluation corpora are versioned in **Azure Data Lake / Microsoft Fabric**. Purview enforces classification and lineage.

### 2. Prompt / Agent Engineering (versioned)
Prompts, agent definitions, tool schemas, and orchestration graphs are authored in **Azure AI Foundry / Prompt flow** and stored **as code** in Git. Every prompt and agent config is versioned, code-reviewed, and traceable to an evaluation result — no ad-hoc production prompt edits.

### 3. Evaluation (offline + online)
See the dedicated section below.

### 4. CI/CD
Automated pipelines promote artifacts through dev → test → prod behind evaluation gates. See CI/CD section below.

### 5. Observability
**Azure Monitor + Application Insights** ingest **OpenTelemetry** traces using the **GenAI semantic conventions**: token usage, cost, latency per turn/agent/tool, quality scores, groundedness, and drift. Dashboards surface FinOps (token spend by use case, via APIM metering) alongside quality KPIs.

### 6. Feedback Loop
End-user thumbs, human QA scores, and production incidents are captured and routed back into curated datasets — closing the flywheel so real-world failures become tomorrow's regression tests.

## Evaluation in Depth

Evaluation is the discipline that separates a demo from an enterprise deployment. Afni runs a layered evaluation strategy using the **Azure AI Evaluation SDK**.

### Offline Evaluation
- **Golden datasets** — curated, versioned input/expected-output sets per use case and per specialist agent, including edge cases and known failure modes. Every prompt/agent change is scored against them.
- **LLM-as-judge** — a strong model (GPT-4o) scores responses on relevance, coherence, completeness, and tone using calibrated rubrics, enabling scale beyond manual review.
- **Groundedness / faithfulness** — RAG outputs are checked against retrieved sources (Azure AI Content Safety groundedness detection) to catch hallucination; every claim must trace to a citation.
- **Human-in-the-loop review** — SMEs from ops and HR review sampled and high-risk outputs; their labels calibrate the LLM judge and feed golden sets.
- **Red-teaming** — adversarial testing for jailbreaks, prompt injection, PII leakage, unsafe tool calls, and (for HR) bias/adverse-impact probing, aligned to NYC Local Law 144 bias-audit expectations.

### Online Evaluation
- **A/B testing** — new prompt/model versions serve a traffic slice; business KPIs (containment, AHT, FCR, CSAT; time-to-fill, funnel conversion) are compared.
- **Shadow testing** — a candidate version runs silently on live traffic with outputs logged but not served, de-risking changes before exposure.
- **Continuous online scoring** — sampled production interactions are scored by the LLM judge and monitored for quality drift.

### Regression Gates
Promotion is blocked automatically if a change reduces golden-set scores, groundedness, or safety metrics below defined thresholds, or increases cost/latency beyond budget. Gates are codified in the pipeline, not left to reviewer judgment.

## CI/CD in Depth

- **Prompt / model registry** — every prompt, agent config, and model deployment is a registered, immutable, versioned artifact with lineage to its evaluation results and approver.
- **Pipeline stages** — commit triggers lint/schema validation → offline evaluation on golden sets → red-team suite → integration tests → gated promotion.
- **Canary** — new version receives a small production traffic percentage with automated KPI/guardrail monitoring before ramp.
- **Blue-green** — a fully provisioned parallel environment enables instant cutover and instant fallback.
- **Rollback** — because prompts and models are versioned artifacts behind the APIM gateway, rollback is a routing change to the prior registered version — fast and deterministic.

Pipelines run on **Azure DevOps or GitHub Actions**; infrastructure is Bicep/Terraform; agents deploy to **Azure Container Apps / AKS**.

## Serving
Production traffic flows through the **Azure API Management** AI gateway providing token metering, quotas, semantic caching, and multi-deployment routing (see `03-platform-architecture.md`). The gateway is also the enforcement point for version routing during canary and rollback.

## Toolchain Mapped to Azure Services

| Lifecycle Component | Azure Service |
|---|---|
| Knowledge ingestion / extraction | Azure AI Document Intelligence |
| Retrieval index / vectors | Azure AI Search; Cosmos DB |
| Embeddings & models | Azure OpenAI (GPT-4o / 4o-mini / gpt-realtime), Azure AI Speech |
| Prompt / agent authoring | Azure AI Foundry, Prompt flow |
| Prompt / model registry | Azure AI Foundry registry + Git |
| Evaluation (offline + online) | Azure AI Evaluation SDK, Content Safety (groundedness) |
| CI/CD | Azure DevOps / GitHub Actions |
| Serving & gateway | Azure API Management; Container Apps / AKS |
| Observability | Azure Monitor, Application Insights, OpenTelemetry (GenAI) |
| Data & analytics | Azure Data Lake / Microsoft Fabric; Azure SQL |
| Governance & security | Microsoft Purview, Entra ID, Key Vault, Defender for Cloud, Content Safety |

## LLMOps vs. Traditional MLOps / DevOps

| Dimension | DevOps | MLOps | **LLMOps** |
|---|---|---|---|
| Core artifact | Code | Code + trained model + data | Code + **prompts** + agents + tools + foundation model |
| Determinism | Deterministic | Statistical, reproducible with seed | **Non-deterministic** outputs from the same input |
| Testing | Unit/integration (pass/fail) | Metrics on holdout set | **Judge-based, rubric scoring, groundedness, red-team** |
| Model training | N/A | Central activity | Often **no training** — prompt/RAG/agent engineering dominate |
| Failure modes | Bugs, outages | Drift, accuracy decay | Drift **plus** hallucination, injection, PII leakage, bias |
| Cost driver | Compute/hosting | Training compute | **Per-token inference cost** — FinOps is first-class |
| Guardrails | Access control | Data validation | **Content safety + deterministic policy around probabilistic models** |
| Human role | Reviewer | Data/label validation | **Human-in-the-loop for consequential decisions** |

LLMOps inherits DevOps automation and MLOps discipline but adds first-class handling of prompts as versioned artifacts, non-deterministic evaluation, token-level FinOps, safety/groundedness guardrails, and mandatory human oversight for consequential decisions — exactly the controls Afni's regulated contact-center and hiring workloads require.
