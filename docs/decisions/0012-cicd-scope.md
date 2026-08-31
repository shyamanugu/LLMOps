# ADR 0012: CI/CD — real CI now, CD designed but not built

## Status
Accepted

## Context
Eight components now have real test suites (79 tests total) and eight Bicep templates exist, none of them ever run through a CI check before this — every "passes" claim in this session's ADRs relied on running `pytest` and `az bicep build` by hand, once, at authoring time. That doesn't catch a regression introduced by a later change to a different component. Separately, actually deploying anything to Azure from a CI system requires the system to authenticate — which needs Entra ID app registration, explicitly outside this access level per the standing project constraint.

## Decision
1. **Build real CI now**: a `test` job (matrix over every component with a package), a `lint` job (`ruff check`), and a `bicep-validate` job (`az bicep build`, no Azure login required — it's a local compile). All three run on GitHub-hosted runners with zero Azure credentials.
2. **The workflow file lives at `.github/workflows/ci.yml`**, not inside `platform/services/09-cicd/`, because GitHub Actions only executes workflows from that root-level path. This component's folder documents the design; the root-level file is the actual running artifact. This is the one component whose deliverable isn't a Python package.
3. **Do not build `cd.yml`.** Any deployment job would need to authenticate to Azure — a service principal or OIDC federated credential, both requiring Entra ID app registration permissions this access level doesn't have. A workflow file that always fails for lack of credentials is worse than no file: it's a permanently red status that trains reviewers to ignore CI failures. The full design is documented in this component's README as a code block, ready to implement the moment Entra ID access is granted — this is now a concrete item for the batched Phase 0 access request.
4. **Fix what CI's first real run surfaced, before adding the job that would catch it going forward**: `ruff check` found 139 style findings (mostly pre-PEP 585/604 typing syntax accumulated across this session's writing); fixed via `ruff --fix` plus two manual `RUF013` (implicit-Optional) fixes, verified against the full 79-test suite with zero regressions. `az bicep build` found a real bug in `01-repo-foundation/infra/main.bicep`: its `managed-identity` module used a Resource Group module's *output* as a deployment `scope`, which Bicep can't resolve at compile time (the scope argument must be calculable before any module deploys). Fixed by computing the resource group name locally from the same input parameters, rather than reading it back from `rg.outputs.resourceGroupName`.

## Alternatives Considered
- **Building `cd.yml` now with placeholder/disabled deployment steps**: rejected — see Decision point 3. A workflow that either can't run or always fails provides no real signal and risks normalizing ignored CI failures.
- **Skipping the lint/Bicep-validate jobs, keeping only `test`**: rejected — both jobs found real, pre-existing issues (139 style findings, one genuine Bicep scope bug) the moment they were run for the first time, which is exactly the value a CI system is supposed to provide. Leaving them out would have meant discovering the Bicep bug only when someone actually tried to deploy.
- **Loosening ruff's rule set to avoid fixing 139 findings**: rejected — `ruff --fix` handled 137 of them mechanically and safely (verified against the full test suite), and the two remaining were genuine implicit-Optional annotations worth being explicit about. Weakening the linter to dodge real, correctly-flagged findings would defeat the point of adding it.

## Consequences
- Every future pull request now runs 79 tests, a lint pass, and a Bicep compile check automatically — the first time this platform has had any regression protection beyond "I ran it by hand once."
- The Bicep bug this caught (`main.bicep`'s scope error) would have surfaced as a deployment-time failure once Contributor access was used to actually provision component 01 — CI catching it now, before any real deployment attempt, is the entire point of validating Bicep in CI.
- Deployment remains entirely manual (the `az` commands documented in each component's README) until Entra ID access is granted — nothing about this ADR changes that; CI validates that infrastructure *would* deploy correctly, it doesn't deploy anything itself.

## Revisit When
- Entra ID app registration (or federated credential) access is granted — implement the `cd.yml` design documented in this component's README, add the required secrets, and wire the Evaluation Gate (04) call into it as the actual deploy-blocking check that component was built for.
- A real usecase exists with its own golden dataset — extend the CI matrix (or a new job) to run Evaluation Gate against that usecase's pipeline, not just Evaluation Gate's own unit tests.
