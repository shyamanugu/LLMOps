# Model Management

> Models change fast — a new one lands worth switching to every few months. If model names are
> scattered through application code, every switch is a code change, a redeploy, and a re-test of
> everything. This note describes the alternative: model choice as configuration, gated the same way
> a prompt change is gated.

## How model choice actually works

Two layers, kept deliberately separate:

1. **The catalog + deployments layer (Foundry).** Microsoft Foundry's model catalog is where models
   actually get provisioned. A model like GPT-5.2 is turned into a **named deployment** — for example
   `gpt-5-2-prod-eastus` — with its own quota, its own region, its own capacity type (standard or
   provisioned throughput unit, explained below). A separate deployment typically exists per
   environment (dev/test/prod), so a quota problem or a bad experiment in dev can't touch prod
   traffic. All access to these deployments goes through API Management (APIM), which acts as the
   gateway — the application never calls Foundry directly.

2. **The task-alias layer (`models.yaml` in Git).** The application code never asks for a deployment
   name. It asks for a task alias — `reason`, `summarize`, `voice` — and a small config file resolves
   that alias to the actual deployment for the current environment. This is the layer that makes model
   swaps a config change instead of a code change.

### Example `models.yaml`

```yaml
# models.yaml — one file per platform, environment-scoped sections
# Task alias -> Foundry deployment name. App code only ever references the alias.

dev:
  summarize: gpt-5-mini-dev
  reason: gpt-5-2-dev
  extract: gpt-5-mini-dev
  voice: gpt-realtime-1-5-dev
  embed: text-embedding-3-large-dev

test:
  summarize: gpt-5-mini-test
  reason: gpt-5-2-test
  extract: gpt-5-mini-test
  voice: gpt-realtime-1-5-test
  embed: text-embedding-3-large-test

prod:
  summarize: gpt-5-mini-prod-eastus
  reason: gpt-5-2-prod-eastus
  extract: gpt-5-mini-prod-eastus
  voice: gpt-realtime-1-5-prod-eastus
  embed: text-embedding-3-large-prod-eastus

# Per-use-case override example: billing-assistant needs a bigger context window for reasoning
overrides:
  billing-assistant:
    prod:
      reason: gpt-5-4-prod-eastus   # 272k-token context tier instead of the default reason alias
```

The application's orchestration code contains lines like `model = resolve_alias("reason",
use_case="billing-assistant")` — never a literal model name. This is the same discipline as the prompt
registry: application code should not know or care which concrete model or prompt version is running,
only which named contract it is asking for.

## Why no model names in app code

Three concrete reasons this pays off:

- **Swapping models is a config PR, not a code change.** When a better or cheaper model becomes
  available, the change is one line in `models.yaml`, and it goes through the same PR + evaluation
  gate as a prompt change (`eval-full.yml` runs the golden dataset against the new alias mapping before
  it can merge). No redeploy of application logic is needed.
- **Per-environment safety.** Dev can point `reason` at a cheap or experimental deployment while prod
  stays pinned to a validated one, without an `if environment == "prod"` branch anywhere in application
  code.
- **Rollback is instant.** If a swapped model regresses in production, reverting `models.yaml` to the
  previous deployment name is the entire rollback — no container rebuild.

## Model Router — automatic cost/quality routing

Foundry's Model Router sits as an option above the static alias mapping. Instead of one alias always
resolving to one fixed deployment, the router looks at each request — task type, measured complexity,
a required quality bar, a latency service-level objective (SLO), and a cost ceiling — and picks the
cheapest deployment that clears the quality bar for that specific request. Simple, high-volume,
low-stakes turns (formatting, short classification) get routed to a small/instant model; a turn that
looks ambiguous or high-stakes gets escalated to a larger reasoning model automatically. Prompt caching
on stable context (the system prompt, retrieved policy text, few-shot examples) further cuts the cost
of the escalated calls.

**When to use explicit aliases instead of the router:** if a task's cost/quality tradeoff is well
understood and stable (a voice turn always needs `gpt-realtime-1.5`, an embedding call always needs
`text-embedding-3-large` — there's no "cheaper option that still works" to search for), an explicit
alias is simpler, cheaper to reason about, and easier to debug when something goes wrong.

**When to use the router:** tasks with wide variance in per-request difficulty and volume high enough
that the savings matter — a general Q&A endpoint, a triage/classification front door, a summarization
pipeline processing thousands of documents a day where most are simple and a minority need real
reasoning. Turn the router on only after the quality bar for that task class has a golden-dataset
score attached, otherwise there's nothing for the router's routing decisions to be measured against.

## New-model adoption loop

A new model landing in the catalog does not get adopted by editing `models.yaml` directly. It goes
through a loop:

```
New model appears in Foundry catalog
        │
        ▼
