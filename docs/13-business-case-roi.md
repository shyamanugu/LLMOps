# Business Case & ROI

> **IMPORTANT — ALL FINANCIAL FIGURES IN THIS DOCUMENT ARE ILLUSTRATIVE PLACEHOLDERS.** They demonstrate the shape and mechanics of the business case only. Every number must be replaced with AFNI actuals (interaction volumes, fully-loaded agent costs, QA/coaching costs, hiring volumes, recruiter costs, and program economics) during discovery. Do not treat any figure here as a commitment or estimate of actual return.

## How to Read This Business Case

The value of the LLMOps platform comes from **three flagship initiatives sharing one governed foundation**. Because the platform, multi-agent pattern, and LLMOps lifecycle are reused, each incremental initiative carries lower marginal cost — so the business case improves as adoption scales. Under AFNI's **Gainshare** model, a meaningful portion of delivery-side savings can be shared with clients, reinforcing partnerships rather than eroding revenue.

## Value Levers

### Performance Intelligence Index (PI Index)

| Lever | Mechanism | Illustrative Range* |
|---|---|---|
| QA coverage | Automated scoring of every interaction replaces sampled review | 5–10% → **100%** |
| Coaching velocity | Driver breakdowns + targeted recommendations speed coaching | Faster, more consistent coaching cycles |
| Attrition reduction | Earlier risk detection + fairer, more consistent feedback | Modest reduction in frontline attrition |
| QA labor efficiency | Manual QA effort redirected to calibration/appeals | Redeployed QA capacity |
| Gainshare reporting | Objective, explainable performance evidence per client | Stronger outcome reporting |

### Voice Agent

| Lever | Mechanism | Illustrative Range* |
|---|---|---|
| AHT reduction | Copilot surfaces answers, next-best-action, auto-summary | 15–25% |
| Call containment / deflection | Autonomous agent handles eligible call types with warm handoff | 20–40% of eligible calls |
| Agent ramp time | Copilot shortens time-to-proficiency | 20–40% faster ramp |
| Compliance adherence | Real-time disclosure/PII nudges (TCPA/PCI) | Fewer violations, lower rework |
| Collections uplift | Promise-to-pay and payment-reminder assist | Higher promise-to-pay rate |

### Hiring Intelligence

| Lever | Mechanism | Illustrative Range* |
|---|---|---|
| Recruiter time savings | Automated JD, sourcing, screening, scheduling | 30–50% of screening effort |
| Time-to-fill reduction | Faster funnel throughput | 20–35% shorter |
| Cost-per-hire reduction | Fewer manual touches per hire | 15–30% lower |
| 90-day attrition | Better structured screening/matching + Candidate Fit signal | Modest reduction |
| Candidate experience | Conversational screening + faster scheduling | Higher candidate NPS |

*\*Illustrative ranges per proposal bible; replace with AFNI actuals.*

## Illustrative Cost-Benefit Model

The table below is a **hypothetical** annualized model at steady state (post Phase 2). Figures are placeholders scaled to a mid-size multi-program deployment.

| Category | Item | Illustrative Annual Range (USD)* |
|---|---|---|
| **Investment** | Azure platform & consumption (models, AI Search, compute, gateway) | $0.6M – $1.2M |
| | Implementation & integration (Year 1) | $1.0M – $2.0M |
| | Run / CoE, LLMOps, and governance (ongoing) | $0.8M – $1.5M |
| | **Total illustrative annual investment** | **$2.4M – $4.7M** |
| **Benefit** | Voice Agent — AHT + containment + ramp value | $2.5M – $6.0M |
| | PI Index — QA labor + coaching + attrition value | $0.8M – $2.0M |
| | Hiring Intelligence — recruiter time + faster fill + cost-per-hire | $1.0M – $2.5M |
| | Compliance/QA risk reduction & rework avoidance | $0.3M – $0.8M |
| | **Total illustrative annual benefit** | **$4.6M – $11.3M** |
| **Net** | **Illustrative annual net benefit** | **$2.2M – $6.6M** |

*\*Purely illustrative. Ranges, not point estimates. To be replaced with AFNI actuals in discovery.*

## Payback Period

Combining a Year-1 implementation and platform build with steady-state annual benefits, the **illustrative payback period is approximately 9–15 months**, consistent with the proposal bible. Payback is front-loaded by the agent-assist copilot, the PI Index offline-scoring MVP, and the Hiring Intelligence screening pilot (lower autonomy risk, faster value) and improves further as the autonomous Voice Agent and additional use cases scale in Phases 2–3.

## Sensitivity Notes

The model is most sensitive to a small number of drivers:

- **Interaction volume and fully-loaded agent cost** dominate Voice Agent benefit; small changes in eligible-call volume move the result significantly.
- **Containment rate realism** — benefits should be modeled conservatively; only genuinely containable call types count, and human handoff paths must remain funded.
- **QA and coaching economics** drive PI Index benefit; the value of moving from sampled to 100% coverage depends on current QA staffing and attrition costs.
- **Azure consumption cost** scales with token/minute usage; disciplined FinOps (caching, model right-sizing with GPT-4o-mini where adequate, quotas via API Management) materially protects margin.
- **Hiring volume** drives Hiring Intelligence benefit; seasonality and program ramps should be reflected.
- **Adoption ramp** — benefits lag deployment; a realistic 3–6 month adoption curve should be applied rather than assuming day-one steady state.

A conservative (low-range benefit, high-range investment) scenario should still be modeled to confirm the case holds under pessimistic assumptions before commitment.

## Non-Financial Benefits

Several benefits are strategic and difficult to monetize directly but material to the decision:

- **Competitive positioning** as an AI-forward BPO, strengthening client retention and new-logo win rates.
- **Gainshare upside** — quantified productivity gains and objective PI Index evidence become a shared-value narrative with clients.
- **Compliance and auditability** — consistent TCPA/PCI/HIPAA guardrails and 100% PI Index QA coverage reduce regulatory and reputational risk.
- **Employee experience** — copilots reduce cognitive load and after-call work; fairer, more consistent PI Index coaching supports retention against industry-high attrition.
- **Organizational capability** — a governed platform and CoE create reusable AI muscle for future use cases at low marginal cost.
- **Candidate experience and fairness** — faster, more consistent, bias-audited hiring improves AFNI's employer brand.

## Gainshare Note

Because AFNI delivers under **Gainshare** arrangements tied to measurable outcomes, delivery-side gains from the Voice Agent and PI Index are not purely internal savings — a defined share can be passed to clients as demonstrable performance improvement. This reframes AI investment from a cost-cutting exercise into a partnership-deepening, revenue-protecting lever. The precise split, measurement baselines, and attribution methodology are contractual and must be modeled per client during discovery.

## Recommendation

Even under conservative, clearly hypothetical assumptions, the combined three initiatives plausibly return well above the platform investment within roughly one year, with strong non-financial upside. The Office of GenAI Architecture recommends approving the Phase 0 discovery to replace these illustrative figures with validated AFNI actuals and to finalize a committed business case ahead of the Phase 1 pilots.
