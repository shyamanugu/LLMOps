# LLMOps Approach Package — 5th Aug

Working draft for review. This package defines **how we approach LLMOps**, grounded in two live use cases —
**APIX (Afni Performance Intelligence Index)** and **Hiring Intelligence** — and written to apply to any future
use case. It focuses on **approach, activities, observability and evaluation**. **Timelines are intentionally
deferred** at this stage (the only "weeks" references are APIX's own 4-week trend feature).

Both use cases are **sequential agent pipelines** (one step feeds the next), not agent-to-agent systems — the
approach reflects that throughout.

## What to send / present
- **`document/LLMOps-Approach.docx`** — the sendable document consolidating the approach (sections 1–8: approach,
  the two pipelines, as-is/to-be, activities, observability, evaluation, infrastructure, what we need to proceed).
- **`presentation/LLMOps-Approach-Walkthrough.pptx`** — a fully editable (native shapes, no images) 16-slide deck
  to walk through, weighted toward observability and evaluation. Speaker notes on every slide.

## Detailed reference (`docs/`)
| # | Doc | Covers |
|---|-----|--------|
| 01 | [Approach & Activities](./docs/01-approach-and-activities.md) | The approach and the nine workstreams (A–I), sequenced, no dates |
| 02 | [Current State vs Target State](./docs/02-current-state-to-be.md) | As-is (as a discovery checklist) vs to-be, per area |
| 03 | [Use Cases as Pipelines](./docs/03-usecases-as-pipelines.md) | APIX and Hiring as sequential pipelines; metric coverage |
| 04 | [Observability Deep-Dive](./docs/04-observability-deep-dive.md) | Trace tree; what's captured per request / model / tool / session |
| 05 | [Evaluation Deep-Dive](./docs/05-evaluation-deep-dive.md) | Metric groups, tool-selection evaluation, tooling, run modes, golden datasets |
| 06 | [Infrastructure & Hosting](./docs/06-infrastructure-hosting.md) | Hosting comparison, bill of services, environments (no dates) |

`research-brief.md` is the source of truth that all of the above follow.

## The client asks this responds to
1. How we approach LLMOps. 2. The activities involved (no timelines). 3. What exists vs what changes.
4. Observability & evaluation in detail — what's tracked per request, model call, tool call, and agent session.
5. Infrastructure setup (Azure services + hosting), no timelines.

## Regenerating
```bash
pip install python-pptx python-docx
python scripts/generate_deck.py    # -> presentation/LLMOps-Approach-Walkthrough.pptx
python scripts/generate_doc.py     # -> document/LLMOps-Approach.docx
```
