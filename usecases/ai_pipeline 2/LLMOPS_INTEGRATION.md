# LLMOps Integration Plan — AI Pipeline Call-Analytics Pipeline

**Status:** Draft · Strategy approved (thin adapter) · Owner: <fill in>
**Scope:** Wire the AFNI LLMOps platform (`platform/services/*`) into this pipeline (`usecases/ai_pipeline 2`) with minimal disruption to working step logic.

---

## 1. Strategy: thin adapter at the single LLM choke point

This pipeline makes **every** LLM call through one function — `services/__init__.py::query()`. All four LLM steps build an `openai.AsyncOpenAI` client and call `query()`:

| Step | Client instantiation | `query()` call | Model arg |
|------|---------------------|----------------|-----------|
| `steps/denoise.py` | `:98` (`chat_endpoint`/`chat_api_key`) | `:46` | `cfg.openai.chat_deployment` |
| `steps/analysis.py` | `:95` (`reasoning_*`) | `:68` (with `schema=`) | `cfg.openai.reasoning_deployment` |
| `steps/summary.py` | `:456` | `:433` | `cfg.openai.reasoning_deployment` |
| `steps/individual_metrics.py` | `:247` | `:210` | `cfg.openai.reasoning_deployment` |

`kpi` is pure aggregation (no LLM). Because all traffic converges on `query()`, we inject the entire LLMOps stack **there** — step logic stays untouched.

**Decision (approved):** Thin adapter — reuse the platform's *functions* (`resolve`, `build_guardrail`, `PromptRegistry`, `Tracer`, `compute_cost`) directly inside a wrapped `query()`. We do **not** rewrite the steps as `orchestration.ModelStep` (that's a possible later "hybrid" phase, out of scope here).

---

## 2. How the platform is consumed (important constraints)

From the platform's own ADRs and code:

- **No SDK / no `pip install`.** Services are consumed by adding each service's `src/` to `PYTHONPATH` (ADR 0004). Cross-service deps are declared via `-r ../0X-.../requirements.txt`.
- **Constructor injection with safe no-op defaults.** `NullTracer`, `PassthroughGuardrail`, in-memory stores — so we can integrate and test the full flow **before any Azure resource exists**, then swap in real backends.
- **Onboard by config, not code.** A new usecase is registered by adding entries to 6 YAML files (below), not by editing platform code.
- **Azure-first, hand-rolled.** Tracing → Azure Monitor via OpenCensus; guardrails → Azure Content Safety; model provider → Azure OpenAI. No Langfuse/MLflow/LiteLLM/Ragas.
- **Secrets:** real credentials go in `.env.local` (gitignored), never committed `.env`.

### Platform functions we will call

```python
from prompt_management.registry import PromptRegistry      # .render(name, **vars) -> str
from model_management.model_router import resolve           # (alias, env, expected_kind) -> ModelHandle(provider, deployment, kind)
from observability.tracer import InMemoryTracer             # later: AzureMonitorTracer
from observability.types import StepEvent, PipelineEvent
from observability.cost import compute_cost                 # (deployment, in_tok, out_tok) -> float
from guardrails.builder import build_guardrail              # (usecase, env) -> CompositeGuardrail(.check_input/.check_output)
from evaluation_gate.gate import EvaluationGate             # .run(usecase, cases, sut, threshold) -> GateResult
from feedback.store import JsonlFileFeedbackStore
```

---

## 3. Target architecture (after integration)

```
Prefect (batch)  ─▶  denoise → analysis → summary → individual_metrics → kpi
                          │  (steps unchanged — still call query())
                          ▼
              services.query()  ── THE ONE INJECTION SEAM ──
                 1. render prompt        PromptRegistry.render()       (Phase 4)
                 2. guardrail.check_input(system+user)                 (Phase 3)
                 3. resolve(alias, env)  → provider/deployment         (Phase 2)
                 4. provider.chat(...)   (existing AsyncOpenAI path)   (unchanged)
                 5. guardrail.check_output(content)                    (Phase 3)
                 6. tracer.record_step(StepEvent + compute_cost())     (Phase 1)
                          │
             ┌────────────┼───────────────────────────┐
       AzureMonitorTracer │                    JsonlFileFeedbackStore
                          ▼
          EvaluationGate (CI, pre-deploy)  ◀── golden datasets ◀── feedback.promotion
```

