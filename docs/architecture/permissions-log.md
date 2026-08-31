# Permissions Log

Tracks every 🔒 access request this platform's build has identified, and the interim workaround used while it's pending. Mirrors the Permission Request Queue in `docs/checklist/BUILD-CHECKLIST.md` (Phase 0) — this file is the append-only history (requested date, approved date, workaround), that table is the current-state summary.

| # | What | Requested | Approved | Interim workaround | Notes |
|---|---|---|---|---|---|
| 1 | RBAC: Managed Identity → Key Vault Secrets User | Not yet requested | — | No Key Vault exists yet (ADR 0001) — `.env`/`.env.local` split used instead | Batch with the rest once ready to request |
| 2 | RBAC: Managed Identity → Storage Blob Data Contributor | Not yet requested | — | `AZURE_STORAGE_CONNECTION_STRING` in `.env.local` (component 11) | |
| 3 | RBAC: Managed Identity → Cognitive Services OpenAI User | Not yet requested | — | `AZURE_OPENAI_API_KEY` in `.env.local` (component 03) | |
| 4 | RBAC: Managed Identity → Search Index Data Contributor | Not yet requested | — | `AZURE_SEARCH_API_KEY` in `.env.local` (component 07) | |
| 5 | RBAC: Managed Identity → Cosmos DB Built-in Data Contributor | Not yet requested | — | N/A — Cosmos DB was not chosen; component 11 uses Blob Storage instead | This queue item may be obsolete; confirm before requesting |
| 6 | Entra ID App Registration + Federated Credential (GitHub Actions OIDC) | Not yet requested | — | None — CI/CD (09) built test/lint/Bicep-validate only; no deployment job exists | Blocks CD entirely until granted (ADR 0012). Also the same underlying capability Serving & Hosting (10) needs for Easy Auth / API Management on the HTTP endpoint (item 14) — one Entra ID app registration request likely serves both |
| 7 | Cost Management Contributor (if budget creation needs it) | Not yet requested | — | None — `budget.bicep` (component 12) authored, deployment attempt itself will reveal whether it's needed | See ADR 0014 |
| 8 | Azure OpenAI model quota (region + TPM) | Not yet requested | — | None — no usecase has real traffic yet | Support ticket, not a role assignment |
| 9 | Policy exception review (if any resource type/region is blocked) | Not yet requested | — | None — no blocked resource/region encountered yet | Only becomes relevant if a deployment attempt actually hits a policy block |

Additional items surfaced during the build, not in the original Phase 0 table:

| # | What | Requested | Approved | Interim workaround | Notes |
|---|---|---|---|---|---|
| 10 | RBAC: Managed Identity → Cognitive Services User (Content Safety, component 06) | Not yet requested | — | `AZURE_CONTENT_SAFETY_API_KEY` in `.env.local` | Optional — only if a usecase enables `azure_content_safety` |
| 11 | RBAC: Managed Identity → Cognitive Services Speech User (component 07) | Not yet requested | — | `AZURE_SPEECH_KEY`/`AZURE_SPEECH_REGION` in `.env.local` | |
| 12 | RBAC: Managed Identity → AcrPull (container registry, component 10) | Not yet requested | — | Public placeholder image (`mcr.microsoft.com/k8se/quickstart`) used in Bicep instead | No private registry exists yet either — this is blocked on item 6 (no image can be pushed without OIDC) |
| 13 | Azure AI Foundry project role assignment (for prompt flow, if migrating off git-backed prompts) | Not yet requested | — | Git-backed `PromptRegistry` used instead (component 02, ADR 0006) | Distinct from item 6 — this is a Foundry project-level role, not GitHub OIDC. Only becomes relevant if ADR 0006's "Revisit When" (Foundry RBAC becomes available) is acted on |
| 14 | Entra ID app registration for Serving & Hosting's (10) HTTP endpoint auth (Easy Auth or API Management) | Not yet requested | — | None — endpoint is unauthenticated; acceptable for local shape validation, not for real traffic | Same underlying access as item 6; see ADR 0013 |

**Every item above is still "not yet requested"** — per the standing workflow (batch all elevated-access requests together rather than one at a time), none has been submitted. This log exists so that when the batch request is made, it's made from a complete, accurate list rather than reconstructed from memory.
