"""Pipeline — run steps in sequence (NOT agent-to-agent).

A use case is a list of steps. Each step is a plain function that takes the shared `state` dict,
does its work (retrieve, call a model, score, etc.), and updates the state. The pipeline runs them
in order, inside one trace, so every step is observable. This is the simple orchestration the v2
deck describes: agents in a pipeline, one after another.
"""

from framework import guardrails
from framework.observability import span, start_trace

# A step is: (name, function(state) -> None). Functions mutate `state` in place.
Step = tuple


def run(use_case: str, steps: list, initial_state: dict) -> dict:
    """Run the steps in order. Returns the final state. Guardrails wrap the input and output."""
    trace_id = start_trace(use_case)
    state = {"trace_id": trace_id, **initial_state}

    # Input guardrail (before any model call).
    gin = guardrails.check_input(state.get("question", ""))
    if not gin["allowed"]:
        state["answer"] = "I can't help with that request."
        state["blocked"] = gin["reason"]
        return state

    for name, fn in steps:
        with span(name):
            fn(state)

    # Output guardrail (redact personal data before returning).
    gout = guardrails.check_output(state.get("answer", ""))
    state["answer"] = gout["text"]
    return state
