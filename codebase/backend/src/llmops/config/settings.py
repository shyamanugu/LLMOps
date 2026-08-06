"""Application settings (twelve-factor: config from the environment).

All configuration comes from environment variables (prefixed ``LLMOPS_``) or a local
``.env`` file for development. **No secrets are stored in code.** In Azure, secret values
(keys, connection strings) are resolved via Managed Identity + Key Vault references on the
Container App, so the values below are typically endpoints and non-secret settings only.

Usage:
    from llmops.config.settings import get_settings
    settings = get_settings()
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed platform configuration.

    Field names map to ``LLMOPS_<UPPER>`` environment variables. See ``.env.example``.
    """

    model_config = SettingsConfigDict(
        env_prefix="LLMOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- environment / app ---
    environment: str = Field(default="dev", description="dev | test | prod")
    log_level: str = Field(default="INFO")
    service_name: str = Field(default="llmops-platform")

    # --- Azure OpenAI (models) ---
    azure_openai_endpoint: str = Field(default="")
    azure_openai_api_version: str = Field(default="2025-01-01-preview")
    # Auth: prefer Managed Identity. A key may be injected in dev only.
    azure_openai_api_key: str = Field(default="", repr=False)

    # --- Azure AI Search (RAG) ---
    azure_search_endpoint: str = Field(default="")
    azure_search_api_key: str = Field(default="", repr=False)

    # --- Azure AI Document Intelligence ---
    document_intelligence_endpoint: str = Field(default="")

    # --- Content Safety (guardrails) ---
    content_safety_endpoint: str = Field(default="")

    # --- Cosmos DB (state / feedback) ---
    cosmos_endpoint: str = Field(default="")
    cosmos_database: str = Field(default="llmops")

    # --- Observability ---
    applicationinsights_connection_string: str = Field(default="", repr=False)
    langfuse_host: str = Field(default="")
    langfuse_public_key: str = Field(default="", repr=False)
    langfuse_secret_key: str = Field(default="", repr=False)
    otel_enabled: bool = Field(default=True)

    # --- Prompt registry ---
    prompt_registry: str = Field(default="git", description="git | langfuse | foundry")

    # --- Paths (relative to repo root) ---
    models_config_path: str = Field(default="platform/models.yaml")
    usecases_dir: str = Field(default="usecases")

    # --- API ---
    api_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    def is_prod(self) -> bool:
        return self.environment == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
