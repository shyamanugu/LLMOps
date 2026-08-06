"""Model management — pick a model by task alias and call it.

Reusable across every use case. App code asks for an *alias* (e.g. "reason" or "bulk"); this file
resolves the alias to a real Azure OpenAI deployment (from models.json) and calls it. Swapping a
model is a change to models.json — never a code change.

Offline: if no Azure endpoint is set (config.MOCK_MODE), a deterministic mock answer is returned so
the whole pipeline runs on a laptop.
"""

import time

from framework import config
from framework.observability import record_model_call

_MODELS = config.load_models()

# Indicative prices (US$ per 1,000,000 tokens). Update to your Azure contract. Only used for the
# cost figure we attach to each call; not a hard dependency.
_PRICES = {
    "gpt-5.2": {"in": 5.0, "out": 30.0},
    "gpt-5-mini": {"in": 0.25, "out": 2.0},
    "text-embedding-3-large": {"in": 0.13, "out": 0.0},
}


def resolve(alias: str) -> str:
    """Return the deployment name for a task alias in the current environment."""
    if alias not in _MODELS:
        raise KeyError(f"model alias '{alias}' not in models.json for env '{config.APP_ENV}'")
    return _MODELS[alias]


def _cost(deployment: str, in_tokens: int, out_tokens: int) -> float:
    p = _PRICES.get(deployment, {"in": 0.0, "out": 0.0})
    return round(in_tokens / 1e6 * p["in"] + out_tokens / 1e6 * p["out"], 6)


def _client():
    """Build the Azure OpenAI client. Uses Managed Identity if no key is set."""
    from openai import AzureOpenAI  # imported lazily so the skeleton installs without it

    if config.AZURE_OPENAI_API_KEY:
        return AzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
        )
    # No key -> Managed Identity (recommended in Azure).
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        azure_ad_token_provider=token_provider,
        api_version=config.AZURE_OPENAI_API_VERSION,
    )


def chat(alias: str, messages: list[dict], temperature: float = 0.2, prompt_id: str | None = None) -> dict:
    """Call a chat model by alias. Returns {text, model, tokens_in, tokens_out, cost_usd, latency_ms}.

    In mock mode (no endpoint) returns a deterministic answer built from the input so the pipeline
    and the evaluation gate still run offline.
    """
    deployment = resolve(alias)
    start = time.time()

    if config.MOCK_MODE:
        text = _mock_answer(messages)
        tokens_in = sum(len(m.get("content", "").split()) for m in messages)
        tokens_out = len(text.split())
    else:
        client = _client()
        resp = client.chat.completions.create(
            model=deployment, messages=messages, temperature=temperature
        )
        text = resp.choices[0].message.content or ""
        tokens_in = resp.usage.prompt_tokens
        tokens_out = resp.usage.completion_tokens

    result = {
        "text": text,
        "model": deployment,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": _cost(deployment, tokens_in, tokens_out),
        "latency_ms": int((time.time() - start) * 1000),
    }
    # Observability: every model call is recorded (tokens, cost, latency).
    record_model_call(alias=alias, prompt_id=prompt_id, **result)
    return result


def _mock_answer(messages: list[dict]) -> str:
    """Deterministic offline answer: echo the provided context so groundedness stays high in tests."""
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    # The prompt puts the retrieved context after the marker 'Context:'; return it as the answer.
    if "Context:" in user:
        context = user.split("Context:", 1)[1].strip()
        return f"Based on our documents: {context[:600]}"
    return f"(mock answer) {user[:200]}"
