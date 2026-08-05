# Prompt Management

Let us be precise about the challenge, because this is the component where the difference from what the team does today is easy to get wrong.

Your prompts are already in Git. The whole project is version-controlled, and the prompt text sits inside that repository along with the code. So **"store prompts in Git" is not the change.** If that were the whole pitch, there would be nothing new here, and you would be right to be unconvinced.

The real change is three specific things: prompts become **one versioned YAML artifact each**, every prompt change passes an **evaluation gate**, and a **runtime registry** holds prompts so we can swap and roll back versions without a redeploy. Below is each one, concretely.

## (a) One YAML file per prompt

Today the prompt text is buried inside a code file — a string constant, an f-string (a Python formatted string), something assembled at runtime. There is no YAML file per prompt today. That means a prompt has no independent version, no place to record why it changed, and no declared link to how it should be tested. You confirmed this is a gap worth closing.

Our setup gives each prompt its own file. Here is the real APIX coaching-report prompt:

```yaml
id: apix.coaching_report
version: 3
labels: [prod]                 # which version production uses; staging can point elsewhere
model_alias: reason            # resolved via models.yaml (not a raw model name)
temperature: 0.2
inputs: [agent_name, program, dimension_scores, evidence]
template: |
  You are a contact-center coach. Using ONLY the evidence quotes below, write a short
  coaching note for {{agent_name}} ({{program}}). Cite the evidence you use.
  Do not invent moments that are not in the evidence.
  Scores: {{dimension_scores}}
  Evidence: {{evidence}}
eval_refs: [evals/apix/golden.telesales.jsonl]
changelog:
  - v3: require evidence citation; forbid invented moments
  - v2: added program to the context
```

Every field earns its place:

- **`id`** — a stable name (`apix.coaching_report`) the application code uses to load the prompt. Code never contains the prompt text; it asks for the prompt by id.
- **`version`** — an integer bumped on every change. This is what lets us compare and roll back precisely.
- **`labels`** — which version an environment points at. `[prod]` here means production uses version 3; staging can point at a different version. Labels are how we hot-swap (see part d).
- **`model_alias`** — `reason`, not `gpt-5.2`. The prompt declares the *kind* of model it needs; `models.yaml` resolves that alias to an actual Azure OpenAI deployment. Change the model without touching the prompt.
- **`temperature`** — the sampling setting (how much the model is allowed to vary its wording), versioned with the prompt because it affects output as much as the wording.
- **`inputs`** — the variables the template expects (`agent_name`, `program`, `dimension_scores`, `evidence`). This is a contract; the loader can validate that all inputs are supplied.
- **`template`** — the prompt text itself, with `{{...}}` placeholders for the inputs. This is the part that used to be buried in code.
- **`eval_refs`** — the golden dataset(s) this prompt is graded against. This is the link that makes the evaluation gate possible: the prompt itself declares how it must be tested.
- **`changelog`** — plain-language notes on what changed and why, version by version. When a coaching note goes wrong in production, this is where you see that v3 added the "cite the evidence" rule.

## (b) The evaluation gate on every prompt change

Today, editing a prompt ships like any other code change. It goes through review, maybe unit tests, and out — with no check that the new wording actually produces better (or even acceptable) output. There is no gate.

Our setup runs every prompt change through the CI/CD pipeline (the automated build-and-test pipeline). When the YAML file changes, the pull-request workflow scores the prompt against the golden datasets named in its `eval_refs`, and the change is blocked from approval and deploy unless it clears the thresholds. This is the same `pr-checks.yml` gate the backbone document describes:

```yaml
- run: python evals/run.py --subset changed --fail-under baseline
  #     runs Ragas + DeepEval + tool_selection on the changed prompt;
  #     exits non-zero (blocks merge) if a metric drops past its baseline
```

So a prompt edit is no longer a matter of "looks good to me." It is measured — against ground truth, on every change, before it can reach production. That is the single biggest practical difference from prompts-in-Git-as-usual.

## (c) The runtime registry — what it is, and the three ways to run it

You asked what a registry actually is. Plainly: a **registry is where prompts are held at runtime so the application can fetch the right version by id and label, and so we can fall back to a previous version if a new one turns out worse.** It is the difference between "the prompt is baked into the deployed build" and "the running application looks up which prompt version is live right now" — the latter is what lets us roll back without a redeploy.

The application never hard-codes prompt text. It calls the loader with an id and a label, and the loader returns the right version from the registry:

