"""Unit tests for :meth:`llmops.prompts.schema.PromptSpec.render`."""

from __future__ import annotations

import pytest

from llmops.common.errors import PromptRenderError
from llmops.prompts.schema import PromptSpec


def _spec(**overrides: object) -> PromptSpec:
    base: dict[str, object] = {
        "id": "apix.triage.system",
        "version": 1,
        "labels": ["prod"],
        "model_alias": "reason",
        "inputs": ["ticket", "customer"],
        "template": "Ticket: {{ ticket }} for {{customer}}.",
    }
    base.update(overrides)
    return PromptSpec.model_validate(base)


def test_render_fills_placeholders() -> None:
    spec = _spec()
    out = spec.render(ticket="cannot log in", customer="Acme")
    assert out == "Ticket: cannot log in for Acme."


def test_render_tolerates_whitespace_in_placeholders() -> None:
    spec = _spec(template="Hello {{   name   }}!", inputs=["name"])
    assert spec.render(name="world") == "Hello world!"


def test_render_missing_input_raises() -> None:
    spec = _spec()
    with pytest.raises(PromptRenderError) as excinfo:
        spec.render(ticket="only one")
    assert "customer" in excinfo.value.detail["missing"]


def test_render_ignores_extra_variables() -> None:
    spec = _spec()
    out = spec.render(ticket="x", customer="y", unused="z")
    assert out == "Ticket: x for y."


def test_render_coerces_non_string_values() -> None:
    spec = _spec(template="Count: {{ n }}", inputs=["n"])
    assert spec.render(n=42) == "Count: 42"


def test_undeclared_placeholder_in_template_raises() -> None:
    # Placeholder present in body but not declared as an input and not supplied.
    spec = _spec(template="Hi {{ ghost }}", inputs=[])
    with pytest.raises(PromptRenderError):
        spec.render()


def test_declared_placeholders_reports_body_names() -> None:
    spec = _spec()
    assert spec.declared_placeholders() == {"ticket", "customer"}


def test_blank_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        _spec(id="   ")
