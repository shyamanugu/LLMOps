# Observability Deep-Dive

This note answers, in detail, the four questions the client raised about observability:

1. What gets tracked for **every request**?
2. How are **model calls** tracked?
3. How are **tool calls** tracked?
4. How are **agent sessions** monitored?

Both use cases we are grounding this in — APIX (Afni Performance Intelligence Index) and Hiring Intelligence — are **agent pipelines**: a request flows through a fixed sequence of agents, one after another. There is no agent-to-agent negotiation. That sequential shape is exactly what makes tracing clean: each step is a node, and the nodes nest.

## 1. The mental model: a request is a trace, everything inside is a span

The single idea to hold onto: **one request becomes one trace, and every unit of work inside that request becomes a span.** A span is a timed, named record of one operation. Spans nest — a parent span (say, an agent step) contains child spans (its model call, its tool call). The whole nested set, sharing one `trace_id`, is the trace tree.

This is standard distributed-tracing thinking (the same model your web services already use), pointed at Large Language Model (LLM) pipelines. Because the pipeline is sequential, the tree reads top-to-bottom exactly like the pipeline runs.

Here is one APIX request — analyzing a single call recording — as a trace tree:

```
Request (trace_id=apix-7f3a…)  use_case=apix  program=telesales  input=call_88421
  └─ Pipeline run
       ├─ Agent 1: transcript-prep            (span)
       │    └─ model call: gpt-4o segment      (span)
       ├─ Agent 2: dimension-sales-eff         (span)
       │    └─ model call: gpt-4o analyze       (span)
       ├─ Agent 3: dimension-customer-exp       (span)
       │    └─ model call: gpt-4o analyze       (span)
       ├─ Agent 4: extraction                   (span)
       │    ├─ model call: gpt-4o extract        (span)
       │    └─ tool call: crm.get_outcome        (span)
       ├─ Agent 5: scoring-aggregation          (span)   [analytical, no model]
       ├─ Agent 6: trend-compute                (span)   [analytical, no model]
       ├─ Agent 7: coaching-recommendation       (span)
       │    └─ model call: gpt-4o coach          (span)
       └─ Final output → stored → dashboard
```

Every box above is one row in our telemetry with a start time, a duration, a status, and its own fields. Read the tree top-down and you can see exactly what happened, what it cost, and where it broke.

## 2. What is captured at each level

Each span level records a specific set of fields. The tables below expand the capture list with the data type and, more importantly, *why we keep it*. These are the fields our instrumentation is required to set.

### Request / trace (one row per request)

This is the row that answers "what gets tracked for **every request**".

| Field | Type | Why it matters |
|---|---|---|
| `trace_id` | string | The join key. Every span, feedback event, and evaluation score links back to this. |
| `use_case` | enum (apix / hiring) | Lets us slice cost, latency, quality by product line. |
| `program` | enum (telesales / wcc / role) | APIX Telesales and WCC (Warranty Contact Center) use different rubrics; Hiring differs by requisition. Must slice on this. |
| `timestamp` | datetime | Ordering, drift analysis over time. |
| `input_ref` | string | `call_id` (APIX) or `candidate_id` (Hiring). Points to the source, not the raw content. |
| `output_ref` | string | Where the result landed (score row, candidate summary). |
| `status` | enum (ok / error / partial) | Top-level health of the request. |
| `total_latency_ms` | int | End-to-end time. Feeds Service Level Objectives and the APIX volume story. |
| `total_tokens` | int | Sum across all model calls. Drives cost. |
| `total_cost_usd` | decimal | Rolled up from child model-call spans. FinOps join key. |
| `agents_run` | int | How many pipeline steps executed. Catches short-circuits. |
| `human_intervention` | bool | Was a person in the loop (coach edit, recruiter override)? Important for governance reporting. |

### Agent span (one per pipeline step)

| Field | Type | Why it matters |
|---|---|---|
| `span_id` | string | This span's identity. |
| `parent` / `trace_id` | string | Ties it into the tree. |
| `agent_name` | string | Which step (e.g. `dimension-sales-eff`). |
| `agent_version` | string | We version agents; a regression must be attributable to a version. |
| `role` | string | What this step is responsible for. |
| `input` / `output` | text or ref | The handoff content (redacted/hashed if it carries PII — see section 6). |
| `models_used` | list | Which deployments this step invoked. |
| `tools_used` | list | Which tools this step invoked. |
| `model_calls` / `tool_calls` | int | Counts, for quick anomaly spotting. |
| `latency_ms`, `tokens`, `cost_usd` | numeric | Per-step performance and cost. Finds the expensive step. |
| `status` | enum | Step-level health. |
| `next_agent` | string | The handoff target — reconstructs the pipeline path for path-correctness evaluation. |

### Model-call span

This answers "how are **model calls** tracked". One span per LLM invocation.

