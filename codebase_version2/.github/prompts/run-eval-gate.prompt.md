---
mode: 'ask'
description: 'Run the evaluation gate for a use case, interpret the scorecard, and suggest the smallest fix'
---

# Run the evaluation gate

Run the gate for use case `${input:usecase}` and interpret the result:

```
python scripts/run_eval_gate.py ${input:usecase}
```

This runs the whole golden dataset through the pipeline, scores each answer, compares the averages
to the thresholds in `usecases/${input:usecase}/evaluators.json`, and exits 0 (PASS) or 1 (FAIL).
See [run_eval_gate.py](../../scripts/run_eval_gate.py) and
[evaluation.py](../../framework/evaluation.py).

## Interpret the scorecard

For each metric (e.g. `grounded`, `contains`) report `avg` vs `threshold` and whether it is `OK` or
`LOW`, then the overall PASS/FAIL.

## If it FAILS, suggest the SMALLEST fix (in this order)

1. **Prompt wording** — if answers drift or add detail, tighten the ground-only template
   (`usecases/${input:usecase}/prompts/*.prompt.json`) via `/add-prompt`.
2. **Retrieval** — if the answer is missing facts that exist in `knowledge.json`, raise `k` or fix
   the retrieval step in the use case pipeline (see [rag.py](../../framework/rag.py) and
   [tools.py](../../framework/tools.py)).
3. **Threshold** — only if the current bar is genuinely unrealistic, and say why. Never lower a
   threshold just to pass.

Do not edit files in this mode — recommend the specific prompt (`/add-prompt`, `/add-golden-cases`)
to apply the fix. Keeping the gate green is the definition of done (golden rule 2).
