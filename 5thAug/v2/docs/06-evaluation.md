# Evaluation (How We Actually Evaluate)

This is the document Kiran pushed hardest on. The earlier material said we would evaluate but never said *how*. So this one is concrete: what the golden dataset is, the exact metric groups, the real code that produces each score, what each score actually means, how the thresholds are set, what each evaluation technique costs, and how those scores become a gate that can block a merge. APIX is the running example. The tool-selection part uses a Hiring Intelligence example (Applicant Tracking System tools), because that is the clearest case of an agent picking the wrong tool.

## Today, our setup, what changes

| | Detail |
|---|---|
| **Today** | Evaluation is a manual spot-check. Someone runs a few transcripts by hand, reads the output, and decides it looks fine. There is no dataset, no score, no threshold. A prompt or model change ships with nothing stopping it if the output quietly got worse. |
| **Our setup** | A golden dataset per use case and per program, four groups of metrics each produced by a real mechanism (Ragas, DeepEval, custom Python, Large Language Model as judge), thresholds declared in `evaluators.yaml`, and a Continuous Integration (CI) gate that runs them on every pull request and blocks the merge if a metric drops below its baseline. Plus online evaluation on sampled production traffic. |
| **What changes** | Evaluation moves from "a person looks at it sometimes" to "every change is scored against a fixed dataset and cannot deploy unless it clears the bar." That is the whole delta, and it is what makes this enterprise-grade. |

## The golden dataset

A golden dataset is a fixed set of inputs with their expected outcomes — ground truth for the use case. For APIX Telesales, each record is a real call transcript plus what a good coaching report should contain: the score band it should land in, the moments it must flag, whether it must cite evidence.

**Kiran's question: how is this different from normal ground truth?** It is the same idea. The difference is not the data, it is what we *do* with it. In LLMOps the golden dataset is run as a **gate at every change and every pipeline run** before a release can deploy. Normal ground truth sits in a spreadsheet and gets looked at when someone remembers. The golden dataset is wired into the pipeline so that no prompt edit, model swap, or agent change reaches production without being scored against it first.

One record from the APIX Telesales set (this is the exact format we use):

```json
{"id":"apix-telesales-014","input":{"transcript_id":"c-88421","program":"telesales"},
 "grading":{"must_cite_evidence":true,"expected_score_band":[70,85],"must_flag":["missed_upsell"]},
 "meta":{"program":"telesales","source":"sme_authored"}}
```

`input` is what the pipeline receives. `grading` is what we check the output against. `meta.source` records where the record came from, which matters because the dataset is built in three steps.

**Where the records come from (three steps):**

1. **Subject Matter Expert (SME) authored, first.** For a new use case the SME writes the initial set — the transcripts and the correct scoring for each. This is the very first artifact we create for any use case, before we tune a single prompt. You cannot evaluate against nothing.
2. **Real traffic over time.** Once the pipeline is live we pull real production examples into the set. This matters because **users have format and personalization preferences an SME will not think to write down** — a coach wants the note phrased a certain way, a program lead wants upsell misses called out in a specific style. The SME's clean examples never capture that. Real traffic does.
3. **SME and business review.** Candidate records pulled from production are reviewed again by SMEs and business users before they become golden. We do not promote raw production output into ground truth without a human confirming it is actually correct.

**How many to start:** 50 to 200 records **per use case and per program**. APIX has two programs — Telesales and Web Contact Center (WCC) — so `golden.telesales.jsonl` and `golden.wcc.jsonl` are separate files, each 50 to 200 records. The two programs score differently and flag different things, so mixing them would hide regressions in one behind the other. Fifty is enough to catch real regressions; we grow toward 200 as real traffic comes in.

## Metric groups

We score four groups. Each group answers a different question and is produced by a different mechanism.

| Group | Example metrics | How scored | Tool |
|---|---|---|---|
| **RAG (retrieval quality)** | Groundedness (answer supported by retrieved context), context relevance, context recall | Model-graded against the retrieved context | Ragas |
| **Writing quality** | Coherence, tone match, conciseness, follows the coaching format | Large Language Model as judge with a rubric (G-Eval) | DeepEval |
| **Execution / task-path** | Reached the expected score band, flagged the required moments, cited evidence | Deterministic checks against the `grading` block | Custom Python |
| **Agent behavior** | Correct tool chosen, arguments correct, no wrong-tool or missing-tool calls | Compare the agent's actual tool calls to expected | Custom Python (`tool_selection.py`) |

