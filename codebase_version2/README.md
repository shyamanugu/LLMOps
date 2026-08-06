# LLMOps starter (version 2) — minimal and explainable

A deliberately small LLMOps skeleton. The goal is that you can understand it from the folder
structure alone, run it on a laptop with no cloud, and explain every file. It covers exactly the
components in the v2 deck — nothing more. Only three file types: **Python** (`.py`), **JSON**
(`.json`), and **pipeline** files (`.yml`).

## Folder map (read this once)

```
codebase_version2/
├─ platform/                 THE REUSABLE FRAMEWORK — build once, every use case reuses it
│  ├─ config.py              settings from env; loads models.json
│  ├─ models.json            task alias -> model deployment (e.g. "reason" -> gpt-5.2)
│  ├─ model_management.py    pick and call a model by alias; returns text + tokens + cost
│  ├─ prompt_management.py   load a prompt from the repo (GitHub IS the registry), version, render
│  ├─ guardrails.py          input/output safety checks (unsafe content, personal data)
│  ├─ observability.py       trace every step; record tokens, cost, latency (console or Langfuse)
│  ├─ rag.py                 retrieval: fetch from MULTIPLE sources, then search by relevance
│  ├─ tools.py               the reusable tool catalog (search, sql, get_record)
│  ├─ evaluation.py          run a golden dataset, score it, decide pass/fail (the GATE)
│  └─ pipeline.py            run agents in sequence (NOT agent-to-agent)
│
├─ usecases/                 a use case = prompts + a pipeline + a golden dataset
│  └─ example_qa/            ONE complete, runnable example (a knowledge assistant)
│     ├─ knowledge.json      the source documents for RAG (kept as data)
│     ├─ prompts/answer.prompt.json   the prompt (id, version, template, variables)
│     ├─ pipeline.py         wires the platform components into a pipeline
│     ├─ golden_dataset.json the test cases (question + expected)
│     └─ evaluators.json     the metrics + thresholds (the gate config)
│
├─ jobs/                     scheduled work
│  └─ nightly_eval/          a sample Azure Function App (Python, timer trigger)
│     ├─ function_app.py     runs the full evaluation every night
│     ├─ host.json           Functions host config
│     └─ requirements.txt
│
├─ scripts/
│  ├─ run_pipeline.py        run the example use case once, locally
│  └─ run_eval_gate.py       run the golden dataset as a gate (exit 0 pass / 1 fail) — used by CI
│
└─ pipelines/                CI/CD (the LLMOps part is the eval gate before deploy)
   ├─ pr-eval-gate.yml       on a pull request: run the eval gate; block merge if it fails
   ├─ deploy.yml             build + deploy to Azure Container App / App Service (only if gated)
   └─ nightly.yml            scheduled: run the nightly evaluation
```

## Run it now (no cloud needed)

```bash
pip install -r requirements.txt         # only the base deps; Azure/eval libs are optional
python scripts/run_pipeline.py          # ask the example knowledge assistant a question
python scripts/run_eval_gate.py         # run the golden dataset as a gate -> prints scores + PASS/FAIL
```

With no Azure endpoint set, the model layer runs in a small **mock mode** so everything works
offline for a demo. Set the values in `.env` (see `.env.example`) to use real Azure OpenAI.

## The five things this shows the client

1. **Reusable framework** — every component is one readable Python file in `platform/`, reused by any use case.
2. **Prompt registry = GitHub** — prompts are JSON files in the repo, versioned by pull request.
3. **RAG from multiple sources** — `rag.py` pulls from more than one source and searches by relevance.
4. **Golden dataset as a gate** — `evaluation.py` + `run_eval_gate.py` score the dataset and block on failure.
5. **Pipelines** — `pipelines/*.yml` run the gate on every change and only deploy if it passes; `jobs/` shows a nightly Function App.

## Adding a real use case

Copy `usecases/example_qa/` to `usecases/<your_use_case>/`, change the prompt(s), the knowledge/data
sources, and the golden dataset. The `platform/` code does not change — that is the point.
