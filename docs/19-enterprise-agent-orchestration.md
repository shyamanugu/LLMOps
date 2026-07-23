# Enterprise Multi-Agent Orchestration

> AFNI · Office of GenAI Architecture — Internal & Confidential. Reference section for the AFNI Enterprise GenAI Framework (proposal-bible §7).

## 1. Why orchestration is the load-bearing layer

Single prompts do not run a contact center. Real AFNI work — resolving a subrogation claim, containing a billing call, pre-screening a candidate — is a *multi-step process* that spans retrieval, tool calls, policy checks, and human approvals. The framework therefore treats **multi-agent orchestration** as first-class infrastructure: a supervisor routes work to narrow, testable specialist agents, and a durable runtime guarantees the process completes exactly once even across failures, restarts, and hours-long human waits.

The orchestration substrate is **Microsoft Agent Framework 1.0** (GA April 2026), the convergence of **AutoGen** (multi-agent research runtime) and **Semantic Kernel** (enterprise-grade, typed, connector-rich SDK) into one supported stack for **.NET and Python**. Agents are hosted on **Foundry Agent Service**, which supplies sandboxed sessions, managed state/filesystem, memory, and publish targets (Microsoft Teams, M365 Copilot, Voice Live).

## 2. Orchestration patterns

Agent Framework ships the pattern library the framework standardizes on. Each initiative composes these rather than inventing control flow:

| Pattern | What it does | AFNI usage |
|---|---|---|
| **Sequential** | Fixed pipeline, output → input | PI Index: transcribe → summarize → score → extract |
| **Concurrent** | Fan-out to N agents, aggregate | Sentiment + compliance + intent scored in parallel on one turn |
| **Group-chat** | Agents deliberate under a manager | Hiring panel: skills, experience, and fit agents debate a shortlist |
| **Handoff** | Explicit transfer of control + context | Voice: containment agent → escalation/human handoff |
| **Magentic** | Dynamic task decomposition + planning ledger for open-ended goals | Subrogation triage where steps are not known in advance |

The **orchestrator (supervisor)** is itself an agent whose job is routing, not answering. It selects a pattern and a specialist set per task tier, keeping each specialist small, single-purpose, and independently evaluable.

## 3. The seven specialist agents across the three initiatives

The framework defines a reusable roster of specialist roles. The same agent *contract* is reused across use cases; only tools, prompts, and evals are swapped.

| # | Specialist agent | Voice Agent | PI Index | Hiring Intelligence |
|---|---|---|---|---|
| 1 | **Intent / Router** | Classify caller intent, route flow | Tag interaction type / disposition | Parse requisition + candidate intent |
| 2 | **Knowledge / RAG** | Ground answers in policy/KB | Pull program rules for scoring | Ground on job spec + rubric |
| 3 | **Action / Tooling (MCP)** | CRM/billing actions | Write scores to lakehouse | ATS updates, schedule interview |
| 4 | **Compliance / Guardrail** | TCPA/PCI redaction, disclosures | PII scrub before storage | EEOC/LL144 fairness checks |
| 5 | **Sentiment** | Real-time caller sentiment | Emotion/effort scoring at 100% | Candidate engagement signal |
| 6 | **Escalation / Handoff** | Warm transfer to human agent | Flag at-risk interactions | Route to recruiter for review |
| 7 | **Summarization / QA & Scoring** | Post-call wrap-up + QA | Core PI scoring engine | Structured candidate scorecard |

## 4. Durable execution (the enterprise differentiator)

Probabilistic agents fail; long processes outlive a single request. Agent Framework's **durable workflows** make orchestration reliable:

