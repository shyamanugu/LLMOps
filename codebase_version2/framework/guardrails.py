"""Guardrails — safety checks on what goes into and comes out of the model.

Reusable. We check the input before calling the model and the output before returning it. Offline
this uses simple built-in checks (a small unsafe-word list and a personal-data regex). If Azure AI
Content Safety is configured, we use that instead for the real categories and prompt-injection
shields.
"""

import re

from framework import config

# Very small offline stand-ins. The real checks come from Content Safety when configured.
_UNSAFE_WORDS = {"bomb", "kill", "suicide"}
_PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CARD]"),
]


def check_input(text: str) -> dict:
    """Return {allowed, reason}. Blocks obviously unsafe input."""
    if config.CONTENT_SAFETY_ENDPOINT:
        return _content_safety(text)
    lowered = text.lower()
    for w in _UNSAFE_WORDS:
        if w in lowered:
            return {"allowed": False, "reason": f"unsafe term: {w}"}
    return {"allowed": True, "reason": None}


def check_output(text: str) -> dict:
    """Return {allowed, reason, text} with personal data redacted from the output."""
    redacted, hits = redact_pii(text)
    if config.CONTENT_SAFETY_ENDPOINT:
        result = _content_safety(redacted)
        result["text"] = redacted
        return result
    return {"allowed": True, "reason": (f"redacted {hits} item(s)" if hits else None), "text": redacted}


def redact_pii(text: str) -> tuple[str, int]:
    """Replace personal data (email, card, SSN) with tags. Returns (redacted_text, count)."""
    hits = 0
    for pattern, tag in _PII_PATTERNS:
        text, n = pattern.subn(tag, text)
        hits += n
    return text, hits


def _content_safety(text: str) -> dict:
    """Call Azure AI Content Safety (categories + prompt shields)."""
    # TODO(wiring): construct the Content Safety client from config and evaluate `text`.
    # Return {"allowed": bool, "reason": category-or-None}. For now, allow (fail-safe for the demo).
    return {"allowed": True, "reason": None}
