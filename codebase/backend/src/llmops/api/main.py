"""FastAPI application factory — the LLMOps control plane (console backend).

Wires together CORS, structured exception handling (mapping the platform's
:class:`~llmops.common.errors.LLMOpsError` hierarchy to stable JSON), an OpenTelemetry
request middleware, and the versioned resource routers under ``/api/v1``. Tracing and
settings are initialised in the lifespan handler so the app is observable from the first
request (everything observable; twelve-factor config).
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from llmops import __version__
from llmops.api.routers import (
    agents,
    costs,
    evaluations,
    feedback,
    guardrails,
    health,
    models,
    prompts,
    traces,
    usecases,
)
from llmops.common.errors import LLMOpsError
from llmops.common.ids import new_trace_id
from llmops.common.logging import configure_logging, get_logger
from llmops.config.settings import get_settings

_log = get_logger(__name__)

_API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise settings, logging, and tracing on startup; flush on shutdown."""
    settings = get_settings()
    configure_logging(settings.log_level)
    _log.info("starting llmops api", version=__version__, environment=settings.environment)

    # TODO(wiring): initialise tracing exporters (App Insights + Langfuse) from settings.
    try:
        from llmops.observability.tracing import init_tracing  # type: ignore[import-not-found]

        init_tracing(settings)
        _log.info("tracing initialised")
    except Exception as exc:  # noqa: BLE001 - observability must never block boot
        _log.warning("tracing not initialised (dev/offline)", error=str(exc))

    yield

    _log.info("shutting down llmops api")


class TracingMiddleware(BaseHTTPMiddleware):
    """Assign/propagate a trace id per request and record latency.

    A real OpenTelemetry ``request`` span is opened when the observability package is
    available; otherwise this still stamps ``x-trace-id`` and logs request latency so the
    control plane remains observable in dev.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        """Wrap each request in a trace context."""
        trace_id = request.headers.get("x-trace-id") or new_trace_id()
        request.state.trace_id = trace_id
        start = time.perf_counter()
        try:
            from llmops.observability.tracing import span  # type: ignore[import-not-found]

            with span("request", **{"http.method": request.method, "http.route": request.url.path}):
                response = await call_next(request)
        except ImportError:
            response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["x-trace-id"] = trace_id
        _log.info(
            "request handled",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=duration_ms,
            trace_id=trace_id,
        )
        return response


def _install_exception_handlers(app: FastAPI) -> None:
    """Map platform + unexpected errors to stable JSON responses."""

    @app.exception_handler(LLMOpsError)
    async def _handle_llmops_error(request: Request, exc: LLMOpsError) -> JSONResponse:
        _log.warning(
            "handled platform error",
            code=exc.code,
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(status_code=exc.http_status, content={"error": exc.to_dict()})

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        _log.error("unhandled error", error=str(exc), path=request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "internal server error", "detail": {}}},
        )


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Returns:
        A fully-wired :class:`fastapi.FastAPI` instance.
    """
    settings = get_settings()
    app = FastAPI(
        title="LLMOps Platform API",
        version=__version__,
        description="Control plane for the reusable LLMOps platform (console backend).",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TracingMiddleware)
    _install_exception_handlers(app)

    # Health lives at the app root as well as under the versioned prefix.
    app.include_router(health.router, prefix=_API_PREFIX, tags=["health"])
    app.include_router(health.router, tags=["health"])
    app.include_router(prompts.router, prefix=_API_PREFIX, tags=["prompts"])
    app.include_router(models.router, prefix=_API_PREFIX, tags=["models"])
    app.include_router(evaluations.router, prefix=_API_PREFIX, tags=["evaluations"])
    app.include_router(traces.router, prefix=_API_PREFIX, tags=["traces"])
    app.include_router(costs.router, prefix=_API_PREFIX, tags=["costs"])
    app.include_router(feedback.router, prefix=_API_PREFIX, tags=["feedback"])
    app.include_router(agents.router, prefix=_API_PREFIX, tags=["agents"])
    app.include_router(guardrails.router, prefix=_API_PREFIX, tags=["guardrails"])
    app.include_router(usecases.router, prefix=_API_PREFIX, tags=["usecases"])

    _log.info("fastapi app created", routes=len(app.routes))
    return app


app = create_app()
