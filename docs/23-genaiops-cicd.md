# GenAIOps: LLMOps CI/CD & Validation

> Internal AFNI reference. Owner: **AFNI · Office of GenAI Architecture** · Internal & confidential.
> Source of truth: `reference/proposal-bible.md` §9. Numbers marked **(ILLUSTRATIVE)** are placeholders — replace with AFNI actuals.

GenAIOps is how AFNI industrializes GenAI: the discipline that turns a promising prototype into a governed, continuously improving production capability. It is the operating core of the framework's paved road, applying the same operational rigor AFNI already brings to running contact centers. The central premise is **everything-as-code** and **evaluation-driven release**: nothing reaches production unless it passes automated quality, safety, and cost gates, and every artifact — agent, prompt, tool binding, model pin, guardrail policy, infrastructure — is versioned, reviewed, and reproducible.

Industry maturity here is low: by credible estimates only **~1% of organizations (ILLUSTRATIVE)** have reached mature, repeatable GenAI operations. AFNI's advantage is to build that maturity *by construction* into the platform, so every use case inherits it. If it is not in Git and did not pass the gates, it does not reach production.

## 1. Everything-as-code

The unit of change is a Git commit, not a console click. The framework treats these as first-class, version-controlled artifacts:

| Artifact | Format | Notes |
|---|---|---|
| **Declarative agents & workflows** | Microsoft Agent Framework YAML | Instructions, tools (MCP bindings), memory, topology, orchestration pattern (sequential / concurrent / group-chat / handoff / Magentic) |
| **Versioned prompts** | Prompt/policy template files, semver tags | All changes flow through PR review |
| **Model pins & routing policy** | Model Router config | Pin to *capabilities* + quality bars, not raw model versions — adopt new frontier models without rewrites |
| **Guardrail packs** | Content Safety config + filters | Prompt shields, groundedness, PII, least-privilege tool scopes |
| **Golden datasets & eval suites** | Versioned datasets | The regression baseline per use case |
| **Infrastructure-as-Code** | Bicep / Terraform | Foundry, AI Search, APIM, Container Apps/AKS, Key Vault, private networking |

## 2. The pipeline

```
 AUTHOR            CI (build + gates)                            DEPLOY                    OPERATE
 ┌────────┐   ┌──────────────────────────────────────────┐  ┌───────────────┐   ┌────────────────────┐
 │ Edit   │   │  Build & lint YAML/prompts/IaC           │  │ Prompt/Model  │   │ Online A/B + Shadow│
 │ agent  │──▶│  ┌────────────────────────────────────┐  │─▶│ Registry      │──▶│ Guardrail monitors │
 │ YAML/  │PR │  │ GATE 1 Unit + contract             │  │  │ (promote tag) │   │ Drift detection    │
 │ prompt │──▶│  │ GATE 2 Prompt regression vs golden │  │  └──────┬────────┘   │ Auto-rollback      │
 │ / IaC  │   │  │ GATE 3 Groundedness / faithfulness │  │         │            └─────────┬──────────┘
 └────────┘   │  │ GATE 4 Safety / red-team / CS      │  │   Canary / Blue-Green        │
              │  │ GATE 5 Cost & latency budgets      │  │   behind APIM (AI gateway)   │ feedback
              │  └────────────────────────────────────┘  │         │                    ▼
              │   All gates BLOCKING                      │   Post-deploy validation  Golden datasets
              └──────────────────────────────────────────┘         │                 (curated)
                        ▲                                           └───────────────────────┘
                        └──────────────── continuous feedback loop ────────────────────────┘
```

Author → Commit/PR → CI build → **evaluation gates** → Registry → canary/blue-green behind APIM → post-deploy validation → feedback into golden datasets.

## 3. Evaluation gates (each BLOCKING)

Every gate runs in CI (GitHub Actions / Azure DevOps) against the candidate build; failure blocks the merge/promotion. Thresholds are per-use-case and stored as code.

