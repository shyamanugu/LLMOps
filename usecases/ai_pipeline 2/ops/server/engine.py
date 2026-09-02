"""Playground engine: run a prompt+model against a golden dataset and score it.

Mock mode uses a deterministic mock LLM (no OpenAI needed). Real mode calls the
actual model via the pipeline's query() path (expects REASONING_MODEL_* creds);
if they're missing it returns a clear error instead of pretending."""
import hashlib
import json
import time

from . import config, datasets, registry, store


# Illustrative per-1k-token USD rates so the demo never shows a misleading $0.
# These are placeholders for presentation; replace with AFNI's contracted rates
# in platform pricing.yaml. Real mode reads pricing.yaml via the platform when
# available; this map is the mock/offline fallback.
_RATES = {
    "gpt-4o":            {"in": 0.0050, "out": 0.0150},
    "gpt-4o-mini":       {"in": 0.00015, "out": 0.00060},
    "gpt-5.4-nano":      {"in": 0.00020, "out": 0.00080},
    "gpt-5-mini":        {"in": 0.00040, "out": 0.00160},
    "gpt-4.1":           {"in": 0.00200, "out": 0.00800},
    "o3-mini":           {"in": 0.00110, "out": 0.00440},
    "text-embedding-3-large": {"in": 0.00013, "out": 0.0},
    "_default":          {"in": 0.00050, "out": 0.00150},
}


def cost_usd(deployment, input_tokens, output_tokens):
    r = _RATES.get(deployment or "", _RATES["_default"])
    return round((input_tokens / 1000) * r["in"] + (output_tokens / 1000) * r["out"], 6)


def list_datasets():
    return [d["name"] for d in datasets.list_datasets()] or ["telesales_golden.jsonl"]


def load_dataset(name):
    return datasets.read_cases(name)


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


def run_playground(program, prompt_name, version, model_alias, dataset, ad_hoc_input=None,
                   prompt_text=None):
    # prompt_text (an edited/unsaved prompt from the Playground) wins over the
    # stored version, so users can iterate on wording before saving a version.
    if prompt_text and prompt_text.strip():
        system = prompt_text
    else:
        prm = registry.get_version(program, prompt_name, version) if version else None
        system = (prm or {}).get("template", "") or f"[in-code {program}/{prompt_name} prompt]"
    models = {m["alias"]: m for m in registry.list_models()}
    deployment = (models.get(model_alias) or {}).get("deployment") or "gpt-5.4-nano"

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
    cost = cost_usd(deployment, tin, tout)
    summary = {"n_cases": len(cases), "passed": passed_n, "pass_rate": pass_rate,
               "input_tokens": tin, "output_tokens": tout, "cost_usd": cost,
               "latency_ms": latency, "mode": config.mode(), "deployment": deployment}
    if not ad_hoc_input:
        store.add_eval_run(program, prompt_name, version or 0, model_alias, dataset,
                           pass_rate, pass_rate >= 0.8, len(cases), cost)
    return {"summary": summary, "results": results, "system_prompt": system}


# ── Mock pipeline run (Application tab) ─────────────────────────────────────
_STEP_META = [
    ("denoise", "Clean raw transcripts", 12, 1400),
    ("analysis", "Per-call scoring", 12, 2200),
    ("summary", "Weekly reflection", 5, 2600),
    ("individual_metrics", "Coaching metrics", 5, 1500),
    ("kpi", "Aggregate → report", 0, 300),
]


def _sample_dashboard():
    """The transcript-derived sample dashboard the Application tab renders.
    Bundled inside ops/ so the console is self-contained (no dependency on the
    legacy React demo folder); falls back to it if the bundled copy is missing."""
    for f in (config.OPS_DIR / "server" / "sample_dashboard.json",
              config.PKG_DIR / "ui" / "public" / "sample-data.json"):
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {"meta": {}, "llmops": {"totals": {}, "by_step": []}, "kpis": [], "employees": []}


def run_pipeline(program="telesales", date="2025-08-28", steps=None, seed_traces=True):
    """Simulate a pipeline run for the Application tab. In mock mode this executes
    instantly and records traces/guardrails so Monitoring reflects the run. Returns
    per-step progress + the results dashboard payload."""
    steps = steps or [s[0] for s in _STEP_META]
    run_id = hashlib.sha1(f"{program}{date}{time.time()}".encode()).hexdigest()[:8]
    progress = []
    for name, desc, calls, latency in _STEP_META:
        if name not in steps:
            continue
        if seed_traces:
            ti, to = (900, 120) if name == "denoise" else (350, 90)
            for _ in range(calls):
                store.add_trace(run_id, name, "reason" if name != "denoise" else "bulk",
                                "gpt-5.4-nano", ti, to, cost_usd("gpt-5.4-nano", ti, to), latency)
        if name in ("analysis", "denoise"):
            store.add_guardrail(run_id, name, "gpt-5.4-nano", "flagged",
                                "PII detected (flagged, not blocked): phone")
        progress.append({"step": name, "desc": desc, "status": "ok", "calls": calls,
                         "latency_ms": latency})
    dash = _sample_dashboard()
    dash.setdefault("meta", {})
    dash["meta"].update({"run_id": run_id, "program": program, "date": date, "mode": config.mode()})
    return {"run_id": run_id, "program": program, "date": date, "steps": progress,
            "dashboard": dash, "mode": config.mode()}
