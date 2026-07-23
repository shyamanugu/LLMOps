# Performance Intelligence Index (PI Index)

> **Confidential — AFNI, Inc. Internal.** Prepared by the AFNI Office of GenAI Architecture.
> All metrics in this document are **ILLUSTRATIVE placeholders** pending discovery with AFNI actuals.
> **Naming note:** "**PI Index**" is a performance metric. It is **never** to be confused or abbreviated as "PII" (Personally Identifiable Information / personal data). They are unrelated concepts.

## What the PI Index Is

The **AFNI Performance Intelligence Index (PI Index)** is an AI-generated, **explainable composite performance score** computed from **100% of interactions** — not from the 2–10% sample that traditional QA reviews. A multi-agent pipeline analyzes every voice and chat interaction across seven dimensions, then **rolls those dimension scores up into a single, calibrated index** per **agent, team, program, and client**.

The PI Index replaces subjective, low-coverage, slow QA with objective, consistent, and fully explainable scoring at full coverage — and it does so on data the **Voice Agent** already produces (Mode C post-call analytics).

```
   100% of interactions            Seven analysis agents            Roll-up
  (voice + chat + data)         (each scores one dimension)      (one index)
        |                                  |                          |
        v                                  v                          v
  +-----------+     +-----------------------------------+     +---------------+
  | Transcripts|    | 1 Compliance adherence            |     |  PI INDEX     |
  | Chat logs  |--> | 2 Communication & empathy         |--> |  per agent /  |
  | Disposit'ns|    | 3 Resolution / FCR                |     |  team /       |
  | CRM outcome|    | 4 Script & process adherence      |     |  program /    |
  | QA metadata|    | 5 Sentiment trajectory            |     |  client       |
  +-----------+     | 6 Efficiency (AHT/silence/holds)  |     +-------+-------+
                    | 7 Business outcome                |             |
                    +-----------------------------------+             v
                        weighted · calibrated · explainable    coaching · QA
                                                               · Gainshare · alerts
```

---

## The Seven Analysis Dimensions (Each an Agent)

| # | Dimension | What the agent measures | Example signals |
|---|---|---|---|
| 1 | **Compliance adherence** | Required disclosures, consent, PCI/HIPAA/TCPA handling | Mini-Miranda, recording notice, no prohibited language |
| 2 | **Communication & empathy** | Clarity, tone, active listening, acknowledgment | Empathy statements, interruptions, jargon |
| 3 | **Resolution / FCR** | Whether the customer's need was resolved first time | Repeat-contact risk, unresolved intents |
| 4 | **Script & process adherence** | Following approved flow and business rules | Verification steps, required offers, correct pathing |
| 5 | **Sentiment trajectory** | Direction of customer sentiment across the call | Start-to-end delta, recovery after friction |
| 6 | **Efficiency (AHT)** | Handle time, dead air, holds, after-call work | Silence %, hold count, ACW time |
| 7 | **Business outcome** | Sale, promise-to-pay, retention, save | Disposition, CRM outcome, conversion |

### How the Dimensions Roll Up

- **Weighted.** Each dimension carries a configurable weight per program and client (a collections program weights business outcome and compliance differently than a care program). Weights are governed and versioned.
- **Calibrated.** Raw agent scores are calibrated against human-reviewed anchors so the index is stable and comparable across programs and over time.
- **Explainable.** The final index always ships with a **driver breakdown** — which dimensions raised or lowered the score, with evidence (transcript spans) — so no score is a black box.

The result is **one index** at each level of the hierarchy: agent → team → program → client, with trends and comparisons.

---

## Data Sources

- **Voice transcripts** from the **Voice Agent** (Mode C post-call analytics; batch and near-real-time).
- **Chat transcripts** from digital channels.
- **Dispositions** and agent wrap-up codes.
- **CRM outcomes** (sale, payment, retention, resolution status).
- **QA metadata** (human-review anchors used for calibration and appeals).

All sources pass through **PII detection and redaction** (Microsoft Purview + Content Safety) before scoring and storage. The PI Index store lives in **Microsoft Fabric / Data Lake**.

---

## The Multi-Agent Scoring Pipeline

