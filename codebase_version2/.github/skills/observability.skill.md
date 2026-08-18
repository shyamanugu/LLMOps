# Observability

**What it is** — A record of what happened on every request and step: model calls and tool calls
with tokens, cost, and latency, all tied to one request id (a trace). This is how a bad answer is
traced back to the exact step and how cost-per-request is known.

**When to use** — Always on. Every request runs inside a trace; every model and tool call is
recorded. Add a `span` around any new step you want timed and attributed.

**How it works here** — `framework/observability.py`:
- `start_trace(use_case="")` begins a request trace and sets the current trace id. The pipeline
  calls this once per run.
- `span(name, **attrs)` is a context manager that times a step and emits a `span` record.
- `record_model_call(alias, model, tokens_in, tokens_out, cost_usd, latency_ms, prompt_id=None)` —
  called automatically by `model_management.chat`.
- `record_tool_call(name, ok, latency_ms, expected_tool=None, **attrs)` — called by tools;
  `expected_tool` lets evaluation check tool selection (`was_correct_tool`).
- `_emit` prints one structured JSON line per record (→ App Insights / Log Analytics in Azure).
  If `LANGFUSE_HOST` is set, `_send_langfuse` also forwards it (currently a `# TODO(wiring)` stub).

**Key files** — `framework/observability.py`, `framework/config.py` (`LANGFUSE_*`),
`framework/model_management.py` and `framework/tools.py` (callers).

**Example**
```python
from framework import observability as obs
obs.start_trace("example_qa")
with obs.span("retrieve"):
    docs = tools.search_knowledge("example_qa", question)
# model + tool calls are recorded for you; cost_usd rides along on each model record
```

**Pitfalls**
- Using `print` in framework code instead of observability — all telemetry goes through `_emit`.
- Doing work outside a trace/span — it won't be attributable.
- Expecting Langfuse offline — by default records are console JSON lines; Langfuse is opt-in via
  `LANGFUSE_HOST`.
- Dropping `prompt_id` on a model call — you lose the link from answer back to prompt.
