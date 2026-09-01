"""Runtime mode switch: **mock** vs **real**.

A single flag lets the same repo either (a) run a self-contained demo with
generated/sample data when no data or Azure is available (`mock`), or (b) plug
into the actual Azure Blob / SQL / OpenAI backends when they are (`real`).

    AI_PIPELINE_MODE = mock | real        (default: mock — safe for demos)

`mock` is the default on purpose: nothing here reaches for a live credential
unless you explicitly opt into `real`. Consumers check `is_mock()`/`is_real()`;
the UI and exporters stamp the resolved mode into the dataset's `meta.mode` so a
viewer can always tell whether they're looking at demo or production data.
"""
from __future__ import annotations

import os

MOCK = "mock"
REAL = "real"


def runtime_mode() -> str:
    """Return 'mock' or 'real' from AI_PIPELINE_MODE (default 'mock')."""
    value = os.environ.get("AI_PIPELINE_MODE", MOCK).strip().lower()
    return REAL if value == REAL else MOCK


def is_mock() -> bool:
    return runtime_mode() == MOCK


def is_real() -> bool:
    return runtime_mode() == REAL
