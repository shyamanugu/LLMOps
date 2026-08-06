# Use case: APIX (contact-center call coaching)

APIX turns a recorded contact-center call into a structured **coaching report** for the
agent. It is the running example throughout the platform docs. This folder holds only
APIX-specific content; all machinery (CI/CD, evaluation gate, tracing, tools, gateway,
guardrails, model router) is inherited from `platform/` and `backend/src/llmops/`.

## Pipeline (sequential)

```
transcript -> dimension agents -> extraction -> scoring -> coaching report
```

1. **Transcript intake** — take the call transcript (by `transcript_id`) and the
   `program` (e.g. telesales, WCC). Normalise and PII-scrub.
2. **Dimension agents** — one analysis pass per coaching dimension (e.g. opening,
   discovery, objection handling, upsell, compliance, closing). Each reads the transcript
   and retrieves program rubric context via `search_knowledge`.
3. **Evidence extraction** — pull the exact quotes from the transcript that support each
   dimension's assessment (used later to force citation).
4. **Scoring** — assign a score per dimension and an overall band, grounded only in the
   extracted evidence.
5. **Coaching report** — write a short, specific coaching note that **cites the evidence**
   and does **not** invent moments not in the transcript.

The pipeline is sequential (not agent-to-agent). See `agents/pipeline.agent.yaml`.

## Data sources

- **RAG**: program rubrics / coaching guidelines in Azure AI Search (`config/datasources.yaml`).
- **Records**: call metadata via `get_record` (systems of record).
- Transcripts arrive in Blob storage; a Function can trigger a run when a new transcript
  lands, or on a nightly batch.

## Prompts

Authored as `prompts/*.prompt.yaml` (e.g. `dimension-sales.prompt.yaml`,
`coaching-report.prompt.yaml`). The coaching-report prompt requires evidence citation and
forbids invented moments (this is a real quality/guardrail requirement, mirrored in the
golden grading `must_cite_evidence` and `must_flag`). Generate drafts via
`COPILOT_PROMPTS.md`.

## Evaluation

Golden datasets are per program (`golden.telesales.jsonl`, `golden.wcc.jsonl`). Metrics:
groundedness (evidence-cited), writing quality (coaching note), tool-selection (did the
right dimension agent call `search_knowledge` for the rubric), and task success (score band
correct, required flags present). Thresholds + floors in `evals/evaluators.yaml`.

## Guardrails

Input: content safety + PII redaction on the transcript (calls contain personal data).
Output: PII redaction + schema validation on the report + content safety. PII leak rate and
unsafe rate are hard floors (0).

See `../../docs/workflows.md` for how a change flows to production, and
`../../docs/hld.md` for where this sits in the platform.
