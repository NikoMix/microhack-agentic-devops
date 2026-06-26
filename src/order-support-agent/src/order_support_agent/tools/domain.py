"""In-process order/inventory domain used by the agent's tools.

The agent's tools are deliberately backed by a small, deterministic repository so
the whole triage flow runs offline in tests and demos. In production the same
tool surface is served by the Contoso Orders MCP server (see ``/mcp``), which
fronts the real Orders API using a managed identity — no code in the agent
changes when swapping the in-process repository for the MCP toolset.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

from order_support_agent.models import InventoryRecord, Order, OrderLine, OrderStatus


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


class InMemoryOrderRepository:
    """A deterministic :class:`OrderRepository` seeded from fixtures."""

    def __init__(
        self,
        orders: dict[str, Order],
        inventory: dict[str, InventoryRecord],
    ) -> None:
        self._orders = dict(orders)
        self._inventory = dict(inventory)

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


def _dt(year: int, month: int, day: int, hour: int = 9) -> datetime:
    return datetime(year, month, day, hour, tzinfo=UTC)


def _seed_orders() -> dict[str, Order]:
    orders = (
        Order(
            order_id="1001",
            customer_id="C-001",
            status=OrderStatus.DELAYED,
            placed_at=_dt(2025, 9, 18),
            lines=(
                OrderLine(
                    sku="SKU-ESP-01",
                    description="Contoso Aurora Espresso Machine",
                    quantity=1,
                    unit_price=Decimal("499.00"),
                ),
            ),
            shipping_city="Stockholm",
            carrier="PostNord",
            tracking_number="PN-7781-SE",
            estimated_delivery=_dt(2025, 9, 24),
            notes="Customer reports the parcel has not moved for six days.",
        ),
        Order(
            order_id="1002",
            customer_id="C-002",
            status=OrderStatus.DELIVERED,
            placed_at=_dt(2025, 9, 28),
            lines=(
                OrderLine(
                    sku="SKU-GRD-02",
                    description="Contoso Burr Coffee Grinder",
                    quantity=1,
                    unit_price=Decimal("129.00"),
                ),
                OrderLine(
                    sku="SKU-CUP-04",
                    description="Contoso Ceramic Cup Set (4)",
                    quantity=2,
                    unit_price=Decimal("39.00"),
                ),
            ),
            shipping_city="Gothenburg",
            carrier="DHL",
            tracking_number="DHL-5521-SE",
            estimated_delivery=_dt(2025, 10, 1),
            notes="Customer says one cup arrived shattered.",
        ),
        Order(
            order_id="1003",
            customer_id="C-002",
            status=OrderStatus.DELIVERED,
            placed_at=_dt(2025, 7, 11),
            lines=(
                OrderLine(
                    sku="SKU-BAG-09",
                    description="Contoso Single-Origin Beans 1kg",
                    quantity=3,
                    unit_price=Decimal("24.00"),
                ),
            ),
            shipping_city="Gothenburg",
            carrier="DHL",
            tracking_number="DHL-3390-SE",
            estimated_delivery=_dt(2025, 7, 14),
        ),
        Order(
            order_id="1004",
            customer_id="C-003",
            status=OrderStatus.PAID,
            placed_at=_dt(2025, 10, 3),
            lines=(
                OrderLine(
                    sku="SKU-ESP-01",
                    description="Contoso Aurora Espresso Machine",
                    quantity=4,
                    unit_price=Decimal("499.00"),
                ),
            ),
            shipping_city="Malmo",
            notes="Large first-time order flagged for review by the payments team.",
        ),
        Order(
            order_id="1005",
            customer_id="C-004",
            status=OrderStatus.SHIPPED,
            placed_at=_dt(2025, 10, 2),
            lines=(
                OrderLine(
                    sku="SKU-GRD-02",
                    description="Contoso Burr Coffee Grinder",
                    quantity=1,
                    unit_price=Decimal("129.00"),
                ),
            ),
            shipping_city="Uppsala",
            carrier="PostNord",
            tracking_number="PN-9001-SE",
            estimated_delivery=_dt(2025, 10, 8),
        ),
    )
    return {order.order_id: order for order in orders}


def _seed_inventory() -> dict[str, InventoryRecord]:
    records = (
        InventoryRecord(
            sku="SKU-ESP-01",
            description="Contoso Aurora Espresso Machine",
            available=12,
            reserved=5,
            warehouse="SE-CENTRAL",
            restock_eta=_dt(2025, 10, 20),
        ),
        InventoryRecord(
            sku="SKU-GRD-02",
            description="Contoso Burr Coffee Grinder",
            available=40,
            reserved=8,
            warehouse="SE-CENTRAL",
        ),
        InventoryRecord(
            sku="SKU-CUP-04",
            description="Contoso Ceramic Cup Set (4)",
            available=0,
            reserved=0,
            warehouse="SE-CENTRAL",
            restock_eta=_dt(2025, 10, 16),
        ),
        InventoryRecord(
            sku="SKU-BAG-09",
            description="Contoso Single-Origin Beans 1kg",
            available=220,
            reserved=15,
            warehouse="SE-WEST",
        ),
    )
    return {record.sku: record for record in records}


def default_repository() -> InMemoryOrderRepository:
    """Build the seeded repository used by demos, tests, and the local agent."""
    return InMemoryOrderRepository(orders=_seed_orders(), inventory=_seed_inventory())
