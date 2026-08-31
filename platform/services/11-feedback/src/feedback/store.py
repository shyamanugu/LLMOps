"""Feedback storage interface. `InMemoryFeedbackStore` is for tests;
`JsonlFileFeedbackStore` is a zero-Azure default, good enough for a single
usecase's local/dev use; `AzureBlobFeedbackStore` (blob_store.py) is the
real backend once a usecase is live and needs shared, durable storage.
"""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Protocol

from .types import FeedbackEvent


class FeedbackStore(Protocol):
    def record(self, event: FeedbackEvent) -> None:
        ...

    def list_for_session(self, session_id: str) -> List[FeedbackEvent]:
        ...


@dataclass
class InMemoryFeedbackStore:
    events: List[FeedbackEvent] = field(default_factory=list)

    def record(self, event: FeedbackEvent) -> None:
        self.events.append(event)

    def list_for_session(self, session_id: str) -> List[FeedbackEvent]:
        return [e for e in self.events if e.session_id == session_id]


@dataclass
class JsonlFileFeedbackStore:
    path: Path

    def record(self, event: FeedbackEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def list_for_session(self, session_id: str) -> List[FeedbackEvent]:
        if not self.path.exists():
            return []
        events = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                if raw.get("session_id") == session_id:
                    events.append(FeedbackEvent(**raw))
        return events
