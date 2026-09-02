"""Seed the local Ops store (mock) so the console shows data on first run:
traces + guardrail + feedback from the demo sample-data.json, and a couple of
starter prompt versions in the registry."""
import json

from . import config, registry, store

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
    c = store.counts()
    if c["traces"] == 0 or force:
        _seed_from_sample()
    if not registry.list_prompts() or force:
        for (prog, name), (tmpl, cap) in _STARTER_PROMPTS.items():
            if not registry.get_prompt(prog, name):
                registry.save_version(prog, name, tmpl, cap, note="seeded starter prompt")
    return {"mode": config.mode(), **store.counts(), "prompts": len(registry.list_prompts())}


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
                            (s.get("cost_usd", 0) or 0) / calls, s.get("avg_latency_ms", 0))
    # a few guardrail + feedback rows for the audit/feedback tabs
    store.add_guardrail(run_id, "analysis", "gpt-5.4-nano", "flagged", "PII detected (flagged, not blocked): phone")
    store.add_guardrail(run_id, "denoise", "gpt-5.4-nano", "flagged", "PII detected (flagged, not blocked): email")
    for e in (data.get("employees") or [])[:3]:
        for call in (e.get("top_calls") or [])[:1]:
            store.add_feedback("telesales", call.get("contact_id", ""), "analysis", "up",
                               comment=f"Good analysis for {e.get('name')}", rater="coach")


if __name__ == "__main__":
    print(seed(force="--force" in __import__("sys").argv))
