"""The atomic unit of a pipeline. `ModelStep` is the first concrete
implementation — it builds its prompt (via Prompt Management, 02, or a raw
template), resolves a model alias via Model Management (03), calls it
through the provider bridge (`model_client.py`), and writes the result into
shared state.
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Protocol

from model_management.model_router import resolve
from model_management.providers.base import ModelProvider
from model_management.types import ModelKind
from prompt_management.registry import PromptRegistry

from .guardrails import GuardrailBlockedError, GuardrailCheck, PassthroughGuardrail
from .model_client import get_provider as _default_get_provider
from .state import State


class Step(Protocol):
    name: str

    def run(self, state: State, environment: str) -> State:
        ...


@dataclass
class ModelStep:
    name: str
    model_alias: str
    output_key: str
    prompt_template: Optional[str] = None
    prompt_name: Optional[str] = None
    prompt_registry: Optional[PromptRegistry] = None
    input_keys: List[str] = field(default_factory=list)
    expected_kind: ModelKind = ModelKind.CHAT
    guardrail: GuardrailCheck = field(default_factory=PassthroughGuardrail)
    provider_factory: Callable[[str], ModelProvider] = field(
        default=_default_get_provider, repr=False
    )

    def __post_init__(self) -> None:
        if bool(self.prompt_name) == bool(self.prompt_template):
            raise ValueError(
                f"Step '{self.name}' must set exactly one of prompt_name "
                "(Prompt Management, 02) or prompt_template (raw string)"
            )
        if self.prompt_name and self.prompt_registry is None:
            raise ValueError(
                f"Step '{self.name}' sets prompt_name but no prompt_registry was given"
            )

    def _build_prompt(self, state: State) -> str:
        prompt_vars = {key: state.get(key) for key in self.input_keys}
        if self.prompt_name:
            return self.prompt_registry.render(self.prompt_name, **prompt_vars)
        return self.prompt_template.format(**prompt_vars)

    def run(self, state: State, environment: str) -> State:
        prompt_text = self._build_prompt(state)

        input_check = self.guardrail.check_input(prompt_text)
        if not input_check.allowed:
            raise GuardrailBlockedError(
                f"Step '{self.name}' blocked on input: {input_check.reason}"
            )

        handle = resolve(self.model_alias, environment, expected_kind=self.expected_kind)
        provider = self.provider_factory(handle.provider)
        response = provider.chat(
            handle.deployment, [{"role": "user", "content": prompt_text}]
        )

        output_check = self.guardrail.check_output(response["content"])
        if not output_check.allowed:
            raise GuardrailBlockedError(
                f"Step '{self.name}' blocked on output: {output_check.reason}"
            )

        state.set(self.output_key, response["content"])
        return state
