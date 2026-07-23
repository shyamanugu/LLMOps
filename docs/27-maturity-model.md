# GenAI Maturity Model

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §11). Any financial or ROI figures below are **ILLUSTRATIVE** pending AFNI actuals.

## 1. Purpose

Maturity is not "how many AI apps do we have" — it is "how reliably, safely, and cheaply can we produce the next one." This model gives AFNI a shared scale to assess where the organization stands, to set a target, and to plan concrete advances. It runs from **Ad-hoc** experimentation to **Self-service / Autonomous** operation, and it maps directly onto AFNI's **Crawl → Walk → Run → Fly** roadmap.

## 2. The five stages

```
 Stage 1        Stage 2          Stage 3       Stage 4       Stage 5
 Ad-hoc   ─▶  Repeatable   ─▶  Governed   ─▶  Optimized  ─▶  Self-service
             (paved road)                                   / Autonomous
   │             │                │              │               │
 pilots     golden path      controls at     cost/quality    spokes onboard
 by hand    + reuse          scale, RAI      tuned, FinOps   themselves; A2A
```

## 3. Stage detail

| Stage | Characteristics | Platform capabilities | Governance | KPIs |
|---|---|---|---|---|
| **1 — Ad-hoc** | Isolated pilots, hand-built stacks, demo-driven, no reuse; success depends on individuals | Point tools; manual prompts; no shared infra; no eval harness | Informal; ad-hoc risk review; shadow IT risk | # experiments; qualitative "does it work" |
| **2 — Repeatable (paved road)** | First golden path; use cases assemble from shared blocks; time-to-pilot in weeks | Paved-road v1; building-block catalog; declarative agents-as-code; eval harness; unified tracing | Value/risk tiering at intake; baseline guardrails; security-by-default templates | Time-to-pilot; % use cases on paved road; eval pass rate |
| **3 — Governed** | Controls hold at scale across multiple live use cases; compliance embedded; auditable | GenAIOps CI/CD; canary/rollback; model/prompt registry; Content Safety + Purview + Defender for AI wired | RAI officer active; OWASP LLM Top 10 controls; audit trails; graduated autonomy enforced | Groundedness; safety incident rate; audit coverage; SLO adherence |
| **4 — Optimized** | Cost, quality, and latency actively tuned; Model Router + FinOps drive efficiency; feedback loops mature | Model Router optimization; layered caching; PTU on critical paths; online eval (A/B, shadow); golden datasets from production | Continuous red-team; drift monitors; budget enforcement; outcome-based funding | Cost per interaction; blended quality; latency SLOs; business-outcome KPIs |
| **5 — Self-service / Autonomous** | Spokes onboard use cases themselves; agent marketplace; cross-runtime A2A ecosystem; graduated full autonomy where earned | Self-service onboarding at scale; agent registry + marketplace; A2A interop; automated evaluation & promotion | Policy-as-code guardrails; automated compliance evidence; autonomy tiers governed by measured trust | Onboarding velocity; # self-served use cases; autonomous action accuracy; portfolio ROI |

## 4. Mapping to AFNI Crawl → Walk → Run → Fly

| Roadmap phase | Maturity stage(s) | What it looks like at AFNI |
|---|---|---|
| **Foundations (Wks 0–4)** | Stage 1 → entering Stage 2 | Landing zone, security baseline, intake process; first blocks assembled |
| **Crawl (M1–3)** | Stage 2 | Platform MVP + paved-road v1; Voice Agent copilot, PI Index MVP, Hiring screening pilot; eval harness live |
| **Walk (M4–7)** | Stage 2 → Stage 3 | Autonomous voice, PI Index live, Hiring voice pre-screen; GenAIOps CI/CD, FinOps, CoE; 2 new use cases onboarded via paved road |
| **Run (M8–12)** | Stage 3 → Stage 4 | Scale across programs/geos; subrogation + knowledge assistant; full governance/DR/security hardening; router + FinOps optimization |
| **Fly (12 mo+)** | Stage 4 → Stage 5 | Self-service onboarding at scale; agent marketplace; A2A ecosystem; graduated autonomy where trust is earned |

The mapping is deliberately overlapping: a phase does not require every use case to reach the same stage. A mature portfolio typically has newer use cases at Stage 2 while flagship initiatives operate at Stage 4 — the platform holds the higher bar so newcomers inherit it.

## 5. How to assess

Assessment is evidence-based, not self-declared. For each stage, verify the artifacts exist and function:

- **Stage 2 evidence:** a documented paved road; a populated building-block catalog; at least one use case assembled from blocks with declarative YAML in Git; a running eval harness with golden datasets.
- **Stage 3 evidence:** eval-in-CI gates blocking merges; canary/rollback in production; a model/prompt registry; Content Safety + Purview + Defender for AI active; audit trails; documented OWASP LLM Top 10 controls; enforced autonomy tiers.
- **Stage 4 evidence:** Model Router with measured cost/quality outcomes; layered caching; online eval (A/B or shadow); drift and budget monitors; golden datasets refreshed from production feedback; outcome-based funding decisions.
- **Stage 5 evidence:** a spoke team onboarding a use case end-to-end without platform-team hand-building; agent registry/marketplace in use; A2A endpoints in production; autonomy granted by measured trust with automated compliance evidence.

Score each of the nine framework layers (doc 17 §2) 1–5, take the **lowest binding layer** as the effective stage — maturity is gated by the weakest control, not the flashiest capability. Reassess quarterly.

## 6. How to advance

Advancement is closing the gap between the current lowest-scoring layers and the next stage's evidence bar.

- **1 → 2:** Publish the paved road; seed the building-block catalog; stand up the eval harness and unified tracing; require intake tiering. Retire hand-built pilots onto the road.
- **2 → 3:** Wire eval-in-CI gates, canary/rollback, and the registry; activate RAI governance and the OWASP control set; enforce graduated autonomy and audit trails.
- **3 → 4:** Turn on Model Router optimization, caching, and PTU; add online eval and drift/budget monitors; close the feedback loop into golden datasets; shift funding to business outcomes.
- **4 → 5:** Enable true self-service onboarding; publish the agent marketplace; expose A2A endpoints; automate evaluation-driven promotion and compliance evidence; grant autonomy by measured trust.

## 7. Why the model matters

Maturity is the mechanism that keeps "build the factory, not the feature" honest. Each stage tightens the guarantees the platform makes to every future use case — reuse at Stage 2, control at Stage 3, efficiency at Stage 4, scale at Stage 5. Advancing the platform's maturity, not shipping one more app, is the strategy that compounds: it is what makes the 40th use case faster, safer, and cheaper than the first.
