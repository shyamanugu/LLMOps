"""API routers — one module per resource under ``/api/v1`` (ARCHITECTURE_SPEC §3).

Each router implements the documented routes with real handlers. Where data must come from
Application Insights or Langfuse (traces, costs, guardrail events) and that wiring is not
yet present, the handler returns a clearly-labelled placeholder payload
(``"source": "placeholder"``) and carries a ``# TODO(wiring): ...`` marker — never a crash.
"""

from __future__ import annotations
