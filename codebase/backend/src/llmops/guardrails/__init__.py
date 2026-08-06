"""Guardrails — the input/output safety engine.

Public surface:
    * :class:`GuardResult`, :class:`Guard` — the guard contract (``base``).
    * :class:`GuardrailEngine` — the ordered execution engine (``engine``).
    * Adapters: :class:`ContentSafetyGuard`, :class:`PiiGuard`, :class:`SchemaGuard`,
      :class:`PromptInjectionGuard`.

Every request and response should pass through a :class:`GuardrailEngine` composed of the
adapters appropriate to the use case. Adapters that require live Azure clients degrade to
fail-safe *allow* in dev and are marked ``# TODO(wiring)``.
"""

from llmops.guardrails.base import Guard, GuardResult
from llmops.guardrails.content_safety import ContentSafetyGuard
from llmops.guardrails.engine import GuardrailEngine
from llmops.guardrails.injection import PromptInjectionGuard
from llmops.guardrails.pii import PiiGuard
from llmops.guardrails.schema_validation import SchemaGuard

__all__ = [
    "Guard",
    "GuardResult",
    "GuardrailEngine",
    "ContentSafetyGuard",
    "PiiGuard",
    "SchemaGuard",
    "PromptInjectionGuard",
]
