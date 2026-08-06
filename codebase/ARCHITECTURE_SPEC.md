# ARCHITECTURE_SPEC — the build contract (read this first)

> This is the single source of truth for the `codebase/` monorepo. Every file must conform to the interfaces,
> names, conventions, and directory layout defined here so that independently-generated modules fit together.
> The codebase implements the **LLMOps platform** described in the v2 deck (`5thAug/v2`). It is the **reusable
> framework** only — use-case code (APIX, Hiring) is scaffolded as templates and completed later via
> `copilot_prompts.py`. Stack: **Python 3.11 backend (FastAPI)** + **React 18 + TypeScript (Vite) frontend**,
> deployed on **Azure** (Container Apps), source + CI/CD on **GitHub**.

## 0. Non-negotiable engineering standards
- **Python**: 3.11+, full type hints, `pydantic` v2 for models/settings, `async` where I/O-bound, Google-style
  docstrings on every public function/class, module docstring at top. Structured logging (never `print`).
  Custom exception hierarchy. No secrets in code — everything via `Settings`. `ruff` + `black` + `mypy` clean.
- **Placeholders**: where client/env-specific wiring is required, raise `NotImplementedError("TODO(<what>): ...")`
  or leave a `# TODO(<area>): <precise instruction>` — never leave silent gaps. Every TODO is indexed in `todo.html`.
- **React/TS**: functional components, hooks, typed API client, no `any`, ESLint clean, component-per-file.
- **Tests**: `pytest`; unit tests for pure logic (router, thresholds, pricing, schema); mark integration tests
  `@pytest.mark.integration` (skipped without live Azure).
- **Design principles applied** (state them in module docstrings where relevant): separation of concerns; dependency
  inversion (adapters behind interfaces); config-as-code; fail-safe defaults; least privilege; everything observable;
  reuse over rebuild; twelve-factor config.

## 1. Directory layout (authoritative)
```
codebase/
├─ ARCHITECTURE_SPEC.md   README.md   checklist.html   todo.html   copilot_prompts.py   .gitignore   LICENSE
├─ docs/         hld.md  lld.md  workflows.md  setup-guide.md  design-principles.md  security.md  adr/*  diagrams/*.mmd
├─ backend/
│  ├─ pyproject.toml  requirements.txt  Dockerfile  .env.example  Makefile  README.md
│  ├─ src/llmops/
│  │  ├─ __init__.py            # exports version
│  │  ├─ config/                # settings.py (pydantic-settings), models_config.py (loads platform/models.yaml)
│  │  ├─ common/                # logging.py, errors.py, types.py, ids.py
│  │  ├─ prompts/               # schema.py, loader.py, registries: git.py, langfuse.py, foundry.py, factory.py
│  │  ├─ models/                # router.py, client.py (AzureOpenAI wrapper), pricing.py
│  │  ├─ observability/         # tracing.py, cost.py, exporters.py
│  │  ├─ guardrails/            # engine.py, content_safety.py, pii.py, schema_validation.py, injection.py, base.py
│  │  ├─ data_access/           # base.py, rag.py, sql.py, documents.py, records.py
│  │  ├─ tools/                 # base.py, registry.py, search_knowledge.py, query_sql.py, extract_document.py, get_record.py
│  │  ├─ orchestration/         # pipeline.py, agent.py, step.py, state.py, context.py
│  │  ├─ evaluation/            # runner.py, gate.py, golden.py, thresholds.py, metrics/{ragas.py,deepeval.py,tool_selection.py,judge.py,base.py}
│  │  ├─ feedback/              # models.py, store.py, service.py
│  │  └─ api/                   # main.py, deps.py, routers/{health,prompts,models,evaluations,traces,costs,feedback,agents,guardrails,usecases}.py
│  ├─ tests/                    # unit/*, integration/*, conftest.py
│  ├─ evals/                    # run.py (CLI entrypoint used by CI), README.md
│  └─ pipelines_cli.py          # run a use-case pipeline locally
├─ frontend/                    # Vite + React + TS "LLMOps Console"
│  ├─ package.json  vite.config.ts  tsconfig.json  index.html  Dockerfile  nginx.conf  .env.example  README.md
│  └─ src/  main.tsx App.tsx router.tsx  api/{client.ts,types.ts,endpoints/*}  components/*  pages/*  hooks/*  store/*  theme/*
├─ platform/                    # config-as-code (mirrors v2 repo)
│  ├─ models.yaml  tools/registry.yaml  evaluators/defaults.yaml  gateway/apim-policies/*.xml
├─ usecases/                    # _template/ + apix/ + hiring/  (scaffolds + per-usecase COPILOT_PROMPTS.md)
├─ infra/                       # main.bicep  modules/*.bicep  params/*.json  docker-compose.yml
└─ .github/  CODEOWNERS  workflows/{pr-checks,eval-full,deploy,index-refresh}.yml
```

