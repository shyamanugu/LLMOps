"""Model router — resolve a task alias to an Azure deployment for the environment.

Application code asks for a *capability* (``reason``, ``bulk``, ``judge``, ``voice``,
``embed``), never a concrete model. The router reads the alias table from
``platform/models.yaml`` (already parsed into :class:`ModelsConfig`) and returns the
deployment name to use in the current environment. Swapping models is therefore a reviewed
change to the YAML, not a code change.
"""

from __future__ import annotations

from llmops.common.logging import get_logger
from llmops.config.models_config import ModelsConfig
from llmops.config.settings import Settings, get_settings

logger = get_logger(__name__)


class ModelRouter:
    """Resolve task aliases to deployment names for a fixed environment.

    Args:
        config: The parsed models configuration.
        env: The environment whose alias table to use (``dev`` | ``test`` | ``prod``).
    """

    def __init__(self, config: ModelsConfig, env: str) -> None:
        self._config = config
        self._env = env

    @property
    def env(self) -> str:
        """The environment this router resolves against."""
        return self._env

    def resolve(self, alias: str) -> str:
        """Resolve ``alias`` to the deployment name for this router's environment.

        Args:
            alias: The task alias (e.g. ``"reason"``).

        Returns:
            The Azure deployment name.

        Raises:
            UnknownAliasError: If the alias or environment is not defined.
        """
        deployment = self._config.resolve(alias, self._env)
        logger.info("resolved model alias", alias=alias, env=self._env, deployment=deployment)
        return deployment

    def aliases(self) -> dict[str, str]:
        """Return the full ``alias -> deployment`` map for this environment.

        Returns:
            A copy of the alias table, or an empty dict if the environment is absent.
        """
        env_cfg = self._config.environments.get(self._env)
        return dict(env_cfg.aliases) if env_cfg else {}

    @classmethod
    def from_settings(cls, config: ModelsConfig, settings: Settings | None = None) -> "ModelRouter":
        """Build a router for the environment named in ``settings``.

        Args:
            config: The parsed models configuration.
            settings: Platform settings; the singleton is used when omitted.

        Returns:
            A router bound to ``settings.environment``.
        """
        settings = settings or get_settings()
        return cls(config, settings.environment)
