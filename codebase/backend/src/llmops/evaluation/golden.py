"""Golden datasets — the labelled cases that drive the evaluation gate.

A *golden case* pairs an input for the use-case pipeline with a ``grading`` payload that
metrics read (expected tool, expected arguments, reference answer, retrieval contexts, …).
Cases are stored as JSONL (one JSON object per line) under
``usecases/<uc>/evals/*.jsonl`` so they diff cleanly in code review and stream without
loading the whole file into memory.

Example line::

    {"id": "apix-001", "input": {"question": "reset my API key"},
     "grading": {"expected_tool": "get_record", "reference": "Go to Settings > Keys"},
     "meta": {"suite": "smoke", "tags": ["auth"]}}
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from llmops.common.errors import ConfigError
from llmops.common.logging import get_logger

_log = get_logger(__name__)


class GoldenCase(BaseModel):
    """A single labelled evaluation case.

    Attributes:
        id: Stable, unique case id (used in gate reports and to select subsets).
        input: The input dict handed verbatim to ``Pipeline.run``.
        grading: Expectations read by metrics. Well-known keys:
            ``expected_tool`` (str), ``expected_tools`` (list[str]),
            ``expected_args`` (dict), ``reference`` (str, gold answer),
            ``contexts`` (list[str], ground-truth retrieval contexts),
            ``rubric`` (str, for the LLM judge).
        meta: Free-form metadata (``suite``, ``tags``, ``owner`` …) used for filtering.
    """

    id: str
    input: dict[str, Any] = Field(default_factory=dict)
    grading: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)

    @property
    def expected_tool(self) -> str | None:
        """First expected tool for the case, if any (convenience accessor)."""
        tool = self.grading.get("expected_tool")
        if tool:
            return str(tool)
        tools = self.grading.get("expected_tools")
        if isinstance(tools, list) and tools:
            return str(tools[0])
        return None

    @property
    def reference(self) -> str | None:
        """Gold reference answer, if provided."""
        ref = self.grading.get("reference")
        return str(ref) if ref is not None else None


def iter_golden(path: str | Path) -> Iterator[GoldenCase]:
    """Yield golden cases from a JSONL file lazily.

    Args:
        path: Path to a ``.jsonl`` file.

    Yields:
        Parsed :class:`GoldenCase` instances, in file order.

    Raises:
        ConfigError: If the file is missing or a line is not valid JSON/schema.
    """
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"golden dataset not found at {p}", detail={"path": str(p)})
    with p.open("r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
                yield GoldenCase.model_validate(obj)
            except (json.JSONDecodeError, ValidationError) as exc:
                raise ConfigError(
                    f"invalid golden case at {p}:{lineno}: {exc}",
                    detail={"path": str(p), "line": lineno},
                ) from exc


def load_golden(path: str | Path) -> list[GoldenCase]:
    """Load all golden cases from a JSONL file into memory.

    Args:
        path: Path to a ``.jsonl`` file.

    Returns:
        The full list of :class:`GoldenCase`.
    """
    cases = list(iter_golden(path))
    _log.info("loaded golden dataset", path=str(path), count=len(cases))
    return cases


def select_subset(
    cases: list[GoldenCase],
    *,
    ids: list[str] | None = None,
    suite: str | None = None,
) -> list[GoldenCase]:
    """Filter cases by explicit ids and/or a ``meta.suite`` tag.

    Args:
        cases: All loaded cases.
        ids: If given, keep only cases whose id is in this list.
        suite: If given, keep only cases whose ``meta.suite`` equals this value.

    Returns:
        The filtered list (order preserved).
    """
    out = cases
    if ids is not None:
        wanted = set(ids)
        out = [c for c in out if c.id in wanted]
    if suite is not None:
        out = [c for c in out if c.meta.get("suite") == suite]
    return out
