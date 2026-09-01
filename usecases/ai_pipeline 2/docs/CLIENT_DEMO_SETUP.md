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

| # | Service | Required? | Auth (Contributor-friendly) | Feeds `.env` |
|---|---------|-----------|------------------------------|--------------|
| 1 | **Azure OpenAI** (AI Foundry) | ✅ Minimal | API key | `REASONING_MODEL_*` |
| 2 | **Storage Account (Blob)** | ✅ Minimal | Account key / conn string | `SALES_STORAGE_*`, `AFNI_FILESTORE_CONNSTRING`, `SALES_*_CONTAINER` |
| 3 | **Azure SQL Database** | ⬜ Optional | Entra admin *or* SQL auth | `APP_AZURE_SQL_*` |
| 4 | **Application Insights** (+ Log Analytics) | ⬜ Optional | Connection string | `APPLICATIONINSIGHTS_CONNECTION_STRING` |
| 5 | **Azure AI Content Safety** | ⬜ Optional | API key | `AZURE_CONTENT_SAFETY_*` |

> **Minimum to run the pipeline end-to-end = #1 + #2.** With just those you can run
> `denoise → analysis → summary`. #3 adds `individual_metrics` + `kpi`. #4/#5 add the
> LLMOps observability-in-Azure and cloud content-safety options (both have local
> alternatives, so they're never blockers for a demo).

---

### 2.1 Azure OpenAI (AI Foundry) — **required**
The LLM every pipeline step calls.

**Portal**
1. Portal → *Create resource* → search **Azure OpenAI** → Create.
2. Subscription + your **RG**, Region = `$LOC`, name `<openai-name>`, pricing tier `Standard S0`.
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
az sql db create -g "$RG" -s "<sqlserver>" -n "<db>" --service-objective S0
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

## 8. Troubleshooting
- **`resolve ... not provisioned` / model 404:** your endpoint's deployment name must
  match `REASONING_MODEL_DEPLOYMENT`. Alias routing falls back to this env value unless
  you provision `reason`/`bulk` in `models.yaml`.
- **Auth errors on SQL:** set the Entra admin (2.5) and `az login`, or skip the SQL steps.
- **UI blank / fetch error:** run from `ui/` with `npm run dev`; confirm
  `public/sample-data.json` exists and is valid JSON.
- **Cost is $0:** expected until real rates are in `pricing.yaml`.
- **Platform import warnings in logs:** harmless — the integration is fail-open and the
  pipeline still runs; check `LLMOPS_PLATFORM_ROOT` if you moved the platform folder.