- **Checkpointing** — workflow state is persisted after each step (backed by Cosmos DB), so a crashed host resumes mid-process, not from zero.
- **Pause / resume** — a workflow can suspend for minutes or days (e.g., awaiting a supervisor approval or a candidate's callback) and rehydrate on the same logical thread.
- **Retries + idempotency** — steps carry idempotency keys so a retried tool call (a payment, an ATS write) executes **exactly once**, never double-charging or double-booking.
- **Compensation / saga** — multi-system transactions register compensating actions; a failure late in the flow rolls back earlier side-effects deterministically.
- **HITL approvals** — high-risk or irreversible actions block on a typed approval gate; the human decision is captured as a first-class, audited workflow event.

```
                         ┌──────────────────────────────────────────┐
   Channel (Voice/Chat/  │        ORCHESTRATOR (supervisor)         │
   Batch/ATS)  ───────▶  │  pattern select · routing · policy       │
                         └───────┬─────────────┬────────────┬───────┘
                                 │ MCP tools   │ A2A         │
             ┌──────────┬────────┴───┬─────────┴───┬─────────┴────────┐
             ▼          ▼            ▼             ▼                  ▼
        Intent/    Knowledge/    Action/       Compliance/       Escalation
        Router      RAG          Tooling(MCP)  Guardrail          Handoff
             \          |            |             |                  /
              \         └──── Sentiment ── Summ/QA & Scoring ────────/
               \                                                    /
   ┌────────────┴────────────────────────────────────────────────┴─────────┐
   │  DURABLE RUNTIME: checkpoint · pause/resume · retry/idempotency · saga  │
   │  DETERMINISTIC GUARDRAIL SHELL  ·  per-hop OpenTelemetry tracing        │
   └────────────────────────────────────────────────────────────────────────┘
```

## 5. Memory tiers

Foundry Agent Service memory is used deliberately, not as an undifferentiated blob:

- **Session memory** — the working context of the current interaction (this call, this screening). Discarded or archived at close.
- **User memory** — durable per-customer / per-candidate facts and preferences, access-controlled per tenant.
- **Procedural memory** — learned how-to knowledge (successful tool sequences, resolution playbooks) that raises success rate over time.

Memory writes pass the Compliance/Guardrail agent so PII is redacted before persistence, and every tier is scoped by Entra ID identity to enforce least privilege.

## 6. Agent registry, versioning & agents-as-code

Agents and workflows are **declarative YAML** — instructions, tool bindings, memory policy, and topology are version-controlled artifacts, not code buried in a service. Each is registered with a semantic version in the **agent registry**; deployments pin explicit versions, support canary/blue-green rollout, and roll back to a prior version instantly. Because topology is data, the same orchestration is reproducible across dev/test/prod and auditable in git history.

```yaml
# excerpt — voice-containment-orchestrator.agent.yaml
name: voice-containment-orchestrator
version: 2.3.0
pattern: handoff
model: capability:reasoning-fast    # router-resolved, not a pinned version
specialists: [intent-router, knowledge-rag, action-tooling, compliance-guardrail,
              sentiment, escalation-handoff, summarization-qa]
guardrails: { input: prompt-shield, output: groundedness+pii }
autonomy: graduated   # HITL gate on irreversible actions
```

Note the model is bound to a **capability + eval profile**, never a raw model id — the Model Router resolves the concrete model, so new frontier models are adopted with no rewrite.

## 7. Protocol stack — MCP + A2A

- **MCP (Model Context Protocol)** — the tool layer. Every system-of-record (CRM, billing, HRIS, ATS) is wrapped as an MCP server with least-privilege scopes and a curated **Toolbox** per agent. MCP is agent→tools.
- **A2A (Agent-to-Agent v1.0, Linux Foundation)** — agent→agent across runtimes and teams. Foundry can expose any agent as an A2A endpoint, so an AFNI orchestrator can delegate to an agent owned by another team (or runtime) without shared code.

Use MCP for connectors and A2A for cross-team collaboration and the future agent marketplace.

## 8. Deterministic guardrails, graduated autonomy, tracing

The framework wraps **probabilistic agents in a deterministic shell**: input prompt shields, output groundedness/PII/policy validators, and hard schema/authorization checks around every tool call. Autonomy is **graduated** — low-risk actions run unattended; high-risk or irreversible ones require human approval (§4). Every hop — model call, tool invocation, sub-agent handoff — emits **OpenTelemetry** spans linked to evaluations, giving per-hop tracing and a full audit trail for every decision.

*ROI/performance figures elsewhere in the framework are ILLUSTRATIVE until replaced with AFNI actuals.*
