"""Fakes standing in for real Azure backends — every test in this component
runs with no network call and no Azure credentials.
"""
from typing import Dict, List, Sequence

from data_tools.types import SearchHit


class FakeSearchBackend:
    """Partitions seeded hits by index_name — the same partitioning
    real Azure AI Search gives for free by having one index per client. A
    search against an index_name with no seeded data returns nothing, it
    never falls back to another index's data."""

    def __init__(self, seed: Dict[str, List[SearchHit]] = None) -> None:
        self._data: Dict[str, List[SearchHit]] = dict(seed or {})

    def search(self, index_name: str, vector: Sequence[float], top_k: int) -> List[SearchHit]:
        return self._data.get(index_name, [])[:top_k]

    def upsert(self, index_name: str, documents) -> None:
        self._data.setdefault(index_name, []).extend(documents)


class FakeEmbeddingProvider:
    def embed(self, deployment: str, texts: Sequence[str]) -> List[List[float]]:
        return [[0.0, 0.0, 0.0] for _ in texts]

    def chat(self, deployment, messages, **kwargs):
        raise NotImplementedError("FakeEmbeddingProvider only supports embed()")


class FakeSpeechBackend:
    def transcribe(self, audio_bytes: bytes) -> str:
        return f"[transcribed {len(audio_bytes)} bytes]"

    def synthesize(self, text: str) -> bytes:
        return f"[audio for: {text}]".encode("utf-8")
