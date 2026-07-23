# Use Case 2 — AI-Driven HR Recruitment

## Executive summary

Afni hires at high volume and high velocity. Staffing thousands of contact-center roles across US sites (IL, AZ, KY, TX, MO, AL), Mexico, the Philippines, and the **Afni@Home** program means large applicant funnels, seasonal surges, and constant pressure on time-to-fill, cost-per-hire, and early attrition. This use case applies the same governed **Azure AI Foundry** multi-agent platform proposed for Voice AI to Afni's *own* recruiting operation — turning a labor-intensive, inconsistent funnel into a fast, consistent, and **auditable** candidate experience.

One principle governs every design choice below and is stated up front because it is load-bearing for the entire use case:

> **AI assists, humans decide. No candidate is ever autonomously rejected by a model.**

Every consequential decision — advance, reject, offer — is made by a human recruiter or hiring manager. The agents accelerate, structure, and standardize; they do not adjudicate.

## Candidate journey and the agents at each stage

| Stage | Agent | What it does | Human decision point |
|---|---|---|---|
| Requisition | **JD-generation agent** | Drafts inclusive, bias-checked job descriptions from role templates and structured criteria | Recruiter approves/edits JD |
| Sourcing & screening | **Sourcing/screening agent** | Parses resumes, ranks against *job-related* structured criteria with explanations | Recruiter reviews ranked list |
| Conversational screening | **Conversational screening agent** | Chat screen (+ optional **voice pre-screen** reusing the Voice AI platform) for availability, eligibility, role fit | Recruiter reviews transcript/flags |
| Scheduling | **Scheduling agent** | Books interviews across calendars/ATS; handles reschedules and reminders | Recruiter confirms slate |
| Candidate support | **Candidate-Q&A concierge** | Answers candidate questions 24/7 (role, pay, sites, process, benefits) | — (informational only) |
| Structured interview | **Interview-scoring ASSIST agent** | Provides structured rubric prompts and note capture; suggests evidence-based scores | Interviewer scores and decides |
| Oversight | **Fairness/adverse-impact monitor** | Continuously measures selection rates across groups; flags disparity | RAI officer + recruiting leadership act |

### Stage detail

- **JD generation** — Produces role-appropriate, inclusive language; strips exclusionary phrasing; grounds pay/benefit statements in approved content via Azure AI Search. Output is a draft, never auto-posted.
- **Sourcing/screening & resume ranking** — Ranks candidates against **job-related, validated criteria only** (skills, availability, licensure where required). Every ranking carries an **explanation** ("advanced for: bilingual, weekend availability") so recruiters see the *why*. Protected characteristics and proxies are excluded from features.
- **Conversational screening (incl. optional voice pre-screen)** — Reuses the Mode A/B voice platform for a short structured pre-screen where appropriate, with explicit notice and consent. It gathers factual, job-related information; it does **not** score personality from voice tone.
- **Scheduling** — Eliminates recruiter calendar tetris; sends reminders to cut no-shows.
- **Candidate-Q&A concierge** — A grounded RAG bot improving candidate experience and reducing recruiter interruptions.
- **Structured-interview scoring ASSIST** — Enforces a consistent, structured interview; captures evidence and *suggests* scores against a rubric. The interviewer always makes the call.
- **Fairness/adverse-impact monitor** — Runs continuously across the funnel, computing selection rates and four-fifths-rule style checks, feeding the bias-audit process.

## Recruitment funnel flow

```
   Requisition
       |
       v
 [JD-generation agent] --(draft)--> Recruiter approves --> Post to ATS/job boards
                                                              |
                                                              v
                                                      Applicants (high volume)
                                                              |
                                                              v
                                            +-----------------------------------+
                                            | Sourcing/Screening agent          |
                                            | resume parse + explainable rank   |
                                            +-----------------+-----------------+
                                                              | ranked + reasons
                                                              v
                                                   >>> RECRUITER REVIEWS <<<
                                                   (human decides who advances)
                                                              |
                                                              v
                                        +-------------------------------------+
                                        | Conversational screening agent      |
                                        | chat (+ optional voice pre-screen)  |
                                        +-------------------+-----------------+
                                                            | transcript + flags
                                                            v
                                                   >>> RECRUITER REVIEWS <<<
                                                            |
                                                            v
                                              +---------------------------+
                                              | Scheduling agent          |
                                              +-------------+-------------+
                                                            v
                                              +---------------------------+
                                              | Structured interview      |
                                              | (ASSIST scoring, human    |
                                              |  interviewer decides)     |
                                              +-------------+-------------+
                                                            v
                                                   >>> HIRING MGR DECIDES <<<
                                                   advance / offer / decline
                                                            |
   [Candidate-Q&A concierge] --- available 24/7 across ALL stages ---+
                                                            |
   [Fairness/Adverse-impact monitor] --- observes EVERY stage --------+
                                          (flags disparity to RAI officer)
```

## Multi-agent breakdown

