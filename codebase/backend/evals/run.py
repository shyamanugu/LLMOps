"""CLI entrypoint for the evaluation gate — the CI quality barrier.

Invoked by ``.github/workflows/pr-checks.yml`` (and locally) as, e.g.::

    python evals/run.py --usecase apix --subset changed --fail-under baseline

It runs :class:`llmops.evaluation.gate.EvaluationGate`, prints a CI-friendly summary, and
sets the process exit code: ``0`` when the gate passes, ``1`` when any thresholded metric
fails (which blocks the PR). This is a thin synchronous wrapper around the async gate — the
only place a sync wrapper is allowed (per the conventions in ARCHITECTURE_SPEC §6).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure ``src`` is importable when run directly from the backend directory.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llmops.common.logging import configure_logging, get_logger  # noqa: E402
from llmops.evaluation.gate import EvaluationGate, GateReport  # noqa: E402

_log = get_logger(__name__)

#: Map the ``--subset`` CLI vocabulary to the gate's scope literals.
_SUBSET_TO_SCOPE = {"changed": "changed", "full": "full", "smoke": "smoke"}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the LLMOps evaluation gate for a use-case.")
    parser.add_argument("--usecase", required=True, help="Use-case name (dir under usecases/).")
    parser.add_argument(
        "--subset",
        choices=sorted(_SUBSET_TO_SCOPE),
        default="changed",
        help="Which cases to run: changed (PR), full (nightly), or smoke.",
    )
    parser.add_argument(
        "--fail-under",
        default="baseline",
        help="Threshold policy: 'baseline' uses evaluators.yaml (baseline-relative + floors).",
    )
    parser.add_argument("--usecases-dir", default="usecases", help="Root of use-case dirs.")
    parser.add_argument("--json", action="store_true", help="Emit the GateReport as JSON.")
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> GateReport:
    """Execute the gate and return its report."""
    scope = _SUBSET_TO_SCOPE[args.subset]
    gate = EvaluationGate(usecases_dir=args.usecases_dir)
    return await gate.run(args.usecase, scope)  # type: ignore[arg-type]


def main(argv: list[str] | None = None) -> int:
    """Run the gate and return the process exit code (0 pass, 1 fail).

    Args:
        argv: Optional argument vector (defaults to ``sys.argv``).

    Returns:
        ``0`` if the gate passed, ``1`` otherwise.
    """
    args = _parse_args(argv)
    configure_logging()

    # The ``--fail-under baseline`` policy is the default and only supported policy today;
    # numeric overrides would be applied here as an absolute floor across metrics.
    if args.fail_under != "baseline":
        _log.warning("only --fail-under baseline is supported; using evaluators.yaml", given=args.fail_under)

    try:
        report = asyncio.run(_run(args))
    except Exception as exc:  # noqa: BLE001 - surface config/run errors as a hard failure
        _log.error("evaluation gate errored", usecase=args.usecase, error=str(exc))
        print(f"evaluation gate ERROR for '{args.usecase}': {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, default=str))
    else:
        print(report.as_ci_summary())

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
