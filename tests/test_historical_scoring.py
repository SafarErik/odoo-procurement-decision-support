"""Runtime regressions for the bounded, opt-in T10 historical criterion."""

from dataclasses import fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import permutations

import pytest

from application.decision_input_assembly import CanonicalDecisionInput
from application.decisions import evaluate_procurement_decision_with_history
from application.historical_performance import (
    HistoricalDataWarning,
    HistoricalMetric,
    HistoricalWarningCode,
    SupplierHistoricalPerformance,
)
from application.historical_performance import (
    HistoricalPerformanceAvailability as AppAvailability,
)
from decision_core import (
    Criterion,
    CriterionContribution,
    CriterionDirection,
    DomainValidationError,
    HistoricalPerformanceAvailability,
    HistoricalScoringProfile,
    PurchaseRequirement,
    StrategicProfile,
    SupplierHistoricalPerformanceInput,
    SupplierOffer,
    evaluate_decision,
    evaluate_historical_decision,
)
from tools.t9_scoring_evaluation import evaluate_scenario, required_scenarios


def _history(
    supplier_id: str,
    value: str | None,
    sample_size: int,
) -> SupplierHistoricalPerformanceInput:
    return SupplierHistoricalPerformanceInput(
        supplier_id=supplier_id,
        metric_id=Criterion.DELIVERY_SCHEDULE_ADHERENCE,
        value=Decimal(value) if value is not None else None,
        sample_size=sample_size,
        availability=(
            HistoricalPerformanceAvailability.USABLE
            if value is not None
            else HistoricalPerformanceAvailability.WITHHELD
        ),
    )


def _offer(
    offer_id: str,
    supplier_id: str,
    price: str,
    lead: str,
    moq: str = "1",
) -> SupplierOffer:
    return SupplierOffer(
        offer_id=offer_id,
        supplier_id=supplier_id,
        unit_price=Decimal(price),
        lead_time_days=Decimal(lead),
        minimum_order_quantity=Decimal(moq),
    )


def _profile(name: str) -> HistoricalScoringProfile:
    return {
        "cost-focused": HistoricalScoringProfile.cost_focused_history_v1,
        "urgent": HistoricalScoringProfile.urgent_history_v1,
        "risk-averse": HistoricalScoringProfile.risk_averse_history_v1,
    }[name]()


def test_versioned_profiles_are_exact_and_legacy_profiles_are_unchanged() -> None:
    assert tuple(field.name for field in fields(CriterionContribution)) == (
        "criterion",
        "direction",
        "raw_value",
        "normalized_value",
        "weight",
        "weighted_contribution",
    )
    assert StrategicProfile.cost_focused() == StrategicProfile(
        "cost-focused", Decimal("0.7"), Decimal("0.3")
    )
    assert StrategicProfile.urgent() == StrategicProfile("urgent", Decimal("0.3"), Decimal("0.7"))
    assert StrategicProfile.balanced() == StrategicProfile(
        "balanced", Decimal("0.5"), Decimal("0.5")
    )
    expected = {
        "cost_focused_history_v1": ("0.60", "0.25", "0.15"),
        "urgent_history_v1": ("0.25", "0.60", "0.15"),
        "risk_averse_history_v1": ("0.30", "0.30", "0.40"),
    }
    for profile in (
        HistoricalScoringProfile.cost_focused_history_v1(),
        HistoricalScoringProfile.urgent_history_v1(),
        HistoricalScoringProfile.risk_averse_history_v1(),
    ):
        weights = (
            profile.unit_price_weight,
            profile.lead_time_weight,
            profile.delivery_schedule_adherence_weight,
        )
        assert weights == tuple(Decimal(value) for value in expected[profile.name])
        assert sum(weights, start=Decimal("0")) == Decimal("1")


