# Copilot instructions — LLMOps starter (read this every session)

GitHub Copilot includes THIS file in every chat automatically. It is the shared brain across all
chat sessions — the reason every chat should behave consistently. Keep it accurate; the
`skill-maintainer` chat mode updates it as the project matures.

## What this repository is
A minimal, reusable **LLMOps framework** (see `README.md`). Only Python, JSON, and pipeline `.yml`
files. It runs offline in "mock mode" (no cloud). The framework lives in `framework/`; each use case
lives in `usecases/<name>/`. Framework code is reused unchanged; a use case only adds prompts, a
pipeline, and a golden dataset.

## Architecture you must respect (do not break these)
- `framework/config.py` — settings from env; `MOCK_MODE` when no Azure endpoint; `load_models()`.
- `framework/model_management.py` — call a model by **task alias** (`reason`/`bulk`/`judge`/`embed`);
  aliases resolve via `framework/models.json`. **Never hard-code a model/deployment name in code.**
- `framework/prompt_management.py` — prompts are JSON files in `usecases/*/prompts/` (**GitHub is the
  prompt registry**). Load + render; never inline prompt text in Python.
- `framework/guardrails.py` — `check_input` / `check_output` (unsafe + PII). Input checked before the
  model; output redacted before returning.
- `framework/observability.py` — every model/tool call is recorded (tokens, cost, latency) under one
  trace id. Use `record_model_call` / `record_tool_call` / `span`.
- `framework/rag.py` — retrieval across **multiple sources**; add a loader, keep `retrieve()` stable.
- `framework/tools.py` — the reusable tool catalog (`search_knowledge`, `query_sql`, `get_record`).
- `framework/evaluation.py` — run a golden dataset, score it, decide pass/fail = **the gate**.
- `framework/pipeline.py` — steps run **in sequence** (NOT agent-to-agent). A step is
  `(name, function(state) -> None)`; it mutates `state`.
- The folder is named `framework/` (not `platform/`) because `platform` shadows a Python stdlib
  module. In the proposal deck this is called "the platform".

## Golden rules (the definition of done)
1. **Config-as-code, not hard-coding.** Model choice → `models.json` alias. Prompt → a `.prompt.json`
   file. Thresholds → `evaluators.json`.
2. **Every prompt/agent change must pass the evaluation gate.** After changing a prompt or pipeline,
   run `python scripts/run_eval_gate.py <usecase>` and keep it green.
3. **Reuse the framework; do not duplicate it.** New behaviour → a new tool or a new step, not a copy
   of framework logic.
4. **Ground answers in retrieved context.** Prompts must instruct the model to answer only from the
   provided context and to say "I don't know" otherwise.
5. **Guardrails + observability are not optional.** New entry points call `check_input`/`check_output`
   and run inside a trace.
6. **Keep it explainable.** Small, readable files; a docstring at the top of every module; comments
   that say *why*. No new file types beyond `.py` / `.json` / `.yml`.
7. **Secrets never in code.** Endpoints/keys come from env; in Azure use Managed Identity.

## Coding standards
Python 3.11, type hints, Google-style docstrings, standard library first, no `print` in framework
code (use `observability`), fail loudly on missing inputs (no silent gaps). Match the style already
in `framework/`.

## How to work (per session)
1. Pick a **chat mode** (agent) from `.github/chatmodes/` that fits the task (LLMOps Engineer, Prompt
   Engineer, Evaluation Engineer, RAG/Data Engineer, or Skill Maintainer).
2. For a repeatable task, run a **prompt** with `/` (see `.github/prompts/`), e.g. `/add-usecase`.
3. Before finishing, satisfy `.github/hooks/definition-of-done.md`.
4. If you learned something durable (a decision, a convention, a new pattern), update memory —
   run `/update-memory` or ask the Skill Maintainer.

## Memory protocol (why chats stay consistent)
- This file + `.github/memory/project-memory.md` + `.github/memory/decisions.md` +
  `.github/memory/conventions.md` are the durable memory.
- At the start of a non-trivial task, read `project-memory.md` (current state + what's next) and the
  relevant file in `.github/skills/`.
- When something durable changes, update memory in the same change. Stale memory is worse than none.

## Current focus
See `.github/memory/project-memory.md` for what is built, what is in progress, and what is next.
