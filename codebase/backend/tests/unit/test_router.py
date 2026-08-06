"""Unit tests for :class:`llmops.models.router.ModelRouter` (pure logic, no I/O)."""

from __future__ import annotations

import pytest

from llmops.common.errors import UnknownAliasError
from llmops.config.models_config import ModelsConfig
from llmops.models.router import ModelRouter


def _config() -> ModelsConfig:
    """Build a small in-memory models config mirroring platform/models.yaml."""
    return ModelsConfig.model_validate(
        {
            "environments": {
                "prod": {"aliases": {"reason": "gpt-5.2", "bulk": "gpt-5-mini"}},
                "dev": {"aliases": {"reason": "gpt-5-mini", "bulk": "gpt-5-mini"}},
            }
        }
    )


def test_resolve_prod_reason() -> None:
    router = ModelRouter(_config(), "prod")
    assert router.resolve("reason") == "gpt-5.2"


def test_resolve_is_environment_specific() -> None:
    prod = ModelRouter(_config(), "prod")
    dev = ModelRouter(_config(), "dev")
    assert prod.resolve("reason") == "gpt-5.2"
    assert dev.resolve("reason") == "gpt-5-mini"


def test_unknown_alias_raises() -> None:
    router = ModelRouter(_config(), "prod")
    with pytest.raises(UnknownAliasError) as excinfo:
        router.resolve("does-not-exist")
    assert excinfo.value.detail["alias"] == "does-not-exist"


def test_unknown_environment_raises() -> None:
    router = ModelRouter(_config(), "staging")
    with pytest.raises(UnknownAliasError):
        router.resolve("reason")


def test_aliases_returns_full_map_copy() -> None:
    router = ModelRouter(_config(), "prod")
    aliases = router.aliases()
    assert aliases == {"reason": "gpt-5.2", "bulk": "gpt-5-mini"}
    aliases["reason"] = "mutated"
    # Mutating the returned dict must not affect the router's config.
    assert router.resolve("reason") == "gpt-5.2"


def test_aliases_unknown_env_is_empty() -> None:
    router = ModelRouter(_config(), "nope")
    assert router.aliases() == {}
