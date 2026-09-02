"""Paths + runtime mode for the Ops console. Mock is the default: everything
lives under ops/data as local SQLite + JSON, no Azure required. Real mode reads
AI_PIPELINE_MODE=real and expects live Azure creds/services downstream."""
import os
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parents[1]        # .../ops
PKG_DIR = OPS_DIR.parent                              # ai_pipeline package dir
UI_DIR = OPS_DIR / "ui"

DATA_DIR = Path(os.environ.get("AI_PIPELINE_OPS_DATA", str(OPS_DIR / "data"))).resolve()
REGISTRY_DIR = DATA_DIR / "registry" / "prompts"     # <program>/<name>/vN.json + active.json
DB_PATH = DATA_DIR / "ops.db"

BACKEND_PORT = int(os.environ.get("OPS_BACKEND_PORT", "8000"))
UI_PORT = int(os.environ.get("OPS_UI_PORT", "5173"))


def mode() -> str:
    return "real" if os.environ.get("AI_PIPELINE_MODE", "mock").strip().lower() == "real" else "mock"


def is_mock() -> bool:
    return mode() == "mock"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