| Field | Type | Why it matters |
|---|---|---|
| `model_name` | string | e.g. `gpt-4o`. |
| `model_version` | string | Provider model version; a silent version bump can move quality. |
| `deployment` | string | The Azure OpenAI deployment name actually hit. |
| `prompt_id` + `prompt_version` | string | Which prompt template and which revision. Ties output changes to prompt changes. |
| `system_prompt` + `user_prompt` | text **or hash** | Full text in non-PII cases; salted hash when the prompt embeds candidate or customer data. |
| `completion` | text or ref | Model output (same PII rule). |
| `prompt_tokens` / `completion_tokens` | int | Cost and context-budget tracking. |
| `cost_usd` | decimal | Per-call cost, priced from tokens × model rate. |
| `latency_ms` | int | Model responsiveness; separates model time from tool/network time. |
| `temperature` | float | Reproducibility; explains output variance. |
| `finish_reason` | enum (stop / length / filter) | `length` means truncation; `filter` means a safety block — both are quality signals. |
| `cache_hit` | bool | Prompt-cache hits cut cost and latency; we want to see the hit rate. |

### Tool-call span

This answers "how are **tool calls** tracked". One span per tool invocation — the ATS (Applicant Tracking System) read/write in Hiring, or the CRM outcome lookup in APIX.

| Field | Type | Why it matters |
|---|---|---|
| `tool_name` | string | Which tool was actually called. |
| `mcp_server` | string | Which MCP (Model Context Protocol) server exposed it. |
| `input_args` | json | The arguments the model chose. Feeds argument-correctness checks. |
| `result` | json or ref | What came back. |
| `success` / `error` | bool | Did the call work? |
| `error_msg` | string | Failure detail for debugging. |
| `latency_ms` | int | Tool/backend responsiveness. |
| `expected_tool` | string | In evaluation runs, the tool that *should* have been chosen for this case. |
| `was_correct_tool` | bool | Whether the selected tool matched `expected_tool`. |

The last two fields are the ones the client specifically probed. When an MCP server exposes several tools, a fluent answer built on the **wrong** tool is unreliable. So on every evaluation-run trace we record what the agent picked next to what it should have picked. Aggregating `was_correct_tool` across a golden dataset gives us **tool-selection accuracy**, plus per-tool precision and recall, wrong-tool rate, unnecessary-call rate, and missing-call rate. These fields are the raw feed for that evaluator — captured at the trace level, scored downstream in custom Python.

### Session (multi-turn)

Some flows are conversational — the Hiring screening Question-and-Answer exchange with a candidate is several turns. A session groups those turns.

| Field | Type | Why it matters |
|---|---|---|
| `session_id` | string | Links all turns (each turn is its own trace). |
| `conversation_history` | list of refs | The ordered turns. |
| `user_id` | **hashed** string | Who the session belongs to, without storing identity in the clear. |
| `total_turns` | int | Length; runaway sessions are a signal. |
| `outcome` | enum | Where the session ended (advanced / rejected / scheduled). |

This is how "agent **sessions** are monitored": a `session_id` fans out to per-turn traces, and each turn carries the full agent/model/tool span tree above. Session-level views (turn count, outcome, drop-off) sit on top of trace-level detail.

### Feedback events

Feedback is captured as its own event, linked by `trace_id`: thumbs up/down plus a reason, coach edits to a generated APIX report, recruiter overrides of a Hiring recommendation. Because it shares the trace id, we can later pull the exact prompt, model, and tool decisions that produced a rejected output — that is the raw material for the golden datasets.

## 3. How it is implemented on Azure

We keep data in Afni's tenant and use open standards so we are not locked to one vendor.

- **OpenTelemetry with GenAI semantic conventions** is the instrumentation standard. Every span above is an OpenTelemetry span with the GenAI attribute names (`gen_ai.request.model`, `gen_ai.usage.input_tokens`, and so on). One vocabulary across both pipelines.
- **Azure Application Insights + Log Analytics** is the system of record. All spans land here; the data stays in tenant, queryable with Kusto Query Language, and drives the Azure Monitor dashboards and alerts.
- **Self-hosted Langfuse** (on Azure Container Apps, backed by Azure Database for PostgreSQL) is the LLM-specific lens: cost per model, prompt-version diffs, per-trace evaluation scores, and dataset runs. Self-hosting keeps prompts and completions inside the tenant.
- **Azure AI Foundry tracing** links evaluation scores back to the exact trace, so a low groundedness score is one click from the spans that produced it.

Here is the instrumentation pattern — a span around a model call and around a tool call, with the key attributes set:

