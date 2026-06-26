"""Data access for the Orders MCP tools.

Two interchangeable backends implement one :class:`OrderRepository` protocol:

* :class:`InMemoryOrderRepository` — deterministic fixtures shipped with the
  package; the default so the server runs offline with zero configuration.
* :class:`AzureOrdersRepository` — the live path. It calls a downstream Orders
  API using a **bearer token from a managed identity** (``DefaultAzureCredential``)
  with **no keys**, and is the single documented egress target.

``build_repository`` picks the backend from configuration, so swapping fixtures
for the live API is a deployment change, not a code change.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

import httpx
from azure.identity.aio import DefaultAzureCredential

from contoso_orders_mcp.models import InventoryRecord, Order

if TYPE_CHECKING:
    from collections.abc import Iterable

    from contoso_orders_mcp.config import ServerSettings


@runtime_checkable
class OrderRepository(Protocol):
    """Read-only data access the order tools depend on."""

    async def get_order(self, order_id: str) -> Order | None:
        """Return the order with ``order_id`` or ``None`` if unknown."""
        ...

    async def lookup_inventory(self, sku: str) -> InventoryRecord | None:
        """Return the inventory record for ``sku`` or ``None`` if unknown."""
        ...

    async def get_order_history(self, customer_id: str, *, limit: int = 10) -> tuple[Order, ...]:
        """Return up to ``limit`` of a customer's orders, newest first."""
        ...

    async def aclose(self) -> None:
        """Release any held resources."""
        ...


class InMemoryOrderRepository:
    """A deterministic :class:`OrderRepository` seeded from packaged fixtures."""

    def __init__(self, orders: Iterable[Order], inventory: Iterable[InventoryRecord]) -> None:
        self._orders = {order.order_id: order for order in orders}
        self._inventory = {record.sku: record for record in inventory}

    @classmethod
    def from_packaged_data(cls) -> Self:
        """Build the repository from the JSON fixtures shipped in ``data/``."""
        data = files("contoso_orders_mcp.data")
        orders_raw = json.loads((data / "orders.json").read_text(encoding="utf-8"))
        inventory_raw = json.loads((data / "inventory.json").read_text(encoding="utf-8"))
        orders = [Order.model_validate(item) for item in orders_raw]
        inventory = [InventoryRecord.model_validate(item) for item in inventory_raw]
        return cls(orders, inventory)

    async def get_order(self, order_id: str) -> Order | None:
        """Return the order with ``order_id`` or ``None`` if unknown."""
        return self._orders.get(order_id)

    async def lookup_inventory(self, sku: str) -> InventoryRecord | None:
        """Return the inventory record for ``sku`` or ``None`` if unknown."""
        return self._inventory.get(sku)

    async def get_order_history(self, customer_id: str, *, limit: int = 10) -> tuple[Order, ...]:
        """Return up to ``limit`` of a customer's orders, newest first."""
        owned = [order for order in self._orders.values() if order.customer_id == customer_id]
        owned.sort(key=lambda order: order.placed_at, reverse=True)
        return tuple(owned[:limit])

    async def aclose(self) -> None:
        """No-op — fixtures hold no external resources."""


class AzureOrdersRepository:
    """Live :class:`OrderRepository` backed by the downstream Orders API.

    Authenticates with a managed identity (``DefaultAzureCredential``) and sends a
    short-lived bearer token on every request — no API keys are stored or sent.
    """

    def __init__(self, *, base_url: str, scope: str, timeout: float) -> None:
        self._scope = scope
        self._credential = DefaultAzureCredential()
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)

    async def _auth_headers(self) -> dict[str, str]:
        token = await self._credential.get_token(self._scope)
        return {"Authorization": f"Bearer {token.token}"}

    async def get_order(self, order_id: str) -> Order | None:
        """Fetch a single order from the Orders API."""
        response = await self._client.get(f"/orders/{order_id}", headers=await self._auth_headers())
        if response.status_code == httpx.codes.NOT_FOUND:
            return None
        response.raise_for_status()
        return Order.model_validate(response.json())

    async def lookup_inventory(self, sku: str) -> InventoryRecord | None:
        """Fetch a SKU's inventory record from the Orders API."""
        response = await self._client.get(f"/inventory/{sku}", headers=await self._auth_headers())
        if response.status_code == httpx.codes.NOT_FOUND:
            return None
        response.raise_for_status()
        return InventoryRecord.model_validate(response.json())

    async def get_order_history(self, customer_id: str, *, limit: int = 10) -> tuple[Order, ...]:
        """Fetch a customer's recent orders from the Orders API."""
        response = await self._client.get(
            f"/customers/{customer_id}/orders",
            params={"limit": limit},
            headers=await self._auth_headers(),
        )
        response.raise_for_status()
        payload = response.json()
        return tuple(Order.model_validate(item) for item in payload)

    async def aclose(self) -> None:
        """Close the HTTP client and the credential."""
        await self._client.aclose()
        await self._credential.close()


def build_repository(settings: ServerSettings) -> OrderRepository:
    """Return the configured repository: live Azure path or packaged fixtures."""
    if settings.api_base_url:
        return AzureOrdersRepository(
            base_url=settings.api_base_url,
            scope=settings.api_scope,
            timeout=settings.request_timeout_seconds,
        )
    return InMemoryOrderRepository.from_packaged_data()
