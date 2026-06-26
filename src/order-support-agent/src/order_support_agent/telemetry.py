"""OpenTelemetry wiring for the Order Support agent.

The Microsoft Agent Framework already emits GenAI spans and metrics from its
telemetry layers; this module turns that instrumentation on and points the
exporters at Azure Monitor (Application Insights). The same OTLP traces surface
in the Azure AI Foundry portal when the connection string belongs to the
project's linked Application Insights resource — that is the "Foundry tracing"
option, optionally auto-discovered via :mod:`azure.ai.projects` when installed.

Telemetry is strictly best-effort: a misconfigured exporter must never crash the
agent, so failures are logged and swallowed.
"""

from __future__ import annotations

import logging

from order_support_agent.config import Settings, get_settings

logger = logging.getLogger(__name__)


def _foundry_connection_string(endpoint: str) -> str | None:
    """Best-effort fetch of a Foundry project's linked App Insights string.

    Requires the optional ``azure-ai-projects`` package. Returns ``None`` (and
    logs) when the package is absent or the lookup fails for any reason.
    """
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        logger.warning(
            "azure-ai-projects is not installed; cannot auto-discover Foundry "
            "tracing. Set APPLICATIONINSIGHTS_CONNECTION_STRING or run "
            "'uv add azure-ai-projects'.",
        )
        return None
    try:
        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=endpoint, credential=credential) as client,
        ):
            connection_string: str = client.telemetry.get_connection_string()
    except Exception:  # telemetry must never crash the agent
        logger.warning("Failed to read Foundry App Insights connection string.", exc_info=True)
        return None
    return connection_string


def _resolve_connection_string(settings: Settings) -> str | None:
    """Pick the Application Insights connection string for the active config."""
    if settings.applicationinsights_connection_string:
        return settings.applicationinsights_connection_string
    if settings.enable_foundry_tracing and settings.azure_ai_foundry_project_endpoint:
        return _foundry_connection_string(settings.azure_ai_foundry_project_endpoint)
    return None


def setup_telemetry(settings: Settings | None = None, *, console: bool = False) -> str:
    """Configure exporters and enable Agent Framework instrumentation.

    Args:
        settings: Configuration. Defaults to :func:`get_settings`.
        console: When no Azure Monitor exporter is configured, emit spans to the
            console instead (useful for local development).

    Returns:
        The exporter that was configured: ``"azure_monitor"``, ``"console"`` or
        ``"none"``.
    """
    resolved = settings or get_settings()
    from agent_framework.observability import (
        create_resource,
        enable_instrumentation,
    )

    connection_string = (
        _resolve_connection_string(resolved) if resolved.enable_azure_monitor else None
    )
    exporter = "none"

    if connection_string:
        try:
            from azure.monitor.opentelemetry import (
                configure_azure_monitor,
            )
        except ImportError:
            logger.warning(
                "azure-monitor-opentelemetry is not installed; skipping Azure Monitor export.",
            )
        else:
            configure_azure_monitor(
                connection_string=connection_string,
                resource=create_resource(service_name=resolved.otel_service_name),
                enable_live_metrics=False,
            )
            exporter = "azure_monitor"

    if exporter == "none" and console:
        from agent_framework.observability import (
            configure_otel_providers,
        )

        configure_otel_providers(enable_console_exporters=True)
        exporter = "console"

    enable_instrumentation(enable_sensitive_data=resolved.enable_sensitive_telemetry)
    logger.info(
        "Telemetry configured (exporter=%s, sensitive_content=%s).",
        exporter,
        resolved.enable_sensitive_telemetry,
    )
    return exporter