### Usecase identity
Register this pipeline everywhere as usecase **`ai_pipeline`**. Model-alias mapping:

| App config today | Platform alias | Notes |
|------------------|----------------|-------|
| `cfg.openai.reasoning_deployment` | `reason` | analysis / summary / individual_metrics |
| `cfg.openai.chat_deployment` | `bulk` | denoise (cheaper/bulk cleanup) |
| — | `judge` | used by `LLMJudgeEvaluator` in eval gate |

---

## 4. Phase-by-phase checklist (execution order)

Each phase is independently shippable and ordered by ROI ÷ risk. Value lands after Phase 1 alone.

### Phase 0 — Wiring & registration (no app-logic change) ✅ DONE
- [x] Add platform `src/` dirs to `PYTHONPATH` — done via `ai_pipeline/_platform_bootstrap.py` (auto-runs on import; env override `LLMOPS_PLATFORM_ROOT`). Wires: `02,03,04,05,06,11`.
- [x] Register `ai_pipeline` usecase:
  - `03-model-management/config/models.yaml` — `reason`/`bulk`/`judge` aliases already present for `dev`/`test`/`prod` (confirmed).
  - `03-model-management/config/pricing.yaml` — added `gpt-5-nano`/`gpt-5-mini` deployment keys. **TODO (operator):** replace `0.0` with AFNI's real per-1k rates so cost is non-zero.
  - `06-guardrails/config/guardrails.yaml` — added `usecases.ai_pipeline` stub (Phase 3 fills policy).
  - `04-evaluation-gate/config/gates.yaml` — added `usecases.ai_pipeline` thresholds stub (Phase 5).
- [~] Secrets: thin adapter keeps the pipeline's own `AsyncOpenAI` (Foundry `/openai/v1`) client and only borrows platform *functions*, so platform `AZURE_OPENAI_*` are **not** required for Phases 0–1. `.env.local` reconciliation deferred until a phase needs a platform Azure backend (Phase 3 Content Safety / Phase 1 Azure tracer).
- **Acceptance:** ✅ verified by `scratchpad/smoke_llmops.py` — platform imports, `resolve("reason","dev")→gpt-4o`, `build_guardrail("ai_pipeline","dev")` builds, `compute_cost` reads pricing.

### Phase 1 — Observability & cost (highest ROI, lowest risk) ✅ DONE
- [x] Process-wide tracer created once in `main.py::run_pipeline` via `observability.init_tracer()`. Choice via `AI_PIPELINE_TRACER` = `memory` (default) | `null` | `azure`.
- [x] Attribution flows through **`contextvars`** (not new `query()` params — cleaner, steps stay one-line): `set_run_context(run_id, program, env)` in `main.py`; `set_step_context(step, alias)` at each step entry (`denoise→bulk`, `analysis`/`summary`/`individual_metrics`→`reason`).
- [x] `services.query()` wraps `_query_impl` and emits one `StepEvent` per call (tokens + `compute_cost()` + latency + status/error) across **all** return paths (ok / length-limit / content-filter / bad-request). Fail-open.
- [x] One `PipelineEvent` per invocation in `main.py`; run-level LLM totals (calls / tokens / cost / errors) logged in the RUN SUMMARY.
- **Acceptance:** ✅ smoke test shows per-call token + cost + latency captured with correct step/model attribution, plus end-to-end recording through the real `query()` wrapper.
- **Remaining for production value:** fill real rates in `pricing.yaml`; optionally set `AI_PIPELINE_TRACER=azure` + `APPLICATIONINSIGHTS_CONNECTION_STRING` to ship traces to Azure Monitor; run against real data to observe the logs.

**Files changed (Phase 0–1):** `_platform_bootstrap.py` (new), `observability.py` (new), `main.py`, `services/__init__.py`, `steps/{denoise,analysis,summary,individual_metrics}.py`, `requirements.txt` (+PyYAML); platform `pricing.yaml`/`guardrails.yaml`/`gates.yaml` (usecase registration).

