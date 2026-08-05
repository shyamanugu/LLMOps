# Serving, Gateway & Deployment

This document shows where the pipeline actually runs and how a change reaches production. The short version: each pipeline step runs as its own container on Azure Container Apps, event triggers are Azure Functions, everything is reached through one Azure API Management (APIM) gateway, and deployment goes through the gated GitHub Actions workflow with a canary and automatic rollback.

## Today

**Today (assumption — to confirm):** the pipeline runs as one process (a script or a single web app), so a change to one step means redeploying the whole thing, and one slow step holds up the rest. New transcripts or candidates are probably picked up by a polling job or a manual trigger. There is no single front door — callers hit the service directly, so there is no place to enforce quotas, meter tokens, or cache. Deployment is a straight push: the new version replaces the old one for everyone at once, and rolling back means redeploying the previous build by hand.

## Our setup

**Each pipeline step is its own container/service on Azure Container Apps.** The APIX pipeline — ingest-facing retrieval, dimension scoring, coaching-report generation — is not one binary. Each step is a container app that does one job, reads its prompt and model alias from the registry and `models.yaml`, and emits its own traces. Steps scale independently and **scale to zero** when idle, so we pay for the coaching-report generator only while reports are being written. An orchestrator container runs the sequence (`src/pipelines/apix/run.py`) and calls each step; because the steps are separate services, we can redeploy the report generator without touching scoring, and we can canary one step at a time.

**Azure Functions handle event triggers.** The pipeline is kicked off by events, not polling. A new transcript landing in Blob Storage fires a Blob-triggered Function; a new candidate record fires a Function too. The Function does the thin work — validate, enqueue, call the orchestrator — and nothing more. This keeps the always-on surface small and the trigger logic separate from the pipeline logic.

**Azure API Management is the one entry point.** Nothing calls a container app directly. APIM is the single front door for every use case, and it is where the cross-cutting controls live:

- **Quotas and rate limits** per caller/subscription, so one team or a runaway loop cannot exhaust capacity.
- **Token metering** — APIM records token usage per call (from the response usage or the trace) and attributes cost to a caller, which feeds the cost view alongside the App Insights `app.cost_usd` attribute from `tracing.py`.
- **Caching** of identical or near-identical requests at the gateway, so repeated asks do not re-hit the model.
- **One authenticated, logged edge** — callers get a stable URL and key; the containers behind it stay private on the network.

```
                       ┌───────────────────────────────────────────┐
   new transcript ─▶ Azure Function (Blob trigger) ─┐               │
   new candidate  ─▶ Azure Function (event trigger) ─┤              │
                                                     ▼              │
 caller ─▶  API Management (APIM)                orchestrator       │
            • one entry point                    (Container App)    │
            • quotas + rate limit                     │             │
            • token metering                          ├─▶ step: retrieval   (Container App, scale-to-zero)
            • response caching        ───────────▶    ├─▶ step: scoring     (Container App, scale-to-zero)
            • auth + logging                           └─▶ step: coaching    (Container App, scale-to-zero)
                                                          │      │      │
                                                          ▼      ▼      ▼
                                              Azure OpenAI   AI Search   Content Safety
            envs on a landing zone:  dev  ──▶  test  ──▶  prod   (each its own APIM + Container Apps env)
```

**Environments on a landing zone.** We run three environments — **dev**, **test**, **prod** — each in its own resource group on an Azure landing zone, each with its own APIM instance, Container Apps environment, and `models.yaml` block (dev points `reason` at a cheaper model; prod points it at the full one). Configuration differs by environment through config, never through code branches. Promotion is the GitHub Actions `deploy.yml` walking a change from dev to test to prod, with a required reviewer on test and prod (GitHub Environments protection).

**Canary and automatic rollback.** Container Apps gives us revisions and traffic splitting, and `deploy.yml` uses them directly. A new prod revision takes **10% of traffic** first; a watcher observes the Service Level Objectives (SLOs) for a set window; traffic goes to 100% only if it stays healthy, otherwise it reverts:

```yaml
# .github/workflows/deploy.yml  (prod job — the canary + rollback)
prod:
  environment: prod                                  # requires reviewer + passes eval-full
  needs: test
  steps:
    - run: az containerapp revision copy ...          # new revision at 10% traffic (canary)
    - run: python ops/watch.py --for 15m --slo latency,errors,groundedness
    - run: az containerapp ingress traffic set ...    # 100% if healthy, else revert (rollback)
```

The watcher checks latency, error rate, and **groundedness** (an online eval sample, not just infrastructure health), so a revision that is technically up but producing worse answers is caught and rolled back automatically, not just one that throws errors.

## Option → fit

| Option | Fit |
|---|---|
| **Azure Container Apps** | **Recommended, and what we use.** Each pipeline step a separate service; independent scaling; scale-to-zero for cost; built-in revisions and traffic split give us canary + rollback for free. |
| **Azure Functions** | For **event triggers** — new transcript, new candidate. Thin, event-driven, cheap at idle. We use it for the front of the pipeline, not for the model-calling steps. |
| **Azure AI Foundry Agent Service** | **Later.** A managed home for agents once patterns settle; adopt when we outgrow hand-run orchestration. One-line footnote, not today's choice. |
| Azure Kubernetes Service | Only if we later need cluster-level control we do not need now; more to operate. Not chosen. |

## What changes

**What changes:** the single-process pipeline becomes independently deployable, independently scaling steps on Container Apps, so a change ships one step at a time and idle steps cost nothing. Polling/manual kick-off becomes event-driven Azure Functions. Direct calls to the service become one governed APIM front door with quotas, token metering, and caching. And the replace-everything-at-once deploy becomes a 10%-canary with an SLO watcher and automatic rollback, gated behind test/prod reviewers and the full evaluation run. **Migration step:** containerise the existing APIX steps as-is (they already run today — we are repackaging, not rewriting), put APIM in front, move the trigger into a Blob-triggered Function, and switch `deploy.yml` on for the dev environment first. Nothing about the pipeline's logic changes; where and how it runs does.
