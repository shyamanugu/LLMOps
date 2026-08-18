# Conventions and gotchas

> Naming rules, patterns, and traps that keep the repo consistent. Append a line when one is
> learned; keep them short and true.

## Naming
- **Model aliases** are `reason`, `bulk`, `judge`, `embed`. Code asks for an alias; the deployment
  name lives only in `framework/models.json`. Never hard-code a deployment name.
- **Prompt files** are named `<name>.prompt.json` under `usecases/<uc>/prompts/`. The `id` inside is
  usually `<usecase>.<name>` (e.g. `example_qa.answer`).
- **Docs** from any retrieval source are shaped `{id, text, source}` (plus `score` after
  `retrieve()`). Keep the shape identical across sources.
- **The reusable layer is `framework/`, not `platform/`** (`platform` shadows a stdlib module). The
  deck calls it "the platform" — same thing.

## Patterns
- **A pipeline step is `(name, fn(state) -> None)`.** The function mutates the shared `state` dict
  and returns nothing. Steps run in sequence, not agent-to-agent.
- **Config-as-code**: model → alias in `models.json`; prompt → a `.prompt.json` file; thresholds →
  `evaluators.json`. New behaviour → a new tool or step, not a copy of framework logic.
- **A new use case = a copy of `usecases/example_qa/`** (prompts + pipeline + golden dataset). The
  `framework/` code does not change.
- **Only three file types**: `.py`, `.json`, `.yml`. No new file types beyond these.

## Gotchas
- **Mock mode triggers when `AZURE_OPENAI_ENDPOINT` is blank** (`config.MOCK_MODE`). Offline answers
  are deterministic echoes of the context — don't test for "smart" behaviour offline.
- **Run the gate from the repo root**: `python scripts/run_eval_gate.py <usecase>` — so `framework`
  and `usecases` import correctly.
- **`render()` raises on a missing declared variable** — keep `variables` in sync with the
  `{{placeholders}}` in the template.
- **Optional cloud is wired lazily**: Azure OpenAI, Azure AI Search, Content Safety, and Langfuse
  activate only when their env values are set; unfinished connectors are marked `# TODO(wiring)`.
- **Secrets come from env / Managed Identity**, never from code.
