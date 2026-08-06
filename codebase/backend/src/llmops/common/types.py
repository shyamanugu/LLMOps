"""Shared, cross-cutting data types used across the platform.

These are deliberately small, immutable value objects (pydantic models) that flow between
layers — the model client, orchestration, evaluation, and the API. Keeping them here avoids
circular imports between feature packages.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Usage(BaseModel):
    """Token usage for a single model call."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ChatResult(BaseModel):
    """Result of a single chat/completion call, with cost and timing attached."""

    text: str
    model: str  # the resolved Azure deployment name
    usage: Usage = Field(default_factory=Usage)
    cost_usd: float = 0.0
    latency_ms: int = 0
    finish_reason: str | None = None
    cache_hit: bool = False


class ToolResult(BaseModel):
    """Result of a tool invocation."""

    name: str
    ok: bool = True
    output: Any = None
    error: str | None = None
    latency_ms: int = 0


class Chunk(BaseModel):
    """A retrieved knowledge chunk (RAG)."""

    id: str
    text: str
    score: float = 0.0
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Environment(str, Enum):
    """Deployment environments."""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"
