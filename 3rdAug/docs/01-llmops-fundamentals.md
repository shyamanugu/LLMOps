# LLMOps Fundamentals

> LLMOps = Large Language Model Operations. This note explains what that term means once you strip
> away the marketing, what the actual moving parts are, which of those parts you build once versus
> rebuild per project, and how to tell if a given setup deserves to be called LLMOps at all.

## What LLMOps actually is

LLMOps is the discipline of running large language model (LLM) applications in production the same
way a good engineering team runs any other production system — with version control, automated
testing, staged rollouts, monitoring, and a feedback loop — but adapted for the fact that the core
component (the model) is probabilistic, not deterministic. A generative AI (GenAI) system can give a
different answer to the same input twice. That single fact breaks a lot of assumptions that DevOps
(development operations) and MLOps (machine learning operations) practices are built on, and it is why
LLMOps needs its own playbook rather than just borrowing one wholesale.

The short version: DevOps ships code, MLOps ships trained models, LLMOps ships prompts + agents +
model configuration + guardrails, and grades all of it with evaluation runs because you cannot unit-test
"is this answer good" the way you unit-test "does this function return 4."

### DevOps vs MLOps vs LLMOps — comparison table

| Dimension | DevOps | MLOps | LLMOps |
|---|---|---|---|
| Main thing being shipped | Application code | Code + a trained model + training data | Code + prompts + agent definitions + model config (aliases/deployments) + guardrail rules |
| Is the output repeatable? | Yes, deterministic | Statistically repeatable given the same data/seed | No — same input can produce a different (still valid) output |
| How you test before release | Unit tests, integration tests | Model metrics (accuracy, AUC, F1) on a held-out set | Evaluation runs against a golden dataset, scored by rules and by another LLM acting as judge |
| What "broke production" looks like | Crash, 500 error, failed deploy | Model accuracy drifted, features stopped matching training data | Hallucination, prompt injection, PII (personally identifiable information) leak, cost spike, tone drift |
| What you monitor after release | Uptime, error rate, latency | Data drift, prediction drift | All of the above, plus token cost per request, groundedness, and safety-filter hit rate |
| Who reviews changes before merge | Engineers | Engineers + data scientists | Engineers + prompt authors + a subject matter expert (SME) for the golden dataset, sometimes security |
| Rollback unit | A code deploy | A model version | A prompt version, a model alias, or an agent workflow version — each independently reversible |

The practical takeaway: LLMOps is not a replacement for DevOps or MLOps, it sits on top of both. You
still need CI/CD (continuous integration / continuous delivery) pipelines, still need infrastructure as
code, still need model training know-how if you ever fine-tune. LLMOps adds the layer that deals with
prompts, evaluation of open-ended text, and the new failure modes that come from letting a model call
tools and make decisions on its own.

## The component map

An LLMOps setup is not one tool. It is thirteen distinct pieces of plumbing that all have to work
together. Below is the full map — this is the checklist to use when someone says "we have LLMOps" and
you want to know what they actually mean.

| # | Component | One-line job |
|---|---|---|
| 1 | Source control & ops backbone | Git repo, branching, pull requests (PRs), CI/CD pipelines, environments, federated login to cloud |
| 2 | Prompt management | Where prompt text lives, how it is versioned, how it gets to production, A/B testing |
| 3 | Model management | Which model serves which task, how you swap models, cost/quality routing |
| 4 | Evaluation | Golden datasets, scoring metrics, automated gates before merge/deploy |
| 5 | Observability | Tracing every model call, tool call, and agent hop; token cost, latency, quality over time |
| 6 | Feedback & analytics | Capturing thumbs up/down and edits, dashboards, closing the loop back into evaluation |
| 7 | Data pipelines & knowledge | Ingesting source documents, chunking, embedding, indexing for retrieval-augmented generation (RAG) |
| 8 | Guardrails & safety | Input/output filtering, PII detection, policy enforcement, jailbreak resistance |
| 9 | Serving & gateway | API management, rate limits/quotas, response caching, canary releases |
| 10 | Multi-agent orchestration | Frameworks and patterns for agents that plan, call tools, and hand off to each other |
| 11 | Security & identity | Authentication, authorization, secrets management, audit trail |
| 12 | FinOps (financial operations for cloud spend) | Cost metering per use case, budgets, alerts, showback/chargeback |
| 13 | Environments & infrastructure as code (IaC) | Dev/test/prod separation, reproducible infrastructure via Bicep or Terraform |

None of these are optional at scale. A team can start with a thin version of all thirteen (Level 0
below) rather than a deep version of two or three — that is the "start small, go big" approach this
whole package follows.

## Reusability — what you build once vs. what repeats per use case

