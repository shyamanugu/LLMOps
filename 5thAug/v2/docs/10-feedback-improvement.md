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

## The loop, step by step

This is the part that makes feedback an improvement engine rather than a log. Six steps, each in plain terms:

```
 capture ─▶ Fabric lakehouse ─▶ triage negatives ─▶ label ─▶ add to golden dataset
                                                                     │
   ship ◀── re-evaluate (the GATE) ◀── fix (prompt / retrieval / agent) ◀──┘
```

1. **Capture and land.** Feedback comes in the four ways above, each tied to a trace id, and lands as App Insights events and Langfuse scores, both flowing into the Fabric lakehouse. This is the raw material — nothing is acted on yet, but everything is now joinable to the exact response that caused it.

2. **Triage negatives.** This is the step that matters most, so here is exactly what it means. "Triage" is the same idea as in a hospital: look at everything that came in, work out what is actually wrong with each case, and decide what to deal with first. Concretely: we pull the low-rated and failed responses — the thumbs-down, the heavy coach edits, the recruiter overrides, the abandoned outputs — and we **read them**, using the trace to see what happened inside each one. Then we **sort each bad case by its root cause**:
   - **Bad retrieval** — the model was given the wrong or missing evidence (a chunking, indexing, or search problem, doc 08).
   - **Wrong tool** — the agent called the wrong tool, or the right tool with wrong arguments (visible in the trace, measured by `tool_selection.py`, doc 06).
   - **Weak prompt** — retrieval and tools were fine, but the instruction produced the wrong tone, format, or missed something it should have caught.
   - **Missing data** — the answer needed information the system simply does not have yet (a source not connected, a field not captured).
   Then we **prioritise**: which cause is hurting the most cases, or the most important cases, gets fixed first. The output of triage is not a vague "quality is down" — it is a ranked list like "forty telesales coaching notes failed, thirty of them from bad retrieval on one program; fix that first." We do this on a regular cadence (weekly), clustering by reason code and prompt version so we act on patterns, not one-offs.

3. **Label.** For each bad case we are going to act on, a Subject Matter Expert (SME) confirms what the correct output *should* have been. For coach edits and recruiter overrides this is largely already done — the human already produced the right answer when they edited or overrode it. For thumbs-down cases the SME writes or approves the expected result. This is what turns a complaint into a test with a known-good answer.

4. **Add to the golden dataset.** The confirmed cases become new records in `usecases/apix/evals/golden.*.jsonl`, in the exact format from doc 06. This is the three-step sourcing in action: SME-authored first, then **real traffic enriches it** with the format and personalisation preferences an SME would never think to write down, then reviewed again. The golden set grows toward what actually goes wrong in production, so the gate keeps getting stricter about real failures.

5. **Fix at the right layer, then re-evaluate — the gate.** Triage already told us the cause, so we fix the matching layer and nothing else: a **prompt** change for weak-prompt cases, a **retrieval** change for bad-retrieval cases, an **agent** change for wrong-tool cases, or a **data-source connection** for missing-data cases. Cheapest correct lever first. The fix is a pull request, so it runs the same evaluation gate as every other change (`pr-checks.yml`): the newly added failing cases *plus* the full golden set must pass their thresholds. A fix that helps the reported case but hurts others cannot merge — that is the safety net.

6. **Ship.** Through the normal canary/rollback deploy (doc 09). The loop closes: the case that failed in production is now a permanent test case in the golden set, a standing guard against the same failure coming back.

## When fine-tuning enters

Fine-tuning is deliberately last. **We reach for it only after prompt and RAG improvements have plateaued** — when the golden set is rich, prompts and retrieval are tuned, and a measurable class of errors still remains. It is not a first move, because it is slower to iterate, harder to audit, and freezes behaviour that prompts and retrieval let us change in a pull request.

When we do fine-tune:

- **Training pairs are human-approved and PII-scrubbed.** The pairs come from the loop above — largely the coach-edit and recruiter-override before/after pairs, which are real ground truth — each reviewed by an SME and run through the same PII redaction as everything else before it becomes training data.
- **We use Azure OpenAI fine-tuning**, staying inside the same Azure boundary and `models.yaml` indirection: the fine-tuned model becomes a new deployment behind an alias, swapped in by config.
- **It clears the same gate.** The fine-tuned model is evaluated against the golden set exactly like a base model, and only replaces the alias if it beats the current model on the thresholds. A fine-tune is a candidate, not an automatic upgrade.

## What changes

**What changes:** feedback stops being anecdotal and becomes structured signal tied to a trace id, captured four ways, and landed in a queryable Fabric lakehouse. "Someone changed a prompt" becomes a defined loop — capture, triage negatives by root cause, label, add to golden set, fix at the right layer, re-evaluate at the gate, ship — where every production failure becomes a permanent test. Fine-tuning moves from a tempting first idea to a last, gated, human-approved step. **Migration step:** add the trace id to APIX responses and stand up the `/feedback` endpoint plus the coach-edit capture; the first week of real edits seeds the golden set faster than SME authoring alone, and the loop is running from there.
