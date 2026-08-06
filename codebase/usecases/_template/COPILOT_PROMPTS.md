# Copilot prompts — generate this use case's content

These are the exact prompts to run with GitHub Copilot (or `python
../../copilot_prompts.py --usecase <name>`) **inside the client environment** to produce
this use case's prompts, pipeline, and evals. The framework provides the *shape*; these
prompts fill the *content*. Always have an SME review the output — especially golden data
and thresholds.

Replace `<name>`, `<domain>`, and the bracketed specifics before running.

## 0. Context to give Copilot first

> You are working in an LLMOps monorepo. Shared platform code is in
> `backend/src/llmops/` and `platform/`. This use case lives in `usecases/<name>/`.
> Prompts are `*.prompt.yaml` files with fields: id, version, labels, model_alias,
> temperature, inputs, template, eval_refs, changelog. The pipeline is sequential (not
> agent-to-agent) and defined in `agents/pipeline.agent.yaml`. Model aliases are reason,
> bulk, judge, voice, embed (resolved via platform/models.yaml). Reusable tools are
> search_knowledge, query_sql, extract_document, get_record. Follow these conventions
> exactly.

## 1. Data sources

> Fill `usecases/<name>/config/datasources.yaml` for a <domain> use case. We have
> [describe: unstructured docs / a SQL warehouse / PDF files / a CRM]. Enable only the
> sources we actually use; keep SQL read-only and allow-listed to [tables].

## 2. Pipeline

> Design `usecases/<name>/agents/pipeline.agent.yaml` as an ordered sequential pipeline for
> <domain>. The steps are: [list the steps]. For each step give an id, agent name,
> prompt_id, model_alias (bulk for simple/high-volume, reason for complex), the tools it
> may call, and the outputs it writes to the shared context. Add a guardrail policy.

## 3. Prompts (one file per step)

> Create `usecases/<name>/prompts/<step>.prompt.yaml` for the "<step>" step. Fields: id
> `<name>.<step>`, version 1, labels [prod], model_alias <alias>, temperature 0.2, inputs
> [<vars>], a template that [describe the task; require citing evidence; forbid inventing
> facts], eval_refs pointing to the golden set, and a changelog. Use {{var}} placeholders
> matching inputs.

Repeat per step.

## 4. Golden dataset

> Create 15-25 rows in `usecases/<name>/evals/golden.<program>.jsonl`. Each row: id, input
> (the pipeline input), grading (must_include / must_not_include / must_cite_evidence /
> expected_score_band / must_flag as appropriate), meta (program, source: sme_authored).
> Cover typical, edge, and known-failure cases. These are ground truth run as a gate.

## 5. Evaluators + thresholds

> Fill `usecases/<name>/evals/evaluators.yaml`: enable the metric groups relevant to
> <domain> (RAG metrics only if we retrieve; tool_selection if the pipeline uses tools;
> task_success via judge). Set minimums and a max_drop vs baseline. Keep absolute floors
> pii_leak_rate 0 and unsafe_rate 0.

## 6. Review

Have an SME confirm the golden answers and business users confirm format/personalization
preferences. Run `python backend/evals/run.py --usecase <name> --subset full --fail-under
baseline` to record the baseline, then open a PR (the eval gate runs automatically).
