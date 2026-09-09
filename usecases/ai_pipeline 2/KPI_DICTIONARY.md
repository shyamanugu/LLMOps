# APIX KPI Dictionary

**Purpose.** One authoritative reference for every metric the APIX (AFNI Performance Index) pipeline produces — across all three programs (Telesales, WCC, PSO). For each KPI it records the source schema field, how it is aggregated, its unit, its polarity, its dashboard group, and a **status** flag. This is the sign-off artifact for AFNI SME review and the map of the label space that the golden/evaluation dataset must cover.

> Scope note: this dictionary is generated from the code in `programs_config/<program>/` and `steps/kpi_aggregator.py`. Line references are to those files. It documents behaviour **as coded today**, including known defects (flagged), not the intended spec.

---

## How to read this

### The three metric layers
A prompt change can only move **one** of these. Keeping them separate is what makes evaluation tractable.

| Layer | What it is | Where | How it should be validated |
|---|---|---|---|
| **L1 — Call-level LLM analysis** | Per-call booleans/scores/flags the `analysis` step emits per transcript | `programs_config/<prog>/schemas.py` | **Golden dataset**: transcript + SME-certified expected field values (exact/near match) |
| **L2 — Aggregation math** | The KPIs in this dictionary + the composite scores — deterministic functions of L1 | `programs_config/<prog>/__init__.py`, `steps/kpi_aggregator.py` | **Unit tests** — not golden data |
| **L3 — Aggregate LLM output** | Weekly reflection + coaching recommendations, per employee | `steps/summary.py`, `steps/individual_metrics.py` | **Rubric / LLM-judge** eval, not exact match |
| **SQL — Operational metrics** | AHT, VXS, resolve %, disconnect % etc. | Azure SQL `vzw.rep_pivoted` (see §5) | **Not LLM-produced** — validate the query, golden data does not apply |

**Consequence:** every LLM-derived KPI below (L2) is a deterministic roll-up of L1 fields. Certify L1 + unit-test L2 ⇒ the aggregates are correct by construction. The golden set therefore targets **L1 schema fields**, not the aggregate numbers.

### Status legend
| Flag | Meaning |
|---|---|
| ✅ | Clean — definition, field, and unit are consistent |
| 🐞 | **Code bug** — behaves wrong today; fix in code |
| ❓ | **Needs AFNI/SME confirmation** — definition or data availability is a question for the business |

### Polarity
`↑good` = higher is better · `↓bad` = presence/higher is worse · `denom` = neutral denominator (an "opportunity" count; not good or bad on its own).

### Unit
`count` = absolute number of calls · `pct` = 0–1 fraction. **"Tagged unit"** is what the summary step actually labels it (`count_kpi_keys`); a mismatch vs the true nature is a labelling bug.

---

## 1. Telesales (VZW Telesales) — 12 KPIs
Schema: `SalesAgentEvaluation` · Config: `programs_config/telesales/__init__.py`
✅ **FIXED 2026-09-08:** `count_kpi_keys` is now set → count KPIs are tagged `unit="count"`; the 3 fraction KPIs (`*_opportunity_missed`, `customer_experience`) stay `percent`. *(The "Tagged" column below shows the pre-fix value that was corrected.)*

