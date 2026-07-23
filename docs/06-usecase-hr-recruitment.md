# Hiring Intelligence

> **Confidential — AFNI, Inc. Internal.** Prepared by the AFNI Office of GenAI Architecture.
> All metrics in this document are **ILLUSTRATIVE placeholders** pending discovery with AFNI actuals.

## Overview

**Hiring Intelligence** is AFNI's AI-driven, fair, high-volume recruitment capability for AFNI's own contact-center hiring across the US, Mexico, and the Philippines. It is one of AFNI's three flagship LLMOps initiatives. It applies the same multi-agent platform used by the **Voice Agent** and the **Performance Intelligence Index (PI Index)** — and reuses the Voice Agent speech stack for optional candidate voice pre-screens.

The governing principle is non-negotiable and appears at every stage of this document:

> **AI assists, humans decide. There is no autonomous rejection.** Every consequential decision — advance, decline, offer — is made by a human recruiter or hiring manager. Agents rank, summarize, draft, and surface signals; they never auto-reject a candidate.

---

## Candidate Journey — An Agent at Each Stage

```
   SOURCING            SCREENING             SELECTION           DECISION
      |                    |                     |                  |
 +----v----+   +----------v---------+   +--------v-------+   +------v------+
 |   JD    |   | Résumé Ranking     |   | Structured     |   |  Human      |
 | Gen     |-->| (assist, not auto) |-->| Interview      |-->|  Recruiter/ |
 | Agent   |   |  + Conversational  |   | Scoring ASSIST |   |  Manager    |
 +---------+   |  Screening         |   +----------------+   |  DECIDES    |
              |  (chat / opt. voice)|   | Candidate Fit  |   +-------------+
              +----------+----------+   | signal         |         ^
                         |              +----------------+         |
                    +----v-----+                                   |
                    |Scheduling|-----------------------------------+
                    |  Agent   |
                    +----------+
   ================ FAIRNESS / ADVERSE-IMPACT MONITOR (continuous) ==========
```

Every stage is wrapped by a **continuous fairness / adverse-impact monitor** and the shared **Compliance/Guardrail** agent.

### 1. JD Generation Agent
Drafts inclusive, bias-checked job descriptions from role templates and hiring-manager inputs; flags exclusionary or non-essential requirements. **Assist only** — recruiters review and approve.

### 2. Sourcing & Résumé Ranking Agent
Ranks and summarizes inbound applicants against **job-related** criteria, with an explainable rationale per candidate. Produces a **ranked shortlist, not a decision** — recruiters see why each candidate ranked where they did and can override.

### 3. Conversational Screening Agent (chat + optional voice pre-screen)
Conducts structured, consistent pre-screens (availability, eligibility, role-fit questions) via chat, or via an **optional voice pre-screen that reuses the Voice Agent platform** (gpt-realtime + Azure AI Speech). Candidates are told they are interacting with an AI assistant and may request a human.

### 4. Scheduling Agent
Coordinates interview slots across recruiters, hiring managers, and candidates; handles reminders, reschedules, and time-zone logic across geographies.

### 5. Structured Interview Scoring — ASSIST
Provides interviewers a **structured rubric and note-taking aid**, and drafts summary scores against defined competencies. **The interviewer owns the score;** the agent never finalizes an outcome.

### 6. Candidate Fit Signal
A composite, explainable **signal** (not a verdict) summarizing job-related fit to help recruiters prioritize. Every Fit signal ships with its contributing factors so a human can inspect and challenge it.

### 7. Fairness / Adverse-Impact Monitor
Continuously measures selection rates and outcomes across protected groups and sites, computes adverse-impact ratios, and alerts governance to drift — feeding the required bias audits.

---

## Responsible AI and Fairness (Critical)

Hiring is a **high-risk** use of AI and is governed accordingly. This capability is designed to the following, at minimum:

