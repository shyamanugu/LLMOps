# LLMOps Approach & Activities

## The approach in plain terms

Afni already has two working systems built by the product team: **APIX** (Afni
Performance Intelligence Index) and **Hiring Intelligence**. Both are agent
**pipelines** — a fixed sequence of steps that run one after another. They are
not agent-to-agent (A2A) systems where agents negotiate with each other; each
step hands off to the next in a known order.

We are **not rebuilding these use cases**. They run today. What is missing is the
operational layer around them: consistent version control for prompts and models,
proper tracing of every request, an evaluation framework that can gate releases,
guardrails, and a repeatable deploy path.

LLMOps (Large Language Model Operations) is that layer. The plan is to:

1. **Wrap** the two existing pipelines with tracing, evaluation, and release
   controls — without changing what they do.
2. **Standardize** how prompts, models, data, and deployments are managed so both
   pipelines follow the same rules.
3. **Make it reusable** so any future use case plugs into the same setup instead
   of reinventing observability and evaluation each time.

APIX and Hiring are the grounding examples. The framework has to generalize past
them — that is the client's explicit requirement.

## The nine workstreams (A–I)

### A. Discovery & current-state assessment

- **Goal:** Know exactly what exists before we change anything.
- **Activities:**
  - Inventory both pipelines: list every agent/step, its prompt, its model, its
    tools, and its data sources.
  - Map current logging and any existing evaluation or spot-checking.
  - Record where prompts live today (code, notebooks, portal) and how models are
    referenced.
  - Identify gaps against the target state.
- **Produces:** A confirmed pipeline map per use case and the filled-in as-is /
  to-be table (see doc 02).

### B. Foundation

- **Goal:** A clean home for code, config, and infrastructure.
- **Activities:**
  - Set up a GitHub monorepo with a clear structure:
    `/prompts /agents /evals /src /pipelines /infra /dashboards`.
  - Stand up the Azure landing zone: Entra ID (identity), Key Vault (secrets),
    API Management (APIM, the gateway), and model deployments.
- **Produces:** Repo skeleton, landing zone, and a place to deploy into.

### C. Instrumentation & observability

