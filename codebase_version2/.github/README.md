# GitHub Copilot setup for this repo

This `.github/` folder configures **GitHub Copilot Chat** so it understands this project and gives
consistent, useful output in every session. Copy the whole folder with the repo. Everything here is
plain markdown.

## What each part is (and whether Copilot loads it automatically)

| Folder / file | What it is | Loaded automatically? |
|---|---|---|
| `copilot-instructions.md` | The master brief — architecture, golden rules, memory protocol | **Yes — included in every chat** |
| `instructions/*.instructions.md` | Path-specific rules (Python, framework, use cases, prompts, evaluation, pipelines) | **Yes — when you edit a matching file** (via `applyTo`) |
| `prompts/*.prompt.md` | Reusable tasks you run with `/name` in chat (e.g. `/add-usecase`) | ▶ You invoke them with `/` |
| `chatmodes/*.chatmode.md` | Custom "agents" you pick from the chat **mode** dropdown | ▶ You select one per chat |
| `skills/*.skill.md` | A knowledge library (how each component works) | ▶ You `#`/@-reference them when needed |
| `hooks/*.md` | Policy / definition-of-done checklists | ▶ Referenced by the agents & instructions |
| `memory/*.md` | Curated cross-session memory (state, decisions, conventions) | ▶ Read at the start of a task; kept current |
| `../AGENTS.md` | Brief for the autonomous Copilot coding agent | **Yes — by the coding agent** |

## Turn it on (one setting)
In VS Code, ensure custom instructions are enabled (they are, by default, in recent versions):
`Settings → search "instruction files" → Use Instruction Files` = on
(`github.copilot.chat.codeGeneration.useInstructionFiles: true`). That is what makes
`copilot-instructions.md` load into every chat.

## How to use it, day to day
1. **Start a chat and pick an agent (chat mode)** that fits: LLMOps Engineer, Prompt Engineer,
   Evaluation Engineer, RAG/Data Engineer, or Skill Maintainer.
2. **Run a task prompt** with `/`, e.g. `/add-usecase`, `/add-prompt`, `/run-eval-gate`.
3. **Reference a skill** when you want deep context, e.g. type `#` and pick
   `skills/evaluation-gate.skill.md`, or drag the file into chat.
4. **At the end**, if you learned something durable, switch to the **Skill Maintainer** agent (or run
   `/update-memory`) so the setup absorbs it.

## Your two questions, answered

### "Each chat behaves completely differently / underperforms."
GitHub Copilot has **no automatic long-term memory** across chats (unlike ChatGPT's memory). Each
chat starts fresh. The fix, which this folder implements:
- **`copilot-instructions.md` is injected into every chat automatically** — so it is your persistent
  context. Everything the model must always know lives there (or is pointed to from there).
- **`memory/project-memory.md`** holds the current state; read it at the start of a task. The
  instructions tell the agent to do this.
- **Pick a chat mode** every session — it sets a consistent persona and toolset, so behaviour does
  not swing between chats.
- **Keep memory curated** — run `/update-memory` or use the Skill Maintainer. Consistency comes from
  good, current instruction/memory files, not from hidden memory.
Net: treat `copilot-instructions.md` + `memory/` as the brain. If a chat underperforms, it is almost
always because those files are missing context — add it there and every future chat improves.

### "An agent that updates the skills as the project matures."
That is the **Skill Maintainer** chat mode (`chatmodes/skill-maintainer.chatmode.md`). At the end of a
session, select it and tell it what changed; it makes surgical updates to the skills and memory. Use
it whenever a decision, convention, or reusable pattern changes — including when you reuse this
framework for another project (the skills stay generic; project facts go into `memory/`).

## Honest limits (so nothing surprises you in the client environment)
- Copilot has **no runtime hooks** like Claude Code. The `hooks/` files are checklists/policies the
  agents follow, not executable events.
- **Skills are not a native Copilot feature.** They are a convention: markdown the agents and you
  reference. Copilot will not auto-load them; reference them with `#`/@ when needed.
- Chat modes and prompt files are supported in **VS Code / Visual Studio Copilot Chat**. If a
  teammate uses a client that does not support them, `copilot-instructions.md` still works everywhere.

## If you rename the folder
This setup assumes the repo layout of this project (`framework/`, `usecases/`, `scripts/`,
`pipelines/`). Keep `.github/` at the **repo root**. If you take it to another project, keep the
files, update `memory/project-memory.md` for the new project, and let the Skill Maintainer adapt the
rest.
