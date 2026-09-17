"""Deterministic hard-constraint, WSM scoring, and ranking pipeline."""

from collections.abc import Iterable
from decimal import Decimal

from decision_core.constraints import evaluate_hard_constraints
from decision_core.errors import DomainValidationError
from decision_core.models import (
    Criterion,
    CriterionContribution,
    CriterionDirection,
    DecisionResult,
    PurchaseRequirement,
    RankedOffer,
    StrategicProfile,
    SupplierOffer,
)
from decision_core.normalization import normalize_values

_CRITERIA = (
    (Criterion.UNIT_PRICE, CriterionDirection.COST),
    (Criterion.LEAD_TIME_DAYS, CriterionDirection.COST),
)


def _raw_value(offer: SupplierOffer, criterion: Criterion) -> Decimal:
    if criterion is Criterion.UNIT_PRICE:
        return offer.unit_price
    if criterion is Criterion.LEAD_TIME_DAYS:
        return offer.lead_time_days
    raise DomainValidationError(f"Unsupported criterion: {criterion!r}.")


def _validate_offer_set(offers: tuple[SupplierOffer, ...]) -> None:
    if not offers:
        raise DomainValidationError("At least one supplier offer is required.")

    identifiers = [offer.offer_id for offer in offers]
    duplicates = sorted(
        identifier for identifier in set(identifiers) if identifiers.count(identifier) > 1
    )
    if duplicates:
        raise DomainValidationError(
            "Offer identifiers must be unique; duplicates: " + ", ".join(duplicates) + "."
        )


def evaluate_decision(
    requirement: PurchaseRequirement,
    offers: Iterable[SupplierOffer],
    profile: StrategicProfile,
) -> DecisionResult:
    """Evaluate constraints, normalize eligible offers, score, and rank them.

    Ranking is deterministic: total score descending, then offer identifier
    ascending. Offers excluded by a hard constraint never enter normalization.
    """

    offer_tuple = tuple(offers)
    _validate_offer_set(offer_tuple)

    ordered_offers = tuple(sorted(offer_tuple, key=lambda offer: offer.offer_id))
    constraint_evaluation = evaluate_hard_constraints(requirement, ordered_offers)
    eligible = constraint_evaluation.eligible_offers
    if not eligible:
        return DecisionResult(
            requirement=requirement,
            profile=profile,
            ranked_offers=(),
            excluded_offers=constraint_evaluation.excluded_offers,
        )

    normalized_by_criterion: dict[Criterion, tuple[Decimal, ...]] = {}
    for criterion, direction in _CRITERIA:
        raw_values = tuple(_raw_value(offer, criterion) for offer in eligible)
        normalized_by_criterion[criterion] = normalize_values(raw_values, direction)

    scored: list[tuple[SupplierOffer, Decimal, tuple[CriterionContribution, ...]]] = []
    for index, offer in enumerate(eligible):
        contributions: list[CriterionContribution] = []
        for criterion, direction in _CRITERIA:
            raw_value = _raw_value(offer, criterion)
            normalized_value = normalized_by_criterion[criterion][index]
            weight = profile.weight_for(criterion)
            contribution = normalized_value * weight
            contributions.append(
                CriterionContribution(
                    criterion=criterion,
                    direction=direction,
                    raw_value=raw_value,
                    normalized_value=normalized_value,
                    weight=weight,
                    weighted_contribution=contribution,
                )
            )

        contribution_tuple = tuple(contributions)
        total_score = sum(
            (item.weighted_contribution for item in contribution_tuple),
            start=Decimal("0"),
        )
        scored.append((offer, total_score, contribution_tuple))

    scored.sort(key=lambda item: (-item[1], item[0].offer_id))
    ranked = tuple(
        RankedOffer(
            rank=rank,
            offer=offer,
            total_score=score,
            contributions=contributions,
        )
        for rank, (offer, score, contributions) in enumerate(scored, start=1)
    )
    return DecisionResult(
        requirement=requirement,
        profile=profile,
        ranked_offers=ranked,
        excluded_offers=constraint_evaluation.excluded_offers,
    )
