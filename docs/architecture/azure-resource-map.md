# Azure Resource Map

Every Azure resource authored across this platform's components, its SKU, and its actual status. "Authored" means a Bicep template exists and compiles (`az bicep build`, checked in CI); it does not mean the resource exists in a live Azure subscription. Nothing in this platform has been deployed as of this writing — see each component's README for the exact `az deployment group create` command to run when ready.

| Component | Resource | Type | SKU / Tier | Status |
|---|---|---|---|---|
| 01 Repo & Foundation | Resource Group | `Microsoft.Resources/resourceGroups` | n/a | Authored, not deployed |
| 01 Repo & Foundation | User-Assigned Managed Identity | `Microsoft.ManagedIdentity/userAssignedIdentities` | n/a | Authored, not deployed |
| 03 Model Management | Azure OpenAI account + deployments | `Microsoft.CognitiveServices/accounts` (kind `OpenAI`) | S0 | Authored, not deployed |
| 05 Observability | Log Analytics workspace | `Microsoft.OperationalInsights/workspaces` | PerGB2018 | Authored, not deployed |
| 05 Observability | Application Insights (workspace-based) | `Microsoft.Insights/components` | n/a | Authored, not deployed |
| 06 Guardrails | Content Safety account | `Microsoft.CognitiveServices/accounts` (kind `ContentSafety`) | S0 | Authored, not deployed; optional — only if a usecase enables it |
| 07 Data & Tools | Azure AI Search service | `Microsoft.Search/searchServices` | basic | Authored, not deployed |
| 07 Data & Tools | Azure AI Speech account | `Microsoft.CognitiveServices/accounts` (kind `SpeechServices`) | S0 | Authored, not deployed |
| 10 Serving & Hosting | Container Apps managed environment | `Microsoft.App/managedEnvironments` | n/a | Authored, not deployed |
| 10 Serving & Hosting | Container App | `Microsoft.App/containerApps` | 0.5 vCPU / 1Gi, min 1 / max 3 replicas | Authored, not deployed; placeholder public image until a real one is built |
| 11 Feedback Loop | Storage Account (Blob) | `Microsoft.Storage/storageAccounts` | Standard_LRS | Authored, not deployed |
| 12 FinOps | Budget | `Microsoft.Consumption/budgets` | n/a | Authored, not deployed; whether current access permits creation is unconfirmed (see ADR 0014) |
| 12 FinOps | Cost export | `Microsoft.CostManagement/exports` | n/a | Authored, not deployed; writes to an existing Storage Account (e.g. component 11's), not a new one |

## Not yet an Azure resource
- Key Vault — deferred entirely per ADR 0001; no Bicep authored
- Any RBAC role assignment — every one is queued in the Phase 0 Permission Request Queue (`docs/checklist/BUILD-CHECKLIST.md`), tracked in `docs/architecture/permissions-log.md`
- Any container registry / pushed image — blocked on Entra ID access for CI/CD's (09) deployment job (ADR 0012)

Update this table whenever a component's infra changes, and update the Status column the moment a deployment actually happens — "authored" and "deployed" must never be conflated here.
