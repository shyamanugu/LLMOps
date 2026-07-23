# Afni Business Context & Opportunity

## Who Afni Is

Afni, Inc. is a global Business Process Outsourcing (BPO) and customer-engagement provider. *(Public-source facts:)* Founded in 1936 and headquartered in Bloomington, Illinois, Afni operates with approximately 3,400+ employees across a distributed delivery footprint. The company serves clients in insurance, financial services, telecom, healthcare, fitness, and media, and delivers work under a partnership-oriented commercial model that includes **Gainshare** arrangements tied to measurable outcomes.

*(Assumption, to be confirmed in discovery:)* Afni's scale, multi-site model, and outcome-based contracts imply a large, repetitive interaction volume and a continuous, high-volume internal hiring pipeline — both of which are natural fits for the two flagship GenAI use cases proposed here.

## Service Lines

Afni's core service lines span the customer lifecycle:

| Service Line | Description | GenAI Relevance |
|---|---|---|
| **Acquisition & Growth** | Sales, upsell, and customer acquisition | Agent-assist next-best-offer; lead qualification |
| **Care & Retention** | Customer service, support, retention | Voice AI containment, copilot, churn-save assist |
| **Collections** | Receivables and payment recovery | Payment-reminder voice agent, promise-to-pay assist |
| **P&C Insurance (incl. subrogation)** | Claims support, subrogation recovery | Document-heavy RAG, subrogation packet automation |
| **Gainshare model** | Outcome-based commercial partnership | Directly monetizes AI-driven productivity gains |

## Locations & Scale

*(Public-source facts:)* Afni operates sites across the United States (Illinois, Arizona, Kentucky, Texas, Missouri, Alabama), Mexico, and the Philippines, complemented by an **Afni@Home** remote-workforce program. This blended onshore/nearshore/offshore/remote model gives Afni flexibility in labor sourcing but also concentrates the industry's structural cost and attrition pressures across many geographies and time zones — a distribution that a cloud-native, centrally governed AI platform is well suited to serve.

## Strategic Pressures on BPOs

The BPO industry faces converging pressures that make a GenAI capability strategically urgent rather than optional:

- **Margin compression.** Clients demand lower per-interaction and per-transaction costs while expecting higher quality, squeezing already-thin BPO margins.
- **Labor cost inflation.** Wage growth across delivery geographies erodes the labor-arbitrage advantage that historically underpinned BPO economics.
- **Attrition.** Frontline agent attrition remains high, driving persistent recruiting, onboarding, and ramp costs — a direct link between the two flagship use cases.
- **AI disruption of the industry.** Generative AI can automate containable interactions outright, threatening seat-based revenue for firms that fail to adapt — and rewarding those that reposition around AI-augmented outcomes.
- **Gainshare alignment.** *(Assumption:)* Afni's outcome-based model turns this disruption into upside: productivity gains from AI can be shared with clients, deepening partnerships rather than cannibalizing revenue.

## The GenAI Opportunity Map

The following candidate use cases are grounded in Afni's service lines and the multi-agent pattern defined in the proposal bible. Impact and effort are directional estimates *(assumptions)* to be validated in discovery.

| # | Candidate Use Case | Service Line | Impact | Effort | Notes |
|---|---|---|---|---|---|
| 1 | Agent-assist copilot (real-time) | Care & Retention | High | Medium | Flagship; low autonomy risk, fast value |
| 2 | Autonomous voice agent (containable calls) | Care, Collections | High | High | Flagship; latency + compliance critical |
| 3 | 100% post-call QA & analytics | All voice | High | Medium | Replaces sampled QA; coaching insights |
| 4 | AI-driven HR recruitment | Internal (HR) | High | Medium | Flagship; fairness/LL144 governance |
| 5 | Payment-reminder / promise-to-pay agent | Collections | Medium | High | TCPA + PCI sensitive |
| 6 | Subrogation packet automation | P&C Insurance | Medium | High | Document-intensive RAG; Phase 3 |
| 7 | Knowledge-base concierge (internal) | All | Medium | Low | RAG over policies/procedures |
| 8 | Next-best-offer assist | Acquisition & Growth | Medium | Medium | Upsell guidance for reps |
| 9 | Retention / churn-save assist | Care & Retention | Medium | Medium | Sentiment-driven interventions |
| 10 | Automated disposition & summarization | All voice | Medium | Low | After-call work reduction |

**Prioritization logic:** the flagship pilots (rows 1, 3, 4) are deliberately high-impact / lower-autonomy-risk and quick to value, establishing the platform and trust before higher-autonomy or more heavily regulated use cases (rows 2, 5, 6) are scaled in later phases.

## The Specific GenAI Opportunity

Afni sits at the intersection of two reinforcing opportunities. On the **delivery side**, Voice AI can lower AHT, contain eligible calls, and lift QA coverage across Care, Collections, and Insurance programs — value that flows to clients and, via Gainshare, back to Afni. On the **internal-operations side**, high-volume recruitment is both a major cost center and the primary lever against attrition; an AI-driven, fairness-governed hiring pipeline shortens time-to-fill and reduces cost-per-hire while improving candidate experience.

Crucially, both opportunities reuse the *same* multi-agent orchestration pattern and the *same* governed platform. This shared foundation is what converts individual point solutions into a compounding, enterprise-wide capability — and it is the central rationale for the platform-first approach detailed in the sections that follow. *(All quantified benefits appear as illustrative ranges in the Business Case and are to be replaced with Afni actuals during discovery.)*
