"""Application use case for evaluating canonical procurement decisions."""

from collections.abc import Iterable

from application.decision_input_assembly import CanonicalDecisionInput
from application.historical_performance import HistoricalPerformanceAvailability as AppAvailability
from decision_core import (
    Criterion,
    DecisionResult,
    DomainValidationError,
    HistoricalPerformanceAvailability,
    HistoricalScoringProfile,
    HistoricalScoringResult,
    PurchaseRequirement,
    StrategicProfile,
    SupplierHistoricalPerformanceInput,
    SupplierOffer,
    evaluate_decision,
    evaluate_historical_decision,
)


def evaluate_procurement_decision(
    requirement: PurchaseRequirement,
    offers: Iterable[SupplierOffer],
    profile: StrategicProfile,
) -> DecisionResult:
    """Evaluate caller-supplied canonical data through the Decision Core."""

    return evaluate_decision(requirement, offers, profile)


def evaluate_procurement_decision_with_history(
    decision_input: CanonicalDecisionInput,
    profile: HistoricalScoringProfile,
) -> HistoricalScoringResult:
    """Map T8 history into the explicit ERP-neutral historical scoring path."""

    if decision_input.profile != profile.fallback_profile:
        raise DomainValidationError(
            "The canonical profile must equal the historical policy's legacy fallback profile."
        )
    historical_inputs = tuple(
        SupplierHistoricalPerformanceInput(
            supplier_id=item.supplier_id,
            metric_id=Criterion(item.metric_id.value),
            value=item.value,
            sample_size=item.sample_size,
            availability=(
                HistoricalPerformanceAvailability.USABLE
                if item.availability is AppAvailability.USABLE
                else HistoricalPerformanceAvailability.WITHHELD
            ),
        )
        for item in decision_input.historical_performance
    )
    return evaluate_historical_decision(
        decision_input.requirement,
        decision_input.offers,
        profile,
        historical_inputs,
    )
