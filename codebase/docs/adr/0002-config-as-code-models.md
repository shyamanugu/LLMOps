# ADR 0002 — Model selection is config-as-code (models.yaml + alias resolver)

- Status: Accepted
- Date: 2026-08-06
- Deciders: Platform engineering

## Context

Teams today likely hard-code model names inside agent code (`"gpt-5.2"`) or pick a model
in a portal. That makes a model swap a code edit scattered across files, untested against
quality, and inconsistent between environments. The v2 deck is explicit that the delta we
add is small but real: a config-driven **task alias**, the rule that a model swap is a
**gated config change**, and **one shared config reused by every agent and use case**.

We considered three placements for the mapping: (a) hard-coded in agent code, (b) a
runtime portal/database toggle, (c) a versioned file in the repo. Option (a) is what we
are replacing. Option (b) makes changes invisible to review and untestable before they go
live. Option (c) makes every change a reviewable, eval-gated pull request.

## Decision

Model selection is config-as-code. `platform/models.yaml` is the single file that maps a
task alias (`reason`, `bulk`, `judge`, `voice`, `embed`) to an Azure OpenAI deployment
name, per environment (`dev`/`test`/`prod`). Application code asks the `ModelRouter` for
an alias and never names a raw model. This is simultaneously:

- **Code-level**: the mapping is a file in the repo, changed via pull request.
- **Pipeline-level**: any change is validated and must pass the evaluation gate.
- **Runtime-level**: the app resolves alias -> deployment at run time using `APP_ENV`.

`llmops.config.models_config.ModelsConfig.resolve(alias, env)` performs the lookup and
raises `UnknownAliasError` for an unknown alias/environment.

## Consequences

- Positive: swapping a model is one reviewed line change, eval-gated before it can ship.
- Positive: environments differ safely (prod can use a stronger `reason` model than dev)
  without any code change.
- Positive: no raw model strings in application code; consistent across all use cases.
- Negative: adds one indirection (alias -> deployment); engineers must know the aliases.
- Negative: deployment *names* still have to exist in Azure OpenAI; the YAML is validated
  for shape but not that the deployment exists (that is a setup/`todo.html` step).
