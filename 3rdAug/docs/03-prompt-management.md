# Prompt Management

> The single most common mistake in a GenAI (generative AI) project is a prompt buried in a Python
> f-string somewhere in the app code, changed by whoever is debugging that day, with no record of what
> it used to say. This note describes the alternative: prompts as versioned files in Git, promoted
> through a registry, changeable without a full app redeploy.

## Where prompts actually live

Source of truth is Git. Every prompt is one file: `/prompts/<use-case>/<prompt-name>.yaml`. It is not
allowed to change except through a pull request (PR), and that PR cannot merge unless it passes the
evaluation gate (see below). This single rule — no prompt change without a passing eval — is what
turns "we edit prompts" into "we operate prompts."

### Full example prompt file

```yaml
# prompts/billing-assistant/answer-question.yaml
id: billing-assistant.answer-question
version: 2.3.0                     # semantic versioning: major.minor.patch
status: active

model_hints:
  preferred_alias: reason          # task alias, resolved via models.yaml — see model management doc
  fallback_alias: summarize
  max_output_tokens: 600
  temperature: 0.2

variables:
  - name: customer_question
    type: string
    required: true
  - name: retrieved_context
    type: string
    required: true
    description: "Top-k chunks from the billing knowledge base index"
  - name: account_type
    type: string
    required: false
    default: "standard"

template: |
  You are a billing support assistant for {account_type} accounts.
  Answer the customer's question using ONLY the context below. If the context
  does not contain the answer, say you don't know and offer to escalate.

  Context:
  {retrieved_context}

  Customer question:
  {customer_question}

  Answer in 3 sentences or fewer. Do not invent policy details.

eval_refs:
  golden_dataset: evals/billing-assistant/golden-v4.jsonl
  evaluators:
    - groundedness        # checks answer is supported by retrieved_context
    - answer_relevance
    - pii_leak_check

changelog:
  - version: 2.3.0
    date: 2026-07-22
    change: "Added account_type variable to adjust tone for premium accounts"
    author_pr: "#412"
  - version: 2.2.0
    date: 2026-06-30
    change: "Tightened instruction to cap hallucinated policy claims (groundedness eval was at 0.81)"
    author_pr: "#389"
  - version: 2.1.0
    date: 2026-05-14
    change: "Initial production version"
    author_pr: "#301"
```

Every field earns its place: `id` and `version` let the runtime ask for an exact prompt; `model_hints`
keeps the prompt author's intent (this prompt wants a reasoning-tier model) without hard-coding a model
name; `eval_refs` ties the prompt permanently to the dataset it must keep passing; `changelog` answers
"why did this change" without anyone needing to dig through Git blame.

## The PR + eval gate flow

1. Engineer or prompt author edits the YAML file, bumps `version`, adds a `changelog` entry, opens a
   PR.
2. `pr-checks.yml` (the CI workflow described in the GitHub ops backbone) detects the changed file
   under `/prompts/`, runs the prompt against a small golden subset, and posts a scorecard as a PR
   comment.
3. A reviewer from `CODEOWNERS` (prompt reviewers, plus an SME for anything customer-facing) approves.
4. On merge, `eval-full.yml` runs the complete golden dataset overnight or immediately, and the result
   is what actually promotes the new version into the runtime registry with the `staging` label.
5. After a manual or scripted check in staging, the version gets re-labeled `prod`. This re-labeling
   is a config action, not a redeploy — see hot-swap below.

## Runtime prompt registry — the options

Git holds the historical record. At runtime, the app needs to ask "give me the prompt with this ID,
labeled `prod`" without redeploying every time a label changes. That's the job of a runtime registry,
sitting between Git and the running application.

