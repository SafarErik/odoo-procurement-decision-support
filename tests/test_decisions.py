"""Application tests for canonical procurement decision evaluation."""

from decimal import Decimal

from application.decisions import evaluate_procurement_decision
from decision_core import PurchaseRequirement, StrategicProfile, SupplierOffer


def _reference_offers() -> tuple[SupplierOffer, ...]:
    return (
        SupplierOffer(
            offer_id="Offer A",
            supplier_id="Supplier A",
            unit_price=Decimal("10"),
            lead_time_days=Decimal("10"),
            minimum_order_quantity=Decimal("50"),
        ),
        SupplierOffer(
            offer_id="Offer B",
            supplier_id="Supplier B",
            unit_price=Decimal("12"),
            lead_time_days=Decimal("5"),
            minimum_order_quantity=Decimal("100"),
        ),
        SupplierOffer(
            offer_id="Offer C",
            supplier_id="Supplier C",
            unit_price=Decimal("9"),
            lead_time_days=Decimal("8"),
            minimum_order_quantity=Decimal("150"),
        ),
    )


def test_decision_use_case_returns_complete_cost_focused_result() -> None:
    """The application delegates the full explained evaluation to the pure core."""

    result = evaluate_procurement_decision(
        PurchaseRequirement("REQ-100", Decimal("100")),
        _reference_offers(),
        StrategicProfile.cost_focused(),
    )

    assert result.recommended_offer is not None
    assert result.recommended_offer.offer.offer_id == "Offer A"
    assert [item.offer.offer_id for item in result.ranked_offers] == ["Offer A", "Offer B"]
    assert [item.total_score for item in result.ranked_offers] == [
        Decimal("0.7"),
        Decimal("0.3"),
    ]
    assert [item.criterion.value for item in result.ranked_offers[0].contributions] == [
        "unit_price",
        "lead_time_days",
    ]
    assert [item.weighted_contribution for item in result.ranked_offers[0].contributions] == [
        Decimal("0.7"),
        Decimal("0.0"),
    ]
    assert [item.offer.offer_id for item in result.excluded_offers] == ["Offer C"]
    assert result.excluded_offers[0].failed_constraint.value == "minimum_order_quantity"


def test_decision_use_case_returns_no_recommendation_when_all_offers_are_excluded() -> None:
    """A complete set of constraint failures is a valid application result."""

    result = evaluate_procurement_decision(
        PurchaseRequirement("REQ-1", Decimal("1")),
        _reference_offers(),
        StrategicProfile.balanced(),
    )

    assert result.recommended_offer is None
    assert result.ranked_offers == ()
    assert [item.offer.offer_id for item in result.excluded_offers] == [
        "Offer A",
        "Offer B",
        "Offer C",
    ]
