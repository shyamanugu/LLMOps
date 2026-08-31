# ADR 0016: Security & Compliance — cross-reference over re-decision, one validated diagnostic pattern

## Status
Accepted

## Context
By this point in the build, Key Vault's deferral (ADR 0001), PII detection (ADR 0009), and the Contributor-only access model had each already been decided by the components that needed them. What hadn't happened: a single place confirming those decisions are actually consistent with each other, a genuine audit of whether every RBAC-adjacent gap surfaced across 13 components had actually been logged, and any concrete mechanism for getting resource logs into Log Analytics (component 05's whole reason for existing, but nothing sends it anything yet).

## Decision
1. **This component cross-references and audits rather than re-deciding.** `data-residency.md` and `pii-handling-policy.md` point back to ADR 0003 and ADR 0009 respectively rather than re-litigating them, and surface what those decisions leave genuinely unaddressed (no per-client region override exists; golden datasets/promoted feedback carry real content with no PII-scrubbing policy).
2. **The permissions audit found two real, previously unlogged gaps** by grepping every component README for "RBAC" rather than trusting the existing list was complete: Azure AI Foundry's project-level role assignment (Prompt Management, distinct from GitHub OIDC) and the Entra ID app registration Serving & Hosting's HTTP auth would need (the same underlying capability as CI/CD's OIDC, but not previously cross-referenced as such). Both added to `docs/architecture/permissions-log.md` as items 13 and 14.
3. **One diagnostic-settings pattern is validated against a concrete resource type (Azure OpenAI), not built as a generic module.** A diagnostic setting is an ARM extension resource that must be scoped to its target via an `existing` reference of that target's exact type — Bicep can't express "attach this to any resource type" generically without knowing the type at authoring time. Rather than write a module that looks generic but would fail or behave unexpectedly against resource types it wasn't actually tested against, one real, `az bicep build`-validated example stands as the pattern every other component's Bicep should copy and adapt.
4. **Wiring the pattern into every existing component's Bicep is explicitly left as follow-up, not done here.** Making this change would mean touching ~10 already-built, already-tested Bicep files in the same change that establishes the pattern — mechanical, real work, but not something to rush through to close out this component.

## Alternatives Considered
- **A single "universal" diagnostic-settings Bicep module parameterized by resource type**: rejected — see Decision point 3. A module using a generic `existing` reference (e.g., typed as a base `Microsoft.Resources/resources` reference) wouldn't reliably support the `scope:` extension-resource pattern the way a concretely-typed `existing` reference does; authoring it without verifying against each actual resource type risks the same "deploys but silently wrong" failure mode already avoided for Workbooks (ADR 0014) and Prompt Shields (ADR 0009).
- **Wiring diagnostic settings into every component now**: rejected for this change — it's real, valuable, mechanical work, but doing it as a rushed afterthought within the component that merely establishes the pattern risks doing it carelessly across 10 files instead of correctly.
- **Assuming the permissions log was already complete** without a fresh audit: rejected — grepping actually found two real gaps (items 13, 14) that would have stayed silently missing otherwise, which is exactly the kind of "confirm, don't assume" discipline this component exists to apply.

## Consequences
- The permissions log is now more accurate than it was — 14 items instead of 12, found by actually checking rather than trusting the prior list.
- No resource in this platform is actually sending logs to Log Analytics yet; the pattern exists and is proven, the mechanical rollout across every component's Bicep is real remaining work.
- Data residency and PII handling both have a documented "this is not solved yet, here's exactly what's missing" — better than silence, but genuinely unsolved until a real client requirement or real PII-bearing dataset forces the question.

## Revisit When
- Wiring `diagnosticSettings` into each component's existing Bicep — a mechanical pass, one component at a time, each verified with `az bicep build` before moving to the next.
- A client contract specifies a data residency requirement — see `data-residency.md`'s own "Revisit when."
- A golden dataset or promoted feedback file is likely to contain real customer PII — see `pii-handling-policy.md`'s own "Revisit when."
