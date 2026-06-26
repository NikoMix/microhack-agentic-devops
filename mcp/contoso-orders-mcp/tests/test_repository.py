"""Tests for the order repositories."""

from __future__ import annotations

from contoso_orders_mcp.config import ServerSettings
from contoso_orders_mcp.repository import (
    AzureOrdersRepository,
    InMemoryOrderRepository,
    build_repository,
)


async def test_get_order_found(repo: InMemoryOrderRepository) -> None:
    order = await repo.get_order("1001")
    assert order is not None
    assert order.customer_id == "C-001"
    assert str(order.total) == "499.00"


async def test_get_order_missing(repo: InMemoryOrderRepository) -> None:
    assert await repo.get_order("9999") is None


async def test_lookup_inventory(repo: InMemoryOrderRepository) -> None:
    record = await repo.lookup_inventory("SKU-CUP-04")
    assert record is not None
    assert record.sellable == 0


async def test_history_newest_first(repo: InMemoryOrderRepository) -> None:
    orders = await repo.get_order_history("C-002")
    assert [order.order_id for order in orders] == ["1002", "1003"]


async def test_history_limit(repo: InMemoryOrderRepository) -> None:
    orders = await repo.get_order_history("C-002", limit=1)
    assert len(orders) == 1
    assert orders[0].order_id == "1002"


def test_build_repository_uses_fixtures() -> None:
    built = build_repository(ServerSettings())
    assert isinstance(built, InMemoryOrderRepository)


async def test_build_repository_live_path() -> None:
    built = build_repository(ServerSettings(api_base_url="https://orders.example.invalid"))
    assert isinstance(built, AzureOrdersRepository)
    await built.aclose()
