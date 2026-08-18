---
mode: 'agent'
description: 'Add or edit a prompt JSON in a use case, bump version + changelog, then run the gate'
---

# Add or edit a prompt

Add a new prompt, or edit an existing one, for use case `${input:usecase}` (prompt id
`${input:promptId}`). Prompts are JSON files in `usecases/<name>/prompts/` — GitHub is the prompt
registry, so never inline prompt text in Python (golden rule 1). Match
[answer.prompt.json](../../usecases/example_qa/prompts/answer.prompt.json) and the
[usecases instructions](../instructions/usecases.instructions.md).

## Rules

- Keep exactly these fields: `id`, `version`, `labels`, `model_alias`, `variables`, `template`,
  `changelog`.
- `model_alias` must be an alias from [models.json](../../framework/models.json)
  (`reason` / `bulk` / `judge` / `embed`) — never a raw deployment name.
- The `template` is GROUND-ONLY: instruct the model to answer using ONLY the provided context and to
  say "I don't know" when the context does not contain the answer. Do not invent details
  (golden rule 4).
- Every `variable` referenced with `{{...}}` in the template must be listed in `variables`.

## When editing an existing prompt

- Increment `version` by 1.
- Append a one-line entry to `changelog` describing what changed and why.
- Keep `labels` accurate (`prod` only when it is the live version).

## Finish

Run the gate and confirm it stays green:

```
python scripts/run_eval_gate.py ${input:usecase}
```

If a metric drops, adjust the wording (not the threshold) first, re-run, then suggest `/update-memory`.
