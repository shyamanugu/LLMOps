# Multi-Agent Systems in the Ops Setup

## Why "just prompt it" stops working

A single prompt is fine for a question-and-answer task. It stops being fine the moment a task needs more than one
skill: look something up, check a policy, take an action in another system, and decide whether a human needs to
sign off. That is a multi-step process, and the practical answer is to split it into small, single-purpose agents
coordinated by an orchestrator, rather than one giant prompt trying to do everything at once. This doc covers
which framework to build on, which agent types actually get built, how the workflow control flow is chosen, and —
the part that gets skipped most often — how these agents run through the exact same Ops pipeline as everything
else (Git, CI, tracing, evals) instead of living as one-off scripts nobody can test.

## Framework choice — compared honestly

There is no single right framework for every team; the table below is what each one is actually good at.

| Framework | What it is | Strengths | When to pick it |
|---|---|---|---|
| **Microsoft Agent Framework** | Convergence of Semantic Kernel (enterprise-grade, typed, connector-rich) and AutoGen (multi-agent research runtime) into one supported stack, for .NET and Python | Durable workflows (checkpoint/pause/resume), Azure-native identity and observability, hosted on Foundry Agent Service, declarative YAML agent definitions | Default choice on an Azure-first stack; pick it when you need production durability, not just a working demo |
| **LangGraph** | Graph/state-machine framework for building agent control flow explicitly as nodes and edges | Fine-grained control over branching and cycles, large ecosystem, works with any model provider | Pick it when the workflow logic is genuinely graph-shaped (many conditional branches) and the team is already in the LangChain ecosystem |
| **CrewAI** | Role-based "crew" abstraction — agents are given roles, goals, and backstories and collaborate on a task | Fast to prototype, low ceremony, good for demoing an idea quickly | Pick it for a proof of concept or hackathon; reconsider before it carries production traffic — durability and enterprise auth are thinner |
| **OpenAI Agents SDK** | Lightweight SDK for defining agents, tools, and handoffs | Simple mental model, minimal boilerplate | Pick it for a small, provider-tied project where Azure-native hosting is not a requirement |

For an Azure-committed enterprise, Microsoft Agent Framework is the primary lane because it is the one that
plugs directly into Foundry Agent Service, Entra ID, and the same OpenTelemetry tracing already used for
everything else — an agent built there does not need a second observability story. LangGraph is a reasonable
second choice specifically for workflows with heavy conditional branching. CrewAI and OpenAI Agents SDK are fine
for getting something running this week, with the expectation that it may get rebuilt on the primary framework
before it goes to production.

## The agent types you actually build

Across real use cases, the same handful of agent roles keeps showing up. Naming them consistently matters because
it is what lets one team's "critic agent" be evaluated and reused the same way as another team's.

| Agent type | Responsibility | Example |
|---|---|---|
| **Router / intent** | Classify what the request is actually asking for and send it to the right downstream path | A chat message gets classified as "billing question" vs "technical issue" before anything else runs |
| **Planner / supervisor** | Decide which agents/steps are needed and in what order; owns the workflow pattern, not the answer | Breaks "help me dispute this charge" into: look up account, check policy, draft response, request approval |
| **Retrieval (RAG)** | Pull grounding context from the knowledge index before generation | Fetches the three most relevant policy passages for a billing question |
| **Tool / action (via MCP)** | Call out to a real system to read or write data | Updates a case status in the ticketing system through an MCP (Model Context Protocol) server |
| **Critic / evaluator** | Review another agent's draft output against a rubric before it goes further | Checks a drafted customer response for tone and policy compliance before it is sent |
| **Summarizer** | Condense a long transcript or thread into a short, structured summary | Produces the after-call summary from a full call transcript |
| **Guardrail / compliance** | Enforce policy and safety rules on inputs and outputs | Redacts an account number before it is written to a log or memory store |
| **Human-proxy / approval** | Represent the human-in-the-loop step; blocks the workflow until a person responds | Holds a refund-over-$500 workflow at a pending state until a supervisor approves |

Not every use case needs all eight. A simple FAQ bot might just be router + retrieval + guardrail. A claims
workflow might use all eight plus a second critic pass.

## Orchestration and workflow management

### The five patterns

