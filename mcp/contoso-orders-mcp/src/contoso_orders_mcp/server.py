"""The Contoso Orders MCP server.

Exposes three safe, read-only tools — ``get_order``, ``lookup_inventory`` and
``get_order_history`` — over the Model Context Protocol. Tools are thin wrappers
over :mod:`contoso_orders_mcp.tools`, backed by the configured repository
(fixtures by default, or the live managed-identity path).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from contoso_orders_mcp import tools
from contoso_orders_mcp.config import ServerSettings, get_settings
from contoso_orders_mcp.repository import OrderRepository, build_repository

_INSTRUCTIONS = (
    "Contoso Commerce order support tools. Use get_order to fetch an order's status, "
    "carrier and tracking; lookup_inventory to check stock and sellable units for a SKU; "
    "and get_order_history to review a customer's recent orders. All tools are read-only "
    "and return structured JSON. Never invent order ids or SKUs — call a tool to verify."
)


def create_server(
    *,
    settings: ServerSettings | None = None,
    repository: OrderRepository | None = None,
) -> FastMCP:
    """Build the FastMCP server with the order tools registered.

    Args:
        settings: Configuration. Defaults to :func:`get_settings`.
        repository: A repository to back the tools. Defaults to the configured
            backend (fixtures, or the live Orders API path).

    Returns:
        A ready-to-run :class:`~mcp.server.fastmcp.FastMCP` server.
    """
    resolved = settings or get_settings()
    repo = repository or build_repository(resolved)

    server = FastMCP(
        name="contoso-orders",
        instructions=_INSTRUCTIONS,
        host=resolved.host,
        port=resolved.port,
    )

    @server.tool(
        name="get_order",
        title="Get order",
        description="Look up a Contoso Commerce order's status, carrier and tracking by id.",
    )
    async def get_order(order_id: str) -> dict[str, Any]:
        """Look up a single order by its identifier.

        Args:
            order_id: The order identifier, for example ``"1001"``.

        Returns:
            A dict with ``found`` and either the order fields (including ``total``)
            or an ``error`` message.
        """
        return await tools.get_order(repo, order_id)

    @server.tool(
        name="lookup_inventory",
        title="Look up inventory",
        description="Check stock and sellable units for a Contoso Commerce SKU.",
    )
    async def lookup_inventory(sku: str) -> dict[str, Any]:
        """Look up the stock position for a SKU.

        Args:
            sku: The stock-keeping unit, for example ``"SKU-ESP-01"``.

        Returns:
            A dict with ``found`` and either the inventory fields (including
            ``sellable``) or an ``error`` message.
        """
        return await tools.lookup_inventory(repo, sku)

    @server.tool(
        name="get_order_history",
        title="Get order history",
        description="List a customer's recent Contoso Commerce orders, newest first.",
    )
    async def get_order_history(customer_id: str, limit: int = 10) -> dict[str, Any]:
        """List a customer's recent orders, newest first.

        Args:
            customer_id: The customer identifier, for example ``"C-002"``.
            limit: Maximum number of orders to return (1-50).

        Returns:
            A dict with ``customer_id``, ``count`` and an ``orders`` list.
        """
        return await tools.get_order_history(repo, customer_id, limit=limit)

    return server
