# 5thAug Brief — LLMOps Approach for APIX & Hiring Intelligence (source of truth)

> Anchor for everything in `5thAug/`. This package responds to a live client discussion (see below). It defines
> the **LLMOps approach and activities** grounded in two real use cases, generalizable to any future use case.
> **No timelines anywhere** (client asked to defer dates; focus on approach + activities). Both use cases are
> **agent pipelines (sequential), not agent-to-agent (A2A)** systems — reflect this throughout.
> Grounded in Afni + the two named use cases; author kept generic (no "prepared by").

## What the client asked for (from the discussion)
The document must cover, and Kiran (client lead) will refine it with us in a follow-up:
1. **How we plan to approach LLMOps.**
2. **The activities involved** (no timelines).
3. **What already exists and what needs to change** (as-is → to-be).
4. **How observability and evaluation will work — in detail.** Specifically:
   - What gets tracked for **every request**?
   - How **model calls** are tracked.
   - How **tool calls** are tracked.
   - How **agent sessions** are monitored.
5. **Infrastructure setup** (Azure services + hosting) — proposed, **no timelines**.
Client emphasis: spend the most time on **evaluation**. He specifically probed **tool-selection evaluation**
(if an MCP server exposes multiple tools, did the model pick the *correct* tool — a wrong tool that still
produces an answer is unreliable) and asked why **writing-quality vs task-execution** are separate metric groups.
He noted the use cases are just examples — the approach must apply to any project.

## The two use cases (grounding; describe as pipelines)

### APIX — Afni Performance Intelligence Index
Web-based performance-intelligence **dashboard** for Afni's contact-center operations. Replaces manual review of
call recordings with automated, data-driven coaching. Users: managers and coaches (each coach owns 15–25 agents
and cannot listen to every call). Multi-program: **Telesales** and **WCC** run on the same platform with
**different measurement criteria**.
- **Weekly per-agent report:** composite score /100; KPIs across sales, retention, customer experience; 4-week
  trend; AI coaching recommendations with practical steps; risk flags; breakdowns of escalations, sentiment, sales.
- **Pipeline shape (our understanding — to confirm):** call recording → speech-to-text transcript (+ metadata:
  agent id, program, queue, disposition, sales/CRM outcome) → **LLM analysis pipeline** → dashboard (web app reads results).
  LLM/agent pipeline steps (sequential): (1) transcript prep/segmentation; (2) **dimension-analysis agents** per
  program criteria (sales effectiveness, customer experience, retention, compliance/script adherence,
  sentiment/escalation); (3) **extraction agent** (escalations, sentiment, sales outcomes → structured); (4)
  **scoring/aggregation** into the /100 composite using program-weighted rubric; (5) trend computation (analytical,
  not LLM, over 4 weeks); (6) **coaching-recommendation agent** (practical steps + risk flags) → results stored → dashboard.
- **Data/tools:** transcript store, call-metadata store, sales/CRM outcomes, **program rubric config** (per-program weights).
- **What it exercises for evaluation:** groundedness (coaching must cite real transcript evidence, not hallucinate
  moments/quotes), scoring-vs-human-QA agreement, extraction accuracy (F1 on escalation/sentiment/outcome),
  coaching writing quality, consistency/fairness across agents & sites, operational cost/latency at "thousands of
  calls/day" scale. Tool-selection is minor here; data-retrieval correctness matters.

### Hiring Intelligence
AI-assisted, high-volume recruitment. **Pipeline shape (our understanding — to confirm):** intake/router agent →
résumé parse & rank agent (RAG over job description + rubric) → screening Q&A agent (RAG over role/policy) →
scoring & summary agent (structured candidate summary + fit score) → human recruiter decides.
- **Data/tools (via MCP — Model Context Protocol):** ATS (applicant tracking system) read/write, requisition DB,
  scheduling/calendar, résumé store.
- **What it exercises:** RAG groundedness/relevance, ranking quality, **tool-selection accuracy** (did it call the
  right ATS/MCP tool with the right arguments), summary writing quality, **fairness/bias** in ranking, operational.

