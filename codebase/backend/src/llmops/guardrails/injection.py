"""Prompt-injection guard — jailbreak / injection detection via Prompt Shields.

Prompt injection (a.k.a. jailbreaking) is the attempt to override system instructions through
crafted user input or poisoned retrieved documents. The authoritative detector on Azure is
`Prompt Shields`_, part of Azure AI Content Safety, which scores both the *user prompt* and any
*documents* for attack content.

This guard is a thin, focused adapter (the broader :class:`ContentSafetyGuard` can also run
Prompt Shields; this one exists so a pipeline can enable injection detection independently). In
dev, with no endpoint configured, it **degrades to allow** but still applies a conservative
heuristic screen so obvious local test attacks are caught without a cloud call.

.. _Prompt Shields: https://learn.microsoft.com/azure/ai-services/content-safety/concepts/jailbreak-detection
"""

from __future__ import annotations

import re
from typing import Any, Final

from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.guardrails.base import GuardResult

_logger = get_logger(__name__)

#: Heuristic phrases indicative of an injection attempt (dev-only screen; not exhaustive).
_HEURISTIC_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"ignore (all|any|previous|prior) (instructions|prompts)", re.IGNORECASE),
    re.compile(r"disregard (the )?(system|previous) (prompt|message|instructions)", re.IGNORECASE),
    re.compile(r"you are now (in )?(developer|dan|jailbreak) mode", re.IGNORECASE),
    re.compile(r"reveal (your )?(system prompt|instructions|hidden)", re.IGNORECASE),
    re.compile(r"pretend (you are|to be) (an?|the) .* without (any )?(restrictions|rules)", re.IGNORECASE),
)


class PromptInjectionGuard:
    """Detect prompt-injection / jailbreak attempts on inbound text and documents.

    Args:
        settings: Platform settings (endpoint + auth). Defaults to the process singleton.
        heuristic_in_dev: When live Prompt Shields is unavailable, apply the local heuristic
            screen (recommended for tests/dev); set ``False`` for a pure fail-safe allow.
    """

    name = "prompt_injection"

    def __init__(self, settings: Settings | None = None, *, heuristic_in_dev: bool = True) -> None:
        self._settings = settings or get_settings()
        self._heuristic_in_dev = heuristic_in_dev
        self._client: Any | None = None

    @property
    def _enabled(self) -> bool:
        """Whether a live Content Safety endpoint (hosting Prompt Shields) is configured."""
        return bool(self._settings.content_safety_endpoint)

    def _get_client(self) -> Any | None:
        """Lazily construct the Content Safety client used for Prompt Shields, or ``None``."""
        if not self._enabled:
            return None
        if self._client is not None:
            return self._client
        # TODO(wiring): construct ContentSafetyClient from settings / managed identity and call
        #   the Prompt Shields (shield_prompt) API with userPrompt + documents.
        raise NotImplementedError(
            "TODO(wiring): construct Content Safety client and call the Prompt Shields API"
        )

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Screen inbound user text (and any ``ctx['documents']``) for injection."""
        documents = ctx.get("documents") if isinstance(ctx, dict) else None
        if self._enabled:
            return await self._shield(text, documents)
        if self._heuristic_in_dev:
            return self._heuristic(text, documents)
        _logger.debug("prompt-injection dev mock: allow")
        return GuardResult.allow()

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Injection is an input-side concern; outputs always allow."""
        return GuardResult.allow()

    async def _shield(self, text: str, documents: Any) -> GuardResult:
        """Call the live Prompt Shields API and map ``attackDetected`` to a result."""
        client = self._get_client()
        if client is None:  # pragma: no cover - guarded by _enabled
            return GuardResult.allow()
        # TODO(wiring): resp = await client.shield_prompt(user_prompt=text, documents=documents)
        #   return GuardResult.block("jailbreak", ...) if resp.*.attack_detected else allow.
        raise NotImplementedError("TODO(wiring): call Prompt Shields shield_prompt")

    def _heuristic(self, text: str, documents: Any) -> GuardResult:
        """Conservative local screen used only when Prompt Shields is not wired."""
        haystacks = [text]
        if isinstance(documents, list):
            haystacks.extend(str(d) for d in documents)
        for hay in haystacks:
            for pattern in _HEURISTIC_PATTERNS:
                if pattern.search(hay):
                    return GuardResult.block(
                        category="jailbreak",
                        detail=f"heuristic injection match: {pattern.pattern!r}",
                    )
        return GuardResult.allow()
