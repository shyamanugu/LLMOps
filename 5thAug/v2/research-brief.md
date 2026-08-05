# v2 Brief — Implementation-level LLMOps (source of truth)

> This is **version 2**: same component flow as the 3rdAug deep-dive, but **every component is written as a concrete
> implementation** — real repo layout, real files, real code/config, exact runtime flow, and a **"today → our setup →
> what changes"** delta. Be **decisive**: show *the* implementation, not a menu of options. Alternatives get at most a
> one-line footnote. Client stack: **Azure + GitHub**. No timelines.
> Running example = **APIX** (understood). Keep **Hiring Intelligence light** (still being scoped). Both are
> **sequential agent pipelines**, not agent-to-agent.

## Why v2 (the feedback)
Earlier material listed options and compared tools but never showed *how we actually implement it*. The client
(Kiran) wants: how we set up LLMOps here, the activities, what exists today and what changes, and — in detail —
observability (what is tracked on every request: model calls, tool calls, agent sessions) and evaluation (how exactly
we evaluate, including tool-selection). Prompt management is his example: show the actual mechanism and how it differs
from what the team has now, not a high-level description.

## The "today vs ours" framing (every component doc must include this)
For each component: **Today (assumption — to confirm):** how the APIX/Hiring teams likely do it now (prompts inline in
code or edited in a portal; model names hard-coded; logs only; manual spot-checks). **Our implementation:** the concrete
setup below. **What changes:** the specific delta and the small migration step.

## Canonical repository layout (all docs + deck reuse this exactly)
```
llmops-platform/                      # one monorepo; one subfolder per use case inside prompts/agents/evals
├── prompts/
│   └── apix/
│       ├── dimension-sales.prompt.yaml
│       └── coaching-report.prompt.yaml
├── agents/
│   └── apix/
│       └── pipeline.agent.yaml       # the pipeline: ordered steps, each -> a prompt + tools
├── evals/
│   └── apix/
│       ├── golden.telesales.jsonl    # golden dataset (per program)
│       ├── golden.wcc.jsonl
│       └── evaluators.yaml           # which metrics/evaluators run, thresholds
│   └── tool_selection.py             # custom Python evaluator (agent/tool behaviour)
├── src/
│   ├── pipelines/apix/run.py         # the pipeline runtime
│   └── common/
│       ├── prompt_loader.py          # loads prompt by id + label
│       ├── model_router.py           # resolves task alias -> deployment (reads models.yaml)
│       └── tracing.py                # OpenTelemetry spans (model/tool/agent)
├── models.yaml                       # task-alias -> Azure OpenAI deployment, per environment
├── .github/
│   ├── CODEOWNERS                    # /prompts and /agents require review
│   └── workflows/
│       ├── pr-checks.yml             # lint + unit + eval-subset gate on PR
│       ├── eval-full.yml             # full golden-set run on merge / nightly
│       └── deploy.yml                # OIDC login, gated envs, canary, rollback
├── infra/                            # Bicep (Container Apps, APIM, AI Search, Cosmos, etc.)
└── dashboards/                       # dashboard + alert definitions as code
```

## Canonical artifacts (use these EXACT examples everywhere)

### prompts/apix/coaching-report.prompt.yaml
```yaml
id: apix.coaching_report
version: 3
labels: [prod]                 # which version production uses; staging can point elsewhere
model_alias: reason            # resolved via models.yaml (not a raw model name)
temperature: 0.2
inputs: [agent_name, program, dimension_scores, evidence]
template: |
  You are a contact-center coach. Using ONLY the evidence quotes below, write a short
  coaching note for {{agent_name}} ({{program}}). Cite the evidence you use.
  Do not invent moments that are not in the evidence.
  Scores: {{dimension_scores}}
  Evidence: {{evidence}}
eval_refs: [evals/apix/golden.telesales.jsonl]
changelog:
  - v3: require evidence citation; forbid invented moments
  - v2: added program to the context
```

### src/common/prompt_loader.py
```python
from functools import lru_cache
# Prompt source of truth = Git. At runtime we read from the registry (Langfuse), which is
# synced from Git in CI. The app never hard-codes prompt text.
@lru_cache(maxsize=256)
def load_prompt(prompt_id: str, label: str = "prod"):
    p = registry.get(prompt_id, label=label)     # e.g. Langfuse.get_prompt(id, label)
    return Prompt(text=p.template, model_alias=p.config["model_alias"],
                  version=p.version, temperature=p.config.get("temperature", 0.2))
```