- **Goal:** Turn every request into a readable trace tree.
- **Activities:**
  - Add OpenTelemetry tracing to both pipelines with spans at the agent, model,
    and tool level.
  - Stand up Azure Application Insights + Log Analytics as the system of record
    (data stays in Afni's tenant) and self-hosted Langfuse as the LLM-specific
    lens (cost per model, prompt versions, per-trace scores).
  - Define what is captured per request, per model call, per tool call, and per
    session.
- **Produces:** Full trace coverage and the capture specification (see doc on
  observability).

### D. Evaluation framework (priority)

- **Goal:** Measure quality automatically and stop bad changes from shipping.
- **Activities:**
  - Build golden datasets per use case **and per program** (Telesales and WCC
    measure differently; keep them separate).
  - Implement evaluators: Ragas for retrieval / RAG (Retrieval-Augmented
    Generation) quality, DeepEval for writing quality and general checks, and
    **custom Python for tool-selection accuracy** (off-the-shelf tools do not
    cover it).
  - Wire the evaluation gate into continuous integration (CI).
  - Set up online sampling of live traffic and a human-review loop.
- **Produces:** A working evaluation suite, a CI gate, and quality trend
  tracking.

### E. Prompt & model management

- **Goal:** No untracked prompts, no hard-coded model names.
- **Activities:**
  - Move prompts into Git as the source of truth, mirrored to a runtime registry
    with labels (prod / staging).
  - Define model task-aliases in config (`models.yaml`) so a step asks for, say,
    `apix-scoring-model`, not a literal model name.
  - Require a pull request (PR) plus a passing evaluation gate for any prompt or
    model change.
- **Produces:** Versioned prompts, swappable models, and a change process.

### F. CI/CD & release

- **Goal:** Safe, repeatable deployment.
- **Activities:**
  - GitHub Actions workflows: `pr-checks`, `eval-full`, `deploy`.
  - OIDC (OpenID Connect) federated login to Azure — no stored keys.
  - Gated environments: dev / test / prod.
  - Canary releases with automatic rollback.
- **Produces:** A hands-off, auditable release path.

### G. Data & knowledge pipelines

- **Goal:** Keep the data both use cases depend on fresh and managed.
- **Activities:**
  - Hiring RAG ingestion: job descriptions, rubrics, and policy documents into a
    search index.
  - APIX transcript and call-metadata flow into the analysis pipeline.
  - Scheduled or change-data-capture (CDC) refresh, with index aliases so a
    reindex does not break the running pipeline.
- **Produces:** Managed, refreshable knowledge and data feeds.

### H. Guardrails & governance

- **Goal:** Keep outputs safe, compliant, and fair.
- **Activities:**
  - Azure AI Content Safety on inputs and outputs.
  - PII (personally identifiable information) detection and redaction.
  - Fairness checks — bias in Hiring ranking, consistency across agents and sites
    in APIX.
  - Human-in-the-loop for consequential outputs (a recruiter decides; a coach can
    edit).
- **Produces:** Enforced guardrails and a governance checkpoint.

### I. Feedback & improvement loop

- **Goal:** Turn real usage into better models over time.
- **Activities:**
  - Capture coach and recruiter feedback (thumbs, edits, overrides), linked by
    trace ID.
  - Analytics dashboards on quality and cost.
  - Triage negatives → label → add to the golden set → fix the prompt, retrieval,
    or agent → re-evaluate → ship.
- **Produces:** A closed loop where production issues feed back into the
  evaluation set.

## Sequencing (no dates)

Order by dependency, not by calendar.

- **Foundational, must come first:** A (Discovery), B (Foundation), and
  C (Instrumentation). You cannot evaluate or release well without a repo, a
  landing zone, and traces to read from.
- **Runs early and continuously:** D (Evaluation). This is the client's priority.
  Evaluation is not a phase that ends — golden datasets grow, online sampling runs
  all the time, and the CI gate stays on. It starts as soon as there are traces to
  pull examples from and never stops.
- **Runs alongside D:** E (Prompt & model management) and F (CI/CD), because the
  evaluation gate only has teeth once prompts, models, and deploys go through PRs.
- **Layer in after the core is stable:** G (Data pipelines), H (Guardrails), and
  I (Feedback loop). These harden and extend the platform once the trace-and-eval
  core is proven.

```
        ┌─────────────────────────────┐
        │  A. Discovery / current      │
        │     state assessment         │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  B. Foundation (repo, Azure  │
        │     landing zone)            │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  C. Instrumentation /        │
        │     observability (traces)   │
        └──────────────┬──────────────┘
                       │
     ┌─────────────────┼───────────────────┐
     │                 │                    │
┌────▼─────┐   ┌───────▼────────┐   ┌───────▼────────┐
│ D. Eval  │◄─►│ E. Prompt &    │◄─►│ F. CI/CD &     │
│ (early + │   │    model mgmt  │   │    release     │
│  always) │   └────────────────┘   └────────────────┘
└────┬─────┘
     │  (D feeds and gates E and F)
     ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│ G. Data &   │  │ H. Guardrails│  │ I. Feedback &  │
│  knowledge  │  │ & governance │  │  improvement   │
└─────────────┘  └──────────────┘  └────────────────┘
        (layer in once the core is stable)
```

## What we need from the client to proceed

Still no dates — this is about access and inputs, not scheduling.

- **Access:**
  - Read access to the APIX and Hiring code repositories.
  - Azure subscription access to stand up the landing zone (or a delegated
    environment).
  - Access to current logs and any existing evaluation notebooks.
- **Data:**
  - Sample (anonymized) call transcripts and call metadata for APIX, per program.
  - Sample résumés, job descriptions, rubrics, and policy documents for Hiring.
  - The per-program scoring rubric and weights used by APIX.
- **Subject-matter expert (SME) time:**
  - QA leads and coaches to help author and validate APIX golden datasets and to
    confirm scoring against human review.
  - Recruiters to validate Hiring summaries, ranking, and fairness expectations.
  - The product team to confirm the pipeline maps from Discovery.
