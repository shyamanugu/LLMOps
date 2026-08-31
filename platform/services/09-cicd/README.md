# CI/CD

## What this is
Continuous integration for every component built so far: run each component's own test suite, lint the whole platform, and validate every Bicep template compiles — on every push and pull request, entirely on GitHub-hosted runners, with **no Azure credential of any kind**. Continuous *deployment* (actually pushing a change to a live Azure resource) is designed and documented below but not implemented — it requires an Entra ID app registration this access level can't create. See `docs/decisions/0012-cicd-scope.md`.

## Where the real files live
GitHub Actions only recognizes workflows physically at `.github/workflows/` in the repo root — they can't live inside this component's folder and still run. This folder is the source of truth for the *design*; the actual, executing file is `.github/workflows/ci.yml`. This is the one component whose deliverable isn't a Python package — there's no `src/`, no `pytest.ini`; the workflow YAML itself is the product.

## What CI actually does today
`.github/workflows/ci.yml` has three jobs, all genuinely running (not stubbed):

1. **`test`** — a matrix over every component with a Python package (02, 03, 04, 05, 06, 07, 08, 11), installing that component's `requirements.txt` and running `pytest` in its own directory. 01 (Bicep-only) and 09 (this component, no package) are intentionally excluded from the matrix.
2. **`lint`** — `ruff check platform/services`. Building this job surfaced 139 real style findings across the whole tree (mostly pre-PEP 585/604 typing syntax); fixed via `ruff check --fix` before this workflow was added, so it starts green rather than red on day one.
3. **`bicep-validate`** — compiles every `*.bicep` file with `az bicep build` (a local, offline compile — no Azure login involved). Building this job caught a genuine bug in `01-repo-foundation/infra/main.bicep`: its `managed-identity` module used a Resource Group module's *output* as a deployment `scope`, which Bicep can't resolve at compile time. Fixed by computing the resource group name from the same input parameters locally instead of reading it back from the module output.

## What CI does not do
No deployment job exists. Deploying anything (a Bicep template, a container image) to a live Azure subscription from GitHub Actions requires the workflow to authenticate as something — a service principal or an OIDC federated credential — both of which require Entra ID app registration permissions this access level doesn't have. Building a `cd.yml` that would fail on every run (for lack of credentials) would be worse than not having one: a red pipeline that can never pass isn't useful signal, it's noise. The planned design is documented below, ready to implement the moment that access exists.

## Planned CD workflow (not implemented — blocked on Entra ID access)
```yaml
# .github/workflows/cd.yml (future — do not create until Entra ID access exists)
name: CD
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # required for OIDC federated credential login
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Deploy Bicep templates
        run: az deployment group create --resource-group rg-llmops-<env>-eastus-001 --template-file <component>/infra/main.bicep --parameters <component>/infra/main.parameters.<env>.json
      - name: Run Evaluation Gate before promoting
        run: # a real usecase's pipeline + golden dataset, once one exists — see docs/decisions/0008-evaluation-gate-scope.md
```
This is a design sketch, not a file that exists — creating it now would mean it either sits disabled (useless) or runs and fails every time (worse). The batched access request this needs: **an Entra ID app registration (or federated credential) scoped to this platform's resource group, for GitHub Actions OIDC login.**

## File layout
```
workflow-templates/    # (empty) — reserved for reusable workflow snippets if the CD design above graduates from sketch to file once Entra ID access exists
```
The real deliverable, `.github/workflows/ci.yml`, lives at the repo root per GitHub's requirement — see "Where the real files live" above.

## Prerequisites
None to run `ci.yml` as it stands today — it needs no Azure credential, only GitHub Actions itself (enabled by default on this repo).

## Dependencies
- Depends on: every component with a test suite (02, 03, 04, 05, 06, 07, 08, 11) — the test matrix runs each one's own `requirements.txt`/`pytest.ini`
- Depended on by: nothing yet; this is infrastructure other components' pull requests now run against, not something they import

## Cost notes
Free — GitHub Actions on a public or appropriately-tiered private repo, no Azure resource provisioned or required for CI as built. CD, once implemented, costs whatever the underlying Azure deployments cost — no separate CD infrastructure charge.
