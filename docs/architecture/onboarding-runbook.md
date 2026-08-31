# Onboarding a New Usecase

The reusability acceptance test for this platform (`docs/checklist/BUILD-CHECKLIST.md`, Phase 3) is: onboarding usecase #2 requires **zero changes to `platform/services/**`**. Every step below either creates files under `usecases/<name>/` or adds a small, additive config entry to a platform component's config file — never edits platform code.

## Steps
1. **Copy the scaffold**: `cp -r usecases/_template usecases/<name>`
2. **Author prompts**: replace `prompts/*.yaml` with real prompts, following Prompt Management's (02) schema. Reference shared fragments (`platform/services/02-prompt-management/prompts/shared/`) instead of re-writing common phrasing — see `usecases/_template/pipeline.py` for how a usecase registers that directory alongside its own.
3. **Author a golden dataset**: replace `golden_dataset.jsonl` with real curated cases, following Evaluation Gate's (04) schema (`id`, `input`, `expected`/`rubric`/`output_schema`, `evaluator`).
4. **Wire the pipeline**: edit `pipeline.py`, building real `ModelStep`s (and any Data & Tools tools, Guardrails, tracer) for this usecase's actual logic.
5. **Add config entries** (all additive — new keys, never edits to another usecase's existing entry):
   - `platform/services/06-guardrails/config/guardrails.yaml` — paste `config/guardrail_policy_snippet.yaml`'s block under `usecases:`
   - `platform/services/04-evaluation-gate/config/gates.yaml` — paste `config/gate_threshold_snippet.yaml`'s block under `usecases:` (optional — omitting it uses the platform default of 100%)
   - `platform/services/07-data-tools/config/clients.yaml` — only if this usecase uses retrieval; paste `config/client_index_snippet.yaml`'s block under `environments.<env>.clients`, then run `scripts/provision_client_index.py`
6. **Wire serving**: adapt `serving_entrypoint.py` if `pipeline.py`'s function signature changed; this becomes the real container image's entrypoint (see `platform/services/10-serving-hosting/README.md`).
7. **Run Evaluation Gate locally** against the golden dataset before considering any prompt/pipeline change safe to ship — `EvaluationGate.run(usecase=..., cases=..., system_under_test=...)`.
8. **Deploy**: manual today, via each platform component's README "Setup" section; automated once CI/CD (09)'s deployment job exists (blocked on Entra ID access — see `docs/decisions/0012-cicd-scope.md`).

## What counts as a platform code change (and would fail the reusability test)
Editing any `.py` file under `platform/services/**/src/`. Adding a config *entry* (a new key under `usecases:` or `environments.<env>.clients`) is **not** a platform code change — it's exactly the mechanism ADRs 0006, 0007, 0008, and 0009 were each designed around. If onboarding a usecase ever requires touching platform source code, that's a platform gap: log it in `docs/architecture/reusability-scorecard.md`, fix it generically so every usecase benefits, never patch it usecase-specifically.

## See also
- `docs/architecture/inherited-vs-defined.md` — the living breakdown of what every usecase gets for free versus what it must supply
- `docs/architecture/reusability-scorecard.md` — filled in once usecase #2's onboarding is actually attempted (Phase 3), not before
