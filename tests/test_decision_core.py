"""Behavioral evidence for the ERP-independent procurement Decision Core."""

from decimal import Decimal
from itertools import permutations

import pytest

from decision_core import (
    Constraint,
    Criterion,
    CriterionDirection,
    DomainValidationError,
    PurchaseRequirement,
    StrategicProfile,
    SupplierOffer,
    evaluate_decision,
    normalize_values,
)


def _offer(
    offer_id: str,
    *,
    supplier_id: str | None = None,
    unit_price: str = "10",
    lead_time_days: str = "5",
    minimum_order_quantity: str = "1",
) -> SupplierOffer:
    return SupplierOffer(
        offer_id=offer_id,
        supplier_id=supplier_id or f"Supplier {offer_id}",
        unit_price=Decimal(unit_price),
        lead_time_days=Decimal(lead_time_days),
        minimum_order_quantity=Decimal(minimum_order_quantity),
    )


@pytest.fixture
def reference_requirement() -> PurchaseRequirement:
    return PurchaseRequirement("REQ-100", Decimal("100"))


@pytest.fixture
def reference_offers() -> tuple[SupplierOffer, ...]:
    return (
        _offer(
            "Offer A",
            supplier_id="Supplier A",
            unit_price="10",
            lead_time_days="10",
            minimum_order_quantity="50",
        ),
        _offer(
            "Offer B",
            supplier_id="Supplier B",
            unit_price="12",
            lead_time_days="5",
            minimum_order_quantity="100",
        ),
        _offer(
            "Offer C",
            supplier_id="Supplier C",
            unit_price="9",
            lead_time_days="8",
            minimum_order_quantity="150",
        ),
    )


@pytest.mark.parametrize(
    "quantity",
    [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")],
)
def test_purchase_requirement_rejects_invalid_quantity(quantity: Decimal) -> None:
    with pytest.raises(DomainValidationError):
        PurchaseRequirement("REQ-1", quantity)


@pytest.mark.parametrize("identifier", ["", "   "])
def test_purchase_requirement_rejects_empty_identifier(identifier: str) -> None:
    with pytest.raises(DomainValidationError, match="Requirement identifier"):
        PurchaseRequirement(identifier, Decimal("1"))


@pytest.mark.parametrize("identifier_field", ["offer_id", "supplier_id"])
def test_supplier_offer_rejects_empty_identifiers(identifier_field: str) -> None:
    values = {"offer_id": "Offer A", "supplier_id": "Supplier A"}
    values[identifier_field] = " "

    with pytest.raises(DomainValidationError, match="identifier"):
        SupplierOffer(
            **values,
            unit_price=Decimal("10"),
            lead_time_days=Decimal("5"),
            minimum_order_quantity=Decimal("1"),
        )


@pytest.mark.parametrize("unit_price", ["0", "-1"])
def test_supplier_offer_rejects_non_positive_price(unit_price: str) -> None:
    with pytest.raises(DomainValidationError, match="Unit price"):
        _offer("Offer A", unit_price=unit_price)


def test_supplier_offer_rejects_negative_lead_time() -> None:
    with pytest.raises(DomainValidationError, match="Lead time"):
        _offer("Offer A", lead_time_days="-1")


@pytest.mark.parametrize("minimum_order_quantity", ["0", "-1"])
def test_supplier_offer_rejects_invalid_minimum_order_quantity(
    minimum_order_quantity: str,
) -> None:
    with pytest.raises(DomainValidationError, match="Minimum order quantity"):
        _offer("Offer A", minimum_order_quantity=minimum_order_quantity)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("unit_price", Decimal("NaN")),
        ("lead_time_days", Decimal("Infinity")),
        ("minimum_order_quantity", Decimal("-Infinity")),
    ],
)
def test_supplier_offer_rejects_non_finite_numbers(field_name: str, invalid_value: Decimal) -> None:
    values = {
        "offer_id": "Offer A",
        "supplier_id": "Supplier A",
        "unit_price": Decimal("10"),
        "lead_time_days": Decimal("5"),
        "minimum_order_quantity": Decimal("1"),
    }
    values[field_name] = invalid_value

    with pytest.raises(DomainValidationError, match="finite"):
        SupplierOffer(**values)


def test_decision_rejects_duplicate_offer_identifiers(
    reference_requirement: PurchaseRequirement,
) -> None:
    offers = (_offer("Offer A"), _offer("Offer A", supplier_id="Another supplier"))

    with pytest.raises(DomainValidationError, match="duplicates: Offer A"):
        evaluate_decision(reference_requirement, offers, StrategicProfile.balanced())


