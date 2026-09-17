"""Application use case for evaluating canonical procurement decisions."""

from collections.abc import Iterable

from decision_core import (
    DecisionResult,
    PurchaseRequirement,
    StrategicProfile,
    SupplierOffer,
    evaluate_decision,
)


def evaluate_procurement_decision(
    requirement: PurchaseRequirement,
    offers: Iterable[SupplierOffer],
    profile: StrategicProfile,
) -> DecisionResult:
    """Evaluate caller-supplied canonical data through the Decision Core."""

    return evaluate_decision(requirement, offers, profile)
