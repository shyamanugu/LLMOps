"""Prompt management — prompts live in the repo (GitHub IS the registry).

Each prompt is a JSON file under usecases/<name>/prompts/. It carries an id, a version, the
template (with {{variables}}), the list of variables, and the model alias to use. Changing a prompt
is a pull request that must pass the evaluation gate — that is the difference from "prompts buried
in code".

This module loads a prompt by name and renders it with values.
"""

import json

from framework import config


def load_prompt(usecase: str, name: str) -> dict:
    """Load usecases/<usecase>/prompts/<name>.prompt.json as a dict."""
    path = config.ROOT / "usecases" / usecase / "prompts" / f"{name}.prompt.json"
    if not path.exists():
        raise FileNotFoundError(f"prompt not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def render(prompt: dict, **values) -> str:
    """Fill the {{variable}} placeholders in the prompt template.

    Raises if a declared variable was not supplied — no silent gaps.
    """
    missing = [v for v in prompt.get("variables", []) if v not in values]
    if missing:
        raise ValueError(f"prompt '{prompt['id']}' missing variables: {missing}")
    text = prompt["template"]
    for key, val in values.items():
        text = text.replace("{{" + key + "}}", str(val))
    return text


def list_prompts(usecase: str) -> list[str]:
    """List the prompt names available for a use case."""
    folder = config.ROOT / "usecases" / usecase / "prompts"
    return [p.name.replace(".prompt.json", "") for p in folder.glob("*.prompt.json")]