**The overlap Kiran raised.** He is right that coherence could sit under RAG, and that in a RAG-heavy use case most metrics fall under RAG. We still keep the groups separate on purpose, because they answer different questions:

- **Writing quality** is about *how it reads*. A coaching note can be perfectly grounded in the transcript and still be a badly written, rambling note. Groundedness will not catch that; a writing-quality judge will.
- **Execution / task-path** is about *whether it did the right thing*. Did it land in the right score band, did it flag the missed upsell. An answer can read beautifully and be wrong.
- **Agent behavior** is about *whether it took the right action* — did it call the right tool with the right arguments. This is not a RAG question at all, and it is the group Ragas and DeepEval do not cover.

Non-RAG use cases exist (a pure scoring step with no retrieval), and any step that calls tools needs agent-behavior metrics regardless of RAG. That is why four groups, not one.

## What each metric actually means

Kiran asked for the metrics in plain words, not jargon. Every metric below returns a number between 0 and 1, where 1 is best. Higher is always better, so a threshold reads "must be at least X."

| Metric | What it measures, in plain words | Scale |
|---|---|---|
| **Groundedness** | Every claim in the answer is backed by the retrieved context. Nothing invented. This is the "do not make up moments" rule, measured. | 0 to 1 (1 = fully supported) |
| **Context relevance / precision** | Of the chunks we retrieved and fed the model, how many were actually on-point for the question. Catches retrieval pulling in junk. | 0 to 1 (1 = all retrieved chunks on-point) |
| **Answer relevance** | Does the answer address what was actually asked, rather than drifting to a related-but-different point. | 0 to 1 (1 = directly on the ask) |
| **Coherence / fluency** | Does it read well — clear, ordered, readable, correct language. A quality-of-writing score, separate from whether it is correct. | 0 to 1 (1 = clean, readable) |
| **Correctness / similarity** | How close the answer is to the reference (golden) answer in meaning. Compared against ground truth, not just judged in isolation. | 0 to 1 (1 = matches reference) |
| **Tool-selection accuracy** | Fraction of cases where the agent chose the right tool for the job. The core agent-behavior number. | 0 to 1 (1 = right tool every time) |
| **Task success** | End-to-end: did the whole pipeline produce a correct, complete result for the case, across all steps. | 0 to 1 (1 = fully correct end-to-end) |

## The HOW — real mechanisms

### Ragas for RAG metrics

Ragas scores retrieval-augmented answers against the context that was actually retrieved. For the APIX evidence-gathering step we check groundedness and context relevance:

```python
from ragas import evaluate
from ragas.metrics import faithfulness, context_relevancy
from datasets import Dataset

def score_rag(samples):  # samples: question, answer, contexts (retrieved chunks)
    ds = Dataset.from_list(samples)
    result = evaluate(ds, metrics=[faithfulness, context_relevancy])
    return {"groundedness": result["faithfulness"],
            "context_relevance": result["context_relevancy"]}
```

`faithfulness` is our groundedness metric — it checks that every claim in the answer is supported by the retrieved context, which is exactly the "do not invent moments" rule from the coaching prompt.

### DeepEval for writing quality (G-Eval), pytest-style in CI

DeepEval runs like unit tests, so it drops straight into the CI pipeline. We use G-Eval to define a custom writing-quality metric from a plain-English rubric:

```python
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

coaching_quality = GEval(
    name="CoachingQuality",
    criteria="The note is concise, uses a supportive coaching tone, and follows "
             "the required format: one strength, one area to improve, cited evidence.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7,
)

def test_coaching_quality(case):
    tc = LLMTestCase(input=case["input"], actual_output=run_pipeline(case["input"]))
    assert_test(tc, [coaching_quality])   # fails the CI job if score < 0.7
```

### Custom Python for agent behavior / correct tool usage