| # | KPI key | Label | Source field(s) | Aggregation | True unit | Tagged | Polarity | Dashboard group | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `new_line_pitches` | New line Pitches | `pitched_new_line` (filter `new_line_opportunity_exists`) | sum of True | count | pct | ↑good | Sales KPIs | ✅ unit-fixed |
| 2 | `new_line_opportunity_exists` | New line Opportunity Exists | `new_line_opportunity_exists` | sum of True | count | pct | denom | Sales KPIs | ✅ unit-fixed |
| 3 | `new_line_opportunity_missed` | New line Opportunity Missed | `new_line_opportunity_exists` + `pitched_new_line` | custom: `1 − pitched/has` | pct | pct | ↓bad | Sales KPIs | ✅ (see note A) |
| 4 | `upgrade_attempts` | No. of upgrade attempts | `pitched_plan_upgrade` (filter `upgrade_opportunity_exists`) | sum of True | count | pct | ↑good | Sales KPIs | ✅ unit-fixed |
| 5 | `upgrade_opportunity_exists` | Upgrade Opportunity Exists | `upgrade_opportunity_exists` | sum of True | count | pct | denom | Sales KPIs | ✅ unit-fixed |
| 6 | `upgrade_opportunity_missed` | Upgrade Opportunity Missed | `upgrade_opportunity_exists` + `pitched_plan_upgrade` | custom: `1 − pitched/has` | pct | pct | ↓bad | Sales KPIs | ✅ (note A) |
| 7 | `save_attempts` | No. of save attempts | `save_attempt` | sum of True | count | pct | ↑good | Retention & Assurance | ✅ unit-fixed |
| 8 | `escalations` | Escalations | OR(`escalation_due_to_frustration`, `escalation_requested_by_customer`) | custom: count of calls | count | pct | ↓bad | Customer KPIs | ✅ unit-fixed |
| 9 | `fwa_attempts` | FWA attempts | `pitched_fwa` | sum of True | count | pct | ↑good | Customer KPIs | ✅ unit-fixed |
| 10 | `mobile_protection_attempts` | Mobile Protection attempts | `pitched_mobile_protection` | sum of True | count | pct | ↑good | Retention & Assurance | ✅ unit-fixed + note B |
| 11 | `we_got_you_utterances` | "We've got you" utterances | `weve_got_you_statement` (non-null) | custom: count | count | pct | ↑good | Retention & Assurance | ✅ unit-fixed |
| 12 | `customer_experience` | Customer Experience | `customer_experience.rating` | custom: `not-Poor / rated` | pct | pct | ↑good | Customer KPIs | ✅ |

**Notes.**
- **A** — KPIs 3 & 6 recompute the miss-rate from the opportunity/pitch flags and **never read** the LLM's own `new_line_opportunity_missed` / `upgrade_opportunity_missed` booleans (schema fields exist but are dead → two-sources-of-truth risk). ❓ confirm which is authoritative.
- **B** — the downstream composite (`performance_score`) reads a key `mobile_protection`, but this KPI is named `mobile_protection_attempts` → the composite's mobile-protection term is dead. See §6.
- **Inverted schema flags (L1, feeds behavior scores not KPIs):** `objection_handling`, `value_positioning`, `compliance_disclosures` describe False as "behavior *is* performed" — backwards vs siblings and the prompt. 🐞 (`schemas.py:132/133/135`). `clarity` already fixed.

## 2. WCC (Wireless Customer Care) — 11 KPIs
Schema: `WccAgentEvaluation` · Config: `programs_config/wcc/__init__.py`
✅ **FIXED 2026-09-08:** `count_kpi_keys` is now set → count KPIs tagged `unit="count"`; `customer_experience` stays `percent`. Phases: LEARN / PROVIDE / CLOSE. *(The "Tagged" column shows the pre-fix value that was corrected.)*

| # | KPI key | Label | Source field(s) | Aggregation | True unit | Tagged | Polarity | Dashboard group | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `resolution_opportunities` | Resolution Opportunities | `resolution_opportunity_exists` | sum of True | count | pct | denom | WCC Core | ✅ unit-fixed |
| 2 | `resolutions` | Resolutions | `resolution_actual_exists` (filter `resolution_opportunity_exists`) | sum of True | count | pct | ↑good | WCC Core | ✅ unit-fixed |
| 3 | `survival_opportunities` | Survival Opportunities | `survival_rate_opportunity_exists` | sum of True | count | pct | denom¹ | WCC Core | ✅ unit-fixed + ❓ |
| 4 | `saves` | Saves | `survival_rate_actual_exists` (filter opp) | sum of True | count | pct | ↑good | WCC Core | ✅ unit-fixed |
| 5 | `right_of_sell_opportunities` | Right of Sell Opportunities | `right_of_sell_opportunity_exists` | sum of True | count | pct | denom | WCC Core | ✅ unit-fixed |
| 6 | `right_of_sell_actuals` | Right of Sell Actuals | `right_of_sell_actual_exists` (filter opp) | sum of True | count | pct | ↑good | WCC Core | ✅ unit-fixed |
| 7 | `sales_made` | Sales Made | `sale_made` | sum of True | count | pct | ↑good | WCC Core | 🐞 **field never prompted** |
| 8 | `new_prospects` | New Prospects | `new_prospect` | sum of True | count | pct | denom | WCC Core | ✅ unit-fixed |
| 9 | `new_prospects_converted` | New Prospects Converted | `new_prospect_converted` | sum of True | count | pct | ↑good | WCC Core | 🐞 **field never prompted** |
| 10 | `escalations` | Escalations | OR(escalation cols) | custom: count | count | pct | ↓bad | Customer KPIs | ✅ unit-fixed |
| 11 | `customer_experience` | Customer Experience | `customer_experience.rating` | custom: not-Poor/rated | pct | pct | ↑good | Customer KPIs | ✅ |

