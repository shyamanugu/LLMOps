# AI Pipeline — LLMOps Console

The **single, unified console** for the AI Pipeline application and its LLMOps
operations. One app, one look, seven tabs:

1. **Application** — run the pipeline (mock executes instantly) and view the coaching
   intelligence it produces: pipeline flow, KPIs, per-agent behaviour scores + AI
   reflection + top calls.
2. **Playground** — test a prompt version + model against a golden dataset; scored with a
   pass-rate donut and per-case results.
3. **Evaluation** — golden-dataset metrics: pass-rate trend, pass rate by prompt version,
   full eval-run history.
4. **Golden Datasets** — view / edit / add / delete cases and upload whole datasets
   (saved locally in mock).
5. **Monitoring** — LLM cost, tokens, latency-by-step, calls-by-step, guardrail flags,
   recent runs.
6. **Feedback** — submit and review per-transcript feedback.
7. **Guardrails** — audit trail of every guardrail decision.

Everything is **pure Python standard library + a zero-build vanilla-JS UI** — no pip
installs, no npm, no CDN, no network. That means it runs on a locked-down VDI (incl.
Python 3.14) and never touches corporate SSL/cert.pem. Charts are hand-drawn inline SVG.

## Run it (mock — nothing to install)

```bash
# from the usecase root: usecases/ai_pipeline 2
python ops/start_backend.py      # stdlib HTTP API on http://127.0.0.1:8000
python ops/start_ui.py           # serves the console on http://127.0.0.1:5173 (opens a browser)
```

Start the backend first, then the UI. The backend seeds a local SQLite DB, starter
prompts, golden datasets, and demo metrics on first run, so the console is full of data
immediately. Mock mode uses a deterministic mock LLM in the playground — no keys needed.

> This unified console supersedes the earlier standalone React demo under `ui/`. The
> `ui/` folder is retained only for its data/exporter utilities (`export_run.py`,
> `make_sample_data.py`, `public/sample-data.json`).

## Mock vs Real (via `.env`)

- `AI_PIPELINE_MODE=mock` (default): local SQLite (`ops/data/ops.db`) + JSON prompt
  registry (`ops/data/registry/`); playground uses the mock LLM.
- `AI_PIPELINE_MODE=real`: the playground calls the real model (needs `REASONING_MODEL_*`
  in `.env`) and errors clearly if creds are missing. Monitoring reads the same local
  store (mirror it from real runs / Azure Monitor as you wire that up).

## Prompt versioning → the pipeline, with no redeploy

The **Prompts registry is live-connected to the pipeline.** Editing a template and
clicking **Save as new version** writes `vN.json`; **Activate** writes `active.json`.
The pipeline's `prompts_gate` resolves each prompt in this order:

1. env-pinned version — `AI_PIPELINE_PROMPT_<PROGRAM>_<NAME>=v3`
   (e.g. `AI_PIPELINE_PROMPT_TELESALES_ANALYSIS=v3`) — deploy a version by changing an
   env value, no code change;
2. the registry's `active.json` pointer (what **Activate** sets);
3. a git-backed YAML prompt (`prompts/<program>/`);
4. the in-code prompt.

So activating a version in the UI (or setting the env var) changes what the **next
pipeline run** uses — no deployment step.

## Golden datasets

The **Golden Datasets** tab lists datasets (stored as JSONL under `ops/data/datasets/`),
shows every case in a table, and lets you **edit / add / delete** a case or **upload** a
whole dataset (paste JSONL or a JSON array). In mock everything is saved locally — nothing
is uploaded anywhere. These datasets are exactly what the Playground and Evaluation tabs
score against.

## Folder map

```
ops/
  start_backend.py   start_ui.py         # the two files you run
  server/            config, store (SQLite), registry (prompts+models),
                     datasets (golden CRUD), engine (playground + mock run),
                     seed, api, sample_dashboard.json
  ui/                index.html, app.js, style.css   (zero-build vanilla JS, inline-SVG charts)
  data/              (gitignored) ops.db + registry/prompts/... + datasets/*.jsonl
```
