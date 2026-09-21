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
    ExcludedOffer,
    HistoricalCriterionContribution,
    HistoricalScoringProfile,
    HistoricalScoringResult,
    PurchaseRequirement,
    RankedOffer,
    StrategicProfile,
    SupplierHistoricalPerformanceInput,
    SupplierOffer,
)
from decision_core.normalization import normalize_values

_CRITERIA = (
    (Criterion.UNIT_PRICE, CriterionDirection.COST),
    (Criterion.LEAD_TIME_DAYS, CriterionDirection.COST),
)
_HISTORICAL_CRITERIA = (
    *_CRITERIA,
    (Criterion.DELIVERY_SCHEDULE_ADHERENCE, CriterionDirection.BENEFIT),
)
_HISTORY_INACTIVE_MISSING = (
    "historical criterion inactive: at least one MOQ-eligible offer has missing or withheld history"
)
_HISTORY_INACTIVE_NO_ELIGIBLE = "historical criterion inactive: no MOQ-eligible offers"
_HISTORY_ACTIVE = "historical criterion active: every MOQ-eligible offer has usable history"


def _raw_value(offer: SupplierOffer, criterion: Criterion) -> Decimal:
    if criterion is Criterion.UNIT_PRICE:
        return offer.unit_price
    if criterion is Criterion.LEAD_TIME_DAYS:
        return offer.lead_time_days
    raise DomainValidationError(f"Unsupported criterion: {criterion!r}.")


def _historical_explanation(raw_value: Decimal, sample_size: int, weight: Decimal) -> str:
    normalized = raw_value / Decimal("100")
    return (
        "delivery schedule adherence "
        f"{format(raw_value, 'f')}% from sample size {sample_size}; normalized directly "
        f"to {format(normalized, 'f')} and weighted by {format(weight, 'f')}"
    )


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


def _history_by_supplier(
    history: tuple[SupplierHistoricalPerformanceInput, ...],
    offers: tuple[SupplierOffer, ...],
) -> dict[str, SupplierHistoricalPerformanceInput]:
    provided: dict[str, SupplierHistoricalPerformanceInput] = {}
    for item in history:
        if not isinstance(item, SupplierHistoricalPerformanceInput):
            raise DomainValidationError("Historical performance inputs must be typed.")
        if item.supplier_id in provided:
            raise DomainValidationError(
                "Historical supplier mappings must be unambiguous; duplicate supplier: "
                f"{item.supplier_id}."
            )
        provided[item.supplier_id] = item

    known_supplier_ids = {offer.supplier_id for offer in offers}
    unknown = sorted(set(provided) - known_supplier_ids)
    if unknown:
        raise DomainValidationError(
            "Historical performance references unknown suppliers: " + ", ".join(unknown) + "."
        )
    return provided