### models.yaml + resolver
```yaml
# models.yaml — the ONLY place a task maps to a model. Swap a model = edit here, via PR + eval gate.
environments:
  prod:
    aliases: { reason: gpt-5.2, bulk: gpt-5-mini, voice: gpt-realtime-1.5, embed: text-embedding-3-large }
  dev:
    aliases: { reason: gpt-5-mini, bulk: gpt-5-mini, voice: gpt-realtime-1.5, embed: text-embedding-3-large }
```
```python
# src/common/model_router.py
def resolve(alias: str, env: str) -> str:      # returns the Azure OpenAI *deployment name*
    return MODELS[env]["aliases"][alias]        # app code says resolve("reason"), never "gpt-5.2"
```

### src/common/tracing.py (OpenTelemetry — the exact attributes captured)
```python
from opentelemetry import trace
tracer = trace.get_tracer("apix.pipeline")

def call_model(alias, prompt_id, messages, env):
    with tracer.start_as_current_span("gen_ai.chat") as sp:
        deployment = resolve(alias, env)
        sp.set_attribute("gen_ai.system", "azure_openai")
        sp.set_attribute("gen_ai.request.model", deployment)
        sp.set_attribute("app.prompt_id", prompt_id)
        sp.set_attribute("app.prompt_version", version_of(prompt_id))
        sp.set_attribute("app.use_case", "apix")
        resp = client.chat.completions.create(model=deployment, messages=messages)
        u = resp.usage
        sp.set_attribute("gen_ai.usage.input_tokens", u.prompt_tokens)
        sp.set_attribute("gen_ai.usage.output_tokens", u.completion_tokens)
        sp.set_attribute("app.cost_usd", cost(deployment, u))
        return resp

def call_tool(name, mcp_server, args, expected=None):
    with tracer.start_as_current_span("tool.call") as sp:
        sp.set_attribute("tool.name", name)
        sp.set_attribute("tool.mcp_server", mcp_server)
        sp.set_attribute("tool.args", redact(args))
        if expected is not None:
            sp.set_attribute("eval.expected_tool", expected)
            sp.set_attribute("eval.was_correct_tool", name == expected)
        result = mcp.invoke(name, args)
        sp.set_attribute("tool.status", result.status)
        return result
```
Spans export to **Azure Monitor / Application Insights** (system of record) and **Langfuse** (LLM lens). One trace id
per request; child spans (agent → model/tool) roll up automatically.

### evals/apix/golden.telesales.jsonl (one record)
```json
{"id":"apix-telesales-014","input":{"transcript_id":"c-88421","program":"telesales"},
 "grading":{"must_cite_evidence":true,"expected_score_band":[70,85],"must_flag":["missed_upsell"]},
 "meta":{"program":"telesales","source":"sme_authored"}}
```

### evals/tool_selection.py (custom Python — the thing Ragas/DeepEval don't do)
```python
def evaluate_tool_selection(cases, run_agent):
    rows = []
    for c in cases:                                 # c: input, expected_tool, expected_args
        trace = run_agent(c["input"])
        chosen = trace.tool_calls[0].name if trace.tool_calls else None
        args_ok = compare_args(trace.tool_calls[0].args if trace.tool_calls else {}, c["expected_args"])
        rows.append({"expected": c["expected_tool"], "chosen": chosen, "args_ok": args_ok})
    return {
      "accuracy": mean(r["chosen"] == r["expected"] for r in rows),
      "wrong_tool_rate": mean(r["chosen"] not in (None, r["expected"]) for r in rows),
      "missing_tool_rate": mean(r["chosen"] is None and r["expected"] is not None for r in rows),
      "arg_correctness": mean(r["args_ok"] for r in rows),
      # + per-tool precision/recall
    }
```

