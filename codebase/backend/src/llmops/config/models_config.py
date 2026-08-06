"""Loader for ``platform/models.yaml`` — the task-alias -> deployment mapping.

This is the single place a task ("reason", "bulk", "judge", "voice", "embed") maps to a
concrete Azure OpenAI *deployment name*, per environment. Application code always asks for
an alias; swapping a model is a reviewed change to the YAML that must pass the evaluation
gate (see the deck: "config-as-code"). Nothing here is hard-coded in agent code.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from llmops.common.errors import ConfigError, UnknownAliasError


class EnvAliases(BaseModel):
    aliases: dict[str, str]


class ModelsConfig(BaseModel):
    """Parsed ``models.yaml``: environment -> {alias -> deployment}."""

    environments: dict[str, EnvAliases]

    def resolve(self, alias: str, env: str) -> str:
        """Resolve ``alias`` to a deployment name for ``env``.

        Raises:
            UnknownAliasError: if the environment or alias is not defined.
        """
        env_cfg = self.environments.get(env)
        if env_cfg is None:
            raise UnknownAliasError(
                f"environment '{env}' not present in models.yaml",
                detail={"env": env, "known": list(self.environments)},
            )
        deployment = env_cfg.aliases.get(alias)
        if deployment is None:
            raise UnknownAliasError(
                f"alias '{alias}' not defined for environment '{env}'",
                detail={"alias": alias, "env": env, "known": list(env_cfg.aliases)},
            )
        return deployment


def load_models_config(path: str | Path) -> ModelsConfig:
    """Load and validate the models configuration from ``path``."""
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"models config not found at {p}", detail={"path": str(p)})
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return ModelsConfig.model_validate(raw)
    except Exception as exc:  # noqa: BLE001 - re-wrap as ConfigError
        raise ConfigError(f"failed to parse models config: {exc}", detail={"path": str(p)}) from exc
