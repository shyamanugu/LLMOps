# Setup Guide — standing up the LLMOps Platform

Step-by-step prose to stand the platform up from nothing. This mirrors `../checklist.html`
(the tick-box companion) but in narrative form so you understand *why* each step exists.
Every place that needs a client/tenant-specific value is also flagged in `../todo.html`.

Order matters: Azure resources -> secrets/identity -> GitHub OIDC + environments -> local
dev -> first eval run -> first deploy.

Prerequisites on your workstation: Azure CLI (`az`), a subscription with Contributor
rights, GitHub CLI (`gh`) or repo admin, Python 3.11+, Node 18+, Docker.

---

## 1. Provision Azure resources

Use the Bicep under `infra/` (`main.bicep` + `modules/*.bicep`, params in `params/*.json`).
Deploy per environment (`dev`, `test`, `prod`) into a resource group each.

```bash
az login
az group create -n rg-llmops-dev -l <region>
az deployment group create -g rg-llmops-dev \
  -f infra/main.bicep -p infra/params/dev.json
```

The deployment provisions:
- **Azure OpenAI** + model **deployments** for each alias (`reason`, `bulk`, `judge`,
  `voice`, `embed`). Record the deployment names — they go into `platform/models.yaml`.
- **Azure AI Search** (RAG index) — Basic tier for dev (indicative ~$74/mo).
- **Azure AI Document Intelligence** (file extraction).
- **Azure AI Content Safety** (guardrails: Prompt Shields, categories, groundedness).
- **Cosmos DB** (pipeline state + feedback) — serverless in dev.
- **Application Insights / Log Analytics** (traces, cost, metrics).
- **API Management** (gateway) — Basic/Standard as sized.
- **Container Apps environment** (hosts API + Console + runtime) and, optionally,
  **Functions** for event/scheduled triggers.
- **Key Vault** and a **user-assigned Managed Identity** attached to the Container Apps.

Confirm sizing/cost with the client (label figures "confirm at sizing").

## 2. Configure identity and secrets

- Grant the Managed Identity the least-privilege roles it needs: Cognitive Services OpenAI
  User (Azure OpenAI), Search Index Data Reader/Contributor, Cosmos DB data-plane role,
  Content Safety user, Key Vault Secrets User.
- Put any residual secret values in **Key Vault**; reference them from the Container App as
  Key Vault references (no keys in app settings). Endpoints (non-secret) can be plain
  Container App environment variables prefixed `LLMOPS_`.
- Do **not** create static API keys for production; Managed Identity is the auth path. Keys
  are dev-only.

## 3. Deploy the self-hosted Langfuse (optional but recommended)

Run Langfuse (MIT-licensed) inside the client network — a Container App + Postgres — so
LLM telemetry and prompt data stay in-tenant (indicative infra ~$50-150/mo). Record its
host and public/secret keys for `LLMOPS_LANGFUSE_*`. If you skip this initially, set
`LLMOPS_PROMPT_REGISTRY=git` and observability still flows to Application Insights.

## 4. GitHub: OIDC federated login + Environments

- Register a federated credential so GitHub Actions can log in to Azure without stored
  keys: create an Entra ID app/service principal (or use the Managed Identity federation),
  add a federated credential scoped to the repo/branch/environment, and grant it deploy
  rights on the resource groups.
- Set repository **variables** (not secrets): `AZ_CLIENT_ID`, `AZ_TENANT_ID`, `AZ_SUB_ID`.
- Create GitHub **Environments** `dev`, `test`, `prod`. Add **required reviewers** to
  `test` and `prod` (this is the promotion gate). `dev` deploys automatically.
- `CODEOWNERS` already requires review on `usecases/*/prompts` and `platform/`; confirm the
  owning team is set.
- The three workflows (`pr-checks`, `eval-full`, `deploy`) and `index-refresh` are in
  `.github/workflows/`. They use `id-token: write` for OIDC.

## 5. Local development via docker-compose

For a fully local loop (no Azure account needed — adapters degrade to mocks where a live
client is not wired):

```bash
cd infra
docker compose up --build
# API      -> http://localhost:8000/api/v1/health
# Console  -> http://localhost:5173
# Langfuse -> http://localhost:3000
```

Or run the pieces directly:

```bash
cd backend
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # set endpoints; leave keys blank for mocks/MI
uvicorn llmops.api.main:app --reload --port 8000

cd ../frontend
npm install && cp .env.example .env               # VITE_API_BASE=http://localhost:8000/api/v1
npm run dev
```

Point `LLMOPS_MODELS_CONFIG_PATH` and `LLMOPS_USECASES_DIR` at the repo's `platform/` and
`usecases/` (the defaults in `.env.example` already do this for the `backend/` working
directory).

## 6. First evaluation run (establish the baseline)

Before any deploy, run the gate to establish a baseline for a use case:

```bash
cd backend
# run a single pipeline locally to sanity-check wiring:
python pipelines_cli.py --usecase apix --input '{"transcript_id":"demo"}'
# run the evaluation gate against the golden set:
python evals/run.py --usecase apix --subset full --fail-under baseline
```

The first full run records the **baseline** scores; subsequent PRs are gated relative to
it, plus the absolute floors in `usecases/apix/evals/evaluators.yaml` (PII = 0, unsafe = 0,
groundedness minimum). Fix any wiring TODOs surfaced here (`todo.html`).

## 7. First deploy

- Push to a branch and open a PR. `pr-checks` runs lint + unit + the eval subset gate. Get
  CODEOWNER approval and merge.
- On merge, `eval-full` runs the full golden set. `deploy` then promotes:
  - **dev** automatically,
  - **test** after a reviewer approves (and eval-full passed),
  - **prod** after a reviewer approves — the new revision goes out at ~10% traffic
    (canary), `ops/watch` watches SLOs (latency, errors, groundedness) for ~15 minutes,
    then ramps to 100% if healthy or auto-rolls back.
- Verify in the Console: `/` dashboard (requests, p95 latency, cost/day, quality trend,
  guardrail events), `/evaluations` (the gate report), `/traces` (a trace tree), `/costs`.

## 8. Onboarding the next use case

Follow `workflows.md` section 5: copy `usecases/_template/`, fill `config/datasources.yaml`,
compose tools, generate prompts/agents/evals via `COPILOT_PROMPTS.md` + `copilot_prompts.py`,
add SME golden data + thresholds, tune guardrails, add dashboards, run the first eval, and
deploy. The Nth use case reuses all shared machinery.

## 9. Ongoing operations

- Reconcile `app.cost_usd` monthly against **Azure Cost Management** (the invoice).
- Keep the price table (`models/pricing.py`) current when deployments change.
- Refresh RAG indexes on schedule (`index-refresh`).
- Feed production feedback into golden data (`workflows.md` section 4).
