# Risks & Mitigations

Deploying multi-agent GenAI into regulated contact-center, performance-scoring, and hiring workflows introduces real risk. This section presents a structured risk register spanning technical, model/quality, compliance/legal, fairness/scoring, security/privacy, adoption, cost, and delivery categories. The governing design principle — **deterministic guardrails around probabilistic agents**, with human-in-the-loop for consequential decisions — is the backbone of every mitigation below. All owners are AFNI-internal roles within the GenAI Center of Excellence (CoE) operating model.

## Risk Register

Scoring: Likelihood and Impact rated **L / M / H**.

| # | Risk | Category | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R1 | Latency exceeds sub-second turn target, degrading Voice Agent UX | Technical | M | H | gpt-realtime speech-to-speech; regional co-location; streaming; hybrid Azure AI Speech fallback; load/latency SLOs in eval gates | AFNI GenAI Architect |
| R2 | Integration failures with CCaaS/telephony (Genesys, NICE, Five9, Connect) | Technical | M | H | Generic integration layer via SIP/APIs; Azure Communication Services for greenfield; contract tests; sandbox before production | AFNI Platform / Integration Lead |
| R3 | Model hallucination / ungrounded answers to callers or candidates | Model/Quality | H | H | RAG grounding via Azure AI Search; Content Safety groundedness detection; citation requirement; confidence thresholds → escalate to human | AFNI RAI/Governance Officer |
| R4 | Model or data drift degrades quality over time | Model/Quality | M | M | Online evaluation + shadow testing; drift monitors in Azure Monitor; scheduled re-eval on golden sets; feedback-loop tuning of prompts/KB | AFNI LLMOps Engineer |
| R5 | Prompt injection / jailbreak via caller or résumé content | Model/Quality / Security | M | H | Content Safety prompt shields; input sanitization; least-privilege tool access; deterministic policy layer; red-teaming | AFNI Security Lead |
| R6 | **PI Index produces unfair or inconsistent scores across agents/sites/accents** | Fairness/Scoring | M | H | Score explainability + driver breakdown; fairness testing across agents/sites/demographics; human calibration & appeals process; model cards; do not use protected attributes as features | AFNI RAI/Governance Officer |
| R7 | **PI Index over-trusted or misused for punitive HR action without human review** | Fairness/Scoring / Adoption | M | H | Position as decision-support, not automated adjudication; human-in-the-loop for consequential HR use; documented appeals; audit trail; governance sign-off on downstream uses | AFNI HR + RAI/Governance Officer |
| R8 | Unfair candidate scoring / adverse impact in Hiring Intelligence | Fairness/Scoring / Compliance | M | H | **AI assists, humans decide** — no autonomous rejection; independent bias audit (NYC LL144); adverse-impact monitor; Candidate Fit as signal only; candidate notice/consent; explainability | AFNI HR + RAI/Governance Officer |
| R9 | TCPA violation on outbound/collections voice (consent, timing) | Compliance/Legal | M | H | Compliance/guardrail agent enforces consent checks, calling windows, mandatory disclosures; do-not-say/must-say lists; audit trail | AFNI RAI/Governance Officer |
| R10 | PCI-DSS exposure during payment capture | Compliance/Legal / Security | M | H | Pause/mask on payment segments; no card data to LLM; tokenization; scope isolation; PCI-audited flow | AFNI Security Lead |
| R11 | HIPAA breach for healthcare-client interactions | Compliance/Legal / Security | L | H | PHI detection/redaction (Purview + Content Safety); BAAs; data residency controls; access logging | AFNI RAI/Governance Officer |
| R12 | EEOC / NYC Local Law 144 / IL AI Video Act / EU AI Act non-compliance in hiring | Compliance/Legal | M | H | Risk-tiered intake; independent bias audit + publication (LL144); candidate notice/consent; DPIA; model/system cards; high-risk documentation | AFNI HR + RAI/Governance Officer |
| R13 | PII leakage or unauthorized data access | Security/Privacy | M | H | Entra ID identity; Key Vault secrets; Purview lineage/DLP; Defender for Cloud posture; network isolation; least privilege | AFNI Security Lead |
| R14 | Low frontline adoption / rep distrust of copilot or PI Index | Adoption/Change | H | M | Change-management plan; agent involvement in design; training; transparent "assist not replace" and "fair, explainable scoring" messaging; adoption KPIs | AFNI AI Product Owner |
| R15 | Candidate or client perception backlash against AI | Adoption/Change | M | M | Transparency and consent; human oversight messaging; opt-out paths; measured rollout with communications plan | AFNI AI Product Owner |
| R16 | Azure consumption cost overrun (tokens/minutes), including 100% PI Index scoring | Cost/FinOps | M | M | API Management quotas + token metering; caching; model right-sizing (GPT-4o-mini); batch/off-peak scoring; budget alerts; cost dashboards | AFNI LLMOps Engineer |
| R17 | Model lock-in or deprecation | Cost/Vendor | M | M | Abstraction via orchestration framework; model catalog optionality (incl. open-weight Llama/Phi); acknowledge Bedrock/Vertex alternatives; portable prompts/evals | AFNI GenAI Architect |
| R18 | Scope creep / phased delivery slippage | Delivery | M | M | Crawl/Walk/Run gating; evaluation gates before promotion; RACI; steering cadence; MVP-first discipline | AFNI Delivery Lead / Exec Sponsor |
| R19 | Insufficient/poor-quality data & knowledge for RAG and PI Index scoring | Delivery / Model | M | H | Data & knowledge curation workstream in Phase 0; Document Intelligence ingestion; SME validation; KB and scoring-rubric quality gates | AFNI Data Engineer |
| R20 | Unclear ROI / benefits not measured | Delivery / Business | M | M | Baseline metrics in Phase 0; success KPIs per initiative; online A/B; benefits tracking tied to Gainshare | AFNI AI Product Owner / Exec Sponsor |
| R21 | AI incident with no response plan | Governance | L | H | AI-specific incident response; kill-switch/rollback (canary, blue-green); audit trails; escalation runbooks | AFNI RAI/Governance Officer |

