# Model Management

**What it is** — Calling a model by a task **alias** (`reason` / `bulk` / `judge` / `embed`)
instead of a deployment name. The alias resolves to a real Azure OpenAI deployment via
`framework/models.json`. Swapping a model is a JSON change, never a code change.

**When to use** — Any time code needs to call an LLM: generation, judging, embeddings. Always ask
for an alias; never reference `gpt-5.2` or another deployment name in Python.

**How it works here** — `framework/model_management.py`:
- `resolve(alias)` looks the alias up in the current environment's map from `models.json`.
- `chat(alias, messages, temperature=0.2, prompt_id=None)` calls the model and returns
  `{text, model, tokens_in, tokens_out, cost_usd, latency_ms}`. It records the call via
  `record_model_call` (observability) automatically.
- **Mock mode**: when `config.MOCK_MODE` is true (no `AZURE_OPENAI_ENDPOINT`), `_mock_answer`
  returns a deterministic answer built from the input context, so the pipeline and the gate run
  offline.
- **Cost**: `_cost()` uses the indicative `_PRICES` table (US$ per 1M tokens) to attach `cost_usd`
  to every call. Update the table to your Azure contract; it's informational, not a hard dependency.
- The Azure client is built lazily in `_client()` and uses Managed Identity when no API key is set.

**Key files** — `framework/model_management.py`, `framework/models.json`, `framework/config.py`
(`MOCK_MODE`, `APP_ENV`, `load_models`).

**Example**
```python
from framework import model_management
res = model_management.chat("reason", [{"role": "user", "content": user_prompt}], prompt_id="qa.answer")
print(res["text"], res["cost_usd"])
```
```json
{ "environments": { "prod": { "reason": "gpt-5.2", "bulk": "gpt-5-mini",
  "judge": "gpt-5-mini", "embed": "text-embedding-3-large" } } }
```

**Pitfalls**
- Hard-coding a deployment name in code — always go through an alias.
- Assuming a cloud call — in mock mode answers are deterministic echoes of the context; don't test
  for "intelligent" behaviour offline.
- Forgetting `prompt_id` — pass it so observability can tie the call to the prompt.
- Adding a new alias in code but not in every environment block of `models.json`.
