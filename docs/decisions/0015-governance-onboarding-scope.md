# ADR 0015: Governance & Onboarding — verified scaffold, unfilled scorecard

## Status
Accepted

## Context
Phase 3 of this platform's build plan (`docs/checklist/BUILD-CHECKLIST.md`) is explicitly "the actual product acceptance test": onboard a second usecase using only new prompts, new pipeline config, new golden dataset, and new data-source config — zero changes to platform code. That test can't actually be run yet (no second usecase has been supplied), but the mechanism it will be run against — a scaffold to copy, a runbook to follow, a matrix of what's inherited vs. defined — is buildable and verifiable now, independent of having a real usecase.

## Decision
1. **The scaffold lives at `usecases/_template/`, at the repo root**, not inside `platform/services/13-governance-onboarding/` — usecases consume the platform, they aren't part of it, mirroring the directory-separation reasoning already used for CI/CD's workflow file (ADR 0012).
2. **The scaffold's `pipeline.py` and `serving_entrypoint.py` were actually run, not just written.** A first draft of `pipeline.py` omitted wiring Prompt Management's shared-fragments directory; `example_prompt.yaml`'s `{{fragment:safety_preamble}}` reference failed with `FragmentNotFoundError` the moment it was actually rendered. This is exactly the kind of mistake a real usecase author copying the template would hit, and finding it now — before any real usecase copies this — is the entire value of verifying a template rather than trusting it by inspection.
3. **`docs/architecture/reusability-scorecard.md` is created as an explicitly unfilled template.** Its rows (files changed, time to onboard, % reused vs. net-new) require an actual usecase #2 attempt to populate honestly; inventing plausible-looking numbers now would misrepresent something that hasn't happened as though it had, the same violation the "authored vs. deployed" distinction has guarded against since ADR 0001.
4. **`docs/architecture/inherited-vs-defined.md` is filled in now**, based on what's actually been built across components 01–12 — unlike the scorecard, this doesn't require a real usecase to be accurate as of today; it's a direct summary of existing components' READMEs, correctable once Phase 3 reveals where the summary was wrong.

## Alternatives Considered
- **Writing `pipeline.py`/`serving_entrypoint.py` as pure prose/pseudocode instead of real, importable Python**: rejected — a template that can't actually be run can't be verified, and this build's standing practice (every component's tests actually run before its README claims they pass) applies here too, even though this component has no formal test suite.
- **Pre-filling the reusability scorecard with estimated numbers** ("expect roughly X% reuse"): rejected — it would misrepresent a projection as a measurement, undermining the scorecard's entire purpose as evidence for "the pitch to leadership" (the checklist's own words for what this number is for).
- **Placing the scaffold inside `platform/services/13-governance-onboarding/templates/`** (the pre-existing empty skeleton folder): rejected — usecases are meant to sit alongside `platform/`, not nested inside a specific component's folder, and discoverability matters more for something meant to be copied by whoever onboards the next usecase.

## Consequences
- Whoever attempts usecase #2's onboarding starts from a scaffold that's already been proven to construct and render correctly, not just to look plausible.
- The reusability scorecard staying empty is itself informative — it signals Phase 3 hasn't happened yet, rather than silently implying (via placeholder numbers) that it has.
- `inherited-vs-defined.md` is a snapshot, not a guarantee — it will need correcting the moment a real usecase's onboarding reveals something the summary got wrong or missed.

## Revisit When
- Usecase #2's onboarding is actually attempted — fill in `reusability-scorecard.md` with real measurements, and correct `inherited-vs-defined.md` against whatever it actually took.
- A platform gap is found during a real onboarding attempt — fix it generically in the relevant platform component, document it in the scorecard's "Platform gaps found" section, and never patch it as a usecase-specific workaround (per the runbook's explicit definition of what would fail the reusability test).
