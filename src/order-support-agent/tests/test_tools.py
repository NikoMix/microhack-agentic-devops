"""Tests for the pure order tools and the Agent Framework tool binding."""

from __future__ import annotations

from order_support_agent.agent.tools import build_order_toolset
from order_support_agent.tools import get_order, get_order_history, lookup_inventory
from order_support_agent.tools.domain import InMemoryOrderRepository


async def test_get_order_found(repo: InMemoryOrderRepository) -> None:
    result = await get_order(repo, "1001")
    assert result["found"] is True
    assert result["order_id"] == "1001"
    assert result["status"] == "delayed"
    assert result["total"] == "499.00"


async def test_get_order_missing(repo: InMemoryOrderRepository) -> None:
    result = await get_order(repo, "9999")
    assert result["found"] is False
    assert "error" in result


async def test_lookup_inventory_reports_sellable(repo: InMemoryOrderRepository) -> None:
    result = await lookup_inventory(repo, "SKU-ESP-01")
    assert result["found"] is True
    assert result["sellable"] == 7  # 12 available - 5 reserved


async def test_lookup_inventory_missing(repo: InMemoryOrderRepository) -> None:
    result = await lookup_inventory(repo, "SKU-UNKNOWN")
    assert result["found"] is False


async def test_get_order_history_orders_newest_first(repo: InMemoryOrderRepository) -> None:
    result = await get_order_history(repo, "C-002")
    assert result["count"] == 2
    order_ids = [order["order_id"] for order in result["orders"]]
    assert order_ids == ["1002", "1003"]


async def test_get_order_history_caps_limit(repo: InMemoryOrderRepository) -> None:
    result = await get_order_history(repo, "C-002", limit=1)
    assert result["count"] == 1


def test_build_order_toolset_exposes_three_tools(repo: InMemoryOrderRepository) -> None:
    tools = build_order_toolset(repo)
    names = {tool.name for tool in tools}
    assert names == {"get_order", "lookup_inventory", "get_order_history"}


def test_build_order_toolset_emits_function_schema(repo: InMemoryOrderRepository) -> None:
    get_order_tool = next(tool for tool in build_order_toolset(repo) if tool.name == "get_order")
    spec = get_order_tool.to_json_schema_spec()
    assert spec["type"] == "function"
    assert spec["function"]["name"] == "get_order"
    assert "order_id" in spec["function"]["parameters"]["properties"]