def _score_eligible_offers(
    requirement: PurchaseRequirement,
    eligible: tuple[SupplierOffer, ...],
    excluded_offers: tuple[ExcludedOffer, ...],
    profile: StrategicProfile | HistoricalScoringProfile,
    criteria: tuple[tuple[Criterion, CriterionDirection], ...],
    history_by_supplier: dict[str, SupplierHistoricalPerformanceInput] | None = None,
) -> DecisionResult:
    normalized_by_criterion: dict[Criterion, tuple[Decimal, ...]] = {}
    for criterion, direction in criteria:
        if criterion is Criterion.DELIVERY_SCHEDULE_ADHERENCE:
            if history_by_supplier is None:
                raise DomainValidationError("Historical performance is required for scoring.")
            raw_values = tuple(history_by_supplier[offer.supplier_id].value for offer in eligible)
            if any(value is None for value in raw_values):
                raise DomainValidationError("Usable historical performance requires a value.")
            normalized_by_criterion[criterion] = tuple(
                value / Decimal("100") for value in raw_values if value is not None
            )
        else:
            raw_values = tuple(_raw_value(offer, criterion) for offer in eligible)
            normalized_by_criterion[criterion] = normalize_values(raw_values, direction)

    scored: list[tuple[SupplierOffer, Decimal, tuple[CriterionContribution, ...]]] = []
    for index, offer in enumerate(eligible):
        contributions: list[CriterionContribution] = []
        for criterion, direction in criteria:
            if criterion is Criterion.DELIVERY_SCHEDULE_ADHERENCE:
                if history_by_supplier is None:
                    raise DomainValidationError("Historical performance is required for scoring.")
                historical = history_by_supplier[offer.supplier_id]
                if historical.value is None:
                    raise DomainValidationError("Usable historical performance requires a value.")
                raw_value = historical.value
                sample_size = historical.sample_size
                explanation = _historical_explanation(
                    raw_value,
                    sample_size,
                    profile.weight_for(criterion),
                )
            else:
                raw_value = _raw_value(offer, criterion)
            normalized_value = normalized_by_criterion[criterion][index]
            weight = profile.weight_for(criterion)
            contribution = normalized_value * weight
            if criterion is Criterion.DELIVERY_SCHEDULE_ADHERENCE:
                contributions.append(
                    HistoricalCriterionContribution(
                        criterion=criterion,
                        direction=direction,
                        raw_value=raw_value,
                        normalized_value=normalized_value,
                        weight=weight,
                        weighted_contribution=contribution,
                        sample_size=sample_size,
                        explanation=explanation,
                    )
                )
            else:
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
        excluded_offers=excluded_offers,
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
    return _score_eligible_offers(
        requirement=requirement,
        eligible=eligible,
        excluded_offers=constraint_evaluation.excluded_offers,
        profile=profile,
        criteria=_CRITERIA,
    )


def evaluate_historical_decision(
    requirement: PurchaseRequirement,
    offers: Iterable[SupplierOffer],
    profile: HistoricalScoringProfile,
    historical_performance: Iterable[SupplierHistoricalPerformanceInput],
) -> HistoricalScoringResult:
    """Explicitly evaluate the fixed complete-case historical scoring policy."""

    if not isinstance(profile, HistoricalScoringProfile):
        raise DomainValidationError("A versioned historical scoring profile is required.")
    offer_tuple = tuple(offers)
    _validate_offer_set(offer_tuple)
    ordered_offers = tuple(sorted(offer_tuple, key=lambda offer: offer.offer_id))
    history_by_supplier = _history_by_supplier(
        tuple(historical_performance),
        ordered_offers,
    )

    baseline = evaluate_decision(requirement, ordered_offers, profile.fallback_profile)
    constraint_evaluation = evaluate_hard_constraints(requirement, ordered_offers)
    eligible = constraint_evaluation.eligible_offers
    if not eligible:
        return HistoricalScoringResult(
            decision_result=baseline,
            historical_criterion_active=False,
            explanation=_HISTORY_INACTIVE_NO_ELIGIBLE,
        )

    affected_offers = tuple(
        offer.offer_id
        for offer in eligible
        if (
            offer.supplier_id not in history_by_supplier
            or not history_by_supplier[offer.supplier_id].usable
        )
    )
    if affected_offers:
        affected_suppliers = tuple(
            sorted(
                {
                    offer.supplier_id
                    for offer in eligible
                    if (
                        offer.supplier_id not in history_by_supplier
                        or not history_by_supplier[offer.supplier_id].usable
                    )
                }
            )
        )
        return HistoricalScoringResult(
            decision_result=baseline,
            historical_criterion_active=False,
            explanation=_HISTORY_INACTIVE_MISSING,
            affected_offer_ids=affected_offers,
            affected_supplier_ids=affected_suppliers,
        )

    result = _score_eligible_offers(
        requirement=requirement,
        eligible=eligible,
        excluded_offers=constraint_evaluation.excluded_offers,
        profile=profile,
        criteria=_HISTORICAL_CRITERIA,
        history_by_supplier=history_by_supplier,
    )
    return HistoricalScoringResult(
        decision_result=result,
        historical_criterion_active=True,
        explanation=_HISTORY_ACTIVE,
    )
