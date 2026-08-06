"""Agents router — list pipelines/agents discovered under ``usecases/*/agents``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter

from llmops.api.deps import SettingsDep
from llmops.common.logging import get_logger

_log = get_logger(__name__)
router = APIRouter(prefix="/agents")


def _discover_pipelines(usecases_dir: Path) -> list[dict[str, Any]]:
    """Scan ``usecases/*/agents/pipeline.agent.yaml`` and summarise each pipeline."""
    items: list[dict[str, Any]] = []
    if not usecases_dir.exists():
        return items
    for uc_dir in sorted(p for p in usecases_dir.iterdir() if p.is_dir()):
        pipeline_file = uc_dir / "agents" / "pipeline.agent.yaml"
        if not pipeline_file.exists():
            continue
        try:
            spec = yaml.safe_load(pipeline_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            _log.warning("could not parse pipeline yaml", path=str(pipeline_file), error=str(exc))
            continue
        steps = spec.get("steps", spec.get("agents", []))
        items.append(
            {
                "usecase": uc_dir.name,
                "name": spec.get("name", uc_dir.name),
                "steps": [s.get("name", s) if isinstance(s, dict) else s for s in steps],
                "path": str(pipeline_file),
            }
        )
    return items


@router.get("", summary="List pipelines/agents from usecases/*/agents")
async def list_agents(settings: SettingsDep) -> dict[str, Any]:
    """Return the pipelines defined across onboarded use-cases (config-as-code)."""
    items = _discover_pipelines(Path(settings.usecases_dir))
    return {"source": "usecases", "items": items, "count": len(items)}
