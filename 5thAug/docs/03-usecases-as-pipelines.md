# The Two Use Cases as Agent Pipelines

Both APIX and Hiring Intelligence are **sequential agent pipelines**. Each step
finishes and hands off to the next in a fixed order. They are **not
agent-to-agent (A2A)** systems — no agent negotiates with or delegates to a peer
at runtime. This matters for operations: a pipeline has a known path, so we can
trace it step by step, evaluate each step, and evaluate the whole end to end.

The pipeline internals below are marked **our understanding — to confirm** because
we have not audited the code yet. Discovery replaces these with the confirmed
maps.

## APIX — Afni Performance Intelligence Index

### What it is

APIX is a web-based performance-intelligence **dashboard** for Afni's
contact-center operations. It replaces managers and coaches manually listening to
call recordings with automated, data-driven coaching. Each coach owns 15–25 agents
and cannot listen to every call. Two programs — **Telesales** and **WCC** (Winback
& Customer Care) — run on the same platform but use **different measurement
criteria**.

The output is a weekly per-agent report: a composite score out of 100, KPIs (key
performance indicators) across sales, retention, and customer experience, a 4-week
trend, AI coaching recommendations with practical steps, and risk flags, plus
breakdowns of escalations, sentiment, and sales.

This is an analytical, batch pipeline — it processes call after call and stores
results the dashboard reads. It is not a chat.

### Pipeline shape (our understanding — to confirm)

```
call recording
     │
     ▼
speech-to-text transcript  (+ metadata: agent_id, program, queue,
     │                        disposition, sales/CRM outcome)
     ▼
┌──────────────────────────────────────────────────────────────┐
│  LLM ANALYSIS PIPELINE (sequential)                           │
│                                                               │
│  (1) transcript prep / segmentation                           │
│           │                                                   │
│           ▼                                                   │
│  (2) dimension-analysis agents  (per program criteria)        │
│      sales effectiveness · customer experience · retention ·  │
│      compliance/script adherence · sentiment/escalation       │
│           │                                                   │
│           ▼                                                   │
│  (3) extraction agent  (escalations, sentiment, sales → JSON) │
│           │                                                   │
│           ▼                                                   │
│  (4) scoring / aggregation  (/100 composite, program-weighted)│
│           │                                                   │
│           ▼                                                   │
│  (5) trend computation  (analytical, not LLM, over 4 weeks)   │
│           │                                                   │
│           ▼                                                   │
│  (6) coaching-recommendation agent  (steps + risk flags)      │
└───────────┬──────────────────────────────────────────────────┘
            ▼
     results stored ──► dashboard (web app reads results)
```

### Steps

| Step | What it does | Model or logic | Tools / data used |
|---|---|---|---|
| 1. Transcript prep / segmentation | Cleans and splits the transcript into analyzable units | Light LLM or rule-based | Transcript store |
| 2. Dimension-analysis agents | Score each dimension against the program's criteria | LLM per dimension, program-specific prompt | Transcript, program rubric config |
| 3. Extraction agent | Pull escalations, sentiment, and sales outcomes into structured JSON | LLM with structured output | Transcript, call metadata |
| 4. Scoring / aggregation | Combine dimensions into the /100 composite using program weights | Deterministic (rubric math) | Program rubric config (per-program weights) |
| 5. Trend computation | Compare against the prior 4 weeks | Analytical, not LLM | Stored historical scores |
| 6. Coaching-recommendation agent | Write practical coaching steps and raise risk flags | LLM with rubric | Dimension results, extraction output |

### Data sources and tools

- Transcript store (speech-to-text output).
- Call-metadata store (agent_id, program, queue, disposition).
- Sales / CRM (customer relationship management) outcomes.
- Program rubric config — per-program weights for Telesales vs WCC.

APIX does little tool selection. What matters is **data-retrieval correctness**:
pulling the right transcript, the right metadata, and the right program rubric.

### What this use case exercises for evaluation & observability

- **Groundedness** — coaching must cite real transcript evidence, not invent
  moments or quotes.
- **Scoring-vs-human-QA agreement** — does the /100 track what a human QA (quality
  assurance) reviewer would give?
- **Extraction accuracy** — F1 on escalation, sentiment, and outcome extraction.
- **Coaching writing quality** — is the advice clear, complete, and useful?
- **Consistency / fairness** — comparable agents and sites scored comparably.
- **Operational** — cost and latency at "thousands of calls a day".

