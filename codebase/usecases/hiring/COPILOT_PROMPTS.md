# Copilot prompts — generate Hiring Intelligence content

Exact prompts to run with GitHub Copilot (or `python ../../copilot_prompts.py --usecase
hiring`) **inside the client environment** to produce Hiring's prompts, pipeline, and
evals. This use case is lighter and still being scoped, so confirm the pipeline shape with
the business before generating. Pipeline: intake -> resume rank -> screening -> summary.

## 0. Context to give Copilot first

> You are in an LLMOps monorepo. Shared code is in `backend/src/llmops/` and `platform/`.
> Hiring Intelligence lives in `usecases/hiring/`. Prompts are `*.prompt.yaml` (id,
> version, labels, model_alias, temperature, inputs, template, eval_refs, changelog). The
> pipeline is sequential: intake -> resume rank -> screening -> summary. Model aliases:
> reason (complex), bulk (simple), judge (eval). Tools: extract_document (resume PDFs),
> search_knowledge (rubric RAG), get_record (ATS). Judgements MUST be grounded in the
> resume text; NEVER use protected characteristics in ranking.

## 1. Intake prompt

> Create `usecases/hiring/prompts/intake.prompt.yaml`: id `hiring.intake`, model_alias
> bulk, inputs [resume_files, job_id]. Template: normalise extracted resume text, PII-scrub,
> and load the job description + rubric. Output clean, structured resume text per candidate.

## 2. Resume rank prompt

> Create `usecases/hiring/prompts/resume-rank.prompt.yaml`: id `hiring.resume_rank`,
> model_alias reason, temperature 0.2, inputs [resumes_text, job_spec, rubric]. Template:
> score and rank each candidate against the JD + rubric using ONLY evidence in the resume;
> cite the evidence; produce a shortlist. Explicitly exclude protected characteristics from
> the rationale. Return strict JSON so schema_validation passes. eval_refs to the golden set.

## 3. Screening prompt

> Create `usecases/hiring/prompts/screening.prompt.yaml`: id `hiring.screening`,
> model_alias reason, inputs [shortlist, resumes_text, job_spec]. Template: per shortlisted
> candidate, list strengths, gaps vs the rubric, and 3-5 suggested screening questions —
> each grounded in the resume, no invented experience.

## 4. Summary prompt

> Create `usecases/hiring/prompts/summary.prompt.yaml`: id `hiring.summary`, model_alias
> bulk, inputs [ranking, screening_notes]. Template: a short recruiter-facing summary of
> the shortlist with the ranking rationale, evidence-cited, neutral tone.

## 5. Golden dataset

> Create `usecases/hiring/evals/golden.example.jsonl` (grow into per-role sets), 15-25
> rows. Each row: id, input {job_id, candidate_ids}, grading {expected_top_candidate or
> expected_shortlist, must_cite_evidence, must_not_include: protected characteristics,
> expected_score_band}, meta {role, source: sme_authored}. Model the starter rows already
> in that file.

## 6. Evaluators

> Confirm `usecases/hiring/evals/evaluators.yaml` enables groundedness (min 0.88),
> tool_selection_accuracy, task_success, and writing metrics, with floors pii_leak_rate 0
> and unsafe_rate 0. Set max_drop from the baseline run. Add fairness checks during scoping.

## 7. Baseline + PR

Run `python backend/evals/run.py --usecase hiring --subset full --fail-under baseline` to
record the baseline, then open a PR — the eval gate runs automatically. SME + HR review
confirms rankings and screening quality, and signs off on fairness handling.
