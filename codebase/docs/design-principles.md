# Design Principles — LLMOps Platform

The principles the platform is built on, and — importantly — **where each is enforced in
the code**, so a reviewer can check they are actually applied, not just asserted. These are
the principles called out in section 0 of `../ARCHITECTURE_SPEC.md` and the v2 deck.

---

## 1. Separation of concerns

Each package has one job; endpoints stay thin and delegate to feature packages.

Enforced in: the package layout (`prompts`, `models`, `observability`, `guardrails`,
`data_access`, `tools`, `orchestration`, `evaluation`, `feedback`, `api`) with a strict
one-way dependency direction (see the dependency graph in `lld.md`). The FastAPI routers
in `api/routers/*` hold no business logic — they call the packages. Shared value objects
live in `common/types.py` to prevent cross-package coupling.

## 2. Dependency inversion (adapters behind interfaces)

High-level code depends on abstractions; concrete Azure/registry clients sit behind
protocols and can be swapped or mocked.

Enforced in: `prompts/base.PromptRegistry` (Git/Langfuse/Foundry all implement it),
`guardrails/base.Guard`, `data_access/base.DataSource`, `evaluation/metrics/base.Metric`,
`tools/base.Tool`. Application code calls `load_prompt(...)`, not a specific registry;
`factory.build_registry` chooses the backend from config.

## 3. Config-as-code

Operational choices live in versioned files changed via reviewed, gated pull requests —
never hard-coded, never a hidden portal toggle.

Enforced in: `platform/models.yaml` (alias -> deployment; ADR 0002),
`platform/tools/registry.yaml`, `platform/evaluators/defaults.yaml`,
`usecases/*/evals/evaluators.yaml` (thresholds), `usecases/*/agents/pipeline.agent.yaml`
(pipeline definition), and `*.prompt.yaml` (prompts). `Settings` reads all runtime config
from the environment (twelve-factor).

## 4. Fail-safe defaults

The safe outcome is the default; unsafe conditions block rather than pass silently.

Enforced in: the evaluation gate's **absolute floors** (PII leak = 0, unsafe = 0) in
`evaluation/thresholds.py`; guardrails run on every input and output and raise
`GuardrailBlocked` (a controlled 422) on a block; adapters degrade to a mock in dev instead
of crashing, but production wiring is required (TODO-indexed) before go-live; the eval gate
exits non-zero (blocks the release) on any regression.

## 5. Least privilege

Every identity and data path gets only the access it needs.

Enforced in: Managed Identity + Key Vault for Azure access (no keys in code — `Settings`
secret fields are `repr=False`); `data_access/sql.py` is **read-only, parameterised, and
allow-listed** to specific tables; API Management enforces quotas/throttling; GitHub uses
OIDC federated login (no stored cloud credentials) with per-environment approvers. See
`security.md`.

## 6. Everything observable

Nothing runs untraced or uncosted; logs are structured and correlated.

Enforced in: `observability/tracing.py` (OpenTelemetry, GenAI semantic conventions; spans
nest request -> agent -> model/tool), `cost.py` (`app.cost_usd` computed once at emit),
`exporters.py` (App Insights + Langfuse), and `common/logging.py` (structured key=value,
never `print`, correlated to the active span). Tool spans carry `eval.was_correct_tool`.

## 7. Reuse over rebuild

Build shared machinery once; a new use case adds a folder and inherits everything.

Enforced in: the monorepo split of `platform/` + `backend/src/llmops/` (shared) vs
`usecases/<uc>/` (per use case) with an identical folder shape (ADR 0001); the reusable
tool catalog in `tools/`; `usecases/_template/` as the copy source for onboarding.

## 8. Twelve-factor config

Config comes from the environment; the same build runs in every environment.

Enforced in: `config/settings.Settings` (`env_prefix="LLMOPS_"`, reads `.env` in dev, env
vars / Key Vault references in Azure) and `get_settings()` singleton; per-environment
behaviour (e.g. model choice) comes from `models.yaml` keyed by `APP_ENV`, not from
separate builds.

---

## Cross-reference

| Principle | Primary enforcement points |
|---|---|
| Separation of concerns | package layout; thin routers; `common/types.py` |
| Dependency inversion | `*/base.py` protocols; `prompts/factory.py`; `deps.py` |
| Config-as-code | `models.yaml`; `evaluators.yaml`; `*.prompt.yaml`; `pipeline.agent.yaml` |
| Fail-safe defaults | `thresholds.py` floors; `GuardrailEngine`; gate exit codes |
| Least privilege | Managed Identity + Key Vault; read-only allow-listed SQL; APIM; OIDC |
| Everything observable | `tracing.py`; `cost.py`; `exporters.py`; `logging.py` |
| Reuse over rebuild | `platform/` vs `usecases/`; tool catalog; `_template/` |
| Twelve-factor config | `Settings`; `get_settings()`; env-keyed `models.yaml` |
