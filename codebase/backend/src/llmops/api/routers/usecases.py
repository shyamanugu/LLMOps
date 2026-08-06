"""Use-cases router — onboarded use cases and their status."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from llmops.api.deps import SettingsDep
from llmops.common.logging import get_logger

_log = get_logger(__name__)
router = APIRouter(prefix="/usecases")


def _usecase_status(uc_dir: Path) -> dict[str, Any]:
    """Summarise a use-case directory: which building blocks are present."""
    has_prompts = (uc_dir / "prompts").is_dir()
    has_agents = (uc_dir / "agents" / "pipeline.agent.yaml").exists()
    has_evals = (uc_dir / "evals").is_dir() and any((uc_dir / "evals").glob("*.jsonl"))
    ready = has_prompts and has_agents and has_evals
    return {
        "name": uc_dir.name,
        "has_prompts": has_prompts,
        "has_pipeline": has_agents,
        "has_goldens": has_evals,
        "status": "ready" if ready else "scaffolding",
    }


@router.get("", summary="Onboarded use cases + status")
async def list_usecases(settings: SettingsDep) -> dict[str, Any]:
    """Return the use cases present under ``usecases/`` with an onboarding status.

    A use case is ``ready`` when it has prompts, a pipeline definition, and a golden set;
    otherwise it is still ``scaffolding``. The ``_template`` scaffold is excluded.
    """
    root = Path(settings.usecases_dir)
    items: list[dict[str, Any]] = []
    if root.exists():
        for uc_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if uc_dir.name.startswith("_"):
                continue
            items.append(_usecase_status(uc_dir))
    return {"source": "usecases", "items": items, "count": len(items)}