```python
from opentelemetry import trace

tracer = trace.get_tracer("apix.pipeline")

# --- model call span ---
with tracer.start_as_current_span("model_call") as span:
    span.set_attribute("gen_ai.system", "azure_openai")
    span.set_attribute("gen_ai.request.model", "gpt-4o")
    span.set_attribute("gen_ai.request.temperature", 0.2)
    span.set_attribute("prompt.id", "coaching_v7")
    span.set_attribute("prompt.version", "7")
    resp = client.chat.completions.create(...)
    span.set_attribute("gen_ai.usage.input_tokens", resp.usage.prompt_tokens)
    span.set_attribute("gen_ai.usage.output_tokens", resp.usage.completion_tokens)
    span.set_attribute("gen_ai.response.finish_reason",
                       resp.choices[0].finish_reason)

# --- tool call span ---
with tracer.start_as_current_span("tool_call") as span:
    span.set_attribute("tool.name", "ats.get_candidate")
    span.set_attribute("mcp.server", "hiring-ats")
    span.set_attribute("tool.input_args", json.dumps(args))
    span.set_attribute("tool.expected_tool", "ats.get_candidate")  # eval runs
    result = call_tool(args)
    span.set_attribute("tool.success", result.ok)
    span.set_attribute("tool.was_correct_tool",
                       "ats.get_candidate" == expected_tool)
```

Wrapping each agent step the same way builds the full tree automatically, because OpenTelemetry nests spans by their active context.

## 4. Worked examples

**APIX — analyze one call.** Request `apix-7f3a` opens the trace (`use_case=apix`, `program=telesales`, `input_ref=call_88421`). Agent 1 (transcript-prep) runs a model call that segments the transcript — its span records `gpt-4o`, prompt `segment_v3`, 1,200 prompt tokens, `finish_reason=stop`. Agents 2–3 (dimension analyzers) each emit a model-call span citing transcript evidence. Agent 4 (extraction) emits a model-call span *and* a tool-call span (`crm.get_outcome`, args `{call_id: 88421}`, success). Agents 5–6 are analytical — spans with latency but no model. Agent 7 (coaching) emits the final model-call span, prompt `coaching_v7`. The trace closes with `total_tokens`, `total_cost_usd`, `total_latency_ms`, `agents_run=7`. A coach later edits the report — that lands as a feedback event on `apix-7f3a`.

**Hiring — screen one candidate.** Request `hire-2c91` opens (`use_case=hiring`, `input_ref=cand_5567`). The résumé-rank agent runs a RAG (Retrieval-Augmented Generation) model call over the job description and rubric — its span shows retrieved context and the fit reasoning. Then a tool-call span fires: `ats.get_candidate` on the `hiring-ats` MCP server, args `{req_id: R-204, candidate: cand_5567}`. On an evaluation trace this span also carries `expected_tool=ats.get_candidate` and `was_correct_tool=true`; had the agent called `ats.search` instead, the flag would read false and the tool-selection evaluator would count it as a wrong-tool pick. The scoring/summary agent produces the candidate summary; a recruiter override, if any, attaches as a feedback event.

## 5. Dashboards and alerts to stand up first

| Panel | What it shows | Source |
|---|---|---|
| Request health | Volume, error rate, partial rate by use_case/program | App Insights / Log Analytics |
| Latency | p50/p95/p99 end-to-end and per agent step | App Insights |
| Cost per request | total_cost_usd rolled from model spans; by model and program | Langfuse + App Insights |
| Token usage | Prompt vs completion tokens; cache-hit rate | Langfuse |
| Tool reliability | Tool success/error rate, tool latency by mcp_server | App Insights |
| Tool-selection accuracy | was_correct_tool aggregate on eval runs | Langfuse / Foundry |
| Quality trend | Groundedness, writing, scoring-agreement over time | Foundry (trace-linked) |
| Feedback | Thumbs, coach edits, recruiter overrides by trace | Langfuse |

Alerts to wire from day one: error rate over threshold, p95 latency breach, cost-per-request spike, tool error-rate spike, `finish_reason=length` rate climbing (truncation), and online groundedness dropping below baseline.

**Link to cost (FinOps).** Every model-call span carries tokens and a priced `cost_usd`; those roll up to the trace and then group by model, program, and agent. That is the FinOps view — we can say what a single APIX report or Hiring screen costs, and where the spend concentrates.

**Link to evaluation.** Evaluation scores are written back against the `trace_id`. So a failing groundedness score on an APIX coaching report opens straight to the coaching agent's model-call span — the exact prompt, model version, and cited transcript — with no guesswork. Traces are the connective tissue between quality, cost, and behavior.

## 6. PII handling in traces

Prompts and completions in both use cases can contain Personally Identifiable Information (PII) — customer details in APIX transcripts, candidate details in Hiring résumés. We do not store that in the clear in telemetry.

- **Redaction before export.** A processor scrubs known PII patterns (names, emails, phone numbers, account/candidate IDs) from prompt and completion attributes before spans leave the process.
- **Hashing where linkage is needed.** Fields like `user_id` are stored as salted hashes — we can group a person's sessions without holding their identity.
- **References, not payloads.** `input_ref` / `output_ref` point to governed stores; the raw transcript or résumé lives behind access control, not in the trace.
- **Self-hosting.** Langfuse and Application Insights both run inside Afni's tenant, so even redacted telemetry never leaves Afni's boundary. Sensitive-field access is itself audited.

The rule of thumb: a trace should tell you *what happened and how well* without exposing *who it was about* to anyone reading the dashboard.
