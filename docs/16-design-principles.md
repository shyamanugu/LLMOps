# Design Principles

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §10). Any financial or ROI figures below are **ILLUSTRATIVE** pending AFNI actuals.

These are the CTO's non-negotiables. They are not aspirational slogans; each is a design constraint that the platform enforces mechanically so that the 4th, 10th, and 40th GenAI use case inherit the same guarantees. Every principle below is stated as **what it means**, **why it matters**, and **how it is enforced** in the framework. Where a principle can be violated silently, we make it fail loudly — in CI, in the AI gateway, or in production monitors.

## 1. Platform as a product; paved roads and self-service

- **What:** The platform is an internal product with a roadmap, owners, SLAs, and consumers (the service-line spokes). Use cases travel a **paved road** — an opinionated golden path — rather than starting from a blank page.
- **Why:** One governed path collapses time-to-value from quarters to weeks and makes security, evaluation, and cost controls the default rather than an afterthought bolted on per project.
- **How enforced:** A product owner owns the paved road; onboarding is self-service via the intake portal and building-block catalog; deviating from the road requires an explicit architecture exception, so the easy path is the safe path.

## 2. Reuse over rebuild; composable building blocks

- **What:** Teams assemble use cases from a catalog of agent/workflow YAML templates, MCP tool connectors, prompt/policy libraries, guardrail packs, golden datasets, and IaC modules — not bespoke stacks.
- **Why:** Every rebuild re-introduces risk and cost. Composition amortizes the platform investment across the portfolio, so each new use case is cheaper and faster than the last.
- **How enforced:** Blocks are versioned, registered, and discoverable; PRs that hand-roll a capability already in the catalog are flagged in review; the CoE curates and deprecates blocks.

## 3. Model-agnostic and frontier-ready

- **What:** Agents bind to **capability profiles + eval bars**, not to `GPT-5.5` or any single version. The **Model Router** resolves a profile to a concrete model at request time.
- **Why:** Models are commodities that change monthly. Version lock-in creates rewrite debt and forfeits the frontier. AFNI must adopt each new frontier model without re-integration.
- **How enforced:** Application code never names a model; the router and model registry own that binding. Promoting a new model is a re-run of the eval suite, not a code change.

## 4. Evaluation-driven everything

- **What:** Nothing ships without passing evals. Prompts, agents, and workflows are gated by golden-dataset quality, groundedness, safety/red-team, and cost/latency budgets.
- **Why:** Generative output is non-deterministic; "looks good in a demo" is not evidence. Evals are the release criteria and the regression net.
- **How enforced:** Evaluation-in-CI blocks merges on regression; online eval (A/B, shadow) and auto-rollback guard production; every eval links back to the exact OpenTelemetry trace.

## 5. Deterministic guardrails around probabilistic components

- **What:** Probabilistic LLM behavior is wrapped in deterministic controls — Content Safety prompt shields, schema validators, allowlists, policy checks, approval gates.
- **Why:** You cannot rely on a model to police itself. Consequential behavior must be constrained by code whose behavior is predictable and testable.
- **How enforced:** Guardrail packs are mandatory blueprint components; input/output filtering and output-handling validation run on every consequential path and are themselves tested.

## 6. Zero Trust and least privilege; treat all model I/O as untrusted

- **What:** All model input, model output, and retrieved content are treated as untrusted. Identity is verified, tools are least-privilege, networking is private.
- **Why:** Prompt injection (direct and indirect), sensitive-information disclosure, and excessive agency (OWASP LLM01/LLM02/LLM06) are the defining threats. Untrusted content must never gain implicit authority.
- **How enforced:** Entra ID + managed identities, Key Vault, VNet/private endpoints (no public egress), strict role/instruction separation of untrusted content, scoped MCP tool permissions, Defender for AI monitoring.

## 7. Human-in-the-loop; graduated autonomy

- **What:** Consequential or irreversible actions require human approval. Autonomy is granted in graduated tiers as an agent earns measured trust.
- **Why:** Automating the wrong action at scale is a business, legal, and brand risk. Autonomy must be a dial, not a switch.
- **How enforced:** Durable workflows implement pause/resume approval gates; autonomy tier is a governed configuration tied to eval performance and risk tier, auditable per action.

## 8. Observability and cost are first-class

