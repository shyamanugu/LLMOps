# AFNI LLMOps Platform — Copilot Instructions

## What this repository is
A reusable LLMOps platform, not a single usecase. Code under `platform/services/` is shared infrastructure and application logic used by every usecase under `usecases/`. Nothing usecase-specific belongs in `platform/`.

## Non-negotiable practices

**Document every decision when it's made.** Any architectural choice, tradeoff, or deviation from an earlier decision gets an Architecture Decision Record in `docs/decisions/`, following the format in `docs/decisions/0000-template.md`, numbered sequentially. Write it at the time of the change, not after the fact.

**No secrets in source control, ever.** Values in `.env` and elsewhere are placeholders only. See `docs/decisions/0001-repo-foundation-approach.md` for the current interim configuration approach — Key Vault is not wired in yet, and this rule applies with no exceptions until it is.

**Respect the current Azure access level.** This platform is being built under Contributor access only: it cannot create RBAC role assignments, cannot manage Entra ID app registrations, and cannot assume Key Vault is usable. Do not write code or infrastructure that assumes elevated permissions exist. If a task genuinely needs them, flag it explicitly rather than working around it silently — add it to the permission queue in `docs/checklist/BUILD-CHECKLIST.md` (Phase 0).

**Naming and tagging.** Every Azure resource follows `<type-abbreviation>-<workload>-<environment>-<region>-<instance>` (e.g. `rg-llmops-dev-eastus-001`). Tagging schema is documented in `platform/services/01-repo-foundation/README.md`.

## Where to look before making a change
- `docs/architecture/azure-resource-map.md` — component → Azure resource → status
- `docs/decisions/` — every accepted decision and the reasoning behind it
- `docs/checklist/BUILD-CHECKLIST.md` — what's built, what's pending, what needs elevated access
- `platform/services/<component>/README.md` — setup and scope for that specific component

## Scope-specific guidance
Path-specific instructions live in `.github/instructions/` and apply automatically based on the file being edited.