## 2. Component → v2 deck mapping (must all exist)
| v2 component | Code location |
|---|---|
| Source control & CI/CD | `.github/workflows/*`, `CODEOWNERS`, `infra/` |
| Prompt registry & management | `backend/src/llmops/prompts/*`, `platform/*` |
| Model catalog & routing | `backend/src/llmops/models/*`, `platform/models.yaml` |
| Evaluation engine & gate | `backend/src/llmops/evaluation/*`, `backend/evals/run.py` |
| Observability & tracing (+ cost) | `backend/src/llmops/observability/*` |
| Guardrails engine | `backend/src/llmops/guardrails/*` |
| Data-access (RAG/SQL/docs) | `backend/src/llmops/data_access/*` |
| Reusable tool catalog (MCP) | `backend/src/llmops/tools/*`, `platform/tools/registry.yaml` |
| Orchestration / pipeline runtime | `backend/src/llmops/orchestration/*` |
| Serving & gateway | `backend/src/llmops/api/*`, `platform/gateway/*`, `backend/Dockerfile` |
| Feedback capture & analytics | `backend/src/llmops/feedback/*` |
| Console (view all of the above) | `frontend/*` |

## 3. Core interfaces (implement to these EXACT signatures)

### config/settings.py
```python
class Settings(BaseSettings):  # pydantic-settings, env_prefix="LLMOPS_", reads .env
    environment: str = "dev"                 # dev|test|prod  (APP_ENV)
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2025-01-01-preview"
    azure_search_endpoint: str = ""
    cosmos_endpoint: str = ""
    content_safety_endpoint: str = ""
    applicationinsights_connection_string: str = ""
    langfuse_host: str = ""; langfuse_public_key: str = ""; langfuse_secret_key: str = ""
    prompt_registry: str = "git"             # git|langfuse|foundry
    models_config_path: str = "platform/models.yaml"
    # ... key vault refs; use managed identity in Azure
def get_settings() -> Settings: ...          # lru_cache singleton
```

### prompts
```python
# schema.py
class PromptSpec(BaseModel):  # mirrors the .prompt.yaml
    id: str; version: int; labels: list[str]; model_alias: str; temperature: float = 0.2
    inputs: list[str]; template: str; eval_refs: list[str] = []; changelog: list[str] = []
    def render(self, **vars) -> str: ...      # fills {{var}} placeholders; validates all inputs present
# base registry interface
class PromptRegistry(Protocol):
    def get(self, prompt_id: str, label: str = "prod") -> PromptSpec: ...
    def list(self) -> list[PromptSpec]: ...
    def push(self, spec: PromptSpec) -> None: ...     # Git->registry sync (langfuse/foundry)
# loader.py
def load_prompt(prompt_id: str, label: str = "prod") -> PromptSpec: ...   # uses factory(get_settings().prompt_registry)
# git.py GitPromptRegistry reads usecases/*/prompts/*.prompt.yaml ; langfuse.py, foundry.py are adapters (TODO client wiring)
```