@pytest.mark.parametrize(
    ("weights", "message"),
    [
        (("0.6", "0.25", "0.14"), "sum exactly"),
        (("NaN", "0.25", "0.15"), "finite"),
        (("0.7", "0.4", "-0.1"), "negative"),
    ],
)
def test_historical_profile_rejects_invalid_weights(
    weights: tuple[str, str, str], message: str
) -> None:
    with pytest.raises(DomainValidationError, match=message):
        HistoricalScoringProfile(
            "invalid_history_v1",
            *(Decimal(value) for value in weights),
            fallback_profile=StrategicProfile.balanced(),
        )


def test_historical_profile_requires_an_explicit_versioned_name() -> None:
    with pytest.raises(DomainValidationError, match="positive version"):
        HistoricalScoringProfile(
            "cost_focused_history",
            Decimal("0.60"),
            Decimal("0.25"),
            Decimal("0.15"),
            fallback_profile=StrategicProfile.cost_focused(),
        )


@pytest.mark.parametrize("sample_size", [0, 1, 2])
def test_samples_below_three_are_withheld_not_zero(sample_size: int) -> None:
    item = _history("supplier-A", None, sample_size)
    assert not item.usable
    with pytest.raises(DomainValidationError, match="sample size of at least 3"):
        SupplierHistoricalPerformanceInput(
            supplier_id="supplier-A",
            metric_id=Criterion.DELIVERY_SCHEDULE_ADHERENCE,
            value=Decimal("0"),
            sample_size=sample_size,
            availability=HistoricalPerformanceAvailability.USABLE,
        )


def test_sample_size_three_and_percentage_endpoints_are_usable() -> None:
    assert _history("supplier-A", "0", 3).usable
    assert _history("supplier-B", "100", 3).usable


@pytest.mark.parametrize("value", ["-0.01", "100.01", "NaN", "Infinity"])
def test_invalid_historical_percentages_fail_closed(value: str) -> None:
    with pytest.raises(DomainValidationError):
        _history("supplier-A", value, 3)


def test_t9_fixed_scenarios_match_runtime_policy() -> None:
    for scenario in required_scenarios():
        evaluated = evaluate_scenario(scenario)
        history = tuple(
            _history(
                next(
                    offer.supplier_id
                    for offer in scenario.offers
                    if offer.offer_id == item.offer_id
                ),
                format(item.value, "f") if item.value is not None else None,
                item.sample_size,
            )
            for item in scenario.history
        )
        runtime = evaluate_historical_decision(
            scenario.requirement,
            scenario.offers,
            _profile(scenario.profile_name),
            history,
        )

        assert runtime.historical_criterion_active == evaluated.history_criterion_active
        assert (
            tuple(item.offer.offer_id for item in runtime.decision_result.ranked_offers)
            == evaluated.candidate_ranking
        )
        assert tuple(
            (item.offer.offer_id, item.total_score)
            for item in runtime.decision_result.ranked_offers
        ) == tuple((item.offer_id, item.total_score) for item in evaluated.candidate_ranked_offers)


def test_active_contributions_are_direct_reconstructable_and_explained() -> None:
    requirement = PurchaseRequirement("REQ", Decimal("10"))
    offers = (
        _offer("A", "supplier-A", "10", "5"),
        _offer("B", "supplier-B", "12", "4"),
    )
    result = evaluate_historical_decision(
        requirement,
        offers,
        HistoricalScoringProfile.cost_focused_history_v1(),
        (_history("supplier-A", "33.33", 3), _history("supplier-B", "100", 8)),
    )

    assert result.historical_criterion_active
    assert result.affected_offer_ids == result.affected_supplier_ids == ()
    for ranked in result.decision_result.ranked_offers:
        assert ranked.total_score == sum(
            (item.weighted_contribution for item in ranked.contributions),
            start=Decimal("0"),
        )
        historical = ranked.contributions[-1]
        assert historical.criterion is Criterion.DELIVERY_SCHEDULE_ADHERENCE
        assert historical.direction is CriterionDirection.BENEFIT
        assert historical.normalized_value == historical.raw_value / Decimal("100")
        assert historical.sample_size in {3, 8}
        assert historical.weight == Decimal("0.15")
        assert historical.weighted_contribution == historical.normalized_value * historical.weight
        assert historical.explanation is not None
        assert "normalized directly" in historical.explanation
        assert f"sample size {historical.sample_size}" in historical.explanation


