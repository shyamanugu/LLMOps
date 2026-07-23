# Security Deep-Dive (Zero Trust + OWASP LLM Top 10)

> Internal AFNI reference. Owner: **AFNI · Office of GenAI Architecture** · Internal & confidential.
> Source of truth: `reference/proposal-bible.md` §8. Numbers marked **(ILLUSTRATIVE)**.

GenAI expands the attack surface: the model itself is a new, manipulable execution path, retrieved content is untrusted code-adjacent input, and agents can take consequential real-world actions. AFNI's stance is **Zero Trust + defense-in-depth**, designed for hostile inputs. The governing assumption: **treat all model I/O and retrieved content as untrusted**. No single control is sufficient; security is layered so that a failure at one layer is caught by the next.

## 1. Defense-in-depth layers

```
                          ┌───────────────────────────────────────────────┐
   Untrusted input  ───▶  │ 1. IDENTITY & NETWORK                          │
                          │    Entra ID, managed identities, VNet,        │
                          │    private endpoints, no public egress         │
                          ├───────────────────────────────────────────────┤
                          │ 2. AI GATEWAY (APIM)                           │
                          │    Authn/z, rate & token quotas, routing,      │
                          │    caching, WAF, per-tenant throttles          │
                          ├───────────────────────────────────────────────┤
                          │ 3. INPUT GUARDRAILS                            │
                          │    Content Safety prompt shields, injection    │
                          │    detection, PII pre-screen, schema checks    │
                          ├───────────────────────────────────────────────┤
                          │ 4. ORCHESTRATION (least privilege)             │
                          │    Scoped MCP tools, role/instruction          │
                          │    separation, HITL approval for high-risk     │
                          ├───────────────────────────────────────────────┤
                          │ 5. OUTPUT GUARDRAILS                           │
                          │    Groundedness, PII/secret redaction,         │
                          │    protected-material & safety filtering       │
                          ├───────────────────────────────────────────────┤
                          │ 6. DATA & VECTORS                              │
                          │    Per-tenant/per-source ACLs, encryption,     │
                          │    Purview lineage & DLP, poisoning defense    │
                          ├───────────────────────────────────────────────┤
   Alerts / audit  ◀───▶  │ 7. MONITOR & RESPOND                           │
                          │    Defender for AI, OTel traces, audit,        │
                          │    anomaly detection, AI incident response     │
                          └───────────────────────────────────────────────┘
```

Each layer maps to concrete Azure controls: **Entra ID** + managed identities and private networking (layer 1); **API Management** as the AI gateway (layer 2); **Azure AI Content Safety** prompt shields (layers 3, 5); least-privilege **MCP** tool scopes and human-in-the-loop (layer 4); **Microsoft Purview** governance/DLP and per-source vector ACLs (layer 6); **Defender for Cloud + Defender for AI** and unified OpenTelemetry (layer 7).

## 2. OWASP Top 10 for LLM Applications (2025) → AFNI controls

| ID | Risk | AFNI control |
|----|------|--------------|
| **LLM01** | Prompt Injection (direct + indirect) | Content Safety prompt shields; strict role/instruction separation; treat retrieved content as untrusted data, never instructions; output validation; least-privilege tools |
| **LLM02** | Sensitive Information Disclosure | PII detection/redaction (Purview + Content Safety); output secret-scanning; per-tenant data ACLs; data minimization |
| **LLM03** | Supply Chain | AI-BOM: model, dependency & MCP-server provenance; signed artifacts; curated model catalog; Defender for Cloud dependency scanning |
| **LLM04** | Data & Model Poisoning | Vetted/lineage-tracked sources (Purview); ingestion validation; RAG source allow-lists; anomaly detection on knowledge base |
| **LLM05** | Improper Output Handling | Never trust output as code/SQL/HTML; encode/escape; schema-validate; sandbox downstream execution |
| **LLM06** | Excessive Agency | Least-privilege scoped tools; graduated autonomy; **human approval for irreversible/high-risk actions**; deterministic guardrails wrap agents |
| **LLM07** | System-Prompt Leakage | No secrets in prompts (Key Vault); prompt-extraction red-team tests; output filtering for system text |
| **LLM08** | Vector & Embedding Weaknesses | Per-tenant/per-source access control on vectors; embedding-space isolation; retrieval authz enforced |
| **LLM09** | Misinformation | Groundedness/faithfulness evals + citations; refuse-when-unsupported; confidence surfacing |
| **LLM10** | Unbounded Consumption | Rate/token/cost limits at APIM; per-tenant quotas; loop/step caps; budget alerts + circuit breakers |

## 3. Priority threat detail

**Prompt injection (LLM01).** The signature GenAI vulnerability. *Direct* injection is a user telling the model to ignore its instructions; *indirect* injection hides malicious instructions inside retrieved documents, web content, or tool output. Defense is architectural: retrieved/tool content is always framed as **untrusted data with hard role separation**, never merged into the instruction channel; prompt shields flag known patterns; and — critically — even a successful injection is contained by least-privilege tools and output guardrails downstream.

**Excessive agency (LLM06) & data exfiltration (LLM02).** An agent with broad tool scopes and an injected instruction is an exfiltration engine. AFNI curbs this with narrowly scoped MCP tools, **human-in-the-loop approval for consequential/irreversible actions** (graduated autonomy), egress controls (no public egress; private endpoints), and output redaction so PII/secrets cannot leave even if requested.

**AI-BOM / supply chain (LLM03).** Every model, embedding, library, and MCP server is inventoried with provenance in an **AI Bill of Materials**; artifacts are signed and scanned (Defender for Cloud), and only catalog-approved models are deployable.

**PII.** Detected and redacted on both input and output via Microsoft Purview and Content Safety; Purview provides lineage, classification, and DLP so sensitive data flows are governed and auditable.

## 4. Red-teaming, Defender for AI & incident response

Security is continuous, not a launch checkpoint. An **adversarial red-team** suite runs in CI (injection, jailbreak, exfiltration, excessive-agency probes) as a blocking gate and is refreshed from new threats. **Microsoft Defender for AI** provides runtime threat protection for AI workloads — detecting anomalous prompts, jailbreak attempts, and suspicious agent behavior — integrated with Defender for Cloud. **AI incident response** extends AFNI's existing IR playbooks with GenAI-specific runbooks: contain (revoke tool scopes / disable agent via APIM), investigate (OpenTelemetry trace replay), remediate (patch prompt/guardrail, re-eval), and report. All model I/O is audit-logged.

## 5. Compliance mapping

The framework is compliant-by-default, inheriting controls per use case:

| Regime | Relevance | Key controls |
|--------|-----------|--------------|
| **PCI-DSS** | Payment data in collections/care | Tokenization, redaction, network segmentation, audit |
| **HIPAA** | Healthcare clients | PHI redaction, BAA-aligned services, encryption, access logs |
| **TCPA** | Outbound voice/contact | Consent, disclosure, call-handling controls |
| **SOC 2** | Enterprise trust | Access control, monitoring, change management, evidence |
| **GDPR** | EU data subjects | Data minimization, DSAR support, lineage, retention |
| **EEOC / NYC LL144** | Hiring Intelligence | Bias audits, disparate-impact testing, transparency |
| **EU AI Act** | High-risk AI (hiring) | Risk classification, human oversight, documentation, logging |

Zero Trust layering, OWASP-mapped controls, continuous red-teaming, Defender for AI, and inherited compliance make the paved road safe to scale — security by construction, not by exception.
