# `.github/hooks/` — policies, not executable hooks

**Honest note up front:** GitHub Copilot has **no runtime hook engine.** Unlike Claude Code, Copilot cannot run a script automatically before or after you edit a file. There is no programmatic enforcement here.

So the files in this folder are **checklists and policies**, not code that runs. They are the shared "definition of done" for this repo, written in plain markdown.

## How they are actually enforced

- **The chat modes and instruction files reference them.** The agents in `.github/chatmodes/` and the path-scoped rules in `.github/instructions/` point back to these checklists, so Copilot is told to follow them as part of doing the work.
- **You can @-mention them in chat.** In a Copilot chat, reference a file (e.g. `#before-change.md` / attach `after-change.md`) to pull the checklist into context before or after a change.
- **They mirror the golden rules** in `.github/copilot-instructions.md` and the memory files — one source of truth, restated as a per-change checklist.

## Files

- `before-change.md` — run through this before editing code.
- `after-change.md` — run through this after editing code.
- `definition-of-done.md` — the bar a change must clear before it's "done".

These are enforced by discipline (and by the eval gate in CI, which *is* real and *does* block). Keep them short and current.
