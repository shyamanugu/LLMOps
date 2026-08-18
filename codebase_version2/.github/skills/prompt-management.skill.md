# Prompt Management

**What it is** — Prompts as versioned JSON files in the repo. **GitHub is the prompt registry** —
a prompt change is a pull request that must pass the evaluation gate, not text buried in code.

**When to use** — Whenever you write or edit a prompt. Never inline prompt text in a `.py` file.

**How it works here** — `framework/prompt_management.py`:
- `load_prompt(usecase, name)` reads `usecases/<usecase>/prompts/<name>.prompt.json` as a dict.
- `render(prompt, **values)` fills `{{variable}}` placeholders. It **raises** if a declared variable
  in `variables` wasn't supplied — no silent gaps.
- `list_prompts(usecase)` lists the prompt names for a use case.

A prompt file carries: `id`, `version`, `labels`, `model_alias` (the alias to call — see the
model-management skill), `variables`, `template`, and a `changelog`. Versioning is manual and
explicit: bump `version` and append a `changelog` line on every change.

**Key files** — `framework/prompt_management.py`,
`usecases/example_qa/prompts/answer.prompt.json`.

**Example**
```json
{
  "id": "example_qa.answer",
  "version": 1,
  "labels": ["prod"],
  "model_alias": "reason",
  "variables": ["question", "context"],
  "template": "Answer using ONLY the context below. If it isn't there, say you don't know.\n\nQuestion: {{question}}\n\nContext: {{context}}",
  "changelog": ["v1: initial version — answer strictly from retrieved context"]
}
```
```python
prompt = prompt_management.load_prompt("example_qa", "answer")
user = prompt_management.render(prompt, question=q, context=ctx)
```

**Pitfalls**
- `variables` out of sync with the `{{placeholders}}` in `template` — `render` raises on a missing
  value; an undeclared placeholder is silently left unfilled.
- Editing a template without bumping `version` or adding a changelog line.
- Writing a prompt that lets the model answer from outside the context — always instruct
  "answer only from the context; say you don't know otherwise" (grounding).
- Changing a prompt and not re-running `python scripts/run_eval_gate.py <usecase>`.
