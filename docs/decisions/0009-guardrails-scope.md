# ADR 0009: Guardrails — composable checks, directional PII defaults, no redaction

## Status
Accepted

## Context
Orchestration's `ModelStep` has accepted a `guardrail` parameter since it was built (satisfied only by the no-op `PassthroughGuardrail`), with the real implementation explicitly deferred to this component. "Implement all possible guardrails" was the brief — the questions were which checks are actually buildable without new Azure access, how they compose, and where the honest boundaries are.

## Decision
1. **Five checks need no Azure resource at all**: `PIIGuardrail` (regex), `BlocklistGuardrail` (config-supplied terms), `PromptInjectionGuardrail` (heuristic pattern match, input-only), `SecretLeakGuardrail` (regex, output-only), `MaxLengthGuardrail`. These are free, always available, and on by default (except `BlocklistGuardrail`'s terms, which start empty, and `SecretLeakGuardrail`'s noisy `generic_api_key` category, which starts disabled).
2. **One check uses a real Azure resource**: `AzureContentSafetyGuardrail`, wrapping Azure AI Content Safety's `analyze_text` harm-category moderation (Hate, SelfHarm, Sexual, Violence, each 0-7). Off by default, opt-in per usecase, same interim key-auth pattern as every other real-Azure backend in this platform (Model Management's `AzureOpenAIProvider`, Data & Tools' `AzureAISearchBackend`/`AzureSpeechBackend`).
3. **PII defaults differ by direction**: `flag` (allowed through, recorded) on input, `block` on output, per category. PII a customer volunteers about themselves is often legitimate input; PII the model repeats or invents in output is a stronger signal something is wrong.
4. **`CompositeGuardrail` combines any set of checks into Orchestration's exact `check_input`/`check_output` shape** — a drop-in replacement for `PassthroughGuardrail`, no change to Orchestration (08) required. `CheckResult` and the `GuardrailCheck` shape are defined independently in this component rather than imported from `orchestration.guardrails`, keeping the dependency direction consistent with every other component (nothing here imports Orchestration; Orchestration, or a consuming test, imports this).
5. **Policy lives in `config/guardrails.yaml`**, resolved per usecase per environment by `build_guardrail()` — same mechanism/policy split as every other component. A usecase not listed gets the `defaults` block.
6. **Not built**: redaction, Content Safety's Prompt Shields, topic/scope restriction, rate limiting. See Alternatives Considered and Revisit When.

## Alternatives Considered
- **Redaction instead of / alongside blocking**: rejected for now — Orchestration's `GuardrailCheck` protocol only returns `allowed`/`reason`, not modified text. Building redaction here would either silently do nothing useful (the modified text has nowhere to go) or require unilaterally changing an interface Orchestration already depends on. That's a cross-component interface change, not a call this component should make alone.
- **Wrapping Content Safety's Prompt Shields** as a second Azure-backed injection detector: rejected — its exact SDK call shape wasn't verified against a live resource at the time of writing (unlike `analyze_text`, whose shape is well-documented and used with reasonable confidence). Authoring an unverified integration and presenting it as working would violate the same honesty standard this platform has held to "authored vs. deployed" throughout (ADR 0001 onward) — here extended to "authored vs. verified against a real SDK shape."
- **Topic/scope restriction as an LLM-judge-style check**: rejected — no usecase has defined what "off-topic" means for it yet, and building a speculative judge-based check risks getting the definition wrong before any real requirement exists. Same reasoning already applied to voice (ADR 0003) and semantic-similarity evaluation (ADR 0008): don't build ahead of a concrete need.
- **Rate limiting/abuse detection here**: rejected — this is a request-volume/infrastructure concern, not a content check; it belongs with Serving & Hosting (10) or API Management, mirroring the voice-pattern split between components 03 and 07.

## Consequences
- A usecase gets meaningful default protection (prompt injection blocked, PII flagged/blocked appropriately, secrets never leaked in output) with zero Azure setup and zero config — `build_guardrail()` with an unlisted usecase still applies the `defaults` block.
- The one Azure-backed check (Content Safety) requires the same RBAC-deferred, key-based interim auth as every other real backend in this platform — 🔒 role assignment is a Phase 0 queue item when a usecase actually needs it.
- If a usecase eventually needs redaction, it forces a real design conversation about changing `GuardrailCheck`'s contract in Orchestration (08) — flagged now so it's an expected, not surprising, future change.
- `generic_api_key` disabled by default means a usecase that genuinely leaks bespoke-format secrets in output won't be caught by that category alone; the three named-format categories (AWS keys, Azure connection strings, private key headers) still catch the common cases.

## Revisit When
- A usecase needs redaction, not just blocking — design a `GuardrailCheck` protocol change in Orchestration (08) first, then update this component's checks to populate a modified-text field.
- Someone verifies Content Safety's Prompt Shields SDK shape against a live resource — add `AzurePromptShieldGuardrail` as a second, stronger injection detector alongside the heuristic one.
- A usecase defines a concrete "off-topic" boundary — build a topic-restriction check for that usecase's actual definition, not a speculative general one.
- A usecase's traffic makes `generic_api_key` a reasonable signal despite the noise — enable it per usecase in config, don't flip the platform default.
