# Copilot prompts — generate APIX content

Exact prompts to run with GitHub Copilot (or `python ../../copilot_prompts.py --usecase
apix`) **inside the client environment** to produce APIX's prompts, pipeline, and evals.
The framework provides the shape; these fill the content. An SME must review golden data
and scoring bands. Pipeline: transcript -> dimension agents -> extraction -> scoring ->
coaching report.

## 0. Context to give Copilot first

> You are in an LLMOps monorepo. Shared code is in `backend/src/llmops/` and `platform/`.
> APIX lives in `usecases/apix/`. Prompts are `*.prompt.yaml` (id, version, labels,
> model_alias, temperature, inputs, template, eval_refs, changelog). The APIX pipeline is
> sequential: transcript -> dimension agents -> evidence extraction -> scoring -> coaching
> report. Model aliases: reason (complex), bulk (simple/high-volume), judge (eval). Tools:
> search_knowledge (rubric RAG), get_record (call metadata). Coaching output MUST cite
> transcript evidence and MUST NOT invent moments.

## 1. Dimension prompts (one per coaching dimension)

> Create `usecases/apix/prompts/dimension-<name>.prompt.yaml` for the "<name>" coaching
> dimension (e.g. sales, discovery, objection-handling, upsell, compliance, closing).
> Fields: id `apix.dimension_<name>`, version 1, labels [prod], model_alias reason,
> temperature 0.2, inputs [transcript, program, rubric], template that: reads the
> transcript, uses the retrieved rubric, judges this dimension, and lists the exact quotes
> it relied on. Forbid using anything not in the transcript. eval_refs to the program
> golden set. Add a changelog.

Repeat per dimension.

## 2. Evidence extraction prompt

> Create `usecases/apix/prompts/evidence-extraction.prompt.yaml`: id
> `apix.evidence_extraction`, model_alias bulk, inputs [transcript, dimension_findings].
> Template: return, per finding, the exact verbatim quotes from the transcript that support
> it, with speaker + rough timestamp if present. No paraphrasing, no invention.

## 3. Scoring prompt

> Create `usecases/apix/prompts/scoring.prompt.yaml`: id `apix.scoring`, model_alias
> reason, inputs [dimension_findings, evidence, program]. Template: assign a score per
> dimension and an overall band using ONLY the evidence; output raised flags (e.g.
> missed_upsell, compliance_disclosure_missing). Return strict JSON matching the scoring
> schema so schema_validation passes.

## 4. Coaching report prompt (canonical example)

> Create `usecases/apix/prompts/coaching-report.prompt.yaml` matching the canonical example
> in `../../5thAug/v2/research-brief.md`: id `apix.coaching_report`, version 3, labels
> [prod], model_alias reason, temperature 0.2, inputs [agent_name, program,
> dimension_scores, evidence]. Template: a contact-center coach writes a short coaching note
> for {{agent_name}} ({{program}}) using ONLY the evidence quotes, citing them, and NOT
> inventing moments. eval_refs [evals/apix/golden.telesales.jsonl]. changelog documenting
> the citation requirement.

## 5. Golden datasets (per program)

> Create `usecases/apix/evals/golden.telesales.jsonl` and `golden.wcc.jsonl`, 20-30 rows
> each. Each row: id, input {transcript_id, program}, grading {must_cite_evidence,
> expected_score_band, must_flag, must_not_include}, meta {program, source: sme_authored}.
> Model the example rows in `golden.example.jsonl`. Cover strong calls, weak calls, and
> known compliance-miss cases.

## 6. Evaluators

> Confirm `usecases/apix/evals/evaluators.yaml` enables groundedness (min 0.90),
> tool_selection_accuracy (min 0.90), task_success, writing metrics, with floors
> pii_leak_rate 0 and unsafe_rate 0. Set max_drop from the baseline run.

## 7. Baseline + PR

Run `python backend/evals/run.py --usecase apix --subset full --fail-under baseline` to
record the baseline, then open a PR — the eval gate runs automatically and blocks
regressions. SME + business review confirms scoring bands and report style.