### models
```python
# router.py
class ModelRouter:
    def __init__(self, config: ModelsConfig, env: str): ...
    def resolve(self, alias: str) -> str: ...        # alias -> Azure deployment name; raises UnknownAliasError
# client.py
class ModelClient:                                   # async wrapper over Azure OpenAI, emits a tracing span + cost
    async def chat(self, *, alias: str, messages: list[dict], prompt_id: str|None=None,
                   temperature: float=0.2) -> ChatResult: ...   # ChatResult has text, usage, cost_usd, model, latency_ms
# pricing.py  PRICES: dict[str, ModelPrice]; def cost_usd(deployment, usage) -> float
```

### observability
```python
# tracing.py  — OpenTelemetry, GenAI semantic conventions. Spans nest: request>agent>model/tool.
def init_tracing(settings: Settings) -> None: ...
def get_tracer() -> Tracer: ...
@contextmanager
def span(name: str, **attrs): ...                    # sets attributes, records exceptions
def model_call_span(alias, deployment, prompt_id, prompt_version): ...   # yields span; caller sets usage+cost
def tool_call_span(name, mcp_server, args, expected_tool=None): ...      # sets eval.was_correct_tool if expected given
# cost.py  attach app.cost_usd to spans; helpers to aggregate. exporters.py: App Insights (azure-monitor-opentelemetry) + Langfuse.
```

### guardrails
```python
# base.py
class GuardResult(BaseModel): allowed: bool; category: str|None; detail: str|None; redacted_text: str|None=None
class Guard(Protocol):
    async def check_input(self, text: str, ctx: dict) -> GuardResult: ...
    async def check_output(self, text: str, ctx: dict) -> GuardResult: ...
# engine.py GuardrailEngine runs an ordered list of Guards; content_safety.py, pii.py (Presidio/Azure Language),
# schema_validation.py (pydantic/json-schema), injection.py (Prompt Shields). All adapters have TODO client wiring.
```

### data_access + tools
```python
# data_access/base.py  class DataSource(Protocol): async def query(self, q, **kw) -> Any
# rag.py RagRetriever(search_endpoint,index) -> retrieve(query, k) -> list[Chunk]
# sql.py SqlDataSource -> nl2sql + safe parameterised read-only execute (allow-listed tables)
# documents.py DocumentExtractor -> Azure AI Document Intelligence extract(file) -> ExtractedDoc
# records.py RecordClient -> get_record(system, id)
# tools/base.py  class Tool(BaseModel): name; description; input_schema(pydantic); async def run(self, **kwargs)->ToolResult
# tools/registry.py ToolRegistry loads platform/tools/registry.yaml; get(name); MCP-compatible descriptions.
# tools: search_knowledge(RAG), query_sql(SQL), extract_document(Doc Intel), get_record(systems).
```

### orchestration
```python
# agent.py  class Agent: name; role; prompt_id; tools:list[str]; model_alias; async def run(self, ctx: PipelineContext) -> AgentResult
# step.py   a pipeline step wraps an Agent or a function; records an agent span.
# pipeline.py  class Pipeline: name; steps:list[Step]; async def run(self, input: dict) -> PipelineResult   # sequential (NOT A2A)
#              loads from usecases/<uc>/agents/pipeline.agent.yaml
# state.py  PipelineState persisted to Cosmos DB (checkpoint/resume) — adapter with TODO wiring; in-memory default for dev.
# context.py PipelineContext carries trace_id, inputs, shared memory, settings.
```

### evaluation
```python
# golden.py  load_golden(path) -> list[GoldenCase]; GoldenCase(id,input,grading,meta)
# metrics/base.py  class Metric(Protocol): name; async def score(self, case, output, trace) -> MetricScore
# metrics: ragas.py (groundedness,relevance via Ragas), deepeval.py (writing/G-Eval), tool_selection.py (custom, from trace),
#          judge.py (LLM-as-judge with rubric using a small model alias).
# thresholds.py  load evaluators.yaml -> Thresholds; check(scores) -> GateDecision (baseline-relative + absolute floors)
# gate.py  EvaluationGate.run(usecase, subset|full) -> GateReport (pass/fail per metric, blocks CI)
# runner.py orchestrates: for each golden case run pipeline, collect trace, score with metrics, apply thresholds.
```

