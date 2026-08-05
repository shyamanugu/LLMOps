# Prompt Management

Let us be precise about the challenge, because this is the component where the difference from what the team does today is easy to get wrong.

Your prompts are already in Git. The whole project is version-controlled, and the prompt text sits inside that repository along with the code. So **"store prompts in Git" is not the change.** If that were the whole pitch, there would be nothing new here, and you would be right to be unconvinced.

The real change is three specific things: prompts become **one versioned YAML artifact each**, every prompt change passes an **evaluation gate**, and a **runtime registry** holds prompts so we can swap and roll back versions without a redeploy. Below is each one, concretely.

## (a) One YAML file per prompt

Today the prompt text is buried inside a code file — a string constant, an f-string, something assembled at runtime. There is no YAML file per prompt today. That means a prompt has no independent version, no place to record why it changed, and no declared link to how it should be tested. You confirmed this is a gap worth closing.

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
- **`temperature`** — the sampling setting, versioned with the prompt because it affects output as much as the wording.
- **`inputs`** — the variables the template expects (`agent_name`, `program`, `dimension_scores`, `evidence`). This is a contract; the loader can validate that all inputs are supplied.
- **`template`** — the prompt text itself, with `{{...}}` placeholders for the inputs. This is the part that used to be buried in code.
- **`eval_refs`** — the golden dataset(s) this prompt is graded against. This is the link that makes the evaluation gate possible: the prompt itself declares how it must be tested.
- **`changelog`** — plain-language notes on what changed and why, version by version. When a coaching note goes wrong in production, this is where you see that v3 added the "cite the evidence" rule.

## (b) The evaluation gate on every prompt change

Today, editing a prompt ships like any other code change. It goes through review, maybe unit tests, and out — with no check that the new wording actually produces better (or even acceptable) output. There is no gate.

Our setup runs every prompt change through the CI/CD pipeline. When the YAML file changes, the pull-request workflow scores the prompt against the golden datasets named in its `eval_refs`, and the change is blocked from approval and deploy unless it clears the thresholds. This is the same `pr-checks.yml` gate the backbone document describes:

```yaml
- run: python evals/run.py --subset changed --fail-under baseline
  #     runs Ragas + DeepEval + tool_selection on the changed prompt;
  #     exits non-zero (blocks merge) if a metric drops past its baseline
```

So a prompt edit is no longer a matter of "looks good to me." It is measured — against ground truth, on every change, before it can reach production. That is the single biggest practical difference from prompts-in-Git-as-usual.

## (c) The runtime registry

You asked what a registry actually is. Plainly: a **registry is where prompts are held at runtime so the application can fetch the right version by id and label, and so we can fall back to a previous version if a new one turns out worse.** It is the difference between "the prompt is baked into the deployed build" and "the running app looks up which prompt version is live right now" — the latter is what lets us roll back without a redeploy.

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

There are three sensible ways to run the registry. Git stays the source of truth in all three; they differ in where the runtime copy lives.

| Option | What it is | When |
| --- | --- | --- |
| **Git + in-app cache** | The prompt YAML in the repo, loaded into an in-memory cache in the app (the `lru_cache` above). No extra service; everything stays in our repo. | **Start here.** Simplest, nothing new to operate. |
| **Langfuse prompt management** | An open-source product from the Langfuse (Lang) family. We self-host it in our own container and network, so data stays with us. It also gives observability and token/cost dashboards. | Adopt as we scale — one tool covers prompts and observability. |
| **Foundry prompt assets** | Prompt assets native to the Azure AI Foundry platform (Microsoft). More managed and Azure-native. | Add if we want the fully managed, Azure-native route. Cost to confirm. |

**Recommendation: start with Git plus an in-app cache, and add Langfuse or Foundry as we scale.** Beginning with Git means no new service to stand up and no data leaving the repository, while still giving versioned, labelled prompts and a clean rollback path. Langfuse is the natural next step because self-hosting it keeps data in our network and folds prompt management together with the observability we need anyway. Foundry is the option if you prefer a fully managed Azure-native asset store. Cost either way is minor and to be confirmed.

## (d) Versioning, labels, hot-swap, A/B, and evaluation-driven rollback

The YAML fields above are not decoration — they drive real runtime behaviour:

- **Versioning.** Every change bumps `version`. Version 2 and version 3 both exist in the registry; nothing is overwritten.
- **Labels (prod / staging).** A label is a pointer to a version. Production reads the version tagged `prod`; staging can read a newer candidate. Promoting a prompt is moving the `prod` label, not editing text.
- **Hot-swap without redeploy.** Because the running app fetches the live version by label, moving the `prod` label to a new version changes what production uses without shipping a new build. Rolling back is moving the label back — near-instant, no deploy.
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
