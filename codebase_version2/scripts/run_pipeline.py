"""Run the example use case once, locally.

    python scripts/run_pipeline.py
    python scripts/run_pipeline.py "how long does the warranty last?"
"""

import sys
from pathlib import Path

# Make the repo root importable so `from framework import ...` and the use case both resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from usecases.example_qa import pipeline  # noqa: E402


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "How long do I have to return an item?"
    state = pipeline.ask(question)
    print("\nQUESTION:", question)
    print("ANSWER:  ", state.get("answer"))
    print("COST:    ", state.get("cost_usd"), "USD")


if __name__ == "__main__":
    main()
