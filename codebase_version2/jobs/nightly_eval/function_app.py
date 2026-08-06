"""Sample Azure Function App — a nightly job.

This is how a scheduled job is created in Azure Functions (Python v2 model): a timer trigger with a
cron schedule. Every night it re-runs the full evaluation gate for a use case, so we notice quality
drift in production even when nobody changed the code (data and the world move underneath us).

Deploy this folder as a Function App (see pipelines/nightly.yml). The same pattern works for other
scheduled work, e.g. re-indexing RAG sources.
"""

import logging

import azure.functions as func  # provided by the Azure Functions runtime

from framework import evaluation

app = func.FunctionApp()


# Runs at 02:00 every day (NCRONTAB: sec min hour day month day-of-week).
@app.timer_trigger(schedule="0 0 2 * * *", arg_name="timer", run_on_startup=False)
def nightly_eval(timer: func.TimerRequest) -> None:
    """Re-run the evaluation gate nightly and log the result."""
    from usecases.example_qa import pipeline  # imported here so the module loads without a use case

    report = evaluation.run_gate("example_qa", lambda case: pipeline.ask(case["question"]))
    logging.info("nightly_eval result=%s averages=%s", report["passed"], report["averages"])
    # TODO(wiring): if not report["passed"], raise an alert (email / Teams / an incident).
