"""LLMOps feedback loop for the AI Pipeline (Phase 6).

Thin adapter over the AFNI Feedback service (component 11). Captures human
signals about a step's output (a coach's correction, a reviewer's reject) and
**promotes** the ones carrying a correction into a golden dataset the Evaluation
Gate (Phase 5) can load — closing the improve loop: production correction →
golden case → CI gate.

Storage is a local JSONL by default (``AI_PIPELINE_FEEDBACK_PATH`` or
``feedback/feedback.jsonl`` under the package); swap in ``AzureBlobFeedbackStore``
for shared/durable storage once live. Fail-open: capture never raises into the
caller.

CLI:
    python -m ai_pipeline.feedback_gate record --step analysis --rating reject \
        --input '{"transcript": "..."}' --corrected '{"score": 4}' --role coach
    python -m ai_pipeline.feedback_gate promote          # -> eval/dataset/promoted_golden.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional

from ai_pipeline import _platform_bootstrap  # noqa: F401  (side effect: sys.path)
from ai_pipeline.logging_config import get_logger

logger = get_logger("feedback")

_PKG_ROOT = Path(__file__).resolve().parent
_DEFAULT_STORE = _PKG_ROOT / "feedback" / "feedback.jsonl"
_DEFAULT_GOLDEN = _PKG_ROOT / "eval" / "dataset" / "promoted_golden.jsonl"

try:
    from feedback.store import JsonlFileFeedbackStore
    from feedback.types import FeedbackEvent
    from feedback.promotion import promote_to_golden_dataset

    _PLATFORM = True
except Exception as exc:  # pragma: no cover - only when platform absent
    logger.warning("LLMOps feedback unavailable (%s) — feedback disabled", exc)
    _PLATFORM = False


def _store_path(path: Optional[Path] = None) -> Path:
    if path is not None:
        return Path(path)
    env = os.environ.get("AI_PIPELINE_FEEDBACK_PATH", "").strip()
    return Path(env) if env else _DEFAULT_STORE


def _current_session_id() -> str:
    """Best-effort: reuse the current pipeline run id if one is set."""
    try:
        from ai_pipeline import observability as obs

        return obs._run_id.get() or "adhoc"
    except Exception:
        return "adhoc"


def record_feedback(
    step_name: str,
    rating: str,
    *,
    original_input: Optional[dict] = None,
    corrected_output: Optional[str] = None,
    rater_role: str = "reviewer",
    comment: str = "",
    session_id: Optional[str] = None,
    path: Optional[Path] = None,
) -> bool:
    """Record one feedback signal. Returns True if stored, False if disabled.

    ``corrected_output`` should be a string (e.g. JSON) — only events that carry
    a correction become regression cases on promotion.
    """
    if not _PLATFORM:
        return False
    try:
        event = FeedbackEvent(
            session_id=session_id or _current_session_id(),
            step_name=step_name,
            rating=rating,
            original_input=original_input or {},
            corrected_output=corrected_output,
            rater_role=rater_role,
            comment=comment,
        )
        JsonlFileFeedbackStore(path=_store_path(path)).record(event)
        return True
    except Exception as exc:
        logger.warning("record_feedback failed: %s", exc)
        return False


def _load_all_events(path: Path) -> list:
    if not path.exists():
        return []
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(FeedbackEvent(**json.loads(line)))
            except Exception:
                continue
    return events


def promote(
    session_id: Optional[str] = None,
    *,
    path: Optional[Path] = None,
    dataset_path: Optional[Path] = None,
) -> int:
    """Promote corrections into a golden dataset the Eval Gate can load.
    Returns the number of regression cases written (events without a correction
    are skipped by the platform). Optionally filter to one ``session_id``."""
    if not _PLATFORM:
        return 0
    store_path = _store_path(path)
    events = _load_all_events(store_path)
    if session_id is not None:
        events = [e for e in events if e.session_id == session_id]
    out = Path(dataset_path) if dataset_path else _DEFAULT_GOLDEN
    written = promote_to_golden_dataset(events, out)
    logger.info("Promoted %d correction(s) -> %s", written, out)
    return written


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="AI Pipeline feedback loop")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="record a feedback signal")
    r.add_argument("--step", required=True)
    r.add_argument("--rating", required=True, help="free-form, e.g. accept|edit|reject|up|down")
    r.add_argument("--input", default="{}", help="original input as JSON")
    r.add_argument("--corrected", default=None, help="corrected output (string/JSON)")
    r.add_argument("--role", default="reviewer")
    r.add_argument("--comment", default="")
    r.add_argument("--session", default=None)

    pr = sub.add_parser("promote", help="promote corrections into the golden dataset")
    pr.add_argument("--session", default=None)
    pr.add_argument("--out", default=None)

    args = p.parse_args(argv)
    if not _PLATFORM:
        logger.error("Feedback platform unavailable — nothing to do.")
        return 1

    if args.cmd == "record":
        try:
            original_input = json.loads(args.input)
        except json.JSONDecodeError:
            original_input = {"raw": args.input}
        ok = record_feedback(
            args.step, args.rating,
            original_input=original_input, corrected_output=args.corrected,
            rater_role=args.role, comment=args.comment, session_id=args.session,
        )
        print("recorded" if ok else "failed")
        return 0 if ok else 1

    if args.cmd == "promote":
        n = promote(session_id=args.session, dataset_path=Path(args.out) if args.out else None)
        print(f"promoted {n} case(s)")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