¹ `survival_rate_opportunity_exists` counts churn-risk presence — a high "opportunity" value means *more at-risk customers*, which reads as positive in a KPI list. ❓ confirm intended interpretation.

**WCC-specific defects (beyond the table):**
- 🐞 **Analysis prompt requests 8 fields the schema rejects** (`coaching_tip`, `sales_tip`, `other_feedback`, `call_importance`, `save_attempt`, `weve_got_you_statement`, new-prospect `confidence`, `UNKNOWN` state). All generated then dropped → wasted tokens, **no coaching output stored**.
- 🐞 KPIs 7 & 9 are backed by fields (`sale_made`, `new_prospect_converted`) the **prompt never asks the model to produce** → unreliable.
- 🐞 **Reflection prompt is the Telesales prompt verbatim** and is handed the *Telesales* schema — WCC's Resolution/Survival/Right-of-Sell metrics are invisible to reflection (L3).
- ❓ Docstrings disagree on what "WCC" stands for (`schemas.py` "Whole Call Coaching" vs `__init__.py` "Wireless Customer Care").

## 3. PSO (VZ Mobile Service) — 24 KPIs
Schema: `PsoAgentEvaluation` · Config: `programs_config/pso/__init__.py:102-168`
**`count_kpi_keys` IS set** → PSO units are correct. Most metric-dense program. 22 bool KPIs (built from `BOOL_KPI_COLUMNS`) + `escalations` + `customer_experience`.

> ⚠️ **KPI key ≠ schema field** in 3 rows (intentional indirection): `next_steps_clarity`→`next_steps_communication`, `escalation_handling`→`escalation_necessity`, `aht_efficiency`→`aht_assessment`. Consistent internally but fragile.

