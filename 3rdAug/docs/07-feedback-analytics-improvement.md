# Feedback, Analytics & the Improvement Loop

## What this closes

Evaluation (doc 05) and observability (doc 06) tell you whether the system is working. This document is about the next step: turning what users actually do and say into concrete changes to prompts, retrieval, and agents — and, eventually, into fine-tuning data. Without this loop, a golden dataset goes stale, dashboards get built and ignored, and the same complaint keeps recurring because nobody routed it back to the thing that caused it.

## How responses are captured

Every response the system produces carries a **trace id** — the same one used for observability — so that any feedback about that response can be joined back to the exact prompt version, model, and retrieved context that produced it. Feedback comes in two flavors:

**Explicit signals** — the user (or an agent) deliberately tells you something:

- Thumbs up / thumbs down, with an optional reason code ("wrong information," "too slow," "didn't understand me," "unhelpful tone")
- Edits — the user (or a human agent reviewing an AI draft) changes the output before using it; the diff between the AI draft and the final edited version is itself signal
- Escalation to a human — the system or the user gave up on the AI and routed to a person

**Implicit signals** — nobody said anything, but behavior tells you something:

- Retries — the user asked essentially the same question again, which usually means the first answer did not land
- Abandonment — the user left the session without a resolution signal
- Session length — an unusually long session on a task that should be quick is often a sign of the assistant going in circles

All of this is written through a **feedback application programming interface (API)** — a small internal endpoint the front end and any human-review tooling call when a signal happens. That API fans out to two places at once: an App Insights (Azure Application Insights) custom event, and a Langfuse score attached to the trace. Neither destination is optional — App Insights is the system of record and Langfuse is what makes the feedback usable day-to-day (filterable, attachable to a session view, browsable by an SME without a query language).

```json
{
  "trace_id": "8f3e2c91-...",
  "event_type": "feedback",
  "signal": "thumbs_down",
  "reason_code": "wrong_information",
  "free_text": "Told me the wrong refund window",
  "use_case": "billing-support-assistant",
  "prompt_version": "v7",
  "timestamp": "2026-08-03T14:22:10Z"
}
```

## Where the data lands

- **App Insights custom events** — the durable, compliance-covered record. Every feedback event, every model call, every trace — all of it lands here first, inside the Azure tenant, subject to the same retention policy as the rest of the platform's telemetry.
- **Langfuse scores** — the same feedback, attached to the corresponding trace/generation inside Langfuse, so an engineer debugging a specific session can see the user's thumbs-down sitting right next to the prompt and completion that earned it.
- **Microsoft Fabric lakehouse** — both of the above are exported (via a scheduled diagnostic export from App Insights, and a periodic export job from Langfuse) into a Fabric lakehouse. This is where the data becomes reusable beyond day-to-day debugging: business intelligence (BI) reporting, trend analysis over months, and — eventually — curation of training pairs for fine-tuning, all run against the lakehouse copy rather than querying the live observability tools.

## Analytics dashboard spec

| Tile / panel | What it shows | Rendered by |
|---|---|---|
| **Volume** | Requests/sessions per use case per day, trend over time | Power BI on Fabric |
| **Containment** | Percentage of sessions resolved by the AI without escalating to a human | Power BI on Fabric |
| **p95 latency** | 95th-percentile response time per use case | Langfuse (real-time), Power BI (historical trend) |
| **Cost per use case per day** | Token cost broken out by use case and by model | Power BI on Fabric, cross-checked against Foundry portal cost view |
| **Quality trend** | Evaluation scores over time (groundedness, relevance, task success) | Foundry portal, mirrored in Power BI for cross-use-case comparison |
| **Feedback rate** | Percentage of responses that received any explicit feedback | Power BI on Fabric |
| **Top negative reasons** | Ranked list of thumbs-down reason codes | Power BI on Fabric, drill-through to Langfuse traces |
| **Top intents** | Most common request categories/intents handled | Power BI on Fabric |
| **Drift indicators** | Change in input distribution or quality-score trend versus the evaluation baseline | Foundry portal (evaluation drift), Langfuse (session-level anomalies) |

