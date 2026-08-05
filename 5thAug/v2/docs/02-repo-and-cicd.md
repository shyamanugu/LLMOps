# Source Control & CI/CD (Component #1)

This is the backbone and the first thing we set up. Continuous Integration / Continuous Deployment (CI/CD) plus source control is component #1 for a reason: every other component — prompts, models, evaluation, observability, guardrails — lands in this repository and flows through these workflows. Once the backbone is in place, we onboard the rest one at a time.

## Today

The APIX and Hiring code is already on GitHub. There are pull requests, reviews, and some deployment automation. This is a real starting point, and we are not replacing it. What is missing is the LLMOps-specific structure: prompts and agent definitions are buried inside application code rather than living as reviewable artifacts, and there is no evaluation step in the pipeline — a change to a prompt or a model ships like any other code change, with unit tests at best and no check on output quality.

## Our setup

### One monorepo, split into platform and use cases

Everything lives in one repository. It has two halves. `platform/` holds the shared machinery — built once, reused by every use case. `usecases/<name>/` holds one folder per use case, each the same shape, holding only that use case's own content. When you read the tree, the split is the message: almost everything is on the `platform/` side.

```
llmops-platform/
├─ platform/                         # SHARED — built once, reused by every use case
│  ├─ common/     prompt_loader.py  model_router.py  tracing.py  guardrails.py  data_access.py
│  ├─ tools/      search_knowledge/  query_sql/  extract_document/  get_record/   # reusable MCP tools
│  ├─ evaluators/ ragas_eval.py  deepeval_suite.py  tool_selection.py  judges/
│  ├─ gateway/    apim-policies/
│  └─ infra/      bicep modules (container apps, apim, ai search, cosmos, langfuse)
├─ usecases/
│  ├─ apix/
│  │  ├─ prompts/   *.prompt.yaml
│  │  ├─ agents/    pipeline.agent.yaml
│  │  ├─ evals/     golden.telesales.jsonl  golden.wcc.jsonl  evaluators.yaml   # thresholds
│  │  ├─ tools/     (only use-case-specific tools, if any)
│  │  └─ config/    datasources.yaml  model-overrides.yaml
│  └─ hiring/       (same shape)
├─ models.yaml                       # shared task-alias -> deployment
├─ .github/workflows/                # shared pipelines (pr-checks, eval-full, deploy)
└─ dashboards/
```

Where each thing sits:

- **Use cases** — each is one folder under `usecases/`. `apix/` and `hiring/` are the two we start with. A use case folder is the *only* place a use case's own content lives.
- **Prompts** — `usecases/<name>/prompts/*.prompt.yaml`, one YAML file per prompt. This is the source of truth for prompt text. Covered in detail in the prompt management document.
- **Agents (the pipeline)** — `usecases/<name>/agents/pipeline.agent.yaml`. This describes the ordered steps and, for each step, which prompt and which tools it uses. This is where the shape of a use case is defined. The runtime that *executes* those steps is shared and lives in `platform/`.
- **Models** — one shared `models.yaml` at the root maps task aliases to Azure OpenAI deployments for every use case. A use case that needs a different model for one step records it in its own `config/model-overrides.yaml`, still resolved through the shared router.
- **Tools** — the reusable tool catalog is shared in `platform/tools/` (`search_knowledge`, `query_sql`, `extract_document`, `get_record`). A use case composes these. Only a genuinely use-case-specific tool sits under `usecases/<name>/tools/`, and once it is generally useful it graduates into the shared catalog.
- **Evals and golden datasets** — the evaluation *engine* is shared in `platform/evaluators/` (Ragas, DeepEval, the tool-selection harness, the LLM judges). The golden dataset *contents* and the thresholds are per use case in `usecases/<name>/evals/` — the JSON Lines golden files plus `evaluators.yaml`.
- **Shared code** — `platform/common/` holds what every use case reuses: `prompt_loader.py`, `model_router.py`, `tracing.py`, `guardrails.py`, `data_access.py`.
- **Gateway and infrastructure** — `platform/gateway/` (APIM policies) and `platform/infra/` (Azure infrastructure as Bicep: Container Apps, APIM, AI Search, Cosmos DB, self-hosted Langfuse).
- **Workflows** — `.github/workflows/` holds the three shared pipelines that run for every use case.
- **Dashboards** — dashboard and alert definitions kept as code, so monitoring changes are reviewed like everything else.

**Adding the Nth use case is adding one folder.** Copy the shape of `usecases/apix/`, fill in the prompts, the pipeline design, the golden dataset and thresholds, and the data-source config, and reuse from `platform/`: the CI/CD workflows, the evaluation engine, the tracing, the tool catalog, the gateway, the guardrails, the model router. No new infrastructure, no new pipeline code. The large work is standing up `platform/` once; each additional use case is filling in its folder.

### Branching and CODEOWNERS

We use short-lived feature branches with pull requests into `main`. `main` is protected: no direct pushes, and merges require a passing `pr-checks` run and at least one review.

`CODEOWNERS` puts a named reviewer requirement on the `prompts/` and `agents/` folders inside each use case. A change to a prompt or a pipeline step cannot merge without sign-off from the owner of that area — usually a subject-matter expert (SME) or the pipeline owner, not just any engineer. This is what makes prompt and agent changes first-class, reviewable artifacts instead of edits hidden inside a larger code diff.

## The CI/CD flow, stage by stage

Every change — a prompt edit, a model swap in `models.yaml`, a new agent step — travels the same path from an engineer's branch to production. The stages are:

