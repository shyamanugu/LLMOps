"""Promotes human-corrected feedback into golden-dataset-shaped JSONL lines
Evaluation Gate (04) can load directly via its `load_dataset()` — see
docs/decisions/0008-evaluation-gate-scope.md for that format. This is a
data-format bridge, not a code dependency: this component doesn't import
`evaluation_gate`, it only writes lines matching the format that
component's README documents, so a wrong guess about that format would be
caught the moment someone tries to load the file, not silently.
"""
import json
from pathlib import Path
from typing import List

from .types import FeedbackEvent


def promote_to_golden_dataset(events: List[FeedbackEvent], output_path: Path) -> int:
    """Writes one exact_match case per event carrying a human correction —
    `corrected_output` becomes the case's expected value, so a future
    regression that stops producing this corrected answer is caught by
    Evaluation Gate. Events with no `corrected_output` are skipped; a
    thumbs-up/down with no correction isn't a new regression case, it's a
    quality signal with nowhere else to go yet — see "Revisit When" in
    docs/decisions/0011-feedback-scope.md. Returns how many cases were
    written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(output_path, "a", encoding="utf-8") as f:
        for event in events:
            if not event.corrected_output:
                continue
            case = {
                "id": f"feedback_{event.session_id}_{event.step_name}",
                "input": event.original_input,
                "expected": event.corrected_output,
                "evaluator": "exact_match",
            }
            f.write(json.dumps(case) + "\n")
            written += 1
    return written