### Phase 2 — Model management (alias indirection) ✅ DONE
- [x] Added `AzureOpenAIConfig.deployment_for(alias)` + module helper `_resolve_alias_deployment` in `programs_config/base/config.py`. Calls the platform `resolve(alias, env)`, **cached per (alias, env)** so per-row calls don't re-parse YAML, and **fail-open** to the pipeline's env deployment (`REASONING_MODEL_DEPLOYMENT`) if the platform is absent / alias unknown / unprovisioned.
- [x] Environment via `AI_PIPELINE_ENV` (introduced in Phase 1), default `dev`.
- [x] Routed all four call sites through the alias: `denoise → deployment_for("bulk")`; `analysis`/`summary`/`individual_metrics → deployment_for("reason")`.
- [x] `models.yaml`: set `reason`/`bulk` to `deployment: null` (**unprovisioned**, the platform's "provisioned later" pattern) for `dev`/`test`/`prod`. This keeps runs **identical to today** (fail-open uses the pipeline's real deployment) and makes `models.yaml` the one-line **activation point** for registry-driven model choice.
- **Design note — why `null` not a hardcoded name:** the smoke test revealed the operator's real deployment is `gpt-5.4-nano` (from `.env`), not a guessable default. A concrete-but-wrong name in `models.yaml` would resolve successfully and send a non-existent deployment to the endpoint (fail-open only catches exceptions, not wrong-but-valid names). `null` → fail-open → the real env deployment is always used until an operator deliberately provisions the alias.
- **Acceptance:** ✅ smoke test — `reason`/`bulk`/unknown aliases fail-open to fallback; a provisioned alias (`judge→gpt-4o-mini`) resolves from the registry; `deployment_for("reason"/"bulk")` returns the env deployment (`gpt-5.4-nano`). No step logic changed.
- **To activate registry-driven selection (operator, one-line):** set `reason`/`bulk` deployment in `models.yaml` to your real Azure/Foundry deployment name(s) per environment — e.g. point `bulk` at a cheaper model than `reason` to cut denoise cost. Also fill real rates for `gpt-5.4-nano` in `pricing.yaml` to light up cost tracking.

**Files changed (Phase 2):** `programs_config/base/config.py`, `steps/{denoise,analysis,summary,individual_metrics}.py`; platform `models.yaml` (reason/bulk → null), `pricing.yaml` (gpt-5.4-nano key).

### Phase 3 — Guardrails ✅ DONE
- [x] `guardrails_gate.py` (new) — builds one `CompositeGuardrail` per run via `build_guardrail("ai_pipeline", env)` (`main.py` calls `gate.init_guardrail`). Fail-open helpers `check_input`/`check_output`.
- [x] `services.query()` runs `check_input(system+user)` before send and `check_output(content)` after. A **block** returns a `Status.SKIPPED` `Response` (mirrors existing content-filter handling — batch never crashes); a **flag** passes through. Guardrail reason is recorded on the `StepEvent`; real token cost is still recorded even when output is blocked.
- [x] `guardrails.yaml` `usecases.ai_pipeline` policy — **deliberately non-destructive:** PII is **flagged, not blocked** on both sides (email/phone/ssn/credit_card) so analyzed calls are never silently dropped; `secret_leak` blocks; `prompt_injection` **disabled** (internal transcripts, not adversarial agent input — avoids false-positive drops); `azure_content_safety` off (enable when provisioned).
- **Acceptance:** ✅ smoke test — clean text passes; PII on input/output is flagged (`allowed=True` + reason) and **not** dropped; `query()` returns `ok` for PII-bearing content with the flag reason on its trace event.