1. **Author change** — an engineer or SME edits an artifact on a feature branch: a prompt YAML, a pipeline step, a threshold, a line in `models.yaml`. The change is a small, reviewable diff, not buried in application code.
2. **Pull request** — the branch is opened as a pull request into `main`. Peer review plus a `CODEOWNERS` reviewer for the touched `prompts/` or `agents/` area must approve. Nothing merges unreviewed.
3. **Automated checks** — the pull request triggers `pr-checks.yml`, which runs lint, unit tests, and contract tests on the change. These catch the mechanical faults before any model runs.
4. **Evaluation gate** — the same workflow scores the changed artifact against the golden dataset and compares every metric to its baseline. If any metric regresses past its threshold, the job exits non-zero and the merge is **blocked**. This is the step that does not exist today, and it is the heart of the platform.
5. **Merge** — once checks and the evaluation gate are green and the review is approved, the change merges to `main`. On merge, `eval-full.yml` runs the complete golden dataset across all metrics — wider than the fast subset the pull request ran.
6. **Promotion gates** — deployment moves through environments in order: `dev` (automatic), then `test`, then `prod`. Each promotion past `dev` needs a human approver *and* a passing full evaluation. These are GitHub Environments protection rules, enforced by the platform, not by convention.
7. **Canary release** — a production release goes out to a small slice of traffic first (a new Container Apps revision taking about 10%), watched against service-level objectives (SLOs) for latency, errors, and groundedness for a short window.
8. **Full rollout or auto-rollback** — if the canary is healthy, traffic ramps to 100%. If it breaches an SLO, traffic reverts to the previous revision automatically. No bad release sits in front of all users while someone investigates.

The three workflow files below implement these stages. The stage names above are what matters; the filenames are just where the logic lives.

### The three workflows

**`pr-checks.yml` — automated checks and the evaluation gate (stages 3–4).** It runs lint, unit tests, and a subset evaluation on whatever changed. It logs in to Azure using OpenID Connect (OIDC) federated login — GitHub gets a short-lived token from Azure, so there are **no stored keys or secrets** in the repository.

```yaml
name: pr-checks
on: { pull_request: { paths: ["usecases/**","platform/**","models.yaml"] } }
permissions: { id-token: write, contents: read }   # OIDC, no stored keys
jobs:
  test-and-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2                        # federated login to Azure
        with: { client-id: ${{ vars.AZ_CLIENT_ID }}, tenant-id: ${{ vars.AZ_TENANT_ID }},
                subscription-id: ${{ vars.AZ_SUB_ID }} }
      - run: pip install -r requirements.txt
      - run: pytest tests/                          # unit / contract
      - run: python platform/evaluators/run.py --subset changed --fail-under baseline
        #     ^ runs Ragas + DeepEval + tool_selection on changed prompts/agents;
        #       exits non-zero (blocks merge) if a metric drops past its baseline
```

**The evaluation gate is the important part.** Every change triggers this workflow. The changed artifact is scored against the golden dataset, and if any metric drops below its baseline threshold, the step exits non-zero and the merge is blocked. Quality is checked mechanically before anything can ship, not spot-checked by hand afterwards.

**`eval-full.yml` — the full golden-set run (stage 5).** The pull-request check runs only the affected subset to stay fast. On merge to `main`, and on a nightly schedule, we run the complete golden dataset across all metrics. This catches regressions the subset run would miss and keeps a running record of quality over time.

```yaml
name: eval-full
on:
  push: { branches: [main] }
  schedule: [{ cron: "0 2 * * *" }]     # nightly
permissions: { id-token: write, contents: read }
jobs:
  full-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with: { client-id: ${{ vars.AZ_CLIENT_ID }}, tenant-id: ${{ vars.AZ_TENANT_ID }},
                subscription-id: ${{ vars.AZ_SUB_ID }} }
      - run: pip install -r requirements.txt
      - run: python platform/evaluators/run.py --full --report dashboards/eval-latest.json
```

**`deploy.yml` — promotion gates, canary, and automatic rollback (stages 6–8).** Deployment moves through GitHub Environments: `dev` is automatic, `test` requires a reviewer, and `prod` requires a reviewer and a passing full evaluation. A production release goes out as a canary — a new Container Apps revision taking 10% of traffic — and is watched against SLOs for latency, errors, and groundedness. If healthy, traffic goes to 100%; if not, it reverts automatically.

```yaml
name: deploy
on: { push: { branches: [main] } }
permissions: { id-token: write, contents: read }
jobs:
  dev:  { environment: dev,  ... }                  # auto
  test: { environment: test, needs: dev, ... }      # requires reviewer (GitHub Environments)
  prod:
    environment: prod                               # requires reviewer + passes eval-full
    needs: test
    steps:
      - run: az containerapp revision copy ...       # new revision at 10% traffic (canary)
      - run: python ops/watch.py --for 15m --slo latency,errors,groundedness
      - run: az containerapp ingress traffic set ... # 100% if healthy, else revert (rollback)
```

The required-reviewer step on `test` and `prod` is a GitHub Environments protection rule, so it is enforced by the platform, not by convention.

## What changes

Today: prompts and agent logic live inside code files; there is no evaluation in the pipeline; deployment does not distinguish an LLM change from any other change. Our setup: prompts and agents become reviewed artifacts under `CODEOWNERS`, every change passes an evaluation gate before merge, and production releases are canaried with automatic rollback. The migration step is small — move the existing prompt text into `usecases/apix/prompts/`, stand up `platform/` once, and add the three workflows; the branching and review habits the teams already have carry straight over.

With the backbone in place, we onboard the remaining components one by one — prompt management next.
