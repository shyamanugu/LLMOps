# Skills library

Reusable how-to knowledge for the LLMOps framework. Each skill is a short, generic guide to one
component — what it is, when to use it, how it works *in this repo* (with the real file and
functions), and the pitfalls. A chat mode (agent) or a person `@`-mentions a skill to pull that
knowledge into a session.

## Skills vs memory
- **Skills are generic and reusable.** They describe a capability that stays the same across every
  client and project. When this framework is reused elsewhere, the skills come along unchanged.
- **Memory is project-specific.** Facts that are true only for *this* project live in
  `.github/memory/` (`project-memory.md`, `decisions.md`, `conventions.md`) — not in a skill.

So: how RAG works → a skill. Which sources this client uses → memory.

## Skill file shape
Each `.github/skills/<name>.skill.md` is:

```
# <Name>

**What it is** — one or two lines.
**When to use** — the situations that call for it.
**How it works here** — the real file(s) + key functions and their contract.
**Key files** — the exact paths.
**Example** — a short code or JSON snippet.
**Pitfalls** — the mistakes to avoid.
```

## Who keeps them current
The **Skill Maintainer** chat mode (`.github/chatmodes/skill-maintainer.chatmode.md`) owns this
library. When a component's behaviour changes, it updates the relevant skill; when a genuinely new
reusable capability is added, it adds a new skill file and a line here. Don't fork skills per
project — keep them generic and let memory carry the specifics.

## The skills
- `model-management.skill.md` — call a model by task alias; cost; mock mode.
- `prompt-management.skill.md` — prompt JSON, render, versioning; GitHub as registry.
- `guardrails.skill.md` — input/output checks, PII redaction, Content Safety.
- `observability.skill.md` — traces, spans, model/tool records, cost.
- `rag.skill.md` — multi-source retrieval; adding a loader; keyword vs Azure AI Search.
- `evaluation-gate.skill.md` — golden dataset, scoring, thresholds, pass/fail.
- `pipeline.skill.md` — sequential steps, the state dict, guardrail wrapping.
