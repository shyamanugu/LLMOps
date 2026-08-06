"""Indicative Azure OpenAI pricing and cost computation.

Prices are expressed **per 1,000,000 tokens** (USD), matching how Azure OpenAI publishes
them. The figures below are the *indicative* prices from the v2 deck and MUST be reviewed
against your Azure agreement before they drive billing — hence they live in one table,
keyed by deployment/model name, and are easy to audit.

Rule of thumb from the deck: ``gpt-5.2`` is the premium reasoning model (~$5 in / $30 out
per 1M tokens); ``gpt-5-mini`` is materially cheaper for high-volume steps; embeddings are
priced on input tokens only.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from llmops.common.logging import get_logger
from llmops.common.types import Usage

logger = get_logger(__name__)


class ModelPrice(BaseModel):
    """Per-million-token pricing for one model/deployment.

    Attributes:
        input_per_1m: USD per 1M input (prompt) tokens.
        output_per_1m: USD per 1M output (completion) tokens. Zero for embeddings.
        is_embedding: Whether the model is an embedding model (output priced at 0).
    """

    input_per_1m: float = Field(ge=0.0)
    output_per_1m: float = Field(default=0.0, ge=0.0)
    is_embedding: bool = False

    def cost(self, usage: Usage) -> float:
        """Return the USD cost for ``usage`` under this price."""
        return (usage.input_tokens / 1_000_000.0) * self.input_per_1m + (
            usage.output_tokens / 1_000_000.0
        ) * self.output_per_1m


# Keyed by the deployment / model name as it appears in ``platform/models.yaml``.
# Indicative prices (USD per 1M tokens) — review before production use.
PRICES: dict[str, ModelPrice] = {
    # Premium multi-step reasoning.
    "gpt-5.2": ModelPrice(input_per_1m=5.0, output_per_1m=30.0),
    # High-volume, simpler steps and LLM-as-judge — materially cheaper.
    "gpt-5-mini": ModelPrice(input_per_1m=0.25, output_per_1m=2.0),
    # Real-time speech-to-speech (indicative text-token pricing).
    "gpt-realtime-1.5": ModelPrice(input_per_1m=4.0, output_per_1m=16.0),
    # Embeddings — input tokens only.
    "text-embedding-3-large": ModelPrice(input_per_1m=0.13, is_embedding=True),
    "text-embedding-3-small": ModelPrice(input_per_1m=0.02, is_embedding=True),
}


def cost_usd(deployment: str, usage: Usage) -> float:
    """Compute the USD cost of a call to ``deployment`` given ``usage``.

    Unknown deployments cost ``0.0`` and log a warning rather than raising, so an
    unpriced model never breaks a request path — the gap is visible in logs and can be
    corrected in :data:`PRICES`.

    Args:
        deployment: The resolved Azure deployment/model name.
        usage: Token usage for the call.

    Returns:
        Cost in USD, rounded to 6 decimal places.
    """
    price = PRICES.get(deployment)
    if price is None:
        logger.warning("no price entry for deployment; costing as 0", deployment=deployment)
        return 0.0
    return round(price.cost(usage), 6)
