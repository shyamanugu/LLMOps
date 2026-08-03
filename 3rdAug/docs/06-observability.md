# Observability for LLM Applications

## Why normal application monitoring is not enough

Standard application performance monitoring tells you whether a request succeeded and how long it took. For an LLM application that is not enough — a request can return HTTP 200 in 800 milliseconds and still be wrong, ungrounded, or dangerously off-policy, and none of that shows up as an error. LLM observability adds a second layer on top of standard monitoring: it captures the actual prompt and completion, the tokens consumed, which model and which prompt version produced the answer, and — for agents — every intermediate tool call and hand-off between agents. Without that layer, "the bot said something wrong yesterday" is undebuggable; with it, you can open the exact trace, see the exact prompt version and retrieved context, and reproduce the failure.

## What to instrument

Every one of the following needs to be captured, not just "logged somewhere" but captured as structured, queryable telemetry attached to a trace:

| What | Fields to capture |
|---|---|
| **Every model call** | prompt, completion, prompt tokens, completion tokens, total cost, latency, model name + model version, prompt name + prompt version, use-case tag |
| **Every tool call** | tool name, input arguments, output/result, success/failure, latency |
| **Every agent hop** | which agent handed off to which agent, the reason/routing decision, the state passed along |
| **Sessions** | session id, user id (or anonymized equivalent), number of turns, session duration |
| **Feedback events** | thumbs up/down, edit made to the output, escalation to a human, retry, abandonment |

All of these are tied together by a **trace id** that is generated at the start of a user request and threaded through every span underneath it — the model call, the retrieval step, each tool call, each agent hop. That trace id is also the join key that lets a feedback event ("user gave this a thumbs down") point straight back to the exact model call, prompt version, and retrieved context that produced the response being complained about.

## Provider comparison

| Option | What it is | What it tracks | Hosting model | When to choose it |
|---|---|---|---|---|
| **Azure Monitor + Application Insights + Foundry tracing** | Azure-native monitoring stack, built on OpenTelemetry | Traces/spans per model and tool call, tokens, latency, errors, custom events; Microsoft Foundry links evaluation scores directly to the trace that produced them | Fully managed, data stays inside the Azure tenant | Default choice on an Azure-first stack; use as the system of record for everything, always on |
| **Langfuse** | Open-source LLM observability platform, can be self-hosted | Traces, generations, token cost per model, sessions/users, prompt versions, user feedback scores, evaluation scores, datasets | Self-hostable (e.g. on Azure Container Apps + Postgres), or Langfuse Cloud (software as a service, SaaS) | Best purpose-built LLM user experience; also does prompt management and dataset hosting; self-hosting keeps data in tenant while giving engineers a much better day-to-day debugging UI than raw Application Insights |
| **LangSmith** | SaaS observability platform from the LangChain team | Traces, runs, feedback, datasets, prompt hub, online evaluators | SaaS (data residency needs to be checked against compliance requirements) | Strong choice if the application is already built on LangChain or LangGraph — tightest integration there |
| **Arize Phoenix** | Open-source, OpenTelemetry-based observability tool | Traces, evaluations, embedding drift analysis | Self-hosted or Phoenix Cloud | Good when embedding/retrieval drift analysis is a priority, e.g. a RAG index that is expected to degrade as source documents age |
| **W&B Weave** | SaaS observability and evaluation tool from Weights & Biases | Traces, evaluations, cost | SaaS | If Weights & Biases is already the standard tool for the machine learning team (model training, experiment tracking) and adding LLM traces there avoids a second tool |
| **Datadog LLM Observability** | Module inside the existing Datadog SaaS platform | Traces, evaluations, cost, tied into the rest of Datadog's application monitoring | SaaS | If Datadog is already the company standard for infrastructure and application monitoring — keeps LLM traces next to everything else already being watched |

## Recommended lane: two layers, not one

Running two tools sounds redundant, but they answer different questions and both are cheap to add once the first one exists.

