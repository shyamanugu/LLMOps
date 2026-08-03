# Team, Timeline, Assumptions & Risks

This document is proposal-style and illustrative: numbers below are a reasonable starting point for a
contact-center business process outsourcing (BPO) enterprise standing up this framework, not a fixed
quote. Adjust headcount and duration to the actual use case backlog and the client's existing platform
maturity before treating any number here as a commitment.

## Core team

| Role | Count | Responsibility | When needed |
|---|---|---|---|
| GenAI architect / lead | 1 | Owns the overall design, the maturity-level roadmap, and technical decisions that cut across use cases (model aliasing, agent framework choice, evaluation strategy) | From Level 0, throughout |
| GenAI engineer | 2–3 | Builds prompts, agents, retrieval pipelines, and the CI/CD wiring for evaluation and deploys | From Level 0, throughout |
| Data engineer | 1 | Builds the ingestion pipelines for retrieval-augmented generation (RAG) sources and the telemetry export into the Fabric lakehouse | From Level 1 (RAG pipeline), full-time by Level 2 |
| DevOps | 0.5 | Infrastructure as code (Bicep/Terraform), GitHub Actions pipelines, environment and secret management | From Level 0, part-time until Level 2 scale |
| Security | 0.5 | Content Safety policy review, Entra ID role design, sign-off on data access and PII handling | From Level 0 (landing zone review), heavier at Level 1 (guardrails, first production use case) |
| Product / project manager | 0.5 | Backlog, subject matter expert (SME) coordination for golden datasets, stakeholder reporting | From Level 0, throughout |

At Level 3 this core team grows to roughly 8–10 people, split into a platform team (owns the shared
components: source control backbone, evaluation harness, observability, guardrails, serving/gateway,
security, FinOps, infrastructure as code) and use-case teams (own their own prompts, agents, and golden
datasets, building on top of what the platform team maintains). The split is what makes self-service
onboarding at Level 3 possible — use-case teams stop needing the platform team for every change.

## Timeline

| Level | Duration | Milestone |
|---|---|---|
| Level 0 — Baseline | ≈ 2 weeks | Landing zone live, one use case running in dev |
| Level 1 — Managed | ≈ 4 weeks (weeks 3–6) | **First production use case, around week 6** |
| Level 2 — Production-grade | ≈ 2–3 months | Canary releases, feedback loop, multi-agent orchestration live |
| Level 3 — Scaled | Ongoing from month 4+ | Self-service onboarding, model router, fine-tuning loop |

```
Week:        1    2    3    4    5    6    7    8   ...  ~16          ~20+
             |----|----|----|----|----|----|----|----| .. |------------|---> ongoing
Level 0      [====]
             Baseline: landing zone, repo, one use case in dev
Level 1           [==============]
                  Managed: CI evals, RAG, guardrails, gated deploys
                                     ^
                                first production use case (~week 6)
Level 2                          [====================================]
                                 Production-grade: nightly evals, canary,
                                 feedback loop, cost metering, multi-agent
Level 3                                                              [------->
                                                       Scaled: self-service, router, A2A, DR
```

## Assumptions

- Azure tenant and subscription access already exists, with the ability to create resource groups and
  assign roles (Entra ID access provisioned before Level 0 starts).
- Azure OpenAI quota has been approved for the models the use case needs — this is frequently the
  slowest external approval in the whole plan and should be requested in parallel with, not after,
  kickoff.
- The data sources needed for the use case (SharePoint, CRM/ticketing system, call transcripts, SQL) are
  actually reachable, and someone with authority to grant access is known and available.
- Subject matter experts (SMEs) for the use case's domain are available for roughly four hours a week to
  author and review golden-dataset cases — this is a recurring commitment, not a one-time task.
- A security sign-off process exists and its steps and reviewers are known in advance, rather than being
  discovered mid-project.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Azure OpenAI quota or capacity delay | Medium | High — blocks Level 0 start | Submit the quota request in week 1, in parallel with landing-zone setup, not after; have a fallback region/model in mind |
| Data-access approval takes longer than expected | Medium | High — blocks RAG pipeline and golden-dataset sourcing | Identify data owners and start the access request during Level 0, before Level 1's RAG pipeline work begins |
| Golden-dataset quality is poor (garbage in) | Medium | High — a bad golden set passes changes it should block and blocks changes that were fine | Require SME review before any case enters the set; keep the 60/25/15 happy-path/edge/adversarial split; never let one person author and grade the same change |
| Evaluation overfitting (tuning to the golden set instead of the task) | Medium | Medium | Rotate in new cases from production traffic every sprint or two; hold out 20% of cases from day-to-day tuning; watch for a growing gap between golden-set score and real feedback |
| Multi-agent cost fan-out (one request triggers many model calls across agents) | Medium | Medium–High — cost surprises once multi-agent workflows ship at Level 2 | Cost-per-request tracking from Level 1 onward; a step/turn budget with an alert on runaway loops; review cost trend before promoting a workflow to production |
| Skill ramp (team new to prompt engineering, evaluation design, or agent frameworks) | Medium | Medium — slows early levels | Pair less experienced engineers with the architect on the first use case; keep Level 0's scope to one use case so the learning curve does not compound |
| Scope creep (new use cases pulled in before the platform is ready for them) | Medium | Medium–High — spreads the team thin and stalls the level currently in progress | Hold the line on "one use case through Level 0–1 first"; route new use-case requests into a backlog reviewed at each level transition, not added mid-level |

## What we need to start

- [ ] Azure tenant and subscription access confirmed, with permission to create a resource group.
- [ ] Azure OpenAI quota request submitted (ideally already approved).
- [ ] The first use case named and scoped — one use case, not a portfolio, for Level 0.
- [ ] Data owner identified for whatever source the first use case needs (even if access is still being
      requested).
- [ ] At least one SME committed for roughly four hours a week for golden-dataset work.
- [ ] Security contact identified and the sign-off steps for a new production workload known.
- [ ] GitHub organization/repository access for the team doing the build.
