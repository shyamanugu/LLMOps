---
mode: 'ask'
description: 'Review the current change against the definition of done and the golden rules'
---

# Review this change

Review the current change (the staged/working diff, plus `${file}` and `${selection}` if I point you
at them) against the definition of done and the golden rules. This is a read-only review — list
what is missing, do not edit.

## Check against

- The definition of done in [definition-of-done.md](../hooks/definition-of-done.md).
- The golden rules in [copilot-instructions](../copilot-instructions.md).

## Report a checklist — for each item say PASS / FAIL / N/A with the file + reason

1. **No hard-coded model** — model choice goes through an alias in
   [models.json](../../framework/models.json), never a raw deployment name in `.py`
   (golden rule 1).
2. **No inline prompt** — prompt text lives in a `usecases/*/prompts/*.prompt.json` file, not in
   Python (golden rule 1); if a prompt changed, `version` was bumped and `changelog` appended.
3. **Grounding** — any prompt answers ONLY from retrieved context and says "I don't know" otherwise
   (golden rule 4).
4. **Gate was run** — `python scripts/run_eval_gate.py <usecase>` was run and is green; if a prompt,
   pipeline, or dataset changed and it was not run, flag it (golden rule 2).
5. **Reuse, not duplication** — new behaviour is a new tool or step, not a copy of framework logic
   (golden rule 3); guardrails + observability are still called on any new entry point
   (golden rule 5).
6. **Secrets** — no endpoints/keys hard-coded; env / Managed Identity only (golden rule 7).
7. **File types + style** — only `.py` / `.json` / `.yml`, module docstrings present, type hints,
   no stray `print` in framework code (golden rule 6).
8. **Memory updated** — if something durable changed (a decision, convention, or new pattern), was
   [project-memory.md](../memory/project-memory.md) (and `decisions.md` / `conventions.md`) updated?
   If not, recommend `/update-memory`.

End with the single most important thing to fix before this can merge.
