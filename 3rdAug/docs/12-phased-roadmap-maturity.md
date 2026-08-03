# Start Small, Grow: the Phased Plan

The single biggest way LLMOps projects fail is trying to build all thirteen components (see the
component map in the fundamentals doc) at full depth before shipping anything. This plan does the
opposite: ship one real use case on a thin version of every component first, then add depth level by
level. Each level is additive — nothing built earlier gets torn out later.

## Level 0 — Baseline

**Duration:** weeks 1–2.

**What gets set up:**
- Azure landing zone: one resource group, Entra ID app registrations, a Key Vault instance, an API
  Management (APIM) instance, one Azure OpenAI deployment.
- GitHub repository with the folder structure in place (`/prompts`, `/agents`, `/evals`, `/src`,
  `/pipelines`, `/infra`, `/dashboards`), even if most folders only hold one file.
- Prompts for the one chosen use case committed as YAML files in `/prompts`, not hard-coded in the app.
- Basic tracing: Application Insights capturing each model call (prompt, completion, tokens, latency)
  via the OpenTelemetry SDK.
- A manual evaluation notebook an engineer runs by hand against a first pass at 20–30 test cases.
- One use case reachable end to end, in a development environment only.

**Capability this unlocks:** the team can point at a real, working system and say what it does, what it
costs per call, and how it performs against a first, small set of test cases — the baseline everything
else measures against.

**Exit criteria:** the use case runs in dev without manual babysitting; every model call shows up as a
trace; the notebook produces a repeatable score on the first test cases; prompts live in Git.

**Deliberately deferred:** automated evaluation in continuous integration (CI), a prompt registry,
retrieval-augmented generation (RAG), safety guardrails, staged environments, gated deploys. None are
needed to prove the use case works; they are needed to run it safely at volume, which is Level 1's job.

## Level 1 — Managed

**Duration:** weeks 3–6 (first production use case around week 6).

**What gets set up:**
- `pr-checks.yml` GitHub Actions workflow: every pull request touching a prompt or agent runs against a
  first golden dataset (golden-v1, 50–200 cases).
- A prompt registry with `prod` and `staging` labels (Langfuse or Foundry prompt assets), synced from Git
  in CI, so the app requests "prompt X, label prod" rather than a hard-coded version.
- An Azure AI Search RAG pipeline (ingestion, chunking, embedding, an index the retrieval agent queries),
  if the use case needs retrieval.
- Content Safety guardrails turned on for both input and output.
- First dashboards: volume, latency, basic quality trend, even if manually assembled.
- Dev, test, and production as separate GitHub Environments, each deploy gated by a required reviewer.

**Capability this unlocks:** the first use case can go to production. There is now a gate that stops a bad
prompt change before it ships, a way to roll a prompt back to a known-good label without a code deploy,
and a guardrail layer that catches the most common failure modes before they reach a customer.

**Exit criteria:** a pull request has been blocked by a failing evaluation and the prompt was actually
fixed, not overridden; the use case serves real traffic in production behind APIM; a rollback has been
exercised at least once, even as a drill.

**Deliberately deferred:** nightly full-suite evaluation, canary releases with automatic rollback, cost
metering per use case, a dedicated LLM observability tool, a red-team suite, and multi-agent
orchestration. The use case stays a single agent or a simple prompt-and-retrieve pipeline on purpose;
Level 2 is where it is allowed to get more complex.

## Level 2 — Production-grade

**Duration:** months 2–4.

**What gets set up:**
- `eval-full.yml` running the complete golden set nightly and on every merge, posting a scorecard.
- Canary deploys: a small percentage of production traffic hits the new version first; auto-rollback on
  health or evaluation-score alarms.
- Feedback capture (thumbs up/down, edits, escalations) writing to Application Insights and feeding
  analytics on Microsoft Fabric.
- Cost metering per use case, not one lump cloud bill line.
- Langfuse (or an equivalent dedicated LLM observability tool) self-hosted, for a session- and
  prompt-version-level view.
- A red-team test suite (adversarial prompts, injection attempts, PII-leak probes) run on a schedule.
- Multi-agent orchestration using Microsoft Agent Framework, with an agent registry so each agent is a
  versioned, independently deployable unit.

**Capability this unlocks:** more than one use case can run at once without the platform team hand-
holding each release; a bad deploy self-heals before most users notice; the feedback-to-golden-set loop
runs on its own schedule instead of relying on someone remembering to check a dashboard; agents can be
composed into multi-step workflows instead of staying single-purpose.

**Exit criteria:** a canary has caught and auto-rolled-back at least one real regression; the cost-per-
use-case report is something a manager can read and act on; the red-team suite has a real run history,
not just one at launch; at least one production workflow uses more than one agent handing off to another.

**Deliberately deferred:** self-service onboarding, automatic model routing, a fine-tuning loop,
agent-to-agent (A2A) collaboration, drift detection, disaster recovery. These need the platform muscle
built in Levels 0–2 already solid; building them earlier means rebuilding them once usage is known.

## Level 3 — Scaled / self-service

**Duration:** months 4 and onward, ongoing.

**What gets set up:**
- A self-service path: a new use-case team gets a starter template and goes through the same CI/CD
  pipeline without the platform team doing setup for them.
- Model Router wired in for automatic routing by task complexity and cost, plus a fine-tuning loop (Azure
  OpenAI fine-tuning) for use cases where prompt and RAG gains have plateaued.
- Agent-to-agent (A2A) collaboration patterns across previously siloed use cases.
- Drift detection on retrieval quality and model output quality over time.
- Disaster recovery: documented, tested failover for the runtime and the data layer.
- FinOps budgets and automated alerts per use case, not a report read after the fact.
- Training-data curation pulled directly from the Fabric-integrated warehouse, not ad hoc exports.

**Capability this unlocks:** the platform stops being "the thing the GenAI team runs" and becomes
infrastructure other teams build on, the same way they would use a shared database or CI/CD system.

**Exit criteria:** a use case has been onboarded by a team outside the platform team, via the self-service
path, without a platform engineer doing the setup.

**Deliberately deferred:** nothing structural — Level 3 is the ongoing operating state, not a finish line.

## Summary table

| Level | Weeks | Components added | You can now... |
|---|---|---|---|
| **Level 0 — Baseline** | 1–2 | Landing zone, Git repo structure, prompts in Git, basic tracing, manual eval notebook | Point at one working use case in dev and measure it |
| **Level 1 — Managed** | 3–6 | CI evaluation on PRs, prompt registry + labels, RAG pipeline, guardrails, first dashboards, gated dev/test/prod | Put the first use case into production safely |
| **Level 2 — Production-grade** | ~8–16 | Nightly evaluation, canary + auto-rollback, feedback + Fabric analytics, cost metering, dedicated LLM observability, red-team suite, multi-agent orchestration | Run several use cases and multi-step workflows without hand-holding |
| **Level 3 — Scaled** | 16+, ongoing | Self-service onboarding, model router + fine-tuning, agent-to-agent collaboration, drift detection, disaster recovery, FinOps alerts | Let other teams onboard their own use cases on the platform |

The point of naming the levels is discipline, not speed. A team on Level 1 that claims Level 2
capabilities while still deploying straight to production is setting itself up for an outage it did not
plan for. Know the level you are actually on.
