"""Tests for the typed settings / env contract."""

from __future__ import annotations

from order_support_agent.config import InferenceProvider, Settings


def test_defaults_match_env_contract() -> None:
    settings = Settings()
    assert settings.inference_provider is InferenceProvider.GITHUB_MODELS
    assert settings.github_models_endpoint == "https://models.github.ai/inference"
    assert settings.github_models_model == "openai/gpt-4o-mini"
    assert settings.azure_openai_chat_deployment == "gpt-4o-mini"
    assert settings.azure_openai_api_version == "2024-10-21"
    assert settings.azure_ai_foundry_chat_deployment == "gpt-4o-mini"


def test_active_model_tracks_provider() -> None:
    assert (
        Settings(inference_provider=InferenceProvider.GITHUB_MODELS).active_model
        == "openai/gpt-4o-mini"
    )
    assert (
        Settings(
            inference_provider=InferenceProvider.AZURE_OPENAI,
            azure_openai_chat_deployment="gpt-4o",
        ).active_model
        == "gpt-4o"
    )
    assert (
        Settings(
            inference_provider=InferenceProvider.FOUNDRY,
            azure_ai_foundry_chat_deployment="phi-4",
        ).active_model
        == "phi-4"
    )


def test_azure_monitor_requires_connection_string() -> None:
    enabled_but_unset = Settings(enable_azure_monitor=True)
    assert enabled_but_unset.azure_monitor_enabled is False

    configured = Settings(
        enable_azure_monitor=True,
        applicationinsights_connection_string="InstrumentationKey=00000000-0000-0000-0000-000000000000",
    )
    assert configured.azure_monitor_enabled is True


def test_describe_is_redaction_safe() -> None:
    settings = Settings(
        github_token="super-secret-token",
    )
    description = settings.describe()
    assert "super-secret-token" not in description
    assert "provider=github_models" in description
