# Before you change code (checklist)

Not an executable hook — a checklist to run yourself before editing.

- [ ] **Read the memory.** `.github/memory/project-memory.md` (current state + what's next), and the decisions/conventions files if relevant.
- [ ] **Read the relevant skill** in `.github/skills/` for the component you're touching.
- [ ] **Confirm the target.** Is this a `framework/` component (reusable) or a `usecases/<name>/` change (specific)? Don't put use-case specifics in the framework.
- [ ] **Don't hard-code.** Model → `models.json` alias. Prompt → a `*.prompt.json` file. Threshold → `evaluators.json`. Secret → env / Managed Identity.
- [ ] **Plan to keep signatures stable** if editing `framework/`.
- [ ] **Know how you'll verify:** which use case's eval gate will you run?
