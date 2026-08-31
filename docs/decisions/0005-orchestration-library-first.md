# ADR 0005: Orchestration — library-first, deployment deferred

## Status
Accepted

## Context
The original architecture frames Orchestration as a live service on Container Apps, fronted by API Management. But at this point in the build, Prompt Management (02), Data & Tools (07), Guardrails (06), and Observability (05) don't exist yet, and no usecase has defined what HTTP contract this component should actually expose. Building a deployable service now would mean standing up infrastructure with no real behavior behind it and no defined API surface — the same mistake already avoided with Key Vault (ADR 0001) and voice infrastructure (ADR 0003).

## Decision
Orchestration is built now as a Python library: `Pipeline`, `Step`, `State`, plus extension-point interfaces (`Tool`/`ToolRegistry`, `GuardrailCheck`) for components that don't exist yet, and a bridge (`model_client.py`) to Model Management (03). It ships with one runnable, non-usecase-specific example, tested against a fake model provider — no live Azure call, nothing deployed.

The HTTP/service wrapper (FastAPI app, Dockerfile, Container Apps bicep) is deferred until a real usecase or Serving & Hosting (component 10) defines what should actually be exposed. The deployment path this will eventually follow is documented in `platform/services/08-orchestration/README.md` now, ahead of building it, so the plan isn't lost between now and whenever it's implemented.

## Alternatives Considered
- Build the deployable service shell now (empty FastAPI app, Dockerfile, Container Apps bicep) so "the infrastructure is ready": rejected — it would be infrastructure with nothing real to run, and its actual shape (endpoints, auth, scaling) can't be meaningfully decided without a usecase or Serving & Hosting's design driving it.

## Consequences
- The engine is fully testable and demonstrable today with zero Azure deployment — a genuine, runnable proof that the platform's core mechanics work.
- When usecase code is provided later (expected), it needs to be reconciled against this engine's `Step`/`Pipeline`/`State` shape rather than assumed compatible — this is anticipated, not a surprise.
- Nothing here blocks Serving & Hosting (10) or CI/CD (09) from later defining the actual deployment; the documented plan in the README is a starting point for that work, not a commitment to its exact shape.

## Revisit When
A real usecase (or Serving & Hosting's design) defines a concrete HTTP contract this component needs to expose.
