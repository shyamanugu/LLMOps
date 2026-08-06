"""PII guard — detect and redact personal data with Microsoft Presidio.

This adapter uses the open-source `Presidio`_ analyzer + anonymizer. Unlike the Azure adapters
it needs no cloud endpoint, so it runs identically in dev and prod. By default it **redacts**
(rather than blocks) so a pipeline can proceed on sanitised text; set ``block`` to deny instead.

If Presidio is not installed the guard degrades to a conservative regex fallback for the most
common identifiers (email, phone, credit card, SSN) and logs a warning, so PII is never silently
passed through untouched.

.. _Presidio: https://microsoft.github.io/presidio/
"""

from __future__ import annotations

import re
from typing import Any, Final

from llmops.common.logging import get_logger
from llmops.guardrails.base import GuardResult

_logger = get_logger(__name__)

#: Presidio entity types redacted by default.
DEFAULT_ENTITIES: Final[tuple[str, ...]] = (
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "US_SSN",
    "IBAN_CODE",
    "PERSON",
    "IP_ADDRESS",
)

#: Minimal regex fallback used only when Presidio is unavailable.
_FALLBACK_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    "EMAIL_ADDRESS": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "PHONE_NUMBER": re.compile(r"\+?\d[\d\s().-]{7,}\d"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "US_SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


class PiiGuard:
    """Detect and redact PII using Presidio (with a regex fallback).

    Args:
        entities: Entity types to detect. Defaults to :data:`DEFAULT_ENTITIES`.
        language: Presidio analyzer language code.
        block: When ``True`` the guard *blocks* on any detection; when ``False`` (default)
            it *redacts* and allows the sanitised text to proceed.
        redact_input: Apply redaction on the input path.
        redact_output: Apply redaction on the output path.
    """

    name = "pii"

    def __init__(
        self,
        *,
        entities: tuple[str, ...] = DEFAULT_ENTITIES,
        language: str = "en",
        block: bool = False,
        redact_input: bool = True,
        redact_output: bool = True,
    ) -> None:
        self._entities = list(entities)
        self._language = language
        self._block = block
        self._redact_input = redact_input
        self._redact_output = redact_output
        self._analyzer: Any | None = None
        self._anonymizer: Any | None = None
        self._presidio_ready = self._init_presidio()

    def _init_presidio(self) -> bool:
        """Construct the Presidio analyzer/anonymizer engines if the library is present."""
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
        except Exception:  # noqa: BLE001 - optional dependency / model download
            _logger.warning("Presidio unavailable; PII guard using regex fallback")
            return False
        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()
        return True

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Detect/redact PII on inbound text."""
        return self._process(text) if self._redact_input else GuardResult.allow()

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Detect/redact PII on outbound text."""
        return self._process(text) if self._redact_output else GuardResult.allow()

    def _process(self, text: str) -> GuardResult:
        """Run detection and produce an allow-with-redaction or block result."""
        found, redacted = self._detect_and_redact(text)
        if not found:
            return GuardResult.allow()
        if self._block:
            return GuardResult.block(
                category="pii",
                detail=f"PII detected: {sorted(found)}",
            )
        return GuardResult.allow(
            redacted_text=redacted,
            detail=f"redacted PII: {sorted(found)}",
        )

    def _detect_and_redact(self, text: str) -> tuple[set[str], str]:
        """Return the set of entity types found and the redacted text."""
        if self._presidio_ready and self._analyzer is not None and self._anonymizer is not None:
            results = self._analyzer.analyze(text=text, entities=self._entities, language=self._language)
            found = {r.entity_type for r in results}
            if not found:
                return set(), text
            anonymized = self._anonymizer.anonymize(text=text, analyzer_results=results)
            return found, anonymized.text
        return self._fallback_redact(text)

    def _fallback_redact(self, text: str) -> tuple[set[str], str]:
        """Regex-based redaction used when Presidio is unavailable."""
        found: set[str] = set()
        redacted = text
        for entity, pattern in _FALLBACK_PATTERNS.items():
            if entity not in self._entities:
                continue
            if pattern.search(redacted):
                found.add(entity)
                redacted = pattern.sub(f"<{entity}>", redacted)
        return found, redacted
