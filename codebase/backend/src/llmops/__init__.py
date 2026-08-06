"""LLMOps platform — reusable framework for running LLM applications on Azure.

Package layout (see ``ARCHITECTURE_SPEC.md`` at the repo root):
    config/         settings + models.yaml loader
    common/         logging, errors, ids, shared types
    prompts/        prompt registry (Git / Langfuse / Foundry) + rendering
    models/         model router + Azure OpenAI client + pricing
    observability/  OpenTelemetry tracing + cost tracking + exporters
    guardrails/     input/output safety engine (Content Safety, PII, schema, injection)
    data_access/    RAG, SQL/NL2SQL, document extraction, records
    tools/          reusable MCP tool catalog
    orchestration/  sequential pipeline runtime (agents, steps, state)
    evaluation/     golden datasets, metrics, thresholds, the CI gate
    feedback/       capture + improvement loop
    api/            FastAPI control plane (the console's backend)
"""

__version__ = "0.1.0"
