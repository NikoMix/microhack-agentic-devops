"""Typed configuration for the Order Support agent.

All runtime configuration is sourced from environment variables (or an optional
``.env`` file) so the same image runs unchanged across providers. The
:class:`InferenceProvider` selection is the single switch that swaps the model
backend — see :mod:`order_support_agent.inference.factory`.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InferenceProvider(StrEnum):
    """Supported, env-selectable inference backends (chat/text only)."""

    FOUNDRY = "foundry"
    AZURE_OPENAI = "azure_openai"
    GITHUB_MODELS = "github_models"


class Settings(BaseSettings):
    """Strongly typed settings honoring the modular-inference env contract.

    Field names map 1:1 to the upper-cased environment variables documented in
    ``.env.example`` (for example ``inference_provider`` ⇐ ``INFERENCE_PROVIDER``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- provider selection -------------------------------------------------
    inference_provider: InferenceProvider = InferenceProvider.GITHUB_MODELS

    # ----- GitHub Models (zero Azure cost; only needs GITHUB_TOKEN) -----------
    github_models_endpoint: str = "https://models.github.ai/inference"
    github_models_model: str = "openai/gpt-4o-mini"
    github_token: str | None = None

    # ----- Azure OpenAI (keyless via Entra) ----------------------------------
    azure_openai_endpoint: str | None = None
    azure_openai_chat_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-10-21"

    # ----- Azure AI Foundry (keyless via Entra) ------------------------------
    azure_ai_foundry_project_endpoint: str | None = None
    azure_ai_foundry_chat_deployment: str = "gpt-4o-mini"

    # ----- generation defaults -----------------------------------------------
    agent_temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.2
    agent_max_tokens: Annotated[int, Field(gt=0, le=16_384)] = 1024
    request_timeout_seconds: Annotated[float, Field(gt=0)] = 60.0

    # ----- observability ------------------------------------------------------
    otel_service_name: str = "order-support-agent"
    applicationinsights_connection_string: str | None = None
    enable_azure_monitor: bool = True
    enable_foundry_tracing: bool = False
    enable_sensitive_telemetry: bool = False

    # ----- MCP integration ----------------------------------------------------
    orders_mcp_url: str | None = None

    def describe(self) -> str:
        """A redaction-safe one-line description of the active configuration."""
        return (
            f"provider={self.inference_provider.value} "
            f"model={self.active_model} "
            f"azure_monitor={'on' if self.azure_monitor_enabled else 'off'}"
        )

    @property
    def active_model(self) -> str:
        """The model/deployment name for the selected provider."""
        match self.inference_provider:
            case InferenceProvider.GITHUB_MODELS:
                return self.github_models_model
            case InferenceProvider.AZURE_OPENAI:
                return self.azure_openai_chat_deployment
            case InferenceProvider.FOUNDRY:
                return self.azure_ai_foundry_chat_deployment

    @property
    def azure_monitor_enabled(self) -> bool:
        """True only when Azure Monitor export is both enabled and configured."""
        return self.enable_azure_monitor and bool(self.applicationinsights_connection_string)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-wide settings (cached). Tests construct ``Settings`` directly."""
    return Settings()
