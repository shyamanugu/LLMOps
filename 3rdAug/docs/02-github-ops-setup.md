# The Ops Backbone on GitHub

> This is the concrete setup: one monorepo per platform, one folder per use case inside it, four GitHub
> Actions workflows, gated environments, and federated login to Azure with no stored keys. Everything
> below is meant to be copy-able, not aspirational.

## Why a monorepo, and why per-use-case folders

Splitting every use case into its own repo sounds clean but breaks the thing LLMOps is supposed to
deliver: a shared, reusable platform. If prompt registry code, evaluation harness code, and CI
pipeline code live in ten different repos, every fix has to be applied ten times. A single monorepo
with a folder per use case keeps the platform pieces (`/src`, `/pipelines`, `/infra`) shared and lets
each use case own its own prompts, agents, and datasets without stepping on anyone else's.

```
llm-platform/
├── prompts/
│   ├── claims-triage/
│   │   ├── intent-router.yaml
│   │   └── summarize-note.yaml
│   └── billing-assistant/
│       └── answer-question.yaml
├── agents/
│   ├── claims-triage/
│   │   ├── router-agent.yaml
│   │   └── workflow.yaml          # sequential/handoff graph definition
│   └── billing-assistant/
│       └── workflow.yaml
├── evals/
│   ├── claims-triage/
│   │   ├── golden-v3.jsonl
│   │   └── evaluators.yaml
│   └── billing-assistant/
│       ├── golden-v1.jsonl
│       └── evaluators.yaml
├── src/
│   ├── orchestration/             # shared app/runtime code, all use cases import this
│   ├── connectors/                # RAG source connectors, tool clients
│   └── gateway/                   # APIM policy fragments, routing helpers
├── pipelines/                      # GitHub Actions workflow YAML lives here (mirrors .github/workflows)
│   ├── pr-checks.yml
│   ├── eval-full.yml
│   ├── deploy.yml
│   └── index-refresh.yml
├── infra/
│   ├── modules/                   # Bicep or Terraform modules (Foundry, AI Search, APIM, Key Vault)
│   └── envs/
│       ├── dev.bicepparam
│       ├── test.bicepparam
│       └── prod.bicepparam
├── dashboards/
│   ├── power-bi/
│   └── langfuse-configs/
└── CODEOWNERS
```

What lives where, in plain terms:

| Folder | Contents | Who edits it |
|---|---|---|
| `/prompts` | One YAML file per prompt, one folder per use case, semantic versioning (semver) in the file | Prompt authors, engineers |
| `/agents` | Agent and workflow definitions as code (roles, tools, orchestration pattern) | Engineers, with SME sign-off on behavior |
| `/evals` | Golden datasets in JSON Lines (JSONL) format, plus evaluator configuration | SMEs author cases, engineers wire evaluators |
| `/src` | The actual runtime/orchestration code that loads prompts, calls models, calls tools | Engineers |
| `/pipelines` | GitHub Actions workflow definitions (this package keeps a mirror copy here; the live copies GitHub reads must be under `.github/workflows/`) | DevOps/platform engineers |
| `/infra` | Infrastructure as code — Bicep or Terraform modules and per-environment parameter files | DevOps/platform engineers |
| `/dashboards` | Power BI report definitions, Langfuse dashboard configs, saved queries | Data/analytics engineers |

## Branching model

Trunk-based development. `main` is always deployable. Feature branches are short-lived (days, not
weeks) and named `feature/<use-case>-<short-description>` or `fix/<short-description>`. No long-running
`develop` branch — that just becomes a second place merge conflicts hide. Every change to `main` goes
through a pull request (PR); direct pushes to `main` are disabled at the branch-protection level.

`CODEOWNERS` at the repo root routes review requests automatically:

```
# CODEOWNERS
/prompts/          @genai-platform-team @prompt-reviewers
/agents/           @genai-platform-team @agent-reviewers
/evals/*/golden-*  @genai-platform-team @sme-reviewers
/infra/            @devops-team
/pipelines/        @devops-team
```

The `/prompts` and `/agents` lines matter most: a change to production behavior should never merge on
a single engineer's approval alone.

## The four GitHub Actions workflows

| Workflow | Trigger | What it does |
|---|---|---|
| `pr-checks.yml` | Every PR | Lint, unit tests, and — for any changed prompt or agent file — a **prompt regression evaluation** against a small golden subset (fast, cheap, blocks merge on failure) |
| `eval-full.yml` | Nightly + on every merge to `main` | Runs the **full** golden dataset for every use case, posts a scorecard as a PR/commit summary comment |
| `deploy.yml` | Merge to `main`, or manual dispatch | Builds a container image, deploys dev → test → prod through **GitHub Environments** with required reviewers on test and prod, runs a canary slice before full rollout, auto-rolls-back on health or evaluation alarms |
| `index-refresh.yml` | Scheduled (cron) + can be triggered by a data-change event | Re-runs the RAG (retrieval-augmented generation) ingestion pipeline to refresh the search index |

