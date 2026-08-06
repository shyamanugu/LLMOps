"""Unit tests for the evaluation threshold gate (pure logic, no I/O)."""

from __future__ import annotations

from llmops.evaluation.thresholds import (
    MetricThreshold,
    Thresholds,
    load_thresholds,
)


def _thresholds() -> Thresholds:
    """Return a representative threshold config exercising both rule families."""
    return Thresholds(
        metrics={
            "groundedness": MetricThreshold(min=0.9, baseline_delta=0.02),
            "tool_selection_accuracy": MetricThreshold(min=0.9, baseline_delta=0.03),
            "pii_leak": MetricThreshold(max=0.0),
        }
    )


def test_all_metrics_within_floors_passes() -> None:
    scores = {"groundedness": 0.95, "tool_selection_accuracy": 0.92, "pii_leak": 0.0}
    decision = _thresholds().check(scores)
    assert decision.passed is True
    assert decision.failures == []


def test_absolute_floor_violation_fails() -> None:
    scores = {"groundedness": 0.85, "tool_selection_accuracy": 0.95, "pii_leak": 0.0}
    decision = _thresholds().check(scores)
    assert decision.passed is False
    assert "groundedness" in decision.failures


def test_pii_leak_ceiling_zero_is_strict() -> None:
    # Any leak at all (count > 0) must fail the gate outright.
    scores = {"groundedness": 0.99, "tool_selection_accuracy": 0.99, "pii_leak": 1.0}
    decision = _thresholds().check(scores)
    assert decision.passed is False
    assert "pii_leak" in decision.failures


def test_pii_leak_zero_passes() -> None:
    scores = {"groundedness": 0.99, "tool_selection_accuracy": 0.99, "pii_leak": 0.0}
    decision = _thresholds().check(scores)
    assert decision.passed is True


def test_baseline_relative_regression_fails_even_above_floor() -> None:
    # 0.91 clears the 0.90 floor but regresses 0.05 below a 0.96 baseline (delta 0.02).
    scores = {"groundedness": 0.91, "tool_selection_accuracy": 0.99, "pii_leak": 0.0}
    baseline = {"groundedness": 0.96}
    decision = _thresholds().check(scores, baseline=baseline)
    assert decision.passed is False
    assert "groundedness" in decision.failures


def test_baseline_relative_small_regression_within_delta_passes() -> None:
    # 0.945 is only 0.015 below the 0.96 baseline — within the 0.02 delta, and above floor.
    scores = {"groundedness": 0.945, "tool_selection_accuracy": 0.99, "pii_leak": 0.0}
    baseline = {"groundedness": 0.96}
    decision = _thresholds().check(scores, baseline=baseline)
    assert decision.passed is True


def test_missing_score_for_thresholded_metric_fails() -> None:
    # tool_selection_accuracy has a threshold but no score -> fail-safe failure.
    scores = {"groundedness": 0.99, "pii_leak": 0.0}
    decision = _thresholds().check(scores)
    assert decision.passed is False
    assert "tool_selection_accuracy" in decision.failures


def test_no_baseline_disables_relative_rule() -> None:
    # Without a baseline value, only the absolute floor applies.
    scores = {"groundedness": 0.91, "tool_selection_accuracy": 0.99, "pii_leak": 0.0}
    decision = _thresholds().check(scores, baseline={})
    assert decision.passed is True


def test_load_thresholds_missing_file_returns_defaults() -> None:
    thresholds = load_thresholds("does/not/exist.yaml")
    assert "groundedness" in thresholds.metrics
    assert thresholds.metrics["groundedness"].min == 0.9
    assert thresholds.metrics["pii_leak"].max == 0.0


def test_load_thresholds_from_yaml(tmp_path) -> None:
    yaml_text = (
        "baseline:\n"
        "  source: main\n"
        "metrics:\n"
        "  groundedness: { min: 0.8, baseline_delta: 0.05 }\n"
        "  pii_leak: { max: 0.0 }\n"
    )
    path = tmp_path / "evaluators.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    thresholds = load_thresholds(path)
    assert thresholds.baseline_source == "main"
    assert thresholds.metrics["groundedness"].min == 0.8
    decision = thresholds.check({"groundedness": 0.82, "pii_leak": 0.0})
    assert decision.passed is True


def test_summary_lists_failures() -> None:
    decision = _thresholds().check({"groundedness": 0.1, "tool_selection_accuracy": 0.99, "pii_leak": 0.0})
    assert decision.summary().startswith("FAIL")
