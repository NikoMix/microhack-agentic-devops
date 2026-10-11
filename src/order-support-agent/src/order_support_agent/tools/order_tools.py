"""Pure, framework-agnostic implementations of the order tools.

Each function takes an :class:`OrderRepository` and returns a JSON-serializable
``dict`` — the same shape the Contoso Orders MCP server returns for the matching
tool. Keeping these free of any agent framework makes them trivial to unit-test
and lets the MCP server and the in-process agent share one contract.
"""

from __future__ import annotations

from typing import Any

from order_support_agent.tools.domain import OrderRepository


def _order_to_dict(order: Any) -> dict[str, Any]:
    payload: dict[str, Any] = order.model_dump(mode="json")
    payload["total"] = f"{order.total:.2f}"
    return payload


async def get_order(repo: OrderRepository, order_id: str) -> dict[str, Any]:
    """Look up a single order by its identifier.

    Args:
        repo: The backing order repository.
        order_id: The order identifier, e.g. ``"1001"``.

    Returns:
        A dict with ``found`` and either the order fields or an ``error``.
    """
    order = await repo.get_order(order_id)
    if order is None:
        return {"found": False, "order_id": order_id, "error": "Order not found."}
    return {"found": True, **_order_to_dict(order)}


async def lookup_inventory(repo: OrderRepository, sku: str) -> dict[str, Any]:
    """Look up the stock position for a SKU.

    Args:
        repo: The backing order repository.
        sku: The stock-keeping unit, e.g. ``"SKU-ESP-01"``.

    Returns:
        A dict with ``found`` and either the inventory fields (including
        ``sellable``) or an ``error``.
    """
    record = await repo.lookup_inventory(sku)
    if record is None:
        return {"found": False, "sku": sku, "error": "SKU not found."}
    return {"found": True, **record.model_dump(mode="json"), "sellable": record.sellable}


async def get_order_history(
    repo: OrderRepository, customer_id: str, *, limit: int = 10
) -> dict[str, Any]:
    """List a customer's recent orders, newest first.

    Args:
        repo: The backing order repository.
        customer_id: The customer identifier, e.g. ``"C-002"``.
        limit: Maximum number of orders to return (1-50).

    Returns:
        A dict with ``customer_id``, ``count`` and an ``orders`` list.
    """
    capped = max(1, min(limit, 50))
    orders = await repo.get_order_history(customer_id, limit=capped)
    return {
        "customer_id": customer_id,
        "count": len(orders),
        "orders": [_order_to_dict(order) for order in orders],
    }
