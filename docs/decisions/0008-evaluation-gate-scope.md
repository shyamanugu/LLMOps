# ADR 0008: Evaluation Gate — strict default threshold, callable-based system-under-test, library-first

## Status
Accepted

## Context
Every prior ADR in this platform (0001, 0004, 0005, 0006, 0007) has referred to a change becoming safe to ship only after it's "reviewed and gated," without that gate existing yet. This component is that gate: given a golden dataset and a way to produce actual outputs, score and decide pass/fail.

Two open questions needed resolving before building it: how a "system under test" gets invoked (a hard dependency on Orchestration's `Pipeline`, or something looser), and what the default pass threshold should be given golden-dataset cases are meant to be curated rather than a representative sample.

## Decision
1. **`system_under_test` is a plain callable** (`EvalCase -> Any`), supplied by the caller — this component has no import dependency on Orchestration (08). A caller wraps `pipeline.run(...)` in a lambda when testing a full pipeline, or passes something narrower (a single prompt render, a single model call) when that's all that's being evaluated. This keeps the harness usable for testing any granularity of change, and avoids a dependency that would only exist to serve one calling pattern.
2. **Default pass threshold is 100%** (every case must pass), overridable per usecase per environment in `config/gates.yaml`. Golden-dataset cases are assumed curated and critical, not a statistical sample where some failure rate is tolerable — a softer default would quietly normalize "most of the critical cases pass" as good enough.
3. **Three evaluators**: `ExactMatchEvaluator` (deterministic fields), `SchemaEvaluator` (validates against Prompt Management's `output_schema`, its first real consumer), `LLMJudgeEvaluator` (rubric-based scoring via the `judge` alias, for anything not exact-match-able). Each case declares its evaluator explicitly.
4. **No semantic-similarity evaluator built now** — the three above cover every case shape asked for; a fourth is additive later if a usecase needs it.
5. **Library only, no CI/CD wiring** — CI/CD (component 09) doesn't exist yet, so there's nothing real to wire this into. The integration plan is documented in `platform/services/04-evaluation-gate/README.md`'s "Future CI/CD integration" section ahead of the work, same posture as ADR 0005 for Orchestration.

## Alternatives Considered
- **Hard dependency on Orchestration's `Pipeline` type** (accept a `Pipeline` + `State` directly instead of a callable): rejected — it would force every use of this gate through a full pipeline run, even when only a single prompt or model swap is being evaluated, and would create a dependency in the direction opposite to how Orchestration already depends on Model Management and Prompt Management.
- **Default threshold as a percentage (e.g. 90%)**: rejected as the default — it would silently tolerate regressions in curated critical cases; a usecase that genuinely wants a softer bar can set one explicitly per environment.
- **Structured JSON verdicts from the LLM judge**: rejected — depends on the judge model reliably producing valid JSON on every call, an availability risk for no real benefit over a single-line `PASS:`/`FAIL:` verdict that's trivially parseable.

## Consequences
- Any component or usecase can gate a change without importing Orchestration — the dependency only runs one direction (Orchestration depends on Model Management, Prompt Management, Data & Tools; nothing depends on Orchestration).
- A usecase that wants a softer threshold has to explicitly opt in via config — the default behavior is the strict one, not the lenient one.
- No CI check actually blocks anything yet; the gate can be run manually or from a script today, but "reviewed and gated" doesn't become automatically enforced until CI/CD (09) calls this component.

## Revisit When
- CI/CD (component 09) exists — wire `EvaluationGate.run(...)` into it as the actual deploy-blocking check.
- A usecase needs a semantic-similarity evaluator (e.g. comparing free-text answers by meaning rather than exact match or judge rubric) — add it as a fourth `Evaluator` implementation.
- A usecase needs to compare two prompt versions against the same dataset to decide which to pin (the capability ADR 0006 flagged this component would eventually unlock) — build that comparison workflow once a real usecase needs it, not speculatively.
