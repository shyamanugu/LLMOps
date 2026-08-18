---
applyTo: "usecases/**"
---

# Building a use case

A use case **composes** the framework — it does not reimplement it.

- **Reuse, don't duplicate.** Call `framework/` components (model_management, prompt_management, guardrails, observability, rag, tools, evaluation, pipeline). New behaviour → a new tool or a new pipeline step, never a copy of framework logic.
- **A use case = these parts, nothing more:**
  - `prompts/*.prompt.json` — versioned prompt files (GitHub is the registry).
  - `pipeline.py` — wires framework components into **sequential steps** (NOT agent-to-agent). Each step is `(name, function(state) -> None)` and mutates `state`.
  - `knowledge.json` — the RAG source data for this use case.
  - `golden_dataset.json` — the test cases.
  - `evaluators.json` — metrics + thresholds (the gate config).
- **Keep pipeline steps small.** One responsibility each (retrieve, then render+call, then guard, then record). Easy to read and to trace.
- **Always ground answers in retrieved context.** Retrieve first, pass that context into the prompt, and rely on prompts that answer only from context and say "I don't know" otherwise.
- **Guardrails + observability are not optional.** Entry points run `check_input` before the model and `check_output` before returning, inside a trace.
- Start a new use case by copying `usecases/example_qa/`; change prompts, knowledge, and the golden dataset — leave `framework/` untouched.