| Pattern | Schematic | Use it when |
|---|---|---|
| **Sequential** | `A → B → C` | Each step depends on the previous one's output, fixed order |
| **Concurrent** | `A → [B, C, D] → merge` | Independent checks that can run in parallel and get combined |
| **Group chat** | `A ⇄ B ⇄ C (under a manager)` | Agents need to deliberate — debate a shortlist, negotiate a plan |
| **Handoff** | `A —hands off→ B (with context)` | Control and context transfer explicitly, e.g. bot to human |
| **Planner / Magentic** | `Planner: plan → step → replan → step ...` | The steps are not known ahead of time; the plan has to unfold as work happens |

Sequential and concurrent cover most "known process" work. Group chat and Magentic are for open-ended or
deliberative tasks where a fixed pipeline would be too rigid. Handoff is specifically the pattern for moving
control between agents or between an agent and a human mid-task, keeping full context intact.

### Durable execution

Agents fail, and some processes outlive a single request (they wait on a human for hours). Durable execution is
what makes that survivable rather than catastrophic:

- **Checkpoint** — workflow state is saved after each step, not just at the end, so a crash resumes from the last
  completed step instead of from zero.
- **Pause / resume** — a workflow can suspend (waiting on an approval) and pick back up later on the same logical
  run, potentially much later.
- **Retry** — a failed step is retried, ideally with an idempotency key so a retried action (a payment, a record
  write) does not execute twice.
- **Compensation** — if a multi-step transaction fails partway through, earlier side effects are rolled back
  deliberately rather than left in an inconsistent state.

State backing this — checkpoints, pending approvals, conversation state — lives in **Cosmos DB**, chosen for low
latency and because it doubles as the vector/state store already used for agent memory elsewhere in the stack.

### A2A for cross-team agents

**A2A (Agent-to-Agent protocol)** is the standard for agent-to-agent communication across teams or runtimes — as
opposed to MCP, which is agent-to-tool. A2A matters once more than one team is building agents independently: it
lets one team's orchestrator delegate a sub-task to another team's agent without either side needing to know how
the other one is implemented internally. Use MCP to wrap systems of record as tools; use A2A when the thing being
called is itself another team's agent.

## How agents ride the same Ops setup

This is the point that is easy to miss: multi-agent systems are not a separate discipline from the rest of
LLMOps (large language model operations). They plug into the exact same pipeline used for a single prompt.

- **Agents defined as YAML/code in Git.** An agent's instructions, tool bindings, and topology are a
  version-controlled file, not logic buried inside a service. A change to an agent is a pull request, same as a
  change to a prompt.
- **Per-agent unit evals + end-to-end scenario evals in CI.** Each specialist agent gets a small golden set testing
  it in isolation (does the router classify correctly, does the critic catch a bad response), and the whole
  workflow gets scenario-level evals (does the full claims flow reach the right outcome end to end). Both run in
  continuous integration (CI) on every change.
- **Per-hop tracing.** Every agent hop — model call, tool call, handoff to another agent — emits a trace span, so
  a failure or a bad answer can be traced back to the exact hop that caused it, not just "the workflow was wrong
  somewhere."
- **Agent registry and versioning.** Agents are registered with a version number; a deployment pins an explicit
  version, supports canary rollout, and can roll back instantly if the new version regresses.
- **Guardrails per step.** The compliance/guardrail agent type is not applied once at the end — checks run at each
  step boundary that matters (before a tool call executes, before a response reaches a user).
- **Human-in-the-loop approval nodes.** The human-proxy agent type is a first-class workflow node, not an
  afterthought bolted on — its approval or rejection is a captured, audited event in the workflow's history.

```yaml
# excerpt — billing-dispute-orchestrator.agent.yaml
name: billing-dispute-orchestrator
version: 1.4.0
pattern: sequential
model: capability:reasoning-standard   # resolved by Model Router, not a pinned model id
specialists:
  - intent-router
  - knowledge-rag
  - action-tooling        # MCP: billing system read/write
  - compliance-guardrail
  - human-proxy-approval  # blocks on refunds over policy threshold
guardrails:
  input: prompt-shield
  output: groundedness+pii
autonomy: graduated        # low-risk steps run unattended; refund action requires approval
evals:
  unit: evals/billing-dispute/unit/
  scenario: evals/billing-dispute/scenario_v3.jsonl
```

## Where this sits in the maturity plan

Level 0-1 usually means a single agent or a simple two-step chain, tested manually. Multi-agent orchestration with
Microsoft Agent Framework and a real agent registry is a Level 2 capability, arriving alongside canary deploys and
nightly full eval runs. A2A across teams, drift detection on agent behavior, and self-service agent onboarding by
other teams are Level 3 — by that point, adding a new agent to an existing workflow should be a config change and
a PR, not a rebuild.
