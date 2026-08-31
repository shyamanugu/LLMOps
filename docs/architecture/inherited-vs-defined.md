# Inherited vs. Defined

What a new usecase gets from the platform "for free" (inherited) versus what it must supply itself (defined), by component. This is the concrete answer to "what does onboarding usecase #2 actually require" — kept current as components change, corrected against reality once Phase 3's actual onboarding attempt happens (see `docs/architecture/reusability-scorecard.md`).

| Component | Inherited (platform-owned) | Defined (usecase-owned) |
|---|---|---|
| 01 Repo & Foundation | Naming convention, tagging schema, Managed Identity, resource group | Nothing |
| 02 Prompt Management | `PromptRegistry` mechanism, shared fragments | Actual prompt files, prompt directory |
| 03 Model Management | Alias resolution, provider adapters | Which alias to call (`model_alias` on a Step) |
| 04 Evaluation Gate | `EvaluationGate`, 3 evaluators, threshold mechanism | Golden dataset, `system_under_test` callable, per-usecase threshold override (optional) |
| 05 Observability | `Tracer` types, `compute_cost()`, backends | Which tracer to construct, wiring it into Steps/Pipeline |
| 06 Guardrails | 5 heuristic checks, `CompositeGuardrail`, `build_guardrail()` | Blocklist terms, per-usecase policy config entry |
| 07 Data & Tools | `RetrievalTool`, STT/TTS tools, `HttpApiTool`, per-client index isolation | Client config entry (if using retrieval), connector configs, actual documents to ingest |
| 08 Orchestration | `Pipeline`/`Step`/`State` engine | Actual `Step` instances — the pipeline's real logic |
| 09 CI/CD | Test/lint/Bicep-validate workflow | Its own tests, if any, under its own usecase folder |
| 10 Serving & Hosting | `create_app()`, `PipelineRegistry`, Container Apps Bicep | `serving_entrypoint.py` registering its real pipeline(s) |
| 11 Feedback Loop | `FeedbackEvent`, stores, `promote_to_golden_dataset()` | Where feedback actually gets collected (a UI, an agent tool) — not built by any component yet |
| 12 FinOps | Budget/export mechanism, tagging schema | Nothing usecase-specific — cost visibility is platform-wide |

Filled in as of the last component built (12-finops, at time of writing). Usecase #1 and #2's actual onboarding experience (Phase 3) will confirm or correct this table against reality, not just intent — expect this file to change once that happens.
