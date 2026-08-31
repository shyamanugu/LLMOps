# AFNI LLMOps Platform — Master Build Checklist

**Status:** Working draft — updated continuously during build. PPT is updated only after this document is stable (see Phase 4).

## Legend

- ✅ **Contributor-safe** — you can do this today with current Azure access
- 🔒 **Requires elevated permission** — needs Owner / User Access Administrator / Entra ID admin; must be requested and tracked
- 🌐 **External dependency** — support ticket, quota request, or a decision from someone outside this build (IT governance, client, security)

## Guiding Principles

1. **Access reality first.** We hold Contributor only. Every item that needs RBAC role-assignment or Entra ID app registration is called out explicitly and routed to a request queue — never assumed.
2. **Platform, not a POC.** Every component is built once in `platform/services/`, reused by every usecase. Nothing usecase-specific leaks into platform code.
3. **Reusability is proven, not claimed.** Usecase #2 (Hiring Intelligence) must onboard using *only* config/prompts/data — zero platform code changes. That's the actual acceptance test for "product-grade."
4. **Documentation before slides.** Every decision, setup step, and open question lives in `.md` first. The PPT is a translation of this document once it's settled — not a parallel source of truth.

---

## Phase 0 — Access & Permissions Audit

Must be resolved (or explicitly queued) before infra work starts.

- [ ] Confirm current Azure role: Contributor at [subscription / resource group] — record exact scope
- [ ] Confirm Entra ID permissions: can this account register App Registrations? (Y/N)
- [ ] Identify who holds Owner / User Access Administrator on the target subscription
- [ ] Identify who holds Application Administrator / Global Administrator in Entra ID
- [ ] Confirm existing Azure Policy assignments (naming, region restriction, allowed resource types, tagging enforcement) — request read access if not visible
- [ ] Confirm AFNI's resource naming convention (or propose one if none exists)
- [ ] Confirm AFNI's tagging taxonomy (cost center, environment, owner, project) — or propose one
- [ ] Confirm network model: existing hub-spoke VNet vs. build from scratch; private endpoint policy
- [ ] Confirm who owns cost/budget alerts today

### Permission Request Queue (hand off to Azure Owner / Entra ID admin)

| # | What | Why | Scope | Action Needed | Status |
|---|------|-----|-------|----------------|--------|
| 1 | RBAC: Managed Identity → Key Vault Secrets User | Container Apps read secrets without keys | RG | Role assignment | Pending |
| 2 | RBAC: Managed Identity → Storage Blob Data Contributor | RAG ingestion writes to blob | RG | Role assignment | Pending |
| 3 | RBAC: Managed Identity → Cognitive Services OpenAI User | Model calls without API keys | RG | Role assignment | Pending |
| 4 | RBAC: Managed Identity → Search Index Data Contributor | RAG index writes | RG | Role assignment | Pending |
| 5 | RBAC: Managed Identity → Cosmos DB Built-in Data Contributor | Feedback store writes | RG | Role assignment | Pending |
| 6 | Entra ID App Registration + Federated Credential | GitHub Actions OIDC → Azure (passwordless CI/CD) | Tenant | App registration | Pending |
| 7 | Cost Management Contributor (if budgets need programmatic creation) | Budget alerts as code | Subscription | Role assignment | Pending |
| 8 | Azure OpenAI model quota (region + TPM) | Enough throughput for prod | Subscription | Support ticket | Pending |
| 9 | Policy exception review (if any resource type/region is blocked) | Unblock a needed SKU/region | RG | Policy exception | Pending |

**Interim fallback while requests are pending:** use Key Vault (Access Policy model, not RBAC) to store connection strings / API keys — this is Contributor-safe and unblocks development without waiting on role assignments. Migrate to managed-identity/RBAC once approved. Track every interim workaround in `docs/architecture/permissions-log.md` so nothing quietly becomes permanent.

---

## Phase 1 — Documentation-First Workflow Setup

- [ ] Create `docs/decisions/` for Architecture Decision Records (ADRs)
- [ ] Create ADR template (`docs/decisions/0000-template.md`)
- [ ] Create `docs/architecture/azure-resource-map.md` (living doc: component → resource → SKU → status)
- [ ] Create `docs/architecture/permissions-log.md` (every 🔒 item: requested date, approved date, interim workaround used)
- [ ] Create `docs/architecture/reusability-scorecard.md` (filled in Phase 3)
- [ ] Commit this checklist (`.md` + `.html`) to the repo
- [ ] Agree as a team: PPT update happens only after Phase 3 is marked complete

