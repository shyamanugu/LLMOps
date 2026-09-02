"""AI Pipeline Orchestrator.

Usage
-----
    # Single program mode (existing)
    python -m ai_pipeline.main --program telesales
    python -m ai_pipeline.main --program telesales --date 2025-08-28
    python -m ai_pipeline.main --program telesales --step denoise

    # Mode-based (filters by program names from .env)
    python -m ai_pipeline.main --mode telesales
    python -m ai_pipeline.main --mode wcc --date 2025-08-28
    python -m ai_pipeline.main --mode "telesales|wcc" --step analysis

    # Date range
    python -m ai_pipeline.main --program telesales --start 2025-08-01 --end 2025-08-07 --step analysis
    python -m ai_pipeline.main --mode wcc --start 2025-08-01 --end 2025-08-07

Steps
-----
    denoise   → Transcription cleanup via LLM
    analysis  → Per-call evaluation via LLM (structured output)
    summary   → Weekly per-employee aggregation + LLM reflection
    kpi       → Post-summary KPI aggregation → CSV upload
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
import uuid
import sys
from datetime import date, datetime, timedelta, timezone

from ai_pipeline.programs_config import load_program_config, load_mode_config
from ai_pipeline.logging_config import setup_logging, get_logger
from ai_pipeline import observability as obs
from ai_pipeline import guardrails_gate as gate
from ai_pipeline import mode as run_mode
from ai_pipeline.services.storage import make_storage
from ai_pipeline.steps import run_denoise, run_analysis, run_summary, run_individual_metrics
from ai_pipeline.steps.kpi_aggregator import run_kpi_aggregator

STEPS = {
    "denoise": run_denoise,
    "analysis": run_analysis,
    "summary": run_summary,
    "individual_metrics": run_individual_metrics,
    "kpi": run_kpi_aggregator,
}
STEP_ORDER = ["denoise", "analysis", "summary", "individual_metrics", "kpi"]


def _date_range(start: date, end: date) -> list[date]:
    """Return an inclusive list of dates from *start* to *end*."""
    days = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=1)
    return days


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="AI Pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--program", default=None, help="Program config id (e.g. telesales, wcc)")
    group.add_argument("--mode", default=None, help="Processing mode(s) — filters by mapped programs from .env. Use | to combine (e.g. telesales|wcc)")
    parser.add_argument("--date", default=None, help="Processing date YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--start", default=None, help="Start date YYYY-MM-DD (inclusive) for date-range mode")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD (inclusive) for date-range mode")
    parser.add_argument("--step", default=None, choices=STEP_ORDER, help="Run a single step instead of the full pipeline")
    parser.add_argument("--coach", default=None, help="CoachID allow-list: single (9040400), multiple comma-separated (9040400,3000510), or 'all' for every coach")
    parser.add_argument("--agent", default=None, help="EmployeeID allow-list (for datasets without CoachID): single, comma-separated, or 'all'")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args(argv)


async def run_pipeline(args):
    run_id = uuid.uuid4().hex[:8]
    setup_logging(level=args.log_level, pipeline_run_id=run_id)
    logger = get_logger("main")

    # LLMOps observability (Phase 1): choose a tracer for this run. Fail-open —
    # a no-op if the platform packages aren't importable.
    environment = obs.current_environment()
    obs.init_tracer(environment)
    gate.init_guardrail("ai_pipeline", environment)

    # Runtime data mode: 'mock' (self-contained demo) or 'real' (live Azure DB).
    data_mode = run_mode.runtime_mode()
    logger.info("Runtime data mode: %s", data_mode.upper())
    if run_mode.is_real() and not os.environ.get("SALES_STORAGE_ACCOUNT_NAME"):
        logger.warning(
            "AI_PIPELINE_MODE=real but SALES_STORAGE_ACCOUNT_NAME is unset — live reads will fail. "
            "Fill the Storage/SQL blocks in .env, or set AI_PIPELINE_MODE=mock for a self-contained demo."
        )

    logger.info("Pipeline starting | program=%s mode=%s run_id=%s env=%s data_mode=%s",
                args.program, args.mode, run_id, environment, data_mode)

    if args.mode:
        cfg = load_mode_config(args.mode)
    else:
        cfg = load_program_config(args.program)

    obs.set_run_context(run_id, cfg.program_id or args.program or args.mode or "unknown", environment)

    # CLI coach filter overrides the env-derived default when provided.
    # Accept "all"/"*" (case-insensitive) to explicitly process every coach.
    if args.coach:
        if args.coach.strip().lower() in ("all", "*"):
            cfg.coach_filter = None
            logger.info("Coach filter: ALL coaches (no CoachID restriction)")
        else:
            cfg.coach_filter = [int(c.strip()) for c in args.coach.split(",") if c.strip()]
            logger.info("Coach filter set from CLI: %s", cfg.coach_filter)
    if args.agent:
        if args.agent.strip().lower() in ("all", "*"):
            cfg.agent_filter = None
            logger.info("Agent filter: ALL agents (no EmployeeID restriction)")
        else:
            cfg.agent_filter = [int(a.strip()) for a in args.agent.split(",") if a.strip()]
            logger.info("Agent filter set from CLI: %s", cfg.agent_filter)

    storage = make_storage(cfg.storage)  # local FS in mock mode, Azure Blob in real mode

    # Determine date(s) to process
    if args.start and args.end:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
        dates = _date_range(start, end)
        logger.info("Date range mode: %s -> %s (%d days)", start, end, len(dates))
    elif args.date:
        dates = [datetime.strptime(args.date, "%Y-%m-%d").date()]
    else:
        dates = [datetime.now(timezone.utc).date()]

    steps_to_run = [args.step] if args.step else STEP_ORDER
    total = len(dates)
    processed: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    pipeline_start = time.perf_counter()

    for i, date_utc in enumerate(dates, 1):
        tag = f"[{i}/{total}] {date_utc}"
        logger.info("%s | START (steps: %s)", tag, ", ".join(steps_to_run))
        try:
            for step_name in steps_to_run:
                logger.info("%s | step '%s' running...", tag, step_name)
                await STEPS[step_name](date_utc, cfg, storage)
                logger.info("%s | step '%s' done", tag, step_name)
            processed.append(str(date_utc))
            logger.info("%s | DONE", tag)
        except FileNotFoundError as exc:
            skipped.append(str(date_utc))
            logger.warning("%s | SKIPPED (no source data): %s", tag, exc)
        except Exception:
            failed.append(str(date_utc))
            logger.exception("%s | FAILED", tag)

    # ── Emit one LLMOps PipelineEvent for the whole invocation ────────────
    obs.record_pipeline(
        step_count=len(dates) * len(steps_to_run),
        total_latency_ms=(time.perf_counter() - pipeline_start) * 1000,
        error=("; ".join(failed) if failed else None),
    )

    # ── Final run summary ────────────────────────────────────────────────
    logger.info("===== RUN SUMMARY | program=%s mode=%s run_id=%s =====", args.program, args.mode, run_id)
    logger.info("Processed (%d/%d): %s", len(processed), total, ", ".join(processed) or "none")
    logger.info("Skipped   (%d/%d): %s", len(skipped), total, ", ".join(skipped) or "none")
    logger.info("Failed    (%d/%d): %s", len(failed), total, ", ".join(failed) or "none")

    totals = obs.run_totals()
    if totals:
        logger.info(
            "LLM usage | calls=%d in_tok=%d out_tok=%d cost_usd=%s errors=%d",
            totals["llm_calls"], totals["input_tokens"], totals["output_tokens"],
            totals["cost_usd"], totals["errors"],
        )

    if failed:
        logger.error("Completed with %d failed date(s) — see traceback(s) above.", len(failed))
    else:
        logger.info("Completed successfully.")


def main():
    args = parse_args()
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
