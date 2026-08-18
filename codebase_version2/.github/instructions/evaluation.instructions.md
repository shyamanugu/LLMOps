---
applyTo: "usecases/**/evaluators.json,usecases/**/golden_dataset.json,scripts/run_eval_gate.py,framework/evaluation.py"
---

# Evaluation (the gate)

- **`golden_dataset.json` is a list of cases.** Each case has at least a `question` and `expected_contains` (the substrings/facts a correct answer must include). Keep cases small and specific.
- **`evaluators.json` holds the metrics and thresholds** — the gate config. Thresholds live here, never hard-coded in Python.
- **A change is not done until the gate passes.** After changing a prompt, pipeline, knowledge, or evaluator, run:
  ```
  python scripts/run_eval_gate.py <usecase>
  ```
  It must exit 0 (PASS). A red gate blocks the change.
- **Grow the golden set from real failures.** When you find a wrong or ungrounded answer, add it as a case before fixing — so the gate catches the regression next time.
- **Keep absolute floors.** Some checks are non-negotiable regardless of score — e.g. **no PII leak**, no unsafe content. These must never be relaxed to make the gate go green.
- `framework/evaluation.py` runs the dataset, scores it, and decides pass/fail. Keep it use-case-agnostic; use-case data stays in the use case.
