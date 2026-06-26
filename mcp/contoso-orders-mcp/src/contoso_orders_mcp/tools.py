"""Pure, framework-agnostic implementations of the order tools.

Each function takes an :class:`OrderRepository` and returns a JSON-serializable
``dict``. Keeping them free of any MCP/server types makes them trivial to
unit-test and lets the server register thin wrappers over them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contoso_orders_mcp.models import Order
    from contoso_orders_mcp.repository import OrderRepository

_MAX_HISTORY = 50


def _order_to_dict(order: Order) -> dict[str, Any]:
    payload: dict[str, Any] = order.model_dump(mode="json")
    payload["total"] = f"{order.total:.2f}"
    return payload


async def get_order(repo: OrderRepository, order_id: str) -> dict[str, Any]:
    """Look up a single order by its identifier."""
    order = await repo.get_order(order_id)
    if order is None:
        return {"found": False, "order_id": order_id, "error": "Order not found."}
    return {"found": True, **_order_to_dict(order)}


async def lookup_inventory(repo: OrderRepository, sku: str) -> dict[str, Any]:
    """Look up the stock position for a SKU."""
    record = await repo.lookup_inventory(sku)
    if record is None:
        return {"found": False, "sku": sku, "error": "SKU not found."}
    return {"found": True, **record.model_dump(mode="json"), "sellable": record.sellable}


async def get_order_history(
    repo: OrderRepository, customer_id: str, *, limit: int = 10
) -> dict[str, Any]:
    """List a customer's recent orders, newest first."""
    capped = max(1, min(limit, _MAX_HISTORY))
    orders = await repo.get_order_history(customer_id, limit=capped)
    return {
        "customer_id": customer_id,
        "count": len(orders),
        "orders": [_order_to_dict(order) for order in orders],
    }
