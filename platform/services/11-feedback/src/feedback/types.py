"""`FeedbackEvent` — one signal about how good a step's output actually was,
as judged by whoever saw it: an agent, an end customer, or a reviewer.

`rating` is a free-form string by convention, not an enum — different
usecases legitimately want different vocabularies (accept/edit/reject for
an agent-assist tool, up/down for an end-customer survey) and this
component doesn't own that choice. `original_input` is recorded alongside
`corrected_output` because a correction is only useful as a future
regression case if the input that produced the wrong answer is captured
too — see `promotion.py`.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FeedbackEvent:
    session_id: str
    step_name: str
    rating: str
    original_input: dict = field(default_factory=dict)
    corrected_output: Optional[str] = None
    rater_role: str = "end_user"
    comment: str = ""
    timestamp: str = field(default_factory=_now_iso)
