# Evaluation gate (`evals/`)

`evals/run.py` is the CI entrypoint for the LLMOps **evaluation gate**. It runs a use-case's
golden dataset through its pipeline, scores every case with the metric suite, aggregates the
scores, and applies the thresholds in `platform/evaluators/defaults.yaml` (or a per-use-case
`usecases/<uc>/evals/evaluators.yaml`). The process **exit code is the gate**: `0` = pass,
`1` = fail — which is what `.github/workflows/pr-checks.yml` blocks on.

## Usage

```bash
# From backend/ — the PR check (only cases affected by the change):
python evals/run.py --usecase apix --subset changed --fail-under baseline

# Nightly / eval-full.yml — the whole golden set:
python evals/run.py --usecase apix --subset full

# Fast local smoke run + machine-readable output:
python evals/run.py --usecase apix --subset smoke --json
```

### Arguments

| Flag | Values | Meaning |
|---|---|---|
| `--usecase` | e.g. `apix`, `hiring` | Use-case directory under `usecases/`. |
| `--subset` | `changed` \| `full` \| `smoke` | Which cases to run. `changed` degrades to `smoke` until the PR-diff wiring lands. |
| `--fail-under` | `baseline` | Threshold policy. `baseline` = baseline-relative rule + absolute floors from `evaluators.yaml`. |
| `--json` | flag | Emit the full `GateReport` as JSON instead of the text summary. |

## How the gate decides

Each metric must satisfy **all** applicable rules (fail-safe: a thresholded metric with no
score fails):

- **Absolute floors/ceilings** — e.g. `groundedness` min `0.9`; `pii_leak` max `0`
  (any leak fails outright).
- **Baseline-relative** — the candidate may not regress more than `baseline_delta` below the
  current baseline (usually `main`), catching drift even when the floor is met.

## Metrics

- **tool_selection** (custom, trace-driven) — the flagship agentic metric: reads the tool the
  agent actually called from the trace and compares it (and its arguments) to the golden
  expectation. Aggregated into `tool_selection_accuracy` plus per-tool precision/recall.
- **groundedness / answer_relevance** — Ragas (optional `eval` extra).
- **writing_quality** — DeepEval G-Eval (optional `eval` extra).
- **judge_score** — LLM-as-judge on the `judge` alias with a rubric.

Metrics whose optional dependency is missing self-report an error rather than crashing, so
the gate runs everywhere; install them with `pip install -e '.[eval]'`.

## Golden datasets

JSONL under `usecases/<uc>/evals/*.jsonl`, one case per line:

```json
{"id": "apix-001", "input": {"question": "reset my API key"},
 "grading": {"expected_tool": "get_record", "reference": "Settings > Keys"},
 "meta": {"suite": "smoke", "tags": ["auth"]}}
```

An optional `usecases/<uc>/evals/baseline.json` (`{"metrics": {"groundedness": 0.94, ...}}`)
supplies the baseline for the relative rule. In production the baseline is read from stored
gate history (App Insights / Langfuse) — see the `# TODO(wiring)` markers in
`llmops.evaluation.gate`.
