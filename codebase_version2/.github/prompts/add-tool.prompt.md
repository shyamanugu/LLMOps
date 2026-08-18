---
mode: 'agent'
description: 'Add a reusable, read-only tool to the framework tool catalog with an observability record'
---

# Add a reusable tool

Add a new tool named `${input:toolName}` to the shared catalog in
[framework/tools.py](../../framework/tools.py). Tools are built ONCE here and reused by any use case
(golden rule 3) — do not add a tool inside a use case. Follow the
[framework instructions](../instructions/framework.instructions.md).

## What to produce

1. A plain function `${input:toolName}(...)` next to the existing tools
   (`search_knowledge`, `query_sql`, `get_record`). Google-style docstring, type hints, Python 3.11.
2. Keep it READ-ONLY and safe — no writes, no destructive calls. If it hits an external system,
   leave a `# TODO(wiring)` marker and return an empty/mock result so it works offline in mock mode.
3. Record the call for observability: call `record_tool_call("${input:toolName}", ok=..., latency_ms=..., ...)`
   from [observability.py](../../framework/observability.py). Every tool/model call must be recorded
   (golden rule 5).
4. Add a `CATALOG` entry with `fn`, `description` (one line), and `inputs` (list of parameter names),
   matching the existing entries. The description must be MCP-ready (enough to expose over Model
   Context Protocol without changing the tool).

## Notes

- No secrets in code — endpoints/keys come from [config.py](../../framework/config.py) / env
  (golden rule 7).
- Do not duplicate framework logic; if it retrieves documents, delegate to
  [rag.py](../../framework/rag.py).
- Mention in the docstring that this tool is reusable by any use case.

After editing, run the example gate to confirm nothing broke, then suggest `/update-memory`:

```
python scripts/run_eval_gate.py
```
