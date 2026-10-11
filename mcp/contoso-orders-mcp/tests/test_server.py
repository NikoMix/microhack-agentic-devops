"""Tests for the FastMCP server wiring.

Behaviour is covered by ``test_tools`` / ``test_repository``; here we assert that
all three tools are registered with the expected, well-formed input schemas. We
use ``list_tools`` (stable, fully typed) rather than ``call_tool`` (whose declared
return type does not match its runtime tuple).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contoso_orders_mcp.config import ServerSettings
from contoso_orders_mcp.server import create_server

if TYPE_CHECKING:
    from contoso_orders_mcp.repository import InMemoryOrderRepository

_EXPECTED_TOOLS = {"get_order", "get_order_history", "lookup_inventory"}


async def test_registers_three_tools(repo: InMemoryOrderRepository) -> None:
    server = create_server(settings=ServerSettings(), repository=repo)
    listed = await server.list_tools()
    assert {tool.name for tool in listed} == _EXPECTED_TOOLS


async def test_get_order_tool_schema(repo: InMemoryOrderRepository) -> None:
    server = create_server(settings=ServerSettings(), repository=repo)
    by_name = {tool.name: tool for tool in await server.list_tools()}
    schema = by_name["get_order"].inputSchema
    assert "order_id" in schema["properties"]
    assert schema["required"] == ["order_id"]


async def test_history_tool_has_optional_limit(repo: InMemoryOrderRepository) -> None:
    server = create_server(settings=ServerSettings(), repository=repo)
    by_name = {tool.name: tool for tool in await server.list_tools()}
    schema = by_name["get_order_history"].inputSchema
    assert "customer_id" in schema["properties"]
    assert "limit" in schema["properties"]
    assert schema["required"] == ["customer_id"]
