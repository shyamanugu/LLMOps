# Governance & Onboarding

## What this is
The mechanism Phase 3's reusability proof (`docs/checklist/BUILD-CHECKLIST.md`) will actually be measured against: a copyable usecase scaffold, a step-by-step onboarding runbook, and a living matrix of what's inherited from the platform versus what a usecase must define itself. This component doesn't onboard a usecase — it's what makes onboarding usecase #2 with zero platform code changes possible to attempt in the first place.

## Where the real scaffold lives
`usecases/_template/` at the repo root, not inside this component's folder — usecases are siblings of `platform/`, not nested under it, since they consume the platform rather than being part of it. This component's own `templates/` folder is intentionally empty; it exists per the original skeleton but the real deliverable is at the repo-root path above, the same "real file lives elsewhere per a structural constraint" pattern already used for CI/CD (09)'s `.github/workflows/ci.yml`.

## What's in the scaffold
```
usecases/_template/
├── README.md                      # quick file-by-file map of what to change
├── prompts/example_prompt.yaml     # placeholder, matches Prompt Management's schema, references a real shared fragment
├── golden_dataset.jsonl            # placeholder, matches Evaluation Gate's schema
├── pipeline.py                     # builds a real Pipeline via Orchestration + Prompt Management — verified to actually construct and render
├── serving_entrypoint.py           # registers that pipeline into Serving & Hosting's app — verified to actually import and build an app
├── config/
│   ├── guardrail_policy_snippet.yaml   # paste into 06's config/guardrails.yaml
│   ├── gate_threshold_snippet.yaml      # paste into 04's config/gates.yaml
│   └── client_index_snippet.yaml        # paste into 07's config/clients.yaml, if using retrieval
└── requirements.txt
```
`pipeline.py` and `serving_entrypoint.py` are not just illustrative snippets — both were run and verified during this build: `build_pipeline()` actually constructs a real `orchestration.pipeline.Pipeline`, resolves `example_prompt.yaml`, and expands its `{{fragment:safety_preamble}}` reference against Prompt Management's real shared fragment directory; `serving_entrypoint.py`'s relative import actually resolves and builds a real FastAPI app. A first draft of `pipeline.py` didn't wire the shared-fragments directory and failed exactly the way a usecase author copying it would have hit — fixed before this was documented as working.

## The onboarding runbook and the two supporting docs
- `docs/architecture/onboarding-runbook.md` — the numbered steps, and an explicit definition of what would count as failing the reusability test (any edit to `platform/services/**/src/`)
- `docs/architecture/inherited-vs-defined.md` — per-component breakdown of what's inherited vs. usecase-defined, kept current as components change
- `docs/architecture/reusability-scorecard.md` — a template, deliberately left unfilled; it gets real numbers only when usecase #2's onboarding is actually attempted (Phase 3), not estimated in advance

## What this component does not do
It does not onboard usecase #1 or usecase #2 — no usecase has been supplied yet (see this session's earlier note that usecase code is expected later, to reconcile against Orchestration's `Step`/`Pipeline` shape). Building the scaffold and runbook now is buildable and provable independent of having a real usecase; actually running Phase 3's proof is not, and isn't faked here with placeholder numbers.

## Prerequisites
None — this component has no Azure resource and no Python package requiring installation of its own; `usecases/_template/` reuses whichever platform components a real usecase's copy ends up needing.

## Dependencies
- Depends on: every platform component whose config or mechanism a usecase might use (02, 03, 04, 05, 06, 07, 08, 10) — indirectly, through what the scaffold demonstrates wiring
- Depended on by: Phase 3's reusability proof, whenever it's actually attempted

## Cost notes
None — no Azure resource, no deployment.
