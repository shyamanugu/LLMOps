"""Integration test for the API health endpoint.

Marked ``integration`` per ARCHITECTURE_SPEC §0, but it needs no live Azure — it exercises
the FastAPI app in-process to prove the control plane boots, routers mount, and the
health/error wiring works. This is the smoke test ``deploy.yml`` can run against a running
container by swapping the ``TestClient`` for an HTTP call.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from llmops import __version__
from llmops.api.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return a TestClient over a freshly-built app (runs lifespan startup/shutdown)."""
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_at_root(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["environment"] in {"dev", "test", "prod"}


def test_health_under_versioned_prefix(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_trace_id_header_present(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.headers.get("x-trace-id")


def test_models_endpoint_returns_aliases_or_placeholder(client: TestClient) -> None:
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["source"] in {"models.yaml", "placeholder"}


def test_usecases_endpoint_ok(client: TestClient) -> None:
    resp = client.get("/api/v1/usecases")
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_feedback_capture_roundtrip(client: TestClient) -> None:
    payload = {"trace_id": "abc123", "kind": "thumbs", "value": True}
    resp = client.post("/api/v1/feedback", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["trace_id"] == "abc123"
    # A thumbs event is not promotable to a golden candidate.
    assert body["golden_candidate_id"] is None
