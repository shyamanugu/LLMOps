# GenAIOps Lifecycle & Toolchain

## Overview

**GenAIOps** is the operational backbone that lets AFNI build, evaluate, deploy, govern, and continuously improve fleets of cooperating AI agents with the same rigor AFNI already applies to running contact centers. It is the discipline the enterprise framework runs on: because every use case is onboarded through the same lifecycle, security, evaluation, and observability are inherited by default rather than re-invented per project.

This document defines the end-to-end lifecycle, the evaluation and CI/CD disciplines that make it trustworthy, and the mapping of each lifecycle stage to concrete Microsoft Foundry / Azure services. It applies uniformly to the three proof-point use cases — the **Voice Agent**, the **Performance Intelligence Index (PI Index)**, and **Hiring Intelligence** — and to every future use case onboarded via the paved road.

Governance and Responsible AI wrap the entire loop. **A model/prompt/agent registry entry and passing evaluation gates are mandatory before any promotion to production.** The CI/CD pipeline mechanics are expanded in `23-genaiops-cicd.md`; the evaluation methodology in `25-evaluation-framework.md`.

## MLOps -> LLMOps -> GenAIOps

The practice has evolved through three overlapping generations, and AFNI's framework deliberately targets the third:

| | **MLOps** | **LLMOps** | **GenAIOps** |
|---|---|---|---|
| Core artifact | Trained model + data | **Prompts** + foundation model + RAG | **Agents, tools, workflows** + prompts + models |
| Unit of delivery | A model endpoint | A prompt/chain behind an app | A **fleet of cooperating agents** with tools and memory |
| Central activity | Train / retrain | Prompt & RAG engineering | Agent, tool (MCP), and workflow engineering |
| Evaluation | Metrics on a holdout set | Judge/rubric scoring, groundedness | Above **+ multi-step trajectory, tool-use, and agent-quality** evals |
| Observability | Model metrics, drift | Token/cost/quality traces | **Unified OpenTelemetry** across model/tool/sub-agent/handoff |
| New risks | Drift, accuracy decay | Hallucination, injection, PII, cost | Above **+ excessive agency, unsafe tool calls, orchestration failure** |

GenAIOps inherits DevOps automation and MLOps discipline, then adds first-class handling of **agents and MCP tools as versioned artifacts**, non-deterministic and multi-step evaluation, token-level FinOps, safety/groundedness guardrails, and mandatory human oversight for consequential decisions — exactly the controls AFNI's regulated contact-center, performance-scoring, and hiring workloads require.

## The Lifecycle

```
        +----------------------------------------------------------+
        |            GOVERNANCE & RESPONSIBLE AI (wraps all)        |
        |     Purview · Content Safety · RAI review · audit         |
        +----------------------------------------------------------+
          |                                                    ^
          v                                                    |
  +----------------+   +----------------------+   +----------------------+
  | 1. DATA &      |-->| 2. PROMPT / AGENT /  |-->| 3. EVALUATION        |
  | KNOWLEDGE      |   | WORKFLOW ENGINEERING |   | offline (golden sets,|
  | CURATION       |   | (versioned YAML:     |   | rubric evaluators) + |
  | ingest·label   |   | prompts·agents·tools)|   | online (A/B, shadow) |
  +----------------+   +----------------------+   +----------+-----------+
          ^                                                  |
          |                                          [evaluation gate]
          |                                                  v
  +----------------+   +----------------------+   +----------------------+
  | 6. FEEDBACK    |<--| 5. OBSERVABILITY     |<--| 4. CI/CD             |
  | thumbs·QA·     |   | unified OTel tracing |   | registry·canary·     |
  | incidents ->   |   | ·cost·quality·drift  |   | blue-green·rollback  |
  | dataset        |   | ·groundedness        |   +----------------------+
  +----------------+   +----------------------+              |
          ^                     |                            v
          +-----------------  SERVING (APIM gateway + Model Router, quotas, caching)
```

### 1. Data & Knowledge Curation
Source documents (policies, KBs, job requisitions, transcripts) are ingested via **Azure AI Document Intelligence**, chunked, embedded with **text-embedding-3-large**, and indexed in **Azure AI Search** (integrated vectorization). Curated datasets, golden sets, evaluation corpora, and PI Index scoring rubrics are versioned in **Microsoft Fabric / OneLake**. Purview enforces classification and lineage.

### 2. Prompt / Agent / Workflow Engineering (versioned)
Prompts, **agent definitions, tool schemas, and orchestration graphs are authored declaratively and stored as version-controlled YAML** in Git (Microsoft Agent Framework 1.0 declarative agents-and-workflows-as-code), with Foundry for interactive authoring and testing. Every prompt, agent, and workflow config is versioned, code-reviewed, and traceable to an evaluation result — no ad-hoc production edits.

### 3. Evaluation (offline + online)
See the dedicated section below and `25-evaluation-framework.md`.

### 4. CI/CD
Automated pipelines promote artifacts through dev → test → prod behind evaluation gates. See CI/CD section below and `23-genaiops-cicd.md`.

### 5. Observability
A **single, unified OpenTelemetry pipeline** captures every model call, tool invocation, sub-agent hop, and handoff using the **GenAI semantic conventions**: token usage, cost, latency per turn/agent/tool, quality scores, groundedness, and drift. **Azure Monitor + Application Insights** surface these; **Foundry evaluations link every score back to the exact trace**. Dashboards surface FinOps (token spend by use case, via APIM metering) alongside quality KPIs. See `10-observability-finops.md`.

