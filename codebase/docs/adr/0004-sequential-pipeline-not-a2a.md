# ADR 0004 — Sequential agent pipelines, not agent-to-agent (A2A)

- Status: Accepted
- Date: 2026-08-06
- Deciders: Platform engineering

## Context

Both current use cases (APIX, Hiring Intelligence) are, at heart, ordered sequences of
steps: for APIX, transcript -> per-dimension analysis -> extraction -> scoring -> coaching
report; for Hiring, intake -> resume rank -> screening -> summary. The v2 brief states
plainly that these are **sequential agent pipelines, not agent-to-agent**. An
agent-to-agent (A2A) design — autonomous agents negotiating and delegating to each other
at run time — is powerful but harder to make deterministic, harder to evaluate (the
task-path is not fixed), harder to trace cleanly, and harder to reason about for cost and
safety. For enterprise use cases where the steps are known, that non-determinism is a
liability, not a feature.

## Decision

The orchestration runtime executes a **fixed, ordered list of steps** defined in
`usecases/<uc>/agents/pipeline.agent.yaml`. `Pipeline.run(input)` runs steps in sequence;
each `Step` wraps an `Agent` (or a plain function), and each agent has a `prompt_id`,
declared `tools`, and a `model_alias`. Data flows forward through a shared
`PipelineContext`. Spans nest request -> agent -> model/tool so a trace mirrors the
pipeline exactly. State can be checkpointed to Cosmos DB for resume (in-memory default in
dev).

## Consequences

- Positive: deterministic, inspectable task-path; the evaluation gate can assert the
  expected tool at each step (`tool_selection` metric) because the path is known.
- Positive: traces map one-to-one to pipeline steps, making debugging and cost attribution
  straightforward; checkpoint/resume is well-defined.
- Positive: simpler mental model and safer blast radius per step for guardrails.
- Negative: dynamic problems that genuinely need run-time delegation are not expressible;
  those would require a different (A2A) runtime.
- Negative: branching/looping is limited to what the step model supports; complex control
  flow must be encoded as explicit steps.
- Note: this does not preclude adopting a managed agent runtime (e.g. Foundry Agent
  Service) later for hosting; the *sequential* contract is what is fixed here.