def test_decision_rejects_empty_offer_collection(
    reference_requirement: PurchaseRequirement,
) -> None:
    with pytest.raises(DomainValidationError, match="At least one supplier offer"):
        evaluate_decision(reference_requirement, (), StrategicProfile.balanced())


@pytest.mark.parametrize(
    ("price_weight", "lead_time_weight", "message"),
    [
        (Decimal("-0.1"), Decimal("1.1"), "must not be negative"),
        (Decimal("0.4"), Decimal("0.4"), "must sum to no more than 1"),
        (Decimal("0.5000001"), Decimal("0.5"), "must sum to no more than 1"),
        (Decimal("NaN"), Decimal("0.5"), "must be finite"),
        (Decimal("0.5"), Decimal("Infinity"), "must be finite"),
    ],
)
def test_strategic_profile_rejects_invalid_weights(
    price_weight: Decimal, lead_time_weight: Decimal, message: str
) -> None:
    with pytest.raises(DomainValidationError, match=message):
        StrategicProfile("invalid", price_weight, lead_time_weight)


def test_strategic_profile_accepts_small_weight_shortfall() -> None:
    profile = StrategicProfile(
        "rounded",
        unit_price_weight=Decimal("0.4999995"),
        lead_time_weight=Decimal("0.5"),
    )

    assert profile.unit_price_weight + profile.lead_time_weight == Decimal("0.9999995")


@pytest.mark.parametrize("minimum_order_quantity", ["50", "100"])
def test_offer_at_or_below_requested_quantity_remains_eligible(
    reference_requirement: PurchaseRequirement, minimum_order_quantity: str
) -> None:
    result = evaluate_decision(
        reference_requirement,
        (_offer("Offer A", minimum_order_quantity=minimum_order_quantity),),
        StrategicProfile.balanced(),
    )

    assert [ranked.offer.offer_id for ranked in result.ranked_offers] == ["Offer A"]
    assert result.excluded_offers == ()


def test_offer_with_moq_above_requested_quantity_is_excluded(
    reference_requirement: PurchaseRequirement,
) -> None:
    result = evaluate_decision(
        reference_requirement,
        (_offer("Offer C", minimum_order_quantity="150"),),
        StrategicProfile.balanced(),
    )

    assert result.ranked_offers == ()
    assert result.recommended_offer is None
    exclusion = result.excluded_offers[0]
    assert exclusion.failed_constraint is Constraint.MINIMUM_ORDER_QUANTITY
    assert exclusion.requested_quantity == Decimal("100")
    assert exclusion.minimum_order_quantity == Decimal("150")
    assert "Offer C" in exclusion.explanation
    assert "100" in exclusion.explanation
    assert "150" in exclusion.explanation


def test_all_offers_excluded_returns_clear_outcome(
    reference_requirement: PurchaseRequirement,
) -> None:
    offers = (
        _offer("Offer A", minimum_order_quantity="101"),
        _offer("Offer B", minimum_order_quantity="150"),
    )

    result = evaluate_decision(reference_requirement, offers, StrategicProfile.cost_focused())

    assert result.ranked_offers == ()
    assert result.recommended_offer is None
    assert [item.offer.offer_id for item in result.excluded_offers] == [
        "Offer A",
        "Offer B",
    ]


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        (
            CriterionDirection.COST,
            (Decimal("1"), Decimal("0.5"), Decimal("0")),
        ),
        (
            CriterionDirection.BENEFIT,
            (Decimal("0"), Decimal("0.5"), Decimal("1")),
        ),
    ],
)
def test_normalization_maps_endpoints_and_intermediate_value(
    direction: CriterionDirection, expected: tuple[Decimal, ...]
) -> None:
    assert normalize_values((Decimal("10"), Decimal("15"), Decimal("20")), direction) == expected


@pytest.mark.parametrize("direction", [CriterionDirection.COST, CriterionDirection.BENEFIT])
def test_equal_values_normalize_to_one(direction: CriterionDirection) -> None:
    assert normalize_values((Decimal("5"), Decimal("5")), direction) == (
        Decimal("1"),
        Decimal("1"),
    )