| Option | What it is | How labeling/hot-swap works | Notes |
|---|---|---|---|
| **Langfuse Prompt Management** | Open-source LLM observability tool with a built-in prompt store (self-hostable, e.g. on Azure Container Apps + PostgreSQL) | Prompts pushed from CI; each version can carry labels like `prod`/`staging`; app fetches by label with a short cache TTL (time to live), so a label change is live in seconds | Best fit if already running Langfuse for observability — one tool for both jobs, and prompt-level performance metrics show up next to traces |
| **Microsoft Foundry prompt assets** | Prompt asset type native to the Foundry portal/SDK | Versioned assets, referenced by ID from the orchestration code; environment binding controls which version an environment resolves to | Best fit for an Azure-native stack with no separate observability tool; ties naturally into Foundry's eval-linked tracing |
| **Plain Git + application-level cache** | No separate registry — the app pulls the YAML file straight from a Git ref (or a built artifact) and caches it in memory with a refresh interval | "Labeling" is just which branch/tag the app points to; hot-swap means changing a config value and waiting for the next cache refresh (typically minutes) | Simplest option, no extra infrastructure, but no built-in A/B split and no live prompt-level metrics — fine for Level 0/Level 1 maturity, outgrown by Level 2 |

Recommended lane for an Azure-first stack: **Foundry prompt assets** if there's no plan to self-host
Langfuse; **Langfuse** if observability is already going there, since it gives prompt management and
tracing in the same place. Either way, CI is what pushes Git changes into the registry — nobody edits
the registry portal directly.

## Labels: prod vs staging

Every prompt version can carry a label independent of its version number. A version can be `staging`
for a week while it earns trust, then get relabeled `prod` — the running application never has to
change, because it always asks for "the version labeled `prod`," not "version 2.3.0" by number. This
is also what makes rollback painless: relabel `prod` back to the previous version, and every request
after that point uses the old prompt again, with no deploy.

## Hot-swap without redeploy

Because the application resolves prompts by ID + label at request time (not by baking prompt text into
the compiled container), changing which version serves traffic is a registry update, not a code
deploy. The only thing that needs to be fast is the app's cache refresh interval — keep that in the
tens-of-seconds range for Level 2+ maturity, minutes is acceptable for Level 0/1.

## A/B testing two prompt versions

1. Push both candidate versions to the registry with distinct labels, e.g. `ab-control` and
   `ab-variant`.
2. At the app or gateway layer, split traffic by a stable key (user ID hash, session ID) so the same
   user always lands on the same variant during the test window — this avoids a user seeing
   inconsistent behavior mid-conversation.
3. Tag every trace with which variant served it (this is a required observability field, see the
   observability note).
4. Compare online metrics after a defined sample size: user feedback rate, escalation rate, latency,
   cost per response, and any automated eval score computed on sampled live traffic.
5. Promote the winner to `prod`, demote the loser back to `staging` for reference, never delete —
   keep it in Git history regardless.

## Naming and semantic versioning conventions

- File and `id` naming: `<use-case>.<prompt-name>`, lowercase, hyphen-separated. Matches the folder
  path so anyone can find the file from the ID alone.
- Semantic versioning (semver): `major.minor.patch`.
  - **Patch** (`2.2.0` → `2.2.1`): wording tweak, no behavior change expected, no eval re-run required
    beyond the standard PR check.
  - **Minor** (`2.2.0` → `2.3.0`): new variable, instruction change, expected to shift eval scores —
    full golden dataset run required before promotion.
  - **Major** (`2.x.x` → `3.0.0`): change to the prompt's purpose or output contract (e.g., output
    format changes from prose to structured JSON) — treat like a breaking API change, coordinate with
    every caller.

## Anti-patterns to flag in review

- **Prompt text hard-coded in application code.** If it's an f-string or a string constant in `src/`,
  it has no version history, no eval binding, and no way to hot-swap. Move it to `/prompts` immediately
  even if that's the only fix in the PR.
- **Untracked edits made directly in a portal.** Editing a prompt asset or a Langfuse prompt straight
  in the UI, without a matching Git commit, means the next CI sync silently overwrites it — or worse,
  it survives and nobody knows why production behavior no longer matches what's in Git. Every registry
  write should be traceable to a PR.
- **One giant prompt file trying to do five jobs.** If a prompt has branching logic inside the template
  for different intents, split it into separate prompt files with a router in front, so each one has
  its own golden dataset and its own version history.
- **Skipping the changelog.** A version bump with no changelog entry is a version bump nobody can
  explain in six months.
