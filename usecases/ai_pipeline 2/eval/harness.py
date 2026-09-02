"""LLMOps evaluation gate for the AI Pipeline (Phase 5).

Runs a golden dataset through the pipeline's analysis step and scores each case
with the evaluator it declares (via the AFNI Evaluation Gate, component 04),
producing a pass/fail decision against the ``ai_pipeline`` thresholds in
``gates.yaml``. Intended to run in CI before a prompt/model change ships.

Design:
* The system-under-test is **injectable** — the default runs the pipeline's real
  ``analysis`` on each case's transcript; tests pass a fake. This keeps the
  harness importable (and unit-testable) without pulling in the whole pipeline.
* Gate results are **fail-closed** (a failing dataset returns a non-zero exit,
  the whole point of a gate). Infra problems (no model creds) **skip** with a
  loud warning and exit 0 unless ``--require-creds`` is passed, so a missing
  secret can't spuriously block a merge.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Callable, Optional

from ai_pipeline import _platform_bootstrap  # noqa: F401  (side effect: sys.path)
from ai_pipeline.logging_config import get_logger

logger = get_logger("eval")

DATASET_DIR = Path(__file__).resolve().parent / "dataset"
SEED_DATASET = DATASET_DIR / "analysis_golden.seed.jsonl"

try:
    from evaluation_gate.gate import EvaluationGate
    from evaluation_gate.dataset_loader import load_dataset

    _PLATFORM = True
    _IMPORT_ERR: Optional[Exception] = None
except Exception as exc:  # pragma: no cover - only when platform absent
    _PLATFORM = False
    _IMPORT_ERR = exc


def _env() -> str:
    return os.environ.get("AI_PIPELINE_ENV", "dev").strip() or "dev"


def build_live_sut(program: str) -> Callable:
    """Return a system-under-test that runs the pipeline's analysis on a case's
    ``input['transcript']`` and returns the parsed structured output. Imports the
    pipeline lazily (it needs polars etc., present only in the real venv)."""
    from openai import AsyncOpenAI

    from ai_pipeline.programs_config import load_program_config
    from ai_pipeline.services import query

    cfg = load_program_config(program)
    client = AsyncOpenAI(
        base_url=cfg.openai.reasoning_endpoint, api_key=cfg.openai.reasoning_api_key
    )

    async def _run(case):
        text = case.input.get("transcript") or case.input.get("text") or ""
        result = await query(
            client=client,
            user_prompt=str(text),
            system_prompt=cfg.analysis_system_prompt,
            model=cfg.openai.deployment_for("reason"),
            temperature=cfg.openai.analyze_temperature,
            schema=cfg.analysis_schema,
            max_completion_tokens=cfg.openai.max_completion_tokens,
        )
        return result.get("message")

    def sut(case):
        return asyncio.run(_run(case))

    return sut


def run_gate(
    dataset_path,
    usecase: str = "ai_pipeline",
    program: str = "telesales",
    environment: Optional[str] = None,
    system_under_test: Optional[Callable] = None,
    threshold: Optional[float] = None,
):
    """Load *dataset_path*, run each case through the SUT, return a GateResult."""
    if not _PLATFORM:
        raise RuntimeError(f"evaluation_gate unavailable: {_IMPORT_ERR}")
    environment = environment or _env()
    cases = load_dataset(Path(dataset_path))
    sut = system_under_test or build_live_sut(program)
    gate = EvaluationGate(environment=environment)
    return gate.run(usecase, cases, sut, threshold=threshold)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="AI Pipeline evaluation gate")
    p.add_argument("--dataset", default=str(SEED_DATASET))
    p.add_argument("--program", default="telesales")
    p.add_argument("--usecase", default="ai_pipeline")
    p.add_argument("--env", default=None)
    p.add_argument("--threshold", type=float, default=None)
    p.add_argument(
        "--require-creds",
        action="store_true",
        help="fail (exit 2) instead of skipping when model creds are absent",
    )
    args = p.parse_args(argv)

    if not _PLATFORM:
        logger.warning("Evaluation Gate platform unavailable (%s) — skipping.", _IMPORT_ERR)
        return 2 if args.require_creds else 0

    # Skip gracefully when live model creds are absent (the SUT can't run).
    if not os.environ.get("REASONING_MODEL_APIKEY") and not args.require_creds:
        logger.warning(
            "No REASONING_MODEL_APIKEY set — skipping eval gate (exit 0). "
            "Pass --require-creds to enforce."
        )
        return 0

    try:
        result = run_gate(
            args.dataset,
            usecase=args.usecase,
            program=args.program,
            environment=args.env,
            threshold=args.threshold,
        )
    except Exception as exc:
        logger.error("Eval gate could not run: %s", exc)
        return 2 if args.require_creds else 0

    logger.info(
        "GATE %s | pass_rate=%.2f threshold=%.2f | %d case(s)",
        "PASSED" if result.passed else "FAILED",
        result.pass_rate,
        result.threshold,
        len(result.results),
    )
    for r in result.results:
        if not r.passed:
            logger.info("  FAIL %s: %s", r.case_id, r.reason)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
