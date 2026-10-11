"""Shared fixtures for the Orders MCP test-suite."""

from __future__ import annotations

import pytest

from contoso_orders_mcp.repository import InMemoryOrderRepository

_CONTRACT_ENV_VARS = (
    "ORDERS_MCP_TRANSPORT",
    "ORDERS_MCP_HOST",
    "ORDERS_MCP_PORT",
    "ORDERS_MCP_API_BASE_URL",
    "ORDERS_MCP_API_SCOPE",
    "ORDERS_MCP_REQUEST_TIMEOUT_SECONDS",
    "ORDERS_MCP_KEY_VAULT_URI",
    "ORDERS_MCP_LOG_LEVEL",
)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear ``ORDERS_MCP_*`` so settings tests are deterministic on any host."""
    for name in _CONTRACT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def repo() -> InMemoryOrderRepository:
    """An in-memory repository seeded from the packaged fixtures."""
    return InMemoryOrderRepository.from_packaged_data()