### Phase 4 — Prompt management ✅ DONE (override layer)
- [x] `prompts_gate.py` (new) — a `PromptRegistry` over `prompts/<program>/*.yaml`. **Override semantics:** a git-backed YAML prompt wins **when present**; otherwise the in-code prompt is kept (fail-open). Wired via `config._apply_prompt_overrides` inside `load_program_config` (so `load_mode_config` is covered too — it delegates). No step code changed (steps still read `cfg.*_system_prompt`, now optionally YAML-sourced).
- [x] **Why override, not hard cutover:** the in-code prompts are dynamic f-strings that interpolate each program's Pydantic schema at import time — freezing them into static YAML verbatim would drop the schema injection and change behaviour. Migration is deliberate and faithful via `prompts_gate.dump_prompts(cfg, program)` (run from the real venv to export resolved text), documented in `prompts/README.md`.
- [x] `analysis_schema`/`reflection_schema` stay code-side (structured-output contract).
- **Acceptance:** ✅ smoke test — `render()`/overrides fall back to in-code prompts when no YAML; a dropped-in YAML prompt overrides the matching `cfg` field while un-migrated prompts are untouched.

**Files changed (Phase 3–4):** `guardrails_gate.py` (new), `prompts_gate.py` (new), `prompts/README.md` (new), `services/__init__.py`, `main.py`, `programs_config/base/config.py`; platform `guardrails.yaml` (ai_pipeline policy).