```
+-------------------+     +------------------+     +-----------------------+
| INGEST & PREP     |     | REDACTION/PII    |     | ORCHESTRATOR          |
| transcripts, chat |---> | Purview +        |---> | fan-out to 7 analysis |
| dispositions, CRM |     | Content Safety   |     | agents (concurrent)   |
+-------------------+     +------------------+     +-----------+-----------+
                                                              |
        +-----------------------------------------------------+
        v
+-------------------+     +------------------+     +-----------------------+
| 7 DIMENSION AGENTS|---> | WEIGHTING &      |---> | CALIBRATION vs human  |
| score + evidence  |     | ROLL-UP          |     | anchors (reflection)  |
+-------------------+     +------------------+     +-----------+-----------+
                                                              |
        +-----------------------------------------------------+
        v
+-------------------+     +------------------+     +-----------------------+
| EXPLAINABILITY    |---> | PI INDEX STORE   |---> | OUTPUTS: coaching, QA |
| driver breakdown  |     | (Fabric/Lake)    |     | Gainshare, alerts     |
+-------------------+     +------------------+     +-----------------------+
```

The pipeline uses the shared multi-agent pattern: an **Orchestrator/Supervisor** fans out to the seven concurrent **analysis agents**, a **reflection/critic** step calibrates against human anchors, and **deterministic guardrails** wrap every model call. Orchestration runs on Azure AI Agent Service (Semantic Kernel / AutoGen → Microsoft Agent Framework); scoring uses Azure OpenAI (GPT-4o / GPT-4o-mini) with cost tiers via APIM.

---

## Outputs

- **Coaching recommendations.** Targeted, per-agent guidance tied to the specific dimensions and transcript evidence that moved the index — turning scores into next actions.
- **QA calibration.** 100% coverage plus human-anchored calibration lets QA teams focus on edge cases and audits rather than sampling.
- **Gainshare / performance reporting.** Objective, consistent index feeds AFNI's partnership/Gainshare commercial model and client-facing performance reviews.
- **Anomaly / risk alerts.** Early detection of compliance risk, sentiment collapse, or outcome drift at agent, team, or program level.

---

## Governance and Responsible AI

- **Score explainability.** No score without a driver breakdown and transcript evidence; every index is inspectable.
- **Fairness across agents and sites.** Continuous monitoring for systematic bias by site, shift, tenure, or demographic proxy; scores are validated to reflect performance, not population.
- **Human calibration & appeals.** Agents and supervisors can **appeal** a score; human reviewers adjudicate, and outcomes feed back into calibration. Humans remain accountable for consequential people decisions.
- **Model cards.** Each scoring model and dimension agent has a documented model/system card (purpose, data, limits, evaluation).
- **Audit trails & lineage.** Purview lineage from source interaction to final index; full audit history.
- **PII discipline.** Redaction before scoring; and the **"PI Index" ≠ "PII"** naming rule is enforced in all documentation and dashboards to prevent confusion with personal data.

---

## KPI / Impact Table (ILLUSTRATIVE)

| Metric | Baseline (illustrative) | With PI Index (illustrative) |
|---|---|---|
| QA coverage | 5–10% (sampled) | **100%** of interactions |
| Coaching cycle time | Days–weeks | Near-real-time / same-day |
| Coaching precision (evidence-linked) | Low / subjective | High / transcript-anchored |
| Compliance-risk lead time | Reactive | Proactive alerts |
| Agent attrition (via better coaching) | — | −10–20% |
| QA calibration effort | High manual | Human focuses on edge cases |

---

## Pilot Scope

1. **Foundations (Weeks 0–4).** Data access to historical interactions, PII redaction, dimension definitions and weights, human-anchor set for calibration, model cards, appeals process design.
2. **Crawl — score history first (Months 1–3).** Run the pipeline **offline on historical interactions** for **one program**; validate dimension scores against human QA anchors; publish the first explainable PI Index with driver breakdowns.
3. **Walk — near-real-time (Months 4–7).** Move to **near-real-time scoring** of live Voice Agent and chat interactions; wire coaching workflows, QA calibration, anomaly alerts, and Gainshare reporting; stand up the appeals loop.
4. **Run (Months 8–12).** Scale across programs, geographies, and clients; continuous fairness reporting into the AFNI GenAI governance board.

**Pilot success criteria (illustrative):** PI Index correlates with human QA anchors within an agreed tolerance; 100% coverage achieved on the pilot program; coaching cycle time reduced; at least one measurable compliance or outcome risk surfaced earlier than the prior sampled process.

---

## Synergy Across the Three Initiatives

- **← Voice Agent:** supplies the transcripts and signals (Mode C) that make 100% scoring possible.
- **↔ Hiring Intelligence:** shares the multi-agent scoring, explainability, calibration, and fairness-monitoring patterns.

The PI Index is the layer that turns AFNI's interaction data into performance intelligence — built once on the shared platform and reused everywhere.
