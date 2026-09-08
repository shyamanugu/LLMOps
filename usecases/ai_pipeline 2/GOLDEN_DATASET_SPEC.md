# Apex Golden Dataset — Construction Spec

**Purpose.** Define how Apex golden/ground-truth data is constructed for the LLMOps evaluation gate: what qualifies as golden, at what granularity, how it is certified by the business, and what the evaluation actually measures. This is the answer to the open dependency raised in the client review ("golden data is a foundational dependency requiring a more rigorous, use-case-specific approach").

Companion doc: **`KPI_DICTIONARY.md`** — the authoritative list of every metric, which defines the label space this dataset must cover.

---

## 1. The problem, stated precisely
Apex KPIs are **aggregated across many calls over a period** (e.g. resolution rate, AHT, VXS). A naive golden recipe of *"one transcript → one expected KPI value"* cannot validate an aggregate metric, and it was never defined *why* some transcripts qualify as golden and others don't. This spec resolves both by separating what a prompt can actually change from what it cannot.

## 2. The three layers (a prompt change moves only one)
| Layer | What it is | Certifiable unit | Validation method |
|---|---|---|---|
| **L1 — Call-level analysis** | Per-call fields the `analysis` step emits per transcript (booleans, ratings, scores, evidence) | **1 transcript → its expected field values** | **Golden dataset** — exact/near match vs SME labels |
| **L2 — Aggregation math** | The KPIs in the CSV (sums, fractions, composites) — deterministic functions of L1 | none (no LLM) | **Unit tests** on fixture inputs |
| **L3 — Aggregate LLM output** | Weekly reflection + coaching recommendations per employee | employee-week rubric | **Rubric / LLM-judge** scoring |
| **SQL — Operational metrics** | AHT, VXS, resolve %, disconnect % | none (from `vzw.rep_pivoted`) | **Query validation**, not golden data |

**Central principle:** every LLM-derived aggregate KPI is a deterministic roll-up of L1 fields. **Certify L1 + unit-test L2 ⇒ the aggregates are correct by construction.** Therefore the golden dataset targets **L1**, not the aggregate numbers. The operational metrics (AHT/VXS/resolution rate) are **not LLM outputs at all** — they come from Verizon's data warehouse, so "golden data" does not apply; we validate the SQL.

> This is the answer to "how do we validate aggregate KPIs": you don't validate them as prompt outputs, because they are either (a) deterministic math over certified call-level labels, or (b) external SQL metrics.

## 3. What "golden" means at each layer

### L1 — the core golden set
A golden record = **one transcript + the business-certified expected value for each analysis field** it exercises, drawn from the program's schema (see `KPI_DICTIONARY.md §1–3`). Fields group into:
- **Detection booleans** (e.g. `pitched_new_line`, `resolution_actual_exists`, `escalation_*`) → expected `true/false` + the segment IDs that justify it.
- **Ratings/enums** (e.g. `customer_experience.rating`, `sales_outcome.outcome`) → expected class.
- **Behaviour flags & soft skills** → expected `true/false`.
- **Scores** (`customer_frustration_*`, `call_importance`) → expected value or tolerance band.

Certification is per-field, not per-call-as-a-whole: a call can be "golden" for escalation detection even if its coaching tip is subjective.

### L2 — no golden data; fixtures
Hand-built fixture sets of call-level rows with known aggregate answers (e.g. "10 calls, 4 with a pitched new line and an opportunity ⇒ `new_line_pitches = 4`, `new_line_opportunity_missed = 0.6`"). These are unit tests, authored by engineering, no SME needed.

### L3 — rubric ground truth
For reflection/coaching, exact match is wrong (many good phrasings exist). Ground truth = an **SME-authored rubric** (e.g. "cites a real metric from the data; is specific & actionable; no invented metrics; correct domain — care vs sales") scored by a judge (SME spot-check or LLM-judge calibrated to SME).

