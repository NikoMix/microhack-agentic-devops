"""Domain and triage models for the Order Support agent.

These Pydantic models define the order/inventory domain the tools operate on and
the **structured recommendation** the agent returns. ``TriageRecommendation`` is
the contract the service emits and the agent's structured-output schema.
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
    """A customer order — the primary subject of triage."""

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


class TriageCategory(StrEnum):
    """The nature of the customer's order issue."""

    SHIPPING_DELAY = "shipping_delay"
    DAMAGED_ITEM = "damaged_item"
    WRONG_ITEM = "wrong_item"
    MISSING_ITEM = "missing_item"
    BILLING = "billing"
    CANCELLATION = "cancellation"
    REFUND = "refund"
    GENERAL_INQUIRY = "general_inquiry"
    FRAUD_RISK = "fraud_risk"


class TriageSeverity(StrEnum):
    """How urgently a human should care about the issue."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RecommendedAction(StrEnum):
    """The next best action proposed by the agent."""

    RESHIP = "reship"
    REFUND = "refund"
    PARTIAL_REFUND = "partial_refund"
    REPLACE_ITEM = "replace_item"
    APOLOGIZE_AND_TRACK = "apologize_and_track"
    REQUEST_MORE_INFO = "request_more_info"
    CANCEL_ORDER = "cancel_order"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    NO_ACTION = "no_action"


class TriageRecommendation(BaseModel):
    """The agent's structured triage decision.

    Returned verbatim by the service and used as the agent's structured-output
    schema. Designed to be safe to log (no PII beyond the order reference).
    """

    model_config = ConfigDict(extra="forbid")

    category: TriageCategory
    severity: TriageSeverity
    recommended_action: RecommendedAction
    summary: str = Field(
        min_length=1, description="One-sentence triage summary for an agent or coach."
    )
    suggested_customer_reply: str = Field(
        min_length=1,
        description="A ready-to-send, empathetic reply the support rep can adapt.",
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Model self-reported confidence in this triage."
    )
    order_id: str | None = Field(
        default=None, description="The order this triage refers to, if identified."
    )
    references: tuple[str, ...] = Field(
        default=(),
        description="Tool/data references justifying the decision (e.g. 'order:1001').",
    )

    def render(self) -> str:
        """Return a human-readable, multi-line summary for the console."""
        lines = [
            f"Category:   {self.category.value}",
            f"Severity:   {self.severity.value}",
            f"Action:     {self.recommended_action.value}",
            f"Confidence: {self.confidence:.0%}",
        ]
        if self.order_id:
            lines.append(f"Order:      {self.order_id}")
        lines.extend(["", f"Summary: {self.summary}", "", "Suggested reply:"])
        lines.append(self.suggested_customer_reply)
        if self.references:
            lines.extend(["", f"References: {', '.join(self.references)}"])
        return "\n".join(lines)


class TriageRequest(BaseModel):
    """An inbound triage request accepted by the HTTP service."""

    model_config = ConfigDict(extra="forbid")

    issue: str = Field(min_length=1, description="The customer's free-text complaint.")
    order_id: str | None = Field(default=None, description="A known order id, if any.")
    customer_id: str | None = Field(default=None, description="A known customer id, if any.")
