"""Schema-validation guard — enforce that model output matches a contract.

Structured-output pipelines must not hand malformed JSON to downstream systems. This guard
validates outbound text against either a **pydantic model** (preferred) or a **JSON Schema**
mapping, and blocks when validation fails. It is deterministic, local, and cheap, so it belongs
early in the output guard chain.

On the input path it is a no-op (inputs are free text); it only constrains ``check_output``.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from llmops.common.logging import get_logger
from llmops.guardrails.base import GuardResult

_logger = get_logger(__name__)


class SchemaGuard:
    """Validate model output against a pydantic model or a JSON Schema.

    Args:
        model: A pydantic ``BaseModel`` subclass to validate against, or a JSON Schema ``dict``.
        strict: When ``True``, extra/unknown fields cause a block (pydantic path only relies on
            the model's own config; this flag additionally rejects unexpected top-level keys for
            the JSON-Schema path).
    """

    name = "schema_validation"

    def __init__(self, model: type[BaseModel] | dict[str, Any], *, strict: bool = False) -> None:
        self._model = model
        self._strict = strict

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Inputs are unconstrained free text; always allow."""
        return GuardResult.allow()

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        """Parse ``text`` as JSON and validate it against the configured schema."""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            return GuardResult.block(category="schema", detail=f"output is not valid JSON: {exc}")

        if isinstance(self._model, type) and issubclass(self._model, BaseModel):
            return self._validate_pydantic(self._model, payload)
        return self._validate_jsonschema(self._model, payload)

    def _validate_pydantic(self, model: type[BaseModel], payload: Any) -> GuardResult:
        """Validate ``payload`` against a pydantic model."""
        try:
            model.model_validate(payload)
        except ValidationError as exc:
            return GuardResult.block(category="schema", detail=f"schema validation failed: {exc.errors()}")
        return GuardResult.allow()

    def _validate_jsonschema(self, schema: dict[str, Any], payload: Any) -> GuardResult:
        """Validate ``payload`` against a JSON Schema mapping.

        Uses the ``jsonschema`` library when available; otherwise falls back to a minimal
        required-keys / type check and marks the limitation in the log.
        """
        try:
            import jsonschema  # type: ignore[import-untyped]
        except Exception:  # noqa: BLE001 - optional dependency
            # TODO(wiring): add `jsonschema` to requirements for full JSON-Schema validation.
            _logger.warning("jsonschema not installed; using minimal required-keys validation")
            return self._minimal_validate(schema, payload)

        try:
            jsonschema.validate(instance=payload, schema=schema)
        except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
            return GuardResult.block(category="schema", detail=f"schema validation failed: {exc.message}")
        return GuardResult.allow()

    def _minimal_validate(self, schema: dict[str, Any], payload: Any) -> GuardResult:
        """Best-effort validation without the ``jsonschema`` dependency."""
        if schema.get("type") == "object" and not isinstance(payload, dict):
            return GuardResult.block(category="schema", detail="expected a JSON object")
        required = schema.get("required", [])
        if isinstance(payload, dict):
            missing = [k for k in required if k not in payload]
            if missing:
                return GuardResult.block(category="schema", detail=f"missing required keys: {missing}")
            if self._strict:
                allowed = set(schema.get("properties", {}))
                extra = [k for k in payload if allowed and k not in allowed]
                if extra:
                    return GuardResult.block(category="schema", detail=f"unexpected keys: {extra}")
        return GuardResult.allow()
