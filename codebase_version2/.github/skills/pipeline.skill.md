# Pipeline

**What it is** — Running a use case as a list of steps **in sequence** (NOT agent-to-agent). Each
step is a plain function that mutates a shared `state` dict. The pipeline runs the steps in order,
inside one trace, with guardrails wrapping input and output.

**When to use** — Composing a use case from framework components: retrieve → answer → (score / act).
Any orchestration in this repo is a sequential pipeline, not agents handing off to each other.

**How it works here** — `framework/pipeline.py`:
- A step is `(name, function(state) -> None)`. The function reads and writes `state` in place.
- `run(use_case, steps, initial_state)`:
  1. `start_trace(use_case)` and seed `state` with the trace id + initial state.
  2. **Input guardrail**: `check_input(state["question"])`; if blocked, set a safe answer and return.
  3. Run each step inside a `span(name)` so it's timed and observable.
  4. **Output guardrail**: `check_output(state["answer"])` redacts PII, then return the final state.

A use case (e.g. `usecases/example_qa/pipeline.py`) just defines the step functions and the `STEPS`
list — it composes the framework, never re-implements it.

**Key files** — `framework/pipeline.py`, `usecases/example_qa/pipeline.py`,
`framework/guardrails.py`, `framework/observability.py`.

**Example**
```python
from framework import model_management, pipeline, prompt_management, tools
USECASE = "example_qa"

def _retrieve(state): state["retrieved"] = tools.search_knowledge(USECASE, state["question"], k=3)
def _answer(state):
    prompt = prompt_management.load_prompt(USECASE, "answer")
    ctx = "\n".join(f"- {c['text']}" for c in state["retrieved"])
    user = prompt_management.render(prompt, question=state["question"], context=ctx)
    state["answer"] = model_management.chat(prompt["model_alias"],
        [{"role": "user", "content": user}], prompt_id=prompt["id"])["text"]

STEPS = [("retrieve", _retrieve), ("answer", _answer)]
def ask(q): return pipeline.run(USECASE, STEPS, {"question": q})
```

**Pitfalls**
- Reaching for agent-to-agent orchestration — the v2 design is sequential steps only.
- A step that returns a value instead of mutating `state` — steps return `None` and write to state.
- Skipping the trace/guardrails by calling steps directly instead of through `pipeline.run`.
- Putting framework logic in a step — steps compose framework functions; new reusable behaviour is a
  new tool or a new framework function.
