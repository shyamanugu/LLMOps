# AI Pipeline — Demo UI (legacy — superseded by the LLMOps Console)

> **This standalone React demo is superseded by the unified LLMOps Console** under
> `../ops/` (run `python ops/start_backend.py` + `python ops/start_ui.py`). This folder is
> kept only for its data/exporter utilities (`export_run.py`, `make_sample_data.py`,
> `public/sample-data.json`). You do not need Node to demo anymore.

A local React dashboard that showcases the AI Pipeline (call-analytics) and its
AFNI LLMOps instrumentation to a client. No backend — it reads a single JSON file.

## Run

```bash
cd "usecases/ai_pipeline 2/ui"
npm install
npm run dev        # opens http://localhost:5173
```

Out of the box it shows a realistic **sample** dataset (`public/sample-data.json`),
so you can demo with zero Azure setup.

## Show a real run

After running the pipeline (see `../docs/CLIENT_DEMO_SETUP.md`), export a dataset
from the JSONL traces + summary reports and reload:

```bash
cd "usecases/ai_pipeline 2"
python ui/export_run.py \
  --trace-file traces/trace.jsonl \
  --summaries-dir ./summary_json \
  --program telesales --date 2025-08-28 \
  --out ui/public/sample-data.json
```

Either restart `npm run dev`, or click **"Load run…"** in the header to open any
exported `.json` on the fly (no restart).

## What it shows
- **Header** — run context (program, date, environment, model, run id).
- **Pipeline** — the five stages: denoise → analysis → summary → individual_metrics → kpi.
- **LLMOps Observability** — LLM calls, tokens, cost, latency, guardrail flags, errors,
  and cost/latency by step. (Cost is $0 until per-token rates are set in `pricing.yaml`.)
- **KPIs** — resolution rate, right-of-sell, escalations, etc. with deltas.
- **Agent Coaching Intelligence** — per-employee behavior scores, team comparison, the
  AI coaching reflection, top calls, and escalations.

## Build a static bundle
```bash
npm run build     # -> ui/dist/  (relative asset paths; open index.html or serve statically)
```

## Data contract
See the shape in `public/sample-data.json`. The exporter (`export_run.py`) writes exactly
this shape from a real run; the loader validates it minimally and fails friendly.
