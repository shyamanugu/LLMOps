"""FastAPI dependency providers.

Central place where request handlers obtain their collaborators via ``Depends(...)``:
settings, the prompt registry, the model router, the guardrail engine, the tool registry,
and the feedback service. Each provider constructs its object lazily and caches it for the
process (they are stateless facades). Sibling-package imports are guarded so the control
plane still boots — with clearly-degraded providers — before every feature package or live
Azure client exists (dependency inversion + fail-safe defaults).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends

from llmops.common.logging import get_logger
from llmops.config.settings import Settings, get_settings
from llmops.feedback.service import FeedbackService
from llmops.feedback.store import FeedbackStore

_log = get_logger(__name__)


def settings_provider() -> Settings:
    """Return the process-wide :class:`Settings` singleton."""
    return get_settings()


@lru_cache(maxsize=1)
def _feedback_service() -> FeedbackService:
    """Build the feedback service (in-memory store in dev)."""
    return FeedbackService(FeedbackStore(get_settings()))


def feedback_service_provider() -> FeedbackService:
    """Provide the shared :class:`FeedbackService`."""
    return _feedback_service()


@lru_cache(maxsize=1)
def _prompt_registry() -> Any | None:
    """Build the configured prompt registry, or ``None`` if unavailable in dev."""
    try:
        from llmops.prompts.factory import get_registry  # type: ignore[import-not-found]

        # TODO(wiring): factory selects git|langfuse|foundry from settings.prompt_registry.
        return get_registry(get_settings().prompt_registry)
    except Exception as exc:  # noqa: BLE001
        _log.warning("prompt registry unavailable; endpoints will report placeholder", error=str(exc))
        return None


def prompt_registry_provider() -> Any | None:
    """Provide the prompt registry (may be ``None`` in dev)."""
    return _prompt_registry()


@lru_cache(maxsize=1)
def _model_router() -> Any | None:
    """Build the model router from ``platform/models.yaml``, or ``None`` in dev."""
    try:
        from llmops.config.models_config import load_models_config
        from llmops.models.router import ModelRouter  # type: ignore[import-not-found]

        settings = get_settings()
        config = load_models_config(settings.models_config_path)
        return ModelRouter(config=config, env=settings.environment)
    except Exception as exc:  # noqa: BLE001
        _log.warning("model router unavailable; endpoints will report placeholder", error=str(exc))
        return None


def model_router_provider() -> Any | None:
    """Provide the model router (may be ``None`` in dev)."""
    return _model_router()


@lru_cache(maxsize=1)
def _guardrail_engine() -> Any | None:
    """Build the guardrail engine, or ``None`` if unavailable in dev."""
    try:
        from llmops.guardrails.engine import GuardrailEngine  # type: ignore[import-not-found]

        # TODO(wiring): construct the engine with the configured ordered guard list.
        return GuardrailEngine()  # type: ignore[call-arg]
    except Exception as exc:  # noqa: BLE001
        _log.warning("guardrail engine unavailable; endpoints will report placeholder", error=str(exc))
        return None


def guardrail_engine_provider() -> Any | None:
    """Provide the guardrail engine (may be ``None`` in dev)."""
    return _guardrail_engine()


@lru_cache(maxsize=1)
def _tool_registry() -> Any | None:
    """Build the tool registry from ``platform/tools/registry.yaml``, or ``None`` in dev."""
    try:
        from llmops.tools.registry import ToolRegistry  # type: ignore[import-not-found]

        loader = getattr(ToolRegistry, "from_yaml", None)
        if callable(loader):
            return loader("platform/tools/registry.yaml")
        return ToolRegistry()  # type: ignore[call-arg]
    except Exception as exc:  # noqa: BLE001
        _log.warning("tool registry unavailable; endpoints will report placeholder", error=str(exc))
        return None


def tool_registry_provider() -> Any | None:
    """Provide the tool registry (may be ``None`` in dev)."""
    return _tool_registry()


# Convenience typed aliases for handler signatures.
SettingsDep = Annotated[Settings, Depends(settings_provider)]
PromptRegistryDep = Annotated[Any, Depends(prompt_registry_provider)]
ModelRouterDep = Annotated[Any, Depends(model_router_provider)]
GuardrailEngineDep = Annotated[Any, Depends(guardrail_engine_provider)]
ToolRegistryDep = Annotated[Any, Depends(tool_registry_provider)]
FeedbackServiceDep = Annotated[FeedbackService, Depends(feedback_service_provider)]