1. CANDIDATE  — provision a dev deployment, nothing points at it yet
        │
        ▼
2. GOLDEN-SET SCORECARD — run the full golden dataset for every task alias
   it might replace; score quality the same way the incumbent was scored
        │  passes quality bar?
        ▼
3. COST / LATENCY COMPARE — same golden set, measure cost per request
   and p95 latency side by side with the incumbent
        │  cheaper or faster at equal-or-better quality?
        ▼
4. SHADOW — mirror a slice of live production traffic to the candidate,
   compare traces, no user ever sees the candidate's output
        │  stable under real traffic?
        ▼
5. PROMOTE — flip the alias in models.yaml through the normal config-PR
   + eval-gate flow; canary the traffic split the same way a prompt
   promotion is canaried
```

This is exactly the same shape as the prompt A/B and canary flow described in the other two notes —
model adoption is not a special process, it reuses the ops backbone already built for prompts and
deploys.

## Quota and capacity — standard vs. provisioned throughput unit (PTU), in plain words

Every Foundry deployment has a capacity type, and picking the wrong one causes two very different
kinds of pain:

- **Standard (pay-as-you-go).** Shared capacity, billed per token used. Good default for anything with
  variable or unpredictable volume — dev, test, most early-stage use cases. Risk: under heavy shared
  demand, requests can get throttled (rate-limited), which shows up as latency spikes or failed calls
  at the worst possible time (a traffic spike is usually also when the business cares most).
- **Provisioned throughput unit (PTU).** Reserved, dedicated capacity billed at a fixed rate regardless
  of how much of it gets used. Removes the throttling risk entirely and gives predictable latency,
  but it costs money whether or not it's being used, and it takes lead time to provision — so it's not
  something to reach for the week before a launch.

**Rule of thumb:** standard for dev/test and for any production use case whose volume is still small or
unpredictable; PTU for a production use case that has proven its volume, sits on a critical customer
path, and needs latency guarantees a shared pool can't promise. Moving from standard to PTU is itself
a `models.yaml` change (a different deployment name), not a rewrite.

## Decision table — which model for which task type

| Task type | What it needs | Right-sized choice | Why |
|---|---|---|---|
| Deep reasoning / multi-step agentic work | Long context, reliable multi-tool planning | Frontier reasoning tier (e.g., GPT-5.5 class) | Ambiguous, high-stakes decisions justify the cost; low volume relative to bulk tasks |
| Grounded Q&A / RAG synthesis | Large context window, faithful summarization of retrieved text | Mid reasoning tier (e.g., GPT-5.2 class, ~272k-token context) | Needs enough context to hold retrieved chunks plus instructions, but doesn't need frontier-level planning |
| Bulk classification / formatting / intent routing | Low latency, huge volume, mostly deterministic-feeling decisions | Instant/small tier or open-weight model (e.g., Phi, Llama) | Cost dominates at this volume; task complexity is low enough that a small model clears the quality bar |
| Real-time voice | Sub-second speech-to-speech, tool calling mid-conversation | Realtime audio model (e.g., gpt-realtime-1.5) | Only tier built for live audio turn-taking; text models can't hit the latency budget |
| Embeddings for retrieval | Consistent vector quality, cheap at ingestion-time volume | A dedicated embedding model (e.g., text-embedding-3-large) | Not a chat model at all — a different model family purpose-built for vector generation |
| High-volume scoring / distillation targets | Domain-specific accuracy at minimal per-unit cost, run at full transaction volume | Fine-tuned or distilled small/open-weight model | A frontier model scoring every single transaction is a cost problem; a distilled model trained on frontier-labeled examples gets most of the accuracy at a fraction of the cost |

The pattern across every row: match the task's actual difficulty and latency need to a tier, don't
default to the biggest available model because it feels safest. The golden-dataset scorecard from the
adoption loop above is what proves a smaller tier is "good enough" for a given task — that proof is
what makes the cost savings defensible rather than a guess.
