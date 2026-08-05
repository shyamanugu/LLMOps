# Evaluation Deep-Dive

This is the part the client asked us to spend the most time on, so it goes deep.
It covers how we judge whether the two pipelines — APIX (Afni Performance
Intelligence Index) and Hiring Intelligence — are actually doing good work, not
just producing text that looks good. Both are agent pipelines (sequential steps),
not agent-to-agent systems, so we evaluate each step and the whole chain.

## Why evaluating LLMs is different

Normal software is deterministic. You send the same input, you get the same
output, and a test either passes or fails. Large Language Models (LLMs) are not
like that. The same prompt can give different wording on two runs. More
importantly, a wrong answer can read perfectly — fluent, confident, well
structured — and still be wrong. In APIX a coaching note can quote a moment that
never happened in the call. In Hiring a candidate summary can call the right ATS
(Applicant Tracking System) tool but pass the wrong requisition ID, or call a
fluent-sounding tool that was simply the wrong choice.

So we cannot test with "output equals expected string". We test along several
dimensions at once: is it grounded in real evidence, does it read well, did it
take the right action, is it safe and fair, and is it affordable. A single pass
or fail is replaced by scores per dimension, each with a baseline threshold.

## The metric groups

We group metrics by **what is being judged**, not by the mechanism that produces
the number. That way a future use case that is not Retrieval-Augmented Generation
(RAG) is still covered by the same framework.

| Group | Example metrics | How scored | Which use case |
|---|---|---|---|
| Retrieval / RAG quality | context relevance, groundedness/faithfulness, answer relevance, retrieval precision & recall | Ragas, LLM-as-judge over retrieved context vs answer | Hiring (RAG over job description, rubric, policy); APIX (coaching grounded in transcript) |
| Generation / writing quality | coherence, fluency, tone, completeness, correctness vs a reference | LLM-as-judge with a rubric; DeepEval G-Eval; compare to reference where one exists | APIX coaching notes; Hiring candidate summary |
| Task execution / agentic | task success rate, tool-selection accuracy, tool-argument correctness, pipeline-path correctness, step efficiency | Custom Python reading the trace against expected tool/args/path | Hiring (which ATS/MCP tool, right arguments); APIX (correct data retrieval) |
| Safety / compliance / fairness | unsafe-content rate, PII (Personally Identifiable Information) leakage, policy adherence, bias/consistency | Azure Content Safety, PII scanners, statistical fairness checks across groups | Hiring ranking fairness; APIX consistency across agents and sites |
| Operational | latency, cost, tokens per request | Read straight from the trace/telemetry | Both — matters most at APIX "thousands of calls/day" scale |

### Why writing quality and task execution are separate

The client asked this directly, so we state it plainly. **Writing quality judges
how the answer reads. Task execution judges whether the system did the right
thing.** These are independent. A Hiring summary can be beautifully written and
still be built on the wrong tool call — for example, it screened the candidate
against the wrong job requisition. The prose is fine; the action was wrong. If we
folded both into one "quality" score, a fluent-but-wrong-action answer would pass.
Keeping them apart means a well-written answer built on a wrong tool still fails
the task-execution gate. That is exactly the failure mode the client worried
about.

### Where groups overlap, and how we handle it

Some metrics could sit in two groups. Coherence, for example, could be a RAG
metric (does the answer hang together with the retrieved context) or a writing
metric (does it read well on its own). We do not fight over the label. We assign
each metric to **one** owning group for reporting so the number is not
double-counted, and we note the overlap. Coherence lives under writing quality;
faithfulness-to-context lives under RAG. The rule of thumb: if the metric is about
the answer's relationship to retrieved evidence, it is RAG; if it is about the
answer as a piece of text, it is writing. This keeps the scorecard clean while
acknowledging the reality the client raised.

## Tool-selection evaluation (in depth)

This was the client's specific probe: an MCP (Model Context Protocol) server
exposes several tools; if the agent picks a wrong tool that still returns a
plausible answer, the system is unreliable. Standard RAG evaluators (Ragas,
DeepEval) do not measure this — they judge text, not which function was called.
So we treat tool selection as a first-class evaluator written in **custom Python**
that reads the tool-call span from the trace.

