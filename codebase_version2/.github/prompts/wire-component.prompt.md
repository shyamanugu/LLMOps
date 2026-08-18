---
mode: 'agent'
description: 'Replace a framework mock with the real Azure client at the # TODO(wiring) marker, keeping the mock fallback'
---

# Wire a real Azure client

Replace the mock in framework component `${input:component}` (one of: `model`, `rag`, `guardrails`,
`observability`) with the real Azure client, at the `# TODO(wiring)` marker. Follow the
[framework instructions](../instructions/framework.instructions.md) and the golden rules in
[copilot-instructions](../copilot-instructions.md).

## Which file / marker

- `model` → [model_management.py](../../framework/model_management.py) — the `if config.MOCK_MODE:`
  branch in `chat(...)`; wire Azure OpenAI (chat completions) in the real branch.
- `rag` → [rag.py](../../framework/rag.py) — `# TODO(wiring)` for Azure AI Search
  (hybrid/semantic query via `SearchClient`).
- `guardrails` → [guardrails.py](../../framework/guardrails.py) — `# TODO(wiring)` for Azure AI
  Content Safety.
- `observability` → [observability.py](../../framework/observability.py) — `# TODO(wiring)` for
  Langfuse forwarding.

## Rules (do not break these)

1. KEEP THE MOCK FALLBACK. When `config.MOCK_MODE` is true (no Azure endpoint set) the code must
   still return the deterministic offline result — the repo must keep running on a laptop with no
   cloud.
2. NO SECRETS IN CODE (golden rule 7). Read endpoints from [config.py](../../framework/config.py) /
   env. Authenticate with Managed Identity (`DefaultAzureCredential`) — never a hard-coded key.
3. Do not hard-code a model/deployment name — resolve via alias through
   [models.json](../../framework/models.json) (golden rule 1).
4. Keep the public function signature stable so use cases and [pipeline.py](../../framework/pipeline.py)
   are unaffected. Keep observability recording intact.
5. Any new dependency (e.g. `azure-ai-*`) is optional — import lazily inside the real branch so mock
   mode has no extra install.

## Finish

Confirm mock mode still works, then run the gate:

```
python scripts/run_eval_gate.py
```

Then suggest `/update-memory` to record the wiring decision.