```python
from functools import lru_cache
# Prompt source of truth = Git. At runtime we read from the registry (Langfuse), which is
# synced from Git in CI. The app never hard-codes prompt text.
@lru_cache(maxsize=256)
def load_prompt(prompt_id: str, label: str = "prod"):
    p = registry.get(prompt_id, label=label)     # e.g. Langfuse.get_prompt(id, label)
    return Prompt(text=p.template, model_alias=p.config["model_alias"],
                  version=p.version, temperature=p.config.get("temperature", 0.2))
```

There are three sensible ways to run the registry. **Git stays the source of truth in all three** — the YAML files in the repo are always the master copy, reviewed and gated. What differs is *where the runtime copy lives* and *what extra machinery you get around it*. Here is exactly how each one works and where the prompts physically sit.

### Option 1 — Git plus an in-app cache

**How it works.** There is no separate registry service at all. The prompt YAML files live in the repository. When a pipeline service starts up, it reads the YAML files off disk (they are shipped inside the container image, or pulled from the repo) and holds them in an in-memory cache — the `@lru_cache` in the loader above. At runtime, `load_prompt("apix.coaching_report", "prod")` returns the cached object; there is no network call.

**Where the prompts live.** In the repo, at `usecases/apix/prompts/*.prompt.yaml`. The "registry" is just the repository plus the process memory of each running service.

**Versioning and rollback.** The version is Git plus the YAML `version` field. To roll back, you revert the commit (or point the `prod` label at an older version) and redeploy — because the cache is loaded at startup, a change here means a new build/restart.

**What you do not get.** No web UI to edit or compare prompts, no built-in dashboards, no live hot-swap without a restart. It is the simplest possible thing that still gives versioned, gated, labelled prompts.

**Cost: $0.** The prompts are files in a repository you already pay nothing extra for.

### Option 2 — Langfuse prompt management

**How it works.** Langfuse is an **open-source product** from the Langfuse (Lang) family — a running application, not just a library. **We self-host it** in our own Azure container and network, so no prompt or trace data leaves our environment. Once it is running:

1. **Prompts are pushed into it.** On merge, a CI step reads the YAML files from Git and pushes each prompt (id, template, version, label, config) into Langfuse over its API. Git remains the master; Langfuse is the synced runtime copy. This keeps the two in step automatically — you still edit prompts as reviewed YAML in the repo, and Langfuse always reflects what merged.
2. **It gives a web UI** to view every prompt and every version, **compare** two versions side by side, **label** a version (`prod`, `staging`), and **roll back** by moving a label — all without touching the repo for emergency changes.
3. **The application fetches at runtime by id and label.** `registry.get("apix.coaching_report", label="prod")` is a call to Langfuse (cached in-process, with the last-known-good value as a fallback if Langfuse is briefly unreachable). Move the `prod` label in the UI and the running app picks up the new version on its next fetch — a genuine hot-swap, no redeploy.
4. **It also gives observability.** The same Langfuse instance ingests our traces and produces **token and cost dashboards** — per model, per prompt version, per user. So the one tool covers prompt management *and* the LLM-facing observability we need anyway (see the observability document).

**Where the prompts live.** Master copy in Git (`usecases/apix/prompts/*.prompt.yaml`); runtime copy inside the self-hosted Langfuse instance's database (PostgreSQL / ClickHouse), served from our own network.

**Cost.** Langfuse is **MIT-licensed — the software is free.** You pay only the Azure infrastructure to self-host it: a Container App plus a small managed PostgreSQL (and ClickHouse for high trace volumes). Indicative: **≈ $50–150/month** depending on trace volume (confirm at sizing). There is no per-seat or per-prompt license fee.

### Option 3 — Foundry prompt assets