---

## Phase 2 — Component Build (Contributor-safe path first, elevated items flagged)

### 01. Repo & Foundation
- [ ] Resource group name + region confirmed, matches AFNI convention ✅
- [ ] Tags applied: `environment`, `owner`, `cost-center`, `project=llmops` ✅
- [ ] User-assigned Managed Identity created ✅
- [ ] RBAC: MI → Key Vault / Storage / OpenAI / Search / Cosmos 🔒 (Phase 0, items 1–5)
- [ ] Key Vault created; access model decided — **recommend Access Policies to start** (Contributor-safe), migrate to RBAC once approved ✅
- [ ] `models.yaml` scaffold committed ✅
- [ ] `README.md` written

### 02. Prompt Management
- [x] Registry decision made: git-backed YAML + in-code registry (Contributor-safe, $0) — Foundry prompt assets deferred until Foundry RBAC is approved. See ADR 0006.
- [x] Prompt YAML schema finalized (name, version, description, model_capability, input_variables, output_schema, template)
- [ ] Schema validated with a linter/CI check — deferred to CI/CD (09)
- [ ] First prompt authored for Usecase #1 (APIX) — demo prompt authored under `tests/fixtures/`; real usecase prompts pending your usecase code
- [x] Shared fragment library built (`prompts/shared/`) — safety preamble, JSON-output instruction
- [x] Wired into Orchestration (08) — `ModelStep.prompt_name` + `prompt_registry`
- [x] `README.md` written

### 03. Model Management
- [ ] Azure OpenAI / AI Foundry resource confirmed or provisioned ✅
- [ ] Model quota confirmed available 🌐 (Phase 0, item 8)
- [ ] Required model deployments created (e.g., `reason`, `bulk` aliases)
- [ ] `models.yaml` populated per environment (dev/test/prod)
- [ ] Runtime resolver implemented + unit tested
- [ ] RBAC: MI → Cognitive Services OpenAI User 🔒, interim: API key in Key Vault ✅
- [ ] `README.md` written

### 04. Evaluation Gate
- [ ] Golden dataset schema finalized (`.jsonl`)
- [ ] Golden dataset authored for Usecase #1 — SME-sourced, 50–200 cases, per program
- [ ] Baseline run captured on current production output
- [ ] Metrics implemented: groundedness, tool-selection accuracy, PII leak, safety
- [ ] Thresholds defined in `evaluators.yaml` (regression limit + absolute floors)
- [ ] Container Apps Job created for eval runner ✅
- [ ] CI wired: PR-triggered subset + nightly full run
- [ ] `README.md` written

### 05. Observability
- [ ] Application Insights resource created ✅
- [ ] Log Analytics workspace linked ✅
- [ ] Tracing SDK integrated (OpenTelemetry) — trace/span/agent-session model
- [ ] `app.cost_usd` computed once per model-call span
- [ ] KQL queries / Workbook built: cost by usecase/day/model
- [ ] Langfuse tracing wired if component 02 uses Langfuse
- [ ] `README.md` written

### 06. Guardrails
- [ ] Azure AI Content Safety resource created ✅
- [ ] Input checks implemented: prompt-injection detection, PII scrub
- [ ] Output checks implemented: safety categories, schema validation
- [ ] Guardrail policy made configurable per usecase
- [ ] RBAC: MI → Cognitive Services User 🔒, interim: API key via Key Vault ✅
- [ ] `README.md` written

### 07. Data & Tools
- [ ] Azure AI Search created ✅ — SKU sized to expected index volume
- [ ] Azure SQL / existing AFNI DB access confirmed — **read-only, parameterized queries only**
- [ ] Blob Storage account created for documents ✅
- [ ] Document Intelligence resource created if `extract_document` needed ✅
- [ ] Data isolation model decided: shared index with `client_id` filter vs. per-client index (**BPO-specific — AFNI serves multiple end-clients, this is not optional**)
- [ ] Tools implemented: `search_knowledge`, `query_sql`, `extract_document`, `get_record`
- [ ] MCP server wrapper implemented and tested
- [ ] RBAC: MI → Search/Storage/SQL data roles 🔒, interim: connection strings via Key Vault ✅
- [ ] `README.md` written

