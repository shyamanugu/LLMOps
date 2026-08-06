"""The evaluation gate — the CI quality barrier for a use-case.

:class:`EvaluationGate` ties the pieces together: it loads a use-case's golden dataset,
runs the pipeline over it via :class:`~llmops.evaluation.runner.EvaluationRunner`,
aggregates metric scores, fetches the baseline for the baseline-relative rule, and applies
:class:`~llmops.evaluation.thresholds.Thresholds`. It returns a :class:`GateReport` whose
``passed`` flag drives ``backend/evals/run.py``'s process exit code (non-zero blocks the
PR in ``pr-checks.yml``).

Two run scopes:
    * ``full``    — the entire golden set (nightly / ``eval-full.yml``).
    * ``changed`` — only cases affected by the PR (fast PR check). Deriving the changed set
      requires VCS/registry wiring, so in dev it degrades to the ``smoke`` suite.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from llmops.common.errors import ConfigError
from llmops.common.logging import get_logger
from llmops.evaluation.golden import GoldenCase, load_golden, select_subset
from llmops.evaluation.runner import EvaluationRunner, PipelineLike, RunResult
from llmops.evaluation.thresholds import GateDecision, Thresholds, load_thresholds

_log = get_logger(__name__)

Scope = Literal["full", "changed", "smoke"]


class GateReport(BaseModel):
    """The outcome of a gate run, suitable for CI logs and the console."""

    usecase: str
    scope: str
    passed: bool
    decision: GateDecision
    aggregate: dict[str, float] = Field(default_factory=dict)
    baseline: dict[str, float] = Field(default_factory=dict)
    baseline_source: str = "main"
    total_cases: int = 0
    errored_cases: int = 0
    duration_ms: int = 0
    generated_at: float = Field(default_factory=time.time)

    def as_ci_summary(self) -> str:
        """Return a compact multi-line summary for CI output."""
        lines = [
            f"evaluation gate: {self.usecase} [{self.scope}] -> "
            f"{'PASS' if self.passed else 'FAIL'}",
            f"  cases: {self.total_cases} (errors: {self.errored_cases})",
            f"  baseline: {self.baseline_source}",
        ]
        for gate in self.decision.metrics:
            flag = "ok" if gate.passed else "FAIL"
            lines.append(f"  [{flag}] {gate.metric}={gate.value:.4f} - {gate.reason}")
        return "\n".join(lines)


class EvaluationGate:
    """Runs golden evaluations for a use-case and decides pass/fail against thresholds."""

    def __init__(
        self,
        *,
        usecases_dir: str | Path = "usecases",
        thresholds: Thresholds | None = None,
        pipeline_factory: Any | None = None,
    ) -> None:
        """Initialise the gate.

        Args:
            usecases_dir: Root directory holding ``<usecase>/evals/*.jsonl`` and pipelines.
            thresholds: Pre-loaded thresholds; if ``None`` they are loaded from
                ``platform/evaluators/defaults.yaml`` (or a per-usecase override).
            pipeline_factory: Optional callable ``(usecase) -> PipelineLike`` for injecting
                a pipeline in tests; production wiring uses the orchestration package.
        """
        self._usecases_dir = Path(usecases_dir)
        self._thresholds = thresholds
        self._pipeline_factory = pipeline_factory

    # -- dataset / config discovery -----------------------------------------
    def _golden_path(self, usecase: str, scope: Scope) -> Path:
        """Return the JSONL dataset path for the use-case."""
        base = self._usecases_dir / usecase / "evals"
        # Prefer a scope-specific file when present, else the canonical golden.jsonl.
        candidates = [base / f"{scope}.jsonl", base / "golden.jsonl", base / "cases.jsonl"]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise ConfigError(
            f"no golden dataset found for usecase '{usecase}'",
            detail={"searched": [str(c) for c in candidates]},
        )

    def _load_thresholds(self, usecase: str) -> Thresholds:
        """Load thresholds, preferring a per-usecase override file."""
        if self._thresholds is not None:
            return self._thresholds
        override = self._usecases_dir / usecase / "evals" / "evaluators.yaml"
        if override.exists():
            return load_thresholds(override)
        return load_thresholds()

    def _select(self, cases: list[GoldenCase], scope: Scope) -> list[GoldenCase]:
        """Pick the subset of cases to run for the given scope."""
        if scope == "full":
            return cases
        if scope == "smoke":
            smoke = select_subset(cases, suite="smoke")
            return smoke or cases
        # scope == "changed"
        changed_ids = self._changed_case_ids()
        if changed_ids is None:
            _log.warning("changed-set detection unavailable; running smoke suite")
            smoke = select_subset(cases, suite="smoke")
            return smoke or cases
        return select_subset(cases, ids=changed_ids)

    def _changed_case_ids(self) -> list[str] | None:
        """Return the case ids affected by the current PR, if derivable.

        Returns ``None`` when the changed set cannot be determined offline.
        """
        # TODO(wiring): derive changed golden ids from the PR diff (git) and/or prompt
        # registry version bumps, so PR checks only run affected cases.
        return None

    def _load_baseline(self, usecase: str) -> dict[str, float]:
        """Load baseline metric values for the baseline-relative rule.

        Reads ``usecases/<uc>/evals/baseline.json`` when present. In production this comes
        from the last green gate report stored in App Insights / the eval history.
        """
        # TODO(wiring): fetch the baseline aggregate from stored gate history
        # (App Insights custom events / Langfuse) for the target branch.
        path = self._usecases_dir / usecase / "evals" / "baseline.json"
        if not path.exists():
            return {}
        try:
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
            return {str(k): float(v) for k, v in data.get("metrics", data).items()}
        except Exception as exc:  # noqa: BLE001
            _log.warning("could not read baseline.json", error=str(exc))
            return {}

    def _build_pipeline(self, usecase: str) -> PipelineLike | None:
        """Construct the use-case pipeline, or ``None`` to fall back to the dev stand-in."""
        if self._pipeline_factory is not None:
            return self._pipeline_factory(usecase)
        try:
            from llmops.orchestration.pipeline import Pipeline  # type: ignore[import-not-found]

            # TODO(wiring): confirm the exact factory once orchestration lands; try the
            # documented loader path first.
            loader = getattr(Pipeline, "from_usecase", None)
            if callable(loader):
                return loader(usecase)  # type: ignore[no-any-return]
            path = self._usecases_dir / usecase / "agents" / "pipeline.agent.yaml"
            from_yaml = getattr(Pipeline, "from_yaml", None)
            if callable(from_yaml) and path.exists():
                return from_yaml(path)  # type: ignore[no-any-return]
        except Exception as exc:  # noqa: BLE001
            _log.warning("could not build pipeline; using dev stand-in", error=str(exc))
        return None

    # -- public API ---------------------------------------------------------
    async def run(self, usecase: str, scope: Scope = "full") -> GateReport:
        """Run the gate for a use-case and return a :class:`GateReport`.

        Args:
            usecase: The use-case name (directory under ``usecases/``).
            scope: ``full`` | ``changed`` | ``smoke``.

        Returns:
            A :class:`GateReport`; ``report.passed`` is ``False`` if any thresholded metric
            fails, which callers translate into a non-zero exit code.
        """
        start = time.perf_counter()
        _log.info("evaluation gate starting", usecase=usecase, scope=scope)

        cases = load_golden(self._golden_path(usecase, scope))
        selected = self._select(cases, scope)
        thresholds = self._load_thresholds(usecase)
        baseline = self._load_baseline(usecase)

        pipeline = self._build_pipeline(usecase)
        runner = EvaluationRunner(pipeline=pipeline)
        run_result: RunResult = await runner.run(selected, usecase=usecase)

        decision = thresholds.check(run_result.aggregate, baseline=baseline)
        duration = int((time.perf_counter() - start) * 1000)
        report = GateReport(
            usecase=usecase,
            scope=scope,
            passed=decision.passed,
            decision=decision,
            aggregate=run_result.aggregate,
            baseline=baseline,
            baseline_source=thresholds.baseline_source,
            total_cases=run_result.total,
            errored_cases=run_result.errors,
            duration_ms=duration,
        )
        _log.info(
            "evaluation gate complete",
            usecase=usecase,
            scope=scope,
            passed=report.passed,
            failures=decision.failures,
        )
        return report
