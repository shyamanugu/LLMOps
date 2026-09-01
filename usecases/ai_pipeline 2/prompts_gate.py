"""LLMOps prompt management integration (Phase 4 — thin adapter, override layer).

Uses the AFNI LLMOps Prompt Management service (platform component 02) so that
prompts can live as versioned, git-backed YAML under ``prompts/<program>/`` and
be edited without touching Python.

**Why an override layer rather than a hard cutover:** this pipeline's in-code
prompts are dynamic f-strings that interpolate each program's Pydantic schema at
import time. Freezing them into static YAML verbatim would drop that schema
injection and change behaviour. So the rule is: **a git-backed YAML prompt wins
when present; otherwise the existing in-code prompt is kept** (fail-open). Teams
migrate a prompt to config-as-code deliberately, one at a time — use
``dump_prompts()`` from the real venv to export the currently-resolved prompt
text faithfully, then edit the YAML thereafter.

Directory convention:
    prompts/<program>/denoise.yaml       -> overrides cfg.denoise_system_prompt
    prompts/<program>/analysis.yaml      -> overrides cfg.analysis_system_prompt
    prompts/<program>/reflection.yaml    -> overrides cfg.reflection_system_prompt
    prompts/_fragments/*.yaml            -> optional shared {{fragment:...}} snippets
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ai_pipeline import _platform_bootstrap  # noqa: F401  (side effect: sys.path)
from ai_pipeline.logging_config import get_logger

logger = get_logger("prompts")

_PKG_ROOT = Path(__file__).resolve().parent
PROMPTS_ROOT = _PKG_ROOT / "prompts"
_FRAGMENTS_DIR = PROMPTS_ROOT / "_fragments"

# (prompt name on disk, cfg field it overrides, model capability for dump)
_PROMPT_FIELDS = (
    ("denoise", "denoise_system_prompt", "bulk"),
    ("analysis", "analysis_system_prompt", "reason"),
    ("reflection", "reflection_system_prompt", "reason"),
)

try:
    from prompt_management.registry import PromptRegistry

    _PLATFORM = True
except Exception as exc:  # pragma: no cover - only when platform absent
    logger.warning("LLMOps prompt-management unavailable (%s) — using in-code prompts", exc)
    _PLATFORM = False

_registries: dict[str, Optional[object]] = {}


def _get_registry(program: str):
    if not _PLATFORM or not program:
        return None
    if program in _registries:
        return _registries[program]
    prog_dir = PROMPTS_ROOT / program
    reg = None
    if prog_dir.is_dir():
        try:
            frag_dirs = [_FRAGMENTS_DIR] if _FRAGMENTS_DIR.is_dir() else []
            reg = PromptRegistry(prompt_dirs=[prog_dir], fragment_dirs=frag_dirs)
        except Exception as exc:
            logger.warning("PromptRegistry build failed for '%s' (%s)", program, exc)
    _registries[program] = reg
    return reg


def render(program: str, name: str, fallback: str, **variables) -> str:
    """Render a git-backed prompt if it exists, else return *fallback*."""
    reg = _get_registry(program)
    if reg is None:
        return fallback
    try:
        if name in reg.list_prompts():
            return reg.render(name, **variables)
    except Exception as exc:
        logger.warning("prompt render failed (%s/%s): %s — using in-code prompt", program, name, exc)
    return fallback


def apply_prompt_overrides(cfg, program: str) -> None:
    """Replace cfg.*_system_prompt with git-backed YAML where one exists.

    No-op when the platform is absent or no YAML is present for a prompt — the
    in-code (dynamic) prompt is kept, so this never changes behaviour until a
    team deliberately drops in a YAML prompt.
    """
    reg = _get_registry(program)
    if reg is None:
        return
    try:
        available = set(reg.list_prompts())
    except Exception:
        return
    for name, field_name, _cap in _PROMPT_FIELDS:
        if name in available and hasattr(cfg, field_name):
            try:
                setattr(cfg, field_name, reg.render(name))
                logger.info("Prompt override | program=%s prompt=%s (git-backed YAML)", program, name)
            except Exception as exc:
                logger.warning("Prompt override failed (%s/%s): %s", program, name, exc)


def dump_prompts(cfg, program: str) -> list[str]:
    """Export cfg's currently-resolved in-code prompts to PromptSpec YAML under
    ``prompts/<program>/``. Run ONCE from the pipeline's real venv (where the
    dynamic prompts resolve) to migrate a program to config-as-code. Returns the
    list of files written."""
    import yaml

    prog_dir = PROMPTS_ROOT / program
    prog_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, field_name, cap in _PROMPT_FIELDS:
        template = getattr(cfg, field_name, "") or ""
        if not template.strip():
            continue
        spec = {
            "name": name,
            "version": 1,
            "description": f"{program} {name} system prompt (migrated from code)",
            "model_capability": cap,
            "input_variables": [],
            "template": template,
        }
        path = prog_dir / f"{name}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True, default_style="|")
        written.append(str(path))
        logger.info("Dumped prompt | %s", path)
    return written
