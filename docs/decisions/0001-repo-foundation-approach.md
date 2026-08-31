# ADR 0001: Repository & Foundation — interim approach under Contributor-only access

## Status
Accepted (interim)

## Context
Current Azure access is Contributor. Contributor cannot perform role assignments (`Microsoft.Authorization/roleAssignments/write`), so a Managed Identity can be created but cannot yet be granted access to any other resource — that requires an Owner or User Access Administrator. Secrets-management permissions are also not available, so a Key Vault, even if created, could not be reliably populated or read from under the current access model (many tenants also enforce the Azure RBAC permission model on new vaults rather than Access Policies, which would hit the same role-assignment wall).

**Open assumption:** this ADR assumes Contributor is scoped broadly enough to create a new Resource Group (subscription-level). If Contributor is instead scoped to a single, already-existing Resource Group, `resource-group.bicep` cannot be deployed as written — request the Resource Group be pre-created using the naming convention below, then deploy `managed-identity.bicep` directly into it with `az deployment group create`. Update this line once confirmed.

## Decision
1. Adopt the Cloud Adoption Framework naming pattern for every resource: `<type-abbreviation>-<workload>-<environment>-<region>-<instance>` (e.g., `rg-llmops-dev-eastus-001`).
2. Create the User-Assigned Managed Identity now, with no permissions attached. Every role assignment it will eventually need is tracked as a pending request rather than attempted.
3. Defer Key Vault entirely — no resource, no placeholder file. Standing up infrastructure that cannot be used yet just creates something to explain later.
4. Use a root-level `.env` file for configuration in the interim. Every value in it is a placeholder — no live credential is ever stored here, at any point, even temporarily.
5. `.gitignore` does not exclude `.env` in this repo. That is intentional and recorded here rather than left as an unexplained gap someone "fixes" later.

## Alternatives Considered
- **Create Key Vault now with the Access Policy permission model** as a stand-in for RBAC: rejected. Whether Access Policies can even be self-granted under this tenant's policy is unverified, and building on an unverified assumption defeats the point of an interim step.
- **Store configuration in a committed settings file** (e.g., `config.json`) instead of `.env`: rejected in favor of `.env`, since it is the convention most tooling and contributors already expect, and keeps the eventual migration to Key Vault a single, predictable swap.

## Consequences
- No secret is safe to commit to this repo until Key Vault is live. This holds regardless of deadline pressure — if a real credential is ever needed before then, it stays outside version control entirely (local-only, not even in `.env`).
- Every component built before Key Vault access is granted reads configuration through environment variables. To keep the eventual cutover a single change, components should read config through one loader rather than scattering direct environment-variable access through the codebase.
- The Managed Identity exists ahead of its permissions. This is deliberate — nothing needs to be re-provisioned once role assignments are approved; only the assignments themselves get added.

## Revisit When
Secrets-management access (either a Key Vault Access Policy grant or an RBAC role assignment) is approved. At that point: provision Key Vault, migrate `.env` values into it, update the config loader to read from it, and remove the placeholder values from source control.
