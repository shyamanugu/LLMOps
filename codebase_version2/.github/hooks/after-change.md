# After you change code (checklist)

Not an executable hook — a checklist to run yourself after editing.

- [ ] **Run the eval gate if you touched a prompt, pipeline, knowledge, or evaluator:**
      `python scripts/run_eval_gate.py <usecase>` must exit 0 (PASS).
- [ ] **Grow the golden set** if you fixed a wrong/ungrounded answer — add the case so it can't regress.
- [ ] **Update memory if a decision or convention changed** — edit `.github/memory/` in the *same* change. Stale memory is worse than none. (`/update-memory` or ask the Skill Maintainer.)
- [ ] **Keep it explainable.** Module docstring present, comments say *why*, files stayed small.
- [ ] **No new file types.** Only `.py` / `.json` / `.yml`.
- [ ] **Guardrails + observability** still wrap any new entry point (`check_input`/`check_output`, inside a trace).
