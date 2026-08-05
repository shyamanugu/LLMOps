# Model Management

Let us be honest up front: this is the smallest delta in the whole platform. The teams building APIX and Hiring Intelligence almost certainly already do the sensible thing — a bigger model for the hard agent steps, a cheaper one for the simple ones. We are not going to pretend that is a new idea. What we add is discipline around *where* that choice lives and *how* a change to it gets approved.

## Is this a code change or a pipeline change? It is both — config-as-code

The first question people ask here is whether model management lives at the code level (something a developer edits) or at the pipeline level (something the CI/CD and DevOps machinery handles). The honest answer is that it is deliberately **both**, and the name for that pattern is **config-as-code**. It helps to separate the three things that happen, because they happen in three different places:

1. **Code level — the choice is a file in the repo.** The mapping from a task to a model lives in `models.yaml`, a plain configuration file checked into the repository. Changing which model a task uses means editing that file and opening a pull request, exactly like any other code change. It is reviewed by a person. This is the "code-level" part.
2. **Pipeline level (DevOps) — the change is validated and eval-gated.** That pull request does not merge on a reviewer's say-so alone. The CI/CD pipeline validates the file and runs the **evaluation gate**: the candidate model is scored against the golden dataset before the change is allowed in. This is the "pipeline-level" / DevOps part.
3. **Runtime — the application resolves the alias to a real deployment per environment.** The running application never contains a model name. It asks a resolver for the deployment behind a task alias, for the current environment (`APP_ENV=prod`, `APP_ENV=dev`), and gets back the concrete Azure OpenAI deployment to call. This is the "runtime" part.

State it plainly, because this is the confusion to clear:

- It is **not hard-coded in the agent code.** No pipeline step contains `"gpt-5.2"`.
- It is **not a manual setting clicked in a portal.** Nobody changes production by editing a deployment in the Azure portal.
- It **is** a reviewed, evaluation-gated configuration file that the application reads at run time — code-level to change, pipeline-level to approve, runtime to apply.

Here is the same idea as a flow:

```
repo config              CI eval gate                 runtime resolver (per env)
models.yaml   ──PR──▶    validate + score candidate   ──▶  resolve(alias, APP_ENV)
(edit a line,            against the golden dataset          returns the Azure OpenAI
 code-level)             (DevOps-level; blocks on                deployment name for
                          a regression)                          this environment
```

Read left to right: a developer edits one line of a config file (code level); the pipeline validates it and gates it on evaluation before it can merge and deploy (DevOps level); the application resolves the task alias to the right deployment for whichever environment it is running in (runtime). Three levels, one file.

## Today, our setup, what changes

| | Today (assumption — to confirm) | Our setup | What changes |
|---|---|---|---|
| Where the model name lives | Hard-coded in pipeline code (`"gpt-5.2"` in a call site), possibly in a few places | One line in `models.yaml`, referenced by a task alias | Model name leaves the code entirely |
| Picking bigger vs cheaper | Done, but by hand, per agent, per developer | Same intent, expressed as aliases (`reason`, `bulk`, `voice`, `embed`) shared across all use cases | The choice becomes explicit and consistent |
| Swapping a model | Code edit + redeploy + hope | Config PR that must pass the evaluation gate on the golden dataset | A swap is now proven before it ships, and reverting is one line |
| Per environment | An `if env == "prod"` branch, or the same model everywhere | `models.yaml` resolves the same alias to a different deployment per environment | No environment branching in app code |

The migration step is small: grep the codebase for literal model names, replace each with a `resolve(alias, env)` call, and move the actual names into `models.yaml`. A day of work, not a project.

## The one file where a model is chosen

`models.yaml` is the only place a task is mapped to a model. Nothing else in the codebase names a model. It is a file in the repository — changing it is a pull request, not a portal click.

```yaml
# models.yaml — the ONLY place a task maps to a model. Swap a model = edit here, via PR + eval gate.
environments:
  prod:
    aliases: { reason: gpt-5.2, bulk: gpt-5-mini, voice: gpt-realtime-1.5, embed: text-embedding-3-large }
  dev:
    aliases: { reason: gpt-5-mini, bulk: gpt-5-mini, voice: gpt-realtime-1.5, embed: text-embedding-3-large }
```

