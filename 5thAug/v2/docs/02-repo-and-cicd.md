# Source Control & CI/CD (Component #1)

This is the backbone and the first thing we set up. Continuous Integration / Continuous Deployment (CI/CD) plus source control is component #1 for a reason: every other component — prompts, models, evaluation, observability, guardrails — lands in this repository and flows through these workflows. Once the backbone is in place, we onboard the rest one at a time.

## Today

The APIX and Hiring code is already on GitHub. There are pull requests, reviews, and some deployment automation. This is a real starting point, and we are not replacing it. What is missing is the LLMOps-specific structure: prompts and agent definitions are buried inside application code rather than living as reviewable artifacts, and there is no evaluation step in the pipeline — a change to a prompt or a model ships like any other code change, with unit tests at best and no check on output quality.

## Our setup

### One monorepo

Everything lives in one repository, with one subfolder per use case inside `prompts/`, `agents/`, and `evals/`. The shared machinery under `src/common/` is written once and reused by every use case.

```
llmops-platform/                      # one monorepo; one subfolder per use case inside prompts/agents/evals
├── prompts/
│   └── apix/
│       ├── dimension-sales.prompt.yaml
│       └── coaching-report.prompt.yaml
├── agents/
│   └── apix/
│       └── pipeline.agent.yaml       # the pipeline: ordered steps, each -> a prompt + tools
├── evals/
│   └── apix/
│       ├── golden.telesales.jsonl    # golden dataset (per program)
│       ├── golden.wcc.jsonl
│       └── evaluators.yaml           # which metrics/evaluators run, thresholds
│   └── tool_selection.py             # custom Python evaluator (agent/tool behaviour)
├── src/
│   ├── pipelines/apix/run.py         # the pipeline runtime
│   └── common/
│       ├── prompt_loader.py          # loads prompt by id + label
│       ├── model_router.py           # resolves task alias -> deployment (reads models.yaml)
│       └── tracing.py                # OpenTelemetry spans (model/tool/agent)
├── models.yaml                       # task-alias -> Azure OpenAI deployment, per environment
├── .github/
│   ├── CODEOWNERS                    # /prompts and /agents require review
│   └── workflows/
│       ├── pr-checks.yml             # lint + unit + eval-subset gate on PR
│       ├── eval-full.yml             # full golden-set run on merge / nightly
│       └── deploy.yml                # OIDC login, gated envs, canary, rollback
├── infra/                            # Bicep (Container Apps, APIM, AI Search, Cosmos, etc.)
└── dashboards/                       # dashboard + alert definitions as code
```

Folder by folder:

- **`prompts/`** — one YAML file per prompt, grouped by use case (`apix/`). This is the source of truth for prompt text. Covered in detail in the prompt management document.
- **`agents/`** — the pipeline definition: the ordered steps, and for each step which prompt and which tools it uses. This is where the shape of a use case is described.
- **`evals/`** — the golden datasets (one JSON Lines file per program), the `evaluators.yaml` that says which metrics run at what thresholds, and `tool_selection.py`, a custom evaluator for agent and tool behaviour.
- **`src/pipelines/<use_case>/run.py`** — the runtime that executes the pipeline for a use case.
- **`src/common/`** — the shared code every use case reuses: `prompt_loader.py` (loads a prompt by id and label), `model_router.py` (resolves a task alias to an Azure deployment), and `tracing.py` (emits the OpenTelemetry spans).
- **`models.yaml`** — the single place a task maps to a model, per environment.
- **`.github/`** — `CODEOWNERS` and the three workflows.
- **`infra/`** — the Azure infrastructure as Bicep (Container Apps, APIM, AI Search, Cosmos DB, and so on).
- **`dashboards/`** — dashboard and alert definitions kept as code, so monitoring changes are reviewed like everything else.

### Branching and CODEOWNERS

We use short-lived feature branches with pull requests into `main`. `main` is protected: no direct pushes, and merges require a passing `pr-checks` run and at least one review.

`CODEOWNERS` puts a named reviewer requirement on `/prompts` and `/agents`. A change to a prompt or a pipeline step cannot merge without sign-off from the owner of that area — usually a subject-matter expert (SME) or the pipeline owner, not just any engineer. This is what makes prompt and agent changes first-class, reviewable artifacts instead of edits hidden inside a larger code diff.

### The three workflows

**`pr-checks.yml` — the quality gate on every pull request.** It runs lint, unit tests, and a subset evaluation on whatever changed. It logs in to Azure using OpenID Connect (OIDC) federated login — GitHub gets a short-lived token from Azure, so there are **no stored keys or secrets** in the repository.

```yaml
name: pr-checks
on: { pull_request: { paths: ["prompts/**","agents/**","src/**","evals/**"] } }
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
      - run: python evals/run.py --subset changed --fail-under baseline
        #     ^ runs Ragas + DeepEval + tool_selection on changed prompts/agents;
        #       exits non-zero (blocks merge) if a metric drops past its baseline
```

**The evaluation gate is the important part.** Every change — a prompt edit, a model swap in `models.yaml`, a new agent step — triggers this workflow. The changed artifact is scored against the golden dataset, and if any metric drops below its baseline threshold, the step exits non-zero and the merge is blocked. Quality is checked mechanically before anything can ship, not spot-checked by hand afterwards.

**`eval-full.yml` — the full golden-set run.** The pull-request check runs only the affected subset to stay fast. On merge to `main`, and on a nightly schedule, we run the complete golden dataset across all metrics. This catches regressions the subset run would miss and keeps a running record of quality over time.

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
      - run: python evals/run.py --full --report dashboards/eval-latest.json
```

**`deploy.yml` — gated environments, canary, and automatic rollback.** Deployment moves through GitHub Environments: `dev` is automatic, `test` requires a reviewer, and `prod` requires a reviewer and a passing full evaluation. A production release goes out as a canary — a new Container Apps revision taking 10% of traffic — and is watched against service-level objectives (SLOs) for latency, errors, and groundedness. If healthy, traffic goes to 100%; if not, it reverts automatically.

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

Today: prompts and agent logic live inside code files; there is no evaluation in the pipeline; deployment does not distinguish an LLM change from any other change. Our setup: prompts and agents become reviewed artifacts under `CODEOWNERS`, every change passes an evaluation gate before merge, and production releases are canaried with automatic rollback. The migration step is small — move the existing prompt text into the repository structure and add the three workflows; the branching and review habits the teams already have carry straight over.

With the backbone in place, we onboard the remaining components one by one — prompt management next.