Take the Hiring ATS tools as the example. Suppose the MCP server exposes:
`search_candidates`, `get_requisition`, `update_candidate_stage`,
`schedule_interview`, `parse_resume`. For each test case we record the **expected
tool** and **expected arguments**. We run the agent, read what it actually called
from the trace, and compare.

Metrics we compute:

- **Tool-selection accuracy** = correct tool chosen / total cases.
- **Per-tool precision and recall** — e.g. for `schedule_interview`, precision
  tells us how often calling it was right; recall tells us how often we caught
  the cases that needed it.
- **Wrong-tool rate** — called a tool, but the wrong one.
- **Unnecessary-tool-call rate** — called a tool when none was needed (e.g. it
  scheduled an interview when the step only asked for a summary).
- **Missing-tool rate** — should have called a tool, but did not.
- **Argument-correctness rate** — right tool, but were the arguments right (the
  correct requisition ID, candidate ID, stage value)?

These become gate metrics in Continuous Integration (CI) for agentic use cases
like Hiring. A drop below baseline blocks promotion.

```python
# custom tool-selection evaluator (pseudocode)
def evaluate_tool_selection(cases, agent):
    stats = {"correct": 0, "wrong": 0, "unnecessary": 0,
             "missing": 0, "arg_ok": 0, "total": len(cases)}
    per_tool = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for case in cases:                      # case has input, expected_tool, expected_args
        trace = agent.run(case["input"])    # runs the pipeline, returns the trace tree
        call = read_tool_call(trace)         # pull tool_name + input_args from the tool span
        got_tool = call.tool_name if call else None
        want_tool = case["expected_tool"]    # None means "no tool should be called"

        if want_tool is None and got_tool is None:
            stats["correct"] += 1
        elif want_tool is None and got_tool is not None:
            stats["unnecessary"] += 1
            per_tool[got_tool]["fp"] += 1
        elif want_tool is not None and got_tool is None:
            stats["missing"] += 1
            per_tool[want_tool]["fn"] += 1
        elif got_tool == want_tool:
            stats["correct"] += 1
            per_tool[got_tool]["tp"] += 1
            if args_match(call.input_args, case["expected_args"]):
                stats["arg_ok"] += 1
        else:                                # called the wrong tool
            stats["wrong"] += 1
            per_tool[got_tool]["fp"] += 1
            per_tool[want_tool]["fn"] += 1

    return summarize(stats, per_tool)        # accuracy, wrong/unnecessary/missing rates,
                                             # arg-correctness, per-tool precision/recall
```

`args_match` is deliberately not naive string equality — for identifiers it is
exact match, for free-text arguments it can allow a normalized or semantic match.
The point is that the harness reads the **actual trace**, so the same
instrumentation we use for observability feeds evaluation.

## Evaluator tooling matrix

The client wanted options, not a single tool. We recommend a **mix**, each tool
doing the job it is best at.

| Tool | Covers | Open source? | Use it for |
|---|---|---|---|
| Ragas | RAG metrics: groundedness, context precision/recall, answer relevance | Yes (Python) | APIX groundedness of coaching; Hiring RAG relevance |
| DeepEval | Broad LLM eval incl. RAG, custom G-Eval, some agentic; pytest-style | Yes (Python) | CI gate, writing quality, general checks |
| Custom Python | Tool selection, tool arguments, pipeline path, scoring-vs-label, extraction F1 | Yes (our code) | Agent/tool behavior not covered elsewhere |
| LLM-as-judge (+ rubric) | Subjective quality: coaching usefulness, summary quality | Depends on model | Cases with no single reference answer |
| Azure AI Foundry evaluations | Built-in + custom evaluators, cloud runs, links scores to traces | No (Azure) | Staying inside the Azure tenant; trace-linked eval |
| promptfoo | Config-driven CI evals, quick red-team | Yes | Fast CI checks and red-teaming |
| LangSmith | Eval + observability + datasets platform | No — licensed | Only if already standardized on LangChain; note license cost |

**For APIX:** Ragas for groundedness of coaching notes; custom Python for
scoring-vs-human-QA agreement and extraction F1 (escalation, sentiment, sales
outcome); LLM-as-judge with a rubric for coaching usefulness and tone; DeepEval to
run it all in the CI gate; Foundry evaluations to link scores back to the trace.

