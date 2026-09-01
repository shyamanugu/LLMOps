# Git-backed prompts (LLMOps Prompt Management, component 02)

Prompts placed here **override** the in-code prompts in `programs_config/<program>/`
via `prompts_gate.apply_prompt_overrides`, which runs when a program config is
loaded. If a file below is absent, the pipeline keeps using its in-code prompt —
so this directory is an incremental, non-breaking migration path.

## Layout

```
prompts/
  <program>/                 # telesales | wcc | pso
    denoise.yaml             # -> cfg.denoise_system_prompt
    analysis.yaml            # -> cfg.analysis_system_prompt
    reflection.yaml          # -> cfg.reflection_system_prompt
  _fragments/                # optional shared {{fragment:name}} snippets
    <name>.yaml
```

## File format (PromptSpec)

```yaml
name: analysis            # must match the file's role (denoise|analysis|reflection)
version: 1
description: Telesales per-call analysis system prompt
model_capability: reason  # reason | bulk
input_variables: []       # these system prompts take no variables
template: |
  <the full system prompt text>
```

## Migrating a program's prompts faithfully

The in-code prompts are dynamic f-strings that interpolate each program's schema
at import time. **Do not hand-copy them** — export the resolved text from the
real venv instead:

```python
from ai_pipeline.programs_config import load_program_config
from ai_pipeline import prompts_gate
cfg = load_program_config("telesales")
prompts_gate.dump_prompts(cfg, "telesales")   # writes prompts/telesales/*.yaml
```

Commit the generated YAML, then edit the YAML from then on (the override takes
precedence over the Python constants automatically).
```
