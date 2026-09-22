"""Deterministic T11 fixtures shared by unit and PostgreSQL integration tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from application.decision_cases import EvaluationSnapshot, ScoringPolicy
from application.decision_input_assembly import (
    AssembledDecisionInput,
    CanonicalDecisionInput,
    FieldProvenance,
    ProvenanceManifest,
)
from application.decisions import evaluate_procurement_decision_with_history
from application.historical_performance import (
    HistoricalDataWarning,
    HistoricalMetric,
    HistoricalPerformanceAvailability,
    HistoricalWarningCode,
    SupplierHistoricalPerformance,
)
from decision_core import (
    HistoricalScoringProfile,
    PurchaseRequirement,
    StrategicProfile,
    SupplierOffer,
    evaluate_decision,
)

NOW = datetime(2026, 9, 22, 8, 30, 45, 123456, tzinfo=UTC)
CASE_ID = "11111111-1111-4111-8111-111111111111"


def offer(
    offer_id: str,
    supplier_id: str,
    price: str,
    lead_time: str,
    moq: str = "1.000",
) -> SupplierOffer:
    return SupplierOffer(
        offer_id=offer_id,
        supplier_id=supplier_id,
        unit_price=Decimal(price),
        lead_time_days=Decimal(lead_time),
        minimum_order_quantity=Decimal(moq),
    )


def active_history(supplier_id: str, value: str, sample_size: int) -> SupplierHistoricalPerformance:
    return SupplierHistoricalPerformance(
        metric_id=HistoricalMetric.DELIVERY_SCHEDULE_ADHERENCE,
        value=Decimal(value),
        sample_size=sample_size,
        observation_window_start=NOW - timedelta(days=365),
        observation_window_end=NOW,
        observed_at=NOW,
        supplier_id=supplier_id,
        availability=HistoricalPerformanceAvailability.USABLE,
        warnings=(),
    )


def withheld_history(supplier_id: str) -> SupplierHistoricalPerformance:
    return SupplierHistoricalPerformance(
        metric_id=HistoricalMetric.DELIVERY_SCHEDULE_ADHERENCE,
        value=None,
        sample_size=2,
        observation_window_start=NOW - timedelta(days=365),
        observation_window_end=NOW,
        observed_at=NOW,
        supplier_id=supplier_id,
        availability=HistoricalPerformanceAvailability.WITHHELD_INSUFFICIENT_SAMPLE,
        warnings=(
            HistoricalDataWarning(
                code=HistoricalWarningCode.INSUFFICIENT_HISTORY,
                message="Historical performance is withheld for the deterministic fixture.",
            ),
        ),
    )


def assembled(
    *, history: tuple[SupplierHistoricalPerformance, ...] = (), all_excluded: bool = False
) -> AssembledDecisionInput:
    requirement = PurchaseRequirement("REQ-T11", Decimal("10.000"))
    offers = (
        offer("offer-A", "supplier-A", "10.1200", "5.50", "11" if all_excluded else "1"),
        offer("offer-B", "supplier-B", "12.3400", "3.25", "12" if all_excluded else "1"),
    )
    return AssembledDecisionInput(
        canonical=CanonicalDecisionInput(
            requirement=requirement,
            offers=offers,
            profile=StrategicProfile.cost_focused(),
            historical_performance=history,
        ),
        provenance=ProvenanceManifest(
            entries=(
                FieldProvenance(
                    canonical_path="offers[offer-A].unit_price",
                    field_name="price_unit",
                    source_type="fixture",
                    source_reference="RFQ-A#line-1",
                    observed_at=NOW,
                ),
            )
        ),
    )


def variant(
    name: str,
) -> tuple[AssembledDecisionInput, ScoringPolicy, EvaluationSnapshot]:
    if name == "legacy":
        value = assembled()
        policy = value.canonical.profile
        return (
            value,
            policy,
            evaluate_decision(value.canonical.requirement, value.canonical.offers, policy),
        )
    if name == "historical_active":
        value = assembled(
            history=(
                active_history("supplier-A", "33.33", 3),
                active_history("supplier-B", "100.00", 8),
            )
        )
        policy = HistoricalScoringProfile.cost_focused_history_v1()
        return value, policy, evaluate_procurement_decision_with_history(value.canonical, policy)
    if name == "historical_fallback":
        value = assembled(
            history=(
                withheld_history("supplier-A"),
                active_history("supplier-B", "91.25", 7),
            )
        )
        policy = HistoricalScoringProfile.cost_focused_history_v1()
        return value, policy, evaluate_procurement_decision_with_history(value.canonical, policy)
    if name == "all_excluded":
        value = assembled(all_excluded=True)
        policy = value.canonical.profile
        return (
            value,
            policy,
            evaluate_decision(value.canonical.requirement, value.canonical.offers, policy),
        )
    raise ValueError(f"Unknown fixture variant: {name}.")
