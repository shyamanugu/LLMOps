# Current State vs Target State (As-Is / To-Be)

## How to read this document

We have **not audited the APIX or Hiring pipelines yet**. So the "as-is" column
here is a **discovery checklist**, not a statement of fact. Every current-state
line is marked **assumption — to confirm in discovery**. These are the typical
patterns we see in teams that built working LLM (Large Language Model) features
before adding an operations layer. Discovery (workstream A) replaces each
assumption with what is actually there.

One thing is not an assumption: **APIX and Hiring already run.** They were built
by the product team and produce real output today. This work **wraps and
standardizes** them with an operational layer. **We are not rebuilding the use
cases.** Where a "target" differs from the "as-is", the change is additive —
tracing, versioning, evaluation, gating — around pipelines that keep doing what
they already do.

## The table

| Area | As-is (assumption — to confirm) | Target | Gap / change needed |
|---|---|---|---|
| **Source control** | Code lives in repos; prompts possibly inline in code or notebooks | Monorepo; prompts, agents, and evaluation sets all versioned and PR-reviewed | Pull prompts and eval cases out of code into tracked files |
| **Prompts** | Edited directly in code or a portal, not tracked | Git is the source of truth + a runtime registry with labels (prod/staging) and A/B support | Add prompt registry; enforce PR review for prompt changes |
| **Models** | Model names written directly in code | Task-aliases in config (`models.yaml`); swapping a model is a PR through the eval gate | Introduce alias layer; remove hard-coded model names |
| **Tracing** | Application logs only; no per-model or per-tool spans | Full OpenTelemetry trace tree; Azure Application Insights + self-hosted Langfuse | Instrument both pipelines with agent/model/tool spans |
| **Evaluation** | Manual or spot-check; no automated gate | Golden datasets + automated evaluators + CI gate + online sampling | Build datasets and evaluators; wire the CI gate |
| **Data / RAG** | Ad-hoc ingestion | Managed ingestion + scheduled or CDC refresh + index aliases | Formalize ingestion and refresh; add index aliasing |
| **Guardrails** | Minimal | Content Safety + PII detection/redaction + fairness checks + human-in-the-loop | Add safety, PII, and fairness layers; define review points |
| **Deploy** | Manual | GitHub Actions + OIDC + gated environments + canary + rollback | Automate release; remove stored keys via OIDC |
| **Hosting** | To confirm | Azure Container Apps (+ Functions for triggers); APIM in front | Confirm current hosting, then move to the target shape |

Abbreviations: RAG = Retrieval-Augmented Generation; CDC = change-data-capture;
PII = personally identifiable information; OIDC = OpenID Connect; CI = continuous
integration; APIM = Azure API Management.

## The high-impact areas, one at a time

### Prompts and models

This is usually where the biggest, cheapest wins are. If prompts are edited in a
portal or sit inline in code, nobody can answer "what prompt produced this output
last Tuesday?" — and a small wording change can shift quality with no record. The
target is simple: Git holds the canonical prompt, a runtime registry serves it
with a label, and every change goes through a PR that the evaluation gate checks.
The same logic applies to models. When a model name is hard-coded, swapping it (a
new version, a cheaper deployment) is risky and invisible. A task-alias in
`models.yaml` means a step asks for `hiring-screening-model` and the config maps
that to a real deployment — so a swap is one reviewed change, not a hunt through
the code. **To confirm in discovery:** where prompts actually live today and
whether any model names are already centralized.

### Tracing

Standard application logs tell you a request happened; they do not tell you which
agent called which model with which prompt version, which tool it picked, what
that tool returned, or where the tokens and cost went. For a multi-step pipeline
that gap is expensive — when output is wrong, you cannot see which step failed.
The target turns each request into a trace tree with spans at the agent, model,
and tool level, sent to Application Insights (the tenant system of record) and
Langfuse (the LLM-specific view). This is also the foundation for evaluation:
online evaluators and mined golden-dataset examples both read from traces. **To
confirm in discovery:** what is logged today and whether any correlation ID
already links the steps of one request.

### Evaluation

The client's priority. The likely current state is manual spot-checking — someone
reads a sample of outputs and forms a judgment. That does not scale to "thousands
of calls a day" (APIX) or high-volume recruitment (Hiring), and it cannot block a
bad change before release. The target is golden datasets (curated, versioned test
cases) per use case **and per program**, automated evaluators covering retrieval,
writing quality, task execution, safety/fairness, and operational cost, plus a CI
gate that fails promotion when a metric drops past its baseline, and online
sampling that watches for drift in production. **To confirm in discovery:**
whether any test sets or reference outputs already exist that we can seed from.

### Data / RAG

Hiring depends on retrieval over job descriptions, rubrics, and policy; APIX
depends on a steady flow of transcripts and metadata. If ingestion is ad-hoc, the
knowledge behind answers can go stale silently, and a reindex can disrupt the live
pipeline. The target is managed ingestion, a scheduled or CDC refresh, and index
aliases so a rebuilt index swaps in atomically. **To confirm in discovery:** how
documents and transcripts are loaded today and how often they change.

### Guardrails and deploy

These often start minimal because the priority was getting the feature working.
Both are consequential here: Hiring affects real candidates (fairness and PII
matter), and APIX affects agent coaching and reviews (consistency and evidence
matter). The target adds Content Safety, PII redaction, fairness checks, and
human-in-the-loop review at the points where a person should stay in control —
plus automated, gated, reversible deployment through GitHub Actions with OIDC so
there are no long-lived keys and any release can roll back. **To confirm in
discovery:** current safety measures, where humans already review, and how deploys
happen now.

### Hosting

Left open on purpose until discovery. The proposed target is Azure Container Apps
for the pipeline services (each step as a scalable container), Azure Functions for
event triggers (new transcript, new candidate), and APIM in front as the gateway.
We confirm what the pipelines run on today before proposing any move — the aim is
to fit the operational layer around the existing systems, not to force a
migration.
