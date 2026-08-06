# Security — LLMOps Platform

Working notes on the security posture: Zero Trust, identity, secrets, network, guardrails,
the OWASP Top 10 for Large Language Model (LLM) applications mapped to concrete controls in
this codebase, and personally identifiable information (PII) handling. Abbreviations are
expanded on first use. This is enterprise-grade by design (the client asked for it).

---

## 1. Zero Trust

Assume no implicit trust from network location. Every call authenticates and authorises;
every input and output is inspected; least privilege everywhere.

- **Never trust the network**: services authenticate to each other and to Azure with
  identities, not shared secrets or IP allow-lists alone.
- **Verify explicitly**: API Management authenticates callers and enforces
  quotas/throttling before a request reaches the runtime.
- **Least privilege**: Managed Identity scoped per resource; SQL read-only and
  allow-listed; GitHub environments gated by approvers.
- **Assume breach**: everything is traced and costed; guardrails run on both input and
  output; secrets are short-lived Key Vault references, not embedded keys.

## 2. Identity — Entra ID and Managed Identity

- Azure access uses **Microsoft Entra ID** (formerly Azure Active Directory) with a
  **Managed Identity** on each Container App / Function. The app requests tokens for Azure
  OpenAI, AI Search, Cosmos, Content Safety, and Key Vault as itself — no API keys in code.
- In dev, a key may be injected via `.env` for convenience (`Settings.azure_openai_api_key`
  is `repr=False` so it never prints); in Azure it is left blank and Managed Identity is
  used. This is the `# TODO(wiring)` pattern: construct the client from Managed Identity.
- GitHub Actions authenticate to Azure with **OIDC federated login** (`azure/login@v2`,
  `id-token: write`) — no stored cloud credentials in GitHub secrets.

## 3. Secrets — Key Vault

- All secret values (connection strings, any residual keys) live in **Azure Key Vault** and
  are surfaced to the Container App as Key Vault references resolved via Managed Identity.
- `Settings` fields for secrets use `repr=False`; nothing prints secrets; structured logs
  carry only non-secret `detail`. `.env` is git-ignored; `.env.example` holds placeholders.
- No secret is ever committed; `copilot_prompts.py`/`todo.html` flag every place a real
  value must be supplied in the client tenant.

## 4. Network

- Ingress is through **API Management** (the gateway): quotas, throttling, and routing.
- Backend services run on **Azure Container Apps**; Azure data/AI services are reached over
  Azure networking (private endpoints where the tenant requires it — a setup decision).
- Self-hosted **Langfuse** runs inside the client's own network/container so LLM telemetry
  and prompt data stay with the client (data residency).

## 5. Guardrails (defence in depth)

Guardrails run as **input checks** (before the model) and **output checks** (before
returning/storing), orchestrated by `GuardrailEngine` over an ordered list of `Guard`s:

| Guardrail | What it stops | Implementation in this codebase |
|---|---|---|
| Prompt injection / jailbreak | hijacked instructions | `guardrails/injection.py` — Content Safety Prompt Shields |
| Unsafe content | hate/violence/sexual/self-harm | `guardrails/content_safety.py` — Azure AI Content Safety |
| PII detection & redaction | leaking personal data | `guardrails/pii.py` — Presidio or Azure AI Language PII |
| Hallucination / ungrounded claims | invented facts | Content Safety groundedness + the groundedness eval metric |
| Off-topic / out-of-scope | scope creep | system-prompt constraints + small classifier |
| Output format / schema | malformed output | `guardrails/schema_validation.py` — pydantic / JSON schema |
| Secrets / data exfiltration | data leaving | output scanning + regex (+ Purview DLP at tenant level) |
| Rate / cost abuse | denial-of-wallet | API Management policies (quotas/throttling) + budget alerts |
| Protected material / copyright | copyrighted output | Content Safety protected-material detection |

A block raises `GuardrailBlocked` (HTTP 422) — an expected control-flow signal, handled
gracefully, not a 500.

## 6. OWASP Top 10 for LLM Applications -> controls here

| OWASP LLM risk | Control in this codebase |
|---|---|
| LLM01 Prompt Injection | Prompt Shields (`injection.py`); input guardrails run before every model call; tools have typed input schemas |
| LLM02 Insecure Output Handling | `schema_validation.py` validates output; output guardrails + PII redaction before returning/storing |
| LLM03 Training Data Poisoning | we do not train base models; RAG data goes through ingest -> clean/PII -> index with reviewed sources (`index-refresh`) |
| LLM04 Model Denial of Service | API Management quotas/throttling; budget/cost alerts; `bulk` alias + subset evals limit spend |
| LLM05 Supply Chain | pinned `requirements.txt`; CODEOWNERS review; OIDC (no stored keys); config-as-code under review |
| LLM06 Sensitive Information Disclosure | PII detection/redaction (`pii.py`); Key Vault + Managed Identity; `repr=False` secrets; redacted tool args in traces |
| LLM07 Insecure Plugin/Tool Design | tools are typed `Tool` models with explicit `input_schema`; SQL is read-only, parameterised, allow-listed; MCP-described |
| LLM08 Excessive Agency | sequential pipelines (not A2A) with a fixed task-path; least-privilege tools; human-in-the-loop on high-impact actions |
| LLM09 Overreliance | evaluation gate on every change; online sampling; feedback loop; groundedness floors; citations required (APIX prompt) |
| LLM10 Model Theft | Managed Identity + Key Vault; APIM in front of models; no model weights exposed; access logged/traced |

## 7. PII handling

- **Detect and redact** before storage and before returning output: `pii.py` (Presidio /
  Azure AI Language) returns `redacted_text`; the engine substitutes it downstream.
- **Traces never carry raw PII**: tool args are redacted (`tool.args = redact(args)`);
  feedback stores a `user_hash`, not a raw user identifier.
- **RAG ingest scrubs PII** during clean/PII step before chunking/embedding.
- **Absolute floor**: the evaluation gate treats PII leak rate = 0 as a hard floor — any
  leak fails the gate and blocks the release.
- **Data residency**: Langfuse self-hosted in-network; Azure services in the client tenant.

## 8. Auditing and change control

- Every change (prompt, model, agent, config) is a reviewed PR with CODEOWNERS approval and
  an eval-gate record; promotions to test/prod require a named approver (GitHub
  Environments). Every request is traced with a trace id, enabling end-to-end audit and
  reconstruction of any answer.