### .github/workflows/pr-checks.yml (the quality GATE)
```yaml
name: pr-checks
on: { pull_request: { paths: ["prompts/**","agents/**","src/**","evals/**"] } }
permissions: { id-token: write, contents: read }   # OIDC, no stored keys
jobs:
  test-and-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2                        # federated login to Azure
        with: { client-id: ${{ vars.AZ_CLIENT_ID }}, tenant-id: ${{ vars.AZ_TENANT_ID }},
                subscription-id: ${{ vars.AZ_SUB_ID }} }
      - run: pip install -r requirements.txt
      - run: pytest tests/                          # unit / contract
      - run: python evals/run.py --subset changed --fail-under baseline
        #     ^ runs Ragas + DeepEval + tool_selection on changed prompts/agents;
        #       exits non-zero (blocks merge) if a metric drops past its baseline
```

### .github/workflows/deploy.yml (gated + canary + rollback)
```yaml
name: deploy
on: { push: { branches: [main] } }
permissions: { id-token: write, contents: read }
jobs:
  dev:  { environment: dev,  ... }                  # auto
  test: { environment: test, needs: dev, ... }      # requires reviewer (GitHub Environments)
  prod:
    environment: prod                               # requires reviewer + passes eval-full
    needs: test
    steps:
      - run: az containerapp revision copy ...       # new revision at 10% traffic (canary)
      - run: python ops/watch.py --for 15m --slo latency,errors,groundedness
      - run: az containerapp ingress traffic set ... # 100% if healthy, else revert (rollback)
```

### Content Safety (guardrail — where it sits in the pipeline)
```python
# input check before the model; output check before returning / storing
safe_in  = content_safety.analyze_text(user_or_transcript_text)   # block/flag categories
answer   = call_model(...)
answer   = pii_redact(answer)                                     # hide personal data
safe_out = content_safety.analyze_text(answer)
```

## Component list (v2 docs — same flow as 3rdAug, each an implementation)
01 Overview & how to read this (implementation-first stance; the monorepo backbone; today→ours framing).
02 Repository & GitHub Actions backbone (tree, branching, CODEOWNERS, the 3 workflows, OIDC, environments).
03 Prompt management (file format, registry+labels, loader code, PR+eval flow, A/B, today→ours + migration). *Kiran's example.*
04 Model management (models.yaml, resolver, deployment naming, swap flow, router note).
05 Observability (tracing.py spans, exact captured attributes per level, trace tree, App Insights + self-hosted Langfuse setup, dashboards/alerts). *Answer: what's tracked per request / model call / tool call / agent session.*
06 Evaluation (metric groups → concrete scoring; Ragas for RAG; DeepEval; custom Python tool-selection harness; evaluators.yaml + CI gate; online sampling; per-agent + end-to-end; golden dataset format & sources).
07 Guardrails & safety (Content Safety calls, PII redaction, placement, human-in-the-loop).
08 Data & RAG pipeline (ingest → clean/PII → chunk → embed → Azure AI Search index; refresh + index aliases; for Hiring: JDs/rubrics; for APIX: transcripts/metadata).
09 Serving, gateway & deployment (Container Apps hosting of pipeline steps, APIM gateway, environments, canary/rollback).
10 Feedback & improvement (capture API + events → App Insights/Langfuse → Fabric; triage → golden set → fix → re-eval; fine-tuning note).
11 End-to-end implementation & what changes (one wiring diagram; shared-vs-per-use-case table; a consolidated "today → ours → change" table across all components).

## Deck (v2)
Editable native shapes (no images), follows the 3rdAug flow, but each component slide shows the **concrete artifact**
(repo tree, the prompt YAML, models.yaml, the span code, the tool-selection harness, the Actions gate) — not option
tables. Simple English, abbreviations expanded, speaker notes. APIX as the example; Hiring mentioned lightly.

## FROM THE COMPLETE TRANSCRIPT — nail these head-on (this is what "not convinced" was about)