| # | Gate | What it checks | Method | Illustrative gate |
|---|------|----------------|--------|-------------------|
| 1 | **Unit + contract** | Deterministic behavior: tool-call schema, JSON output contracts, prompt rendering, routing logic | pytest-style unit tests; JSON-schema/contract validation | 100% pass |
| 2 | **Prompt regression** | Quality vs a frozen **golden-set baseline**; no regression on prior wins | Replay golden inputs; LLM-as-judge + rubric vs baseline run | No metric drops > 2% (ILLUSTRATIVE); no new hard failures |
| 3 | **Groundedness / faithfulness** | Answers supported by retrieved context; citations valid; no fabrication | Foundry groundedness evaluator + faithfulness rubric | Groundedness ≥ 0.90 (ILLUSTRATIVE) |
| 4 | **Safety / red-team / Content Safety** | Jailbreak/injection resistance, harmful content, PII leakage, protected material | Adversarial red-team suite + Azure AI Content Safety (prompt shields, PII) | 0 critical; ≥ 98% attack-block (ILLUSTRATIVE) |
| 5 | **Cost & latency budgets** | Token cost/interaction and p95 latency within budget | Measured on eval run; Model Router cost accounting | p95 ≤ budget; cost/txn ≤ budget (ILLUSTRATIVE) |

**Gate 1 — Unit & contract.** The deterministic skeleton around a probabilistic core: does the agent emit well-formed tool calls, honor output schemas, and route correctly? Fast, cheap, run on every commit.

**Gate 2 — Prompt regression.** The golden set is a curated, versioned collection of representative inputs with known-good expectations. The candidate is replayed and scored (LLM-as-judge + rubric) against the baseline run, so a prompt tweak that fixes case A cannot silently break case B.

**Gate 3 — Groundedness / faithfulness.** For RAG and knowledge patterns, we verify every claim traces to retrieved evidence and that citations resolve. This is the primary defense against confident-but-wrong output (OWASP LLM09 Misinformation).

**Gate 4 — Safety / red-team.** An adversarial corpus (direct + indirect prompt injection, data-exfiltration attempts, jailbreaks) plus Content Safety scanning. Blocking because safety is not negotiable.

**Gate 5 — Cost & latency budgets.** Uniquely GenAI: token cost and latency are *release criteria*, not afterthoughts. A change that doubles tokens or blows the sub-second voice budget fails here.

## 4. Registry, canary & post-deploy validation

Passing builds are promoted to a **prompt/model registry** with an immutable version tag, provenance, and the attached eval report. Deployment is **canary / blue-green behind Azure API Management** (the AI gateway): the new version takes a small traffic slice while the stable version serves the rest. **Post-deploy validation** runs continuously:

- **Online A/B & shadow** — compare candidate vs incumbent on live or mirrored traffic without user impact.
- **Guardrail monitors** — real-time groundedness, safety, and PII checks on production traffic.
- **Drift detection** — input-distribution and quality drift vs the eval baseline.
- **Auto-rollback** — breach of a guardrail or SLO threshold reverts APIM routing to the last-good version automatically.

## 5. Feedback into golden datasets

The loop closes: production signals — thumbs up/down, QA scores, escalations, incidents, and PI Index analytics — are triaged, and the most informative cases (especially failures and edge cases) are curated back into the **golden datasets**. Each new use case therefore makes the eval harness stronger, and the next release is measured against a richer bar.

## 6. LLMOps vs MLOps vs DevOps

| Dimension | DevOps | MLOps | **LLMOps / GenAIOps** |
|-----------|--------|-------|------------------------|
| Primary artifact | Code | Code + trained model + data | Code + **prompts** + agent YAML + model pins + guardrails |
| Determinism | Deterministic | Statistical, reproducible given seed/data | **Non-deterministic** generative output |
| Testing | Unit/integration | Data/model validation, metrics | Unit **+ eval-in-CI** (LLM-as-judge, groundedness, red-team) |
| Release criteria | Tests pass | Model metrics (AUC/F1) | Eval gates **+ token cost + latency + safety** |
| Failure modes | Crashes, regressions | Drift, skew | Hallucination, prompt injection, excessive agency, PII leak |
| Build input | Compile | Train | Author/compose (often no training) |
| Monitoring | Uptime, errors | Data/model drift | Quality, groundedness, drift, **safety, cost per token** |

GenAIOps inherits DevOps automation and MLOps evaluation rigor, then adds prompts-as-artifacts, evaluation of generative output, novel adversarial failure modes, and token cost/latency as first-class release criteria — the combination that makes the paved road safe to scale.