**Ragas and DeepEval do not evaluate tool selection.** They score text quality and retrieval; they have no concept of "the agent should have called `parse_resume` and instead called `search_candidates`." That check is ours to write. This is the `tool_selection.py` harness — the Hiring Intelligence example: given a resume file, the agent must pick the resume-parsing tool from the Applicant Tracking System, not the candidate-search tool.

```python
def evaluate_tool_selection(cases, run_agent):
    rows = []
    for c in cases:                                 # c: input, expected_tool, expected_args
        trace = run_agent(c["input"])
        chosen = trace.tool_calls[0].name if trace.tool_calls else None
        args_ok = compare_args(trace.tool_calls[0].args if trace.tool_calls else {}, c["expected_args"])
        rows.append({"expected": c["expected_tool"], "chosen": chosen, "args_ok": args_ok})
    return {
      "accuracy": mean(r["chosen"] == r["expected"] for r in rows),
      "wrong_tool_rate": mean(r["chosen"] not in (None, r["expected"]) for r in rows),
      "missing_tool_rate": mean(r["chosen"] is None and r["expected"] is not None for r in rows),
      "arg_correctness": mean(r["args_ok"] for r in rows),
      # + per-tool precision/recall
    }
```

The metrics it produces:

- **accuracy** — fraction of cases where the agent chose the right tool.
- **wrong_tool_rate** — chose a tool, but the wrong one (called `search_candidates` on a resume).
- **missing_tool_rate** — should have called a tool and called none.
- **arg_correctness** — right tool, but were the arguments right (correct candidate id, correct field).
- **per-tool precision and recall** — so we can see *which* tool the agent confuses, not just an overall number.

### Large Language Model as judge, and LangSmith

For subjective quality that a fixed check cannot capture — is this coaching note genuinely helpful — we use a **Large Language Model as judge** with an explicit rubric. The rubric is the important part: we do not ask "is this good," we give the judge the same criteria a human reviewer would use and have it score against them. G-Eval above is one packaged form of this.

**LangSmith** also does evaluation plus observability in one product, and it is capable. We are not defaulting to it because it is **not open source — it needs a license**. Our default stack (Ragas, DeepEval, custom Python, self-hosted Langfuse) keeps evaluation in our own repository and network with no per-seat license. LangSmith stays on the table if the team wants a managed option later.

## How the thresholds are defined

A threshold that someone picks out of the air is worthless — too low and it never fails, too high and it blocks every change. We set them from evidence, in two parts.

**1. A baseline run of current production.** Before any change, we run the whole golden set against what is live today and record the score for every metric. That recorded set of numbers is the baseline. The gate rule is relative to it:

> **No metric may drop more than X% below its baseline.** (We start with X = 2%.)

This is the main rule because it catches the real danger — a change that quietly makes things worse. It does not demand a fixed absolute score the current system may not even hit; it demands you do not go backwards.

**2. Absolute floors and minimums, on top of the relative rule.** Two things must never be allowed to slide, no matter what the baseline was:

- **Absolute floors for safety — these are zero and stay zero.** PII (Personally Identifiable Information) leak rate = 0. Unsafe-content rate = 0. There is no "2% worse than baseline" tolerance on a safety failure; any leak fails the gate outright.
- **Absolute minimums for critical metrics.** Some metrics have a floor below which the output is not fit to ship even if the baseline happened to be low — for example **groundedness must be at least 0.9**. This protects against a bad baseline dragging the bar down.

So a change passes only if it clears **both** the relative rule (no metric more than X% below baseline) **and** the absolute floors and minimums. All of this lives in `evaluators.yaml` next to the golden data, so the bar is versioned and reviewed like any other config:

```yaml
# evals/apix/evaluators.yaml
suite: apix
datasets: [golden.telesales.jsonl, golden.wcc.jsonl]

metrics:
  groundedness:      { tool: ragas,     min: 0.90 }   # absolute minimum — critical metric
  context_relevance: { tool: ragas,     min: 0.80 }
  answer_relevance:  { tool: ragas,     min: 0.80 }
  coaching_quality:  { tool: deepeval,  min: 0.70 }
  score_band_hit:    { tool: custom,    min: 0.90 }   # execution / task-path
  tool_accuracy:     { tool: custom,    min: 0.95 }   # agent behavior
  arg_correctness:   { tool: custom,    min: 0.90 }

safety_floors:                                        # absolute — must be exactly 0
  pii_leak_rate:     { tool: custom,    max: 0.0 }
  unsafe_rate:       { tool: content_safety, max: 0.0 }

gate:
  relative: no_metric_below_baseline_by: 0.02         # no metric > 2% under its baseline
  baseline: recorded_from_prod                        # baseline captured from current prod
  block_on: [relative, min, safety_floors]            # all three must pass to merge
```

