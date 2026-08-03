# Research Brief — Practical LLMOps (3rdAug package)

> Source of truth for everything in `3rdAug/`. This is a **research-phase** package: practical, tool-specific,
> implementation-level. No marketing tone, no author names, generic (no client names in the deck; docs may
> reference "a contact-center BPO enterprise" for sizing). Every doc must answer "what exactly do we set up
> and with which tool", not "why AI matters".

## Framing
- Start small → go big. Everything is presented as maturity levels: **Level 0 (baseline) → Level 1 (managed) →
  Level 2 (production-grade) → Level 3 (scaled/self-service)**. Each level names exactly what gets added.
- Client is on the **Azure stack** — Azure is the primary lane everywhere, but each component section MUST
  compare the market options (Microsoft vs open-source vs SaaS) honestly and say what each tracks/does,
  then recommend a lane.
- Reuse terminology consistent with the parent repo bible (`reference/proposal-bible.md`): Microsoft Foundry
  (formerly Azure AI Foundry), Foundry Agent Service, Model Router, Microsoft Agent Framework (Semantic Kernel
  + AutoGen convergence), MCP (Model Context Protocol, agent→tool), A2A (agent→agent), GPT-5.x models,
  gpt-realtime-1.5, Microsoft Fabric / OneLake, Azure AI Search, Content Safety, APIM as AI gateway,
  Entra ID / Key Vault / Purview / Defender, Azure Monitor + Application Insights + OpenTelemetry.

## The component map (what LLMOps covers; all are reusable platform components)
1. **Source control & Ops backbone (GitHub)** — repos, branching, PRs, GitHub Actions, Environments, OIDC to Azure.
2. **Prompt management** — where prompts live, versioning, registry, A/B.
3. **Model management** — catalog, deployments, how a team picks/swaps models, router, benchmarks.
4. **Evaluation** — metrics, golden datasets, evaluators, CI gates, LLM-as-judge.
5. **Observability** — tracing, token/cost/latency/quality, provider comparison.
6. **Feedback & analytics** — response capture, user feedback, dashboards, improvement loop, fine-tuning path.
7. **Data pipelines & knowledge** — ingestion, chunking, embedding, index refresh, warehouse relationship.
8. **Guardrails & safety** — input/output checks, PII, policy.
9. **Serving & gateway** — APIM, quotas, caching, canary.
10. **Multi-agent orchestration** — frameworks, agent types, workflow management, how agents ride the same Ops.
11. **Security & identity**, 12. **FinOps**, 13. **Environments/IaC** — cross-cutting.

## Per-component practical anchors (docs must include these specifics)

### Observability — provider comparison (be concrete)
| Option | What it is | What it tracks | Notes |
|---|---|---|---|
| **Azure Monitor + Application Insights (+ Foundry tracing)** | Azure-native, OpenTelemetry-based | Traces/spans per model & tool call, tokens, latency, errors, custom events; Foundry links eval scores to traces | Default lane; data stays in tenant; Power BI/Workbooks dashboards |
| **Langfuse** | Open-source LLM observability (self-hostable on Azure Container Apps + Postgres) | Traces, generations, token cost per model, sessions/users, prompt versions, user feedback scores, eval scores, datasets | Best LLM-specific UX; also does prompt management + datasets; self-host keeps data in tenant |
| **LangSmith** | SaaS from the LangChain team | Traces, runs, feedback, datasets, prompt hub, online evaluators | Strong if LangChain/LangGraph used; SaaS data residency to check |
| **Arize Phoenix** | Open-source, OTel-based | Traces, evals, embedding drift analysis | Good for drift/embedding analysis |
| **W&B Weave / Datadog LLM Obs** | SaaS | Traces, evals, cost | If those platforms already in-house |
Recommended lane: **App Insights (OpenTelemetry GenAI semantic conventions) as the system of record + Langfuse
(self-hosted) as the LLM-specific lens**; Foundry portal for eval-linked traces. What to instrument: every model
call (prompt, completion, tokens, cost, latency, model+version, prompt version, use case tag), every tool call,
every agent hop, session/user ids, feedback events.