## 4. Qualification criteria — why a record is golden
A transcript qualifies **not at random** but by **stratified coverage of the label space** plus reviewer agreement:

1. **Coverage** — the set must include, per program, calls that exercise each decision: with/without each opportunity type; each `customer_experience` rating (Good/Medium/Poor); escalation vs none; sale vs no sale; each phase behaviour present/absent; and edge cases (dropped call, transfer, ambiguous intent, non-target language).
2. **Balance** — enough positive AND negative examples per field to measure precision *and* recall (rare-positive fields like escalations need deliberate over-sampling).
3. **Reviewer agreement** — each record labelled by ≥2 coaches/SMEs; keep only where they agree (or a third breaks ties). Inter-rater agreement (Cohen's κ) is itself a signal: low κ on a field means the *definition* is unclear and must be fixed before it can be golden.
4. **Provenance** — real production transcripts, PII handled per the guardrail policy, frozen with a version + certifier + date.

## 5. Construction workflow
```
 sample (stratified) ─▶ model pre-label ─▶ SME review & correct ─▶ adjudicate (≥2 agree)
        │                                                                  │
   from label-space                                             version + freeze
   coverage matrix                                              store in prompt/eval registry
```
1. **Sample** production transcripts against the coverage matrix (§4.1), per program.
2. **Pre-label** by running the current analysis step → gives reviewers a starting point (accept/correct, faster than labelling blank).
3. **SME review** — coaches correct field values + confirm segment-ID evidence.
4. **Adjudicate** — keep records with ≥2-reviewer agreement; log κ per field.
5. **Freeze** — store transcript + certified labels as an immutable golden version (feeds the playground's "golden dataset" selector shown in the demo).
6. **Grow via feedback loop** — when production feedback (coach 1–5 ratings) exposes an uncovered scenario, add it to the coverage matrix and repeat.

## 6. Sizing & stratification (starting proposal)
Per program, an initial **150–250 certified transcripts**, allocated by the coverage matrix rather than evenly — heavier on rare-but-critical fields (escalations, saves, Poor CX). Rationale mirrors the prior chatbot effort (≈500 questions → SME-validated in cycles); start smaller per program because Apex fields are more constrained than open-domain Q&A. Exact N per field is set once the coverage matrix is filled from `KPI_DICTIONARY.md`.

## 7. What the evaluation gate reports (per prompt/model version)
- **L1 quality:** per-field precision / recall / F1 vs golden (detection booleans), accuracy (enums), MAE (scores) — plus token usage, cost, latency (already in the playground). Threshold-gated: below target ⇒ reject the prompt+model before deploy.
- **L2:** unit-test pass/fail (CI, not the gate).
- **L3:** rubric score distribution + % flagged by judge.

## 8. What we need from the business / SMEs
Bring these — not basic KPI definitions (do the homework first via the existing Apex SMEs). See `KPI_DICTIONARY.md §7` for the full list; the golden-data-specific asks:
1. **Certify labels** on the stratified transcript sample (the actual golden-set creation).
2. **Confirm field definitions** where inter-rater κ is low (definitions are ambiguous → fix before golden).
3. **Author the L3 coaching rubric** (what makes a coaching recommendation good).
4. **Set per-field/per-KPI thresholds** for the gate (what score is acceptable).
5. **Resolve the dictionary's open questions** (inverted flags, survival-opportunity polarity, `escalation_necessity`, WCC sales KPIs).

## 9. Open decisions
- Registry location for golden sets (Azure prompt-set mgmt vs DB vs blob) — currently app cache; long-term TBD (raised in the review).
- Whether L1 certification is done in the playground UI or an offline labelling tool.
- Cadence for refreshing golden sets as prompts/programs evolve.

---
*This spec targets L1 as the golden ground truth, treats aggregates as deterministic (L2) or external (SQL), and rubric-scores L3. It converts "define golden data" from an open-ended business ask into a bounded, coverage-driven labelling task.*
