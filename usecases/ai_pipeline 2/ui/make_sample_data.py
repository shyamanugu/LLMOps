"""Generate ui/public/sample-data.json from the SAME transcripts that
tools/make_sample_raw.py produces, so the demo UI matches a real Tier-B run of
those 12 telesales calls (5 agents, per-agent call distribution, ~34 LLM calls).

This is illustrative sample data (meta.source = "sample") — the per-call analysis
annotations below stand in for what the pipeline's `analysis` step would emit, and
the LLMOps totals reflect a real run's call shape (12 denoise + 12 analysis +
5 summary + 5 individual_metrics; kpi has no LLM). Cost is $0 until per-token
rates are set in pricing.yaml — same as a live run.

    python ui/make_sample_data.py            # writes ui/public/sample-data.json
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PKG = _HERE.parent  # ai_pipeline package dir

# Load build_rows() from the raw generator (pure dicts — no polars needed).
_spec = importlib.util.spec_from_file_location("_msr", _PKG / "tools" / "make_sample_raw.py")
_msr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_msr)
ROWS = _msr.build_rows("VZW Telesales")  # 12 rows, contact_id C1000..C1011

# Per-call analysis annotations (what `analysis` would produce), keyed by contact_id.
# Each: intent, outcome, importance(0-1), tags, excerpt (denoised-style),
# and boolean KPI signals: resolved, ros (right-of-sell), save, escalation, thumbs_up.
ANN = {
    "C1000": ("Plan upgrade — data overages", "Closed deal", 0.92, ["upsell", "value-framing", "data"],
              "Framed the unlimited upgrade against last month's overage charges to justify the $10 difference.",
              dict(resolved=1, ros=1, save=0, esc=0, thumbs=1)),
    "C1001": ("Billing dispute — price increase", "Retained", 0.78, ["retention", "billing", "empathy"],
              "Acknowledged the surprise charge, explained the expired promo, and applied a loyalty credit.",
              dict(resolved=1, ros=0, save=1, esc=0, thumbs=1)),
    "C1002": ("Trade-in promo inquiry", "In progress", 0.70, ["upsell", "trade-in"],
              "Checked live trade value and surfaced the full $800 device credit.",
              dict(resolved=0, ros=1, save=0, esc=0, thumbs=1)),
    "C1003": ("Cancellation — relocating abroad", "Saved (suspend)", 0.88, ["retention", "save", "international"],
              "Offered line suspension up to 24 months instead of cancelling.",
              dict(resolved=1, ros=0, save=1, esc=0, thumbs=1)),
    "C1004": ("Add a line + device", "Closed deal", 0.85, ["add-line", "upsell"],
              "Bundled a new line at $20 with a free entry device.",
              dict(resolved=1, ros=1, save=0, esc=0, thumbs=1)),
    "C1005": ("Service quality — dropped calls", "Resolved", 0.80, ["service", "escalation-risk"],
              "Checked tower maintenance and shipped a network extender at no charge.",
              dict(resolved=1, ros=0, save=0, esc=1, thumbs=0)),
    "C1006": ("One-time bill payment", "No sale", 0.40, ["billing"],
              "Took the payment and respected the customer's decline of autopay.",
              dict(resolved=1, ros=0, save=0, esc=0, thumbs=1)),
    "C1007": ("Carrier switch — 3 lines", "Closed deal", 0.96, ["acquisition", "upsell", "high-value"],
              "Covered switching costs and set up three lines on unlimited plus.",
              dict(resolved=1, ros=1, save=0, esc=0, thumbs=1)),
    "C1008": ("Repeat issue — international texts", "Resolved + credit", 0.82, ["escalation", "service", "recovery"],
              "Owned the repeat contacts, fixed the messaging add-on, and applied a goodwill credit.",
              dict(resolved=1, ros=0, save=0, esc=1, thumbs=1)),
    "C1009": ("Bill review — too expensive", "Retained (plan switch)", 0.75, ["retention", "save", "right-plan"],
              "Moved the customer to a cheaper current plan with a streaming perk.",
              dict(resolved=1, ros=0, save=1, esc=0, thumbs=1)),
    "C1010": ("Lost/stolen device", "Resolved (claim)", 0.70, ["support", "security"],
              "Suspended the line and initiated an insurance claim for a replacement.",
              dict(resolved=1, ros=0, save=0, esc=0, thumbs=1)),
    "C1011": ("Wearable add-on", "Closed deal", 0.72, ["upsell", "wearable"],
              "Added the discounted watch via number share at $10/mo.",
              dict(resolved=1, ros=1, save=0, esc=0, thumbs=1)),
}

# Curated per-employee behavior scores + coaching reflection (what `summary` reflects).
EMP_EXTRA = {
    9040400: dict(  # Jordan Lee
        scores=[("Active Listening", 0.90), ("Acknowledgment", 0.86), ("Empathy", 0.82),
                ("Product Knowledge", 0.91), ("Objection Handling", 0.84), ("Closing", 0.88)],
        reflection=("Jordan consistently anchors offers to the customer's own numbers — the data-overage "
                    "upgrade was a textbook value framing. On the dropped-calls contact, empathy dipped and "
                    "the customer's sentiment stayed negative; slowing down to acknowledge the frustration "
                    "before jumping to the extender would lift the recovery. Strong closer overall.")),
    9040401: dict(  # Priya Nair
        scores=[("Active Listening", 0.88), ("Acknowledgment", 0.92), ("Empathy", 0.90),
                ("Product Knowledge", 0.79), ("Objection Handling", 0.81), ("Closing", 0.72)],
        reflection=("Priya excels at defusing billing frustration — the loyalty-credit save was handled with "
                    "genuine empathy. She respects a 'no' cleanly (autopay decline). Opportunity: on the "
                    "wearable add-on she could deepen product knowledge to pre-empt the number-share question "
                    "and shorten the path to close.")),
    9040402: dict(  # Marcus Reyes
        scores=[("Active Listening", 0.84), ("Acknowledgment", 0.80), ("Empathy", 0.78),
                ("Product Knowledge", 0.93), ("Objection Handling", 0.89), ("Closing", 0.90)],
        reflection=("Marcus is the team's strongest on high-value acquisition — the three-line carrier switch "
                    "was well-orchestrated and the trade-in credit surfaced proactively. Watch the trade-in "
                    "inquiry that stalled in 'in progress'; a firmer next-step ask would convert more of these.")),
    9040403: dict(  # Ava Thompson
        scores=[("Active Listening", 0.91), ("Acknowledgment", 0.88), ("Empathy", 0.93),
                ("Product Knowledge", 0.80), ("Objection Handling", 0.85), ("Closing", 0.76)],
        reflection=("Ava turns saves and service recovery into loyalty — the suspend-instead-of-cancel play and "
                    "the owned repeat-contact recovery both landed well. Her empathy is a standout. To grow, "
                    "pair that trust with a light cross-sell where appropriate rather than closing the call flat.")),
    9040404: dict(  # Diego Alvarez
        scores=[("Active Listening", 0.83), ("Acknowledgment", 0.82), ("Empathy", 0.80),
                ("Product Knowledge", 0.86), ("Objection Handling", 0.83), ("Closing", 0.87)],
        reflection=("Diego balances retention and growth — the add-a-line bundle and the right-plan downgrade "
                    "both kept the customer happy while protecting revenue. Continue leading with the "
                    "total-cost story; it's clearly resonating.")),
}

# LLMOps per-step shape for a real run of these 12 transcripts.
BY_STEP = [
    dict(step="denoise", calls=12, input_tokens=10_800, output_tokens=3_120, cost_usd=0.0,
         avg_latency_ms=1400.0, errors=0, guardrail_flags=0),
    dict(step="analysis", calls=12, input_tokens=42_000, output_tokens=7_200, cost_usd=0.0,
         avg_latency_ms=2200.0, errors=0, guardrail_flags=0),
    dict(step="summary", calls=5, input_tokens=20_000, output_tokens=2_500, cost_usd=0.0,
         avg_latency_ms=2600.0, errors=0, guardrail_flags=0),
    dict(step="individual_metrics", calls=5, input_tokens=6_000, output_tokens=1_500, cost_usd=0.0,
         avg_latency_ms=1500.0, errors=0, guardrail_flags=0),
]


def _pct(numer, denom):
    return round(numer / denom, 3) if denom else 0.0


def build():
    # group contacts per employee, preserving generator order
    by_emp = {}
    for r in ROWS:
        by_emp.setdefault(r["EmployeeID"], []).append(r)

    employees = []
    for emp_id, rows in by_emp.items():
        first = rows[0]
        top_calls, escalations = [], []
        for r in rows:
            intent, outcome, importance, tags, excerpt, _sig = ANN[r["contact_id"]]
            top_calls.append(dict(contact_id=r["contact_id"], intent=intent, outcome=outcome,
                                  importance=importance, tags=tags, excerpt=excerpt))
            if _sig["esc"]:
                escalations.append(dict(contact_id=r["contact_id"], reason=intent, excerpt=excerpt))
        extra = EMP_EXTRA[emp_id]
        # team comparison: escalations count + closed deals for this agent
        esc_ct = sum(ANN[r["contact_id"]][5]["esc"] for r in rows)
        closed = sum(1 for r in rows if "Closed deal" in ANN[r["contact_id"]][1])
        employees.append(dict(
            employee_id=str(emp_id), name=first["EmployeeName"], coach=first["CoachName"],
            calls_analyzed=len(rows),
            reflection=extra["reflection"],
            scores=[dict(label=l, value=v, unit="percent") for (l, v) in extra["scores"]],
            comparisons=[
                dict(metric="Escalations", individual=esc_ct, teamAvg=0.4, unit="count"),
                dict(metric="Closed Deals", individual=closed, teamAvg=0.6, unit="count"),
            ],
            top_calls=top_calls, escalations=escalations,
        ))

    # KPIs aggregated across the 12 calls
    n = len(ROWS)
    resolved = sum(a[5]["resolved"] for a in ANN.values())
    ros = sum(a[5]["ros"] for a in ANN.values())
    saves = sum(a[5]["save"] for a in ANN.values())
    at_risk = sum(1 for a in ANN.values() if "Retain" in a[1] or "Saved" in a[1] or a[1] == "No sale")
    esc = sum(a[5]["esc"] for a in ANN.values())
    thumbs = sum(a[5]["thumbs"] for a in ANN.values())
    avg_handle = round(sum(r["totalcalltime"] for r in ROWS) / n)
    kpis = [
        dict(key="resolution_rate", label="Resolution Rate", value=_pct(resolved, n), unit="percent", delta=0.04),
        dict(key="right_of_sell_rate", label="Right-of-Sell Rate", value=_pct(ros, n), unit="percent", delta=0.06),
        dict(key="save_rate", label="Save Rate", value=_pct(saves, at_risk), unit="percent", delta=0.09),
        dict(key="escalation_rate", label="Escalation Rate", value=_pct(esc, n), unit="percent", delta=-0.03),
        dict(key="avg_handle_time", label="Avg Handle Time (s)", value=avg_handle, unit="count", delta=-12),
        dict(key="thumbs_up", label="Thumbs Up %", value=_pct(thumbs, n), unit="percent", delta=0.05),
    ]

    # LLMOps totals computed from by_step (consistent, like the real exporter)
    tot_calls = sum(s["calls"] for s in BY_STEP)
    lat_weighted = sum(s["calls"] * s["avg_latency_ms"] for s in BY_STEP)
    totals = dict(
        llm_calls=tot_calls,
        input_tokens=sum(s["input_tokens"] for s in BY_STEP),
        output_tokens=sum(s["output_tokens"] for s in BY_STEP),
        cost_usd=round(sum(s["cost_usd"] for s in BY_STEP), 6),
        errors=sum(s["errors"] for s in BY_STEP),
        avg_latency_ms=round(lat_weighted / tot_calls, 1) if tot_calls else 0.0,
        guardrail_flags=sum(s["guardrail_flags"] for s in BY_STEP),
    )

    return dict(
        meta=dict(generated_at="2025-08-28T10:00:00Z", run_id="sample01", program="telesales",
                  environment="dev", date="2025-08-28", model_deployment="gpt-5.4-nano",
                  mode="mock", source="sample"),
        llmops=dict(totals=totals, by_step=BY_STEP),
        kpis=kpis,
        employees=employees,
    )


def main():
    data = build()
    out = _HERE / "public" / "sample-data.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    t = data["llmops"]["totals"]
    print(f"Wrote {out}")
    print(f"  {len(data['employees'])} employees, {len(data['kpis'])} KPIs, "
          f"{t['llm_calls']} LLM calls, {t['input_tokens'] + t['output_tokens']:,} tokens")


if __name__ == "__main__":
    main()
