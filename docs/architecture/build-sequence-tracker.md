# Build Sequence Tracker

Source of truth for "what's done, what's next." Component folder numbers (`01`–`14`) are fixed labels, not the build order — the build order is the leftmost column here. Update this file the moment a component's status changes; do not rely on chat history to know where things stand.

| Seq # | Component | Folder | Status | Notes |
|---|---|---|---|---|
| 1 | Repo & Foundation | `01-repo-foundation` | ✅ Done (code) | See ADR 0001, 0002. Not yet deployed to Azure. |
| 2 | Model Management | `03-model-management` | ✅ Done (code) | See ADR 0003. Not yet deployed to Azure. Package restructured under `src/model_management/` per ADR 0004. |
| 3 | Orchestration | `08-orchestration` | ✅ Done (code) | See ADR 0005. Library only, no service deployed — deployment path documented in its README. Awaiting usecase code from you to reconcile against this engine's Step/Pipeline shape. |
| 4 | Prompt Management | `02-prompt-management` | ✅ Done (code) | See ADR 0006. Git-backed YAML storage, Foundry deferred (RBAC gap). Wired into Orchestration's `ModelStep` via `prompt_name`/`prompt_registry`; also fixed a pre-existing missing `tests/__init__.py` in 08 while wiring it. Not yet deployed (nothing to deploy — no Azure resource). |
| 5 | Data & Tools | `07-data-tools` | ✅ Done (code) | See ADR 0007. Per-client Search index (shared service), STT/TTS pipeline tools, generic HttpApiTool connector. Wired into Orchestration's `ToolRegistry`, closing the "Tools" seam. Not yet deployed — no Azure resource provisioned. |
| 6 | Evaluation Gate | `04-evaluation-gate` | ✅ Done (code) | See ADR 0008. Golden dataset + 3 evaluators (exact_match, schema, llm_judge) + threshold-based gate. `system_under_test` is a plain callable, no dependency on Orchestration. Not wired to CI/CD (09, doesn't exist yet) — plan documented in its README. Not yet deployed — no Azure resource of its own. |
| 7 | Guardrails | `06-guardrails` | ✅ Done (code) | See ADR 0009. 5 free heuristic checks (PII, blocklist, prompt injection, secret leak, max length) + optional Azure Content Safety check, combined via `CompositeGuardrail`. Wired into Orchestration's `ModelStep.guardrail`, closing that seam. Not yet deployed — Content Safety resource is optional and unprovisioned. |
| 8 | Observability | `05-observability` | ✅ Done (code) | See ADR 0010. StepEvent/PipelineEvent + NullTracer/InMemoryTracer/AzureMonitorTracer; compute_cost() reads component 03's pricing.yaml. Added `tracer` param to Orchestration's ModelStep/Pipeline — the one seam that needed genuinely new code in 08, not an existing parameter. Not yet deployed — Log Analytics/App Insights unprovisioned. |
| 9 | Feedback Loop | `11-feedback` | ✅ Done (code) | See ADR 0011. FeedbackEvent + 3 stores (InMemory/JsonlFile/AzureBlob) + promote_to_golden_dataset() as a data-format bridge to component 04 (no code import). No Orchestration change — feedback is collected out of band, not during a Step's run. Not yet deployed — Storage Account unprovisioned. |
| 10 | CI/CD | `09-cicd` | ✅ Done (code) | See ADR 0012. Real `.github/workflows/ci.yml`: test matrix (8 components, 79 tests), ruff lint, Bicep validation — no Azure credentials needed. Caught and fixed a real pre-existing Bicep scope bug in component 01, and 139 ruff findings across the tree. CD not built — blocked on Entra ID app registration; design documented, added to Phase 0 batch. |
| 11 | Serving & Hosting | `10-serving-hosting` | ✅ Done (code) | See ADR 0013. Generic FastAPI wrapper (`/healthz`, `POST /pipelines/{name}/run`) + PipelineRegistry, dispatches to real Orchestration Pipeline/State. Container Apps Bicep (env + app, canary traffic param) validated via `az bicep build`. No auth, no real image built/pushed — both blocked on Entra ID access, same as CI/CD (09). Not yet deployed. |
| 12 | FinOps | `12-finops` | ✅ Done (code) | See ADR 0014. Budget + Cost Export Bicep (validated), reference KQL query (unverified — no export has run). Distinct from Observability's LLM-token cost tracking — this is Azure infra billing. Whether Contributor can create a budget is unconfirmed; deployment attempt itself will answer it. No Python package (Bicep + query only, like 09). Not yet deployed. |
| 13 | Governance & Onboarding | `13-governance-onboarding` | ✅ Done (code) | See ADR 0015. `usecases/_template/` scaffold at repo root, actually run and verified (found + fixed a real fragment-wiring bug), onboarding runbook, inherited-vs-defined matrix filled in, reusability scorecard created unfilled (needs a real usecase #2 attempt). |
| 14 | Security & Compliance | `14-security-compliance` | ⬜ Not started | |

## Status legend
- ⬜ Not started
- 🔶 In discussion (description proposed, awaiting confirmation before any file is written)
- 🔷 In progress (confirmed, files being written)
- ✅ Done (code) — code/config authored and README accurate to what was built. **This does not mean it exists in Azure.** Actual deployment is a manual step, run via the `az` commands in that component's README, done by you when ready.
- ☁️ Deployed — the "done (code)" component has actually been provisioned in a live Azure subscription. Nothing has reached this state yet.
