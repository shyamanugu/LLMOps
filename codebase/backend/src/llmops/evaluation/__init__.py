"""Evaluation engine — golden datasets, metrics, thresholds, and the CI gate.

Public surface (see ``ARCHITECTURE_SPEC.md`` §3):
    * :func:`~llmops.evaluation.golden.load_golden` / :class:`~llmops.evaluation.golden.GoldenCase`
    * :class:`~llmops.evaluation.thresholds.Thresholds` /
      :class:`~llmops.evaluation.thresholds.GateDecision` /
      :func:`~llmops.evaluation.thresholds.load_thresholds`
    * :class:`~llmops.evaluation.runner.EvaluationRunner`
    * :class:`~llmops.evaluation.gate.EvaluationGate` /
      :class:`~llmops.evaluation.gate.GateReport`

The gate is the load-bearing artefact: ``backend/evals/run.py`` calls it and turns
``GateReport.passed`` into the process exit code that ``pr-checks.yml`` blocks on.
"""

from __future__ import annotations

from llmops.evaluation.gate import EvaluationGate, GateReport
from llmops.evaluation.golden import GoldenCase, load_golden
from llmops.evaluation.runner import EvaluationRunner, RunResult
from llmops.evaluation.thresholds import (
    GateDecision,
    Thresholds,
    load_thresholds,
)

__all__ = [
    "GoldenCase",
    "load_golden",
    "Thresholds",
    "GateDecision",
    "load_thresholds",
    "EvaluationRunner",
    "RunResult",
    "EvaluationGate",
    "GateReport",
]
