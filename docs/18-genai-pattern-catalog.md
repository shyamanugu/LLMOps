# GenAI Pattern Catalog (Beyond Chatbots)

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §5). Any financial or ROI figures below are **ILLUSTRATIVE** pending AFNI actuals.

GenAI at AFNI is far broader than chatbots. This catalog defines ten **reusable paved-road patterns** — each a blueprint of reference architecture + eval suite + guardrail pack + IaC. A use case selects one or more patterns during onboarding (doc 17, step 3) and composes them from the building-block catalog. For each pattern below: **what it is**, **AFNI applications** across the four service lines (Collections; P&C / subrogation; Care & Retention; Acquisition & Growth), **reusable blueprint components**, and **KPIs**.

## 1. Conversational assistant / copilot (chat & voice)

- **What:** An assistant that converses with a user or customer, grounded in enterprise knowledge, with tool access.
- **AFNI applications:** Care self-service and agent-assist; Collections payment negotiation copilot; Acquisition product Q&A; P&C claimant status.
- **Blueprint components:** Intent/Router agent, Knowledge/RAG agent, MCP tools, guardrail pack, session memory, Content Safety.
- **KPIs:** Containment %, AHT, CSAT, first-contact resolution, escalation rate.

## 2. Autonomous / agentic workflow

- **What:** Multi-step, tool-using, durable workflow where an orchestrator decomposes a task across specialist agents with checkpointing and human approval.
- **AFNI applications:** Subrogation triage (P&C); Collections dispute resolution; Hiring screening orchestration; Care case resolution.
- **Blueprint components:** Agent Framework orchestration (handoff/Magentic), durable workflows, MCP tools, A2A interop, approval gates, agent registry.
- **KPIs:** Straight-through processing %, cycle time, human-touch rate, action accuracy, rework rate.

## 3. Retrieval-augmented generation (RAG)

- **What:** Grounded generation over enterprise knowledge with hybrid + semantic retrieval and citations.
- **AFNI applications:** Policy/procedure assistant across all lines; P&C coverage lookup; Care knowledge base; Collections compliance guidance.
- **Blueprint components:** AI Search (hybrid + semantic ranker), integrated vectorization, RAG ingestion template, per-tenant vector partitioning, citation enforcement.
- **KPIs:** Groundedness score, citation coverage, answer accuracy, deflection rate, retrieval latency.

## 4. Document intelligence

- **What:** Extraction, classification, and validation of forms, claims, contracts, and correspondence.
- **AFNI applications:** P&C claims/subrogation packet parsing; Hiring resume/credential extraction; Collections dispute documents; Care intake forms.
- **Blueprint components:** AI Document Intelligence, structured-extraction agent, schema validators, PII redaction, human-in-the-loop review.
- **KPIs:** Extraction accuracy/F1, field-level precision/recall, manual-review rate, straight-through %, turnaround time.

## 5. Batch summarization & analytics

- **What:** Large-scale, offline analysis of interactions — 100% coverage rather than sampled QA.
- **AFNI applications:** **PI Index** (100% call/QA analytics); Care sentiment trends; Collections compliance sweeps; Acquisition win/loss analysis.
- **Blueprint components:** Batch pipeline (Fabric/OneLake), distilled/open-weight models, Model Router, summarization/QA & scoring agent, dashboards.
- **KPIs:** Coverage % (target 100%), cost per interaction, QA score reliability, insight-to-action lead time, agreement vs human QA.

## 6. Structured data extraction & entity resolution

- **What:** Turning unstructured text/audio into validated structured records and resolved entities.
- **AFNI applications:** Disposition/outcome extraction from calls; P&C party/policy resolution; Collections promise-to-pay capture; Hiring skills tagging.
- **Blueprint components:** Extraction agent with output schema, validators, entity-resolution logic, golden datasets, Content Safety PII checks.
- **KPIs:** Schema-valid %, extraction accuracy, entity match precision, downstream data-quality score.

## 7. Multimodal

- **What:** Reasoning across audio, image/scan, and document + voice together.
- **AFNI applications:** Voice + document co-analysis in P&C; scanned-form + call context in Care; ID/credential image checks in Hiring.
- **Blueprint components:** gpt-audio-1.5 / realtime path, Document Intelligence, multimodal orchestration, guardrail pack.
- **KPIs:** Cross-modal accuracy, task completion rate, review rate, latency per modality.

## 8. Decision support & forecasting

- **What:** Next-best-action, propensity, and scenario analysis combining LLM reasoning with analytics.
- **AFNI applications:** Collections next-best-action and treatment strategy; Care churn/retention propensity; Acquisition lead prioritization; P&C recovery likelihood.
- **Blueprint components:** LLM + analytics models, feature pipelines (Fabric), decision-support agent, human approval for consequential actions.
- **KPIs:** Recommendation adoption %, lift vs baseline, recovery/retention rate, forecast error (MAPE).

## 9. Code & developer assist

- **What:** Internal engineering acceleration — tooling, test generation, migration.
- **AFNI applications:** Platform team velocity; MCP connector scaffolding; eval-suite generation; legacy integration migration.
- **Blueprint components:** Coding agents, repo-scoped MCP tools, eval-in-CI, guardrails on generated code.
- **KPIs:** Developer cycle time, PR throughput, test coverage delta, defect escape rate.

## 10. Real-time voice

- **What:** Sub-second speech-to-speech agents and live agent-assist.
- **AFNI applications:** **Voice Agent** across Care and Collections; Hiring voice pre-screen; live agent-assist whisper.
- **Blueprint components:** Voice Live path, gpt-realtime-1.5, CCaaS + ACS integration, latency budgets, escalation/handoff agent, TCPA guardrails.
- **KPIs:** Turn latency (sub-second), containment %, AHT, transfer rate, CSAT.

## Pattern → AFNI use-case map

| Pattern | Collections | P&C / Subrogation | Care & Retention | Acquisition & Growth |
|---|---|---|---|---|
| 1 Copilot | Payment negotiation | Claimant status | Self-service + assist | Product Q&A |
| 2 Agentic workflow | Dispute resolution | Subrogation triage | Case resolution | Lead qualification |
| 3 RAG | Compliance guidance | Coverage lookup | Knowledge base | Offer/eligibility Q&A |
| 4 Document intelligence | Dispute docs | Claims packet parsing | Intake forms | Application docs |
| 5 Batch analytics | Compliance sweeps | Recovery analytics | Sentiment trends | Win/loss analysis |
| 6 Structured extraction | Promise-to-pay | Party/policy resolution | Disposition capture | Lead enrichment |
| 7 Multimodal | Doc + call | Scan + voice | Form + call | ID checks |
| 8 Decision support | Next-best-action | Recovery likelihood | Churn propensity | Lead prioritization |
| 9 Code assist | Platform engineering (cross-cutting) | | | |
| 10 Real-time voice | Voice collections | Claimant IVR-plus | Voice self-service | Voice pre-qualification |

## The three initiatives mapped to patterns

| Initiative | Primary patterns | Secondary patterns |
|---|---|---|
| **Voice Agent** | 10 Real-time voice, 1 Copilot | 2 Agentic workflow |
| **Performance Intelligence Index** | 5 Batch summarization & analytics | 6 Structured extraction |
| **Hiring Intelligence** | 2 Agentic workflow | 3 RAG, 4 Document intelligence |

Because each initiative is expressed as a composition of catalog patterns rather than a bespoke build, the reference architectures, eval suites, and guardrail packs they exercise become reusable assets. The fourth use case selects from the same shelf — turning "beyond chatbots" from a slogan into an operational library.