| Agent | Pattern | Autonomy | Key Azure services |
|---|---|---|---|
| JD-generation | Sequential + reflection | Draft only | GPT-4o, AI Search |
| Sourcing/screening | Concurrent | Rank + explain, no reject | Document Intelligence, embeddings, AI Search |
| Conversational screening | Supervisor-orchestrator | Collect facts, no scoring judgments | gpt-realtime / GPT-4o, Speech |
| Scheduling | Action/Tooling hand-off | Autonomous (logistics only) | Azure Functions, ATS/calendar APIs |
| Candidate-Q&A concierge | Knowledge/RAG | Informational only | AI Search, Content Safety |
| Interview-scoring ASSIST | Reflection/critic + human-in-loop | Suggest only | GPT-4o, prompt registry |
| Fairness/adverse-impact monitor | Concurrent oversight | Alert only | Fabric, Purview, evaluation SDK |

The orchestrator sequences these agents, but **human-in-the-loop gates are hard-wired** at every advance/reject/offer point — the platform cannot skip them.

## Responsible AI and fairness (the core of this use case)

Employment decisions are legally and ethically consequential. Under the EU AI Act, AI in recruitment and selection is classified **high-risk**, and multiple US jurisdictions impose specific obligations. The platform is engineered so that Afni meets these obligations by design, not by after-the-fact patching.

| Regulation / standard | Requirement | How the platform complies |
|---|---|---|
| **EEOC / Title VII** | No disparate impact in selection | Fairness monitor + job-related, validated criteria only; humans decide |
| **NYC Local Law 144** | Independent **bias audit** of automated employment decision tools; candidate notice | Audit-ready logs, disparity metrics, annual third-party bias audit, published summary |
| **Illinois AI Video Interview Act** | Notice, consent, explanation, deletion, limited sharing for AI-analyzed video | No autonomous video scoring; explicit notice/consent; retention & deletion controls (relevant to IL HQ) |
| **EU AI Act (high-risk employment)** | Risk management, human oversight, transparency, logging | RAI intake + risk tiering, human-in-loop, model/system cards, full audit trail |
| **GDPR** | Lawful basis, transparency, right to human review of automated decisions | Consent capture, data minimization, no solely-automated decisions, DSAR support |

**Guardrails enforced across all agents:**

- **No autonomous rejection** — models never reject; they rank and explain, humans decide.
- **Explainability** — every ranking/suggestion carries a plain-language, job-related rationale.
- **Bias exclusion** — protected attributes and known proxies excluded from features; continuous adverse-impact testing.
- **Candidate notice & consent** — clear disclosure that AI assists the process, before any AI-assisted step.
- **Model & system cards** — documented for JD, screening, and scoring agents; versioned in the prompt/model registry with evaluation gates before promotion.
- **Audit trail** — immutable logs (Purview) of every recommendation, rationale, and human decision.

## KPI framework

| KPI | Baseline (illustrative) | Target impact |
|---|---|---|
| Time-to-fill | — | 20–40% reduction |
| Cost-per-hire | — | measurable reduction |
| Funnel conversion (apply → hire) | — | +uplift via faster response |
| Recruiter hours saved (screening) | — | 30–50% screening effort reduction |
| Candidate experience / NPS | — | +uplift (24/7 concierge, faster scheduling) |
| Offer-accept rate | — | +uplift |
| 90-day attrition | — | reduction via better-matched hires |
| Interview-to-hire quality | — | more consistent, structured scoring |
| **Adverse-impact ratio** | — | within four-fifths guideline; monitored continuously |

All figures are illustrative placeholders replaced by Afni actuals during Phase 0 discovery. The adverse-impact ratio is a **guardrail metric**, not an efficiency metric — it gates the program.

## ATS / HRIS integration notes

- **Integration layer stays generic** (mirroring the Voice AI approach): connect to Afni's incumbent ATS/HRIS via APIs (e.g., Workday, iCIMS, Greenhouse, SAP SuccessFactors — no specific incumbent assumed).
- **Azure Functions + API Management** broker all reads/writes; **Key Vault** holds credentials; **Entra ID** governs identity and least-privilege access.
- Candidate records, consent status, decision rationale, and audit logs are written back to the ATS so it remains the system of record; analytics land in **Fabric / Data Lake** with **Purview** lineage.
- PII is detected and protected via **Content Safety + Purview**; retention and deletion policies enforce GDPR and Illinois requirements.

## Suggested pilot scope

- **One high-volume role family** (recommend frontline contact-center agents) at **1–2 US sites**, aligning with the Crawl-phase HR screening pilot.
- **In scope:** JD-generation, explainable resume ranking, conversational chat screening, scheduling, and the candidate-Q&A concierge — all with human-in-the-loop gates.
- **Out of scope for the pilot:** autonomous decisions of any kind; voice pre-screen deferred to the Walk phase once consent flows and the voice platform are proven.
- **Governance gate before launch:** RAI intake and risk tiering completed, candidate notice/consent finalized with Legal, and the **Local Law 144 bias-audit** process established.
- **8–12 week pilot**, success measured on time-to-fill, recruiter hours saved, candidate NPS, and — as a hard gate — adverse-impact metrics within acceptable bounds before any expansion.
