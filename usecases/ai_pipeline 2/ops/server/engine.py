"""Playground engine: run a prompt+model against a golden dataset and score it.

Mock mode uses a deterministic mock LLM (no OpenAI needed). Real mode calls the
actual model via the pipeline's query() path (expects REASONING_MODEL_* creds);
if they're missing it returns a clear error instead of pretending."""
import glob
import hashlib
import json
import os
import time
from pathlib import Path

from . import config, registry, store

_DATASET_DIR = config.PKG_DIR / "eval" / "dataset"


def list_datasets():
    names = []
    if _DATASET_DIR.exists():
        names = [Path(f).name for f in glob.glob(str(_DATASET_DIR / "*.jsonl"))]
    return names or ["analysis_golden.seed.jsonl"]


def load_dataset(name):
    path = _DATASET_DIR / name
    cases = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


# ── mock LLM: deterministic, structured, no network ─────────────────────────
def _mock_complete(system, user, schema=None):
    seed = int(hashlib.sha256((system + user).encode()).hexdigest(), 16)
    ti = 200 + len(user) // 4
    to = 60 + (seed % 120)
    # Return a small JSON object so schema/type-object cases pass deterministically.
    content = {
        "summary": (user[:120] + "…") if len(user) > 120 else user,
        "score": round(0.5 + (seed % 50) / 100.0, 2),
        "sentiment": ["positive", "neutral", "negative"][seed % 3],
    }
    return {"content": json.dumps(content), "input_tokens": ti, "output_tokens": to}


def _real_complete(system, user, deployment, schema=None):
    import asyncio

    from openai import AsyncOpenAI

    from ai_pipeline.programs_config.base import AzureOpenAIConfig
    from ai_pipeline.services import query

    oc = AzureOpenAIConfig()
    if not oc.reasoning_api_key:
        raise RuntimeError("real mode: REASONING_MODEL_APIKEY is not set")
    client = AsyncOpenAI(base_url=oc.reasoning_endpoint, api_key=oc.reasoning_api_key)
    res = asyncio.run(query(client=client, user_prompt=user, system_prompt=system,
                            model=deployment or oc.reasoning_deployment, temperature=1.0, schema=None))
    msg = res.get("message")
    content = msg if isinstance(msg, str) else json.dumps(msg)
    return {"content": content, "input_tokens": res.get("prompt_tokens", 0),
            "output_tokens": res.get("completion_tokens", 0)}


def _evaluate(output_str, case):
    ev = case.get("evaluator", "schema")
    try:
        parsed = json.loads(output_str) if isinstance(output_str, str) else output_str
    except Exception:
        parsed = output_str
    if ev == "exact_match":
        ok = str(parsed) == str(case.get("expected"))
        return ok, "" if ok else "output != expected"
    if ev == "schema":
        schema = case.get("output_schema") or {"type": "object"}
        try:
            import jsonschema
            jsonschema.validate(parsed, schema)
            return True, ""
        except ImportError:
            return isinstance(parsed, (dict, list)), "" if isinstance(parsed, (dict, list)) else "not JSON object"
        except Exception as e:
            return False, str(e)[:200]
    return True, "no evaluator"


def run_playground(program, prompt_name, version, model_alias, dataset, ad_hoc_input=None):
    prm = registry.get_version(program, prompt_name, version) if version else None
    system = (prm or {}).get("template", "") or f"[in-code {program}/{prompt_name} prompt]"
    models = {m["alias"]: m for m in registry.list_models()}
    deployment = (models.get(model_alias) or {}).get("deployment")

    cases = ([{"id": "ad-hoc", "input": {"transcript": ad_hoc_input}, "evaluator": "schema",
               "output_schema": {"type": "object"}}] if ad_hoc_input
             else load_dataset(dataset))

    results, tin, tout, passed_n = [], 0, 0, 0
    t0 = time.perf_counter()
    for case in cases:
        user = str((case.get("input") or {}).get("transcript") or (case.get("input") or {}).get("text") or "")
        try:
            comp = _mock_complete(system, user) if config.is_mock() else _real_complete(system, user, deployment)
            ok, reason = _evaluate(comp["content"], case)
        except Exception as e:
            comp = {"content": "", "input_tokens": 0, "output_tokens": 0}
            ok, reason = False, f"error: {e}"
        tin += comp["input_tokens"]; tout += comp["output_tokens"]
        passed_n += 1 if ok else 0
        results.append({"case_id": case.get("id"), "passed": ok, "reason": reason,
                        "output": comp["content"][:800]})
    latency = round((time.perf_counter() - t0) * 1000, 1)
    n = len(cases) or 1
    pass_rate = round(passed_n / n, 3)
    summary = {"n_cases": len(cases), "passed": passed_n, "pass_rate": pass_rate,
               "input_tokens": tin, "output_tokens": tout, "cost_usd": 0.0,
               "latency_ms": latency, "mode": config.mode()}
    if not ad_hoc_input:
        store.add_eval_run(program, prompt_name, version or 0, model_alias, dataset,
                           pass_rate, pass_rate >= 0.8, len(cases), 0.0)
    return {"summary": summary, "results": results, "system_prompt": system}
