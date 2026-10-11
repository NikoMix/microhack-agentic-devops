"""Tests for :class:`ServerSettings`."""

from __future__ import annotations

import pytest

from contoso_orders_mcp.config import ServerSettings, Transport


def test_defaults() -> None:
    settings = ServerSettings()
    assert settings.transport is Transport.STDIO
    assert settings.live_mode is False
    assert "fixtures" in settings.describe()


def test_live_mode_when_api_configured() -> None:
    settings = ServerSettings(api_base_url="https://orders.example.invalid")
    assert settings.live_mode is True
    assert "live:" in settings.describe()


def test_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORDERS_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("ORDERS_MCP_PORT", "9000")
    settings = ServerSettings()
    assert settings.transport is Transport.STREAMABLE_HTTP
    assert settings.port == 9000
