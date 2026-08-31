---
applyTo: "platform/services/**/infra/**"
---

# Infrastructure (Bicep) conventions

- Naming pattern: `<type-abbreviation>-<workload>-<environment>-<region>-<instance>`. See `platform/services/01-repo-foundation/README.md` for the abbreviation table.
- Every resource carries the tagging schema defined in that same README: `environment`, `project`, `owner`, `costCenter`, `businessUnit`.
- Do not add role assignments (`Microsoft.Authorization/roleAssignments`) to any template. The current access level cannot grant them — a template that assumes otherwise will fail on deployment. Track the needed permission in `docs/checklist/BUILD-CHECKLIST.md` instead.
- Do not add Key Vault references or dependencies until `docs/decisions/0001-repo-foundation-approach.md` is superseded. Configuration is sourced from environment variables in the interim.
- Prefer a subscription-scope `main.bicep` orchestrator that module-deploys into a resource group, matching `platform/services/01-repo-foundation/infra/main.bicep` — but confirm actual Contributor scope before assuming subscription-level deployment will succeed (see the open assumption in ADR 0001).
