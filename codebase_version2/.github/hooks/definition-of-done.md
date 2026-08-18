# Definition of done

Not an executable hook — the bar every change must clear. Mirrors the golden rules in
`.github/copilot-instructions.md`. A change is done only when **all** of these hold:

1. **Config-as-code, not hard-coding.** Model choice lives in `models.json` (task alias), prompt text in a `*.prompt.json` file, thresholds in `evaluators.json`. No model names, prompts, or thresholds baked into Python.
2. **The eval gate is green.** `python scripts/run_eval_gate.py <usecase>` exits 0 for any prompt/pipeline/knowledge/evaluator change.
3. **The framework was reused, not duplicated.** New behaviour is a new tool or step; framework logic wasn't copied. Public framework signatures stayed stable.
4. **Answers are grounded.** Prompts answer only from retrieved context and say "I don't know" otherwise; the pipeline retrieves before it answers.
5. **Guardrails + observability are present.** Entry points call `check_input`/`check_output` and run inside a trace.
6. **Secrets are not in code.** Endpoints/keys come from env; Azure uses Managed Identity; CI uses OIDC.
7. **Memory is updated if something durable changed.** Decisions/conventions/state recorded in `.github/memory/` in the same change.

Also: explainable (docstrings, *why* comments, small files) and only `.py` / `.json` / `.yml` files.