### feedback
```python
# models.py FeedbackEvent(trace_id, kind: thumbs|edit|override, value, reason, user_hash, ts)
# store.py FeedbackStore (App Insights custom events + Cosmos) ; service.py FeedbackService.capture(...) + to_golden_candidate(...)
```

### api (FastAPI) — routes (all under /api/v1)
```
GET  /health                              -> liveness/readiness
GET  /prompts                             -> list prompts (id, version, labels)
GET  /prompts/{id}                        -> PromptSpec
POST /prompts/{id}/render                 -> render with vars (dev helper)
GET  /models                              -> aliases + resolved deployments (per env)
GET  /evaluations                         -> recent gate reports
POST /evaluations/run                     -> run gate for a usecase (subset|full) [async task]
GET  /traces                              -> recent traces (from App Insights/Langfuse) [read-through, TODO wiring]
GET  /costs                               -> cost aggregates by usecase/day/model
POST /feedback                            -> capture a FeedbackEvent
GET  /agents                              -> list pipelines/agents from usecases/*/agents
GET  /guardrails                          -> configured guardrails + last events
GET  /usecases                            -> onboarded use cases + status
```
`main.py` wires routers, CORS, exception handlers, OpenTelemetry middleware, lifespan (init tracing/settings).
`deps.py` provides `get_settings`, registries, router, engine via FastAPI Depends.

## 4. Frontend (LLMOps Console) — routes/pages
`/` Dashboard (KPI tiles: requests, p95 latency, cost/day, quality trend, guardrail events) ·
`/prompts` (list + detail + version compare) · `/models` (aliases table) · `/evaluations` (gate reports + run) ·
`/traces` (trace list + span tree viewer) · `/costs` (cost by usecase/model/day) · `/agents` (pipelines) ·
`/guardrails` (list + events) · `/feedback` (feedback stream) · `/onboarding` (new use-case checklist).
`api/client.ts` = typed fetch wrapper (base URL from `VITE_API_BASE`); `api/types.ts` mirrors backend pydantic models;
`api/endpoints/*` one module per resource. Components: `Layout`, `Sidebar`, `TopBar`, `DataTable`, `StatTile`,
`SpanTree`, `MetricBadge`, `CodeBlock`, `EmptyState`. Theme: light, restrained (navy/teal), accessible. Use React Query
for data fetching, React Router v6. All API data typed; where the backend endpoint is a TODO, show a clearly-labelled
"mock/placeholder" state (documented in todo.html) — never crash.

## 5. platform/models.yaml (shape)
```yaml
environments:
  prod: { aliases: { reason: gpt-5.2, bulk: gpt-5-mini, judge: gpt-5-mini, voice: gpt-realtime-1.5, embed: text-embedding-3-large } }
  test: { aliases: { reason: gpt-5-mini, bulk: gpt-5-mini, judge: gpt-5-mini, voice: gpt-realtime-1.5, embed: text-embedding-3-large } }
  dev:  { aliases: { reason: gpt-5-mini, bulk: gpt-5-mini, judge: gpt-5-mini, voice: gpt-realtime-1.5, embed: text-embedding-3-large } }
```

## 6. Conventions summary
- Package import root: `llmops` (e.g. `from llmops.models.router import ModelRouter`).
- IDs: `trace_id`, `span_id` are UUID4 hex; use `common/ids.py`.
- All async I/O; sync wrappers only in CLI.
- Errors subclass `llmops.common.errors.LLMOpsError`.
- Nothing prints; use `llmops.common.logging.get_logger(__name__)`.
- Every adapter that needs a live Azure/Langfuse client marks the client-construction line with
  `# TODO(wiring): construct <client> from settings / managed identity` and degrades gracefully in dev (mock).
