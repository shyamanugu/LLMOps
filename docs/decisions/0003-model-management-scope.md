# ADR 0003: Model Management — provider abstraction, capability taxonomy, and voice architecture boundary

## Status
Accepted

## Context
Model Management needs to support more than a single provider and a single "chat model" concept: reasoning models, high-volume/cost-optimized models, embeddings, an evaluation judge model, and voice — with the explicit expectation that Anthropic or other providers may be added later, and that AFNI's client base spans multiple geographic zones rather than a single region.

Voice specifically has two legitimate architectures: a single Realtime API model handling audio directly, or a pipeline of separate Speech-to-Text and Text-to-Speech services around an existing chat model. These are not the same kind of thing — the first is a model deployment, the second is a composition of two non-LLM cognitive services with an LLM in the middle.

## Decision
1. `models.yaml` uses a capability-based alias taxonomy (`reason`, `bulk`, `nano`, `embedding`, `judge`, `voice`), each entry carrying `provider`, `deployment`, and `kind` (`chat` | `embedding` | `realtime`). New aliases are added by editing config, never by changing resolver code.
2. A provider adapter interface (`src/providers/base.py`) decouples the resolver from any single SDK. Azure OpenAI is the only implemented adapter today; adding Anthropic or another provider later means implementing the same interface, not redesigning the resolver.
3. Default region for all deployments is `eastus`. This is a default, not a constraint — AFNI's client base spans multiple regions, and per-deployment region overrides may be needed later for data-residency reasons. That capability is not built now; it is noted here so it isn't forgotten when the need becomes concrete.
4. Model Management owns only the **Realtime API** voice pattern (`kind: realtime` — it is a model deployment like any other). The **separate STT → chat model → TTS pipeline** pattern is not owned here — Speech-to-Text and Text-to-Speech are not "models" in the alias/provider/kind sense, they are cognitive services composed around an existing chat alias. That pattern belongs to Data & Tools (component 07) as tools, alongside `search_knowledge` and `query_sql`.
5. Neither voice pattern is provisioned yet. The `voice` alias exists in config with `deployment: null` so the slot is visible and ready, but nothing is deployed until a real usecase needs it.

## Alternatives Considered
- Treat STT/TTS as part of Model Management too, under a broader "any AI capability" umbrella: rejected. It would blur the resolver's contract (alias → model deployment) with a fundamentally different resource shape, making config harder to reason about as more providers are added.
- Provision both voice patterns now, since "the platform should have it available": rejected — available means the architecture has a place for it, not that infrastructure sits idle waiting for a consumer. Mirrors the Key Vault deferral in ADR 0001.

## Consequences
- Orchestration code always asks for an alias plus expected kind, never a raw model name — a provider swap for any alias is a config change plus an evaluation-gate pass, not a code change.
- When a usecase first needs voice, the decision of which pattern to build is already scoped: Realtime API is a `models.yaml` entry plus a bicep deployment; STT/TTS is new tools under component 07. No architectural debate needed at that point, only the build itself.
- The region default will need revisiting once a specific client contract requires data to stay in a specific geography — flagged here so it surfaces as a known item, not a surprise.

## Revisit When
- A specific usecase requires voice — implement whichever pattern that usecase actually needs, not both speculatively.
- A client contract requires region-specific data residency — add a per-deployment region override to `models.yaml` at that point.
- A second model provider is actually being integrated — implement its adapter against `src/providers/base.py`.
