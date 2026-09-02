# AIA pipeline container image.
#
# IMPORTANT: build from the REPO ROOT so the LLMOps platform is in the build
# context (the pipeline imports it from platform/services/*/src):
#
#   docker build -f "usecases/ai_pipeline 2/Dockerfile" -t aia-pipeline:latest .
#
# Run one step (env from your .env, or --env-file):
#   docker run --rm --env-file "usecases/ai_pipeline 2/.env" \
#       aia-pipeline:latest --program telesales --step summary --date 2025-08-28
FROM python:3.11-slim

WORKDIR /app

# System deps for pyodbc (Azure SQL) + the MS ODBC driver. Skip-able if you
# never run the individual_metrics/kpi steps, but harmless to include.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ unixodbc unixodbc-dev curl gnupg \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# LLMOps platform (fail-open, but include it so observability / model routing /
# guardrails / prompts / eval all work inside the container).
COPY platform/ /platform/
ENV LLMOPS_PLATFORM_ROOT=/platform/services

# Install the usecase (deps first for layer caching).
COPY ["usecases/ai_pipeline 2/requirements.txt", "usecases/ai_pipeline 2/pyproject.toml", "./"]
RUN pip install --no-cache-dir -r requirements.txt pyyaml jsonschema
COPY ["usecases/ai_pipeline 2/", "./"]
RUN pip install --no-cache-dir -e .

# Defaults — override at run time. mock keeps it self-contained until real Azure
# creds are provided; jsonl writes traces to /app/traces.
ENV AI_PIPELINE_MODE=mock \
    AI_PIPELINE_ENV=dev \
    AI_PIPELINE_TRACER=jsonl

ENTRYPOINT ["python", "-m", "ai_pipeline.main"]
CMD ["--program", "telesales", "--step", "summary"]
