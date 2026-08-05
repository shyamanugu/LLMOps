# Evaluation (How We Actually Evaluate)

This is the document Kiran pushed hardest on. The earlier material said we would evaluate but never said *how*. So this one is concrete: what the golden dataset is, the exact metric groups, the real code that produces each score, and how those scores become a gate that can block a merge. APIX is the running example. The tool-selection part uses a Hiring Intelligence example (Applicant Tracking System tools), because that is the clearest case of an agent picking the wrong tool.

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

## The CI gate

Thresholds live in `evaluators.yaml` next to the golden data. This declares which metrics run and the bar each must clear:

```yaml
# evals/apix/evaluators.yaml
suite: apix
datasets: [golden.telesales.jsonl, golden.wcc.jsonl]
metrics:
  groundedness:      { tool: ragas,     min: 0.85 }
  context_relevance: { tool: ragas,     min: 0.80 }
  coaching_quality:  { tool: deepeval,  min: 0.70 }
  score_band_hit:    { tool: custom,    min: 0.90 }   # execution / task-path
  tool_accuracy:     { tool: custom,    min: 0.95 }   # agent behavior
  arg_correctness:   { tool: custom,    min: 0.90 }
gate:
  fail_under: baseline   # block if any metric drops below its recorded baseline
```

The pull-request workflow runs these. This is the gate from the CI/CD backbone doc:

```yaml
# .github/workflows/pr-checks.yml (the relevant step)
- run: python evals/run.py --subset changed --fail-under baseline
  #     ^ runs Ragas + DeepEval + tool_selection on changed prompts/agents;
  #       exits non-zero (blocks merge) if a metric drops past its baseline
```

`--subset changed` runs only the evaluators for the prompts and agents touched in the pull request, so the pull-request gate is fast. The full golden set runs on merge and nightly (`eval-full.yml`). A non-zero exit fails the required check, and the merge button stays disabled. There is no path to production that skips this.

**Per-agent and end-to-end.** We evaluate each pipeline step on its own *and* the whole pipeline top to bottom, because **a pipeline can pass end-to-end while one step quietly degrades.** If the scoring step gets slightly worse but the report-writing step compensates, the final output might still clear the bar while the scoring step is now unreliable. Per-agent evaluation catches the step-level regression before it compounds. Both run in the gate.

## Online evaluation

Offline evaluation on the golden set catches regressions before deploy. It cannot catch drift in live traffic — new call types, changing agent behavior, a model provider quietly updating a model. So we also evaluate in production:

- **Sample** a percentage of production requests (not all — cost).
- **Score them asynchronously** off the request path, using the same evaluators, so live latency is untouched.
- **Alert on drift** — if groundedness or tool accuracy on sampled traffic falls below the offline baseline, it raises an alert on the same dashboards as latency and error rate.
- **Human review** — sampled outputs flagged low by the judge go to SMEs. Their verdicts feed back into the golden dataset (step two above), which closes the loop: production teaches the gate what to catch next time.
