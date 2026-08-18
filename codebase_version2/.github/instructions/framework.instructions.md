---
applyTo: "framework/**"
---

# Editing framework code

`framework/` is the **reusable** layer — build once, every use case reuses it unchanged.

- **No use-case specifics here.** No use-case prompt text, knowledge, question sets, or business rules. Those belong in `usecases/<name>/`. If you're tempted to hard-code something specific, it goes in the use case, not the framework.
- **Keep public function signatures stable.** Other use cases and scripts depend on them (`retrieve()`, `record_model_call`, `check_input`/`check_output`, `load_models()`, pipeline step contract `(name, function(state) -> None)`). Extend with optional keyword args; don't rename or reorder.
- **One component per file.** Config, models, prompts, guardrails, observability, rag, tools, evaluation, pipeline each stay in their own file. Don't merge concerns.
- **Never hard-code a model/deployment name.** Resolve by task alias (`reason`/`bulk`/`judge`/`embed`) via `framework/models.json`.
- **Azure clients are lazy and optional.** Construct them only when an endpoint is configured; with no endpoint, fall back gracefully to **mock mode** so everything runs offline. Never require cloud to import a module.
- **Mark real cloud wiring** you stub or leave for later with `# TODO(wiring): ...` so it's greppable.
- Module docstring at the top; explain *why*, not *what*.
