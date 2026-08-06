"""The guardrail engine — runs an ordered chain of :class:`Guard` checks.

The engine is the single choke point every request and response passes through. It applies
guards **in order**, threading any redactions forward so that later guards see the sanitised
text, and raises :class:`~llmops.common.errors.GuardrailBlocked` the moment any guard denies.

Separation of concerns: the engine knows *nothing* about Azure Content Safety, Presidio, or
Prompt Shields — it only speaks the :class:`Guard` protocol. Wiring a new safety vendor is a
matter of adding an adapter to the ordered list.
"""

from __future__ import annotations

from typing import Any

from llmops.common.errors import GuardrailBlocked
from llmops.common.logging import get_logger
from llmops.guardrails.base import Guard, GuardResult

_logger = get_logger(__name__)


class GuardrailEngine:
    """Compose and execute an ordered list of guards for inputs and outputs.

    Args:
        guards: Guards applied in order. Order matters — put cheap/deterministic guards
            (schema, PII redaction) before network-bound ones (Content Safety, Prompt Shields)
            so obviously-bad text is rejected before incurring a remote call.
        fail_open: When ``True`` (dev convenience), an *adapter error* (not a block) is logged
            and treated as allow. When ``False`` (production default), adapter errors propagate.
    """

    def __init__(self, guards: list[Guard], *, fail_open: bool = False) -> None:
        self._guards = list(guards)
        self._fail_open = fail_open

    @property
    def guards(self) -> list[Guard]:
        """Return the ordered guards (read-only view for the ``/guardrails`` API)."""
        return list(self._guards)

    async def check_input(self, text: str, ctx: dict[str, Any] | None = None) -> GuardResult:
        """Run every guard's ``check_input`` in order.

        Args:
            text: The inbound user text.
            ctx: Optional request context propagated to each guard.

        Returns:
            An allowing :class:`GuardResult` whose ``redacted_text`` holds the final,
            possibly-sanitised text.

        Raises:
            GuardrailBlocked: If any guard denies the text.
        """
        return await self._run("input", text, ctx or {})

    async def check_output(self, text: str, ctx: dict[str, Any] | None = None) -> GuardResult:
        """Run every guard's ``check_output`` in order.

        Args:
            text: The outbound model text.
            ctx: Optional request context propagated to each guard.

        Returns:
            An allowing :class:`GuardResult` whose ``redacted_text`` holds the final,
            possibly-sanitised text.

        Raises:
            GuardrailBlocked: If any guard denies the text.
        """
        return await self._run("output", text, ctx or {})

    async def _run(self, direction: str, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Execute the guard chain for a given direction, threading redactions forward."""
        current = text
        applied: list[str] = []
        for guard in self._guards:
            method = guard.check_input if direction == "input" else guard.check_output
            try:
                result = await method(current, ctx)
            except GuardrailBlocked:
                raise
            except Exception as exc:  # noqa: BLE001 - adapter failure isolation
                if self._fail_open:
                    _logger.warning(
                        "guard adapter error (failing open)",
                        guard=getattr(guard, "name", type(guard).__name__),
                        direction=direction,
                        error=str(exc),
                    )
                    continue
                raise

            if not result.allowed:
                _logger.warning(
                    "guardrail blocked",
                    guard=getattr(guard, "name", type(guard).__name__),
                    direction=direction,
                    category=result.category,
                    detail=result.detail,
                )
                raise GuardrailBlocked(
                    result.detail or "blocked by guardrail",
                    detail={
                        "guard": getattr(guard, "name", type(guard).__name__),
                        "direction": direction,
                        "category": result.category,
                        "scores": result.scores,
                    },
                )

            if result.redacted_text is not None and result.redacted_text != current:
                current = result.redacted_text
                applied.append(getattr(guard, "name", type(guard).__name__))

        _logger.debug(
            "guardrails passed",
            direction=direction,
            guards=len(self._guards),
            redacted_by=applied,
        )
        return GuardResult.allow(redacted_text=current)
