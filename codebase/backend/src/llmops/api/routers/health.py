"""Health router — liveness/readiness for probes and the console."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from llmops import __version__
from llmops.api.deps import SettingsDep

router = APIRouter()


class HealthResponse(BaseModel):
    """Liveness/readiness payload."""

    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse, summary="Liveness/readiness")
async def health(settings: SettingsDep) -> HealthResponse:
    """Return service health.

    Always reports ``ok`` when the process is serving; the ``environment`` and ``version``
    let the console and deploy checks confirm what is running.
    """
    return HealthResponse(status="ok", version=__version__, environment=settings.environment)
