# LLMOps Implementation Package — v2

This is the **implementation-level** version of the LLMOps package for your Azure and GitHub environment. Where the earlier walkthrough listed and compared options, v2 shows *the* setup we put in place — real repository layout, real files, real code and configuration, the exact runtime flow, and a **"today → our setup → what changes"** delta for every component. It is enterprise-grade and reusable: the same platform serves any future use case as a new subfolder, not new infrastructure.

APIX is the running example throughout. Hiring Intelligence is a second, lighter case (still being scoped). Both are **sequential agent pipelines** — one step feeds the next — not agent-to-agent systems. There are no timelines here by design.

## Doc map (`docs/`)

| # | Doc | Covers |
|---|-----|--------|
| 01 | [Overview](./docs/01-overview.md) | Implementation-first stance; the monorepo backbone; the today→ours framing |
| 02 | Repository & GitHub Actions backbone | Tree, branching, CODEOWNERS, the three workflows, OIDC, environments |
| 03 | Prompt management | YAML prompt format, registry + labels, loader code, PR + eval flow, rollback (Kiran's example) |
| 04 | Model management | `models.yaml`, resolver, deployment naming, the swap flow |
| 05 | Observability | `tracing.py` spans; what is captured per request / model / tool / agent session |
| 06 | Evaluation | Golden datasets, Ragas, DeepEval, custom tool-selection harness, the CI gate |
| 07 | Guardrails & safety | Content Safety calls, PII redaction, placement, human-in-the-loop |
| 08 | [Data & RAG pipeline](./docs/08-data-and-rag.md) | Ingest → clean/redact → chunk → embed → Azure AI Search; refresh + index aliases |
| 09 | [Serving, gateway & deployment](./docs/09-serving-and-deploy.md) | Container Apps per step, Azure Functions triggers, APIM gateway, canary/rollback |
| 10 | [Feedback & improvement](./docs/10-feedback-improvement.md) | Capture → App Insights/Langfuse → Fabric; the loop; when fine-tuning enters |
| 11 | [End-to-end & Azure hosting plan](./docs/11-end-to-end-and-hosting.md) | One wiring diagram; bill of services; shared-vs-per-use-case; consolidated delta; what we need |

Read them in order — each leads with what is different from today.

## Presentation

`presentation/LLMOps-Implementation-Walkthrough.pptx` — a fully editable deck (native shapes, no images) that follows the same component flow, but each slide shows the **concrete artifact** (the repo tree, the prompt YAML, `models.yaml`, the span code, the tool-selection harness, the Actions gate) rather than option tables. Simple English, abbreviations expanded, speaker notes on every slide.

`research-brief.md` is the source of truth all of the above follow.

## Supersedes v1

This package **supersedes the v1 approach walkthrough**, which has been removed. v1 described the approach and compared tools; v2 shows the implementation. If you are looking for the earlier `LLMOps-Approach-Walkthrough.pptx`, its content is folded into and replaced by the implementation docs and deck here.
