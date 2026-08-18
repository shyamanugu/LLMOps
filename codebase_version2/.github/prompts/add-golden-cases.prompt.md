---
mode: 'agent'
description: 'Add golden dataset cases to a use case from example questions or failures, then run the gate'
---

# Add golden cases

Add test cases to the golden dataset for use case `${input:usecase}`
(`usecases/${input:usecase}/golden_dataset.json`). The golden dataset is the evaluation gate — it is
how every prompt/pipeline change is proven (golden rule 2). Follow the
[usecases instructions](../instructions/usecases.instructions.md).

## Source of the new cases

Use whatever I provide in `${input:cases}` — either example questions to cover, or observed failures
to lock in as regression tests. If I gave failures, add a case that reproduces each one.

## Keep the exact JSON shape

Match [example golden_dataset.json](../../usecases/example_qa/golden_dataset.json): a JSON array of
objects with:

- `id` — short unique id (e.g. `${input:usecase}-0NN`), continuing the existing numbering.
- `question` — the user question.
- `expected_contains` — a list of substrings the answer MUST contain.

Ground every `expected_contains` value in the use case's `knowledge.json` so the case is answerable
from retrieved context (golden rule 4). Do not duplicate existing questions.

## Finish

Run the gate and show the new scores:

```
python scripts/run_eval_gate.py ${input:usecase}
```

Report the per-metric averages vs thresholds and PASS/FAIL. If a new case fails because the answer
is correct but the substring is too strict, loosen `expected_contains` (not the threshold); if it
fails because retrieval missed, note that for a prompt/RAG fix. Then suggest `/update-memory`.
