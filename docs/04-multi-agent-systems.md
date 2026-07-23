# Multi-Agent Systems Design

## Overview

AFNI's GenAI capability is built on a **multi-agent architecture**: a single **orchestrator/supervisor agent** decomposes each interaction and routes work to a fleet of **specialist agents**, each responsible for one well-scoped capability. This pattern is deliberately reused across all three flagship initiatives — the **Voice Agent**, the **Performance Intelligence Index (PI Index)**, and **Hiring Intelligence** — so that AFNI builds, governs, and operates *one* set of agent capabilities rather than three disconnected solutions.

The guiding principle is **deterministic guardrails around probabilistic agents**: the language models reason and generate, but their behavior is bounded by deterministic routing, policy checks, schema validation, and human-in-the-loop gates that AFNI's compliance and operations teams can inspect and trust.

## The Orchestrator / Specialist Pattern

The orchestrator is the only agent that "sees the whole conversation." It classifies intent, selects the next specialist, manages shared state, enforces turn limits, and decides when to conclude or escalate. Specialists are narrow, independently testable, and independently versioned.

```
                         +---------------------------+
        caller /         |   ORCHESTRATOR /          |
        candidate  <----> |   SUPERVISOR AGENT        |
     (voice/chat) /       |  intent · routing · state |
     interaction feed     +-------------+-------------+
                                       |
        +-------------+----------------+----------------+-------------+
        v             v                v                v             v
  +-----------+ +-----------+   +-------------+  +------------+  +-----------+
  | Intent/   | | Knowledge/|   | Action/     |  | Compliance/|  | Sentiment/|
  | Router    | | RAG agent |   | Tooling     |  | Guardrail  |  | Emotion   |
  | agent     | | (AI Search)|  | agent       |  | agent      |  | agent     |
  +-----------+ +-----------+   +------+------+  +-----+------+  +-----------+
                                       |               |
                                       v               v
                               +-------------+  +--------------+
                               | Systems of  |  | Content      |
                               | record      |  | Safety /     |
                               | CRM/HRIS/ATS|  | policy layer |
                               +-------------+  +--------------+
        +-----------------+   +--------------------------------+
        | Escalation/     |   | Summarization / QA & Scoring   |
        | Handoff agent   |   | agent (feeds PI Index)         |
        +-----------------+   +--------------------------------+
```

## Specialist Agents and Responsibilities

| Agent | Responsibility |
|---|---|
| **Intent / Router** | Classify caller/candidate intent; decide routing and next-best-action. Typically GPT-4o-mini for low-latency classification. |
| **Knowledge / RAG** | Retrieve grounded answers from AFNI policies, client KBs, and requisitions via Azure AI Search (hybrid + semantic ranker). Returns citations. |
| **Action / Tooling** | Execute transactions against systems of record (CRM, billing, HRIS/ATS) through secure, audited tool/function calls. |
| **Compliance / Guardrail** | Enforce disclosures, PII redaction, do-not-say / must-say lists, TCPA, PCI pause-and-mask, and fairness rules. Wraps other agents deterministically. |
| **Sentiment / Emotion** | Detect frustration, confusion, or escalation cues in real time to trigger tone shifts or handoff; contributes the sentiment-trajectory dimension to the PI Index. |
| **Escalation / Handoff** | Perform warm transfer to a human with full context and a running summary. |
| **Summarization / QA & Scoring** | Produce post-interaction summary, disposition coding, and automated QA scoring; emit the dimension scores that roll up into the PI Index. |

## Orchestration Patterns

The Microsoft Agent Framework (Semantic Kernel + AutoGen lineage) supports the full set of coordination patterns AFNI needs:

- **Sequential** — pipeline execution (e.g., transcribe → intent → RAG → compose reply). Used for the deterministic backbone of every turn.
- **Concurrent** — run independent specialists in parallel (e.g., Sentiment and Compliance evaluate the same utterance simultaneously) to protect latency budgets. The PI Index runs several dimension-scoring agents concurrently over each interaction.
- **Hand-off** — one agent transfers control and context to another; the basis for warm human escalation and voice-to-scheduling transitions.
- **Group-chat** — multiple agents collaborate in a shared thread under the orchestrator's moderation (useful for interview-panel scoring synthesis and PI Index score reconciliation).
- **Reflection / critic** — a critic agent reviews a draft answer for accuracy, tone, and policy adherence before it is spoken/sent. Improves groundedness on high-stakes replies and on PI Index score rationales.
- **Human-in-the-loop (HITL)** — a required approval or decision step for consequential actions. HITL is mandatory in Hiring Intelligence (**AI assists, humans decide**) and in PI Index calibration/appeals.