This is the question that decides whether your third GenAI use case takes six weeks or six months.
Most of the thirteen components are **platform work**: build them once, and every new use case just
plugs in. A smaller number require real per-use-case effort every time.

| Component | Built once (platform)? | Per-use-case work remaining |
|---|---|---|
| Source control & ops backbone | Yes — repo structure, workflows, environments | New folder under `/prompts`, `/agents`, `/evals` for the use case |
| Prompt management | Yes — registry, labeling, sync pipeline | Author the actual prompt text and its variables |
| Model management | Yes — catalog access, alias pattern, router policy | Pick which task aliases the use case needs (e.g., `reason`, `summarize`) |
| Evaluation | Yes — harness, CI gate wiring, evaluator library | Build the golden dataset (this is the expensive, SME-driven part) |
| Observability | Yes — tracing SDK wired into the app template | Add use-case-specific tags/dimensions to dashboards |
| Feedback & analytics | Yes — capture API, dashboard shell | Define what "good" feedback looks like for this use case |
| Data pipelines & knowledge | Partially — ingestion framework yes, source connectors mostly yes | New source connection + chunking tuning per knowledge domain |
| Guardrails & safety | Yes — Content Safety policy templates | Tune thresholds and add domain-specific denylist/allowlist terms |
| Serving & gateway | Yes — API Management (APIM) config, quota tiers | Register new route, set the use case's rate limit |
| Multi-agent orchestration | Yes — framework, agent registry, workflow patterns | Design the actual agent graph for this use case's workflow |
| Security & identity | Yes — Entra ID (identity platform) roles, Key Vault (secrets store) pattern | Assign roles/scopes for the new use case's service identity |
| FinOps | Yes — cost tagging convention, budget alert template | Set the use case's specific budget number |
| Environments & IaC | Yes — Bicep/Terraform modules | Parameter file for the new use case's resource sizing |

Rule of thumb: if a component needs a subject matter expert (SME) sitting down and writing test cases
or domain content, it repeats every time no matter how good your platform is. Golden datasets and RAG
source tuning are the two components that never get fully automated away — budget SME time for them
on every new use case.

## Maturity levels

Everything in this package is framed as levels, because trying to build all thirteen components fully
on day one is how projects stall for months before anything ships.

| Level | Name | Timeframe | What gets added |
|---|---|---|---|
| **Level 0** | Baseline | Weeks 1–2 | Git repo + folder structure, cloud landing zone (resource group, identity, secrets store, API gateway, model endpoint), basic tracing, prompts committed to Git, a manual notebook for evaluation, one use case running in a dev environment |
| **Level 1** | Managed | Weeks 3–6 | CI evaluation on every PR against a first golden dataset, prompt registry with prod/staging labels, a RAG ingestion pipeline, safety guardrails turned on, first dashboards, dev/test/prod environments with gated deploys — this is when the first use case goes to production |
| **Level 2** | Production-grade | Months 2–4 | Full golden datasets with nightly evaluation runs, canary releases with automatic rollback, feedback capture feeding analytics, cost metering per use case, dedicated LLM observability tool, a red-team test suite, multi-agent orchestration with an agent registry |
| **Level 3** | Scaled / self-service | Months 4+ | New use cases can be onboarded by a team without platform-team help, automatic model routing plus a fine-tuning loop, agent-to-agent (A2A) collaboration across teams, drift detection, disaster recovery, FinOps budgets and alerts, training data curated straight from the data warehouse |

The point of the levels is not "reach Level 3 as fast as possible." It is: know exactly which level you
are on, and do not claim capabilities from a level you have not built yet (for example, claiming
"canary + auto-rollback" while still deploying straight to production with no staging traffic split).

## Checklist — what makes a setup genuinely LLMOps

Pulled directly from the practical anchors this package works from. If any of these is "no," the setup
is not there yet, regardless of how many dashboards exist.

- [ ] Prompts, agent definitions, and golden datasets are committed to Git — not living in a portal,
      a notebook, or someone's local file.
- [ ] Every change to a prompt or agent runs an automated evaluation before it can merge.
- [ ] Deploys go through gated environments (dev → test → prod) with required reviewers, not a
      direct push to production.
- [ ] Every deploy is reversible — there is a rollback path that does not require a new code change.
- [ ] Production traffic traces flow back into the golden dataset over time, so the test suite gets
      better because the system is being used, not just because someone remembered to add cases.
- [ ] Cloud authentication uses federated identity (OpenID Connect/OIDC), not a long-lived key sitting
      in a repo secret.
- [ ] Cost per request is visible per use case, not just as one combined cloud bill line item.

If all seven are true, the setup earns the name LLMOps. If only the first one is true, what exists is
"prompts in Git" — a good start, but not yet an operating discipline.