Read it plainly. There are four task aliases. `reason` is the heavy reasoning tier for the hard steps. `bulk` is the cheap, fast tier for high-volume simple steps. `voice` is the real-time speech model. `embed` is the embedding model used when we build the retrieval index. In `prod`, `reason` points at `gpt-5.2`; in `dev`, `reason` points at the cheaper `gpt-5-mini` so day-to-day development does not burn the expensive tier. The alias is the contract; the deployment behind it is a detail of the environment — and it is the `environments:` structure that lets one alias resolve differently per environment without a single `if` in the application.

This is exactly the same discipline as prompt management. Application code asks for a named contract (`reason`), never a concrete model version — the same way it asks for a prompt by `id` and `label`, never by pasting the prompt text.

## The resolver — where the runtime part happens

One tiny function turns an alias into the real Azure OpenAI deployment name for the current environment. This is the runtime step in the flow above.

```python
# src/common/model_router.py
def resolve(alias: str, env: str) -> str:      # returns the Azure OpenAI *deployment name*
    return MODELS[env]["aliases"][alias]        # app code says resolve("reason"), never "gpt-5.2"
```

That is the whole mechanism. A pipeline step calls `resolve("reason", env)` — where `env` comes from `APP_ENV` in the running environment — and gets back the deployment it should hit. The application code is identical in dev and prod; only the environment variable differs, and `models.yaml` does the rest. The tracing layer (see the observability note) records that resolved deployment on every model-call span, so a trace always shows which concrete model actually ran, even though the code never named it.

## A model swap is a config change that must pass the gate

This is the rule that makes the small delta worth having — and it is the pipeline-level (DevOps) part of config-as-code. Changing a model is not a quiet edit. It is a pull request against `models.yaml`, and that pull request runs the same evaluation gate as a prompt change:

- The candidate model is run against the golden dataset for every affected use case.
- Its scores are compared side by side with the current model — quality first, then cost per request and p95 latency (the 95th-percentile response time).
- The pull request merges only if the candidate holds or beats quality at equal-or-better cost. If a metric drops past its baseline, the gate fails and the merge is blocked (`eval-full.yml`).

So "should we move `reason` from `gpt-5.2` to the newer model?" is answered by numbers on our own data, not by a release note. And because a swap is one line, rollback is one line — revert the file, no container rebuild.

## One shared config under one hub

There is a single `models.yaml` for the whole platform, and every use case — APIX, Hiring Intelligence, and whatever comes next — reads from it. All the underlying deployments live under **one Azure AI Foundry hub**, so quota, access, and cost roll up in one place. If a use case genuinely needs a different model for one step, it is a per-use-case override in the same file, still under the same hub, still gated the same way. We do not scatter model choices across teams and repositories.

## Which model for which task

The aliases exist because different task types have genuinely different needs. This table is the reasoning behind the four aliases.

| Task type | Alias | Tier | Why this tier |
|---|---|---|---|
| Deep reasoning, multi-step agent work (APIX dimension analysis, coaching write-up) | `reason` | Frontier reasoning (e.g. `gpt-5.2`) | Ambiguous, high-stakes judgement; volume is low relative to bulk work, so the cost is justified |
| High-volume simple steps (classification, formatting, intent routing, extraction) | `bulk` | Small/instant (e.g. `gpt-5-mini`) | Cost dominates at this volume and the task is easy enough that a small model clears the quality bar |
| Real-time voice turns | `voice` | Realtime audio (e.g. `gpt-realtime-1.5`) | Only tier built for live speech-to-speech turn-taking; text models miss the latency budget |
| Building the retrieval index | `embed` | Embedding model (e.g. `text-embedding-3-large`) | A different model family — purpose-built for vectors, not chat |

The point of the table is the habit it enforces: match the task's real difficulty to a tier, and let the golden-dataset scorecard prove a cheaper tier is good enough, rather than defaulting to the biggest model because it feels safe.

## Model Router — an option, not the default

Azure's Model Router can sit above the aliases: instead of one alias always resolving to one deployment, it inspects each request and picks the cheapest deployment that still clears the quality bar — small model for the easy turns, big model for the hard ones, automatically. It is worth turning on later for a task with wide per-request difficulty and high volume, once that task has a golden-dataset score for the router to be measured against.

We keep **aliases as the primary mechanism**. They are simpler, cheaper to reason about, and far easier to debug when something goes wrong — you always know exactly which model ran. The router is an optimisation to add on top of a stable alias, not a replacement for it.
