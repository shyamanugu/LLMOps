# AIA Pipeline — Client Demo Setup (Azure services, `.env`, and the UI)

**Audience:** whoever stands up the demo. This is self-contained — follow it top to
bottom. It covers (1) the Azure services to create with **Contributor at resource-group
level**, (2) the `.env` file, (3) running the pipeline, and (4) the React UI that shows
the output to the client.

> **You cannot deploy hosted infrastructure.** That's fine. The model here is:
> you *create a few Azure resources inside a resource group you already have* (that
> only needs RG-level Contributor), run the pipeline **from your laptop** against them,
> and present the results in a **React UI that also runs on your laptop**. Nothing is
> deployed as a public app.

---

## 0. Two demo tiers — pick based on time

| Tier | What you show | Azure needed | When |
|------|---------------|--------------|------|
| **A — UI only (fastest)** | The full dashboard on bundled realistic **sample** data | **None** | You just need to tell the story today |
| **B — Real run** | The dashboard on data the pipeline actually produced | Azure OpenAI + Storage (min.) | You want to prove it end-to-end |

Tier A needs only Node (Section 6). Tier B additionally needs Sections 2–5.

### Setup order at a glance (follow in this exact sequence for Tier B)

1. **Prerequisites** — Azure CLI / Portal access, Python 3.11+, Node 18+ (Section 1).
2. **Create Azure services manually** in the Portal — Azure OpenAI + a model
   deployment, then a Storage account + containers (Section 2.1, 2.2). Optional:
   SQL, App Insights, Content Safety (2.3–2.5). All are pay-as-you-go/consumption.
3. **`.env` setup** — `cp .env.example .env`, paste the endpoints/keys/containers
   you just created, set `AI_PIPELINE_MODE=real` (Section 3).
4. **Config changes** — set real per-token rates in `pricing.yaml`, and (optional)
   provision the `reason`/`bulk` model aliases in `models.yaml`; review the
   `ai_pipeline` guardrail policy and eval thresholds (Section 3.5).
5. **Install** the pipeline + platform (Section 4).
6. **Provide input data** — upload a `raw/<date>.parquet` (real transcripts, or
   the sample generator in Section 0.5).
7. **Run the steps one by one** — `denoise → analysis → summary` (→ `individual_metrics → kpi` if SQL) (Section 4).
8. **Show the output** — export the run and open the UI (Section 6); optionally
   deploy the container to Azure Container Apps (Section 8).

---

## 0.5 Where does the data come from? (provenance — read this)

**The UI's bundled `sample-data.json` is synthetic** — hand-authored realistic numbers so
you can demo with zero setup (Tier A). It is **not** from any database. The "sample data"
badge in the header marks this.

**The real pipeline is database-backed.** Its data path:

```
Azure Blob Storage                 Azure OpenAI              Azure Blob Storage        Azure SQL
raw/<date>.parquet  ──denoise──▶  (LLM cleans)  ──▶ denoised/  ──analysis──▶ analysis/  ──┐
 (call transcripts)                                                                        │
                                                                       summary/ ◀──summary─┘
                                                          individual_metrics + kpi ◀── Azure SQL (vzw.rep_pivoted,
                                                                                        coach hierarchy)
```

- **Input** = transcript rows in **Azure Blob Storage** (`raw` container), one parquet per
  day. **Coach/employee hierarchy** and **individual metrics** come from **Azure SQL**.
- **Output** = parquet in `denoised`/`analysis`/`summary` and per-employee JSON reports —
  those feed the UI via `ui/export_run.py`.
- **The `.env` already carries the real DB connectivity** for both: `SALES_STORAGE_*` /
  `AFNI_FILESTORE_CONNSTRING` (Blob) and `APP_AZURE_SQL_*` (SQL). Fill those in (Sections
  2.2 / 2.3) and the pipeline reads/writes live data.