def test_excluded_offer_does_not_influence_normalization_bounds(
    reference_requirement: PurchaseRequirement,
    reference_offers: tuple[SupplierOffer, ...],
) -> None:
    result = evaluate_decision(
        reference_requirement, reference_offers, StrategicProfile.cost_focused()
    )

    contributions = {
        ranked.offer.offer_id: {
            contribution.criterion: contribution.normalized_value
            for contribution in ranked.contributions
        }
        for ranked in result.ranked_offers
    }
    assert contributions["Offer A"][Criterion.UNIT_PRICE] == Decimal("1")
    assert contributions["Offer B"][Criterion.UNIT_PRICE] == Decimal("0")
    assert contributions["Offer A"][Criterion.LEAD_TIME_DAYS] == Decimal("0")
    assert contributions["Offer B"][Criterion.LEAD_TIME_DAYS] == Decimal("1")


@pytest.mark.parametrize(
    ("profile", "expected_order", "expected_scores"),
    [
        (
            StrategicProfile.cost_focused(),
            ["Offer A", "Offer B"],
            [Decimal("0.7"), Decimal("0.3")],
        ),
        (
            StrategicProfile.urgent(),
            ["Offer B", "Offer A"],
            [Decimal("0.7"), Decimal("0.3")],
        ),
        (
            StrategicProfile.balanced(),
            ["Offer A", "Offer B"],
            [Decimal("0.5"), Decimal("0.5")],
        ),
    ],
)
def test_reference_scenario_produces_expected_ranking(
    reference_requirement: PurchaseRequirement,
    reference_offers: tuple[SupplierOffer, ...],
    profile: StrategicProfile,
    expected_order: list[str],
    expected_scores: list[Decimal],
) -> None:
    result = evaluate_decision(reference_requirement, reference_offers, profile)

    assert [ranked.offer.offer_id for ranked in result.ranked_offers] == expected_order
    assert [ranked.total_score for ranked in result.ranked_offers] == expected_scores
    assert [ranked.rank for ranked in result.ranked_offers] == [1, 2]
    assert [item.offer.offer_id for item in result.excluded_offers] == ["Offer C"]


def test_cost_focused_contribution_trace_reconstructs_scores(
    reference_requirement: PurchaseRequirement,
    reference_offers: tuple[SupplierOffer, ...],
) -> None:
    result = evaluate_decision(
        reference_requirement, reference_offers, StrategicProfile.cost_focused()
    )

    expected = {
        "Offer A": {
            Criterion.UNIT_PRICE: ("10", "1", "0.7", "0.7"),
            Criterion.LEAD_TIME_DAYS: ("10", "0", "0.3", "0.0"),
        },
        "Offer B": {
            Criterion.UNIT_PRICE: ("12", "0", "0.7", "0.0"),
            Criterion.LEAD_TIME_DAYS: ("5", "1", "0.3", "0.3"),
        },
    }
    for ranked in result.ranked_offers:
        assert ranked.total_score == sum(
            (item.weighted_contribution for item in ranked.contributions),
            start=Decimal("0"),
        )
        for contribution in ranked.contributions:
            trace = expected[ranked.offer.offer_id][contribution.criterion]
            assert contribution.direction is CriterionDirection.COST
            assert contribution.raw_value == Decimal(trace[0])
            assert contribution.normalized_value == Decimal(trace[1])
            assert contribution.weight == Decimal(trace[2])
            assert contribution.weighted_contribution == Decimal(trace[3])


def test_scores_and_contributions_are_in_unit_interval(
    reference_requirement: PurchaseRequirement,
    reference_offers: tuple[SupplierOffer, ...],
) -> None:
    result = evaluate_decision(
        reference_requirement, reference_offers, StrategicProfile.cost_focused()
    )

    for ranked in result.ranked_offers:
        assert Decimal("0") <= ranked.total_score <= Decimal("1")
        for contribution in ranked.contributions:
            assert Decimal("0") <= contribution.normalized_value <= Decimal("1")
            assert Decimal("0") <= contribution.weighted_contribution <= Decimal("1")


def test_repeated_evaluation_is_deterministic_and_input_order_independent(
    reference_requirement: PurchaseRequirement,
    reference_offers: tuple[SupplierOffer, ...],
) -> None:
    profile = StrategicProfile.balanced()
    baseline = evaluate_decision(reference_requirement, reference_offers, profile)

    for input_order in permutations(reference_offers):
        assert evaluate_decision(reference_requirement, input_order, profile) == baseline
    assert evaluate_decision(reference_requirement, reference_offers, profile) == baseline
