# Use case: Hiring Intelligence (lighter — still being scoped)

Hiring Intelligence helps a recruiter shortlist and screen candidates against a job
description (JD) and rubric. It is deliberately **lighter** than APIX because it is still
being scoped. This folder holds only Hiring-specific content; all machinery is inherited
from `platform/` and `backend/src/llmops/`.

## Pipeline (sequential)

```
intake -> resume rank -> screening -> summary
```

1. **Intake** — take the job description + rubric and the set of candidate resumes
   (by reference). Extract text from resume files via `extract_document` if they are PDFs
   or scans; PII-scrub.
2. **Resume rank** — score/rank each candidate against the JD + rubric, grounded in the
   resume text (retrieve the rubric via `search_knowledge`).
3. **Screening** — generate structured screening notes per shortlisted candidate: strengths,
   gaps, and suggested screening questions, grounded only in the resume.
4. **Summary** — a short recruiter-facing summary of the shortlist with the ranking
   rationale.

Sequential (not agent-to-agent). See `agents/pipeline.agent.yaml`.

## Data sources

- **Documents**: resume files (PDF/scan) via Azure AI Document Intelligence.
- **RAG**: JDs / rubrics / competency frameworks in Azure AI Search.
- **Records**: candidate records via `get_record` from the applicant tracking system (ATS),
  if wired.

See `config/datasources.yaml`.

## Prompts

Authored as `prompts/*.prompt.yaml` (e.g. `resume-rank.prompt.yaml`,
`screening.prompt.yaml`, `summary.prompt.yaml`). Grounding rule: judgements must be
supported by the resume text; no invented experience. Generate drafts via
`COPILOT_PROMPTS.md`.

## Evaluation

Golden dataset(s) in `evals/`. Metrics: groundedness (claims supported by the resume),
writing quality (screening notes / summary), tool-selection (rubric retrieval, document
extraction), and task success (ranking matches SME judgement). Thresholds + floors in
`evals/evaluators.yaml`. Fairness note: keep the rubric explicit and evidence-cited to
reduce bias; PII/sensitive-attribute handling is a hard requirement.

## Guardrails

Input: content safety + PII redaction on resumes. Output: PII redaction + schema
validation + content safety. PII leak rate and unsafe rate are hard floors (0). Avoid using
protected characteristics in ranking (policy tuning, to be confirmed during scoping).