### 08. Orchestration / Agent Runtime
- [ ] Container Apps environment created ✅
- [ ] Agent/pipeline code containerized (Dockerfile)
- [ ] Secrets wired via Key Vault reference (not env-var plaintext)
- [ ] Health check endpoint implemented
- [ ] `README.md` written

### 09. CI/CD
- [ ] GitHub Actions workflows created: `pr-eval-gate.yml`, `deploy.yml`, `nightly-eval.yml`
- [ ] GitHub → Azure auth: OIDC via federated credential 🔒 (Phase 0, item 6) — **preferred, passwordless**
- [ ] Interim fallback if blocked: confirm whether a Service Principal + client secret is even permitted (also 🔒, confirm before assuming this is a workaround)
- [ ] Branch protection rules configured (GitHub repo admin, not Azure)
- [ ] `README.md` written

### 10. Serving & Hosting
- [ ] Container Apps multi-revision strategy configured
- [ ] Canary split configured (~10% → ramp to 100%)
- [ ] APIM instance identified — new (Contributor-safe) or existing shared platform instance (confirm ownership)
- [ ] APIM policies: quota, rate limit, auth validation
- [ ] Promotion gate: manual approval step (GitHub Environments) + full eval pass required
- [ ] `README.md` written

### 11. Feedback Loop
- [ ] Cosmos DB (or Azure SQL) created for feedback store ✅
- [ ] Feedback capture schema implemented, tied to `trace_id`
- [ ] Triage workflow defined (Workbook or lightweight UI)
- [ ] "Confirmed bad case → golden dataset" process documented
- [ ] RBAC: MI → Cosmos DB Data Contributor 🔒, interim: connection string via Key Vault ✅
- [ ] `README.md` written

### 12. FinOps / Cost Management
- [ ] Budget alerts configured — confirm Cost Management Contributor is included in current access 🔒/✅ (verify)
- [ ] Cost export to Storage/Workbook configured
- [ ] Tagging enforced for allocation: project, usecase, environment
- [ ] Monthly reconciliation process documented (vs. actual Azure invoice)
- [ ] `README.md` written

### 13. Governance & Onboarding
- [ ] `usecases/_template/` scaffold finalized
- [ ] Onboarding runbook written: step-by-step for adding usecase N
- [ ] "Inherited vs. Defined" matrix kept current
- [ ] `README.md` written

### 14. Security & Compliance
- [ ] Key Vault access model decided and documented
- [ ] All RBAC requests cross-referenced against Phase 0 queue — none silently pending
- [ ] Data residency confirmed per client contract (BPO client data may have region/geo constraints)
- [ ] PII handling policy documented (cross-ref component 06)
- [ ] Diagnostic settings enabled on every resource → Log Analytics
- [ ] `README.md` written

---

## Phase 3 — Reusability Proof (this is the actual product acceptance test)

- [ ] Usecase #1 (APIX) fully onboarded and live end-to-end through the pipeline
- [ ] Usecase #2 (Hiring Intelligence) onboarding attempted using **only**: new prompts, new agent/pipeline config, new golden dataset, new data-source config
- [ ] Zero platform code changes required for Usecase #2 — any exception logged as a "platform gap," fixed generically (never usecase-specific patch)
- [ ] Reusability scorecard completed: % platform reused vs. % net-new, per usecase
- [ ] Time-to-onboard measured for Usecase #2 (this number is the pitch to leadership)
- [ ] Findings written to `docs/architecture/reusability-scorecard.md`

---

## Phase 4 — Documentation Consolidation → PPT Update

- [ ] All 14 component `README.md` files finalized, accurate to what was actually built (not what was planned)
- [ ] All ADRs finalized
- [ ] Reusability scorecard finalized
- [ ] Cost actuals captured — replace "indicative" figures in the original deck with real numbers
- [ ] Original PPT structure and framing preserved — content updated, not redesigned
- [ ] Updated PPT drafted, cross-checked against `.md` source of truth
- [ ] Client-ready version reviewed and approved
