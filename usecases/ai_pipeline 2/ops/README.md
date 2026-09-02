# AIA LLMOps — Ops Console

The operations console for the AIA pipeline: **prompt playground + versioned prompt
registry, LLM monitoring, per-transcript feedback, and guardrail audit** — all local,
no Azure required in mock mode. Everything lives in this one folder.

## Run it (mock — nothing to install)

```bash
# from the usecase root: usecases/ai_pipeline 2
python ops/start_backend.py      # stdlib HTTP API on http://127.0.0.1:8000
python ops/start_ui.py           # serves the console on http://127.0.0.1:5173 (opens a browser)
```

The backend seeds a local SQLite DB + a couple of starter prompts on first run, so the
console has data immediately. Mock mode uses a deterministic mock LLM in the playground —
no keys needed.

## Mock vs Real (via `.env`)

- `AI_PIPELINE_MODE=mock` (default): local SQLite (`ops/data/ops.db`) + JSON prompt
  registry (`ops/data/registry/`); playground uses the mock LLM.
- `AI_PIPELINE_MODE=real`: the playground calls the real model (needs `REASONING_MODEL_*`
  in `.env`) and errors clearly if creds are missing. Monitoring reads the same local
  store (mirror it from real runs / Azure Monitor as you wire that up).

## Tabs

- **Playground** — pick a prompt version + model + golden dataset, run, see pass-rate and
  per-case results. Each run is logged to Monitoring → Evaluation runs.
- **Prompts** — versioned registry. Edit a template → **Save as new version**; **Activate**
  a version to make it the one the pipeline uses **with no redeploy**. You can also pin a
  version by env: `AI_PIPELINE_PROMPT_<PROGRAM>_<NAME>=v3` (e.g. `AI_PIPELINE_PROMPT_TELESALES_ANALYSIS=v3`).
- **Monitoring** — LLM calls, tokens, cost, latency by step, guardrail flags, and the
  per-prompt/model evaluation-run history vs the golden set.
- **Feedback** — submit per-transcript feedback (app-level); the log helps developers tune
  prompts/models. Corrections can promote into the golden dataset.
- **Guardrails** — audit trail of every guardrail decision (PII flagged, secrets blocked).

## How the registry connects to the pipeline

The pipeline's `prompts_gate` reads `ops/data/registry/prompts/<program>/<name>/`:
env-pinned version → `active.json` pointer → git-backed YAML → in-code prompt. So
**Activate** in the UI (or an env var) changes what the next pipeline run uses — no
deployment step.

## Folder map

```
ops/
  start_backend.py   start_ui.py
  server/            config, store (SQLite), registry (prompts+models), engine (playground), seed, api
  ui/                index.html, app.js, style.css   (zero-build vanilla JS)
  data/              (gitignored) ops.db + registry/prompts/<program>/<name>/vN.json
```
