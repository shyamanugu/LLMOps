"""Run the golden dataset as an evaluation GATE.

This is what the CI pipeline calls on every pull request. It runs the whole golden dataset through
the pipeline, scores each answer, compares the averages to the thresholds, prints a scorecard, and
exits 0 (pass) or 1 (fail). A non-zero exit blocks the merge.

    python scripts/run_eval_gate.py                 # default use case: example_qa
    python scripts/run_eval_gate.py example_qa
"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framework import evaluation  # noqa: E402


def main() -> int:
    usecase = sys.argv[1] if len(sys.argv) > 1 else "example_qa"
    uc = importlib.import_module(f"usecases.{usecase}.pipeline")

    def run_one(case: dict) -> dict:
        # Run the pipeline and hand the evaluator the answer + the retrieved context.
        return uc.ask(case["question"])

    report = evaluation.run_gate(usecase, run_one)

    print(f"\n=== Evaluation gate: {usecase} ===")
    for metric, avg in report["averages"].items():
        threshold = report["thresholds"].get(metric, 0)
        mark = "OK " if avg >= threshold else "LOW"
        print(f"  [{mark}] {metric:12} avg={avg:<6} threshold={threshold}")
    print(f"\nRESULT: {'PASS' if report['passed'] else 'FAIL'}\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
