# ADR 0003 — Prompt registry: start with Git + in-app cache, adapters for Langfuse/Foundry

- Status: Accepted
- Date: 2026-08-06
- Deciders: Platform engineering

## Context

The client's litmus-test question was: *"the entire project is already on Git, including
the prompt. So what is the difference?"* Storing prompts in Git is **not** the new part —
they already do that. The delta is three things: (1) one **YAML file per prompt** with
`id, version, template, inputs, eval_refs, changelog` (they confirmed they do not have
this today); (2) an **evaluation gate** on every prompt change against the golden dataset;
(3) a **runtime registry** that lets us swap, roll back, and compare prompt versions.

A registry is simply where prompts are maintained so we can fall back if a new version
fails evaluation. Three backends were on the table:

- **Git + in-app cache** — prompts as `*.prompt.yaml` in the repo, read at startup and
  cached; version = git + the YAML `version`; rollback = git revert / repoint label.
  Cost: $0. Simplest. No extra service.
- **Langfuse prompt management** — open-source (MIT), self-hosted in our own network;
  UI to edit/compare/label (prod/staging) and roll back; also gives tracing + token/cost
  dashboards. Cost: free software, infra ~$50-150/mo to self-host. Adopt as we scale.
- **Azure AI Foundry prompt assets** — versioned assets native to Azure AI Foundry,
  accessed via SDK, integrated with Foundry evaluations/tracing; fully managed. Cost:
  no separate license, folded into Azure usage.

## Decision

Start with **Git + in-app cache** as the default (`LLMOPS_PROMPT_REGISTRY=git`). Define a
single `PromptRegistry` protocol and implement all three behind it (dependency inversion):
`GitPromptRegistry` (default, reads `usecases/*/prompts/*.prompt.yaml`),
`LangfusePromptRegistry`, and `FoundryPromptRegistry` (the last two are adapters with
client wiring marked as TODO). Application code only ever calls `load_prompt(id, label)`,
which selects the configured backend via a factory, so call sites are backend-agnostic and
switching later is a config change, not a code rewrite.

## Consequences

- Positive: zero cost and zero new infrastructure to begin; prompts stay in the repo under
  review and the eval gate from day one.
- Positive: adopting Langfuse (for the editing/compare UI + built-in observability) or
  Foundry (for fully-managed Azure) later is a `LLMOPS_PROMPT_REGISTRY` change plus wiring
  the adapter — no change to pipeline or agent code.
- Positive: CI can push the Git YAML to Langfuse/Foundry on merge to keep them in sync.
- Negative: the Git backend has no editing UI (edit via pull request only) and no built-in
  version-compare view until Langfuse/Foundry is adopted.
- Negative: three backends to keep behind one contract; the two adapters carry TODO wiring
  until a client actually enables them.
