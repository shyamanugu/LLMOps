"""Models router — task aliases and their resolved deployments per environment."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from llmops.api.deps import ModelRouterDep, SettingsDep
from llmops.common.logging import get_logger
from llmops.config.models_config import load_models_config

_log = get_logger(__name__)
router = APIRouter(prefix="/models")


@router.get("", summary="List aliases + resolved deployments (per env)")
async def list_models(settings: SettingsDep, router_dep: ModelRouterDep) -> dict[str, Any]:
    """Return the task-alias -> deployment mapping for the current environment.

    Reads directly from ``platform/models.yaml`` so it works even when the model router
    package is not yet wired; the resolved deployment names come from the config-as-code.
    """
    env = settings.environment
    try:
        config = load_models_config(settings.models_config_path)
        env_cfg = config.environments.get(env)
        aliases = env_cfg.aliases if env_cfg else {}
        items = [{"alias": alias, "deployment": dep, "environment": env} for alias, dep in aliases.items()]
        return {"source": "models.yaml", "environment": env, "items": items}
    except Exception as exc:  # noqa: BLE001 - config issues surface as a labelled placeholder
        _log.warning("could not load models.yaml", error=str(exc))
        return {"source": "placeholder", "environment": env, "items": [], "detail": str(exc)}