def test_missing_eligible_history_returns_exact_baseline_and_sorted_context() -> None:
    requirement = PurchaseRequirement("REQ", Decimal("10"))
    offers = (
        _offer("C", "supplier-C", "14", "3"),
        _offer("A", "supplier-A", "10", "5"),
        _offer("B", "supplier-B", "12", "4"),
    )
    profile = HistoricalScoringProfile.cost_focused_history_v1()
    baseline = evaluate_decision(requirement, offers, StrategicProfile.cost_focused())
    result = evaluate_historical_decision(
        requirement,
        offers,
        profile,
        (_history("supplier-A", None, 2),),
    )

    assert not result.historical_criterion_active
    assert result.decision_result == baseline
    assert result.explanation == (
        "historical criterion inactive: at least one MOQ-eligible offer has missing or "
        "withheld history"
    )
    assert result.affected_offer_ids == ("A", "B", "C")
    assert result.affected_supplier_ids == ("supplier-A", "supplier-B", "supplier-C")
    assert all(len(item.contributions) == 2 for item in result.decision_result.ranked_offers)


def test_missing_history_only_for_moq_ineligible_supplier_does_not_deactivate() -> None:
    requirement = PurchaseRequirement("REQ", Decimal("10"))
    offers = (
        _offer("A", "supplier-A", "10", "5"),
        _offer("B", "supplier-B", "12", "4"),
        _offer("C", "supplier-C", "1", "1", moq="11"),
    )
    result = evaluate_historical_decision(
        requirement,
        offers,
        HistoricalScoringProfile.risk_averse_history_v1(),
        (_history("supplier-A", "50", 3), _history("supplier-B", "70", 3)),
    )

    assert result.historical_criterion_active
    assert [item.offer.offer_id for item in result.decision_result.excluded_offers] == ["C"]


def test_all_offers_excluded_returns_exact_baseline_and_no_eligible_status() -> None:
    requirement = PurchaseRequirement("REQ", Decimal("10"))
    offers = (
        _offer("A", "supplier-A", "10", "5", moq="11"),
        _offer("B", "supplier-B", "12", "4", moq="12"),
    )
    profile = HistoricalScoringProfile.urgent_history_v1()
    result = evaluate_historical_decision(requirement, offers, profile, ())

    assert result.decision_result == evaluate_decision(
        requirement, offers, StrategicProfile.urgent()
    )
    assert not result.historical_criterion_active
    assert result.explanation == "historical criterion inactive: no MOQ-eligible offers"
    assert result.affected_offer_ids == result.affected_supplier_ids == ()


def test_historical_decision_rejects_an_empty_offer_set() -> None:
    with pytest.raises(DomainValidationError, match="At least one supplier offer"):
        evaluate_historical_decision(
            PurchaseRequirement("REQ", Decimal("10")),
            (),
            HistoricalScoringProfile.cost_focused_history_v1(),
            (),
        )


def test_duplicate_and_unknown_supplier_history_fail_closed() -> None:
    requirement = PurchaseRequirement("REQ", Decimal("10"))
    offers = (_offer("A", "supplier-A", "10", "5"),)
    profile = HistoricalScoringProfile.cost_focused_history_v1()
    duplicate = _history("supplier-A", "80", 3)

    with pytest.raises(DomainValidationError, match="unambiguous; duplicate supplier"):
        evaluate_historical_decision(requirement, offers, profile, (duplicate, duplicate))
    with pytest.raises(DomainValidationError, match="unknown suppliers: supplier-X"):
        evaluate_historical_decision(
            requirement,
            offers,
            profile,
            (_history("supplier-X", "80", 3),),
        )


