# ADR 0006: Prompt Management — git-backed storage, Foundry deferred

## Status
Accepted

## Context
Azure AI Foundry prompt flow / prompt assets is the natural Azure-native place to manage prompts — it gives a UI, built-in versioning, and evaluation hooks. Standing it up requires Foundry project RBAC (hub connections, project-level role assignments), which Contributor-only access doesn't grant — the same access gap already documented for Key Vault (ADR 0001) and voice infrastructure (ADR 0003).

Separately, prompt *content* is inherently usecase-specific: usecase A and usecase B need different wording. Unlike Model Management, where the resource being managed (a model deployment) is genuinely shared platform infrastructure, a prompt template is closer to application data. The open question was how a "Prompt Management" component can be a reusable platform piece at all if the thing it manages isn't reusable content.

## Decision
Split the two concerns explicitly:

- **Mechanism (reusable, platform-owned)**: `PromptRegistry` in `platform/services/02-prompt-management/src/prompt_management/` loads `*.yaml` prompt files from directories supplied by the caller, validates required variables before rendering, and expands shared text fragments. It has no knowledge of any specific usecase — pointing it at a new directory is the entire onboarding step for a new usecase's prompts.
- **Content (usecase-owned)**: prompt files themselves live in each usecase's own repo/folder, not inside this platform component. `tests/fixtures/usecase_demo/` stands in for that arrangement and proves the registry works against a directory it doesn't own.
- **Content (genuinely shared)**: a small `prompts/shared/` fragment library (a safety preamble, a JSON-output instruction) that usecases opt into via a `{{fragment:name}}` token in their own templates — the one place actual text, not just mechanism, is reusable.
- **Storage backend**: plain YAML files, versioned via git and reviewed via pull request — no database, no Foundry dependency.
- **Templating**: plain `{variable}` substitution, not Jinja2 — avoids a dependency that today's prompts (no loops, no conditionals) don't need.
- **Version pinning**: a `version` field exists on each prompt file, but there is no per-environment version-pinning mechanism yet (unlike `models.yaml`'s environment-scoped alias resolution) — git history is the version log until an evaluation mechanism exists to justify choosing between versions programmatically.
- **Orchestration integration**: `ModelStep` (08) now accepts `prompt_name` + `prompt_registry` as an alternative to a raw `prompt_template` string, closing the seam that component's README originally left open.

## Alternatives Considered
- **Azure AI Foundry prompt flow now**: rejected — blocked by the same RBAC gap as Key Vault and voice infrastructure; revisit when Foundry project roles are approved.
- **A database-backed prompt store**: rejected — adds a stateful dependency and a deploy target for no benefit over git-backed files at current scale; git already gives history, diffing, and review.
- **Jinja2 templating**: rejected for now — real capability (loops, conditionals, includes) that no current prompt needs; adds a dependency ahead of a real requirement.
- **Treating prompts as pure usecase content with no platform component at all**: rejected — it would mean every usecase reinvents loading, variable validation, and shared phrasing (safety language, output-format instructions) independently, which is exactly the duplication a platform is supposed to prevent.

## Consequences
- Onboarding a new usecase's prompts is a config change (which directories the registry points at), not a code change — same reusability shape as Model Management's alias resolution.
- Prompt review happens through the same pull-request process as code review, which is arguably stronger change control than a UI-based prompt editor would give, at the cost of no non-technical editing UI for prompts.
- `output_schema` is reserved in the file format but unenforced — no validation logic exists until Evaluation Gate (04) is built. Prompt files won't need a format migration when that arrives.
- If a usecase needs real templating logic (conditionals, loops), the plain substitution approach breaks down and Jinja2 needs to be introduced — deferred, not designed around, per the "Revisit When" below.

## Revisit When
- Foundry project RBAC (hub connections, project-level role assignments) becomes available — evaluate migrating to Foundry prompt assets as an alternative `PromptRegistry` backend, following the same protocol-based swap pattern already used for `ModelProvider` in Model Management (03).
- A usecase needs conditional logic or loops inside a prompt template — introduce Jinja2 at that point, not before.
- Evaluation Gate (04) exists and needs to compare prompt versions — add per-environment version pinning to `PromptRegistry`, mirroring `models.yaml`.
