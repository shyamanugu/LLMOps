---
mode: 'agent'
description: 'Scaffold a new use case (prompts + sequential pipeline + golden dataset) and run the gate'
---

# Add a use case

Scaffold a new use case named `${input:name}` described as: `${input:description}`.

Follow the golden rules in [copilot-instructions](../copilot-instructions.md) and the
[usecases instructions](../instructions/usecases.instructions.md). Copy the SHAPE of the example
use case in [usecases/example_qa/](../../usecases/example_qa/pipeline.py) — do not re-implement any
framework logic, only compose it.

## What to produce (under `usecases/${input:name}/`)

1. `knowledge.json` — a few starter source documents for RAG (same shape as
   [example knowledge.json](../../usecases/example_qa/knowledge.json)). Real domain text if the
   description gives it; otherwise clearly-marked placeholders.
2. `prompts/answer.prompt.json` — one prompt, same fields as
   [answer.prompt.json](../../usecases/example_qa/prompts/answer.prompt.json):
   `id` = `${input:name}.answer`, `version: 1`, `labels: ["prod"]`, `model_alias` (pick an alias
   from [models.json](../../framework/models.json) — never a raw model name), `variables`,
   `template`, `changelog`. The template MUST answer ONLY from the provided context and say "I don't
   know" otherwise (grounding — golden rule 4).
3. `pipeline.py` — a SEQUENTIAL pipeline (NOT agent-to-agent) that mirrors
   [example_qa/pipeline.py](../../usecases/example_qa/pipeline.py): step `retrieve` calls
   `tools.search_knowledge`, step `answer` renders the prompt and calls `model_management.chat`.
   Set `USECASE = "${input:name}"`. Reuse [pipeline.py](../../framework/pipeline.py),
   [tools.py](../../framework/tools.py), [prompt_management.py](../../framework/prompt_management.py),
   and [model_management.py](../../framework/model_management.py).
4. `golden_dataset.json` — 5 to 10 cases, same shape as
   [example golden_dataset.json](../../usecases/example_qa/golden_dataset.json):
   `id`, `question`, `expected_contains` (list of substrings that must appear). Derive them from the
   knowledge you wrote so they can pass in mock mode.
5. `evaluators.json` — copy [example evaluators.json](../../usecases/example_qa/evaluators.json)
   with sensible starting thresholds (`grounded`, `contains`).

## Finish

Run the gate and report the scorecard:

```
python scripts/run_eval_gate.py ${input:name}
```

If it fails, make the smallest fix (wording, retrieval `k`, or a threshold) and re-run until green.
Then remind me to run `/update-memory`.
