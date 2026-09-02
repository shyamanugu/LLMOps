"""Stdlib HTTP JSON API for the Ops console. No third-party deps in mock mode.
Run via ops/start_backend.py."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from . import config, datasets, engine, registry, seed, store


def _json_default(o):
    return str(o)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    # ── helpers ────────────────────────────────────────────────────────
    def _send(self, obj, code=200):
        body = json.dumps(obj, default=_json_default).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self._send({}, 200)

    # ── routing ────────────────────────────────────────────────────────
    def do_GET(self):
        p = urlparse(self.path).path.strip("/").split("/")
        try:
            if p[:1] != ["api"]:
                return self._send({"error": "not found"}, 404)
            r = p[1:]
            if r == ["health"]:
                return self._send({"mode": config.mode(), "programs": config.PROGRAMS,
                                   "steps": config.STEPS, **store.counts()})
            if r == ["prompts"]:
                return self._send(registry.list_prompts())
            if len(r) == 3 and r[0] == "prompts":
                return self._send(registry.get_prompt(r[1], r[2]) or {"error": "not found"})
            if r == ["models"]:
                return self._send(registry.list_models())
            if r == ["datasets"]:
                return self._send(datasets.list_datasets())
            if len(r) == 2 and r[0] == "datasets":  # GET /api/datasets/{name}
                return self._send({"name": r[1], "cases": datasets.read_cases(r[1])})
            if r == ["runs"]:
                return self._send(store.list_runs())
            if r == ["monitoring"]:
                return self._send(store.monitoring_summary())
            if r == ["eval-runs"]:
                return self._send(store.list_eval_runs())
            if r == ["feedback"]:
                return self._send(store.list_feedback())
            if r == ["guardrails"]:
                return self._send(store.list_guardrails())
            return self._send({"error": "not found", "path": self.path}, 404)
        except Exception as e:
            return self._send({"error": str(e)}, 500)

    def do_POST(self):
        p = urlparse(self.path).path.strip("/").split("/")
        b = self._body()
        try:
            if p[:1] != ["api"]:
                return self._send({"error": "not found"}, 404)
            r = p[1:]
            # POST /api/prompts/{program}/{name}
            if len(r) == 3 and r[0] == "prompts":
                spec = registry.save_version(r[1], r[2], b.get("template", ""),
                                             b.get("model_capability", "reason"), b.get("note", ""))
                return self._send(spec, 201)
            # POST /api/prompts/{program}/{name}/activate/{version}
            if len(r) == 5 and r[0] == "prompts" and r[3] == "activate":
                return self._send(registry.activate(r[1], r[2], int(r[4])))
            if r == ["playground"]:
                return self._send(engine.run_playground(
                    b.get("program", "telesales"), b.get("prompt_name"), b.get("version"),
                    b.get("model_alias", "reason"), b.get("dataset"), b.get("ad_hoc_input")))
            # POST /api/run  -> execute (mock) a pipeline run for the Application tab
            if r == ["run"]:
                res = engine.run_pipeline(b.get("program", "telesales"),
                                          b.get("date", "2025-08-28"), b.get("steps"))
                store.add_run(res["run_id"], res["program"], res["date"],
                              len(res["steps"]), config.mode())
                return self._send(res)
            # dataset CRUD (local): POST /api/datasets/{name}/(cases|upload|delete)
            if len(r) == 3 and r[0] == "datasets" and r[2] == "cases":
                return self._send(datasets.add_case(r[1], b.get("case", {})), 201)
            if len(r) == 4 and r[0] == "datasets" and r[2] == "cases":  # update by id
                return self._send(datasets.update_case(r[1], r[3], b.get("case", {})))
            if len(r) == 4 and r[0] == "datasets" and r[2] == "delete":  # delete case by id
                return self._send(datasets.delete_case(r[1], r[3]))
            if len(r) == 3 and r[0] == "datasets" and r[2] == "upload":
                return self._send(datasets.upload_dataset(r[1], b.get("content", "")), 201)
            if r == ["feedback"]:
                store.add_feedback(b.get("program", "telesales"), b.get("contact_id", ""),
                                   b.get("step", "analysis"), b.get("rating", ""), b.get("comment", ""),
                                   b.get("corrected_output"), b.get("rater", "reviewer"))
                return self._send({"ok": True}, 201)
            return self._send({"error": "not found", "path": self.path}, 404)
        except Exception as e:
            return self._send({"error": str(e)}, 500)


def serve():
    seed.seed()  # idempotent: ensures DB + starter prompts exist
    addr = ("127.0.0.1", config.BACKEND_PORT)
    print(f"[ops-backend] mode={config.mode()}  http://{addr[0]}:{addr[1]}/api/health")
    ThreadingHTTPServer(addr, Handler).serve_forever()