`min` is the absolute minimum for a metric; `max` is the absolute ceiling for a bad-thing rate (safety). `relative` is the "do not go backwards" rule against the recorded baseline. A change has to satisfy all of them.

## The CI gate

The pull-request workflow runs these. This is the gate from the CI/CD backbone doc:

```yaml
# .github/workflows/pr-checks.yml (the relevant step)
- run: python evals/run.py --subset changed --fail-under baseline
  #     ^ runs Ragas + DeepEval + tool_selection on changed prompts/agents;
  #       exits non-zero (blocks merge) if a metric drops past its baseline
```

`--subset changed` runs only the evaluators for the prompts and agents touched in the pull request, so the pull-request gate is fast. The full golden set runs on merge and nightly (`eval-full.yml`). A non-zero exit fails the required check, and the merge button stays disabled. There is no path to production that skips this.

**Per-agent and end-to-end.** We evaluate each pipeline step on its own *and* the whole pipeline top to bottom, because **a pipeline can pass end-to-end while one step quietly degrades.** If the scoring step gets slightly worse but the report-writing step compensates, the final output might still clear the bar while the scoring step is now unreliable. Per-agent evaluation catches the step-level regression before it compounds. Both run in the gate.

## What each evaluation technique costs

Kiran asked what evaluation itself costs to run. It is not free, but the cost is driven by one thing — how often we call a judge model — and that is controllable. The table below is per technique. All dollar figures are indicative; confirm at sizing.

| Technique | How it is charged | Indicative cost |
|---|---|---|
| **Custom Python** (exact checks, tool-selection, task-path) | Compute only — plain code, no model calls | ~Free (runs on the CI runner) |
| **Ragas / DeepEval — rule-based metrics** | Compute only | ~Free |
| **Ragas / DeepEval — LLM-based metrics** (faithfulness, G-Eval, etc.) | Each metric calls a judge model → token cost | Token cost per case (see LLM-as-judge) |
| **LLM-as-judge** (the underlying mechanism above) | Judge model tokens per case | Small judge (e.g. GPT-5-mini) ≈ cents to low single-digit dollars per 200-case run |
| **LangSmith** | Platform license (per seat / usage tier) | ≈ $1,500–2,800/mo at scale — licensed, the expensive option |
| **Azure AI Foundry evaluations** | Azure usage — judge tokens only, no separate license | Judge token cost, folded into Azure spend |

**The one driver: judge tokens × dataset size × number of runs.** Custom Python and rule-based metrics are effectively free. The cost appears only where an LLM judges an output, and it multiplies by how big the golden set is and how often the suite runs. Three mitigations keep it small:

- **Use a small judge model** (GPT-5-mini class), not a frontier model, for grading. Judging is easier than generating.
- **Subset on pull requests** — `--subset changed` judges only the changed prompts/agents, so day-to-day cost is tiny.
- **Full golden set nightly**, when a slightly larger token bill does not slow anyone down.

Net: at a 200-case golden set with a small judge, a full run is a few cents to low single-digit dollars; PR runs cost a fraction of that. LangSmith is the only line item with a real recurring license, which is why our default stack avoids it.

## Online evaluation

Offline evaluation on the golden set catches regressions before deploy. It cannot catch drift in live traffic — new call types, changing agent behavior, a model provider quietly updating a model. So we also evaluate in production:

- **Sample** a percentage of production requests (not all — cost).
- **Score them asynchronously** off the request path, using the same evaluators, so live latency is untouched.
- **Alert on drift** — if groundedness or tool accuracy on sampled traffic falls below the offline baseline, it raises an alert on the same dashboards as latency and error rate.
- **Human review** — sampled outputs flagged low by the judge go to SMEs. Their verdicts feed back into the golden dataset (step two above), which closes the loop: production teaches the gate what to catch next time.
