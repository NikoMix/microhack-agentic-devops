"""Tests for the domain and triage models."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from order_support_agent.models import (
    InventoryRecord,
    Order,
    OrderLine,
    OrderStatus,
    RecommendedAction,
    TriageCategory,
    TriageRecommendation,
    TriageSeverity,
)


def _recommendation(**overrides: object) -> TriageRecommendation:
    base: dict[str, object] = {
        "category": TriageCategory.REFUND,
        "severity": TriageSeverity.MEDIUM,
        "recommended_action": RecommendedAction.REFUND,
        "summary": "A summary.",
        "suggested_customer_reply": "A reply.",
        "confidence": 0.5,
    }
    base.update(overrides)
    return TriageRecommendation(**base)  # type: ignore[arg-type]


def test_order_total_sums_lines() -> None:
    order = Order(
        order_id="X1",
        customer_id="C-1",
        status=OrderStatus.PAID,
        placed_at="2025-10-01T09:00:00Z",  # type: ignore[arg-type]
        lines=(
            OrderLine(sku="A", description="a", quantity=2, unit_price=Decimal("10.00")),
            OrderLine(sku="B", description="b", quantity=1, unit_price=Decimal("5.50")),
        ),
    )
    assert order.total == Decimal("25.50")


def test_inventory_sellable_never_negative() -> None:
    record = InventoryRecord(sku="A", description="a", available=3, reserved=10, warehouse="W")
    assert record.sellable == 0


def test_recommendation_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        _recommendation(made_up_field="nope")


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_recommendation_confidence_bounds(confidence: float) -> None:
    with pytest.raises(ValidationError):
        _recommendation(confidence=confidence)


def test_recommendation_render_includes_key_fields() -> None:
    rendered = _recommendation(order_id="1001", references=("order:1001",)).render()
    assert "Action:     refund" in rendered
    assert "Order:      1001" in rendered
    assert "References: order:1001" in rendered


def test_recommendation_round_trips_through_json() -> None:
    original = _recommendation(order_id="1003")
    restored = TriageRecommendation.model_validate_json(original.model_dump_json())
    assert restored == original
