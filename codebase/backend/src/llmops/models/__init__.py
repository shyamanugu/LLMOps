"""Model catalog: task-alias routing, pricing, and the async Azure OpenAI client.

The model layer keeps three concerns separate:

* :mod:`~llmops.models.router` resolves a *task alias* (``reason``, ``bulk``, ...) to a
  concrete Azure deployment for the running environment.
* :mod:`~llmops.models.pricing` turns token usage into USD using an indicative price table.
* :mod:`~llmops.models.client` is the async wrapper over Azure OpenAI that ties them
  together, emits a tracing span, and returns a :class:`~llmops.common.types.ChatResult`.
"""

from __future__ import annotations

from llmops.models.client import ModelClient
from llmops.models.pricing import PRICES, ModelPrice, cost_usd
from llmops.models.router import ModelRouter

__all__ = ["ModelRouter", "ModelClient", "ModelPrice", "PRICES", "cost_usd"]
