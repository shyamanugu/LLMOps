# Project memory — current state

> The living status of the project. Read this at the start of a task. Keep it short and current;
> the `skill-maintainer` agent (or `/update-memory`) updates it. Do not let it grow stale.

## What this project is
A reusable LLMOps framework (minimal version). Framework in `framework/`; use cases in `usecases/`.
Runs offline in mock mode. Prompt registry = GitHub. Sequential pipelines (not agent-to-agent).

## What is built (framework — reuse, do not rewrite)
- config, model_management, prompt_management, guardrails, observability, rag, tools, evaluation,
  pipeline — all present and working offline.
- Example use case `usecases/example_qa/` (a knowledge assistant) runs end-to-end; its evaluation
  gate PASSES.
- CI/CD: `pipelines/pr-eval-gate.yml`, `deploy.yml`, `nightly.yml`. Nightly Function App in
  `jobs/nightly_eval/`.

## In progress / next (edit as you go)
- [ ] Wire real Azure OpenAI (set `AZURE_OPENAI_ENDPOINT`; leave key blank to use Managed Identity).
- [ ] First real use case for the client (copy `usecases/example_qa/` → `usecases/<name>/`).
- [ ] Author the first golden dataset with the SME.
- [ ] Optional: real RAG (Azure AI Search), real guardrails (Content Safety), Langfuse dashboards.

## Known decisions
See `.github/memory/decisions.md`.

## Conventions and gotchas
See `.github/memory/conventions.md`.

## How to onboard a new use case (quick)
Copy `usecases/example_qa/`, change the prompt(s), the data sources, and the golden dataset. The
`framework/` code does not change. Then keep `python scripts/run_eval_gate.py <name>` green.
