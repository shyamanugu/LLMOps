"""Start the Ops console backend (stdlib HTTP API on :8000).

    python ops/start_backend.py

Mock by default (local SQLite + JSON registry, no Azure). Set AI_PIPELINE_MODE=real
(and the real creds in .env) to have the playground call live models.
"""
import sys
from pathlib import Path

# Make the ops package importable and load .env (stdlib parser — no python-dotenv,
# so this works on a locked-down VDI with nothing pip-installed).
_OPS = Path(__file__).resolve().parent
sys.path.insert(0, str(_OPS))

from server import config  # noqa: E402

_ENV_PATH = _OPS.parent / ".env"
config.load_dotenv_stdlib(_ENV_PATH)

from server.api import serve  # noqa: E402

if __name__ == "__main__":
    import os
    found = _ENV_PATH.exists()
    print("=" * 64)
    print(f"  MODE: {config.mode().upper()}   (AI_PIPELINE_MODE={os.environ.get('AI_PIPELINE_MODE', '(unset -> mock)')})")
    print(f"  .env: {'loaded ' + str(_ENV_PATH) if found else 'NOT FOUND at ' + str(_ENV_PATH) + '  (copy .env.example -> .env to switch to real)'}")
    print(f"  To switch: set AI_PIPELINE_MODE=real in .env (and REASONING_MODEL_* for live models)")
    print("=" * 64)
    serve()
