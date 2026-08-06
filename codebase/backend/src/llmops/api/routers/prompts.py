"""Prompts router — list/read prompts and a dev render helper (ARCHITECTURE_SPEC §3)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body

from llmops.api.deps import PromptRegistryDep
from llmops.common.errors import PromptNotFoundError
from llmops.common.logging import get_logger

_log = get_logger(__name__)
router = APIRouter(prefix="/prompts")


@router.get("", summary="List prompts (id, version, labels)")
async def list_prompts(registry: PromptRegistryDep) -> dict[str, Any]:
    """Return a summary list of registered prompts.

    Falls back to a labelled placeholder when the prompt registry is not wired in dev.
    """
    if registry is None:
        # TODO(wiring): served once llmops.prompts.factory returns a live registry.
        return {"source": "placeholder", "items": []}
    items = [
        {"id": spec.id, "version": spec.version, "labels": spec.labels}
        for spec in registry.list()
    ]
    return {"source": "registry", "items": items}


@router.get("/{prompt_id}", summary="Get a PromptSpec")
async def get_prompt(prompt_id: str, registry: PromptRegistryDep, label: str = "prod") -> dict[str, Any]:
    """Return the full :class:`PromptSpec` for ``prompt_id`` at ``label``.

    Raises:
        PromptNotFoundError: If the registry is wired but the prompt is unknown.
    """
    if registry is None:
        return {"source": "placeholder", "id": prompt_id, "label": label, "spec": None}
    spec = registry.get(prompt_id, label)
    if spec is None:
        raise PromptNotFoundError(f"prompt '{prompt_id}' ({label}) not found")
    return {"source": "registry", "spec": spec.model_dump()}


@router.post("/{prompt_id}/render", summary="Render a prompt with vars (dev helper)")
async def render_prompt(
    prompt_id: str,
    registry: PromptRegistryDep,
    variables: Annotated[dict[str, Any] | None, Body()] = None,
    label: str = "prod",
) -> dict[str, Any]:
    """Render ``prompt_id`` with the supplied variables (development convenience).

    Raises:
        PromptNotFoundError: If the registry is wired but the prompt is unknown.
    """
    variables = variables or {}
    if registry is None:
        return {"source": "placeholder", "id": prompt_id, "rendered": None}
    spec = registry.get(prompt_id, label)
    if spec is None:
        raise PromptNotFoundError(f"prompt '{prompt_id}' ({label}) not found")
    return {"source": "registry", "rendered": spec.render(**variables)}
