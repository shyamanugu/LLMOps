"""Evaluation thresholds and the pass/fail gate decision.

Loads ``evaluators.yaml`` (config-as-code, mirrors ``platform/evaluators/defaults.yaml``)
into a :class:`Thresholds` model and turns a set of aggregate metric scores into a
:class:`GateDecision`.

Two rule families are supported and combined per metric (all must hold to pass):
    * **Absolute floors/ceilings** — e.g. ``groundedness`` min ``0.9``; ``pii_leak`` max
      ``0`` (any leak fails the gate outright).
    * **Baseline-relative** — the candidate may not regress more than ``baseline_delta``
      below the current baseline (usually ``main``). This catches quality drift even when
      the absolute floor is comfortably met.

The gate is intentionally conservative (fail-safe): a metric that has a threshold but no
score is treated as a failure, and a missing baseline simply disables the relative rule
for that metric rather than silently passing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from llmops.common.errors import ConfigError
from llmops.common.logging import get_logger

_log = get_logger(__name__)

#: Sensible built-in defaults so the gate is usable before a use-case ships its own
#: ``evaluators.yaml``. Higher-is-better metrics use ``min``; violation counts use ``max``.
_DEFAULT_THRESHOLDS: dict[str, dict[str, Any]] = {
    "groundedness": {"min": 0.9, "baseline_delta": 0.02},
    "answer_relevance": {"min": 0.8, "baseline_delta": 0.02},
    "tool_selection_accuracy": {"min": 0.9, "baseline_delta": 0.03},
    "writing_quality": {"min": 0.7, "baseline_delta": 0.05},
    "judge_score": {"min": 0.7, "baseline_delta": 0.05},
    "pii_leak": {"max": 0.0},
}


class MetricThreshold(BaseModel):
    """Threshold rule for a single metric.

    Attributes:
        min: Absolute floor — the score must be ``>= min`` (higher-is-better metrics).
        max: Absolute ceiling — the score must be ``<= max`` (violation-count metrics).
        baseline_delta: Maximum allowed regression below the baseline. With a baseline
            value ``b`` the score must be ``>= b - baseline_delta``. ``None`` disables the
            relative rule for this metric.
        weight: Advisory weight for a blended quality score (not used by the hard gate).
    """

    min: float | None = None
    max: float | None = None
    baseline_delta: float | None = None
    weight: float = 1.0


class Thresholds(BaseModel):
    """Parsed ``evaluators.yaml`` — the per-metric gate configuration."""

    metrics: dict[str, MetricThreshold] = Field(default_factory=dict)
    baseline_source: str = "main"

    def check(
        self,
        scores: dict[str, float],
        baseline: dict[str, float] | None = None,
    ) -> GateDecision:
        """Evaluate ``scores`` against every configured threshold.

        Args:
            scores: Aggregate metric name -> value (typically the mean over the dataset).
            baseline: Optional baseline metric values for the relative rule.

        Returns:
            A :class:`GateDecision` that is ``passed`` only if every metric with a
            threshold satisfies all of its applicable rules.
        """
        baseline = baseline or {}
        results: list[MetricGate] = []

        for metric, rule in self.metrics.items():
            if metric not in scores:
                results.append(
                    MetricGate(
                        metric=metric,
                        value=float("nan"),
                        passed=False,
                        reason="missing score for a metric that has a threshold",
                    )
                )
                continue

            value = scores[metric]
            reasons: list[str] = []
            passed = True

            if rule.min is not None and not value >= rule.min:
                passed = False
                reasons.append(f"{value:.4f} < min {rule.min:.4f}")
            if rule.max is not None and not value <= rule.max:
                passed = False
                reasons.append(f"{value:.4f} > max {rule.max:.4f}")

            base_value = baseline.get(metric)
            if rule.baseline_delta is not None and base_value is not None:
                floor = base_value - rule.baseline_delta
                if not value >= floor:
                    passed = False
                    reasons.append(
                        f"regressed to {value:.4f}; baseline {base_value:.4f} "
                        f"allows down to {floor:.4f}"
                    )

            results.append(
                MetricGate(
                    metric=metric,
                    value=value,
                    baseline=base_value,
                    threshold_min=rule.min,
                    threshold_max=rule.max,
                    baseline_delta=rule.baseline_delta,
                    passed=passed,
                    reason="ok" if passed else "; ".join(reasons),
                )
            )

        overall = all(r.passed for r in results) if results else True
        failures = [r.metric for r in results if not r.passed]
        decision = GateDecision(passed=overall, metrics=results, failures=failures)
        _log.info(
            "threshold check complete",
            passed=overall,
            failures=failures,
            evaluated=len(results),
        )
        return decision


class MetricGate(BaseModel):
    """Per-metric outcome inside a :class:`GateDecision`."""

    metric: str
    value: float
    baseline: float | None = None
    threshold_min: float | None = None
    threshold_max: float | None = None
    baseline_delta: float | None = None
    passed: bool
    reason: str = "ok"


class GateDecision(BaseModel):
    """Aggregate gate outcome across all thresholded metrics."""

    passed: bool
    metrics: list[MetricGate] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)

    def summary(self) -> str:
        """Return a one-line human summary suitable for CI logs."""
        status = "PASS" if self.passed else "FAIL"
        if self.passed:
            return f"{status}: {len(self.metrics)} metric(s) within thresholds"
        return f"{status}: {', '.join(self.failures)}"


def load_thresholds(path: str | Path | None = None) -> Thresholds:
    """Load thresholds from ``evaluators.yaml``, degrading to built-in defaults.

    Args:
        path: Path to the evaluators YAML. Defaults to
            ``platform/evaluators/defaults.yaml`` relative to the repo root.

    Returns:
        A validated :class:`Thresholds`. If the file is absent (common in dev), a warning
        is logged and the built-in defaults are returned so callers never crash.

    Raises:
        ConfigError: If the file exists but cannot be parsed.
    """
    p = Path(path) if path is not None else Path("platform/evaluators/defaults.yaml")
    if not p.exists():
        _log.warning("evaluators.yaml not found; using built-in defaults", path=str(p))
        return Thresholds(
            metrics={k: MetricThreshold(**v) for k, v in _DEFAULT_THRESHOLDS.items()},
        )
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"failed to parse evaluators.yaml: {exc}", detail={"path": str(p)}) from exc

    metrics_raw = raw.get("metrics", raw.get("thresholds", {}))
    if not isinstance(metrics_raw, dict):
        raise ConfigError("evaluators.yaml 'metrics' must be a mapping", detail={"path": str(p)})

    metrics = {name: MetricThreshold.model_validate(cfg) for name, cfg in metrics_raw.items()}
    baseline_source = str(raw.get("baseline", {}).get("source", "main"))
    _log.info("loaded evaluator thresholds", path=str(p), metrics=list(metrics))
    return Thresholds(metrics=metrics, baseline_source=baseline_source)
