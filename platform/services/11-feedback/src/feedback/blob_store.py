"""Azure Blob Storage backend — appends each feedback event as one JSON
line to a single append blob per environment (e.g. `feedback/dev.jsonl`).
Reads credentials from AZURE_STORAGE_CONNECTION_STRING (see .env.local —
never commit a real value to .env).

Not exercised against a live resource by the automated test suite — same
posture as every other real-Azure backend in this platform (`AzureAISearchBackend`,
`AzureSpeechBackend`, `AzureContentSafetyBackend`). The SDK is imported
lazily, inside `__post_init__`, so a usecase using only `InMemoryFeedbackStore`
or `JsonlFileFeedbackStore` doesn't need it installed.
"""
import json
import os
from dataclasses import asdict, dataclass
from typing import List

from .types import FeedbackEvent


@dataclass
class AzureBlobFeedbackStore:
    container_name: str
    blob_name: str

    def __post_init__(self) -> None:
        from azure.storage.blob import AppendBlobClient

        self._client = AppendBlobClient.from_connection_string(
            conn_str=os.environ["AZURE_STORAGE_CONNECTION_STRING"],
            container_name=self.container_name,
            blob_name=self.blob_name,
        )
        if not self._client.exists():
            self._client.create_append_blob()

    def record(self, event: FeedbackEvent) -> None:
        self._client.append_block(json.dumps(asdict(event)) + "\n")

    def list_for_session(self, session_id: str) -> List[FeedbackEvent]:
        raw_bytes = self._client.download_blob().readall()
        events = []
        for line in raw_bytes.decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            if raw.get("session_id") == session_id:
                events.append(FeedbackEvent(**raw))
        return events
