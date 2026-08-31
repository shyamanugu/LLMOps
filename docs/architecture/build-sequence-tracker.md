# Build Sequence Tracker

Source of truth for "what's done, what's next." Component folder numbers (`01`–`14`) are fixed labels, not the build order — the build order is the leftmost column here. Update this file the moment a component's status changes; do not rely on chat history to know where things stand.

| Seq # | Component | Folder | Status | Notes |
|---|---|---|---|---|
| 1 | Repo & Foundation | `01-repo-foundation` | ✅ Done (code) | See ADR 0001, 0002. Not yet deployed to Azure. |
| 2 | Model Management | `03-model-management` | ✅ Done (code) | See ADR 0003. Not yet deployed to Azure. Package restructured under `src/model_management/` per ADR 0004. |
| 3 | Orchestration | `08-orchestration` | ✅ Done (code) | See ADR 0005. Library only, no service deployed — deployment path documented in its README. Awaiting usecase code from you to reconcile against this engine's Step/Pipeline shape. |
| 4 | Prompt Management | `02-prompt-management` | ✅ Done (code) | See ADR 0006. Git-backed YAML storage, Foundry deferred (RBAC gap). Wired into Orchestration's `ModelStep` via `prompt_name`/`prompt_registry`; also fixed a pre-existing missing `tests/__init__.py` in 08 while wiring it. Not yet deployed (nothing to deploy — no Azure resource). |
| 5 | Data & Tools | `07-data-tools` | ⬜ Not started | |
| 6 | Evaluation Gate | `04-evaluation-gate` | ⬜ Not started | |
| 7 | Guardrails | `06-guardrails` | ⬜ Not started | |
| 8 | Observability | `05-observability` | ⬜ Not started | |
| 9 | Feedback Loop | `11-feedback` | ⬜ Not started | |
| 10 | CI/CD | `09-cicd` | ⬜ Not started | |
| 11 | Serving & Hosting | `10-serving-hosting` | ⬜ Not started | |
| 12 | FinOps | `12-finops` | ⬜ Not started | |
| 13 | Governance & Onboarding | `13-governance-onboarding` | ⬜ Not started | |
| 14 | Security & Compliance | `14-security-compliance` | ⬜ Not started | |

## Status legend
- ⬜ Not started
- 🔶 In discussion (description proposed, awaiting confirmation before any file is written)
- 🔷 In progress (confirmed, files being written)
- ✅ Done (code) — code/config authored and README accurate to what was built. **This does not mean it exists in Azure.** Actual deployment is a manual step, run via the `az` commands in that component's README, done by you when ready.
- ☁️ Deployed — the "done (code)" component has actually been provisioned in a live Azure subscription. Nothing has reached this state yet.