- **Layer 1 — Application Insights as the system of record.** Every model call, tool call, and agent hop is instrumented with the **OpenTelemetry GenAI semantic conventions** (the standardized attribute names for LLM spans — model name, token counts, etc.) and shipped to Application Insights. This is what compliance, security, and the platform team rely on: it is inside the Azure tenant, it is covered by existing retention and access policies, and it is what Microsoft Foundry reads when it links an evaluation score back to a trace.
- **Layer 2 — self-hosted Langfuse as the LLM-specific lens.** Deployed on Azure Container Apps with a Postgres database, Langfuse receives the same trace data (via its OpenTelemetry-compatible ingestion endpoint) and gives engineers a purpose-built UI: browse a session turn by turn, diff two prompt versions side by side, see cost broken down per model, attach feedback scores, and run ad-hoc evaluations against a dataset without writing a query. Because it is self-hosted, the data stays in the tenant, satisfying the same residency requirement as layer 1.

The two layers are not duplicated work — the same OpenTelemetry instrumentation emits to both destinations, so the engineering cost is "point the exporter at two endpoints," not "write two sets of instrumentation code."

## Instrumenting a model call (OpenTelemetry, Python)

```python
from opentelemetry import trace
from opentelemetry.trace import SpanKind

tracer = trace.get_tracer("billing-support-assistant")

def call_model(prompt_name, prompt_version, model_name, messages, use_case):
    with tracer.start_as_current_span(
        "gen_ai.chat", kind=SpanKind.CLIENT
    ) as span:
        span.set_attribute("gen_ai.system", "azure_openai")
        span.set_attribute("gen_ai.request.model", model_name)
        span.set_attribute("gen_ai.prompt.name", prompt_name)
        span.set_attribute("gen_ai.prompt.version", prompt_version)
        span.set_attribute("app.use_case", use_case)

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
        )

        usage = response.usage
        span.set_attribute("gen_ai.usage.prompt_tokens", usage.prompt_tokens)
        span.set_attribute("gen_ai.usage.completion_tokens", usage.completion_tokens)
        span.set_attribute("gen_ai.response.model", response.model)
        # cost is derived from token counts x the per-model price table
        span.set_attribute("app.cost_usd", estimate_cost(model_name, usage))

        return response
```

The same span attributes (prefixed `gen_ai.*`, which is the OpenTelemetry GenAI semantic convention namespace) are what both Application Insights and Langfuse's OpenTelemetry ingestion endpoint expect, which is why one instrumentation pass feeds both layers.

## Dashboards and alerts to stand up first

Do not try to build every dashboard on day one. Start with these, in order:

1. **Latency dashboard** — p50/p95 latency per use case, broken out by model call vs. retrieval vs. tool call, so a slowdown can be localized fast.
2. **Cost dashboard** — token cost per use case per day, model mix, so a runaway agent loop or an accidental model upgrade shows up immediately.
3. **Error rate dashboard** — tool-call failures, timeouts, model API errors, with alerting on a burn-rate threshold (a sustained rate that would exhaust the monthly error budget faster than planned).
4. **Quality trend** — evaluation scores over time per use case, so a slow quality decay is visible before a user complains.

Alerts to configure first: latency SLO burn-rate, cost budget threshold (50/80/100% of forecast), a spike in tool-call failure rate, and a drop in evaluation score on the nightly full eval run below the release-gate threshold used in CI.

## How traces link to evaluation scores in Foundry

When an evaluation run scores a model output — whether that is the CI-triggered offline run against the golden set, or an online evaluator scoring live traffic — the score is written back with the same trace id that produced the output being scored. Inside the Microsoft Foundry portal, opening a low-scoring evaluation result surfaces a direct link to the underlying trace: the exact prompt version, the exact retrieved context, the exact model response, and the token/cost/latency numbers for that single call. This turns "the groundedness metric dropped 4 points this week" into an actionable investigation — click through to the ten worst-scoring traces and see, in the actual retrieved context, what went wrong (usually either the retrieval missed the right chunk, or the prompt did not force the model to cite it). The same trace id also appears in Langfuse if the trace was exported there, so the same click-through works from either observability layer.