### Ops on GitHub — the exact setup ("what makes it LLMOps")
- **Repo layout (monorepo per platform, folder per use case):**
  `/prompts` (YAML/Jinja templates, one file per prompt, semver), `/agents` (agent + workflow definitions as code),
  `/evals` (golden datasets JSONL + evaluator configs), `/src` (app/orchestration code), `/pipelines` (GitHub
  workflows), `/infra` (Bicep/Terraform), `/dashboards`.
- **Branching:** trunk-based; short-lived feature branches; PR mandatory; CODEOWNERS on `/prompts` and `/agents`.
- **GitHub Actions workflows:**
  - `pr-checks.yml` — lint, unit tests, **prompt regression evals on changed prompts** (small golden subset).
  - `eval-full.yml` — nightly/on-merge full golden-set run; posts scorecard to PR/summary.
  - `deploy.yml` — build container, deploy to dev → test → prod using **GitHub Environments** with required
    reviewers; canary slice first; auto-rollback on health/eval alarms.
  - `index-refresh.yml` — scheduled RAG re-index.
- **Auth:** GitHub OIDC federated credentials to Entra ID (no stored cloud keys). Secrets in Key Vault.
- **Definition:** it "is LLMOps" when prompts/agents/datasets are versioned in Git, every change runs evals in CI,
  deploys are gated + reversible, and production traces flow back into datasets.

### Prompt management — where prompts live
- **Source of truth = Git** (`/prompts/<use-case>/<prompt-name>.yaml` with fields: id, version, model hints,
  template, variables, eval references, changelog). Changed only via PR + eval gate.
- **Runtime registry** for hot-reload/A-B: Langfuse Prompt Management (versioned, labeled prod/staging) or Foundry
  prompt assets; the app requests "prompt X, label prod". Git→registry sync in CI.
- A/B: two prompt versions labeled, traffic split at the app/gateway, compared on online metrics.

### Model management — how model choice actually works
- **Model catalog** (Foundry) + **named deployments** per environment; access via APIM.
- **Config-driven aliases in Git** (`models.yaml`): each use case maps a *task alias* → deployment
  (e.g., `summarize: gpt-5-mini`, `reason: gpt-5.2`, `voice: gpt-realtime-1.5`). Swapping models = config PR
  that must pass the eval gate. No model names hard-coded in app code.
- **Model Router** option: route by task complexity/cost automatically where quality bar is measured.
- New-model adoption loop: candidate model → run full golden sets → compare scorecards + cost/latency → shadow
  → promote alias.

### Evaluation — metrics & golden datasets
- **Golden dataset** = a curated, versioned set of test cases: input (+context), expected output or grading
  criteria, metadata (intent, difficulty, source). Start ~50–200 per use case. Sources: SME-authored, anonymized
  real traffic (mined from traces/feedback), synthetic (generated then human-reviewed). Stored as JSONL in
  `/evals`, versioned; also mirrored to Langfuse/Foundry datasets for UI runs.
- **Metrics:** RAG (groundedness, relevance, completeness; retrieval precision/recall), generation (coherence,
  fluency, similarity to reference), task (exact match/F1 for extraction; pass-rate for tool calls), agents
  (task success rate, tool-call accuracy, steps, handoff correctness), operational (latency p50/p95, cost/request),
  safety (attack success rate, PII leak rate). Score via **Azure AI evaluation SDK** (built-in + custom evaluators),
  **Ragas** (RAG), **promptfoo** (CI-friendly config-based), **LLM-as-judge** with a strong model + rubric,
  plus human review for a sample. CI gate: fail PR if score drops > threshold vs baseline.

### Feedback, analytics & improvement loop
- Capture: every response logged with trace id; user signals (thumbs up/down + reason, edits, escalation-to-human,
  abandonment); implicit signals (retry, session length). Feedback API writes to App Insights custom events +
  Langfuse scores.
- **Analytics dashboard** (Power BI on Fabric + Langfuse/Foundry dashboards): volume, containment/deflection,
  p95 latency, cost per use case/day, quality scores trend, feedback rate & top negative reasons, top intents,
  drift indicators. Telemetry exported to **Fabric lakehouse** for BI + data science.
- Improvement: triage negative feedback → label → add to golden set → fix prompt/retrieval/agent → eval → ship.
  **Fine-tuning** (Azure OpenAI fine-tuning) only when prompt+RAG plateau: curate accepted responses as training
  pairs (human-approved, PII-scrubbed), fine-tune small model, evaluate vs golden set, deploy behind alias.

