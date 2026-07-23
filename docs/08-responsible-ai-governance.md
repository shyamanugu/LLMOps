# Responsible AI & Governance

## Purpose

Responsible AI (RAI) is not a compliance afterthought bolted onto AFNI's GenAI platform — it is the operating discipline that lets AFNI deploy probabilistic agents into regulated, consequential workflows with confidence. This document translates Microsoft's Responsible AI framework into concrete controls for AFNI's three flagship initiatives — the **Voice Agent**, the **Performance Intelligence Index (PI Index)**, and **Hiring Intelligence** — and defines the governance operating model that wraps the entire LLMOps lifecycle. The guiding design principle is consistent throughout: **deterministic guardrails around probabilistic agents**, with **humans deciding all consequential outcomes**.

## The Six Microsoft Responsible AI Pillars, Applied to AFNI

| Pillar | What it means at AFNI | Representative controls |
| --- | --- | --- |
| **Fairness** | Agents must not produce disparate outcomes across protected classes — critical in hiring, collections, and PI Index scoring across agents/sites. | Adverse-impact / four-fifths testing, fairness monitor agent, NYC LL144 bias audits, score-fairness checks across agents/sites, balanced golden evaluation sets. |
| **Reliability & Safety** | Voice, scoring, and recruitment agents behave predictably under load and edge cases; failures degrade gracefully. | Evaluation gates before promotion, canary/blue-green rollout, groundedness detection, deterministic fallback to human. |
| **Privacy & Security** | Caller and candidate PII is protected end to end. | PII detection/redaction (Purview + Content Safety), Entra ID + RBAC, Key Vault, private networking (see doc 09). |
| **Inclusiveness** | Systems work for diverse callers/candidates — accents, languages, accessibility needs. | Multilingual STT/TTS, accent-robust custom neural voice, accessible agent-assist UI, bias testing across demographics. |
| **Transparency** | Stakeholders understand how agents reach outputs and their limits. | Model cards, system cards, candidate/caller AI-disclosure notices, explainable PI Index driver breakdowns and ranking rationales. |
| **Accountability** | A named human owns every AI system and every consequential decision. | AI Governance Board, RAI/governance officer, audit trails, RACI (see doc 11), human-in-the-loop sign-off. |

> Note: "PI Index" is AFNI's Performance Intelligence Index. It is never abbreviated to "PII", which denotes Personally Identifiable Information.

## Human-in-the-Loop for Consequential Decisions

AFNI draws a firm line between **assistive** and **autonomous** operation. Consequential decisions — candidate rejection, adverse collections action, account changes with financial impact, and performance actions driven by a score — are never made autonomously by an agent.

- **Hiring Intelligence:** AI assists, humans decide. No autonomous rejection. Structured-interview scoring and the Candidate Fit signal are recommendations surfaced to a recruiter with explainable rationale; the recruiter records the decision.
- **PI Index:** Scores are explainable and advisory. Human calibration and an appeals path govern how scores feed coaching, QA calibration, and Gainshare/performance reporting; scores never trigger automated employment action.
- **Voice Agent:** Autonomous handling is limited to pre-approved containable call types. The Escalation/Handoff agent performs a warm transfer with full context whenever confidence, sentiment, or policy thresholds are breached.
- **Reflection/critic pattern:** A critic agent reviews high-stakes outputs before they surface, and the Compliance/Guardrail agent enforces must-say / do-not-say language deterministically.

## AI Use-Case Intake & Risk-Tiering

Every proposed AI use case enters through a standard **intake process** owned by the CoE: a lightweight intake form (business owner, data classes, decision impact, affected populations, compliance exposure) triggers a **risk-tiering assessment** by the RAI/governance officer. The tier dictates the depth of review, evaluation rigor, human-oversight requirements, and monitoring cadence.

### Risk-Tier Table