1. **Prompt management is the litmus test.** Kiran's exact challenge: *"the entire project is on Git, including the
   prompt. So what is the difference? What is the new approach? How will it differ from our existing approach?"* — and
   it caught us off guard. **Do NOT present "store prompts in Git" as new — they already do that.** The delta (what
   actually changes) is:
   - **One YAML file per prompt** with `id, version, template, variables, eval_refs, changelog`. Kiran confirmed *"we
     don't have a YAML file now — that could be a good one."* This is the concrete new artifact. Today: prompt text is
     buried inside code files.
   - **Every prompt change runs the CI/CD pipeline → evaluated against the golden dataset → must pass the metric
     thresholds in `eval_refs` before it is approved/deployed.** Today: a prompt edit ships like any code change, with
     no evaluation gate.
   - **A runtime registry that holds prompts and lets us swap / roll back to a previous prompt and compare versions.**
     Explain what a registry *is* (Kiran asked): it is where prompts are maintained so we can fall back if a new one
     fails evaluation. Three options, explained plainly and with a recommendation:
     - **Git + in-app cache** — simplest, stays in our repo, no extra service. **Start here.**
     - **Langfuse prompt management** — an open-source *product* from the Langfuse (Lang) family; we self-host it in
       our own container/network, so data stays with us; it also gives observability + token dashboards. Adopt as we scale.
     - **Foundry prompt assets** — native to the Azure AI platform (Microsoft), more managed/secure; cost to confirm.
     Recommendation: **start with Git + in-app cache; add Foundry or Langfuse as we scale.** Cost note: minor, to be
     confirmed (Kiran is fine with a minor cost).
   - **Evaluation-driven comparison and rollback** between prompt versions — pick the better prompt, roll back, or
     combine two into a better one, using the evaluation differences as the signal.
   **Net:** prompt management = versioned YAML prompt artifacts + an evaluation gate on every change + a registry for
   rollback/compare. THAT is the difference from "prompts already in Git."

2. **CI/CD + source control is component #1** — Shyam said the very first thing is the CI/CD setup, then we onboard the
   other components one by one. Every change (prompt, model, agent) flows through the pipeline and must pass the
   **evaluation gate** before deployment. Frame the whole thing as **enterprise-grade** (Kiran asked for enterprise-grade).

3. **Evaluation — Kiran's biggest ask: "it doesn't say HOW we evaluate."** Show the HOW, concretely:
   - **Golden dataset** = ground truth; the first thing created for any use case; enhanced over time. Kiran asked *"how
     is it different from normal ground truth?"* — Answer: it is the same idea, but in LLMOps it is run as a **gate at
     every change / every pipeline run** before a release can deploy. Sources (three-step): SME-authored first → real
     traffic over time (users have format/personalization preferences an SME won't capture) → reviewed again by SMEs
     and business users.
   - **Metric groups:** RAG, writing quality, execution / task-path, agent behavior (correct tool usage). Note the
     overlap Kiran raised (coherence can sit under RAG; most sit under RAG) — but non-RAG use cases exist, and MCP tool
     selection needs agent-behavior metrics.
   - **The HOW (mechanisms) — map each group to a real mechanism, with code:**
     - Code frameworks **Ragas** and **DeepEval** → RAG and writing-quality metrics (show real evaluator code).
     - **Custom Python logic** → agent behavior / correct tool usage (show the `tool_selection.py` harness) — Ragas/DeepEval do not cover this.
     - **LangSmith** → also provides evaluation + observability, but it is **not open source — needs a license**.
   - Show how the gate uses these (threshold per metric; block the release if below baseline).

4. **Observability — answer Kiran's exact three questions:** what gets tracked on *every request*; are **model calls**
   tracked; are **tool calls** tracked; are **agent sessions** ("agent hub sessions") tracked. Show the trace with all
   of these captured (use `tracing.py`).

5. **Model management — be honest about the small delta.** They *likely already* pick a bigger model for complex
   agents and a cheaper one for simple ones. What we add: a **config-driven task-alias** (`models.yaml`), the rule that
   a model swap is a **config change that must pass the evaluation gate**, and **one shared config reused by all agents
   / use cases under one hub** (Azure AI Foundry hub). Don't oversell it as brand-new.

6. **Deliverable Kiran asked for:** the approach; all the activities (with **no timelines**); what we have today and what
   must change; the observability + evaluation detail above; and a **plan for hosting on Azure** (services + where each
   runs). Kiran is technical — concrete depth is welcome. Use cases: Hiring Intelligence + APIX (in the transcript APIX
   was transcribed as "epics"). Pipelines, not agent-to-agent.

## Rules
Decisive implementation (not options). Real artifacts. **Lead every component with "what's different from today."**
Azure + GitHub. No timelines. Enterprise-grade. APIX example; light on Hiring. Technical depth is welcome. Not
marketing; must not read as AI-generated.
