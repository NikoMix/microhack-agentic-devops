"""Tests for the pure order-tool implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from contoso_orders_mcp import tools

if TYPE_CHECKING:
    from contoso_orders_mcp.repository import InMemoryOrderRepository


async def test_get_order_found(repo: InMemoryOrderRepository) -> None:
    result = await tools.get_order(repo, "1001")
    assert result["found"] is True
    assert result["order_id"] == "1001"
    assert result["total"] == "499.00"
    assert result["status"] == "delayed"


async def test_get_order_missing(repo: InMemoryOrderRepository) -> None:
    result = await tools.get_order(repo, "9999")
    assert result["found"] is False
    assert "error" in result


async def test_lookup_inventory_found(repo: InMemoryOrderRepository) -> None:
    result = await tools.lookup_inventory(repo, "SKU-GRD-02")
    assert result["found"] is True
    assert result["sellable"] == 32
    assert result["available"] == 40


async def test_lookup_inventory_missing(repo: InMemoryOrderRepository) -> None:
    result = await tools.lookup_inventory(repo, "SKU-NOPE")
    assert result["found"] is False


async def test_order_history_newest_first(repo: InMemoryOrderRepository) -> None:
    result = await tools.get_order_history(repo, "C-002")
    assert result["count"] == 2
    assert [order["order_id"] for order in result["orders"]] == ["1002", "1003"]


async def test_order_history_limit(repo: InMemoryOrderRepository) -> None:
    result = await tools.get_order_history(repo, "C-002", limit=1)
    assert result["count"] == 1
    assert result["orders"][0]["order_id"] == "1002"


async def test_order_history_limit_capped(repo: InMemoryOrderRepository) -> None:
    result = await tools.get_order_history(repo, "C-002", limit=999)
    assert result["count"] == 2
