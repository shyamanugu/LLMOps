"""Settings for the framework.

Everything comes from environment variables (or a local .env). Nothing secret lives in code.
If the Azure OpenAI endpoint is not set, the framework runs in MOCK MODE so the whole thing works
offline for a demo.
"""

import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass  # dotenv is optional; env vars still work without it

# Repo root = one level above this framework/ folder.
ROOT = Path(__file__).resolve().parent.parent

APP_ENV = os.getenv("APP_ENV", "dev")

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")

# Azure AI Search (optional; blank -> local retriever)
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "")

# Content Safety (optional; blank -> simple built-in checks)
CONTENT_SAFETY_ENDPOINT = os.getenv("CONTENT_SAFETY_ENDPOINT", "")

# Langfuse (optional; blank -> console tracing)
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")

# True when no real model endpoint is configured -> run deterministic mock answers.
MOCK_MODE = not AZURE_OPENAI_ENDPOINT


def load_models() -> dict:
    """Load framework/models.json and return the alias->deployment map for the current env."""
    data = json.loads((ROOT / "framework" / "models.json").read_text(encoding="utf-8"))
    return data["environments"][APP_ENV]