| KPI key | Label | Schema field | Unit | Polarity | Dashboard group | Status |
|---|---|---|---|---|---|---|
| `predicted_csat` | Predicted CSAT | `predicted_csat` | pct | ↑good | PSO Customer Experience | ✅ |
| `customer_confidence` | Customer Confidence | `customer_confidence` | pct | ↑good | PSO Customer Experience | ✅ |
| `customer_effort` | Customer Effort (Ease) | `customer_effort` | pct | ↑good² | PSO Customer Experience | ✅ |
| `fcr_likelihood` | FCR Likelihood | `fcr_likelihood` | pct | ↑good | PSO Resolve | ✅ |
| `resolution_completeness` | Resolution Completeness | `resolution_completeness` | pct | ↑good | PSO Resolve | ✅ |
| `resolution_confidence` | Resolution Confidence | `resolution_confidence` | pct | ↑good | PSO Resolve | ✅ |
| `next_steps_clarity` | Next Steps Communication | `next_steps_communication` | pct | ↑good | PSO Resolve | ✅ key≠field |
| `issue_resolution_effectiveness` | Issue Resolution Effectiveness | `issue_resolution_effectiveness` | pct | ↑good | PSO Resolve | ✅ |
| `quality` | Quality Score | `quality` | pct | ↑good | PSO Quality | ✅ |
| `compliance` | Compliance Score | `compliance` | pct | ↑good | PSO Quality | ✅ |
| `process_adherence` | Process Adherence | `process_adherence` | pct | ↑good | PSO Quality | ✅ |
| `issue_ownership` | Issue Ownership Effectiveness | `issue_ownership` | pct | ↑good | PSO Customer Care Handling | ✅ |
| `escalation_handling` | Escalation Necessity | `escalation_necessity` | pct | ❓ ambiguous³ | PSO Customer Care Handling | ❓ key≠field |
| `transfer_avoidance` | Transfer Avoidance | `transfer_avoidance` | pct | ↑good | PSO Customer Care Handling | ✅ |
| `case_management` | Case Management Effectiveness | `case_management` | pct | ↑good | PSO Customer Care Handling | ✅ |
| `aht_efficiency` | AHT Assessment | `aht_assessment` | pct | ↑good | PSO Operational Efficiency | ✅ key≠field |
| `contact_handling_efficiency` | Contact Handling Efficiency | `contact_handling_efficiency` | pct | ↑good | PSO Operational Efficiency | ✅ |
| `hold_management` | Hold Management Effectiveness | `hold_management` | pct | ↑good | PSO Operational Efficiency | ✅ |
| `repeat_contact_risk` | Repeat Contact Risk | `repeat_contact_risk` | count | ↓bad | PSO Repeat Contact Risk | ✅ |
| `escalation_risk` | Escalation Risk | `escalation_risk` | count | ↓bad | PSO Repeat Contact Risk | ✅ |
| `callback_risk` | Callback Risk | `callback_risk` | count | ↓bad | PSO Repeat Contact Risk | ✅ |
| `reopen_risk` | Reopen Risk | `reopen_risk` | count | ↓bad | PSO Repeat Contact Risk | ✅ |
| `escalations` | Escalations | OR(escalation cols) | count | ↓bad | Customer KPIs | ✅ |
| `customer_experience` | Customer Experience | `customer_experience.rating` | pct | ↑good | Customer KPIs | ✅ |

² CES is conventionally lower-is-better; the field is defined as "True = low-effort/easy = good", so it resolves correctly. ³ `escalation_necessity` (True = escalation legitimately required) sits in a "True=good" group but a higher value has ambiguous business meaning. ❓
- ❓ Schema fields with **no KPI consumer**: `issue_resolved` (a direct resolution bool — unmeasured), plus vestigial sales fields `sale_made`/`new_prospect`/`new_prospect_converted` on a care program.
- 🐞 minor: expand rule references `escalation.explanation` which doesn't exist (field is `escalation_reason`) — no-op copy-paste.

---

## 4. Behaviour scores & soft skills (L1 → behaviour block, not KPIs)
Aggregated as `mean` of per-call booleans → 0–1. Reported under `behavior_scores` / soft skills, separate from the KPI list above.

| Program | Behaviour scores | Optional/count behaviours | Soft skills (shared) |
|---|---|---|---|
| Telesales | 10 (`active_listening`…`professional_tone`) | 4 (`objection_handling`, `value_positioning`, `assumptive_close`, `compliance_disclosures`) — 3 inverted 🐞 | 6 (`comprehension`…`subject_matter_expertise`) |
| WCC | 0 | 15 `wcc_*` LEARN/PROVIDE/CLOSE behaviours | 6 (shared) |
| PSO | 13 (Communication/Care/Problem-Solving/Resolution/Ops) | 0 | 6 (shared) |

## 5. SQL operational coaching metrics — **not LLM-produced**
Source: Azure SQL `vzw.rep_pivoted` via `steps/individual_metrics.py`. Config: `base/config.py:170-217`. **All three programs inherit the same base groups** (none define their own).

| Group | MetricDesc keys |
|---|---|
| Resolve | 2-Hour / 3-Day / 30-Day Resolve; 3 / 30 / 90 Day Contact Disconnect % |
| Efficiency | Agent AHT, Agent Outbound AHT, Avg Response Time, Agent Calls, AFRRT |
| Quality | VXS Overall Rep, Thumbs Up %, Thumbs Down % |

