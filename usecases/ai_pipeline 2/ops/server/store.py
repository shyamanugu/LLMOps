"""Local SQLite store for feedback, guardrail-audit, LLM traces, and eval runs.
Stdlib only. In real mode you'd point these reads at Azure Monitor / Blob, but
the Ops console keeps a local mirror so the UI works identically offline."""
import json
import sqlite3
from datetime import datetime, timezone

from . import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conn():
    config.ensure_dirs()
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS feedback(
              id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, program TEXT, contact_id TEXT,
              step TEXT, rating TEXT, comment TEXT, corrected_output TEXT, rater TEXT);
            CREATE TABLE IF NOT EXISTS guardrails(
              id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, run_id TEXT, step TEXT,
              deployment TEXT, decision TEXT, reason TEXT);
            CREATE TABLE IF NOT EXISTS traces(
              id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, run_id TEXT, step TEXT,
              model_alias TEXT, deployment TEXT, input_tokens INTEGER, output_tokens INTEGER,
              cost_usd REAL, latency_ms REAL, error TEXT);
            CREATE TABLE IF NOT EXISTS eval_runs(
              id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, program TEXT, prompt TEXT,
              version INTEGER, model_alias TEXT, dataset TEXT, pass_rate REAL, passed INTEGER,
              n_cases INTEGER, cost_usd REAL);
            """
        )


# ── inserts ──────────────────────────────────────────────────────────────
def add_feedback(program, contact_id, step, rating, comment="", corrected_output=None, rater="reviewer"):
    with _conn() as c:
        c.execute("INSERT INTO feedback(ts,program,contact_id,step,rating,comment,corrected_output,rater)"
                  " VALUES(?,?,?,?,?,?,?,?)",
                  (_now(), program, contact_id, step, rating, comment, corrected_output, rater))


def add_guardrail(run_id, step, deployment, decision, reason):
    with _conn() as c:
        c.execute("INSERT INTO guardrails(ts,run_id,step,deployment,decision,reason) VALUES(?,?,?,?,?,?)",
                  (_now(), run_id, step, deployment, decision, reason))


def add_trace(run_id, step, model_alias, deployment, ti, to, cost, latency, error=None):
    with _conn() as c:
        c.execute("INSERT INTO traces(ts,run_id,step,model_alias,deployment,input_tokens,output_tokens,"
                  "cost_usd,latency_ms,error) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (_now(), run_id, step, model_alias, deployment, ti, to, cost, latency, error))


def add_eval_run(program, prompt, version, model_alias, dataset, pass_rate, passed, n_cases, cost):
    with _conn() as c:
        c.execute("INSERT INTO eval_runs(ts,program,prompt,version,model_alias,dataset,pass_rate,passed,"
                  "n_cases,cost_usd) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (_now(), program, prompt, version, model_alias, dataset, pass_rate, int(passed), n_cases, cost))


# ── reads ────────────────────────────────────────────────────────────────
def _rows(sql, args=()):
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def list_feedback(limit=200):
    return _rows("SELECT * FROM feedback ORDER BY id DESC LIMIT ?", (limit,))


def list_guardrails(limit=200):
    return _rows("SELECT * FROM guardrails ORDER BY id DESC LIMIT ?", (limit,))


def list_traces(limit=500):
    return _rows("SELECT * FROM traces ORDER BY id DESC LIMIT ?", (limit,))


def list_eval_runs(limit=100):
    return _rows("SELECT * FROM eval_runs ORDER BY id DESC LIMIT ?", (limit,))


def monitoring_summary():
    with _conn() as c:
        tot = dict(c.execute(
            "SELECT COUNT(*) llm_calls, COALESCE(SUM(input_tokens),0) input_tokens,"
            " COALESCE(SUM(output_tokens),0) output_tokens, COALESCE(SUM(cost_usd),0) cost_usd,"
            " COALESCE(AVG(latency_ms),0) avg_latency_ms, SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) errors"
            " FROM traces").fetchone())
        by_step = [dict(r) for r in c.execute(
            "SELECT step, COUNT(*) calls, COALESCE(SUM(cost_usd),0) cost_usd,"
            " COALESCE(AVG(latency_ms),0) avg_latency_ms FROM traces GROUP BY step").fetchall()]
        guardrail_flags = c.execute("SELECT COUNT(*) n FROM guardrails").fetchone()["n"]
    tot["guardrail_flags"] = guardrail_flags
    tot["cost_usd"] = round(tot["cost_usd"], 6)
    tot["avg_latency_ms"] = round(tot["avg_latency_ms"], 1)
    return {"totals": tot, "by_step": by_step}


def counts():
    with _conn() as c:
        return {t: c.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"]
                for t in ("feedback", "guardrails", "traces", "eval_runs")}