**How it works.** Azure AI Foundry (Microsoft's managed AI platform) lets you store prompts as **versioned assets inside a Foundry project**. You publish a prompt as an asset through the Foundry **SDK** (software development kit) or portal; Foundry keeps every version. Because the asset lives inside the Foundry project, it **integrates directly with Foundry's own evaluations and tracing** — you can run a Foundry evaluation against a prompt asset and see the results next to it. The application fetches the asset by name/version at runtime through the same SDK. Microsoft runs and secures the whole thing; there is no server for us to operate.

**Where the prompts live.** Master copy still in Git; runtime copy as a managed asset inside the Azure AI Foundry project, in our Azure tenant. (We would still push from Git in CI, the same pattern as Langfuse, so the repo stays the source of truth.)

**What you get and give up.** You get a fully managed, Azure-native store that plugs into Foundry evaluations and tracing, with Azure identity and governance for free. You give up some flexibility — you are inside Foundry's model of prompts and its evaluation tooling rather than the open Langfuse/Ragas/DeepEval stack — and prompt observability is Foundry's, not the unified Langfuse view.

**Cost.** No separate license. It is **folded into ordinary Azure usage** (the Foundry project and the evaluation/judge tokens you run) — a **minor** add on top of what you already spend on Azure.

### Comparison

| Dimension | Git + in-app cache | Langfuse prompt management | Foundry prompt assets |
| --- | --- | --- | --- |
| **Where prompts live** | Files in the repo, cached in process memory | Master in Git; runtime copy in self-hosted Langfuse (our network) | Master in Git; runtime copy as managed asset in an Azure AI Foundry project |
| **Versioning** | Git history + YAML `version` | Every version stored in Langfuse, plus Git | Every version stored as a Foundry asset, plus Git |
| **Compare / rollback UI** | None (Git diff + redeploy) | Full web UI: compare versions, move labels, roll back live | Foundry portal: versioned assets, managed rollback |
| **Runtime fetch** | From in-memory cache (loaded at startup) | By `id + label` over Langfuse API, hot-swap without redeploy | By name/version via Foundry SDK |
| **Extra features** | None — just prompts | Tracing + token/cost dashboards in the same tool | Native tie-in to Foundry evaluations + tracing |
| **Ops burden** | Lowest — nothing new to run | We run/patch a self-hosted service (container + database) | Lowest — Microsoft runs it |
| **Data residency** | In our repo | In our network (self-hosted) | In our Azure tenant (Microsoft-managed) |
| **Cost** | **$0** — files in the repo | **MIT-free software + self-host infra ≈ $50–150/mo** (indicative) | **No license; folded into Azure usage (minor)** |

**Recommendation: start with Git plus an in-app cache, then add Langfuse for the UI and observability, and consider Foundry if you prefer a fully managed Azure-native store.**

Beginning with Git costs nothing, stands up no new service, and keeps all data in the repository, while still giving versioned, labelled prompts, the evaluation gate, and a clean rollback path. Langfuse is the natural next step because it is free software we self-host in our own network — data stays with us — and it folds prompt management, live hot-swap, and the token/cost observability we need anyway into one tool. Foundry is the right call if the preference is a fully managed, Azure-native asset store that plugs straight into Foundry's own evaluations, and you are willing to work inside Foundry's tooling. All three keep Git as the source of truth, so moving between them is a change of runtime copy, not of how we author prompts. Costs are indicative — confirm at a sizing exercise.

## (d) Versioning, labels, hot-swap, A/B, and evaluation-driven rollback

The YAML fields above are not decoration — they drive real runtime behaviour:

- **Versioning.** Every change bumps `version`. Version 2 and version 3 both exist in the registry; nothing is overwritten.
- **Labels (prod / staging).** A label is a pointer to a version. Production reads the version tagged `prod`; staging can read a newer candidate. Promoting a prompt is moving the `prod` label, not editing text.
- **Hot-swap without redeploy.** With a registry service (Langfuse or Foundry), the running app fetches the live version by label, so moving the `prod` label to a new version changes what production uses without shipping a new build. Rolling back is moving the label back — near-instant, no deploy. (With the Git+cache option this needs a restart.)
- **A/B.** We can point a slice of traffic at one version and the rest at another by label, capture the evaluation and cost signals for each (via the tracing described in the observability document), and keep the winner.
- **Evaluation-driven rollback and compare.** This is where it comes together. When a new prompt version is scored against the golden dataset, we get a per-metric comparison against the previous version. That difference is the decision signal: **keep the better prompt, roll back to the previous one, or combine the strengths of two versions into a better third.** The choice is made on measured evaluation differences, not on impression.

## Today → Our setup → What changes

| | Today | Our setup | What changes |
| --- | --- | --- | --- |
| **Where prompts live** | Text buried inside code files, already in Git | One versioned YAML file per prompt, still in Git | Prompt becomes a first-class artifact with its own version and history |
| **Change control** | Ships like any code change, no quality check | Evaluation gate scores every change against the golden dataset before deploy | A prompt edit is measured against ground truth, not eyeballed |
| **Runtime** | Prompt baked into the deployed build | Registry serves prompts by id + label; app loads by reference | Swap or roll back a version without a redeploy |
| **Choosing a version** | Manual judgement | Per-metric evaluation comparison between versions | Keep, roll back, or combine versions on measured signal |

**Net:** prompt management here is versioned YAML prompt artifacts, an evaluation gate on every change, and a registry for rollback and comparison. That — not "prompts in Git" — is the difference from how the team works today.