## Cross-Cutting Mitigation Themes

- **Human-in-the-loop for consequential decisions.** No autonomous candidate rejection; no punitive HR action on a PI Index score without human review; human handoff for low-confidence, high-stakes, or escalation-flagged interactions.
- **Fairness and explainability by design.** Both the PI Index and Hiring Intelligence expose driver breakdowns, run adverse-impact/fairness monitoring, publish model cards, and provide documented calibration and appeals paths. Protected attributes are excluded as scoring features.
- **Deterministic guardrails wrap probabilistic agents.** A dedicated compliance/guardrail agent plus Azure AI Content Safety (prompt shields, groundedness, protected material, PII) enforce must-say / do-not-say, consent, and redaction independently of model behavior.
- **Evaluation gates are mandatory before promotion.** Offline golden sets, LLM-as-judge, and human review gate every prompt/agent/model and scoring-rubric change; online A/B and shadow testing catch regressions in production.
- **Governance wraps the full lifecycle.** Use-case intake with risk tiering, model/system cards, red-teaming, audit trails, and Microsoft Responsible AI pillars (fairness, reliability & safety, privacy & security, inclusiveness, transparency, accountability) apply end to end.
- **Observability makes risk visible.** Azure Monitor, Application Insights, and OpenTelemetry (GenAI semantic conventions) trace quality, cost, drift, and groundedness so issues surface before they become incidents.

## Residual Risk & Governance

No mitigation eliminates risk entirely; residual risk is managed through the CoE's ongoing governance, incident response, and continuous-improvement flywheel. High-impact compliance and fairness risks (R6–R12) warrant legal, compliance, and HR sign-off at each phase gate. The risk register is a living artifact, reviewed at steering cadence and updated as the three initiatives scale across programs and geographies in Phase 3.
