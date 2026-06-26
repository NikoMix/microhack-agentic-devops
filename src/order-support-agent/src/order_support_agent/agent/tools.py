"""Expose the order tools to the Agent Framework as ``FunctionTool`` objects.

The tools close over a single :class:`OrderRepository`, so the same agent code
runs against the in-process fixture repository (tests, offline demos) or, in
production, against the Contoso Orders MCP server — the tool *contract* is
identical either way.
"""

from __future__ import annotations

from typing import Any

from agent_framework import FunctionTool, tool

from order_support_agent.tools import get_order, get_order_history, lookup_inventory
from order_support_agent.tools.domain import OrderRepository


def build_order_toolset(repo: OrderRepository) -> list[FunctionTool]:
    """Build the triage toolset bound to ``repo``.

    Args:
        repo: The repository the tools read from.

    Returns:
        The ``get_order``, ``lookup_inventory`` and ``get_order_history`` tools.
    """

    async def get_order_tool(order_id: str) -> dict[str, Any]:
        """Retrieve a single Contoso order by its id, e.g. '1001'."""
        return await get_order(repo, order_id)

    async def lookup_inventory_tool(sku: str) -> dict[str, Any]:
        """Check current stock for a SKU, e.g. 'SKU-ESP-01'."""
        return await lookup_inventory(repo, sku)

    async def get_order_history_tool(customer_id: str) -> dict[str, Any]:
        """List a customer's recent orders by customer id, e.g. 'C-002'."""
        return await get_order_history(repo, customer_id)

    return [
        tool(
            get_order_tool,
            name="get_order",
            description="Retrieve a single Contoso order (status, lines, shipping) by its id.",
        ),
        tool(
            lookup_inventory_tool,
            name="lookup_inventory",
            description="Check current sellable stock for a SKU before promising a reship.",
        ),
        tool(
            get_order_history_tool,
            name="get_order_history",
            description="List a customer's recent orders to spot repeat issues or fraud signals.",
        ),
    ]
