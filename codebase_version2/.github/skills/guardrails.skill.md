# Guardrails

**What it is** — Safety checks on what goes into and comes out of the model. Input is checked before
the model is called; output is redacted before it's returned. Guardrails are not optional.

**When to use** — Every entry point that reaches a model. The pipeline already wraps them (see the
pipeline skill), so mostly you extend the checks rather than call them by hand.

**How it works here** — `framework/guardrails.py`:
- `check_input(text)` → `{allowed, reason}`. Blocks obviously unsafe input. Offline it uses a small
  built-in unsafe-word list; if `CONTENT_SAFETY_ENDPOINT` is set it defers to `_content_safety`.
- `check_output(text)` → `{allowed, reason, text}`. Redacts personal data from the output; runs
  Content Safety on the redacted text when configured.
- `redact_pii(text)` → `(redacted_text, count)`. Replaces email / card / SSN with tags
  (`[EMAIL]` / `[CARD]` / `[SSN]`) via `_PII_PATTERNS`.
- `_content_safety(text)` is the optional Azure AI Content Safety hook (categories +
  prompt-injection shields) — currently a `# TODO(wiring)` stub that fails safe (allow) for the demo.

**Key files** — `framework/guardrails.py`, `framework/config.py` (`CONTENT_SAFETY_ENDPOINT`),
`framework/pipeline.py` (where they're called).

**Example**
```python
from framework import guardrails
gin = guardrails.check_input(question)
if not gin["allowed"]:
    return "I can't help with that request."
safe = guardrails.check_output(answer)["text"]   # PII redacted
```

**Pitfalls**
- Adding an entry point that skips `check_input` / `check_output` — both are mandatory.
- Treating the offline checks as production-grade — the unsafe-word list and PII regex are
  stand-ins; real coverage comes from Content Safety once wired.
- Widening `_PII_PATTERNS` without testing — an over-eager card/SSN regex can redact legitimate
  numbers.
- Leaving `_content_safety` returning allow in production — wire it before going live.
