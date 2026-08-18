# AGENTS.md — brief for the coding agent

This file is the standing brief for the GitHub Copilot **coding agent** working in this repository.
Read it before making changes. For the always-loaded rules and current state, also read
`.github/copilot-instructions.md` and `.github/memory/`.

## What this repo is
A minimal, reusable **LLMOps framework**. The reusable layer lives in `framework/` (config,
model_management, prompt_management, guardrails, observability, rag, tools, evaluation, pipeline).
Each use case lives in `usecases/<name>/` and adds only prompts, a pipeline, and a golden dataset —
the framework is reused unchanged. It runs **offline in mock mode** (no cloud needed). Only three
file types: `.py`, `.json`, `.yml`.

## How to run it
```bash
pip install -r requirements.txt         # base deps; Azure/eval libs are optional
python scripts/run_pipeline.py          # run the example use case once, locally
python scripts/run_eval_gate.py         # run the golden dataset as a gate -> scores + PASS/FAIL
```
With no `AZURE_OPENAI_ENDPOINT` set, the model layer runs in mock mode so everything works offline.
Run commands from the **repo root** so `framework` and `usecases` import correctly.

## Golden rules
1. **Config-as-code, not hard-coding.** Model → an alias in `framework/models.json`
   (`reason`/`bulk`/`judge`/`embed`). Prompt → a `.prompt.json` file. Thresholds → `evaluators.json`.
2. **The gate must pass.** After any prompt or pipeline change, run
   `python scripts/run_eval_gate.py <usecase>` and keep it green (exit 0). A failing gate blocks the
   change.
3. **Reuse the framework; don't duplicate it.** New behaviour = a new tool (`framework/tools.py`) or
   a new step — not a copy of framework logic. Keep public signatures stable.
4. **Ground answers in retrieved context.** Prompts instruct the model to answer only from the
   provided context and to say "I don't know" otherwise.
5. **Guardrails + observability are not optional.** Every entry point calls `check_input` /
   `check_output` and runs inside a trace.
6. **Secrets never in code.** Endpoints/keys come from env; in Azure use Managed Identity.

## Definition of done
- Change is config-as-code (alias / prompt JSON / thresholds), not a hard-coded value.
- `python scripts/run_eval_gate.py <usecase>` is green; groundedness floor held (no threshold
  lowered to force a pass).
- Framework stays generic — no use-case specifics leaked into `framework/`; public signatures
  unchanged.
- New entry points wrapped in guardrails + a trace; new cloud wiring marked `# TODO(wiring)`.
- Only `.py` / `.json` / `.yml` touched; module docstring on new modules; comments say *why*.
- Durable changes recorded in `.github/memory/` (decisions / conventions).

## Pointers
- Always-loaded rules and architecture: `.github/copilot-instructions.md`.
- Current state, decisions, conventions: `.github/memory/`.
- Component how-tos: `.github/skills/`. Chat modes (agents): `.github/chatmodes/`.