**Why these two together:** APIX = analytical/batch pipeline (groundedness + structured scoring + writing +
fairness); Hiring = agentic-with-tools (tool selection + RAG + fairness). Between them they exercise **every metric
group**, and both are **pipelines, not A2A** — the same Ops setup serves both.

## OBSERVABILITY — the detail the client wants (centerpiece)
A request becomes a **trace tree** (parent → children spans):
```
Request (trace)
  └─ Pipeline run
       ├─ Agent 1 (span)
       │    ├─ Model call (span)
       │    └─ Tool call (span)
       ├─ Agent 2 (span) ...
       └─ Final output
```
**What is captured at each level (the table the deck/doc must include):**

| Level | Captured fields |
|---|---|
| **Request (trace)** | trace_id, use_case (apix/hiring), program (telesales/wcc), timestamp, input ref (call_id / candidate_id), output ref, status, **total latency**, **total tokens**, **total cost**, #agents run, human_intervention (y/n) |
| **Agent (span, per pipeline step)** | span_id, parent trace_id, agent_name, **agent_version**, role, input, output, model(s) used, tools used, #model_calls, #tool_calls, latency, tokens, cost, status, next_agent (handoff) |
| **Model call (span)** | model_name, **model_version**, deployment, **prompt_id + prompt_version**, system+user prompt (or hash if PII), completion, prompt_tokens, completion_tokens, cost, latency, temperature, finish_reason, cache_hit |
| **Tool call (span)** | tool_name, **mcp_server**, input_args, result, success/error, error_msg, latency, **expected_tool** & **was_correct_tool** (for evaluation) |
| **Session (multi-turn, e.g. Hiring screening)** | session_id linking turns, conversation history, user_id (hashed), total turns, outcome |
| **Feedback events** | linked by trace_id: thumbs + reason, coach edits to a report, recruiter overrides |

**Tooling / recommendation:** instrument with **OpenTelemetry GenAI semantic conventions**; send to
**Azure Application Insights + Log Analytics** as the system of record (data stays in tenant), and to
**self-hosted Langfuse** (on Azure Container Apps + Azure Database for PostgreSQL) as the LLM-specific lens
(cost per model, prompt versions, per-trace scores, datasets). **Azure AI Foundry tracing** links evaluation
scores to the exact trace. Answer each client sub-question explicitly: per request (trace row), per model call
(model-call span), per tool call (tool-call span incl. correct-tool flag), per agent session (session id + agent spans).

## EVALUATION — the priority topic

### Metric groups (acknowledge overlap — client raised this)
Some metrics overlap (e.g., coherence could sit under RAG or writing quality). We group by **what is being judged**,
not by mechanism, so a use case beyond RAG is still covered:
1. **Retrieval / RAG quality** — context relevance, groundedness/faithfulness, answer relevance, retrieval precision/recall.
2. **Generation / writing quality** — coherence, fluency, tone, completeness, correctness vs reference. (APIX coaching, Hiring summary.)
3. **Task execution / agentic** — task success rate, **tool-selection accuracy**, tool-argument correctness, plan/step
   efficiency, pipeline-path correctness. (This is why it is separate: a fluent answer built on the wrong tool is unreliable.)
4. **Safety / compliance / fairness** — unsafe-content rate, PII leakage, policy adherence, bias (hiring ranking, APIX consistency).
5. **Operational** — latency, cost, tokens per request (matters at APIX volume).
Rationale for the split (state it): writing quality judges *how it reads*; task execution judges *whether it did the
right thing* (right tool, right action). They are independent — an answer can read well and still be wrong-action.