## Tool / Function Calling

Specialist agents act on the world through **typed tool definitions** exposed by Azure AI Agent Service. Each tool has a strict JSON schema, is fronted by Azure API Management, authenticates via Entra ID managed identity, and is fully audited. Tools include CRM lookups, payment posting (PCI-scoped), knowledge search, ATS scheduling, calendar operations, and PI Index score writes. Schema validation on both arguments and results is a deterministic guardrail: malformed or out-of-policy tool calls are rejected before they reach a system of record.

## Memory and State

| Scope | Contents | Store |
|---|---|---|
| **Short-term (working)** | Current thread, recent turns, active intent, tool results | In-thread context / Azure AI Agent Service threads |
| **Long-term (persistent)** | Conversation history, caller/candidate profile, prior dispositions, PI Index history, embeddings | **Azure Cosmos DB** (state + memory), vectors in Cosmos DB / AI Search |

Cosmos DB provides low-latency, globally distributed persistence for agent state and conversation memory, enabling continuity across a caller's multiple contacts, an agent's PI Index trend over time, or a candidate's multi-stage journey while respecting retention and PII policies enforced via Purview.

## Guardrails Around Agents

Guardrails are layered so that non-deterministic model output is always bounded by deterministic controls:

1. **Input guardrails** — Azure AI Content Safety **prompt shields** (jailbreak/injection defense), PII detection, and topic filtering before the orchestrator acts.
2. **In-loop guardrails** — the Compliance/Guardrail agent and reflection/critic pattern check every consequential output; tool-call schema validation blocks unsafe actions.
3. **Output guardrails** — groundedness detection, protected-material checks, and must-say/do-not-say enforcement before a response is delivered.
4. **Process guardrails** — turn limits, timeouts, HITL approval gates, and full audit logging.

## Frameworks

- **Azure AI Agent Service** — hosted agents, threads, built-in tool calling, and integrated Content Safety. The runtime home for production agents.
- **Semantic Kernel** — enterprise-grade orchestration, planners, and plugin/tool integration in .NET and Python.
- **AutoGen** — advanced multi-agent conversation patterns (group-chat, reflection).
- **Microsoft Agent Framework** — the converged successor unifying Semantic Kernel and AutoGen; AFNI's strategic target framework.

## One Pattern, Three Initiatives

The identical orchestrator/specialist topology serves all three flagships — only the tools, knowledge sources, and policies change. Voice Agent answers callers; PI Index scores interactions; Hiring Intelligence moves candidates.

| Element | Voice Agent (answers callers) | PI Index (scores interactions) | Hiring Intelligence (moves candidates) |
|---|---|---|---|
| Intent/Router | Caller intent (billing, care, collections) | Route interaction to scoring dimensions | Candidate intent (apply, status, FAQ) |
| Knowledge/RAG | Client policies, product KBs | Scoring rubrics, compliance criteria, prior calibrations | Job descriptions, benefits, hiring FAQs |
| Action/Tooling | CRM, billing, payment (PCI) | Write dimension scores + PI Index to Fabric store | ATS, calendar, requisition updates |
| Compliance | TCPA, PCI, HIPAA, disclosures | Fairness across agents/sites, score explainability | EEOC, NYC LL144, IL AI Video Act, GDPR |
| Sentiment | Real-time tone shift / handoff cues | Sentiment-trajectory dimension per interaction | Candidate-experience signal |
| HITL gate | Payment commitments, escalations | QA calibration and score appeals | **All hiring decisions — no autonomous rejection** |
| Summarization/QA & Scoring | Call disposition, QA scoring | Composite index + driver breakdown + coaching recs | Structured-interview scoring (assist), Candidate Fit signal |

By reusing the pattern, the Voice Agent generates the interaction data and real-time automation; the PI Index turns 100% of that interaction data into performance intelligence; and Hiring Intelligence runs its conversational screening (and optional voice pre-screen) on the same voice platform. AFNI builds the multi-agent capability once and all three initiatives — plus future use cases such as subrogation — reuse it, while each domain's guardrails stay distinct and auditable.
