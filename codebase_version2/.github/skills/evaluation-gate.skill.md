# Evaluation Gate

**What it is** — Running a golden dataset through a use case, scoring each answer, and comparing the
averages to thresholds to decide pass/fail. A failing gate blocks the change — this is the LLMOps
control point.

**When to use** — After every prompt, pipeline, tool, or retrieval change. The gate is what keeps a
regression from shipping.

**How it works here** — `framework/evaluation.py`:
- `load_golden(usecase)` reads `usecases/<uc>/golden_dataset.json` (cases: a `question` +
  `expected_contains` phrases).
- `load_thresholds(usecase)` reads `usecases/<uc>/evaluators.json` (`metric -> minimum average`).
- `score_case(case, result)` returns `{metric: score in 0..1}`. Offline metrics: `grounded`
  (answer overlaps the retrieved context) and `contains` (answer includes the expected phrases).
- `run_gate(usecase, run_pipeline)` runs every case, averages each metric, and sets `passed` =
  all averages ≥ their thresholds. Returns `{passed, averages, thresholds, cases}`.
- `scripts/run_eval_gate.py` calls `run_gate`, prints a scorecard, and exits 0 (PASS) / 1 (FAIL) —
  CI uses the exit code to block a merge.

**Adding richer metrics** — plug Ragas / DeepEval / an LLM-as-judge in at the `# TODO(optional)`
spot in `score_case`; don't change `run_gate` or the report shape.

**Key files** — `framework/evaluation.py`, `scripts/run_eval_gate.py`,
`usecases/<uc>/golden_dataset.json`, `usecases/<uc>/evaluators.json`.

**Example**
```json
// evaluators.json
{ "thresholds": { "grounded": 0.6, "contains": 0.9 } }
```
```python
scores = {"grounded": round(grounded, 3), "contains": round(contains, 3)}
# TODO(optional): scores["writing_quality"] = judge_writing(answer)   # Ragas / DeepEval / judge
```
```bash
python scripts/run_eval_gate.py example_qa     # from the repo root -> scorecard + PASS/FAIL
```

**Pitfalls**
- Lowering a threshold to force a green build — keep absolute floors, especially groundedness.
- Running from the wrong directory — run from the repo root so `framework`/`usecases` import.
- A golden dataset that only tests happy paths — include the failure modes and "should say I don't
  know" cases.
- Changing `score_case`'s return contract (`{metric: 0..1}`) or `run_gate`'s report shape.