Power BI on Fabric is the cross-use-case, historical, business-facing layer — this is what a program lead opens once a week. Langfuse is the real-time, engineer-facing layer — this is what someone opens the moment an alert fires. Foundry portal is the evaluation-specific layer — this is where quality trend and drift are analyzed alongside the golden-set scores they are measured against.

## The improvement loop, step by step

1. **Triage** — someone (a rotating on-call role, or a designated quality owner per use case) reviews the negative-feedback and drift signals at least weekly, more often for a new use case in its first month.
2. **Label** — each triaged case gets tagged with a root cause: prompt issue, retrieval miss, wrong tool call, model limitation, or genuinely out-of-scope request.
3. **Add to the golden set** — cases that represent a real, recurring failure mode get anonymized, PII-scrubbed, and added to the relevant `/evals` golden dataset (see doc 05) as a new regression case, so the fix that follows can be proven and future regressions caught automatically.
4. **Fix** — depending on the labeled root cause: edit the prompt, adjust retrieval (better chunking, reranking, a missing document added to the index), fix the agent's tool selection logic, or in some cases decide the request is genuinely out of scope and improve the fallback/escalation message instead.
5. **Eval** — run the fix against the golden set (now including the new regression case) in the normal CI pipeline; it must pass the release gate like any other change.
6. **Ship** — merge, deploy through the normal canary rollout, and monitor the dashboards above for the specific reason code that triggered the fix to confirm it actually dropped.

This loop is what keeps the golden dataset from going stale — it is also the primary source of the "anonymized real traffic" golden-set cases described in doc 05.

## When and how fine-tuning enters

Fine-tuning is the last lever, not the first one. It only gets pulled after prompt engineering and retrieval improvements have plateaued — meaning the improvement loop above has been run several times on the same use case and the quality metrics stop moving, or the remaining failure modes are things a better prompt or better retrieved context structurally cannot fix (e.g., a very specific house style or a domain-specific reasoning pattern that needs many examples to teach).

When that point is reached:

1. **Curate training pairs** — pull human-approved, high-quality response pairs (input plus the accepted/edited output) from the feedback data described above. "Human-approved" means a person confirmed the pair is a good example, not just that no one complained about it.
2. **Scrub PII** — every training pair goes through a personally identifiable information (PII) scrub before it is eligible for fine-tuning; this is a hard gate, not a best-effort step.
3. **Fine-tune** — use Azure OpenAI fine-tuning on a smaller/cheaper base model where possible (fine-tuning a small model to match a larger model's behavior on a narrow task is usually more cost-effective than fine-tuning the large model itself).
4. **Evaluate against the golden set** — the fine-tuned model runs through the exact same evaluation pipeline as any prompt or retrieval change (doc 05); it does not get a different or lighter bar just because it required more engineering effort to produce.
5. **Deploy behind an alias** — the fine-tuned model is registered as a new deployment and reached only through the existing task-alias configuration (see the model management doc); nothing in application code points at the fine-tuned model directly, so it can be rolled back to the previous alias target the same way any other model swap is rolled back.

### Governance of training data

- Every training pair must be traceable back to its source trace id, so if a fine-tuned model produces a bad pattern later, the training example that taught it can be found and removed.
- PII scrubbing is enforced before data enters the fine-tuning dataset, not after — no PII-bearing pair is ever staged for training, even temporarily.
- A designated approver (not the engineer running the fine-tuning job) signs off on the curated dataset before a fine-tuning run starts, matching the same separation-of-duties principle used for golden-set changes.
- Fine-tuning datasets are versioned the same way golden sets are — stored, dated, and retained so a fine-tuned model's behavior can be explained by pointing at exactly what it was trained on.
