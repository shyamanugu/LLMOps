"""Serve the Ops console UI (zero-build: static HTML/JS/CSS) on :5173 and open it.

    python ops/start_ui.py

No Node/npm required — the UI is vanilla JS that calls the backend API at
http://localhost:8000. Start the backend first (python ops/start_backend.py).
"""
import http.server
import os
import socketserver
import webbrowser
from functools import partial
from pathlib import Path

UI_DIR = Path(__file__).resolve().parent / "ui"
PORT = int(os.environ.get("OPS_UI_PORT", "5173"))

if __name__ == "__main__":
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(UI_DIR))
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        url = f"http://127.0.0.1:{PORT}/index.html"
        print(f"[ops-ui] serving {UI_DIR}\n[ops-ui] {url}")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        httpd.serve_forever()
