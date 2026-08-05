# LLMOps Implementation Overview

This is an implementation document, not an options paper. It describes the concrete Large Language Model Operations (LLMOps) setup we are putting in place for your Azure and GitHub environment, using the APIX pipeline as the running example and Hiring Intelligence as a second, lighter case. It is enterprise-grade, and it is reusable: the same components serve any future use case without a rebuild.

## How to read this

Every component document follows the same three-part shape:

- **Today** — what the APIX and Hiring teams already do (some of this is assumption, to confirm with you).
- **Our setup** — the concrete files, code, and configuration we put in place.
- **What changes** — the specific delta and the small migration step to get there.

We lead with the delta on purpose. The point of these documents is not to describe LLMOps in the abstract; it is to show exactly what is different from how the teams work now, and why that difference matters. Where an alternative tool or approach is worth naming, it gets a one-line footnote, not a comparison table.

## Two pipelines, one platform

Both APIX and Hiring Intelligence are **sequential agent pipelines** — an ordered set of steps, each step running a prompt against a model, some steps calling tools. They are not agents talking to other agents. That keeps the runtime predictable and makes each step separately testable and evaluable.

APIX (contact-center coaching) is the worked example throughout: it takes call transcripts, scores them on dimensions, and produces a coaching report. Hiring Intelligence (job descriptions, rubrics, candidate scoring) reuses the exact same platform components; it is still being scoped, so we keep it light here.

The platform is built so that a third or fourth use case is just another subfolder under `prompts/`, `agents/`, and `evals/` — not new infrastructure.

## The order we onboard components

The first thing we set up is source control and Continuous Integration / Continuous Deployment (CI/CD). Everything else plugs into it. Then we onboard the remaining components one at a time, each landing in the same repository and flowing through the same pipeline:

1. **Source control and CI/CD** — the monorepo and the GitHub Actions workflows. The backbone. Every change to a prompt, a model choice, or an agent step flows through here and must pass the evaluation gate before it can deploy.
2. **Prompt management** — one YAML file per prompt, versioned, with an evaluation gate on every change and a runtime registry for rollback and comparison.
3. **Model management** — a single `models.yaml` mapping task aliases to Azure OpenAI deployments, so a model swap is a reviewed config change.
4. **Evaluation** — golden datasets plus concrete scoring mechanisms (Ragas, DeepEval, and custom Python for tool selection), wired into the gate.
5. **Observability** — OpenTelemetry spans capturing every model call, tool call, and agent session, exported to Azure Application Insights and Langfuse.
6. **Guardrails and safety** — Azure Content Safety checks and Personally Identifiable Information (PII) redaction, placed around each model call.
7. **Data and Retrieval-Augmented Generation (RAG)** — the ingest-to-index pipeline feeding Azure AI Search.
8. **Serving and deployment** — Azure Container Apps hosting each pipeline step behind Azure API Management (APIM), with canary release and automatic rollback.
9. **Feedback and improvement** — capturing real usage, triaging it into the golden set, fixing, and re-evaluating.

The evaluation gate is the thread running through all of this: no prompt, model, or agent change reaches production without being scored against a golden dataset and clearing its thresholds. That single rule is what makes the setup enterprise-grade rather than a collection of scripts.

## The monorepo backbone

Everything lives in one repository. One subfolder per use case sits inside `prompts/`, `agents/`, and `evals/`, so the shared machinery (loaders, router, tracing, workflows) is written once and reused.

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

The next document goes into this layout and the CI/CD workflows in detail, because that is the first thing we stand up. Read the rest in the order above; each one names what changes from today first.
