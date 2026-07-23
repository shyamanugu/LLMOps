# Risks & Mitigations

Deploying multi-agent GenAI into regulated contact-center and hiring workflows introduces real risk. This section presents a structured risk register spanning technical, model/quality, compliance/legal, security/privacy, adoption, vendor/cost, and delivery categories. The governing design principle — **deterministic guardrails around probabilistic agents**, with human-in-the-loop for consequential decisions — is the backbone of every mitigation below.

## Risk Register

Scoring: Likelihood and Impact rated **L / M / H**. Owners reference the GenAI Center of Excellence (CoE) operating model.

| # | Risk | Category | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R1 | Latency exceeds sub-second turn target, degrading voice UX | Technical | M | H | Use gpt-realtime speech-to-speech; regional co-location; streaming; hybrid Azure AI Speech fallback; load/latency SLOs in eval gates | GenAI Architect |
| R2 | Integration failures with CCaaS/telephony (Genesys, NICE, Five9, Connect) | Technical | M | H | Generic integration layer via SIP/APIs; Azure Communication Services for greenfield; contract tests; sandbox before production | Platform / Integration Lead |
| R3 | Model hallucination / ungrounded answers to callers or candidates | Model/Quality | H | H | RAG grounding via Azure AI Search; Content Safety groundedness detection; citation requirement; confidence thresholds → escalate to human | RAI/Governance Officer |
| R4 | Model or data drift degrades quality over time | Model/Quality | M | M | Online evaluation + shadow testing; drift monitors in Azure Monitor; scheduled re-eval on golden sets; feedback-loop retraining of prompts/KB | LLMOps Engineer |
| R5 | Prompt injection / jailbreak via caller or resume content | Model/Quality / Security | M | H | Content Safety prompt shields; input sanitization; least-privilege tool access; deterministic policy layer; red-teaming | Security Lead |
| R6 | TCPA violation on outbound/collections voice (consent, timing) | Compliance/Legal | M | H | Compliance/guardrail agent enforces consent checks, calling windows, mandatory disclosures; do-not-say/must-say lists; audit trail | RAI/Governance Officer |
| R7 | PCI-DSS exposure during payment capture | Compliance/Legal / Security | M | H | Pause/mask on payment segments; no card data to LLM; tokenization; scope isolation; PCI-audited flow | Security Lead |
| R8 | HIPAA breach for healthcare-client interactions | Compliance/Legal / Security | L | H | PHI detection/redaction (Purview + Content Safety); BAAs; data residency controls; access logging | RAI/Governance Officer |
| R9 | EEOC / NYC Local Law 144 / IL AI Video Act non-compliance in hiring | Compliance/Legal | M | H | **AI assists, humans decide** — no autonomous rejection; independent bias audit (LL144); adverse-impact monitor; candidate notice/consent; explainability | HR + RAI/Governance Officer |
| R10 | EU AI Act (high-risk employment) / GDPR obligations unmet | Compliance/Legal | L | M | Risk-tiered use-case intake; DPIA; model/system cards; data-subject rights process; documentation for high-risk classification | RAI/Governance Officer |
| R11 | PII leakage or unauthorized data access | Security/Privacy | M | H | Entra ID identity; Key Vault secrets; Purview lineage/DLP; Defender for Cloud posture; network isolation; least privilege | Security Lead |
| R12 | Low frontline adoption / rep distrust of copilot | Adoption/Change | H | M | Change-management plan; agent involvement in design; training; transparent "assist not replace" messaging; adoption KPIs | AI Product Owner |
| R13 | Candidate or client perception backlash against AI | Adoption/Change | M | M | Transparency and consent; human oversight messaging; opt-out paths; measured rollout with communications plan | AI Product Owner |
| R14 | Azure consumption cost overrun (tokens/minutes) | Vendor/Cost | M | M | FinOps: API Management quotas + token metering; caching; model right-sizing (GPT-4o-mini); budget alerts; cost dashboards | LLMOps Engineer |
| R15 | Vendor/model lock-in or deprecation | Vendor/Cost | M | M | Abstraction via orchestration framework; model catalog optionality (incl. open-weight Llama/Phi); acknowledge Bedrock/Vertex alternatives; portable prompts/evals | GenAI Architect |
| R16 | Scope creep / phased delivery slippage | Delivery | M | M | Crawl/Walk/Run gating; evaluation gates before promotion; RACI; steering cadence; MVP-first discipline | Delivery Lead / Exec Sponsor |
| R17 | Insufficient/poor-quality data & knowledge for RAG | Delivery / Model | M | H | Data & knowledge curation workstream in Phase 0; Document Intelligence ingestion; SME validation; KB quality gates | Data Engineer |
| R18 | Unclear ROI / benefits not measured | Delivery / Business | M | M | Baseline metrics in Phase 0; success KPIs per use case; online A/B; benefits tracking tied to Gainshare | AI Product Owner / Exec Sponsor |
| R19 | AI incident with no response plan | Governance | L | H | AI-specific incident response; kill-switch/rollback (canary, blue-green); audit trails; escalation runbooks | RAI/Governance Officer |

## Cross-Cutting Mitigation Themes

- **Human-in-the-loop for consequential decisions.** No autonomous candidate rejection; human handoff for low-confidence, high-stakes, or escalation-flagged interactions.
- **Deterministic guardrails wrap probabilistic agents.** A dedicated compliance/guardrail agent plus Azure AI Content Safety (prompt shields, groundedness, protected material, PII) enforce must-say / do-not-say, consent, and redaction independently of model behavior.
- **Evaluation gates are mandatory before promotion.** Offline golden sets, LLM-as-judge, and human review gate every prompt/agent/model change; online A/B and shadow testing catch regressions in production.
- **Governance wraps the full lifecycle.** Use-case intake with risk tiering, model/system cards, red-teaming, audit trails, and Microsoft Responsible AI pillars (fairness, reliability & safety, privacy & security, inclusiveness, transparency, accountability) apply end to end.
- **Observability makes risk visible.** Azure Monitor, Application Insights, and OpenTelemetry (GenAI semantic conventions) trace quality, cost, drift, and groundedness so issues surface before they become incidents.

## Residual Risk & Governance

No mitigation eliminates risk entirely; residual risk is managed through the CoE's ongoing governance, incident response, and continuous-improvement flywheel. High-impact compliance risks (R6–R10) warrant legal and compliance sign-off at each phase gate. The risk register is a living artifact, reviewed at steering cadence and updated as use cases scale across programs and geographies in Phase 3.
