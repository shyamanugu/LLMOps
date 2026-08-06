"""Unit tests for the guardrail engine and adapters.

Covers ordered execution, block-on-deny (raising :class:`~llmops.common.errors.GuardrailBlocked`),
redaction threading between guards, the ``fail_open`` behaviour on adapter errors, and the pure
PII / schema adapters that run without any Azure endpoint.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import BaseModel

from llmops.common.errors import GuardrailBlocked
from llmops.guardrails.base import Guard, GuardResult
from llmops.guardrails.engine import GuardrailEngine
from llmops.guardrails.pii import PiiGuard
from llmops.guardrails.schema_validation import SchemaGuard


class _AllowGuard:
    """A guard that always allows."""

    name = "allow"

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        return GuardResult.allow()

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        return GuardResult.allow()


class _BlockGuard:
    """A guard that always blocks."""

    name = "block"

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        return GuardResult.block(category="test", detail="blocked for test")

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        return GuardResult.block(category="test", detail="blocked for test")


class _RedactGuard:
    """A guard that redacts a marker token."""

    name = "redact"

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        return GuardResult.allow(redacted_text=text.replace("SECRET", "<REDACTED>"))

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        return GuardResult.allow(redacted_text=text.replace("SECRET", "<REDACTED>"))


class _ExplodingGuard:
    """A guard whose adapter raises (not a block)."""

    name = "boom"

    async def check_input(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        raise RuntimeError("adapter down")

    async def check_output(self, text: str, ctx: dict[str, Any]) -> GuardResult:
        raise RuntimeError("adapter down")


def test_local_guards_satisfy_protocol() -> None:
    """The in-test doubles structurally satisfy the Guard protocol."""
    assert isinstance(_AllowGuard(), Guard)
    assert isinstance(_BlockGuard(), Guard)


@pytest.mark.asyncio
async def test_engine_allows_clean_input() -> None:
    """A chain of allowing guards returns an allowing result."""
    engine = GuardrailEngine([_AllowGuard(), _AllowGuard()])
    result = await engine.check_input("hello", {})
    assert result.allowed is True
    assert result.redacted_text == "hello"


@pytest.mark.asyncio
async def test_engine_raises_on_block() -> None:
    """Any denying guard raises GuardrailBlocked with structured detail."""
    engine = GuardrailEngine([_AllowGuard(), _BlockGuard()])
    with pytest.raises(GuardrailBlocked) as exc_info:
        await engine.check_input("hello", {})
    assert exc_info.value.detail["guard"] == "block"
    assert exc_info.value.detail["category"] == "test"


@pytest.mark.asyncio
async def test_engine_threads_redaction_forward() -> None:
    """Redactions from an earlier guard are reflected in the final result."""
    engine = GuardrailEngine([_RedactGuard(), _AllowGuard()])
    result = await engine.check_output("this is SECRET data", {})
    assert result.allowed is True
    assert result.redacted_text == "this is <REDACTED> data"


@pytest.mark.asyncio
async def test_engine_fail_open_skips_adapter_errors() -> None:
    """With fail_open=True an adapter error is skipped, not raised."""
    engine = GuardrailEngine([_ExplodingGuard(), _AllowGuard()], fail_open=True)
    result = await engine.check_input("hello", {})
    assert result.allowed is True


@pytest.mark.asyncio
async def test_engine_fail_closed_propagates_adapter_errors() -> None:
    """With fail_open=False (default) an adapter error propagates."""
    engine = GuardrailEngine([_ExplodingGuard()])
    with pytest.raises(RuntimeError):
        await engine.check_input("hello", {})


@pytest.mark.asyncio
async def test_pii_guard_redacts_email() -> None:
    """The PII guard redacts an email address and allows the sanitised text."""
    guard = PiiGuard()
    result = await guard.check_input("contact me at jane.doe@example.com please", {})
    assert result.allowed is True
    assert result.redacted_text is not None
    assert "jane.doe@example.com" not in result.redacted_text


@pytest.mark.asyncio
async def test_schema_guard_blocks_invalid_json() -> None:
    """The schema guard blocks output that does not satisfy the pydantic model."""

    class Answer(BaseModel):
        answer: str
        confidence: float

    guard = SchemaGuard(Answer)
    good = await guard.check_output(json.dumps({"answer": "yes", "confidence": 0.9}), {})
    assert good.allowed is True

    bad = await guard.check_output(json.dumps({"answer": "yes"}), {})
    assert bad.allowed is False
    assert bad.category == "schema"

    not_json = await guard.check_output("not json at all", {})
    assert not_json.allowed is False