- **AI assists, humans decide — no autonomous rejection.** Hard platform constraint, not a policy footnote.
- **EEOC / Uniform Guidelines** — job-relatedness and validation; monitoring for adverse impact (four-fifths rule).
- **NYC Local Law 144** — independent **bias audit** of automated employment decision tools (AEDTs), published results, and candidate notice before use.
- **Illinois AI Video Interview Act** — notice, consent, explanation of how AI evaluates video interviews, and deletion on request. (Relevant to AFNI's IL footprint.)
- **EU AI Act** — employment/recruitment is classified **high-risk**; requires risk management, human oversight, logging, transparency, and conformity practices.
- **GDPR** (and equivalent) — lawful basis, data minimization, candidate access/erasure rights, and safeguards against solely automated decisions with legal/significant effect (Art. 22).
- **Notice & consent** — candidates are informed when AI is used, what it assesses, and how to request human review or an accommodation.
- **Explainability** — every ranking, Fit signal, and score carries a human-readable rationale and contributing factors.
- **Bias audits & model cards** — periodic third-party-style audits, documented model/system cards, and versioned evaluation on fairness golden sets.

Deterministic guardrails (Content Safety, PII detection/redaction via Purview, protected-attribute exclusion from scoring features) wrap every probabilistic agent.

---

## KPI Table (ILLUSTRATIVE)

| KPI | Baseline (illustrative) | Target (illustrative) |
|---|---|---|
| Time-to-fill | — | −25–40% |
| Cost-per-hire | — | −15–30% |
| Funnel conversion (apply → hire) | — | +10–20% |
| Recruiter screening hours saved | — | −30–50% |
| Candidate NPS | — | +10–20 pts |
| Offer-accept rate | — | +5–10 pts |
| 90-day attrition | — | −10–20% |
| Adverse-impact ratio (all protected groups) | — | ≥ 0.80 (monitored) |

---

## Integration (ATS / HRIS)

Hiring Intelligence is an **assist layer over AFNI's existing recruiting stack**, not a replacement:

- **ATS** (e.g., Workday Recruiting, iCIMS, Greenhouse, or incumbent) — read applicants and requisitions; write back rankings, notes, Fit signals, and structured scores as **decision support**. Humans action all status changes in the ATS.
- **HRIS** — role templates, headcount, location, and onboarding handoff.
- **Integration layer** — Azure API Management + Functions/Logic Apps; connectors kept **generic** so the ATS/HRIS remains swappable.
- **Voice pre-screen** — reuses the Voice Agent (gpt-realtime + Azure AI Speech + telephony/ACS), avoiding a duplicate speech build.
- **Data & governance** — Microsoft Purview for lineage and PII controls; Entra ID for identity; audit trails on every agent action.

---

## Implementation Approach and Pilot Scope

1. **Foundations (Weeks 0–4).** Use-case risk-tiering (high-risk), ATS/HRIS connectors, fairness golden sets, candidate notice/consent flows, bias-audit plan, model cards.
2. **Crawl pilot (Months 1–3).** **Chat-based conversational screening + résumé-ranking assist** for **one high-volume role in one geography**; recruiters retain all decisions; fairness monitor live from day one.
3. **Walk (Months 4–7).** Add **optional voice pre-screen** (Voice Agent reuse), **scheduling**, and **structured interview-scoring assist**; run the first formal **bias audit** (NYC LL144-style) before broader use.
4. **Run (Months 8–12).** Scale across roles and geographies (US/Mexico/Philippines) with jurisdiction-specific notice/consent and audits; embed continuous fairness reporting into the governance board cadence.

**Pilot success criteria (illustrative):** recruiter screening hours reduced on the pilot role; time-to-fill improvement; candidate NPS lift; **zero autonomous rejections**; adverse-impact ratio ≥ 0.80 across monitored groups with documented audit.

---

## Synergy Across the Three Initiatives

- **← Voice Agent:** reuses the speech-to-speech stack for candidate voice pre-screens.
- **↔ PI Index:** shares the same multi-agent scoring, explainability, and fairness-monitoring patterns; lessons on calibration and appeals transfer directly.

One platform, one multi-agent pattern — AFNI builds it once and reuses it to hire, automate, and measure its workforce.
