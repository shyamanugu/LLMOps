"""Data shapes for a golden-dataset case, a per-case evaluation result, and
the aggregated gate decision.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class EvalCase:
    id: str
    input: dict
    evaluator: str
    expected: Any = None
    rubric: Optional[str] = None
    output_schema: Optional[dict] = None


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    reason: str = ""


@dataclass
class GateResult:
    passed: bool
    pass_rate: float
    threshold: float
    results: List[EvalResult] = field(default_factory=list)


class UnknownEvaluatorError(KeyError):
    pass
