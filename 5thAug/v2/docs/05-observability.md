# Observability

Kiran asked four blunt questions, and this note answers them head-on, in order:

1. What gets tracked on **every request**?
2. How are **model calls** tracked?
3. How are **tool calls** tracked?
4. How are **agent sessions** tracked?

## Today, our setup, what changes

| | Today (assumption — to confirm) | Our setup | What changes |
|---|---|---|---|
| What we can see | Application logs — text lines, per service | A full trace tree per request | We move from scattered log lines to one connected picture per request |
| Model calls | A log line, maybe, with no token or cost detail | A span per call with model, prompt version, tokens, cost | Every model call is measured, not just mentioned |
| Tool calls | Usually invisible | A span per call with tool name, MCP server, arguments, status | Tool behaviour becomes observable and gradable |
| Cost | Estimated from the monthly Azure bill | Priced per call, rolled up per request | We can say what a single APIX report costs |
| Where it lives | Split across service logs | Azure Application Insights (system of record) + self-hosted Langfuse (LLM lens), both in Afni's tenant | One system of record, in tenant, plus an LLM-focused view |

## The mental model: a request is a trace, everything inside is a span

Hold onto one idea: **one request becomes one trace, and every unit of work inside that request becomes a span.** A span is a timed, named record of one operation — an agent step, a model call, a tool call. Spans nest: a parent agent span contains its child model-call and tool-call spans. The whole nested set shares one `trace_id`, and that is the trace tree.

This is standard distributed-tracing thinking — the same model Afni's web services already use — pointed at a Large Language Model (LLM) pipeline. Because APIX and Hiring Intelligence are sequential agent pipelines (no agent-to-agent negotiation), the tree reads top-to-bottom exactly the way the pipeline runs.

Here is one APIX request — analysing a single call recording — as a trace tree:

```
Request (trace_id=apix-7f3a…)  use_case=apix  program=telesales  input_ref=call_88421
  └─ Pipeline run
       ├─ Agent 1: transcript-prep            (span)
       │    └─ gen_ai.chat  alias=bulk         (span)
       ├─ Agent 2: dimension-sales-eff         (span)
       │    └─ gen_ai.chat  alias=reason        (span)
       ├─ Agent 3: dimension-customer-exp       (span)
       │    └─ gen_ai.chat  alias=reason        (span)
       ├─ Agent 4: extraction                   (span)
       │    ├─ gen_ai.chat  alias=bulk           (span)
       │    └─ tool.call  crm.get_outcome         (span)
       ├─ Agent 5: scoring-aggregation          (span)   [analytical, no model]
       ├─ Agent 6: coaching-recommendation       (span)
       │    └─ gen_ai.chat  alias=reason          (span)
       └─ Final output → stored → dashboard
```

Every box is one row in our telemetry, with a start time, a duration, a status, and its own fields. Read the tree top-down and you can see exactly what happened, what it cost, and where it broke.

## The instrumentation

Two small wrappers set the spans and their attributes. This is the exact code that runs.

```python
from opentelemetry import trace
tracer = trace.get_tracer("apix.pipeline")

def call_model(alias, prompt_id, messages, env):
    with tracer.start_as_current_span("gen_ai.chat") as sp:
        deployment = resolve(alias, env)
        sp.set_attribute("gen_ai.system", "azure_openai")
        sp.set_attribute("gen_ai.request.model", deployment)
        sp.set_attribute("app.prompt_id", prompt_id)
        sp.set_attribute("app.prompt_version", version_of(prompt_id))
        sp.set_attribute("app.use_case", "apix")
        resp = client.chat.completions.create(model=deployment, messages=messages)
        u = resp.usage
        sp.set_attribute("gen_ai.usage.input_tokens", u.prompt_tokens)
        sp.set_attribute("gen_ai.usage.output_tokens", u.completion_tokens)
        sp.set_attribute("app.cost_usd", cost(deployment, u))
        return resp

def call_tool(name, mcp_server, args, expected=None):
    with tracer.start_as_current_span("tool.call") as sp:
        sp.set_attribute("tool.name", name)
        sp.set_attribute("tool.mcp_server", mcp_server)
        sp.set_attribute("tool.args", redact(args))
        if expected is not None:
            sp.set_attribute("eval.expected_tool", expected)
            sp.set_attribute("eval.was_correct_tool", name == expected)
        result = mcp.invoke(name, args)
        sp.set_attribute("tool.status", result.status)
        return result
```

Attribute by attribute:

- `gen_ai.system` — the provider, `azure_openai`. One vocabulary across both pipelines.
- `gen_ai.request.model` — the **resolved deployment** (from `resolve(alias, env)`). The trace shows the concrete model even though the code only named an alias.
- `app.prompt_id` + `app.prompt_version` — which prompt template and revision produced this call. This is the link that ties an output change back to a prompt change.
- `app.use_case` — the product line, for slicing cost and quality per use case.
- `gen_ai.usage.input_tokens` / `output_tokens` — token counts, straight from the API response usage.
- `app.cost_usd` — per-call cost, priced from tokens times the model rate. This is what rolls up to the request cost.
- `tool.name` — which tool was actually called.
- `tool.mcp_server` — which Model Context Protocol (MCP) server exposed it.
- `tool.args` — the arguments the model chose, **after redaction** (see PII section).
- `eval.expected_tool` + `eval.was_correct_tool` — set only on evaluation runs: the tool that should have been chosen, and whether the agent chose it. These two feed tool-selection accuracy.
- `tool.status` — did the call succeed.

