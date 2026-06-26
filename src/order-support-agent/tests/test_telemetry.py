"""Tests for the OpenTelemetry setup helper."""

from __future__ import annotations

import agent_framework.observability as af_obs
import pytest

from order_support_agent.config import Settings
from order_support_agent.telemetry import setup_telemetry

_FAKE_CONNECTION_STRING = "InstrumentationKey=00000000-0000-0000-0000-000000000000"


@pytest.fixture
def patch_instrumentation(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, object]]:
    """Patch Agent Framework instrumentation toggles and record calls."""
    recorded: list[tuple[str, object]] = []
    monkeypatch.setattr(
        af_obs, "enable_instrumentation", lambda **kwargs: recorded.append(("enable", kwargs))
    )
    monkeypatch.setattr(af_obs, "create_resource", lambda **kwargs: ("resource", kwargs))
    monkeypatch.setattr(
        af_obs,
        "configure_otel_providers",
        lambda **kwargs: recorded.append(("console", kwargs)),
    )
    return recorded


def test_setup_telemetry_none_when_unconfigured(
    patch_instrumentation: list[tuple[str, object]],
) -> None:
    settings = Settings(enable_azure_monitor=False)
    assert setup_telemetry(settings) == "none"
    assert ("enable", {"enable_sensitive_data": False}) in patch_instrumentation


def test_setup_telemetry_console(patch_instrumentation: list[tuple[str, object]]) -> None:
    settings = Settings(enable_azure_monitor=False)
    assert setup_telemetry(settings, console=True) == "console"
    assert any(entry[0] == "console" for entry in patch_instrumentation)


def test_setup_telemetry_azure_monitor(
    monkeypatch: pytest.MonkeyPatch,
    patch_instrumentation: list[tuple[str, object]],
) -> None:
    captured: dict[str, object] = {}

    def fake_configure(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(
        "azure.monitor.opentelemetry.configure_azure_monitor", fake_configure, raising=False
    )
    settings = Settings(
        enable_azure_monitor=True,
        applicationinsights_connection_string=_FAKE_CONNECTION_STRING,
    )

    assert setup_telemetry(settings) == "azure_monitor"
    assert captured["connection_string"] == _FAKE_CONNECTION_STRING
