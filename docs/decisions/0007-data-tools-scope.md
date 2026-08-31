# ADR 0007: Data & Tools — per-client index isolation, STT/TTS ownership, generic connector pattern

## Status
Accepted

## Context
Three separate things needed a home in this component: retrieval for RAG-style usecases, the STT/TTS voice pipeline that ADR 0003 explicitly deferred here, and a way for usecases to call internal systems (ticketing, CRM) without every usecase writing its own HTTP plumbing.

Retrieval carries a hard constraint specific to AFNI as a multi-client BPO: one client's data must never be reachable from another client's request, and that guarantee needs to be enforced in code, not left to per-usecase discipline. Two isolation models were on the table — a shared Search index with a `client_id` filter applied per query, or a separate index per client. The filter approach is cheaper to operate (one index) but the guarantee only holds as long as every query path remembers to apply the filter; a missed filter is a silent cross-client data leak, not a loud failure.

## Decision
1. **One shared Azure AI Search service, one index per client.** `RetrievalTool` only ever accepts a `client_id`; it resolves that to an index name via `client_index_registry.py` reading `config/clients.yaml`, and there is no parameter or code path that accepts a raw index name. A missing or wrong config entry fails loudly (`UnknownClientError`) rather than silently returning the wrong client's data. Isolation is structural — a query literally cannot reach another client's index — not filter discipline that has to be remembered on every call site.
2. **Onboarding a new client is a config entry plus running `scripts/provision_client_index.py`**, not a code change — the same reusability shape Model Management and Prompt Management already established for their own resources.
3. **STT/TTS pipeline tools** (`SpeechToTextTool`, `TextToSpeechTool`) live here per ADR 0003, wrapping Azure AI Speech. They are independent of the Realtime API voice alias in Model Management (03) — a usecase picks whichever architecture fits, both are available.
4. **A generic, config-driven `HttpApiTool`** is the reusable mechanism for calling internal systems. No AFNI-specific connector (a real ticketing or CRM integration) is built here — that is usecase-owned integration logic that happens to use this mechanism.
5. **`AzureSpeechBackend` lazily imports `azure-cognitiveservices-speech` inside `__init__`**, not at module level, so importing this package doesn't force that (optional, heavier) dependency on a usecase that only needs retrieval or the HTTP connector.

## Alternatives Considered
- **Shared index + `client_id` filter**: rejected as the default — the isolation guarantee would depend on every query path remembering to apply the filter correctly, and a missed filter fails silently (wrong results) rather than loudly (an error). Per-client index makes the failure mode "client not onboarded yet" instead of "data leaked."
- **Per-client Search service** (not just per-client index): rejected — Azure AI Search's Basic tier is a fixed cost regardless of index count, so a new service per client multiplies fixed cost for no isolation benefit over a new index; reserved as an escape hatch only for a client whose contract demands physical resource separation, not the default.
- **Building real AFNI system connectors (ticketing, CRM) now**: rejected — no concrete system integration has been specified yet, and guessing at one risks building the wrong shape; `HttpApiTool` covers the general case, specific connectors arrive with the usecase that actually needs them.

## Consequences
- A new client's onboarding cost, in engineering terms, is one config line plus one script run — no platform code changes, mirroring the acceptance test this whole platform is being built to satisfy.
- Index count scales with client count on one shared Search service; 🌐 the per-service index limit (tier-dependent) becomes an external capacity concern to watch as AFNI's client roster grows, not a permission gap.
- No ingestion pipeline exists yet (chunking, scheduled re-indexing) — `upsert` is available on the backend, but a usecase currently drives ingestion manually. This is a real gap, not a design decision; flagged for whichever component (or this one, later) ends up owning ingestion orchestration.
- `AzureSearchBackend` and `AzureSpeechBackend` are authored against the SDK shapes available at time of writing (azure-search-documents 12.x's `VectorizedQuery`) and are not exercised by the automated test suite — same posture already established for `AzureOpenAIProvider` in Model Management.

## Revisit When
- A client's contract demands physical resource separation beyond index-level isolation — provision a dedicated Search service for that client as an override, not a platform-wide default.
- Client count approaches the per-service index limit for the current Search tier — either upgrade the tier or reconsider the isolation model.
- A real ingestion pipeline (chunking, scheduling, re-embedding on document change) is needed — design it as its own concern rather than folding it into `RetrievalTool`.
- A usecase needs a real AFNI system connector — build it using `HttpApiTool` as the base, or a new `Tool` implementation if the system's shape doesn't fit an HTTP request/response model.
