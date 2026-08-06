# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# Multi-stage image for the LLMOps backend (FastAPI + uvicorn).
# - Stage 1 builds a wheel-based virtualenv (kept out of the final image).
# - Stage 2 is a slim, non-root runtime with only the venv + source.
# Secure by default: runs as an unprivileged user, no build toolchain in runtime,
# no secrets baked in (all config via env / Managed Identity at runtime).
# ---------------------------------------------------------------------------

ARG PYTHON_VERSION=3.11

# ----------------------------- builder -------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Build tooling only needed to compile any wheels (e.g. presidio deps).
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

# Create an isolated virtualenv we copy wholesale into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies first (better layer caching), then the package.
COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copy source and install the package itself (src layout, root = llmops).
COPY src ./src
RUN pip install --no-deps .

# ----------------------------- runtime -------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

# Runtime env: unbuffered logs, venv on PATH, app settings via LLMOPS_* env.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    LLMOPS_ENVIRONMENT=prod

# Create a dedicated non-root user/group.
RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --home /app --no-create-home app

WORKDIR /app

# Copy the prepared virtualenv and application source from the builder.
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app src ./src
# Model catalog / tool registry / evaluators are read at runtime from ./platform.
# Mount or bake as appropriate; kept optional so the image stays config-light.
# COPY --chown=app:app ../platform ./platform   # TODO(build-context): include if building from repo root

# Install curl for the container healthcheck, then drop privileges.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

USER app

EXPOSE 8000

# Liveness/readiness — matches GET /api/v1/health in the FastAPI app.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" || exit 1

# Production server. Single worker per container; scale out via Container Apps
# replicas rather than in-process workers (keeps tracing/state predictable).
CMD ["sh", "-c", "uvicorn llmops.api.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
