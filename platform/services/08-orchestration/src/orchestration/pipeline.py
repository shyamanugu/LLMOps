"""An ordered sequence of Steps, run against one shared State."""
from dataclasses import dataclass
from typing import List

from .state import State
from .step import Step


@dataclass
class Pipeline:
    name: str
    steps: List[Step]

    def run(self, state: State, environment: str) -> State:
        for step in self.steps:
            state = step.run(state, environment)
        return state