| Tier | Definition | Examples at AFNI | Required controls |
| --- | --- | --- | --- |
| **Tier 4 — Prohibited** | Unacceptable risk; not permitted. | Fully autonomous hiring rejection; emotion-based hiring inference; automated employment action from a PI Index score. | Blocked at intake. |
| **Tier 3 — High** | Consequential decisions affecting rights, employment, finances; regulated. | **PI Index performance scoring**, **Hiring Intelligence** (resume ranking, interview scoring assist, Candidate Fit), collections Voice Agent, PCI payment capture. | Mandatory bias audit, model + system card, human-in-the-loop, red-teaming, quarterly board review, full audit trail. |
| **Tier 2 — Moderate** | Customer/candidate-facing, limited autonomy, reversible. | Voice Agent agent-assist copilot, candidate Q&A concierge, JD generation. | Offline + online eval gates, content safety + groundedness, monthly monitoring, human review of samples. |
| **Tier 1 — Low** | Internal productivity, no PII decisioning. | Post-call summary drafts, internal knowledge search. | Standard eval, logging, spot checks. |

Both **PI Index scoring** and **Hiring Intelligence** are classified **Tier 3 — High**: they influence employment and performance outcomes and are subject to bias audit, explainability, human oversight, and audit-trail requirements.

## Model & System Cards

Every promoted model and every deployed agent system carries a card in the model/agent registry:

- **Model cards** — intended use, training/fine-tuning provenance, evaluation results, known limitations, fairness metrics, safety configuration.
- **System cards** — the composed multi-agent system: agent roster and roles, tools/systems of record accessed, guardrail configuration, data flows, human-oversight points, and the responsible owner. Cards are versioned alongside prompts and are a prerequisite for Tier 2+ promotion.

## Content Safety, Groundedness & PII

- **Azure AI Content Safety** provides prompt shields (jailbreak/prompt-injection detection), protected-material detection, harmful-content filters, and **groundedness detection** to catch ungrounded (hallucinated) claims against retrieved sources.
- **PII detection & redaction** is layered: **Microsoft Purview** for data classification, lineage, and governance across the estate, and **Content Safety / Language PII** for real-time redaction in prompts, transcripts, and logs. PCI cardholder data triggers pause-and-mask during Voice Agent payment capture.

## Audit Trails, Incident Response & Red-Teaming

- **Audit trails:** Every agent interaction, tool call, guardrail trigger, PI Index score write, and human override is logged immutably (Azure Monitor + Purview), retained per policy, and queryable for regulatory audits (TCPA, EEOC, LL144).
- **AI incident response:** A defined runbook classifies AI incidents (harmful output, groundedness failure, bias signal, scoring anomaly, data leakage, prompt-injection breach), assigns severity, triggers containment (feature flag / rollback), and feeds root cause into the evaluation dataset — closing the loop back to the LLMOps flywheel.
- **Red-teaming:** Structured adversarial testing (manual + automated via Azure AI red-teaming tooling) is mandatory for Tier 3 systems pre-launch and on a recurring cadence, probing jailbreaks, PII extraction, fairness failures, scoring manipulation, and compliance-language bypass.

## AI Governance Board & Operating Cadence

An **AI Governance Board** — chaired by the executive sponsor, with the AI product owner, GenAI architect, RAI/governance officer, security, legal/compliance, and ops/HR SMEs (all AFNI-internal) — owns policy and accountability.

| Cadence | Forum | Focus |
| --- | --- | --- |
| Weekly | CoE stand-up | Intake triage, incident review, evaluation results. |
| Monthly | RAI review | Tier 2/3 monitoring, drift, fairness metrics (incl. PI Index fairness across sites), model-card updates. |
| Quarterly | Governance Board | Portfolio risk, policy changes, red-team findings, audit readiness. |
| Ad hoc | Incident bridge | Sev-1/2 AI incidents and go/no-go decisions. |

This cadence ensures Responsible AI is continuously enforced, not certified once — matching the operational rigor AFNI already applies to running contact centers.
