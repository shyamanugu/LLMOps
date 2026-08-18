---
applyTo: "usecases/**/prompts/**"
---

# Prompt JSON files (`*.prompt.json`)

GitHub **is** the prompt registry. These files are versioned by pull request — treat them as source of truth.

- **Required fields:** `id`, `version`, `labels`, `model_alias`, `variables`, `template`, `changelog`.
- `model_alias` is a task alias (`reason`/`bulk`/`judge`/`embed`) — never a raw model/deployment name.
- `template` uses `{{var}}` placeholders; every placeholder must be declared in `variables`.
- **On every change: bump `version` and add a `changelog` line** describing what changed and why. No silent edits.
- **The template must instruct the model to answer only from the provided context** and to say **"I don't know"** when the context does not contain the answer. No answering from general knowledge.
- **Never inline prompt text in Python.** Load prompts through `framework/prompt_management.py`; `pipeline.py` references a prompt by `id`, it does not embed the string.
- Keep templates readable and explainable — this is documentation as much as code.
