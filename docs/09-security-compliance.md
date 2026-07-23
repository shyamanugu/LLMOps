# Security, Privacy & Compliance

## Purpose

AFNI operates in some of the most heavily regulated corners of the BPO industry — capturing card payments, handling protected health information for healthcare clients, running consented outbound campaigns, and making employment decisions across the US, Mexico, and the Philippines. The GenAI platform must therefore meet AFNI's existing enterprise-security bar and satisfy client and regulatory audits without exception. This document defines the security architecture, privacy controls, and a compliance matrix mapping the frameworks AFNI is accountable for to concrete Azure controls, across all three flagship initiatives — the **Voice Agent**, the **Performance Intelligence Index (PI Index)**, and **Hiring Intelligence**. The overarching stance is **secure by design, private by default, and auditable end to end**.

## Identity & Access

- **Microsoft Entra ID** is the single identity plane for all platform users, service principals, and agents. No local accounts.
- **Role-Based Access Control (RBAC)** enforces least privilege across Azure AI Foundry projects/hubs, AI Search, Cosmos DB, the PI Index score store, and Key Vault, aligned to CoE and business-unit roles (see doc 11).
- **Managed identities** are used for all service-to-service authentication — agents, Container Apps, and Functions call systems of record and Azure services without stored credentials.
- **Conditional Access, MFA, and Privileged Identity Management (PIM)** gate administrative and production access; just-in-time elevation for break-glass.

## Secrets, Keys & Encryption

- **Azure Key Vault** stores all secrets, API keys, and certificates; agents and pipelines retrieve them at runtime via managed identity. No secrets in code, prompts, or config.
- **Encryption in transit:** TLS 1.2+ everywhere, including telephony/SIP integration and internal service calls.
- **Encryption at rest:** Platform-managed keys by default with **customer-managed keys (CMK)** in Key Vault for Tier 3 data stores (transcripts, PI Index scores, candidate data, payment-adjacent records).

## Network Isolation

- All platform services (AI Foundry, Azure OpenAI, AI Search, Cosmos DB, Key Vault, Storage, Fabric) are deployed into a **hub-and-spoke VNet** and reachable only through **private endpoints**.
- **No public egress for data:** data-plane traffic never traverses the public internet; public network access is disabled on data services. Outbound access is restricted through Azure Firewall / NAT with explicit allow-lists.
- CCaaS/telephony integration (Genesys, NICE, Five9, Amazon Connect, or Azure Communication Services for greenfield) connects over private/VPN or ExpressRoute at a generic integration layer.

## Data Residency & Lifecycle

- **Data residency:** AFNI's footprint spans the **US, Mexico, and the Philippines**. Regional Azure deployments and data-boundary configuration keep regulated data (PHI, cardholder data, candidate PII, interaction transcripts, PI Index scores) resident in the appropriate jurisdiction; model endpoints are pinned to compliant regions and data zones. Cross-border flows are governed by Purview policy and contractual data-processing agreements.
- **Data lifecycle & retention:** Classified via **Microsoft Purview**; retention and purge schedules are enforced per data class and client contract (e.g., call recordings, transcripts, candidate records, score history). Training/evaluation datasets are de-identified; PII is redacted before it reaches logs or golden sets.

## Threat Protection & Posture

- **Microsoft Defender for Cloud** provides continuous posture management (CSPM), secure-score tracking, and workload protection across the platform; findings feed the governance cadence.
- **Prompt-injection & data-exfiltration defenses:** Content Safety **prompt shields** detect jailbreak and indirect injection attempts in user input and retrieved documents; tool-calling is constrained to an allow-listed, least-privilege set of actions; agent outputs are scanned for PII and secret patterns before egress; grounding sources are trust-scoped; and the Compliance/Guardrail agent enforces deterministic do-not-disclose rules. Egress filtering and DLP (Purview) prevent bulk data exfiltration via agent responses.

## Compliance Matrix

| Framework | Applies to | Key Azure / platform controls |
| --- | --- | --- |
| **PCI-DSS** | Payment capture in Voice Agent interactions | Pause-and-mask on card capture, PII redaction, network segmentation, CMK encryption, RBAC, audit logging, no card data in prompts/logs. |
| **HIPAA / HITECH** | Healthcare-client PHI | BAA-covered Azure services, PHI residency, encryption at rest/in transit, access controls, Purview classification, audit trails. |
| **TCPA** | Outbound Voice Agent campaigns | Consent capture and verification, do-not-call enforcement, disclosure scripting via Compliance agent, immutable consent audit log. |
| **SOC 2 (Type II)** | Platform trust services | Change management (CI/CD gates), access reviews, monitoring/alerting, incident response, evidence collection via Azure Monitor. |
| **GDPR** | EU data subjects / candidates | Lawful basis + consent, data-subject-access-request workflow, minimization, residency, right-to-erasure via retention/purge. |
| **EEOC / NYC Local Law 144** | Hiring Intelligence (AI-driven hiring) | Bias audits, adverse-impact testing, candidate notice/consent, human-in-the-loop, explainability, model/system cards. |
| **Illinois AI Video Interview Act** | Video interview tooling | Candidate notice/consent, limited data sharing, deletion on request. |
| **EU AI Act (high-risk employment)** | Hiring Intelligence recruitment agents | Risk management, transparency, human oversight, logging, technical documentation (system cards). |

## Shared-Responsibility & Client Assurance

Security is a shared responsibility: Microsoft secures the cloud fabric; AFNI's GenAI CoE secures the platform configuration, data, and use cases. Because many AFNI programs are audited by end clients, the platform is designed to **produce evidence on demand** — access reviews, encryption attestations, audit trails, bias-audit reports, and Defender secure-score history — so that onboarding a new regulated program becomes a repeatable, low-friction exercise rather than a bespoke security project each time.

## Summary

The security and compliance architecture is deliberately conservative: private networking with no public data egress, Entra-anchored least-privilege identity, Key Vault-managed secrets, CMK encryption for sensitive stores, jurisdiction-aware residency across the US, Mexico, and the Philippines, and layered prompt-injection/exfiltration defenses. Mapped explicitly to PCI-DSS, HIPAA, TCPA, SOC 2, GDPR, and the emerging body of AI-employment law (EEOC, NYC LL144, Illinois AI Video Interview Act, EU AI Act), it gives AFNI and its clients a defensible, audit-ready foundation for deploying GenAI into regulated workflows.
