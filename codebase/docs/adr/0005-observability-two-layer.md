# ADR 0005 — Two-layer observability (Application Insights + Langfuse), one emit

- Status: Accepted
- Date: 2026-08-06
- Deciders: Platform engineering

## Context

The client asked three exact questions about observability: what is tracked on *every
request*, are **model calls** tracked, are **tool calls** tracked, and are **agent
sessions** tracked. We need one trace per request with child spans (agent -> model/tool)
that roll up automatically, and we need cost visibility. There are two natural homes for
this telemetry: **Application Insights / Log Analytics** (the enterprise system of record,
queryable with KQL, reconciles against the Azure invoice) and **Langfuse** (an
LLM-focused lens with ready-made cost dashboards per model/prompt-version/user). Sending
telemetry to only one of them forces a choice between enterprise-grade querying and
LLM-native dashboards.

A risk with two sinks is double counting of cost, or two different definitions of cost.

## Decision

Instrument once with OpenTelemetry using the GenAI semantic conventions. Spans nest
request -> agent -> model/tool. Cost is computed **once, at emit**: each model-call span
sets `app.cost_usd = tokens x unit_price` (unit price from a price table keyed by
deployment, in `models/pricing.py`). The **same span** is exported to both Application
Insights and Langfuse via `observability/exporters.py`. Application Insights is the
aggregation/record source (cost by use case/day/model via KQL or a Workbook); Langfuse is
the ready-made dashboard view. There is no double counting — one attribute, two views —
and we reconcile monthly against Azure Cost Management (the actual invoice).

## Consequences

- Positive: every request, model call, tool call, and agent span is captured with a single
  instrumentation path; both an enterprise query surface and LLM-native dashboards.
- Positive: cost is defined in exactly one place and cannot diverge between the two sinks.
- Positive: `tool_call_span` records `eval.expected_tool`/`eval.was_correct_tool`, so
  offline tool-selection evaluation reads from the same trace shape as production.
- Negative: two export targets to configure and keep healthy; Langfuse must be
  self-hosted and maintained (~$50-150/mo infra).
- Negative: the price table must be kept current or `app.cost_usd` drifts from the invoice
  (monthly reconciliation catches this).
