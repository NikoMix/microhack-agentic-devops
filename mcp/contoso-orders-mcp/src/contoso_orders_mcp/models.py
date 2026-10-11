"""Domain models for the Orders MCP server.

These mirror the order/inventory domain the Order Support agent reasons over.
Kept deliberately small and self-contained so the server has no dependency on the
agent package.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(StrEnum):
    """Lifecycle state of an order."""

    PENDING = "pending"
    PAID = "paid"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class OrderLine(BaseModel):
    """A single line item within an order."""

    model_config = ConfigDict(frozen=True)

    sku: str
    description: str
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)


class Order(BaseModel):
    """A customer order."""

    model_config = ConfigDict(frozen=True)

    order_id: str
    customer_id: str
    status: OrderStatus
    placed_at: datetime
    currency: str = "EUR"
    lines: tuple[OrderLine, ...] = ()
    shipping_city: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    estimated_delivery: datetime | None = None
    notes: str | None = None

    @property
    def total(self) -> Decimal:
        """Order total across all line items."""
        return sum((line.unit_price * line.quantity for line in self.lines), Decimal(0))


class InventoryRecord(BaseModel):
    """Stock position for a SKU in a given warehouse."""

    model_config = ConfigDict(frozen=True)

    sku: str
    description: str
    available: int = Field(ge=0)
    reserved: int = Field(ge=0)
    warehouse: str
    restock_eta: datetime | None = None

    @property
    def sellable(self) -> int:
        """Units that can be promised to a new customer right now."""
        return max(self.available - self.reserved, 0)
