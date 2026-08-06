"""Prompt registry and rendering.

Prompts are treated as versioned, evaluated artifacts — not strings scattered through
code. A prompt is authored as a ``*.prompt.yaml`` file under a use case
(``usecases/<uc>/prompts/``), validated into a :class:`~llmops.prompts.schema.PromptSpec`,
and served through a :class:`~llmops.prompts.base.PromptRegistry`.

Three registry backends implement the same interface (dependency inversion):

* :class:`~llmops.prompts.git.GitPromptRegistry` — Git files are the source of truth (default).
* :class:`~llmops.prompts.langfuse.LangfusePromptRegistry` — Langfuse prompt management.
* :class:`~llmops.prompts.foundry.FoundryPromptRegistry` — Azure AI Foundry prompt store.

Application code should call :func:`~llmops.prompts.loader.load_prompt`, which selects the
configured backend via the factory. This keeps call sites backend-agnostic.
"""

from __future__ import annotations

from llmops.prompts.base import PromptRegistry
from llmops.prompts.factory import build_registry
from llmops.prompts.loader import load_prompt
from llmops.prompts.schema import PromptSpec

__all__ = ["PromptSpec", "PromptRegistry", "build_registry", "load_prompt"]