For observability, APIX produces long traces with many model calls per request
(one per dimension) and a mostly deterministic scoring step — good for testing
per-agent evaluation and cost tracking at volume.

## Hiring Intelligence

### What it is

Hiring Intelligence is AI-assisted, high-volume recruitment. It parses and ranks
résumés, runs screening question-and-answer, and produces a structured candidate
summary with a fit score — then a **human recruiter decides**. Unlike APIX, it
uses **tools via MCP (Model Context Protocol)** to read and write real systems
(the applicant tracking system, scheduling, and so on), which makes tool selection
a first-class concern.

### Pipeline shape (our understanding — to confirm)

```
new candidate / application
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│  AGENT PIPELINE (sequential)                                  │
│                                                               │
│  intake / router agent                                        │
│        │  (classify, route to the right requisition)          │
│        ▼                                                       │
│  résumé parse & rank agent                                    │
│        │  RAG over job description + rubric                    │
│        ▼                                                       │
│  screening Q&A agent                                          │
│        │  RAG over role / policy                               │
│        ▼                                                       │
│  scoring & summary agent                                      │
│        │  structured candidate summary + fit score            │
└────────┼──────────────────────────────────────────────────────┘
         ▼
  human recruiter decides
```

### Steps

| Step | What it does | Model or logic | Tools / data used (via MCP) |
|---|---|---|---|
| 1. Intake / router agent | Classify the application and route to the right requisition | LLM classification | Requisition DB, ATS read (MCP) |
| 2. Résumé parse & rank agent | Parse the résumé and rank against the role | LLM + RAG over job description and rubric | Résumé store, ATS read (MCP) |
| 3. Screening Q&A agent | Ask and interpret screening questions | LLM + RAG over role/policy | Policy/role docs, ATS write, scheduling/calendar (MCP) |
| 4. Scoring & summary agent | Produce a structured summary and fit score | LLM with structured output | Rank + screening results, ATS write (MCP) |

RAG = Retrieval-Augmented Generation; ATS = applicant tracking system.

### Data sources and tools

Tools are exposed through **MCP (Model Context Protocol)** servers:

- **ATS** (applicant tracking system) — read and write.
- **Requisition DB** — the open roles and their requirements.
- **Scheduling / calendar** — for setting up screening or interviews.
- **Résumé store** — the source documents.

Because an MCP server can expose several tools, **the agent must pick the correct
one with the correct arguments**. A fluent answer built on the wrong tool call is
unreliable — this is exactly the tool-selection problem the evaluation framework
treats as first-class.

### What this use case exercises for evaluation & observability

- **RAG groundedness / relevance** — answers grounded in the job description,
  rubric, and policy.
- **Ranking quality** — are the right candidates ranked highest?
- **Tool-selection accuracy** — did it call the right ATS/MCP tool, with the right
  arguments?
- **Summary writing quality** — is the candidate summary clear and complete?
- **Fairness / bias** — no bias in ranking; PII handled correctly.
- **Operational** — cost and latency at high volume.

For observability, Hiring is multi-turn (the screening Q&A) and tool-heavy, so it
tests session tracking and the **tool-call span** with its `expected_tool` and
`was_correct_tool` fields.

## Why these two together cover every metric group

Between them, APIX (analytical/batch, groundedness + structured scoring + writing
+ fairness) and Hiring (agentic-with-tools, tool selection + RAG + fairness)
exercise **every evaluation metric group**. That is the point: if the framework
handles both, it handles a future use case that looks like either — or a mix.

| Metric group | APIX exercises it via | Hiring exercises it via |
|---|---|---|
| Retrieval / RAG quality | Transcript/metadata retrieval correctness | RAG over job descriptions, rubrics, policy |
| Generation / writing quality | Coaching recommendations | Candidate summaries |
| Task execution / agentic (incl. tool selection) | Data-retrieval correctness (minor tool use) | Tool-selection accuracy + argument correctness (MCP) |
| Safety / compliance / fairness | Consistency across agents and sites | Bias in ranking; PII handling |
| Operational | Cost/latency at thousands of calls a day | Cost/latency at high recruitment volume |

Both are **sequential pipelines, not A2A** — so one operational setup (tracing,
evaluation, release) serves both, and the next use case as well.
