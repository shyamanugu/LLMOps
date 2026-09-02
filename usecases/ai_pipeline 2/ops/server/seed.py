"""Seed the local Ops store (mock) so the console shows data on first run:
traces + guardrail + feedback from the demo sample-data.json, and a couple of
starter prompt versions in the registry."""
import json

from . import config, datasets, engine, registry, store

_SAMPLE = config.OPS_DIR / "server" / "sample_dashboard.json"
if not _SAMPLE.exists():
    _SAMPLE = config.PKG_DIR / "ui" / "public" / "sample-data.json"

_STARTER_PROMPTS = {
    ("telesales", "denoise"): ("You clean raw call-center transcripts into a structured, speaker-labelled "
                               "list. Remove filler and disfluencies; preserve meaning and all facts.", "bulk"),
    ("telesales", "analysis"): ("You are a sales-call analyst. Score the agent's behaviors, extract intent, "
                                "outcome, tags, and flag escalations. Return structured JSON.", "reason"),
}


def seed(force=False):
    config.ensure_dirs()
    store.init_db()
    datasets.seed_defaults()
    c = store.counts()
    if c["traces"] == 0 or force:
        _seed_from_sample()
    if c["eval_runs"] == 0 or force:
        _seed_eval_history()
    if not registry.list_prompts() or force:
        for (prog, name), (tmpl, cap) in _STARTER_PROMPTS.items():
            if not registry.get_prompt(prog, name):
                registry.save_version(prog, name, tmpl, cap, note="seeded starter prompt")
    return {"mode": config.mode(), **store.counts(), "prompts": len(registry.list_prompts())}


def _seed_eval_history():
    """A few prior evaluation runs so the Evaluation tab shows trend/metrics."""
    history = [
        ("analysis", 1, "reason", "telesales_golden.jsonl", 0.80),
        ("analysis", 1, "reason", "telesales_golden.jsonl", 0.90),
        ("analysis", 2, "reason", "telesales_golden.jsonl", 0.95),
        ("analysis", 2, "bulk", "telesales_golden.jsonl", 0.85),
        ("denoise", 1, "bulk", "analysis_golden.jsonl", 1.00),
    ]
    for prompt, ver, model, ds, rate in history:
        store.add_eval_run("telesales", prompt, ver, model, ds, rate, rate >= 0.8, 5,
                           engine.cost_usd("gpt-4o-mini", 2100, 360))


def _seed_from_sample():
    if not _SAMPLE.exists():
        return
    data = json.loads(_SAMPLE.read_text(encoding="utf-8"))
    run_id = (data.get("meta") or {}).get("run_id", "sample")
    # traces from llmops.by_step (approx per-call rows so monitoring aggregates look real)
    for s in (data.get("llmops") or {}).get("by_step", []):
        calls = max(1, int(s.get("calls", 1)))
        per_in = int(s.get("input_tokens", 0)) // calls
        per_out = int(s.get("output_tokens", 0)) // calls
        for _ in range(calls):
            store.add_trace(run_id, s.get("step"), None, "gpt-5.4-nano", per_in, per_out,
                            engine.cost_usd("gpt-5.4-nano", per_in, per_out), s.get("avg_latency_ms", 0))
    # a few guardrail + feedback rows for the audit/feedback tabs
    store.add_guardrail(run_id, "analysis", "gpt-5.4-nano", "flagged", "PII detected (flagged, not blocked): phone")
    store.add_guardrail(run_id, "denoise", "gpt-5.4-nano", "flagged", "PII detected (flagged, not blocked): email")
    for e in (data.get("employees") or [])[:3]:
        for call in (e.get("top_calls") or [])[:1]:
            store.add_feedback("telesales", call.get("contact_id", ""), "analysis", "up",
                               comment=f"Good analysis for {e.get('name')}", rater="coach")


if __name__ == "__main__":
    print(seed(force="--force" in __import__("sys").argv))
