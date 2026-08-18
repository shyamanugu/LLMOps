---
applyTo: "**/*.py"
---

# Python standards (this repo)

- Target **Python 3.11**. Use modern typing (`list[str]`, `str | None`), no `from __future__` shims.
- **Type hints on every function** — parameters and return type.
- **Google-style docstrings** on public functions and classes; a **module docstring at the top** of every `.py` file saying what the file is for.
- **No `print` in framework code.** Emit signal through `framework/observability.py` (`record_model_call`, `record_tool_call`, `span`). `print` is only tolerated in `scripts/` CLIs.
- **Fail loudly on missing inputs.** Raise a clear exception (e.g. `ValueError`, `KeyError`, `FileNotFoundError`) — never return `None`, an empty string, or a silent default to paper over a missing prompt, model alias, or config value.
- **Standard library first.** Only reach for a third-party package when stdlib genuinely can't do it, and keep Azure/eval libs optional imports so mock mode still runs offline.
- **Match the existing style** in `framework/` — small readable functions, comments that explain *why*, no clever one-liners.
- Only `.py`, `.json`, and `.yml` file types exist in this repo. Do not introduce others.