**For Hiring:** Ragas for RAG relevance and groundedness; custom Python for
tool-selection and argument correctness (the harness above); LLM-as-judge for
summary quality; fairness checks in custom Python across candidate groups;
promptfoo for red-team probes on the screening Q&A agent.

## How evaluation runs

**Offline (CI gate).** Golden datasets run automatically. Crucially, datasets are
kept **per use case and per program** — APIX Telesales and APIX WCC (the
contact-center program) use different measurement criteria, so a single golden set
would hide program-specific regressions. A fast subset runs on every pull request;
the full set runs nightly and on merge. If any metric drops past its baseline
threshold, promotion is blocked.

**Online (production).** We sample a small percentage of live traffic and run
evaluators asynchronously (out of the request path) — for example an
LLM-as-judge groundedness check on real APIX reports. We track the quality trend
over time and raise **drift alerts** when scores slide, which catches problems
that the fixed golden set cannot.

**Human review.** Coaches and recruiters give feedback (thumbs, edits,
overrides), and Subject-Matter Experts (SMEs) review a periodic sample. Their
findings flow back into the golden datasets.

**Per-agent AND end-to-end.** We evaluate each pipeline step on its own — every
APIX dimension-analysis agent, each Hiring agent — and the final output (report
quality, candidate summary). This matters because **a pipeline can pass end-to-end
while one agent quietly degrades**: the scoring stage can compensate for a weaker
extraction stage, so the composite score looks fine while the extraction F1 has
dropped. Per-agent evaluation catches the silent degradation before it compounds.

## Golden datasets

Golden datasets are curated, versioned test cases in JSONL (one JSON record per
line). Each record carries the input (and any context), the expected output or a
grading rubric, and metadata (intent, difficulty, program, source). They are the
backbone of the offline gate.

An APIX call-analysis record:

```json
{"id": "apix-ts-0142", "use_case": "apix", "program": "telesales",
 "input": {"transcript_ref": "blob://transcripts/2026/call_88431.txt",
           "metadata": {"agent_id": "A2231", "queue": "outbound_sales",
                        "disposition": "sale", "crm_outcome": "closed_won"}},
 "expected": {"composite_score": {"value": 82, "tolerance": 5},
              "extraction": {"escalation": false, "sentiment": "positive",
                             "sales_outcome": "closed_won"},
              "grounded_evidence": [
                 {"claim": "agent used an assumptive close",
                  "transcript_span": "00:04:12-00:04:35"}],
              "coaching_rubric": ["cites a real moment", "gives one concrete step",
                                  "flags no false risk"]},
 "meta": {"difficulty": "medium", "source": "sme_authored", "version": "2026-08"}}
```

A Hiring record:

```json
{"id": "hire-0087", "use_case": "hiring",
 "input": {"candidate_id": "C55120", "requisition_id": "REQ-4471",
           "resume_ref": "blob://resumes/C55120.pdf"},
 "expected": {"expected_tool": "get_requisition",
              "expected_args": {"requisition_id": "REQ-4471"},
              "fit_score": {"value": 71, "tolerance": 6},
              "summary_rubric": ["grounded in resume + JD", "no protected-attribute language",
                                 "states one gap clearly"]},
 "meta": {"difficulty": "hard", "source": "mined_from_traffic", "version": "2026-08"}}
```

**How many to start:** roughly 50–200 cases per use case and per program, grown
from production feedback over time.

**Three sources:** (1) SME-authored gold cases; (2) mined from anonymized real
traffic via the traces; (3) synthetic, generated then human-reviewed.

**Versioning:** datasets live in `/evals` in the repo, are versioned like code,
and are mirrored to Langfuse/Foundry datasets for UI-driven runs. Every record
carries a version stamp so a metric change can be traced to a dataset change.

**Over-fitting guard:** if we only ever optimize against a fixed set, the
pipeline learns the test rather than the task. We rotate and refresh cases, keep a
held-out slice the team does not tune against, and top up regularly from new
production feedback so the golden set keeps reflecting real inputs.
