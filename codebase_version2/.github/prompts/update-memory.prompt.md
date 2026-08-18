---
mode: 'agent'
description: 'Update project memory (project-memory / decisions / conventions) with what changed this session'
---

# Update project memory

Record what changed this session into the durable memory so every future chat stays consistent.
This is the manual counterpart to the `skill-maintainer` chat mode. See the memory protocol in
[copilot-instructions](../copilot-instructions.md).

## Files to update

1. [project-memory.md](../memory/project-memory.md) — the CURRENT state. Update "What is built" and
   the "In progress / next" checklist (tick what got done, add what is now next). Keep it SHORT and
   current — trim anything stale. This file is a snapshot, not a log.
2. `.github/memory/decisions.md` — APPEND-ONLY. If a real decision was made (a model alias choice, a
   threshold, a wiring approach, a naming convention), add a dated entry: what was decided, and why /
   the alternative rejected. Never rewrite past decisions.
3. `.github/memory/conventions.md` — add or refine any durable convention or gotcha discovered
   (e.g. a pattern to follow, a trap to avoid). Keep entries terse.

## Rules

- Only record what is DURABLE (decisions, conventions, new patterns, status). Skip one-off details.
- If nothing durable changed, say so and change nothing — stale memory is worse than none.
- Match the existing tone and structure of each file. Markdown only.
- Do not touch code or run the gate here — this prompt only maintains memory.

Summarise, in one line, what you added to each file.
