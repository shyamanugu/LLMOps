"""Exception hierarchy for the LLMOps platform.

All platform exceptions derive from :class:`LLMOpsError` so callers (and the FastAPI
exception handlers in ``llmops.api.main``) can catch a single base type and map it to a
stable HTTP response. Each error carries a machine-readable ``code`` and an optional
``detail`` payload for structured logging.
"""

from __future__ import annotations

from typing import Any


class LLMOpsError(Exception):
    """Base class for every error raised by the platform.

    Attributes:
        code: Stable, machine-readable identifier (e.g. ``"unknown_alias"``).
        message: Human-readable message.
        detail: Optional structured context safe to log (never secrets).
        http_status: Suggested HTTP status code for API surfaces.
    """

    code: str = "llmops_error"
    http_status: int = 500

    def __init__(self, message: str, *, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation for API responses."""
        return {"code": self.code, "message": self.message, "detail": self.detail}


class ConfigError(LLMOpsError):
    """Raised when configuration is missing or invalid."""

    code = "config_error"
    http_status = 500


class UnknownAliasError(LLMOpsError):
    """Raised when a model task-alias is not defined for the environment."""

    code = "unknown_alias"
    http_status = 400


class PromptNotFoundError(LLMOpsError):
    """Raised when a prompt id/label cannot be resolved by the registry."""

    code = "prompt_not_found"
    http_status = 404


class PromptRenderError(LLMOpsError):
    """Raised when required template variables are missing at render time."""

    code = "prompt_render_error"
    http_status = 400


class GuardrailBlocked(LLMOpsError):
    """Raised when a guardrail blocks an input or output.

    This is an expected, non-exceptional control-flow signal; callers should catch it
    and return a safe response rather than a 500.
    """

    code = "guardrail_blocked"
    http_status = 422


class ToolError(LLMOpsError):
    """Raised when a tool invocation fails."""

    code = "tool_error"
    http_status = 502


class EvaluationGateFailed(LLMOpsError):
    """Raised (in CI) when an evaluation gate does not meet its thresholds."""

    code = "evaluation_gate_failed"
    http_status = 422


class UpstreamError(LLMOpsError):
    """Raised when an upstream Azure service call fails after retries."""

    code = "upstream_error"
    http_status = 502
