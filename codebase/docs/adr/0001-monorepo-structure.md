# ADR 0001 — Monorepo structure (shared platform + per-use-case folders)

- Status: Accepted
- Date: 2026-08-06
- Deciders: Platform engineering

## Context

We are building an LLMOps (Large Language Model Operations) platform that must serve
multiple use cases (APIX contact-center coaching, Hiring Intelligence, and an unknown
number more later). The v2 deck makes one point repeatedly: *most of the machinery is
shared*. Source control and CI/CD, the prompt registry, model routing, the evaluation
gate, observability, guardrails, the data-access layer, the reusable tool catalog, the
pipeline runtime, the gateway, identity/secrets, and feedback are all built once and
reused. Only prompt *content*, agent/pipeline design, golden-dataset *content* and
thresholds, use-case data sources, use-case-specific tools, guardrail policy tuning, and
dashboards are new per use case.

The alternative — a separate repository per use case — would duplicate all shared code,
make platform upgrades an N-way copy exercise, and fragment the evaluation gate and CI
configuration.

## Decision

Use a single monorepo. Shared, reusable code lives under `backend/src/llmops/` (the
importable `llmops` package) and `platform/` (config-as-code: `models.yaml`, tool
registry, evaluator defaults, gateway policies). Each use case is a folder under
`usecases/<name>/` with the *same shape* (`prompts/`, `agents/`, `evals/`, `config/`,
`tools/`, and a `COPILOT_PROMPTS.md`). The Nth use case adds one folder and reuses
everything else. The frontend Console (`frontend/`) and infrastructure (`infra/`) also
live in the same repo so a change and its tests/infra travel together.

## Consequences

- Positive: one place to review, one CI/CD pipeline, one evaluation gate, atomic
  cross-cutting changes, no code duplication, trivial onboarding of new use cases.
- Positive: `CODEOWNERS` can path-own `usecases/*/prompts` and `platform/` for review.
- Negative: the repo grows; CI must scope work to *changed* paths (the workflows filter
  on `paths:` and `--subset changed`) so we do not run every use case's evals on every PR.
- Negative: all use cases share one release train; a use case needing an isolated release
  cadence would need path-scoped deploy jobs (supported, but adds workflow complexity).
