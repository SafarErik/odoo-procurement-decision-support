"""Hard-constraint evaluation performed before scoring."""

from dataclasses import dataclass

from decision_core.models import (
    Constraint,
    ExcludedOffer,
    PurchaseRequirement,
    SupplierOffer,
)


@dataclass(frozen=True, slots=True)
class ConstraintEvaluation:
    """Partition of offers after all currently supported hard constraints."""

    eligible_offers: tuple[SupplierOffer, ...]
    excluded_offers: tuple[ExcludedOffer, ...]


def evaluate_hard_constraints(
    requirement: PurchaseRequirement, offers: tuple[SupplierOffer, ...]
) -> ConstraintEvaluation:
    """Exclude offers whose minimum order quantity exceeds the request."""

    eligible: list[SupplierOffer] = []
    excluded: list[ExcludedOffer] = []
    for offer in offers:
        if requirement.requested_quantity >= offer.minimum_order_quantity:
            eligible.append(offer)
            continue

        excluded.append(
            ExcludedOffer(
                offer=offer,
                failed_constraint=Constraint.MINIMUM_ORDER_QUANTITY,
                explanation=(
                    f"Offer {offer.offer_id} was excluded because the requested quantity "
                    f"of {requirement.requested_quantity} is lower than the supplier's "
                    f"minimum order quantity of {offer.minimum_order_quantity}."
                ),
                requested_quantity=requirement.requested_quantity,
                minimum_order_quantity=offer.minimum_order_quantity,
            )
        )

    return ConstraintEvaluation(tuple(eligible), tuple(excluded))