- **What:** Every trace, tool call, sub-agent hop, and token is captured. Quality, groundedness, latency, drift, safety, and cost are monitored continuously.
- **Why:** You cannot operate, debug, or govern what you cannot see; and token cost and latency are release-grade concerns, not billing footnotes.
- **How enforced:** Unified OpenTelemetry tracing is inherited by default; APIM meters tokens; showback, budgets, and guardrail monitors are wired at deploy time.

## 9. Privacy and data minimization by design

- **What:** Collect and expose the minimum data necessary; detect and redact PII; enforce per-tenant/per-source access on vectors and retrieval.
- **Why:** AFNI handles regulated data (PCI-DSS, HIPAA, TCPA, GDPR). Minimization shrinks the attack and compliance surface.
- **How enforced:** Purview + Content Safety PII detection/redaction, DLP, lineage and retention policies; vector partitioning per domain/tenant enforced at the knowledge layer.

## 10. Secure- and compliant-by-default templates

- **What:** The default template is already secure and compliant; teams opt into risk, never into safety.
- **Why:** Security added late is security missed. Defaults determine the real posture of the portfolio.
- **How enforced:** Landing-zone IaC, hardened blueprints, and policy-as-code ship the controls; compliance mappings (SOC 2, EU AI Act, EEOC/NYC LL144) are baked into the paved road.

## 11. Fail safe; fallbacks and graceful degradation

- **What:** When a model, tool, or dependency fails or breaches a budget, the system degrades gracefully — fallback models, cached responses, safe human handoff.
- **Why:** GenAI dependencies are probabilistic and rate/cost-limited (LLM10 Unbounded Consumption). Failure must never mean an unsafe or silently wrong outcome.
- **How enforced:** Router fallback tiers, layered caching, circuit breakers/backpressure, and explicit escalation-to-human paths are standard blueprint components.

## 12. Everything-as-code and reproducible

- **What:** Agents, prompts, workflows, guardrails, and infrastructure are declarative, version-controlled YAML/IaC artifacts.
- **Why:** Reproducibility, auditability, and rollback depend on code, not clicks. Prompts are release artifacts.
- **How enforced:** Declarative agents/workflows in Git; prompt/model registry; CI/CD with canary and auto-rollback; no manual production changes.

## 13. Grounded and cited over confident-but-wrong

- **What:** Answers are grounded in retrieved, cited enterprise knowledge; ungrounded generation on factual paths is not acceptable.
- **Why:** Misinformation (LLM09) erodes trust and creates compliance exposure. Confidence is not correctness.
- **How enforced:** RAG with citations, groundedness scoring in evals and online monitors, and abstain/escalate behavior when grounding is weak.

## 14. Measure business outcomes, not model vanity metrics

- **What:** Success is defined in AFNI business terms — containment, AHT, recruiter time, QA coverage, Gainshare margin — not token counts or leaderboard scores.
- **Why:** The platform exists to move the business. Vanity metrics can improve while outcomes stagnate.
- **How enforced:** Every use case declares outcome KPIs at intake; dashboards tie model/quality signals to business results; funding continues on outcomes, not activity.

## Principle-to-enforcement summary

| # | Principle | Primary enforcement point |
|---|---|---|
| 1 | Platform as a product | Paved road + architecture exception process |
| 2 | Reuse over rebuild | Building-block catalog + registry + PR review |
| 3 | Model-agnostic / frontier-ready | Model Router + capability profiles + eval bars |
| 4 | Evaluation-driven | Evaluation-in-CI gates + online eval + rollback |
| 5 | Deterministic guardrails | Guardrail packs + Content Safety + validators |
| 6 | Zero Trust / untrusted I/O | Entra ID, private networking, scoped MCP tools |
| 7 | Human-in-the-loop | Durable-workflow approval gates + autonomy tiers |
| 8 | Observability & cost first-class | OpenTelemetry tracing + APIM metering + FinOps |
| 9 | Privacy by design | Purview + Content Safety + vector partitioning |
| 10 | Secure/compliant by default | Landing-zone IaC + policy-as-code + hardened blueprints |
| 11 | Fail safe | Fallback tiers + caching + circuit breakers |
| 12 | Everything-as-code | Git + registries + CI/CD |
| 13 | Grounded & cited | RAG citations + groundedness monitors |
| 14 | Business outcomes | Intake KPIs + outcome dashboards |

**Summary:** These fourteen principles convert intent into constraints. Because they are enforced by the paved road, the registry, the gateway, CI, and production monitors — not by memos — they hold as the portfolio scales from three proof-point initiatives to a fleet of cooperating agents.
