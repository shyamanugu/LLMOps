"""Pipeline execution context — the shared state threaded through a run.

A :class:`PipelineContext` is created once per pipeline invocation and passed to every step. It
carries the correlation ``trace_id``, the immutable original ``inputs``, a mutable ``memory``
shared blackboard (each step writes its output here for later steps to read), and a handle to
platform ``settings``. Keeping this in one small object avoids threading many parameters through
the step chain.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from llmops.common.ids import new_trace_id
from llmops.config.settings import Settings, get_settings


class PipelineContext(BaseModel):
    """Mutable, per-run context shared across pipeline steps.

    Attributes:
        trace_id: Correlation id for the whole run (matches the root tracing span).
        inputs: The original, immutable pipeline inputs.
        memory: Shared blackboard where steps publish their outputs (``{step_name: output}``).
        settings: Platform settings for the run.
        metadata: Free-form run metadata (use case, user hash, locale, ...).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    trace_id: str = Field(default_factory=new_trace_id)
    inputs: dict[str, Any] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)
    settings: Settings = Field(default_factory=get_settings)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def remember(self, key: str, value: Any) -> None:
        """Publish ``value`` under ``key`` on the shared blackboard."""
        self.memory[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        """Read a previously-published value from the blackboard."""
        return self.memory.get(key, default)
