# Decisions log

> Append-only. One dated line per decision — the choice and the reason. Never delete history; if a
> decision is reversed, add a new dated line that supersedes it.

- 2026-08-06 — The reusable layer is named `framework/` (not `platform/`) because `platform`
  shadows a Python standard-library module; the proposal deck still calls it "the platform".
- 2026-08-06 — The prompt registry is GitHub: prompts are versioned `.prompt.json` files in the
  repo, reviewed by pull request and gated by evaluation — not text buried in code.
- 2026-08-06 — Model choice is config, not code: app code calls a task alias
  (`reason`/`bulk`/`judge`/`embed`) resolved via `framework/models.json`. Swapping a model is a JSON
  change, never a code change.
- 2026-08-06 — Orchestration is sequential pipelines, not agent-to-agent: a use case is a list of
  steps `(name, fn(state) -> None)` run in order (`framework/pipeline.py`).
- 2026-08-06 — The project runs offline via mock mode: with no `AZURE_OPENAI_ENDPOINT`, the model
  layer returns deterministic answers so the pipeline and the evaluation gate run on a laptop.