- These feed the L3 coaching prompt as current-vs-previous-window deltas. **Golden data does not apply** — validate the SQL/query, not a prompt.
- ❓ **AFNI confirmation needed:** do these VZW `MetricDesc` rows exist for WCC (loyalty) and PSO (VZ Mobile) employees? If not, the coaching step returns nothing for those programs and needs program-specific metric groups.

## 6. Composite / computed scores — `steps/kpi_aggregator.py`
Computed downstream over the per-employee KPI list; written into the CSV under group **"Computed Scores"**.

| Key | Definition | Status |
|---|---|---|
| `performance_score` | VXS 40% + Sales 30% + Trend 20% + Quality 10% (`kpi_aggregator.py:241-307`) | 🐞 **broken for all programs** — see below |
| `risk_count` | thresholds on vxs/escalations/new_line_pitches/mobile_protection | 🐞 sales-only keys |
| `overall_behavior_score` | mean of behaviour+soft-skill scores × 100 | ✅ |
| `strong_behavior_count` / `focus_behavior_count` | # behaviours >0.5 / ≤0.5 | ✅ |
| `status_label` | Strong ≥80 / Developing ≥70 / Focus (from `performance_score`) | 🐞 inherits the broken score |

🐞 **`performance_score` defect (high severity):**
- `vxs`/`vxs_solutions` is **never emitted as a KPI by any program** (VXS is only an SQL metric, §5) → the 40% term is dead everywhere.
- reads `mobile_protection` but the KPI is `mobile_protection_attempts` → sales term half-dead even for Telesales.
- WCC/PSO have **zero** sales keys → the score collapses to `trend + a flat 100 quality baseline`, and `status_label` then labels those agents Strong/Developing/Focus off a meaningless number.
- *High confidence from static analysis; confirm against one real report JSON before fixing.*

---

## 7. Consolidated open questions for AFNI / SMEs (the ❓ items)
Bring these — not basic KPI definitions — to the business/SME sessions.

1. **Telesales inverted flags** — confirm `objection_handling` / `value_positioning` / `compliance_disclosures` should be True-when-performed (i.e. the schema text is wrong). *(§1)*
2. **Miss-rate source of truth** — should `*_opportunity_missed` use the LLM's own bool or the computed rate? *(§1 note A)*
3. **WCC `sales_made` / `new_prospects_converted`** — are these KPIs actually required for a care program? If yes, the prompt must be extended to produce them. *(§2)*
4. **Survival "opportunity" semantics** — is a higher survival-opportunity count good or a churn-risk warning? *(§2)*
5. **PSO `escalation_necessity`** — define whether higher is good, bad, or neutral. *(§3)*
6. **SQL metrics coverage** — do the `rep_pivoted` Resolve/Efficiency/Quality metrics exist for WCC & PSO employees? *(§5)*
7. **Is `performance_score` used by the business at all?** If it drives coaching/ranking, it must be re-specified per program; if not, it can be removed. *(§6)*
8. **Target ranges** — per KPI, what value is "good"? (thresholds, not definitions) — needed for the evaluation gate.

## 8. Fix backlog (code — no business input needed)
| Item | Where | Severity |
|---|---|---|
| ~~Set `count_kpi_keys` for Telesales & WCC (fix unit mislabelling)~~ **✅ DONE 2026-09-08** | `telesales/__init__.py`, `wcc/__init__.py` | ~~High~~ |
| Re-spec or remove `performance_score`/`risk_count`/`status_label` composite | `kpi_aggregator.py:241-336` | High |
| WCC: prune analysis prompt to schema fields; give WCC its own care reflection prompt | `wcc/prompts.py` | High |
| Telesales: correct 3 inverted flag descriptions (pending Q1) | `telesales/schemas.py:132-135` | Med |
| PSO: fix `escalation.explanation` expand rule → `escalation_reason` | `pso/__init__.py:244` | Low |

---
*Generated as a definitional audit of the APIX pipeline configs. Update this file when KPI definitions change — it is the source of truth for the evaluation/golden dataset scope.*
