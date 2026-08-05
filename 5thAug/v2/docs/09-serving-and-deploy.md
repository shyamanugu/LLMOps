# Serving, Gateway & Deployment

This document shows where the pipeline actually runs, **why each hosting piece exists**, and how a change reaches production. The short version: each pipeline step runs as its own container on Azure Container Apps, event triggers are Azure Functions, agents (when we adopt managed hosting) run on Azure AI Foundry Agent Service, everything is reached through one Azure API Management (APIM) gateway, and deployment goes through the gated GitHub Actions workflow with a canary and automatic rollback. The hosting choices are not a grab-bag — each one is there for a specific reason, spelled out below.

## Today

**Today (assumption — to confirm):** the pipeline runs as one process (a script or a single web app), so a change to one step means redeploying the whole thing, and one slow step holds up the rest. New transcripts or candidates are probably picked up by a polling job or a manual trigger. There is no single front door — callers hit the service directly, so there is no place to enforce quotas, meter tokens, or cache. Deployment is a straight push: the new version replaces the old one for everyone at once, and rolling back means redeploying the previous build by hand.

## Our setup

Three hosting building blocks, each chosen for a reason. Here is what each is and, more importantly, **why it is there**.

### Container Apps — why: host the pipeline services, autoscale, scale to zero

**Each pipeline step is its own container/service on Azure Container Apps.** The APIX pipeline — ingest-facing retrieval, dimension scoring, coaching-report generation — is not one binary. Each step is a container app that does one job, reads its prompt and model alias from the registry and `models.yaml`, and emits its own traces.

Why Container Apps specifically:

- **It hosts long-running HTTP/orchestration services** — the always-on part of the platform that answers requests and runs the pipeline sequence. That is what containers are good at, and Container Apps runs them without us operating a Kubernetes cluster.
- **It autoscales per step.** Each step scales on its own demand, so the scoring step can be busy while the report step is idle, and they do not fight for one process's capacity.
- **It scales to zero.** An idle step costs nothing — we pay for the coaching-report generator only while reports are being written. For bursty, per-program workloads this matters.
- **It gives revisions and traffic splitting for free**, which is exactly what the canary and rollback below are built on.

An orchestrator container runs the sequence (`src/pipelines/apix/run.py`) and calls each step. Because the steps are separate services, we can redeploy the report generator without touching scoring, and we can canary one step at a time.

### Azure Functions — why: event-driven triggers, serverless, cheap for bursty work

**Azure Functions handle event triggers.** The pipeline is kicked off by events, not polling. The reason to use Functions here rather than a container:

- **The work is event-driven, not always-on.** APIX should run **when a new transcript lands in Blob Storage**, or **on a nightly schedule** for batch programs — not on a server that sits polling around the clock. A Blob trigger fires the moment the file arrives; a timer trigger fires on schedule. No polling loop, no always-on process to pay for.
- **It is serverless and cheap for bursty or scheduled work.** Transcripts arrive in clumps, not a steady stream. Functions bill per execution, so a quiet night costs effectively nothing and a busy hour scales out automatically. Putting this on an always-on container would mean paying for idle time and writing our own polling.
- **It keeps the trigger logic thin and separate.** The Function only validates, enqueues, and calls the orchestrator — nothing more. The heavy model-calling work stays in the Container Apps steps, so the always-on surface stays small and the trigger concern stays isolated.

### Azure AI Foundry Agent Service — why: managed agent hosting with state and memory

**Foundry Agent Service is managed hosting for agents, so we do not run our own agent server.** As the agent patterns settle, running an agent means running something that holds conversation **state and memory**, wires up tools, and manages the agent loop. Foundry Agent Service does that as a managed service:

- **It holds state and memory for us** — the per-session context an agent needs across turns — instead of us building and operating that store.
- **It manages the agent runtime and tool wiring**, so we are not standing up and patching our own long-lived agent server.
- **We adopt it as it matures.** For the current sequential pipelines we do not need it yet; it is the managed home for agents once the patterns are stable. This is a deliberate "later," not today's default.

### Azure API Management — why: one governed front door

**Nothing calls a container app directly.** APIM is the single entry point for every use case, and it is where the cross-cutting controls live:

- **Quotas and rate limits** per caller/subscription, so one team or a runaway loop cannot exhaust capacity.
- **Token metering** — APIM records token usage per call (from the response usage or the trace) and attributes cost to a caller, which feeds the cost view alongside the App Insights `app.cost_usd` attribute from `tracing.py`.
- **Caching** of identical or near-identical requests at the gateway, so repeated asks do not re-hit the model.
- **One authenticated, logged edge** — callers get a stable URL and key; the containers behind it stay private on the network.