def test_multiple_offers_share_supplier_history_and_order_is_irrelevant() -> None:
    requirement = PurchaseRequirement("REQ", Decimal("10"))
    offers = (
        _offer("A-2", "supplier-A", "11", "4"),
        _offer("B", "supplier-B", "12", "3"),
        _offer("A-1", "supplier-A", "10", "5"),
    )
    history = (_history("supplier-B", "70", 4), _history("supplier-A", "90", 5))
    profile = HistoricalScoringProfile.cost_focused_history_v1()
    expected = evaluate_historical_decision(requirement, offers, profile, history)

    for offer_order in permutations(offers):
        for history_order in permutations(history):
            assert (
                evaluate_historical_decision(requirement, offer_order, profile, history_order)
                == expected
            )
    supplier_a_history = {
        item.contributions[-1]
        for item in expected.decision_result.ranked_offers
        if item.offer.supplier_id == "supplier-A"
    }
    assert len(supplier_a_history) == 1


def test_application_maps_t8_history_without_provenance_entering_core() -> None:
    now = datetime(2026, 9, 21, tzinfo=UTC)
    app_history = SupplierHistoricalPerformance(
        metric_id=HistoricalMetric.DELIVERY_SCHEDULE_ADHERENCE,
        value=Decimal("33.33"),
        sample_size=3,
        observation_window_start=now - timedelta(days=365),
        observation_window_end=now,
        observed_at=now,
        supplier_id="supplier-A",
        availability=AppAvailability.USABLE,
        warnings=(),
    )
    canonical = CanonicalDecisionInput(
        requirement=PurchaseRequirement("REQ", Decimal("10")),
        offers=(_offer("A", "supplier-A", "10", "5"),),
        profile=StrategicProfile.cost_focused(),
        historical_performance=(app_history,),
    )
    result = evaluate_procurement_decision_with_history(
        canonical, HistoricalScoringProfile.cost_focused_history_v1()
    )

    assert result.historical_criterion_active
    contribution = result.decision_result.ranked_offers[0].contributions[-1]
    assert contribution.normalized_value == Decimal("0.3333")
    assert contribution.sample_size == 3
    assert "source" not in contribution.explanation.lower()


def test_application_maps_withheld_t8_history_to_set_level_fallback() -> None:
    now = datetime(2026, 9, 21, tzinfo=UTC)
    warning = HistoricalDataWarning(
        HistoricalWarningCode.INSUFFICIENT_HISTORY,
        "Historical performance is withheld because fewer than three eligible lines exist.",
    )
    app_history = SupplierHistoricalPerformance(
        metric_id=HistoricalMetric.DELIVERY_SCHEDULE_ADHERENCE,
        value=None,
        sample_size=2,
        observation_window_start=now - timedelta(days=365),
        observation_window_end=now,
        observed_at=now,
        supplier_id="supplier-A",
        availability=AppAvailability.WITHHELD_INSUFFICIENT_SAMPLE,
        warnings=(warning,),
    )
    canonical = CanonicalDecisionInput(
        requirement=PurchaseRequirement("REQ", Decimal("10")),
        offers=(_offer("A", "supplier-A", "10", "5"),),
        profile=StrategicProfile.cost_focused(),
        historical_performance=(app_history,),
    )

    result = evaluate_procurement_decision_with_history(
        canonical, HistoricalScoringProfile.cost_focused_history_v1()
    )
    assert not result.historical_criterion_active
    assert result.decision_result == evaluate_decision(
        canonical.requirement, canonical.offers, canonical.profile
    )


def test_application_rejects_profile_mismatch() -> None:
    canonical = CanonicalDecisionInput(
        requirement=PurchaseRequirement("REQ", Decimal("10")),
        offers=(_offer("A", "supplier-A", "10", "5"),),
        profile=StrategicProfile.urgent(),
    )
    with pytest.raises(DomainValidationError, match="legacy fallback"):
        evaluate_procurement_decision_with_history(
            canonical, HistoricalScoringProfile.cost_focused_history_v1()
        )