### 6. Feedback Loop
End-user thumbs, human QA scores, PI Index calibration adjustments, and production incidents are captured and routed back into curated datasets — closing the flywheel so real-world failures become tomorrow's regression tests.

## Evaluation in Depth

Evaluation is the discipline that separates a demo from an enterprise deployment. AFNI runs a layered evaluation strategy using the **Foundry evaluation** capabilities (Azure AI Evaluation SDK), and **every evaluation result links back to the exact OpenTelemetry trace** that produced it.

### Offline Evaluation
- **Golden datasets** — curated, versioned input/expected-output sets per use case and per specialist agent, including edge cases and known failure modes. Every prompt/agent/workflow change is scored against them. PI Index scoring is validated against human-calibrated reference scores.
- **Rubric evaluators (LLM-as-judge)** — Foundry **auto-generated rubric evaluators** score responses against context-aware rubrics (relevance, coherence, completeness, tone, and agent quality), enabling scale beyond manual review.
- **Groundedness / faithfulness** — RAG outputs are checked against retrieved sources (Content Safety groundedness detection) to catch hallucination; every claim (and every PI Index driver rationale) must trace to a citation or evidence span.
- **Agent trajectory & tool-use evaluation** — multi-step runs are scored on whether the agent selected the right tools, in the right order, with valid arguments — a GenAIOps-specific evaluation beyond single-response scoring.
- **Human-in-the-loop review** — SMEs from ops, QA, and HR review sampled and high-risk outputs; their labels calibrate the rubric evaluators and feed golden sets.
- **Red-teaming** — adversarial testing for jailbreaks, prompt injection, PII leakage, unsafe tool calls, and (for Hiring Intelligence) bias/adverse-impact probing, aligned to the OWASP Top 10 for LLM Applications (2025) and NYC Local Law 144 bias-audit expectations.

### Online Evaluation
- **A/B testing** — new prompt/model/agent versions serve a traffic slice; business KPIs (containment, AHT, FCR, CSAT for Voice Agent; scoring agreement for PI Index; time-to-fill, funnel conversion for Hiring) are compared.
- **Shadow testing** — a candidate version runs silently on live traffic with outputs logged but not served, de-risking changes before exposure. PI Index changes are shadow-scored against production before cutover.
- **Continuous online scoring** — sampled production interactions are scored by rubric evaluators and monitored for quality drift.

### Evaluation Gates
Promotion is blocked automatically if a change reduces golden-set scores, groundedness, scoring agreement, or safety metrics below defined thresholds, or increases cost/latency beyond budget. Gates are codified in the pipeline, not left to reviewer judgment.

## CI/CD in Depth

- **Prompt / model / agent registry** — every prompt, agent config, workflow, and model deployment is a registered, immutable, versioned artifact with lineage to its evaluation results and approver.
- **Pipeline stages** — commit triggers lint/schema validation → offline evaluation on golden sets → red-team suite → integration tests → gated promotion.
- **Canary** — new version receives a small production traffic percentage with automated KPI/guardrail monitoring before ramp.
- **Blue-green** — a fully provisioned parallel environment enables instant cutover and instant fallback.
- **Rollback** — because prompts, agents, and models are versioned artifacts behind the APIM gateway, rollback is a routing change to the prior registered version — fast and deterministic.

Pipelines run on **Azure DevOps or GitHub Actions**; infrastructure is Bicep/Terraform; agents deploy to **Azure Container Apps / AKS**. Full pipeline detail is in `23-genaiops-cicd.md`.

## Serving
Production traffic flows through the **Azure API Management** AI gateway plus the **Model Router**, providing token metering, quotas, semantic/prompt caching, quality-aware model routing, and multi-deployment version routing (see `03-platform-architecture.md`). The gateway is the enforcement point for version routing during canary and rollback.

## Toolchain Mapped to Foundry / Azure Services

| Lifecycle Component | Service |
|---|---|
| Knowledge ingestion / extraction | Azure AI Document Intelligence |
| Retrieval index / vectors | Azure AI Search (integrated vectorization); Cosmos DB |
| Embeddings & models | Foundry model catalog (GPT-5.5 / 5.4 / 5.2, gpt-realtime-1.5), Model Router, text-embedding-3-large |
| Prompt / agent / workflow authoring | Microsoft Foundry; Microsoft Agent Framework 1.0 (declarative YAML) |
| Prompt / model / agent registry | Foundry registry + Git |
| Evaluation (offline + online) | Foundry evaluations / Azure AI Evaluation SDK, rubric evaluators, Content Safety (groundedness) |
| CI/CD | Azure DevOps / GitHub Actions |
| Serving & gateway | Azure API Management + Model Router; Container Apps / AKS |
| Observability | Azure Monitor, Application Insights, unified OpenTelemetry (GenAI conventions) |
| Data & analytics | Microsoft Fabric / OneLake; Azure SQL |
| Governance & security | Microsoft Purview, Entra ID, Key Vault, Defender for Cloud + Defender for AI, Content Safety |

## Why GenAIOps Is Different

The move from DevOps and MLOps to GenAIOps is not incremental. Outputs are **non-deterministic** from the same input; the primary artifacts are **prompts, agents, and MCP tools** rather than trained models; testing is **judge-based, rubric, groundedness, trajectory, and red-team** rather than pass/fail; failure modes include **hallucination, prompt injection, PII leakage, bias, and excessive agency**; the dominant cost is **per-token inference**, so FinOps is a first-class release criterion; and **human-in-the-loop** oversight is mandatory for consequential decisions. AFNI's framework encodes all of these as standard, inherited controls so that every onboarded use case ships trustworthy by construction.
