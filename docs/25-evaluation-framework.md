# Evaluation Framework

> Internal AFNI reference. Owner: **AFNI · Office of GenAI Architecture** · Internal & confidential.
> Source of truth: `reference/proposal-bible.md` §9, §10 (principle 4: "nothing ships without passing evals"). Numbers marked **(ILLUSTRATIVE)**.

Evaluation is the backbone of the AFNI GenAI framework. Because generative systems are **non-deterministic** — the same input can yield different, plausibly-worded outputs, and a fluent answer can be entirely wrong — traditional pass/fail assertions are insufficient. AFNI therefore treats evaluation as a continuous, multi-layer measurement discipline that spans offline (pre-deployment), online (in-production), and human/red-team review, all wired into a **regression-blocking release gate** and a feedback loop that curates production signal back into golden datasets.

Every evaluation links to the exact execution trace via the framework's **unified OpenTelemetry pipeline in Microsoft Foundry**: each model call, tool invocation, sub-agent hop, and handoff is captured, and a failing score can be opened directly to the trace that produced it. This closes the gap between "the metric dropped" and "here is why."

## 1. Evaluating non-deterministic output

We do not assert exact-match on free text. Instead we combine:

- **Rubric / criteria scoring** — score outputs against explicit, context-aware rubrics (relevance, completeness, tone, correctness). Foundry **auto-generated rubric evaluators** produce these per agent.
- **LLM-as-judge** — a strong model grades candidate outputs against reference answers or rubrics, calibrated against human labels to control judge bias.
- **Reference-based metrics** where ground truth exists (extraction accuracy, classification F1).
- **Statistical treatment** — run each eval case multiple times; track distributions and pass-rates, not single samples, so variance is visible.

## 2. Offline evaluation (pre-deployment)

Run in CI on every PR against a versioned **golden dataset** — curated representative inputs with known-good expectations.

| Metric | Measures | Method | Threshold / gate |
|--------|----------|--------|------------------|
| **Groundedness** | Output supported by retrieved context (anti-hallucination) | Foundry groundedness evaluator | ≥ 0.90 (ILLUSTRATIVE), blocking |
| **Faithfulness** | No claims beyond the evidence; citations resolve | LLM-as-judge vs source | ≥ 0.90 (ILLUSTRATIVE), blocking |
| **Relevance / answer quality** | Response addresses the intent | Auto rubric evaluator | ≥ baseline, no regression |
| **Retrieval quality** | Right chunks retrieved (RAG) | Recall@k / MRR vs labeled set | ≥ target (ILLUSTRATIVE) |
| **Task success** | Agentic goal achieved end-to-end | Scenario suite + tool-call assertions | ≥ 95% (ILLUSTRATIVE) |
| **Extraction accuracy** | Structured field correctness | Reference-based | ≥ target (ILLUSTRATIVE) |

Offline eval is the **prompt-regression baseline**: a candidate is replayed against the golden set and compared to the last-good run so no change silently regresses a previously passing case.

## 3. Online evaluation (in-production)

Offline coverage is finite; production reveals the long tail. On live and mirrored traffic we run:

| Method | Purpose | Notes |
|--------|---------|-------|
| **A/B testing** | Compare candidate vs incumbent on live traffic slices behind APIM | Measure quality + business KPI + cost |
| **Shadow evaluation** | Run candidate on mirrored traffic with no user impact | Safe pre-promotion signal |
| **Guardrail monitors** | Real-time groundedness / safety / PII checks on production output | Feed auto-rollback |
| **Drift detection** | Input-distribution and quality drift vs eval baseline | Triggers re-eval / re-curation |
| **User feedback** | Thumbs up/down, escalation, containment, resolution | Implicit + explicit signal |
| **QA feedback** | Contact-center QA scores, PI Index analytics | SME-graded production sample |

Online metrics reconnect to OpenTelemetry traces so a live guardrail breach is instantly diagnosable.

## 4. Human & red-team evaluation

Automated scoring is calibrated and bounded by human judgment.

- **SME review & calibration** — subject-matter experts grade a sample; their labels calibrate the LLM-as-judge and validate rubrics. Inter-rater agreement is tracked.
- **Adversarial red-team** — structured attempts to break the system: direct and indirect prompt injection, jailbreaks, data-exfiltration, excessive-agency probes, unsafe tool use. Maps to the OWASP Top 10 for LLM Applications (2025).
- **Safety / Content Safety** — Azure AI Content Safety scans (prompt shields, harmful content, PII, protected material) on eval and production traffic.
- **Bias & fairness audits** — disparate-impact and outcome-parity testing, essential for the Hiring Intelligence use case (EEOC / NYC LL144, EU AI Act).

## 5. Metrics per pattern

Evaluation is tuned to the GenAI pattern being deployed:

| Pattern | Primary metrics |
|---------|-----------------|
| Conversational assistant / copilot | Answer quality, groundedness, tone/safety, containment, latency |
| Autonomous / agentic workflow | Task success, correct tool selection, step efficiency, safe-action adherence |
| RAG | Groundedness, faithfulness, retrieval recall@k, citation validity |
| Document intelligence | Extraction accuracy, field-level precision/recall, validation pass-rate |
| Batch summarization & analytics | Faithfulness, coverage, consistency vs QA sample (PI Index) |
| Real-time voice | Turn latency (sub-second), ASR/intent accuracy, groundedness, safety |

## 6. Regression-blocking release gate & feedback

```
 Golden datasets ──▶ Offline eval (CI) ──┐
                                         ├─▶ BLOCKING release gate ──▶ Deploy (canary)
 Rubrics / judge ──▶ Scores + trace link ┘          │  fail = block            │
                                                     ▼                          ▼
 Human/SME + Red-team calibration ◀────────── Online eval (A/B, shadow, monitors)
        │                                                     │
        └──────────── curate failures & edge cases ──────────┘
                             ▼
                    Golden datasets (enriched)
```

The release gate is **blocking**: a candidate that regresses any threshold in §2 or fails §4 safety cannot promote. The loop then **feeds production signal back into the golden datasets** — QA-flagged errors, red-team discoveries, and user-reported failures become new eval cases, so coverage compounds and the framework measures each release against an ever-stronger bar. This is the operational meaning of AFNI design principle 4: *evaluation-driven everything.*
