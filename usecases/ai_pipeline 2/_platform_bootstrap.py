"""Make the AFNI LLMOps platform services importable from this pipeline.

The platform (``platform/services/<NN-name>/src``) is consumed via ``PYTHONPATH``
rather than as an installed package (see the platform's ADR 0004). This module
appends each service's ``src`` directory to ``sys.path`` on import so the
pipeline can ``import observability``, ``import model_management``, etc.

Resolution order for the platform's ``services`` directory:
  1. ``LLMOPS_PLATFORM_ROOT`` env var, if set (should point at ``platform/services``)
  2. Derived from this file's location: ``<repo>/platform/services``

Importing this module is idempotent and never raises — if the platform tree is
absent the pipeline still runs (observability degrades to a no-op).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Services this pipeline currently wires in. Adding a service to the integration
# is a one-line change here, not a code change elsewhere.
_WANTED_SERVICES = (
    "02-prompt-management",
    "03-model-management",
    "04-evaluation-gate",
    "05-observability",
    "06-guardrails",
    "11-feedback",
)

_BOOTSTRAPPED = False


def _services_root() -> Path | None:
    override = os.environ.get("LLMOPS_PLATFORM_ROOT", "").strip()
    if override:
        root = Path(override).expanduser()
        return root if root.is_dir() else None
    # <repo>/usecases/ai_pipeline 2/_platform_bootstrap.py -> parents[2] == <repo>
    repo_root = Path(__file__).resolve().parents[2]
    candidate = repo_root / "platform" / "services"
    return candidate if candidate.is_dir() else None


def bootstrap() -> list[str]:
    """Append each wanted service's ``src`` dir to ``sys.path``. Returns the
    list of directories added (empty if the platform tree was not found)."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return []

    services = _services_root()
    added: list[str] = []
    if services is None:
        _BOOTSTRAPPED = True
        return added

    for service in _WANTED_SERVICES:
        src = services / service / "src"
        if src.is_dir():
            path_str = str(src)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
                added.append(path_str)

    _BOOTSTRAPPED = True
    return added


# Run on import so a plain ``import ai_pipeline._platform_bootstrap`` is enough.
bootstrap()