Wrapping each agent step the same way builds the whole tree automatically, because OpenTelemetry nests spans by the active context.

## What gets tracked on every request

The top-level trace row is what answers "every request". These fields are set once per request and roll up from the children.

| Level | Fields captured |
|---|---|
| **Request / trace** | `trace_id`, `use_case`, `program`, `timestamp`, `input_ref`, `output_ref`, `status`, `total_latency_ms`, `total_tokens`, `total_cost_usd`, `agents_run`, `human_intervention` |
| **Agent step** | `span_id`, `parent`/`trace_id`, `agent_name`, `agent_version`, `input`/`output` (redacted), `models_used`, `tools_used`, `latency_ms`, `tokens`, `cost_usd`, `status`, `next_agent` |
| **Model call** | `gen_ai.system`, `gen_ai.request.model` (resolved deployment), `app.prompt_id`, `app.prompt_version`, `app.use_case`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `app.cost_usd`, `latency_ms`, `finish_reason` |
| **Tool call** | `tool.name`, `tool.mcp_server`, `tool.args` (redacted), `tool.status`, `latency_ms`, `eval.expected_tool`, `eval.was_correct_tool` |
| **Session** | `session_id`, `conversation_history` (turn refs), `user_id` (hashed), `total_turns`, `outcome` |
| **Feedback** | `trace_id` (link), `rating`, `reason`, `edit_diff`, `actor` (hashed) |

`input_ref` and `output_ref` point at the source (a `call_id`, a `candidate_id`) — a reference, never the raw transcript or résumé. `human_intervention` records whether a coach or recruiter was in the loop, which governance reporting needs.

## How model calls are tracked

One `gen_ai.chat` span per LLM invocation, produced by `call_model` above. It records the resolved deployment, the prompt id and version, input and output tokens, the priced cost, latency, and `finish_reason` (a `length` finish means truncation; a `filter` finish means a safety block — both are quality signals). Because the deployment is the resolved name and the prompt version is stamped, a model-call span is enough to reproduce and explain any output: which model, which prompt revision, how many tokens, what it cost.

## How tool calls are tracked

One `tool.call` span per tool invocation — the CRM outcome lookup in APIX, the Applicant Tracking System read in Hiring. It records the tool name, the MCP server that exposed it, the (redacted) arguments the model chose, and the status. On evaluation runs it also carries `eval.expected_tool` and `eval.was_correct_tool`. This is the part Kiran probed specifically: when an MCP server exposes several tools, a fluent answer built on the **wrong** tool is unreliable. Aggregating `eval.was_correct_tool` across a golden dataset gives tool-selection accuracy, wrong-tool rate, and missing-tool rate — the raw feed the custom Python evaluator scores downstream.

## How agent sessions are tracked

Some flows are multi-turn — a Hiring screening exchange with a candidate is several turns. A `session_id` groups those turns; each turn is its own trace carrying the full agent/model/tool span tree above. Session-level views (turn count, outcome, drop-off) sit on top of the per-turn detail. The `user_id` on a session is stored **hashed**, so we can group one person's sessions without holding their identity in the clear. That is what "agent hub sessions are tracked" means concretely: a session fans out to per-turn traces, and every turn is fully instrumented.

## How it runs on Azure

We use open standards and keep data in Afni's tenant.

- **OpenTelemetry with GenAI semantic conventions** is the instrumentation standard. Every span above uses the GenAI attribute names (`gen_ai.request.model`, `gen_ai.usage.input_tokens`, and so on) — one vocabulary across both pipelines.
- **Azure Application Insights + Log Analytics** is the **system of record**. All spans land here, the data stays in tenant, it is queryable with Kusto Query Language, and it drives the Azure Monitor dashboards and alerts.
- **Self-hosted Langfuse** (on Azure Container Apps, backed by Azure Database for PostgreSQL) is the **LLM lens**: token and cost dashboards, prompt-version diffs, and per-trace evaluation scores. Self-hosting keeps prompts and completions inside the tenant.

**Link to cost.** Every `gen_ai.chat` span carries `app.cost_usd`; those roll up to `total_cost_usd` on the trace, then group by model, program, and agent. That is the FinOps view — we can state what one APIX report or one Hiring screen costs and where spend concentrates.

**Link to evaluation.** Evaluation scores are written back against the `trace_id`. So a failing groundedness score on an APIX coaching report opens straight to the coaching agent's model-call span — the exact prompt version, resolved model, and cited evidence — with no guesswork. Traces are the connective tissue between quality, cost, and behaviour.

## PII in traces

Prompts and completions here can contain Personally Identifiable Information (PII) — customer details in APIX transcripts, candidate details in Hiring résumés. We do not store that in the clear.

- **Redaction before export.** A processor scrubs known PII patterns (names, emails, phone numbers, account and candidate IDs) from prompt, completion, and `tool.args` attributes before spans leave the process — which is why `call_tool` wraps arguments in `redact(...)`.
- **Hashing where linkage is needed.** `user_id` and any actor field are salted hashes, so sessions and feedback group by person without exposing identity.
- **References, not payloads.** `input_ref` / `output_ref` point at governed stores; the raw transcript or résumé stays behind access control, not in the trace.
- **In tenant.** Both Application Insights and Langfuse run inside Afni's tenant, so even redacted telemetry never leaves Afni's boundary.

The rule of thumb: a trace should tell you *what happened and how well* without exposing *who it was about* to anyone reading the dashboard.
