"""Unit tests for :mod:`llmops.models.pricing` (pure cost math)."""

from __future__ import annotations

from llmops.common.types import Usage
from llmops.models.pricing import PRICES, ModelPrice, cost_usd


def test_price_table_has_deck_models() -> None:
    assert "gpt-5.2" in PRICES
    assert "gpt-5-mini" in PRICES
    assert "text-embedding-3-large" in PRICES


def test_gpt52_is_premium_priced() -> None:
    assert PRICES["gpt-5.2"].input_per_1m == 5.0
    assert PRICES["gpt-5.2"].output_per_1m == 30.0


def test_mini_is_cheaper_than_reason_model() -> None:
    assert PRICES["gpt-5-mini"].input_per_1m < PRICES["gpt-5.2"].input_per_1m
    assert PRICES["gpt-5-mini"].output_per_1m < PRICES["gpt-5.2"].output_per_1m


def test_cost_for_one_million_tokens_each() -> None:
    usage = Usage(input_tokens=1_000_000, output_tokens=1_000_000)
    # 5 (input) + 30 (output) = 35 USD.
    assert cost_usd("gpt-5.2", usage) == 35.0


def test_cost_scales_linearly() -> None:
    usage = Usage(input_tokens=500_000, output_tokens=100_000)
    # 0.5 * 5 + 0.1 * 30 = 2.5 + 3.0 = 5.5
    assert cost_usd("gpt-5.2", usage) == 5.5


def test_embedding_output_is_free() -> None:
    price: ModelPrice = PRICES["text-embedding-3-large"]
    assert price.is_embedding is True
    usage = Usage(input_tokens=1_000_000, output_tokens=999)
    # Output tokens must not contribute for embeddings.
    assert cost_usd("text-embedding-3-large", usage) == round(price.input_per_1m, 6)


def test_unknown_deployment_costs_zero() -> None:
    usage = Usage(input_tokens=1000, output_tokens=1000)
    assert cost_usd("mystery-model", usage) == 0.0


def test_zero_usage_costs_zero() -> None:
    assert cost_usd("gpt-5.2", Usage()) == 0.0