### Data pipelines & warehouse
- LLMOps does not replace the warehouse; it **connects to it both ways**. Microsoft Fabric (OneLake) can BE the
  warehouse/lakehouse: sources → pipelines → lakehouse → serving.
- **Knowledge pipeline (RAG):** sources (SharePoint, Blob, SQL, CRM/ticketing, call transcripts) → ingestion
  (Fabric Data Factory / Logic Apps / AI Search built-in indexers) → clean + PII-scrub → chunk → embed
  (text-embedding-3-large) → Azure AI Search index → scheduled + event-driven (CDC) refresh; index aliases for
  blue-green re-index.
- **Telemetry pipeline:** App Insights → diagnostic export → Fabric lakehouse → Power BI + training-data curation.
- Governance: Purview classification/lineage on both.

### Multi-agent in the Ops setup
- **Frameworks:** Microsoft **Agent Framework** (SK+AutoGen; .NET/Python; durable workflows; Azure-native) — primary;
  **LangGraph** (graph/state-machine orchestration, fine control, strong ecosystem); **CrewAI** (role-based crews,
  fast prototyping); **OpenAI Agents SDK** (lightweight, provider-tied). Hosted runtime: **Foundry Agent Service**.
- **Agent types to build:** router/intent, planner/supervisor, retrieval (RAG), tool/action (via MCP), critic/
  evaluator (reflection), summarizer, guardrail/compliance, human-proxy (approval).
- **Workflow management:** patterns (sequential, concurrent, group chat, handoff, planner/Magentic); durable
  execution (checkpoint, pause/resume, retry, compensation); state in Cosmos DB; long processes via Agent Framework
  durable workflows.
- **Agents ride the same Ops:** defined as YAML/code in Git; per-agent unit evals + end-to-end scenario evals in CI;
  per-hop tracing; registry + versioning; guardrails per step; HITL approval nodes.

## Maturity levels (the start-small plan; use everywhere)
- **Level 0 — Baseline (weeks 1–2):** GitHub repo + structure, Azure landing (RG, Entra ID, Key Vault, APIM,
  Azure OpenAI), App Insights basic tracing, prompts in Git, manual eval notebook, one use case in dev.
- **Level 1 — Managed (weeks 3–6):** CI evals on PR (golden set v1), prompt registry + labels, AI Search RAG
  pipeline, Content Safety guardrails, dashboards v1, dev/test/prod + gated deploys. → *first production use case.*
- **Level 2 — Production-grade (months 2–4):** full golden sets + nightly evals, canary + auto-rollback, feedback
  capture + analytics on Fabric, cost metering/showback, Langfuse (or equal) LLM observability, red-team suite,
  multi-agent orchestration with Agent Framework + agent registry.
- **Level 3 — Scaled (months 4+):** self-service use-case onboarding, model router + fine-tuning loop, A2A across
  teams, drift detection, DR, FinOps budgets/alerts, warehouse-integrated training-data curation.

## Team & timeline (proposal-style; ILLUSTRATIVE)
- **Core team:** 1 GenAI architect/lead, 2–3 GenAI engineers, 1 data engineer, 0.5 DevOps, 0.5 security,
  0.5 product/PM. (Scale to ~8–10 at Level 3 with a platform + use-case split.)
- **Timeline:** Level 0 ≈ 2 wks; Level 1 ≈ 4 wks (first prod use case ~week 6); Level 2 ≈ 2–3 months; Level 3 ongoing.
- **Assumptions:** Azure tenant + subscription access exists; Azure OpenAI quota approved; data sources accessible;
  SMEs available ~4h/week for golden sets; security sign-off process defined.
- **Risks:** quota/capacity delays, data-access approvals, golden-set quality (garbage in), eval over-fitting,
  cost surprises from multi-agent call fan-out, skill ramp, scope creep from use-case pull before platform ready.

## Deck rules
Generic (no client/author), research-phase feel, **editable native shapes only (no images)**, less text/more
diagrams, simple English, abbreviations expanded on first use, ~18–20 slides, speaker notes, simple two-color design.
