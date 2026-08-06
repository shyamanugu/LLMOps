# LLMOps Platform

This repository is the **reusable framework** for running Large Language Model (LLM)
applications on Azure with enterprise-grade operations: versioned prompts, config-driven
model routing, an evaluation gate on every change, full request/model/tool/agent tracing,
cost metering, guardrails, a reusable data-access and tool layer, sequential agent
pipelines, a serving gateway, and a feedback loop. It implements the platform described in
the **v2 deck** (`../5thAug/v2/research-brief.md`). Two use cases ride on top of it:
**APIX** (contact-center call coaching) and **Hiring Intelligence** — each is scaffolded
here as a template and the client-specific content (prompts, agents, evals) is filled in
later via `copilot_prompts.py`.

Read `ARCHITECTURE_SPEC.md` first — it is the build contract every module conforms to.

## What this is (and is not)

- **Is**: the shared platform (`backend/src/llmops/`, `platform/`, `frontend/`, `infra/`,
  `.github/`) plus empty-shaped use-case folders under `usecases/`.
- **Is not**: the finished APIX/Hiring prompt content or golden data — those are generated
  into the client environment using the per-use-case `COPILOT_PROMPTS.md` files.

## Monorepo map

```
codebase/
├─ ARCHITECTURE_SPEC.md   the build contract (read first)
├─ README.md              this file
├─ checklist.html         setup checklist (Azure + GitHub + local) — HTML companion to docs/setup-guide.md
├─ todo.html              index of every TODO/placeholder in the code (client wiring points)
├─ copilot_prompts.py     generator: emits the Copilot prompts that fill each use case's content
├─ docs/                  hld, lld, workflows, design-principles, security, setup-guide, adr/, diagrams/
├─ backend/               Python 3.11 FastAPI control-plane + pipeline runtime (package: llmops)
│  └─ src/llmops/         config, common, prompts, models, observability, guardrails,
│                         data_access, tools, orchestration, evaluation, feedback, api
├─ frontend/              React 18 + TypeScript (Vite) "LLMOps Console"
├─ platform/              config-as-code: models.yaml, tools/registry.yaml, evaluators/, gateway/
├─ usecases/             _template/ + apix/ + hiring/ (scaffolds + COPILOT_PROMPTS.md)
├─ infra/                 Bicep (Container Apps, APIM, AI Search, Cosmos, ...) + docker-compose.yml
└─ .github/               CODEOWNERS + workflows (pr-checks, eval-full, deploy, index-refresh)
```

## How it maps to the v2 deck (12 components)

| v2 component | Where it lives |
|---|---|
| Source control & CI/CD | `.github/workflows/*`, `CODEOWNERS`, `infra/` |
| Prompt registry & management | `backend/src/llmops/prompts/*`, `usecases/*/prompts/*` |
| Model catalog & routing | `backend/src/llmops/models/*`, `platform/models.yaml` |
| Evaluation engine & gate | `backend/src/llmops/evaluation/*`, `backend/evals/run.py` |
| Observability & tracing (+ cost) | `backend/src/llmops/observability/*` |
| Guardrails engine | `backend/src/llmops/guardrails/*` |
| Data-access (RAG/SQL/docs) | `backend/src/llmops/data_access/*` |
| Reusable tool catalog (MCP) | `backend/src/llmops/tools/*`, `platform/tools/registry.yaml` |
| Orchestration / pipeline runtime | `backend/src/llmops/orchestration/*` |
| Serving & gateway | `backend/src/llmops/api/*`, `platform/gateway/*` |
| Feedback capture & analytics | `backend/src/llmops/feedback/*` |
| Console (view all of the above) | `frontend/*` |

MCP = Model Context Protocol (a standard way to describe/expose tools to models).

## Quickstart

Prerequisites: Python 3.11+, Node 18+, Docker (for the local stack). For local dev, Azure
services degrade to mocks where a live client is not wired (see `todo.html`) — you can run
the API, Console, and an offline eval without any Azure account.

### Backend (control-plane API + runtime)

```bash
cd backend
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                               # edit endpoints; leave keys blank to use mocks/MI
uvicorn llmops.api.main:app --reload --port 8000   # http://localhost:8000/api/v1/health
# run a use-case pipeline locally:
python pipelines_cli.py --usecase apix --input '{"transcript_id":"demo"}'
# run an offline eval subset:
python evals/run.py --usecase apix --subset changed --fail-under baseline
```

### Frontend (LLMOps Console)

```bash
cd frontend
npm install
cp .env.example .env        # set VITE_API_BASE=http://localhost:8000/api/v1
npm run dev                 # http://localhost:5173
```

### Local Docker Compose (full stack)

```bash
cd infra
docker compose up --build   # API + Console + self-hosted Langfuse (+ Postgres)
# API   -> http://localhost:8000/api/v1
# Console -> http://localhost:5173
# Langfuse -> http://localhost:3000
```

## Where to look

- **Understand the design**: `docs/hld.md` (high-level), then `docs/lld.md` (per-package
  low-level), with diagrams under `docs/diagrams/*.mmd` (Mermaid).
- **Run/operate it**: `docs/setup-guide.md` (prose) and `checklist.html` (tick-box) to
  stand up Azure + GitHub; `docs/workflows.md` for the operational flows (prompt change,
  model adoption, eval gate, feedback, onboarding).
- **Defend the choices**: `docs/adr/` (Architecture Decision Records) and
  `docs/design-principles.md`.
- **Security posture**: `docs/security.md` (Zero Trust, identity, secrets, OWASP LLM
  Top 10 mapping, PII handling).
- **Find the client wiring points**: `todo.html` indexes every `TODO(...)`/
  `NotImplementedError` placeholder — these are the lines to complete in the client tenant.
- **Fill in a use case's content**: `copilot_prompts.py` (the generator) and each
  `usecases/<uc>/COPILOT_PROMPTS.md` (the exact Copilot prompts to run in the client
  environment to produce that use case's prompts, agents, and evals).

## Engineering standards

Python 3.11+ with full type hints, pydantic v2, async I/O, structured logging (never
`print`), a custom exception hierarchy, and `ruff`/`black`/`mypy` clean. React functional
components with a typed API client, no `any`, ESLint clean. Every client/env-specific gap
is an explicit `TODO(...)` indexed in `todo.html` — never a silent stub. See section 0 of
`ARCHITECTURE_SPEC.md`.
