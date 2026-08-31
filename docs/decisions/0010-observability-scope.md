# ADR 0010: Observability — tracer seam added to Orchestration, config left unwired

## Status
Accepted

## Context
Orchestration's `State` has generated a `session_id` since it was built, with its own README noting it was "threaded through State, emitted nowhere yet." Unlike Prompt Management, Data & Tools, and Guardrails — which all plugged into a parameter (`prompt_name`, `ToolRegistry`, `guardrail`) Orchestration already had — there was no existing hook to record a trace or cost event through. This component had to decide both what an event looks like and how Orchestration should expose the ability to emit one.

## Decision
1. **`ModelStep` and `Pipeline` both gain a `tracer` parameter**, defaulting to `NullTracer` — a genuine, small addition to Orchestration (08), not a workaround. This is expected and different in kind from every prior integration: this is the one seam that didn't exist as a parameter before this component was built.
2. **`StepEvent`/`PipelineEvent` are plain dataclasses**, not imported by Orchestration from anywhere else — Orchestration imports them directly from this component (`observability.types`), the same way it already imports `PromptRegistry` from Prompt Management and `ModelProvider` from Model Management. This is consistent with the established direction: components never import Orchestration, Orchestration imports the components filling its seams.
3. **Cost computation reads Model Management's `pricing.yaml` directly** (`compute_cost()`), rather than duplicating pricing figures — that file's own header comment already named this component as its intended reader.
4. **Pipeline does not recompute cost/latency roll-ups across steps.** Each step's own tracer records its own `StepEvent` independently; summing them into a pipeline total is a query against whatever tracer backend is in use, not logic duplicated in `Pipeline`. An earlier draft had `Pipeline` reach into each step's tracer internals to sum `cost_usd` — rejected during review as fragile (silently wrong for any tracer type other than `InMemoryTracer`, and dependent on `Step`-shaped objects happening to expose the same internal structure `ModelStep` does).
5. **`AzureMonitorTracer` ships events via `opencensus`'s `AzureLogHandler`** attached to a standard Python logger, not a hand-rolled call to Application Insights' ingestion REST API. The exact JSON envelope for that REST API wasn't confidently known at the time of writing; `opencensus-ext-azure`'s logging-handler pattern is well-documented and stable, consistent with this platform's standard of only authoring integrations against a verified shape (see ADR 0009's reasoning for the same call on Content Safety's Prompt Shields).
6. **`config/observability.yaml` (per-environment tracer selection) is informational, not auto-consumed.** No function in this component reads it. `ModelStep`/`Pipeline` take a `tracer` instance directly; whatever wires a usecase's pipeline together decides which tracer to construct. Building an auto-wiring function now would guess at a calling convention no usecase has established yet.

## Alternatives Considered
- **A hand-rolled Application Insights Track API client** (raw REST envelope): rejected — the exact schema wasn't verified with enough confidence to author against it directly, per the standing "don't fabricate unverified integrations" principle.
- **Recomputing pipeline-level cost by inspecting each step's tracer**: rejected after being drafted — see Decision point 4. Correct only by coincidence for `InMemoryTracer`, silently wrong for anything else.
- **Auto-wiring `config/observability.yaml` into a factory function** (`build_tracer(environment)`, mirroring `build_guardrail()`): rejected for now — Guardrails' config-to-object mapping mirrors a real, already-used calling convention (`ModelStep.guardrail` accepting one object). Tracing has no established usecase calling convention yet to mirror; the config file documents intent for a human wiring things together, not a function to build blindly ahead of a real caller.

## Consequences
- Orchestration gained two new constructor parameters (`ModelStep.tracer`, `Pipeline.tracer`) as a direct, deliberate result of this component — flagged here so it's understood as an intentional exception to "components never require Orchestration changes," not scope creep.
- A pipeline's total cost/latency isn't a single field to read off `PipelineEvent` — it requires summing `InMemoryTracer.step_events` or querying Log Analytics, a real but small extra step for whoever consumes this data.
- `config/observability.yaml` currently has no code path reading it — it risks going stale as documentation-only until a real `build_tracer()`-style function is justified by an actual usecase calling convention.

## Revisit When
- A real usecase establishes a calling convention for choosing a tracer (e.g., every usecase's entrypoint reads `config/observability.yaml` the same way) — build `build_tracer(environment)` at that point, mirroring `build_guardrail()`.
- Someone verifies the Application Insights Track API's exact envelope shape against a live resource — consider a lighter-weight direct REST client as an alternative to `opencensus-ext-azure`, if the dependency footprint becomes a concern.
- A usecase needs pipeline-level cost as a queryable field rather than a derived sum — reconsider whether `Pipeline` should own that aggregation after all, informed by whatever that usecase's actual access pattern looks like.
