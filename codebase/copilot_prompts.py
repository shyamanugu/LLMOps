#!/usr/bin/env python3
"""GitHub Copilot prompt catalog for the LLMOps platform codebase.

WHAT THIS IS
------------
Every file in this repository was generated from a Copilot prompt. This module is the
authoritative, ordered catalog of those prompts. It serves three purposes:

1. Provenance — a record that the codebase was produced via GitHub Copilot (the approved tool).
2. Regeneration — run any prompt in Copilot Chat (or Copilot in the IDE) to (re)generate the
   corresponding file(s) inside the client environment, where outside help is not available.
3. Extension — the ``USE_CASE_PROMPTS`` section is what you run to add a new use case
   (e.g. APIX, Hiring) on top of the finished framework.

HOW TO USE (in the client environment)
--------------------------------------
- Open the target file (or an empty file at the target path) in the IDE.
- Open Copilot Chat, paste the prompt for that file, and let Copilot generate it.
- Prompts are ordered so that dependencies are generated before dependents.
- Always keep ``ARCHITECTURE_SPEC.md`` open in the workspace — Copilot uses it as context,
  which is what keeps the generated modules consistent with each other.

    python copilot_prompts.py --list            # list all prompt ids
    python copilot_prompts.py --show foundation  # print prompts for one area
    python copilot_prompts.py --emit prompts.md  # write the whole catalog to Markdown
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

SHARED_CONTEXT = (
    "Context for every prompt: This is an enterprise LLMOps platform. Stack = Python 3.11 "
    "FastAPI backend + React 18 + TypeScript (Vite) frontend, deployed on Azure (Container "
    "Apps), CI/CD on GitHub. Read ARCHITECTURE_SPEC.md in the workspace and conform to it "
    "exactly: import root `llmops`, full type hints, pydantic v2, async I/O, Google-style "
    "docstrings, structured logging (never print), the custom error hierarchy in "
    "llmops.common.errors, ruff/black/mypy-clean. Where live Azure/Langfuse wiring is needed, "
    "degrade gracefully in dev and mark the exact spot with `# TODO(wiring): ...`."
)


@dataclass(frozen=True)
class Prompt:
    """One Copilot prompt targeting one or more files."""

    id: str
    area: str
    target: str
    prompt: str
    depends_on: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------------------
# FRAMEWORK PROMPTS — generate the reusable platform (already generated in this repo).
# ---------------------------------------------------------------------------------------
FRAMEWORK_PROMPTS: list[Prompt] = [
    # -- foundation --
    Prompt(
        "foundation.errors", "foundation", "backend/src/llmops/common/errors.py",
        "Create the platform exception hierarchy. A base `LLMOpsError(message, *, detail)` with "
        "class attributes `code: str` and `http_status: int` and a `to_dict()`; then subclasses "
        "ConfigError, UnknownAliasError, PromptNotFoundError, PromptRenderError, GuardrailBlocked, "
        "ToolError, EvaluationGateFailed, UpstreamError — each with an appropriate code and HTTP status.",
    ),
    Prompt(
        "foundation.logging", "foundation", "backend/src/llmops/common/logging.py",
        "Create structured logging: `configure_logging(level)` (idempotent, stdout, key=value "
        "formatter), and `get_logger(name)` returning a LoggerAdapter that accepts structured "
        "context kwargs (e.g. logger.info('msg', trace_id=..., cost=...)). Never use print.",
    ),
    Prompt(
        "foundation.ids", "foundation", "backend/src/llmops/common/ids.py",
        "Create id helpers: new_trace_id() (uuid4 hex), new_span_id() (16 hex), new_id(prefix).",
    ),
    Prompt(
        "foundation.types", "foundation", "backend/src/llmops/common/types.py",
        "Create shared pydantic value types: Usage(input_tokens,output_tokens, total_tokens prop), "
        "ChatResult(text,model,usage,cost_usd,latency_ms,finish_reason,cache_hit), "
        "ToolResult(name,ok,output,error,latency_ms), Chunk(id,text,score,source,metadata), and "
        "an Environment str-Enum (dev/test/prod).",
    ),
    Prompt(
        "foundation.settings", "foundation", "backend/src/llmops/config/settings.py",
        "Create a pydantic-settings `Settings` (env_prefix LLMOPS_, reads .env) with fields for "
        "environment, Azure OpenAI endpoint/api_version/key, Azure Search endpoint/key, Document "
        "Intelligence endpoint, Content Safety endpoint, Cosmos endpoint/db, App Insights connection "
        "string, Langfuse host/keys, prompt_registry (git|langfuse|foundry), models_config_path, "
        "usecases_dir, api_cors_origins. Add `get_settings()` lru_cache singleton. No secrets in code.",
    ),
    Prompt(
        "foundation.models_config", "foundation", "backend/src/llmops/config/models_config.py",
        "Create the loader for platform/models.yaml: pydantic ModelsConfig(environments: dict[str, "
        "EnvAliases]) with resolve(alias, env)->deployment raising UnknownAliasError; and "
        "load_models_config(path) that validates the YAML and re-wraps failures as ConfigError.",
        depends_on=["foundation.errors"],
    ),
    # -- prompts --
    Prompt(
        "prompts.schema", "prompts", "backend/src/llmops/prompts/schema.py",
        "Create PromptSpec pydantic model mirroring a .prompt.yaml: id, version:int, labels:list[str], "
        "model_alias, temperature=0.2, inputs:list[str], template:str, eval_refs:list[str], "
        "changelog:list[str]. Add render(**vars)->str that substitutes {{var}} placeholders and raises "
        "PromptRenderError if any declared input is missing.",
        depends_on=["foundation.errors"],
    ),
    Prompt(
        "prompts.registry", "prompts", "backend/src/llmops/prompts/{base,git,langfuse,foundry,factory,loader}.py",
        "Create the prompt registry: base.py PromptRegistry Protocol (get(id,label)->PromptSpec, "
        "list(), push(spec)); git.py GitPromptRegistry that reads usecases/*/prompts/*.prompt.yaml from "
        "disk (fully working); langfuse.py and foundry.py adapters with the real call structure but "
        "`# TODO(wiring)` for the client construction; factory.py returning the registry named by "
        "settings.prompt_registry; loader.py load_prompt(id,label='prod').",
        depends_on=["prompts.schema", "foundation.settings"],
    ),
    # -- models --
    Prompt(
        "models.pricing", "models", "backend/src/llmops/models/pricing.py",
        "Create a ModelPrice model and a PRICES table (indicative Azure OpenAI prices: reasoning ~"
        "$5 in/$30 out per 1M tokens, mini/nano cheaper, embeddings) plus cost_usd(deployment, usage)->"
        "float. Clearly mark prices as indicative/configurable.",
    ),
    Prompt(
        "models.router", "models", "backend/src/llmops/models/router.py",
        "Create ModelRouter(config: ModelsConfig, env) with resolve(alias)->deployment (delegates to "
        "config.resolve, raising UnknownAliasError).",
        depends_on=["foundation.models_config"],
    ),
    Prompt(
        "models.client", "models", "backend/src/llmops/models/client.py",
        "Create an async ModelClient wrapping Azure OpenAI (openai SDK AsyncAzureOpenAI with "
        "DefaultAzureCredential token provider). chat(alias, messages, prompt_id=None, temperature) "
        "resolves the alias, opens a model_call span (llmops.observability.tracing), calls the API with "
        "tenacity retries, computes cost via pricing.cost_usd, and returns ChatResult. Graceful dev mock "
        "when no endpoint configured. `# TODO(wiring)` the credential/client construction.",
        depends_on=["models.router", "models.pricing"],
    ),
    # -- observability --
    Prompt(
        "observability.tracing", "observability", "backend/src/llmops/observability/tracing.py",
        "Create OpenTelemetry tracing using GenAI semantic conventions: init_tracing(settings), "
        "get_tracer(), a `span(name, **attrs)` contextmanager that sets attributes and records "
        "exceptions, model_call_span(alias, deployment, prompt_id, prompt_version) and tool_call_span("
        "name, mcp_server, args, expected_tool=None) which sets eval.expected_tool/eval.was_correct_tool "
        "when an expected tool is provided. Spans nest request>agent>model/tool.",
    ),
    Prompt(
        "observability.cost", "observability", "backend/src/llmops/observability/{cost,exporters}.py",
        "cost.py: attach app.cost_usd to the current span and provide aggregation helpers. exporters.py: "
        "configure the azure-monitor-opentelemetry App Insights exporter and the Langfuse exporter from "
        "settings; both no-op safely in dev. `# TODO(wiring)` where connection strings are required.",
        depends_on=["observability.tracing", "foundation.settings"],
    ),
    # -- guardrails --
    Prompt(
        "guardrails", "guardrails", "backend/src/llmops/guardrails/*.py",
        "Create the guardrail engine: base.py (GuardResult, Guard Protocol with check_input/check_output); "
        "engine.py GuardrailEngine that runs an ordered list of guards and raises GuardrailBlocked; and "
        "adapters content_safety.py (Azure AI Content Safety categories + Prompt Shields), pii.py (Presidio "
        "detect+redact), schema_validation.py (validate output against a pydantic/JSON schema), injection.py "
        "(Prompt Shields). Adapters have `# TODO(wiring)` and a dev mock that allows.",
        depends_on=["foundation.errors"],
    ),
    # -- data access + tools --
    Prompt(
        "data_access", "data", "backend/src/llmops/data_access/*.py",
        "Create the data-access layer: base.py DataSource Protocol; rag.py RagRetriever over Azure AI "
        "Search (retrieve(query,k)->list[Chunk]); sql.py SqlDataSource doing NL2SQL then a SAFE, read-only, "
        "parameterised, allow-listed execute (never writes); documents.py DocumentExtractor via Azure AI "
        "Document Intelligence; records.py RecordClient.get_record(system,id). `# TODO(wiring)` clients; dev mocks.",
        depends_on=["foundation.types"],
    ),
    Prompt(
        "tools", "tools", "backend/src/llmops/tools/*.py",
        "Create the reusable, MCP-compatible tool catalog: base.py Tool (name, description, pydantic "
        "input_schema, async run()->ToolResult); registry.py ToolRegistry loading platform/tools/registry.yaml; "
        "and search_knowledge.py, query_sql.py, extract_document.py, get_record.py wrapping the data-access "
        "classes. Each tool records a tool_call span.",
        depends_on=["data_access", "observability.tracing"],
    ),
    # -- orchestration --
    Prompt(
        "orchestration", "orchestration", "backend/src/llmops/orchestration/*.py",
        "Create the SEQUENTIAL pipeline runtime (NOT agent-to-agent): context.py PipelineContext (trace_id, "
        "inputs, shared memory, settings); agent.py Agent(name, role, prompt_id, tools, model_alias) with "
        "async run(ctx)->AgentResult (loads its prompt, calls ModelClient, may call tools, wrapped in an agent "
        "span); step.py Step wrapping an Agent/callable; pipeline.py Pipeline(name, steps) with run(input)->"
        "PipelineResult, loadable from usecases/<uc>/agents/pipeline.agent.yaml; state.py PipelineState "
        "persisted to Cosmos (checkpoint/resume) with `# TODO(wiring)` and an in-memory dev default.",
        depends_on=["prompts.registry", "models.client", "tools"],
    ),
    # -- evaluation --
    Prompt(
        "evaluation", "evaluation", "backend/src/llmops/evaluation/*.py",
        "Create the evaluation subsystem: golden.py (GoldenCase + load_golden(jsonl)); metrics/base.py (Metric "
        "Protocol); metrics/ragas.py (groundedness/relevance via Ragas, guarded import); metrics/deepeval.py "
        "(G-Eval writing quality, guarded import); metrics/tool_selection.py (CUSTOM: read the chosen tool from "
        "the trace, compare to expected; accuracy, per-tool precision/recall, wrong/missing-tool, arg "
        "correctness); metrics/judge.py (LLM-as-judge using the 'judge' alias + rubric); thresholds.py (load "
        "evaluators.yaml, baseline-relative rule + absolute floors, check(scores)->GateDecision); gate.py "
        "(EvaluationGate.run(usecase, subset|full)->GateReport, non-zero exit on fail); runner.py (run pipeline "
        "per case, collect trace, score, apply thresholds).",
        depends_on=["orchestration", "models.client"],
    ),
    # -- feedback --
    Prompt(
        "feedback", "feedback", "backend/src/llmops/feedback/*.py",
        "Create feedback: models.py FeedbackEvent(trace_id, kind: thumbs|edit|override, value, reason, "
        "user_hash, ts); store.py FeedbackStore (App Insights custom event + Cosmos, `# TODO(wiring)`, in-memory "
        "dev); service.py FeedbackService.capture() and to_golden_candidate() that turns a confirmed bad case "
        "into a golden-dataset candidate.",
        depends_on=["foundation.types"],
    ),
    # -- api --
    Prompt(
        "api", "api", "backend/src/llmops/api/*.py",
        "Create the FastAPI control plane: main.py (CORS from settings, exception handlers mapping LLMOpsError "
        "to JSON, OpenTelemetry middleware, lifespan init, routers under /api/v1, /health); deps.py (Depends "
        "providers for settings, registries, router, engine); and routers health/prompts/models/evaluations/"
        "traces/costs/feedback/agents/guardrails/usecases implementing the exact routes in ARCHITECTURE_SPEC "
        "section 3. Where data must come from App Insights/Langfuse, return a clearly-labelled placeholder and "
        "mark `# TODO(wiring)`.",
        depends_on=["evaluation", "feedback", "guardrails", "prompts.registry", "models.router"],
    ),
    Prompt(
        "eval_cli", "api", "backend/evals/run.py",
        "Create the CI evaluation entrypoint: `python evals/run.py --usecase apix --subset changed|all "
        "--fail-under baseline` builds an EvaluationGate, runs it, prints a summary, and sets a non-zero exit "
        "code if the gate fails (this is what blocks a pull request).",
        depends_on=["evaluation"],
    ),
    # -- frontend --
    Prompt(
        "frontend", "frontend", "frontend/**",
        "Create the React 18 + TypeScript (Vite) 'LLMOps Console': a typed API client (VITE_API_BASE), React "
        "Router v6, TanStack React Query, and pages Dashboard, Prompts (+version compare), Models, Evaluations "
        "(gate reports + Run), Traces (+ SpanTree viewer), Costs, Agents, Guardrails, Feedback, Onboarding. "
        "Components: Layout, Sidebar, TopBar, DataTable, StatTile, SpanTree, MetricBadge, CodeBlock, EmptyState. "
        "Restrained light theme (navy/teal). Where a backend endpoint is a placeholder, show a clearly-labelled "
        "placeholder state. Include Dockerfile (nginx) and README.",
        depends_on=["api"],
    ),
    # -- infra + ci --
    Prompt(
        "infra", "infra", "infra/**",
        "Create Bicep IaC: main.bicep plus modules openai, search, containerapps (env + backend + frontend), "
        "apim, cosmos, keyvault, appinsights, contentsafety, storage, langfuse (Container App + PostgreSQL). Use "
        "Managed Identity, params, outputs. Add infra/docker-compose.yml for local dev (backend, frontend, "
        "langfuse + postgres).",
    ),
    Prompt(
        "cicd", "infra", ".github/workflows/*.yml",
        "Create GitHub Actions with OIDC federated login to Azure (no stored keys): pr-checks.yml (lint, type "
        "check, tests, then the EVALUATION GATE `python backend/evals/run.py --subset changed --fail-under "
        "baseline` which blocks merge on regression); eval-full.yml (full golden run on merge + nightly); "
        "deploy.yml (dev->test->prod via GitHub Environments with required reviewers; build+push images to ACR; "
        "deploy to Container Apps; prod canary 10%->100% with rollback); index-refresh.yml (scheduled re-index). "
        "Add CODEOWNERS requiring review on /usecases prompts+agents and /platform.",
    ),
]


# ---------------------------------------------------------------------------------------
# USE-CASE PROMPTS — run these in the client env to build a use case on the framework.
# The framework is done; these fill usecases/<name>/ with prompts, agents, evals.
# ---------------------------------------------------------------------------------------
USE_CASE_PROMPTS: list[Prompt] = [
    Prompt(
        "apix.pipeline", "usecase:apix", "usecases/apix/agents/pipeline.agent.yaml",
        "Using the platform's Pipeline schema (see llmops.orchestration.pipeline and "
        "usecases/_template/agents/pipeline.agent.yaml), define the APIX pipeline as SEQUENTIAL steps: "
        "(1) transcript prep/segmentation; (2) dimension-analysis agents for sales, customer experience, "
        "retention, compliance/script adherence; (3) extraction agent (escalations, sentiment, sales "
        "outcomes); (4) scoring/aggregation into a /100 composite using the program's weights; (5) "
        "coaching-recommendation agent (practical steps + risk flags). Each step references a prompt id and, "
        "where needed, a tool from the catalog. Programs Telesales and WCC use different scoring config.",
    ),
    Prompt(
        "apix.prompts", "usecase:apix", "usecases/apix/prompts/*.prompt.yaml",
        "Create one .prompt.yaml per APIX agent (dimension-sales, dimension-cx, dimension-retention, "
        "compliance, extraction, scoring, coaching-report) following the PromptSpec schema: id, version, "
        "labels:[prod], model_alias (reason for analysis/coaching, bulk for simple extraction), inputs, "
        "template that instructs the model to use ONLY the transcript evidence and cite it, eval_refs pointing "
        "at the golden datasets, changelog.",
    ),
    Prompt(
        "apix.evals", "usecase:apix", "usecases/apix/evals/{golden.telesales.jsonl,golden.wcc.jsonl,evaluators.yaml}",
        "Create APIX golden datasets (JSONL) per program with ~50-200 cases: each has an input (transcript_id + "
        "program), grading (must_cite_evidence, expected_score_band, must_flag) and metadata. Create "
        "evaluators.yaml with metrics groundedness (min 0.9), scoring agreement, extraction F1, coaching writing "
        "quality (judge), and per-metric thresholds + a 0.02 baseline-regression allowance.",
    ),
    Prompt(
        "hiring.pipeline", "usecase:hiring", "usecases/hiring/agents/pipeline.agent.yaml",
        "Define the Hiring Intelligence pipeline as SEQUENTIAL steps: intake/router -> resume parse & rank "
        "(RAG over the job description + rubric) -> screening Q&A (RAG over role/policy) -> scoring & summary for "
        "a human recruiter. Wire the ATS/requisition tools from the catalog (search_knowledge, get_record, "
        "query_sql). Emphasise fairness; the recruiter decides.",
    ),
    Prompt(
        "hiring.evals", "usecase:hiring", "usecases/hiring/evals/*",
        "Create Hiring golden cases and evaluators.yaml, including tool-selection cases (expected ATS tool + "
        "args) so the custom tool_selection metric can score correct-tool usage, plus RAG groundedness, ranking "
        "quality, and fairness checks.",
    ),
]


ALL_PROMPTS = FRAMEWORK_PROMPTS + USE_CASE_PROMPTS


def _print(prompts: list[Prompt]) -> None:
    for p in prompts:
        print(f"\n### [{p.id}]  ->  {p.target}")
        if p.depends_on:
            print(f"# depends on: {', '.join(p.depends_on)}")
        print(SHARED_CONTEXT)
        print()
        print(p.prompt)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LLMOps Copilot prompt catalog")
    parser.add_argument("--list", action="store_true", help="list prompt ids")
    parser.add_argument("--show", metavar="AREA", help="print prompts for one area (or 'all')")
    parser.add_argument("--emit", metavar="FILE", help="write the full catalog to a Markdown file")
    args = parser.parse_args(argv)

    if args.list:
        for p in ALL_PROMPTS:
            print(f"{p.id:28} {p.area:16} {p.target}")
        return 0
    if args.emit:
        lines = ["# LLMOps — Copilot prompt catalog\n", f"\n> {SHARED_CONTEXT}\n"]
        for p in ALL_PROMPTS:
            lines.append(f"\n## {p.id} — `{p.target}`\n")
            if p.depends_on:
                lines.append(f"_depends on: {', '.join(p.depends_on)}_\n")
            lines.append(f"\n{p.prompt}\n")
        from pathlib import Path

        Path(args.emit).write_text("".join(lines), encoding="utf-8")
        print(f"wrote {args.emit} with {len(ALL_PROMPTS)} prompts")
        return 0
    area = args.show or "all"
    selected = ALL_PROMPTS if area == "all" else [p for p in ALL_PROMPTS if p.area == area]
    if not selected:
        areas = sorted({p.area for p in ALL_PROMPTS})
        print(f"no prompts for area '{area}'. Known areas: {', '.join(areas)}", file=sys.stderr)
        return 1
    _print(selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
