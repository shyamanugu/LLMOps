"""Paths + runtime mode for the Ops console.

Mock is the default and is **100% Python standard library** — no third-party
packages, so it installs and runs cleanly on a locked-down VDI (incl. Python
3.14) with no pip, no npm, and no network (so corporate SSL/cert.pem is never a
factor). Real mode (AI_PIPELINE_MODE=real) is opt-in and expects live Azure creds.
"""
import os
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parents[1]        # .../ops
PKG_DIR = OPS_DIR.parent                              # ai_pipeline package dir
UI_DIR = OPS_DIR / "ui"

DATA_DIR = Path(os.environ.get("AI_PIPELINE_OPS_DATA", str(OPS_DIR / "data"))).resolve()
REGISTRY_DIR = DATA_DIR / "registry" / "prompts"     # <program>/<name>/vN.json + active.json
DATASET_DIR = DATA_DIR / "datasets"                  # writable golden datasets (*.jsonl)
DB_PATH = DATA_DIR / "ops.db"

BACKEND_PORT = int(os.environ.get("OPS_BACKEND_PORT", "8000"))
UI_PORT = int(os.environ.get("OPS_UI_PORT", "5173"))

PROGRAMS = ["telesales", "wcc", "pso"]
STEPS = ["denoise", "analysis", "summary", "individual_metrics", "kpi"]


def load_dotenv_stdlib(path: Path | None = None) -> None:
    """Minimal .env loader (stdlib only) so we don't depend on python-dotenv.
    Only sets keys that aren't already in the environment."""
    path = path or (PKG_DIR / ".env")
    try:
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        pass


def mode() -> str:
    return "real" if os.environ.get("AI_PIPELINE_MODE", "mock").strip().lower() == "real" else "mock"


def is_mock() -> bool:
    return mode() == "mock"


def ensure_dirs() -> None:
    for d in (DATA_DIR, REGISTRY_DIR, DATASET_DIR):
        d.mkdir(parents=True, exist_ok=True)