### Phase 5 — Evaluation gate (CI, pre-deploy) ✅ DONE
- [x] `eval/harness.py` (new) — `run_gate(dataset, usecase, program, env, system_under_test)` loads a golden JSONL via the platform loader, runs each case through the SUT, scores with `EvaluationGate`. SUT is **injectable** (default = live pipeline `analysis`; tests pass a fake) so the harness is importable without the full pipeline.
- [x] Default **live SUT** runs the pipeline's `analysis` (its prompt + schema + `deployment_for("reason")`) on each case's transcript and returns the parsed structured output.
- [x] Evaluators: `SchemaEvaluator` for structured steps (validates against the program's Pydantic JSON schema); `LLMJudgeEvaluator` (`judge` alias) available for denoise/summary quality — note the judge path uses the platform's `AzureOpenAIProvider` and needs `AZURE_OPENAI_*` creds.
- [x] `gates.yaml` thresholds set (Phase 0): dev 0.8 / test 0.9 / prod 1.0.
- [x] `eval/dataset/analysis_golden.seed.jsonl` (seed) + `eval/build_dataset.py` (builds a real golden set from a historical `analysis` parquet, embedding the program's JSON schema).
- [x] `.github/workflows/ai-pipeline-eval-gate.yml` — runs the gate on PRs touching the pipeline / `models.yaml` / `gates.yaml`. **Fail-closed** on gate failure (exit 1); **skips** (exit 0) when model creds aren't set as secrets, so it can't spuriously block a merge; `--require-creds` enforces.
- **Acceptance:** ✅ smoke test — gate reads the 0.8 threshold from `gates.yaml`; a half-passing set → `FAILED`, an all-passing set → `PASSED`; `run_gate` loads a JSONL dataset and a schema-invalid SUT output correctly fails the gate.

### Phase 6 — Feedback loop ✅ DONE
- [x] `feedback_gate.py` (new) — `record_feedback(step, rating, original_input, corrected_output, rater_role, comment, session_id)` writes `FeedbackEvent`s to `JsonlFileFeedbackStore` (path via `AI_PIPELINE_FEEDBACK_PATH`; session id auto-links to the current run via the observability context). Fail-open.
- [x] `promote(session_id?, dataset_path?)` wraps `promote_to_golden_dataset` — corrections become `exact_match` golden cases the Eval Gate loads directly, closing the loop into Phase 5. No-correction signals are retained but not promoted (per platform semantics).
- [x] CLI: `python -m ai_pipeline.feedback_gate record …` / `… promote`.
- **Acceptance:** ✅ smoke test — a recorded coach correction promotes to exactly one regression case that loads back as an `EvalCase` (`evaluator=exact_match`, `expected=<correction>`); a thumbs-down with no correction is stored but not promoted.

**Files changed (Phase 5–6):** `eval/{__init__,harness,build_dataset}.py` (new), `eval/dataset/analysis_golden.seed.jsonl` (new), `feedback_gate.py` (new), `.github/workflows/ai-pipeline-eval-gate.yml` (new), `requirements.txt` (+jsonschema), `pyproject.toml` (+ai_pipeline.eval).

---

## 🎯 Integration complete — all 7 phases (0–6) landed and verified

All phases are **non-breaking and fail-open**: with the platform absent or unconfigured, the pipeline runs exactly as originally written. Verified by `scratchpad/smoke_llmops.py` (~40 checks across all phases).

**Operator activation checklist** (all optional, none required to run — each lights up more value):
1. Fill real per-1k rates for `gpt-5.4-nano` in `pricing.yaml` → live cost tracking.
2. Provision `reason`/`bulk` deployment names in `models.yaml` → registry-driven model routing (point `bulk` at a cheaper model to cut denoise cost).
3. Set `AI_PIPELINE_TRACER=azure` + `APPLICATIONINSIGHTS_CONNECTION_STRING` → ship traces to Azure Monitor.
4. Run `prompts_gate.dump_prompts(cfg, program)` from the real venv → migrate prompts to git-backed YAML.
5. Build a real golden set (`eval/build_dataset.py`) and set the eval-gate secrets → enforce the CI gate.
6. Enable `azure_content_safety` in `guardrails.yaml` once the resource is provisioned.

---

## 5. Concrete seam sketch (Phase 1–3 combined, illustrative)

The wrapped `query()` keeps its current signature and behavior; new concerns are additive and guarded by no-op defaults.

```python
# services/__init__.py  (sketch — not final)
async def query(client, user_prompt, system_prompt, model, temperature=1.0,
                schema=None, max_completion_tokens=None, max_token_retries=2,
                *, tracer=None, guardrail=None, run_id="", step_name="", model_alias=""):
    tracer = tracer or NullTracer()
    guardrail = guardrail or PassthroughGuardrail()
    event = StepEvent(session_id=run_id, step_name=step_name, model_alias=model_alias, deployment=model)
    t0 = time.perf_counter()
    try:
        gin = guardrail.check_input(f"{system_prompt}\n{user_prompt}")
        event.guardrail_allowed, event.guardrail_reason = gin.allowed, gin.reason
        if not gin.allowed:
            return Response(status=Status.SKIPPED.value, message=gin.reason).model_dump()

        out = await _existing_completion_path(...)          # unchanged retry/content-filter logic
        event.input_tokens, event.output_tokens = out["prompt_tokens"], out["completion_tokens"]
        event.cost_usd = compute_cost(model, event.input_tokens, event.output_tokens)

        gout = guardrail.check_output(str(out["message"]))
        if not gout.allowed:
            event.guardrail_allowed = False
            return Response(status=Status.SKIPPED.value, message=gout.reason).model_dump()
        return out
    except Exception as e:
        event.error = str(e); raise
    finally:
        event.latency_ms = (time.perf_counter() - t0) * 1000
        tracer.record_step(event)
```

Callers thread `tracer`/`guardrail`/`run_id`/`step_name`/`model_alias` from the per-run context; omitting them = today's behavior exactly.

---

## 6. Risks & open questions
- **Endpoint reconciliation (Phase 0):** pipeline uses a Foundry `/openai/v1` `AsyncOpenAI` client; platform's provider uses `AzureOpenAI` with different env keys. Thin adapter keeps the pipeline's client and borrows only platform *functions* — confirm this is acceptable.
- **`pricing.yaml` is all zeros today** — cost tracking is meaningless until real rates are filled in (Phase 0).
- **Async vs sync:** platform tracer/guardrail calls are synchronous; ensure they don't block the throttled async fan-out meaningfully (they're cheap; Azure Content Safety is a network call — keep it optional/off in bulk `denoise`).
- **PYTHONPATH ergonomics:** decide the cleanest wiring (path config vs editable installs vs vendoring) so local dev, Prefect workers, and CI all resolve the platform packages identically.

---

## 7. What "done" looks like
Every LLM call in this pipeline is traced (tokens/cost/latency/guardrail decision), model choice is config-as-code per environment, prompts are versioned, and no prompt/model change ships without passing the evaluation gate — all with the step logic your teammate wrote left intact.