### Tool-selection evaluation (client's specific probe — give it real treatment)
For an MCP server exposing tools [t1..tn]: build test cases with a **known expected tool** (+ expected args); run the
agent; read the **selected tool & args from the trace**; score with **custom Python** (Ragas/DeepEval do not cover this):
- tool-selection accuracy = correct / total; per-tool precision & recall.
- wrong-tool rate; **unnecessary-tool-call rate** (called a tool when none was needed); **missing-tool rate** (should
  have called one, didn't); **argument-correctness** rate.
Include short pseudocode. This is a first-class evaluator in the CI gate for agentic use cases like Hiring.

### Evaluator tooling matrix (list options, recommend a mix — client wants options)
| Tool | Covers | Open source? | Use it for |
|---|---|---|---|
| **Ragas** | RAG metrics (groundedness, context precision/recall, answer relevance) | Yes (Python) | APIX groundedness, Hiring RAG |
| **DeepEval** | Broad LLM eval incl. RAG + custom (G-Eval) + some agentic; pytest-style | Yes (Python) | CI gate, writing quality, general |
| **Custom Python** | Tool selection, tool args, pipeline path, scoring-vs-label, extraction F1 | Yes (own code) | Agent/tool behavior (not covered elsewhere) |
| **LLM-as-judge (+ rubric)** | Subjective quality (coaching usefulness, summary quality) | Depends | Where there is no single reference answer |
| **Azure AI Foundry evaluations** | Built-in + custom evaluators, cloud runs, links to traces | No (Azure) | Staying inside Azure; trace-linked eval |
| **promptfoo** | Config-driven CI evals, quick red-team | Yes | Fast CI checks, red-team |
| **LangSmith** | Eval + observability + datasets platform | **No — licensed** | If already standardized on LangChain; note license cost |

### How evaluation runs (three modes)
- **Offline (CI gate):** golden datasets per use case **and per program** (Telesales vs WCC differ). Run a subset on
  every PR; full set nightly/on-merge. Fail promotion if a metric drops past its baseline threshold.
- **Online (production):** sample a % of live traffic; run evaluators (e.g., LLM-as-judge groundedness) asynchronously;
  track quality trend; alert on drift.
- **Human review:** coach/recruiter feedback + periodic SME review of a sample; findings feed the golden datasets.
- **Per-agent AND end-to-end:** evaluate each pipeline agent (each APIX dimension analyzer; each Hiring agent) *and*
  the final output (report quality / candidate summary). A pipeline can pass end-to-end while one agent quietly degrades.

### Golden datasets
Curated, versioned test cases (JSONL) with input (+context), expected output or grading rubric, and metadata
(intent, difficulty, program, source). Sources: SME-authored, mined from anonymized real traffic (via traces), and
synthetic + human review. Start ~50–200 per use case/program; grow from production feedback. Stored in `/evals`,
mirrored to Langfuse/Foundry datasets for UI runs. Guard against eval over-fitting (rotate/refresh cases).

## APPROACH & ACTIVITIES (workstreams — sequenced, NO dates)
Present as workstreams with concrete activities and a foundational→later ordering; explicitly no timelines.
- **A. Discovery & current-state assessment** — inventory the existing APIX & Hiring pipelines; map agents, prompts,
  tools, data sources, current logging/eval; identify gaps (feeds the as-is/to-be).
- **B. Foundation** — GitHub repo + structure (/prompts /agents /evals /src /pipelines /infra /dashboards); Azure
  landing zone; Entra ID; Key Vault; API Management gateway; model deployments.
- **C. Instrumentation & observability** — add OpenTelemetry tracing to both pipelines (agent/model/tool spans);
  stand up App Insights + self-hosted Langfuse; define the per-request/model/tool/session capture.
- **D. Evaluation framework (priority)** — build golden datasets (per use case + program); implement evaluators
  (Ragas, DeepEval, custom Python for tool selection); wire CI gate; set up online sampling + human review.
- **E. Prompt & model management** — move prompts to Git + registry (labels prod/staging); model task-aliases
  (models.yaml) so no model name is hard-coded; PR + eval gate for any change.
- **F. CI/CD & release** — GitHub Actions (pr-checks, eval-full, deploy), OIDC to Azure (no stored keys), gated
  environments (dev/test/prod), canary + auto-rollback.
- **G. Data & knowledge pipelines** — Hiring RAG ingestion (job descriptions, rubrics, policy); APIX transcript &
  metadata flow; refresh (scheduled / change-data-capture).
- **H. Guardrails & governance** — Content Safety, PII redaction, fairness checks (hiring ranking, APIX consistency),
  human-in-the-loop for consequential outputs.
- **I. Feedback & improvement loop** — capture coach/recruiter feedback; analytics dashboards; triage negatives →
  label → add to golden set → fix prompt/retrieval/agent → re-evaluate → ship.
Ordering: A–C foundational; **D runs early and continuously (client priority)** alongside E–F; G–I layer in.

## AS-IS → TO-BE (write as a discovery checklist + labeled assumptions, not stated fact)
For each area, "typical current state (TO CONFIRM in discovery)" → "target state". Areas + likely gaps:
| Area | As-is (assumption, to confirm) | To-be (target) |
|---|---|---|
| Source control | Code in repos; prompts possibly inline/in notebooks | Monorepo; prompts/agents/evals versioned, PR-reviewed |
| Prompts | Edited in code or portal, untracked | Git source of truth + runtime registry, labels, A/B |
| Models | Model names in code | Task-aliases in config; swap = PR through eval gate |
| Tracing | App logs; no per-model/tool spans | Full OpenTelemetry trace tree; App Insights + Langfuse |
| Evaluation | Manual/spot-check; no gate | Golden datasets + automated evaluators + CI gate + online sampling |
| Data/RAG | Ad-hoc ingestion | Managed ingestion + scheduled/CDC refresh + index aliases |
| Guardrails | Minimal | Content Safety + PII + fairness + human-in-the-loop |
| Deploy | Manual | Actions + OIDC + gated + canary + rollback |
| Hosting | To confirm | Container Apps (+ Functions for triggers); APIM in front |
Note: APIX and Hiring already run (built by the product team) — the platform wraps and standardizes them; we are not
rebuilding the use cases, we are adding the operational layer around them.

## INFRASTRUCTURE & AZURE HOSTING (proposed; NO timelines)
**Hosting the pipelines — compare, then recommend:**
| Option | Fit | Note |
|---|---|---|
| **Azure Container Apps** (recommended default) | Each agent/pipeline step as a container/microservice; scale-to-zero; KEDA autoscale; Dapr optional | Best general fit for pipeline services |
| **Azure Functions** | Event-driven steps ("new transcript → analyze") | Great for APIX batch/event triggers |
| **Foundry Agent Service** | Managed hosted agents; less infra to run | Consider for hosted agents as it matures |
Recommendation: **Container Apps for the pipeline services + Functions for event triggers (new call/candidate)**;
optionally adopt Foundry Agent Service later for hosted agents.
**Bill of services (grouped):**
- Models/AI: Azure OpenAI / Foundry (model deployments), Content Safety, (AI Document Intelligence if needed).
- Knowledge/RAG: Azure AI Search (Hiring; optional transcript search).
- Data/state: Azure Cosmos DB (agent state/results) and/or Azure SQL (APIX scores for dashboard); Blob Storage
  (transcripts, golden datasets); Microsoft Fabric/OneLake (telemetry lake + analytics + training-data curation — later).
- Gateway/compute: API Management (gateway, quotas, metering); Container Apps + Functions.
- Observability: Azure Monitor + Application Insights + Log Analytics; self-hosted Langfuse (Container Apps +
  Azure Database for PostgreSQL); dashboards in Power BI / Azure Managed Grafana.
- Web app (APIX dashboard): Azure App Service or Static Web Apps + API.
- Security/identity: Entra ID, Key Vault, Private Endpoints/VNet, Microsoft Purview, Defender for Cloud.
- CI/CD: GitHub + GitHub Actions + OIDC federated login to Azure.
Environments: dev / test / prod on a landing zone. **No timelines** — this is the target setup, sequencing lives in the activities section.

## Deliverables
- **`document/`** — a **sendable Word (.docx)** consolidating the approach (the "document" for the client).
- **`presentation/`** — a **fully editable (native shapes, no images)** walkthrough deck.
- **`docs/`** — detailed markdown deep-dives (source + reference reading).

## Tone & rules
Practical, engineer/consultant working-notes tone; not marketing; must not read as AI-generated. Simple English,
abbreviations expanded on first use (LLMOps, RAG, MCP, CI/CD, OIDC, PII, ATS, KPI, WCC, APIX, CDC). Diagram-led deck,
editable. **No timelines.** Pipelines, not A2A. Grounded in Afni + APIX + Hiring; author generic.
