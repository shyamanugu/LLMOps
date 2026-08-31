# ADR 0013: Serving & Hosting — generic dispatch contract, not a usecase-specific API

## Status
Accepted

## Context
Orchestration's README (component 08) sketched a "Future Deployment Path" — FastAPI wrapper, Dockerfile, Container Apps, canary rollout — since ADR 0005 (library-first), on the grounds that no usecase existed yet to define what HTTP contract it should actually expose. That's still true: no usecase has specified its endpoints. But the wrapper itself, the containerization, and the Container Apps infrastructure don't need to know a usecase's specific contract to exist — only the routes a specific usecase would add do.

## Decision
1. **Build a generic dispatch contract**: `GET /healthz` and `POST /pipelines/{name}/run`, backed by a `PipelineRegistry` mapping a name to a constructed `orchestration.pipeline.Pipeline`. This is deliberately the smallest possible HTTP surface that can front *any* registered pipeline, not a guess at what a specific usecase's API should look like.
2. **Ship a reference entrypoint (`main.py`) with an empty registry**, documented as something a real usecase copies and adapts, not something deployed as-is for production traffic. Its Dockerfile builds this empty-registry image, honestly giving a working `/healthz` and a 404 everywhere else.
3. **Test with a fake `Step`, not a real `ModelStep`** — proves the dispatch mechanism (`FastAPI` → `PipelineRegistry` → `Pipeline.run` → `State`) against the real Orchestration classes, without this component's own test suite needing Model Management credentials.
4. **Container Apps Bicep uses a public placeholder image** (`mcr.microsoft.com/k8se/quickstart`) as its default `containerImage` parameter, so the template is authorable and validatable via `az bicep build` today, without a private container registry credential this access level can't create anyway.
5. **Authentication and image build/push are explicitly not built** — both require Entra ID app registration (Easy Auth / API Management for the former, ACR push credentials via CI/CD's OIDC for the latter), the same access gap already blocking CI/CD's (09) deployment job.

## Alternatives Considered
- **Waiting for a real usecase before building anything here**: rejected — unlike a usecase-specific route, the wrapper/container/infrastructure genuinely don't depend on knowing what a usecase's contract looks like. Waiting would mean this component sits at zero code indefinitely for no real reason, the same reasoning ADR 0005 used to justify building Orchestration as a library ahead of a deployed service.
- **Guessing at a plausible usecase-specific contract** (e.g., `/chat`, `/classify`) to make the wrapper feel more "real": rejected — it would be presenting an invented API as though a usecase asked for it, and would need to be redesigned the moment a real usecase's actual needs are known.
- **Deploying with a private image and Managed Identity pull access now**: rejected — requires the RBAC role assignment (`AcrPull`) already queued in Phase 0; the public placeholder image keeps the template real and validatable without that dependency.

## Consequences
- A real usecase's onboarding path for serving is: write its own `main.py`-equivalent entrypoint registering its actual pipelines, build that as the container image, point `container-app.bicep`'s `containerImage` parameter at it. No change to `app.py`, `pipeline_registry.py`, or the Bicep templates themselves.
- The deployed reference image (if someone deployed it as-is) would be publicly reachable with no authentication and no real pipelines — acceptable for validating the infrastructure shape, not something to leave running against real traffic.
- Canary rollout (`latestRevisionTrafficPercent`) is a Bicep parameter a human or a future CD job sets, not an automated progressive-rollout mechanism — no health/eval-signal-driven automation exists yet, since that also depends on CI/CD's deployment job existing.

## Revisit When
- A real usecase exists — replace `main.py`'s empty registry with that usecase's actual entrypoint, and reconsider whether the generic `/pipelines/{name}/run` contract is still the right shape once a real caller's needs are known.
- Entra ID app registration access is granted — add Easy Auth or an API Management front door in front of this service, and let CI/CD (09) build and push a real image via its now-implementable `cd.yml`.
- A real usecase and CI/CD's deployment job both exist — wire an actual canary automation (ramp traffic based on Evaluation Gate / Observability signals) instead of a human-set Bicep parameter.
