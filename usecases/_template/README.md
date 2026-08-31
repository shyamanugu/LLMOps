# _template

Copy this folder to `usecases/<your-usecase-name>/` and adapt every file —
see `docs/architecture/onboarding-runbook.md` for the full step-by-step.

| File | What to do |
|---|---|
| `prompts/*.yaml` | Replace with this usecase's real prompts (Prompt Management schema — see `platform/services/02-prompt-management/README.md`) |
| `golden_dataset.jsonl` | Replace with this usecase's real curated test cases (Evaluation Gate schema — see `platform/services/04-evaluation-gate/README.md`) |
| `pipeline.py` | Replace the single demo Step with this usecase's real Steps |
| `serving_entrypoint.py` | Update the import if `pipeline.py`'s function name changes; otherwise usually no edit needed |
| `config/*_snippet.yaml` | Paste each block into the referenced platform component's config file, replacing the placeholder name |
| `requirements.txt` | Reference only the platform components this usecase's `pipeline.py` actually imports |

None of this requires editing anything under `platform/services/**` — that's the reusability acceptance test this whole platform was built to satisfy.
