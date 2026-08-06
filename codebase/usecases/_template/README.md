# Use case: _template

This is the **shape** every use case follows. Copy this folder to `usecases/<newname>/`
and fill in the content. The shared platform (CI/CD, evaluation gate, tracing, tool
catalog, gateway, guardrail engine, model router) is inherited from `platform/` and
`backend/src/llmops/` — you do **not** rebuild it. You define only what is specific to this
use case.

## Folder shape

```
usecases/<name>/
├─ README.md              this file (describe the use case + pipeline)
├─ config/
│  └─ datasources.yaml    RAG index, SQL tables, document sources, systems of record
├─ agents/
│  └─ pipeline.agent.yaml the sequential pipeline: ordered steps -> prompt + tools + model
├─ prompts/
│  └─ *.prompt.yaml       one YAML file per prompt (generated via COPILOT_PROMPTS.md)
├─ evals/
│  ├─ evaluators.yaml     which metrics run + thresholds (baseline delta + absolute floors)
│  └─ golden.*.jsonl      golden dataset(s) — ground truth, run as a gate on every change
├─ tools/                 use-case-specific tools ONLY (reuse platform tools first)
└─ COPILOT_PROMPTS.md     the exact Copilot prompts to generate this use case's content
```

## What you must define (per use case)

1. **Data sources** (`config/datasources.yaml`) and their connectors.
2. **Pipeline design** (`agents/pipeline.agent.yaml`) — ordered steps, each mapping to a
   prompt, a set of tools, and a model alias. Sequential, not agent-to-agent.
3. **Prompts** (`prompts/*.prompt.yaml`) — versioned YAML artifacts with `eval_refs`.
4. **Golden dataset + thresholds** (`evals/`) — SME-authored first, grown from real
   traffic, reviewed again by SMEs.
5. **Tools** — reuse `search_knowledge` / `query_sql` / `extract_document` / `get_record`
   from the catalog; add new ones under `tools/` only if needed.
6. **Guardrail policy** — tune the guardrail list for this use case's risks.
7. **Dashboards** — cost/quality views.

## What you inherit (do not rebuild)

Source control + CI/CD, the evaluation engine and gate, observability + cost metering, the
guardrail engine, the data-access framework, the reusable tool catalog, the pipeline
runtime, the serving gateway, identity + secrets, and the feedback loop.

## How to generate the content

Run the prompts in `COPILOT_PROMPTS.md` (or `python ../../copilot_prompts.py --usecase
<name>`) inside the client environment to produce first drafts of the prompts, pipeline,
and evals. Then have an SME review the golden data and set thresholds from a baseline run.
See `../../docs/workflows.md` section 5 (onboarding).
