"""Reference pipeline assembly — copy this into a real usecase's own folder
and replace the single demo Step with this usecase's actual Steps. This is
usecase-owned code: the reusability acceptance test (see
docs/architecture/onboarding-runbook.md) is that onboarding a usecase
requires zero changes to platform/services/** — files like this one, living
under usecases/<name>/, are expected to exist and be usecase-specific.
"""
from pathlib import Path

from orchestration.pipeline import Pipeline
from orchestration.step import ModelStep
from prompt_management.registry import PromptRegistry

_PROMPTS_DIR = Path(__file__).parent / "prompts"
# example_prompt.yaml references {{fragment:safety_preamble}} — shared
# fragments live in Prompt Management (02), not per-usecase, so this
# directory has to be registered alongside this usecase's own prompts.
_SHARED_FRAGMENTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "platform" / "services" / "02-prompt-management" / "prompts" / "shared"
)


def build_pipeline() -> Pipeline:
    registry = PromptRegistry(prompt_dirs=[_PROMPTS_DIR], fragment_dirs=[_SHARED_FRAGMENTS_DIR])

    respond = ModelStep(
        name="respond",
        model_alias="nano",
        prompt_name="example_prompt",
        prompt_registry=registry,
        output_key="reply",
        input_keys=["message"],
    )

    return Pipeline(name="REPLACE_WITH_USECASE_NAME", steps=[respond])
