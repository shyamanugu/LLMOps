"""FastAPI control plane for the LLMOps platform (the console's backend).

The application is built by :func:`llmops.api.main.create_app` and exposed as
``llmops.api.main.app`` for ASGI servers (``uvicorn llmops.api.main:app``).
"""

from __future__ import annotations