### `pr-checks.yml` (abbreviated)

```yaml
name: pr-checks

on:
  pull_request:
    branches: [main]

jobs:
  lint-and-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r src/requirements.txt
      - run: ruff check src/
      - run: pytest tests/unit -q

  prompt-regression:
    needs: lint-and-unit
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.changed_files, 'prompts/') ||
        contains(github.event.pull_request.changed_files, 'agents/')
    permissions:
      id-token: write        # required for OIDC (OpenID Connect) federated login
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Azure login (OIDC, no stored secret)
        uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Run golden-subset eval on changed prompts
        run: python pipelines/scripts/run_eval.py --scope changed --subset small
      - name: Post scorecard to PR
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: require('fs').readFileSync('eval-summary.md', 'utf8')
            })
```

### `deploy.yml` (abbreviated)

```yaml
name: deploy

on:
  push:
    branches: [main]
  workflow_dispatch: {}

permissions:
  id-token: write
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build container image
        run: docker build -t $REGISTRY/llm-platform:${{ github.sha }} .
      - name: Push to Azure Container Registry
        run: docker push $REGISTRY/llm-platform:${{ github.sha }}

  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
    environment: dev              # GitHub Environment, no required reviewers
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID_DEV }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID_DEV }}
      - run: ./pipelines/scripts/deploy.sh dev ${{ github.sha }}

  deploy-test:
    needs: deploy-dev
    runs-on: ubuntu-latest
    environment: test             # required reviewer: 1 engineer
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID_TEST }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID_TEST }}
      - run: ./pipelines/scripts/deploy.sh test ${{ github.sha }}
      - run: python pipelines/scripts/run_eval.py --scope full --env test

  deploy-prod-canary:
    needs: deploy-test
    runs-on: ubuntu-latest
    environment: prod             # required reviewers: 2, one from security team
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID_PROD }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID_PROD }}
      - name: Route 5% of prod traffic to new version via APIM
        run: ./pipelines/scripts/canary.sh --slice 5 --sha ${{ github.sha }}
      - name: Watch health + eval alarms for 30 minutes
        run: ./pipelines/scripts/watch_canary.sh --duration 30m
      - name: Promote to 100% if canary is healthy
        run: ./pipelines/scripts/promote.sh --sha ${{ github.sha }}
      - name: Roll back automatically if alarms fired
        if: failure()
        run: ./pipelines/scripts/rollback.sh --to last-good
```

Two things do the real work here: `environment:` on each job maps to a **GitHub Environment**
(`dev`/`test`/`prod`) with its own required reviewers and its own environment-scoped secrets/variables,
and `permissions: id-token: write` plus `azure/login@v2` is what makes OIDC federated login work — no
`AZURE_CLIENT_SECRET` or long-lived key ever gets stored as a GitHub secret. Azure trusts GitHub's
token issuer directly, scoped to this repo and branch, and Entra ID (the identity platform) checks it
on every run. Anything that still needs a secret (a third-party API key, a database connection string)
goes into Key Vault (the secrets store), fetched at runtime with the same federated identity.

## How canary + auto-rollback actually works

1. A new version deploys behind APIM (API Management, acting as the gateway in front of every model
   call) but only receives a small traffic slice — 5% is a reasonable starting point.
2. For the watch window, both the health checks (error rate, latency) and the evaluation alarms
   (quality score dropped, safety filter hit rate rose) are monitored side by side. This is the detail
   that makes it LLMOps rather than plain DevOps canarying: a release can be perfectly healthy from an
   infrastructure point of view and still be failing on quality.
3. If nothing trips an alarm, traffic is stepped up (5% → 25% → 100%) or moved in one jump, depending
   on how conservative the use case needs to be.
4. If anything trips an alarm, the rollback script points APIM's routing back at the last known-good
   version immediately, with no human in the loop required for the rollback itself (a human is
   notified and investigates after).

## Definition of done — "it is LLMOps when..."

- Prompts, agents, and evaluation datasets are versioned in Git — not edited in a portal after the
  fact.
- Every change to a prompt or agent runs an automated evaluation in CI before it can merge.
- Deploys are gated through GitHub Environments with required reviewers, and every deploy has a
  working rollback path.
- Production traces flow back into the golden datasets, so the eval suite keeps improving because the
  system is being used.
- No cloud credential is a stored static key — everything authenticates through OIDC federation to
  Entra ID.
