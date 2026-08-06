"""Evaluation — run a golden dataset, score the answers, decide pass/fail (the GATE).

A golden dataset is a JSON list of test cases (a question + what a good answer must contain). We run
the use-case pipeline for each case, score it, and compare to the thresholds in evaluators.json. If
any threshold is missed, the gate FAILS — this is what blocks a bad change from shipping.

Metrics here are simple and run offline:
  - grounded: does the answer overlap with the retrieved context (not made up)?
  - contains: does the answer contain the expected phrases?
Richer metrics (Ragas / DeepEval / an LLM-as-judge) plug in at the marked spot without changing the
gate logic.
"""

import json
import re

from framework import config


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def load_golden(usecase: str) -> list[dict]:
    """Load usecases/<uc>/golden_dataset.json."""
    path = config.ROOT / "usecases" / usecase / "golden_dataset.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_thresholds(usecase: str) -> dict:
    """Load usecases/<uc>/evaluators.json (metric -> minimum score)."""
    path = config.ROOT / "usecases" / usecase / "evaluators.json"
    return json.loads(path.read_text(encoding="utf-8"))["thresholds"]


def score_case(case: dict, result: dict) -> dict:
    """Score one answer against one golden case. Returns {metric: score in 0..1}."""
    answer = result.get("answer", "")
    context = " ".join(c["text"] for c in result.get("retrieved", []))

    grounded = _overlap(answer, context) if context else 1.0
    expected = case.get("expected_contains", [])
    contains = (
        sum(1 for phrase in expected if phrase.lower() in answer.lower()) / len(expected)
        if expected
        else 1.0
    )

    scores = {"grounded": round(grounded, 3), "contains": round(contains, 3)}
    # TODO(optional): add Ragas / DeepEval / LLM-as-judge metrics here, e.g.
    #   scores["writing_quality"] = judge_writing(answer)
    return scores


def _overlap(answer: str, context: str) -> float:
    a, c = _tokens(answer), _tokens(context)
    return len(a & c) / len(a) if a else 0.0


def run_gate(usecase: str, run_pipeline) -> dict:
    """Run the whole golden dataset as a gate.

    Args:
        usecase: the use-case folder name.
        run_pipeline: a function(case) -> result dict (with 'answer' and 'retrieved').

    Returns a report: {passed: bool, averages: {metric: score}, thresholds, cases: [...]}.
    """
    golden = load_golden(usecase)
    thresholds = load_thresholds(usecase)

    per_case, totals = [], {}
    for case in golden:
        result = run_pipeline(case)
        scores = score_case(case, result)
        for m, s in scores.items():
            totals[m] = totals.get(m, 0.0) + s
        per_case.append({"id": case["id"], "scores": scores})

    n = max(len(golden), 1)
    averages = {m: round(v / n, 3) for m, v in totals.items()}
    passed = all(averages.get(m, 0.0) >= t for m, t in thresholds.items())

    return {"passed": passed, "averages": averages, "thresholds": thresholds, "cases": per_case}