```
                       ┌───────────────────────────────────────────┐
   new transcript ─▶ Azure Function (Blob trigger) ─┐               │
   nightly batch  ─▶ Azure Function (timer trigger) ─┤              │
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

## Environments and the promotion gate

**Environments on a landing zone.** We run three environments — **dev**, **test**, **prod** — each in its own resource group on an Azure landing zone, each with its own APIM instance, Container Apps environment, and `models.yaml` block (dev points `reason` at a cheaper model; prod points it at the full one). Configuration differs by environment through config, never through code branches.

**Promotion gate (definition).** A promotion gate is the condition that must be met to move a change from one environment to the next — **dev → test → prod**. Our gate has two parts, and both must pass:

1. **A human approver** signs off (a required reviewer on the GitHub Environment for `test` and for `prod`).
2. **`eval-full` passes** — the full golden-dataset evaluation run clears its thresholds.

If either is missing, the change does not advance. A change cannot reach prod on approval alone, and it cannot reach prod on a green eval alone; it needs both. This is what stops a well-meaning approval from shipping a quality regression, and stops a passing eval from shipping without a human in the loop.

## Canary and automatic rollback

**Canary (definition).** A canary release is when we send the new version a **small slice of live traffic first — about 10%** — watch how it behaves on real requests, and only then decide. If it stays healthy we **ramp it to 100%**; if it misbehaves we **auto-rollback** to the previous version. The name is the coal-mine canary: a small, early warning before everyone is exposed. It is the opposite of the replace-everything-at-once deploy.

Container Apps gives us revisions and traffic splitting, and `deploy.yml` uses them directly. A new prod revision takes **10% of traffic** first; a watcher observes the Service Level Objectives (SLOs) for a set window; traffic goes to 100% only if it stays healthy, otherwise it reverts.

**Concrete deploy steps (prod):**

1. **Deploy the new revision** alongside the current one (no traffic yet).
2. **Shift 10% of traffic** to the new revision — the canary slice.
3. **Watch the SLOs for 15 minutes** — latency, error rate, and groundedness (an online eval sample, not just infrastructure health).
4. **Promote or revert.** If every SLO holds, shift to 100%. If any SLO breaches, shift traffic back to 0% on the new revision (rollback) and page.

```yaml
# .github/workflows/deploy.yml  (prod job — the promotion gate + canary + rollback)
prod:
  environment: prod                                  # PROMOTION GATE: reviewer + eval-full pass
  needs: test
  steps:
    - run: az containerapp revision copy ...          # 1. deploy new revision (no traffic)
    - run: az containerapp ingress traffic set ... --revision-weight new=10  # 2. shift 10% (canary)
    - run: python ops/watch.py --for 15m --slo latency,errors,groundedness   # 3. watch SLOs 15m
    - run: az containerapp ingress traffic set ...    # 4. promote to 100% if healthy, else revert
```

The watcher checks latency, error rate, and **groundedness**, so a revision that is technically up but producing worse answers is caught and rolled back automatically — not only one that throws errors.

## Hosting piece → why it exists

| Hosting piece | What it hosts | Why it exists |
|---|---|---|
| **Azure Container Apps** | The pipeline services (orchestrator + each step) | Long-running HTTP/orchestration work; autoscales per step; scales to zero when idle; revisions + traffic split give canary/rollback for free — without operating Kubernetes |
| **Azure Functions** | Event triggers (new transcript in Blob; nightly batch) | Work is event-driven, not always-on; serverless and cheap for bursty/scheduled bursts; keeps trigger logic thin and separate from model-calling steps |
| **Azure AI Foundry Agent Service** | Managed agent hosting (later) | Holds agent state/memory and wires tools so we do not run our own agent server; adopt as the patterns mature |
| **Azure API Management** | The single front door | One governed edge: quotas, rate limits, token metering, response caching, auth and logging; keeps containers private |
| Azure Kubernetes Service | — | Only if we later need cluster-level control we do not need now; more to operate. Not chosen. |

## What changes

**What changes:** the single-process pipeline becomes independently deployable, independently scaling steps on Container Apps, so a change ships one step at a time and idle steps cost nothing. Polling/manual kick-off becomes event-driven Azure Functions that fire when a transcript lands or on a nightly schedule. Agent hosting, when we need it, becomes managed Foundry Agent Service rather than a server we operate. Direct calls to the service become one governed APIM front door with quotas, token metering, and caching. And the replace-everything-at-once deploy becomes a **10% canary** watched against SLOs for 15 minutes with automatic rollback, sitting behind a **promotion gate** (approver + `eval-full`) for test and prod. **Migration step:** containerise the existing APIX steps as-is (they already run today — we are repackaging, not rewriting), put APIM in front, move the trigger into a Blob-triggered Function, and switch `deploy.yml` on for the dev environment first. Nothing about the pipeline's logic changes; where and how it runs does.
