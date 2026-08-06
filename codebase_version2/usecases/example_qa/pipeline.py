"""The example use case: a knowledge assistant (RAG question answering).

This wires the reusable framework into a 2-step pipeline:
  step 1 (retrieve): fetch relevant documents across sources (RAG).
  step 2 (answer):   render the prompt with the retrieved context and call the model.

Nothing here re-implements framework logic — it just composes it. Any real use case (APIX, Hiring)
follows the same shape: prompts + a pipeline + a golden dataset.
"""

from framework import model_management, pipeline, prompt_management, tools

USECASE = "example_qa"


def _retrieve(state: dict) -> None:
    """Step 1: retrieve context for the question (RAG over multiple sources)."""
    state["retrieved"] = tools.search_knowledge(USECASE, state["question"], k=3)


def _answer(state: dict) -> None:
    """Step 2: render the prompt with the context and call the model."""
    prompt = prompt_management.load_prompt(USECASE, "answer")
    context = "\n".join(f"- {c['text']}" for c in state["retrieved"])
    user = prompt_management.render(prompt, question=state["question"], context=context)
    result = model_management.chat(
        alias=prompt["model_alias"],
        messages=[{"role": "user", "content": user}],
        prompt_id=prompt["id"],
    )
    state["answer"] = result["text"]
    state["cost_usd"] = result["cost_usd"]


STEPS = [("retrieve", _retrieve), ("answer", _answer)]


def ask(question: str) -> dict:
    """Run the pipeline for one question and return the final state."""
    return pipeline.run(USECASE, STEPS, {"question": question})