**To run Tier B you need input in the `raw` container.** If you don't have production
transcripts to hand, generate a realistic sample parquet and upload it:

```bash
cd "usecases/ai_pipeline 2"
# writes into your raw container using .env Storage creds:
python -m ai_pipeline.tools.make_sample_raw --date 2025-08-28 --upload
# ...or write locally first to inspect, then upload however you prefer:
python -m ai_pipeline.tools.make_sample_raw --date 2025-08-28 --out ./2025-08-28.parquet
```

That generator writes the exact schema `denoise` expects (`full_text`, `contact_id`,
`EmployeeID`, `ProgramName`, optional `CoachID`/`CoachName`/`totalcalltime`/`totalholdtime`)
with twelve messy telesales transcripts the pipeline will clean, score, and summarise.

---

## 0.6 Mock vs Real mode (the switch)

The repo has one flag that decides whether it runs a **self-contained demo** or
**plugs into live data**:

```
AI_PIPELINE_MODE = mock | real      (default: mock)
```

| | `mock` (default) | `real` |
|---|---|---|
| Data source | generated / bundled sample | live Azure Blob + Azure SQL |
| Azure needed | none (Tier A) | Storage (+ SQL) filled in `.env` |
| UI badge | amber **● MOCK DEMO** | green **● LIVE DATA** |
| Set via | nothing (it's the default) | `AI_PIPELINE_MODE=real` in `.env` |

- **`mock`** is the default on purpose — nothing reaches for a live credential
  unless you opt in. Use it to demo instantly (the UI's `mode: "mock"` sample) and
  to generate a sample `raw` parquet (Section 0.5).
- **`real`** makes `main.py` read/write the live Azure backends; if you set it
  without Storage creds, the pipeline logs a clear warning up front. Exports from a
  real run are stamped `mode: "real"` so the UI shows the green **LIVE DATA** badge.

The flag is surfaced in code via `ai_pipeline/mode.py` (`runtime_mode()`,
`is_mock()`, `is_real()`) — a single source of truth you can branch on anywhere.

---

## 1. Prerequisites

- An **existing Azure resource group** where you have the **Contributor** role. (Creating
  the RG itself needs subscription rights — out of scope; ask your Azure admin to create
  the RG and grant you Contributor on it.)
- **Azure CLI** (`az`) logged in — `az login` — or use the Azure Portal (both shown below).
- **Python 3.11+** and **Node 18+** (Node 24 confirmed working) on your machine.
- Set these once so every `az` command targets the right place:
  ```bash
  az account set --subscription "<SUBSCRIPTION_ID>"
  RG="<your-resource-group>"
  LOC="eastus"     # pick a region that offers Azure OpenAI + your model
  ```

### What "Contributor at resource-group level" can and cannot do
- **CAN:** create/read/update/delete resources *inside the RG* (OpenAI, Storage, SQL,
  App Insights, Content Safety), read their keys/connection strings.
- **CANNOT:** create resource groups, assign RBAC roles (that needs *User Access
  Administrator*/*Owner*), or change subscription policy.
- **Consequence:** every service below is wired with **key / connection-string auth**
  (no role assignment required) so Contributor is sufficient — *except* Azure SQL's
  Entra (AAD) auth, which needs one server-admin step (Section 2.5) or you use SQL auth.

---

## 2. Azure services

### 2.0 Summary

| # | Service | Required? | Billing model (choose this tier) | Auth (Contributor-friendly) | Feeds `.env` |
|---|---------|-----------|----------------------------------|------------------------------|--------------|
| 1 | **Azure OpenAI** (AI Foundry) | ✅ Minimal | **Pay-as-you-go** (Standard S0 — per-token consumption) | API key | `REASONING_MODEL_*` |
| 2 | **Storage Account (Blob)** | ✅ Minimal | **Pay-as-you-go** (Standard, LRS — pay per GB + ops) | Account key / conn string | `SALES_STORAGE_*`, `AFNI_FILESTORE_CONNSTRING`, `SALES_*_CONTAINER` |
| 3 | **Azure SQL Database** | ⬜ Optional | **Serverless (consumption)** — General Purpose Serverless, auto-pause | Entra admin *or* SQL auth | `APP_AZURE_SQL_*` |
| 4 | **Application Insights** (+ Log Analytics) | ⬜ Optional | **Pay-as-you-go** (per-GB ingestion) | Connection string | `APPLICATIONINSIGHTS_CONNECTION_STRING` |
| 5 | **Azure AI Content Safety** | ⬜ Optional | **Pay-as-you-go** (Standard S0 — per-call) | API key | `AZURE_CONTENT_SAFETY_*` |
| 6 | **Azure Container Registry** | 🐳 Deploy only | **Pay-as-you-go** (Basic) | Admin user / az login | (deploy only) |
| 7 | **Azure Container Apps** | 🐳 Deploy only | **Consumption plan** (scale-to-zero, per-second) | az login | (deploy only) |

> **Everything above is consumption / pay-as-you-go** — no reserved capacity, no
> fixed monthly commitment. You pay only for tokens processed, GB stored, and
> container seconds used. For a demo the spend is negligible; scale-to-zero on
> Container Apps means the deployed job costs nothing while idle.
>
> **Create these manually in the Azure Portal** (this doc's primary path). The
> `az` CLI equivalents are given for reference/repeatability, but you never have
> to run a provisioning script — every resource is a few clicks in the Portal.
>
> **Minimum to run the pipeline end-to-end = #1 + #2.** With just those you can run
> `denoise → analysis → summary`. #3 adds `individual_metrics` + `kpi`. #4/#5 add the
> LLMOps observability-in-Azure and cloud content-safety options (both have local
> alternatives, so they're never blockers for a demo). #6/#7 are only for the
> optional container deployment in Section 9.

---

### 2.1 Azure OpenAI (AI Foundry) — **required**
The LLM every pipeline step calls.

**Portal**
1. Portal → *Create resource* → search **Azure OpenAI** → Create.
2. Subscription + your **RG**, Region = `$LOC`, name `<openai-name>`, pricing tier
   **Standard S0** (this is the pay-as-you-go, per-token consumption tier — there is
   no separate "consumption" SKU for Azure OpenAI; S0 *is* PAYG).
3. After it deploys → open it → **Model deployments** (or *Go to Azure AI Foundry portal*)
   → **Deploy model** → choose your chat model → set **deployment name** to the value you'll
   put in `REASONING_MODEL_DEPLOYMENT` (e.g. `gpt-5.4-nano`).
4. Resource → **Keys and Endpoint** → copy **Endpoint** and **KEY 1**.

**az CLI**
```bash
az cognitiveservices account create \
  --name "<openai-name>" --resource-group "$RG" --location "$LOC" \
  --kind OpenAI --sku S0 --custom-domain "<openai-name>"

az cognitiveservices account deployment create \
  --name "<openai-name>" --resource-group "$RG" \
  --deployment-name "gpt-5.4-nano" \
  --model-name "<model>" --model-version "<version>" \
  --model-format OpenAI --sku-capacity 10 --sku-name "Standard"

az cognitiveservices account show   --name "<openai-name>" -g "$RG" --query properties.endpoint -o tsv
az cognitiveservices account keys list --name "<openai-name>" -g "$RG" --query key1 -o tsv
```

**→ `.env`:** `REASONING_MODEL_ENDPOINT` = endpoint, `REASONING_MODEL_DEPLOYMENT` =
your deployment name, `REASONING_MODEL_APIKEY` = key.

**Gotchas:** the pipeline uses the OpenAI-compatible surface — the endpoint host is
enough (the app derives the `/openai/v1/` base URL). Deployment **name** (your label),
not the model id, is what goes in `REASONING_MODEL_DEPLOYMENT`. If model choice should be
centrally managed, also set the same deployment name under `reason`/`bulk` in
`platform/services/03-model-management/config/models.yaml` (optional — see the integration doc).

---

### 2.2 Storage Account (Blob) — **required**
Holds pipeline inputs (raw transcripts) and outputs (denoised / analysis / summary parquet).

**Portal**
1. *Create resource* → **Storage account** → your **RG**, name `<storageacct>` (3–24
   lowercase), region `$LOC`, redundancy `LRS` is fine.
2. After deploy → **Containers** → create: `raw`, `denoised`, `analysis`, `summary`,
   `coach-employee-hierarchy`.
3. **Access keys** → copy a **key** and the **connection string**.

**az CLI**
```bash
az storage account create -n "<storageacct>" -g "$RG" -l "$LOC" --sku Standard_LRS
KEY=$(az storage account keys list -n "<storageacct>" -g "$RG" --query "[0].value" -o tsv)
for c in raw denoised analysis summary coach-employee-hierarchy; do
  az storage container create --account-name "<storageacct>" --account-key "$KEY" -n "$c"
done
az storage account show-connection-string -n "<storageacct>" -g "$RG" -o tsv
```

**→ `.env`:** `SALES_STORAGE_ACCOUNT_NAME`, `SALES_STORAGE_ACCOUNT_KEY`,
`AFNI_FILESTORE_CONNSTRING` (connection string), and the five `SALES_*_CONTAINER` names.

**Gotchas:** the pipeline reads raw transcripts from the `raw` container as
`<YYYY-MM-DD>.parquet` with columns including `full_text`, `contact_id`, `EmployeeID`,
`ProgramName` (and optionally `CoachID`). See Section 4 for preparing a sample.

---

### 2.3 Azure SQL Database — *optional* (for `individual_metrics` + `kpi`)

**Portal:** *Create resource* → **SQL Database** → create a new **logical server**
(`<sqlserver>`), pick auth, create DB `<db>`. Under the **server → Networking**, allow
your client IP (or "Allow Azure services").

**az CLI**
```bash
az sql server create -n "<sqlserver>" -g "$RG" -l "$LOC" \
  --admin-user "<admin>" --admin-password "<StrongP@ssw0rd!>"
# Serverless = consumption billing (auto-pauses when idle, pay per vCore-second):
az sql db create -g "$RG" -s "<sqlserver>" -n "<db>" \
  --edition GeneralPurpose --compute-model Serverless \
  --family Gen5 --capacity 2 --auto-pause-delay 60
az sql server firewall-rule create -g "$RG" -s "<sqlserver>" \
  -n allow-my-ip --start-ip-address <your.ip> --end-ip-address <your.ip>
```

**→ `.env`:** `APP_AZURE_SQL_SERVER` = `<sqlserver>.database.windows.net`,
`APP_AZURE_SQL_DATABASE` = `<db>`, plus port/driver/timeouts (defaults are fine).

**Auth note (the one Contributor caveat):** the app authenticates with
`DefaultAzureCredential` (Entra token). To use that, set yourself as the server's
**Microsoft Entra admin** (SQL server → *Microsoft Entra ID* → Set admin — you can do
this as the server creator) and run `az login` as that identity. If you can't set an
Entra admin, this step (and only the `individual_metrics`/`kpi` steps) can be skipped for
the demo — run `--step denoise`, `--step analysis`, `--step summary` instead.

---

### 2.4 Application Insights — *optional* (only if `AI_PIPELINE_TRACER=azure`)
For shipping LLMOps traces to Azure Monitor. **You do not need this for the demo** — the
default `AI_PIPELINE_TRACER=jsonl` captures the same data to a local file (Section 5).

**az CLI**
```bash
az monitor log-analytics workspace create -g "$RG" -n "<law>" -l "$LOC"
WID=$(az monitor log-analytics workspace show -g "$RG" -n "<law>" --query id -o tsv)
az monitor app-insights component create --app "<appi>" -g "$RG" -l "$LOC" --workspace "$WID"
az monitor app-insights component show --app "<appi>" -g "$RG" --query connectionString -o tsv
```
**→ `.env`:** `APPLICATIONINSIGHTS_CONNECTION_STRING`, and set `AI_PIPELINE_TRACER=azure`.

---

### 2.5 Azure AI Content Safety — *optional* (only if you enable it in guardrails)
Cloud moderation for the guardrails layer. Off by default; the local regex PII/secret
guardrails work without it.

**az CLI**
```bash
az cognitiveservices account create -n "<contentsafety>" -g "$RG" -l "$LOC" \
  --kind ContentSafety --sku S0 --custom-domain "<contentsafety>"
az cognitiveservices account show --name "<contentsafety>" -g "$RG" --query properties.endpoint -o tsv
az cognitiveservices account keys list --name "<contentsafety>" -g "$RG" --query key1 -o tsv
```
**→ `.env`:** `AZURE_CONTENT_SAFETY_ENDPOINT`, `AZURE_CONTENT_SAFETY_API_KEY`. Then set
`azure_content_safety.enabled: true` for `ai_pipeline` in
`platform/services/06-guardrails/config/guardrails.yaml`.

---

## 3. Configure `.env`

```bash
cd "usecases/ai_pipeline 2"
cp ".env.example" ".env"        # .env is gitignored — safe for real secrets
```
Open `.env` and paste the values you copied in Section 2. For the **minimal** demo you
only need the Azure OpenAI and Storage blocks (+ `AI_PIPELINE_TRACER=jsonl`, already the
default). Leave optional blocks blank.

> Secrets live only in `.env` (ignored). `.env.example` (placeholders) is the committed
> template. Never put a real key in `.env.example`.

---

## 3.5 Config changes (LLMOps platform)

These are small edits to the platform's config-as-code YAML — the platform is under
`platform/services/` at the repo root. All optional for a first run, but do at least
the pricing one so cost tracking is real.

1. **Real cost tracking** — `platform/services/03-model-management/config/pricing.yaml`:
   set `input_per_1k` / `output_per_1k` for your deployment (the file already has a
   `gpt-5.4-nano` entry with `0.0` placeholders). Until you do, cost shows `$0`.
2. **Central model routing (optional)** —
   `platform/services/03-model-management/config/models.yaml`: set the `reason` and
   `bulk` aliases' `deployment:` to your real Azure deployment name(s) per environment.
   Left as `null`, the pipeline falls back to `REASONING_MODEL_DEPLOYMENT` from `.env`
   (so it works either way). Point `bulk` at a cheaper model to cut denoise cost.
3. **Guardrail policy (review)** —
   `platform/services/06-guardrails/config/guardrails.yaml` → `usecases.ai_pipeline`:
   PII is flagged (not blocked), secrets blocked. Adjust if your policy differs.
4. **Eval thresholds (optional)** —
   `platform/services/04-evaluation-gate/config/gates.yaml` → `usecases.ai_pipeline`:
   dev 0.8 / test 0.9 / prod 1.0. Tighten as your golden dataset grows.

---

## 4. Install & run the pipeline (Tier B)

```bash
cd "usecases/ai_pipeline 2"
python -m venv .venv && . .venv/Scripts/activate     # Windows Git Bash
pip install -e .
pip install -r requirements.txt
```
The LLMOps platform is picked up automatically from `../../platform/services/*/src`
(via `_platform_bootstrap.py`; override with `LLMOPS_PLATFORM_ROOT` if needed).

**Prepare a little input data:** upload one `raw/<YYYY-MM-DD>.parquet` with a few
transcript rows (columns `full_text`, `contact_id`, `EmployeeID`, `ProgramName`, optional
`CoachID`). Use a date you'll pass with `--date`.

**Run:**
```bash
# Full pipeline for one date (min. services cover denoise/analysis/summary):
python -m ai_pipeline.main --program telesales --date 2025-08-28 --step denoise
python -m ai_pipeline.main --program telesales --date 2025-08-28 --step analysis
python -m ai_pipeline.main --program telesales --date 2025-08-28 --step summary
# (with Azure SQL) add: --step individual_metrics  then  --step kpi
```
Outputs land in the `denoised` / `analysis` / `summary` containers. The run log ends with
a `RUN SUMMARY` including an `LLM usage | calls=… cost_usd=…` line (from the LLMOps
observability layer).

---

## 5. Observability without deploying (JSONL tracer)

Because you can't deploy Azure Monitor, keep the default **`AI_PIPELINE_TRACER=jsonl`**.
Every LLM call is recorded to `traces/trace.jsonl` (tokens, cost, latency, guardrail
flags, step, model). That file is what the UI exporter reads. (Cost shows `$0` until you
add real per-1k rates for your deployment in
`platform/services/03-model-management/config/pricing.yaml` — everything else is live.)

---

## 6. The demo UI (React) — Tier A & B

```bash
cd "usecases/ai_pipeline 2/ui"
npm install
npm run dev            # open the printed http://localhost:5173
```
Out of the box it shows a **realistic bundled sample** (`public/sample-data.json`) — this
is your **Tier A** demo, needs no Azure.

**Show your real run (Tier B):** after a pipeline run, generate the UI dataset and reload:
```bash
cd "usecases/ai_pipeline 2"
# download your summary per-employee JSON reports to a local folder first, then:
python ui/export_run.py \
  --trace-file traces/trace.jsonl \
  --summaries-dir ./summary_json \
  --program telesales --date 2025-08-28 \
  --out ui/public/sample-data.json
```
Or use the **"Load run…"** button in the UI header to open any exported `.json` without
restarting.

### What the UI shows
- **Header:** program / date / environment / model / run id (+ a "sample data" badge).
- **Pipeline flow:** denoise → analysis → summary → individual_metrics → kpi.
- **LLMOps panel:** LLM calls, tokens, cost, avg latency, guardrail flags, errors, and
  cost/latency by step — the platform value, made visible.
- **KPIs:** resolution rate, right-of-sell, escalations, etc.
- **Per-employee:** behavior scores, team comparison, the AI coaching reflection, top
  calls (intent/outcome/tags/excerpt), and escalations.

---

## 6.5 Run everything locally (no Docker) — mock & real via `.env`

Docker/Container Apps (Section 8) is one option. For a laptop demo you don't need it —
run the pipeline and the UI directly, and switch between mock and real with **one line
in `.env`**: `AI_PIPELINE_MODE=mock | real`.

### Option A — Mock demo, zero dependencies (fastest)
No Azure, no OpenAI key. Shows the bundled sample on the UI (green/amber badge reads
**MOCK DEMO**).
```bash
cd "usecases/ai_pipeline 2/ui"
npm install && npm run dev        # http://localhost:5173
```
That's the whole demo. (To regenerate the sample from the transcripts:
`python ui/make_sample_data.py`.)

### Option B — Run the real pipeline locally in MOCK mode (local files, no Azure Storage)
`AI_PIPELINE_MODE=mock` makes the pipeline read/write parquet on your **local disk**
(`AI_PIPELINE_LOCAL_DATA_DIR`, default `./data`) instead of Azure Blob. You only need an
LLM key (`REASONING_MODEL_*`) — no Storage/SQL account.
```bash
cd "usecases/ai_pipeline 2"
python -m venv .venv && . .venv/Scripts/activate
pip install -e . && pip install -r requirements.txt

# .env:  AI_PIPELINE_MODE=mock   +   REASONING_MODEL_* filled in
# 1) seed local input (writes ./data/raw/2025-08-28.parquet):
python -m ai_pipeline.tools.make_sample_raw --date 2025-08-28 --local
# 2) run the steps one by one (outputs land in ./data/denoised, ./data/analysis, ./data/summary):
python -m ai_pipeline.main --program telesales --date 2025-08-28 --step denoise
python -m ai_pipeline.main --program telesales --date 2025-08-28 --step analysis
python -m ai_pipeline.main --program telesales --date 2025-08-28 --step summary
# 3) build the UI dataset from the local run + traces, then show it:
python ui/export_run.py --trace-file traces/trace.jsonl \
  --summaries-dir ./data/summary --program telesales --date 2025-08-28 \
  --out ui/public/sample-data.json
cd ui && npm run dev
```
(`individual_metrics`/`kpi` still need Azure SQL — skip them in mock mode.)

### Option C — Run locally in REAL mode (live Azure)
Same commands as Option B, but set `AI_PIPELINE_MODE=real` and fill the Storage (+ SQL)
blocks in `.env`. Now `make_storage()` uses Azure Blob, so drop the `--local` flag and
upload input with `--upload` instead; the UI export shows the **LIVE DATA** badge.

| Path | `.env` `AI_PIPELINE_MODE` | Needs Azure Storage? | Needs LLM key? |
|------|---------------------------|----------------------|----------------|
| A — UI mock demo | mock | no | no |
| B — local pipeline run | mock | no (local disk) | yes |
| C — real pipeline run | real | yes | yes |

The switch is entirely in `.env` — no code change moves you between mock and real.

---

## 7. Suggested client walkthrough (5 minutes)
1. **Pipeline flow** — "Raw calls in, coaching intelligence out, five governed steps."
2. **LLMOps panel** — "Every model call is traced: tokens, cost, latency, and guardrail
   decisions — this is the AFNI platform wrapping the pipeline. PII is flagged, never
   dropped; secrets are blocked."
3. **KPIs + a coach's employee** — "100% of calls scored, not a QA sample; here's one
   agent's drivers, how they compare to team, and the AI's coaching reflection with
   evidence excerpts."
4. **Governance** — "Model choice, prompts, guardrail policy, and the eval gate are all
   config-as-code; a prompt change can't ship without passing the golden-dataset gate."

---

## 8. Deploy the pipeline: local Docker → Azure Container Apps

Your preferred path: **build the image locally**, push it to your registry, and run it
on **Azure Container Apps** (Consumption plan — scale-to-zero, pay-per-second). Because
the pipeline is a **batch job** (run per date/step, then exit), the natural fit is a
**Container Apps Job**, not an always-on app — but both are covered.

All resources here are consumption/pay-as-you-go and creatable manually in the Portal.
The `az` commands are given so you can copy-paste; do them in the Portal instead if you
prefer.

### 8.1 Build the image locally
The Dockerfile lives in the usecase but **must be built from the repo root** so the
LLMOps platform is in the build context:

```bash
cd /d/AFNI/LLMOps                         # repo root
docker build -f "usecases/ai_pipeline 2/Dockerfile" -t aia-pipeline:latest .

# smoke-test locally in mock mode (no Azure needed):
docker run --rm -e AI_PIPELINE_MODE=mock aia-pipeline:latest --program telesales --step summary
# or against real Azure using your .env:
docker run --rm --env-file "usecases/ai_pipeline 2/.env" \
  aia-pipeline:latest --program telesales --step summary --date 2025-08-28
```

### 8.2 Create an Azure Container Registry (Basic, PAYG) and push
**Portal:** *Create resource → Container Registry →* your RG, name `<acr>`, SKU **Basic**.
Then enable *Access keys → Admin user* (simplest for a demo).

```bash
az acr create -g "$RG" -n "<acr>" --sku Basic --admin-enabled true
az acr login -n "<acr>"
docker tag aia-pipeline:latest "<acr>.azurecr.io/aia-pipeline:latest"
docker push "<acr>.azurecr.io/aia-pipeline:latest"
```

### 8.3 Create the Container Apps environment (Consumption)
**Portal:** *Create resource → Container Apps →* it creates a **Container Apps
Environment** (workload profile: **Consumption**). Or:

```bash
az extension add --name containerapp --upgrade
az containerapp env create -g "$RG" -n "<cae-env>" -l "$LOC"   # Consumption by default
```

### 8.4a Deploy as a Container Apps **Job** (recommended for batch)
A Job runs to completion and stops — ideal for a per-date pipeline run, and it costs
nothing between runs.

```bash
az containerapp job create -g "$RG" -n "aia-pipeline-job" \
  --environment "<cae-env>" \
  --trigger-type Manual --replica-timeout 3600 --replica-retry-limit 1 \
  --image "<acr>.azurecr.io/aia-pipeline:latest" \
  --registry-server "<acr>.azurecr.io" \
  --cpu 1.0 --memory 2.0Gi \
  --args "--program" "telesales" "--step" "summary" "--date" "2025-08-28"

# set secrets + env (map your .env values):
az containerapp job secret set -g "$RG" -n "aia-pipeline-job" \
  --secrets openai-key="<key>" storage-key="<key>"
az containerapp job update -g "$RG" -n "aia-pipeline-job" \
  --set-env-vars AI_PIPELINE_MODE=real AI_PIPELINE_ENV=prod \
    REASONING_MODEL_ENDPOINT="<endpoint>" REASONING_MODEL_DEPLOYMENT="gpt-5.4-nano" \
    REASONING_MODEL_APIKEY=secretref:openai-key \
    SALES_STORAGE_ACCOUNT_NAME="<acct>" SALES_STORAGE_ACCOUNT_KEY=secretref:storage-key \
    SALES_RAW_CONTAINER=raw SALES_DENOISED_CONTAINER=denoised \
    SALES_ANALYSIS_CONTAINER=analysis SALES_SUMMARY_CONTAINER=summary

# run it now (and schedule later with --trigger-type Schedule --cron-expression "...")
az containerapp job start -g "$RG" -n "aia-pipeline-job"
```

To change the date/step, update `--args` (or start with `--args` overrides) and start again.

### 8.4b Deploy as a Container **App** (if you want an always-on service)
Only if you later wrap the pipeline in the platform's serving API
(`platform/services/10-serving-hosting`). For the batch pipeline as-is, prefer the Job.

```bash
az containerapp create -g "$RG" -n "aia-pipeline" \
  --environment "<cae-env>" \
  --image "<acr>.azurecr.io/aia-pipeline:latest" \
  --registry-server "<acr>.azurecr.io" \
  --cpu 1.0 --memory 2.0Gi --min-replicas 0 --max-replicas 1   # min 0 = scale to zero
```

### 8.5 Get the output out
The container writes results to your Azure Storage containers (same as a local run). To
refresh the **UI** from a container run, pull the summary JSON + `traces/trace.jsonl`
locally and run `ui/export_run.py` (Section 6), or point the exporter at the outputs you
downloaded from Blob.

---

## 9. Troubleshooting
- **`resolve ... not provisioned` / model 404:** your endpoint's deployment name must
  match `REASONING_MODEL_DEPLOYMENT`. Alias routing falls back to this env value unless
  you provision `reason`/`bulk` in `models.yaml`.
- **Auth errors on SQL:** set the Entra admin (2.5) and `az login`, or skip the SQL steps.
- **UI blank / fetch error:** run from `ui/` with `npm run dev`; confirm
  `public/sample-data.json` exists and is valid JSON.
- **Cost is $0:** expected until real rates are in `pricing.yaml`.
- **Platform import warnings in logs:** harmless — the integration is fail-open and the
  pipeline still runs; check `LLMOPS_PLATFORM_ROOT` if you moved the platform folder.
