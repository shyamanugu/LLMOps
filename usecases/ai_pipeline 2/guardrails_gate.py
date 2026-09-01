"""LLMOps guardrails integration (Phase 3 — thin adapter).

Wraps the AFNI LLMOps Guardrails service (platform component 06). Builds one
``CompositeGuardrail`` per run from ``guardrails.yaml`` and exposes simple
``check_input``/``check_output`` helpers that ``services.query`` calls around
every LLM invocation.

Fail-open, like the rest of the integration: if the platform is unavailable or
policy construction fails, the checks pass everything through and the pipeline
runs unchanged. The policy for this usecase (``ai_pipeline``) deliberately
*flags* PII rather than blocking it — call transcripts legitimately contain
customer PII, and dropping those rows would corrupt the analytics — while
blocking genuine secret leaks. See ``guardrails.yaml``.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

from ai_pipeline import _platform_bootstrap  # noqa: F401  (side effect: sys.path)
from ai_pipeline.logging_config import get_logger

logger = get_logger("guardrails")

try:
    from guardrails.builder import build_guardrail

    _PLATFORM = True
except Exception as exc:  # pragma: no cover - only when platform absent
    logger.warning("LLMOps guardrails unavailable (%s) — guardrails disabled", exc)
    _PLATFORM = False

_GUARDRAIL = None


def init_guardrail(usecase: str = "ai_pipeline", environment: Optional[str] = None):
    """Build the composite guardrail once per run. Safe if platform absent."""
    global _GUARDRAIL
    if not _PLATFORM:
        _GUARDRAIL = None
        return None
    env = environment or os.environ.get("AI_PIPELINE_ENV", "dev").strip() or "dev"
    try:
        _GUARDRAIL = build_guardrail(usecase, env)
        logger.info("Guardrails active | usecase=%s env=%s", usecase, env)
    except Exception as exc:
        logger.warning("build_guardrail(%s,%s) failed (%s) — guardrails disabled", usecase, env, exc)
        _GUARDRAIL = None
    return _GUARDRAIL


def _check(method: str, text: str) -> Tuple[bool, str]:
    if _GUARDRAIL is None or not text:
        return True, ""
    try:
        result = getattr(_GUARDRAIL, method)(text)
        return result.allowed, result.reason or ""
    except Exception as exc:  # never let a guardrail error break a run
        logger.debug("%s error: %s", method, exc)
        return True, ""


def check_input(text: str) -> Tuple[bool, str]:
    """Returns (allowed, reason). reason is set even when allowed (flags)."""
    return _check("check_input", text)


def check_output(text: str) -> Tuple[bool, str]:
    return _check("check_output", text)
