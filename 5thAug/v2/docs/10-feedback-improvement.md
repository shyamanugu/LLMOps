# Feedback & Improvement Loop

This is how the platform gets better over time instead of drifting. Every response carries a trace id; feedback of several kinds attaches to that id; it flows to App Insights, Langfuse, and a Microsoft Fabric lakehouse; and a defined loop turns the bad cases into golden-dataset entries, fixes, and a re-evaluation gate before anything ships. Fine-tuning enters only at the end, and only when the cheaper levers are exhausted.

## Today

**Today (assumption — to confirm):** feedback, if captured at all, is anecdotal — a coach mentions a bad report, a recruiter edits an answer and moves on, and none of it is tied back to the specific response that produced it. There is no trace id to join on, so there is no way to say "these thirty coaching notes were wrong for this reason." Improvements happen when someone notices a pattern and changes a prompt, with no measurement that the change actually helped.

## Our setup

**Every response carries a trace id.** The same OpenTelemetry trace id from `tracing.py` (doc 05) is returned to the caller and stored with the output. That id is the join key for everything below — every piece of feedback points at exactly one response, and through it at the exact prompt version, model deployment, retrieved chunks, and tool calls that produced it.

**Feedback is captured in four ways**, all posted to a small feedback API that writes an App Insights custom event and a Langfuse score, both keyed by trace id:

- **Explicit thumbs + reason** — a rating plus a short structured reason (`wrong_evidence`, `tone`, `missed_issue`), so a negative is triageable, not just a count.
- **Coach edits (APIX)** — when a coach edits a generated coaching note before sending, we capture the before/after. The edit *is* the ground-truth signal: it shows what "right" looked like for that case.
- **Recruiter overrides (Hiring)** — when a recruiter overrides a model's candidate assessment, the override and its reason are captured the same way.
- **Implicit signals** — retries, regenerations, and abandonment (response generated but never used). These need no user action and catch problems people would not bother to rate.

```python
# POST /feedback  — attaches to the response's trace id
def record_feedback(trace_id, kind, value, reason=None, edit=None):
    app_insights.track_event("feedback", {           # system of record
        "trace_id": trace_id, "kind": kind,          # thumb|edit|override|implicit
        "value": value, "reason": reason})
    langfuse.score(trace_id=trace_id, name=kind,     # LLM lens, lines up with traces
                   value=score_of(value), comment=reason)
    if edit: store_pair(trace_id, edit)              # before/after -> candidate golden case
```

**Where it lands.** App Insights is the system of record for events; Langfuse holds the scores next to the traces so we can read a low score and jump straight to the full trace. Both are exported into a **Microsoft Fabric lakehouse**, where feedback joins traces, costs, and eval history in one place we can query and slice — by program, by prompt version, by reason code.

**The loop.** This is the part that makes feedback an improvement engine rather than a log:

```
 capture ─▶ Fabric lakehouse ─▶ triage negatives ─▶ label ─▶ add to golden dataset
                                                                     │
   ship ◀── re-evaluate (the GATE) ◀── fix (prompt / retrieval / agent) ◀──┘
```

1. **Triage negatives.** Weekly, we pull the negatives and overrides from the lakehouse and cluster them by reason and by prompt version. We are looking for patterns — "coaching notes on the telesales program keep citing the wrong moment" — not one-offs.
2. **Label.** A Subject Matter Expert (SME) confirms what the correct output should have been. For coach edits and recruiter overrides this is largely already there — the human already produced the right answer.
3. **Add to the golden dataset.** The confirmed cases become new records in `evals/apix/golden.*.jsonl`, in the exact format from doc 06. This is the three-step sourcing in action: SME-authored first, then **real traffic enriches it** with the format and personalisation preferences an SME would never think to write down, then reviewed again. The golden set grows toward what actually goes wrong in production.
4. **Fix at the right layer.** The trace tells us where the fault is, so we fix the right thing: a **prompt** change (wrong tone, missing instruction), a **retrieval** change (wrong or missing evidence — a chunking or index fix from doc 08), or an **agent** change (wrong tool selected — caught by `tool_selection.py`). Cheapest correct lever first.
5. **Re-evaluate — the gate.** The fix is a pull request, so it runs the same evaluation gate as every other change (`pr-checks.yml`): the newly added failing cases plus the full golden set must pass their thresholds. A fix that helps the reported case but hurts others cannot merge.
6. **Ship.** Through the normal canary/rollback deploy (doc 09). The loop closes: the case that failed in production is now a permanent guardrail against regression.

## When fine-tuning enters

Fine-tuning is deliberately last. **We reach for it only after prompt and RAG improvements have plateaued** — when the golden set is rich, prompts and retrieval are tuned, and a measurable class of errors still remains. It is not a first move, because it is slower to iterate, harder to audit, and freezes behaviour that prompts and retrieval let us change in a pull request.

When we do fine-tune:

- **Training pairs are human-approved and PII-scrubbed.** The pairs come from the loop above — largely the coach-edit and recruiter-override before/after pairs, which are real ground truth — each reviewed by an SME and run through the same PII redaction as everything else before it becomes training data.
- **We use Azure OpenAI fine-tuning**, staying inside the same Azure boundary and `models.yaml` indirection: the fine-tuned model becomes a new deployment behind an alias, swapped in by config.
- **It clears the same gate.** The fine-tuned model is evaluated against the golden set exactly like a base model, and only replaces the alias if it beats the current model on the thresholds. A fine-tune is a candidate, not an automatic upgrade.

## What changes

**What changes:** feedback stops being anecdotal and becomes structured signal tied to a trace id, captured four ways, and landed in a queryable Fabric lakehouse. "Someone changed a prompt" becomes a defined loop — triage, label, add to golden set, fix at the right layer, re-evaluate at the gate, ship — where every production failure becomes a permanent test. Fine-tuning moves from a tempting first idea to a last, gated, human-approved step. **Migration step:** add the trace id to APIX responses and stand up the `/feedback` endpoint plus the coach-edit capture; the first week of real edits seeds the golden set faster than SME authoring alone, and the loop is running from there.
