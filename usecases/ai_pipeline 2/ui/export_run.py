"""Export a real pipeline run into the demo UI's data contract.

Produces `ui/public/sample-data.json` (the shape the React app consumes) from:
  * the JSONL trace file written when AI_PIPELINE_ENV run used AI_PIPELINE_TRACER=jsonl
    (LLM calls, tokens, cost, latency, guardrail flags), and
  * a directory of the summary step's per-employee JSON reports (KPIs, scores,
    comparisons, reflection, top calls, escalations).

Usage:
    python ui/export_run.py \
        --trace-file traces/trace.jsonl \
        --summaries-dir /path/to/summary/json \
        --program telesales --date 2025-08-28 \
        --out ui/public/sample-data.json

This utility uses only the standard library. The summary-JSON field mapping is
best-effort/defensive — if your program's report uses different keys, adjust the
getters below; nothing here crashes on a missing field.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _g(d: dict, *keys, default=None):
    """Return the first present key from *keys* (case-insensitive-ish)."""
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def load_llmops(trace_file: Path) -> dict:
    steps: dict[str, dict] = defaultdict(
        lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
                 "errors": 0, "guardrail_flags": 0, "_lat_sum": 0.0}
    )
    totals = {"llm_calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
              "errors": 0, "guardrail_flags": 0, "_lat_sum": 0.0}

    if trace_file.exists():
        with open(trace_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("kind") != "step":
                    continue
                s = steps[ev.get("step_name", "unknown")]
                lat = float(ev.get("latency_ms", 0) or 0)
                flagged = 1 if ev.get("guardrail_reason") else 0
                errored = 1 if ev.get("error") else 0
                for bucket, key in ((s, "calls"), (totals, "llm_calls")):
                    bucket[key] += 1
                for bucket in (s, totals):
                    bucket["input_tokens"] += int(ev.get("input_tokens", 0) or 0)
                    bucket["output_tokens"] += int(ev.get("output_tokens", 0) or 0)
                    bucket["cost_usd"] += float(ev.get("cost_usd", 0) or 0)
                    bucket["errors"] += errored
                    bucket["guardrail_flags"] += flagged
                    bucket["_lat_sum"] += lat

    def _finish(b: dict, calls_key: str) -> dict:
        calls = b.get(calls_key, 0) or b.get("calls", 0)
        avg = round(b["_lat_sum"] / calls, 1) if calls else 0.0
        out = {k: (round(v, 6) if k == "cost_usd" else v) for k, v in b.items() if not k.startswith("_")}
        out["avg_latency_ms"] = avg
        return out

    by_step = []
    for name, b in steps.items():
        row = _finish(b, "calls")
        row["step"] = name
        by_step.append(row)
    # keep a natural step order when present
    order = ["denoise", "analysis", "summary", "individual_metrics", "kpi"]
    by_step.sort(key=lambda r: order.index(r["step"]) if r["step"] in order else 99)

    totals_out = _finish(totals, "llm_calls")
    return {"totals": totals_out, "by_step": by_step}


def load_employees_and_kpis(summaries_dir: Path) -> tuple[list, list]:
    employees, kpis = [], []
    if not summaries_dir or not summaries_dir.exists():
        return employees, kpis

    for path in sorted(summaries_dir.glob("*.json")):
        try:
            rep = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not kpis:
            raw_kpis = _g(rep, "kpis", "kpi", default=[]) or []
            for k in raw_kpis:
                kpis.append({
                    "key": _g(k, "key", default=""),
                    "label": _g(k, "label", default=_g(k, "key", default="")),
                    "value": _g(k, "value", "score", default=0),
                    "unit": _g(k, "unit", default="percent"),
                    "delta": _g(k, "delta", default=None),
                })

        scores = [
            {"label": _g(s, "label", "key", default=""),
             "value": _g(s, "value", "score", default=0),
             "unit": _g(s, "unit", default="percent")}
            for s in (_g(rep, "scores", "behaviors", default=[]) or [])
        ]
        top_calls = [
            {"contact_id": str(_g(c, "contact_id", "id", default="")),
             "intent": _g(c, "intent", "customer_intent", default=""),
             "outcome": _g(c, "outcome", "sales_outcome", default=""),
             "importance": _g(c, "importance", "call_importance", default=0),
             "tags": _g(c, "tags", default=[]) or [],
             "excerpt": _g(c, "excerpt", "transcript_excerpt", "summary", default="")}
            for c in (_g(rep, "top_calls", "calls", default=[]) or [])[:5]
        ]
        escalations = [
            {"contact_id": str(_g(e, "contact_id", "id", default="")),
             "reason": _g(e, "reason", "summary", default=""),
             "excerpt": _g(e, "excerpt", "transcript_excerpt", default="")}
            for e in (_g(rep, "escalations", default=[]) or [])[:5]
        ]
        employees.append({
            "employee_id": str(_g(rep, "employee_id", "EmployeeID", default=path.stem)),
            "name": _g(rep, "name", "EmployeeName", default=path.stem),
            "coach": _g(rep, "coach", "CoachName", default=""),
            "calls_analyzed": _g(rep, "calls_analyzed", "call_count", default=len(top_calls)),
            "reflection": _g(rep, "reflection", "reflection_text", default=""),
            "scores": scores,
            "comparisons": _g(rep, "comparisons", default=[]) or [],
            "top_calls": top_calls,
            "escalations": escalations,
        })
    return employees, kpis


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Export a pipeline run to the demo UI data contract")
    p.add_argument("--trace-file", default="traces/trace.jsonl")
    p.add_argument("--summaries-dir", default=None, help="dir of summary per-employee JSON reports")
    p.add_argument("--program", default="telesales")
    p.add_argument("--environment", default="dev")
    p.add_argument("--date", default="")
    p.add_argument("--model-deployment", default="gpt-5.4-nano")
    p.add_argument("--run-id", default="")
    p.add_argument("--out", default="ui/public/sample-data.json")
    args = p.parse_args(argv)

    llmops = load_llmops(Path(args.trace_file))
    employees, kpis = load_employees_and_kpis(Path(args.summaries_dir) if args.summaries_dir else None)

    data = {
        "meta": {
            "generated_at": "", "run_id": args.run_id, "program": args.program,
            "environment": args.environment, "date": args.date,
            "model_deployment": args.model_deployment, "mode": "real", "source": "live",
        },
        "llmops": llmops,
        "kpis": kpis,
        "employees": employees,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {out} | {len(employees)} employee(s), {len(kpis)} KPI(s), "
          f"{llmops['totals'].get('llm_calls', 0)} LLM call(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
