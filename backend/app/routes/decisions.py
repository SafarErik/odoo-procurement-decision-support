"""Thin HTTP route for canonical procurement decision evaluation."""

from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

from application.decisions import evaluate_procurement_decision
from backend.app.schemas import (
    CriterionContributionResponse,
    DecisionEvaluationRequest,
    DecisionEvaluationResponse,
    DecisionRequirementResponse,
    ExcludedOfferResponse,
    RankedOfferResponse,
    RecommendedOfferResponse,
    StrategicProfileResponse,
)
from decision_core import (
    DecisionResult,
    DomainValidationError,
    PurchaseRequirement,
    StrategicProfile,
    SupplierOffer,
)

router = APIRouter(prefix="/api/v1/procurement/decisions", tags=["procurement decisions"])


@router.post(
    "/evaluate",
    response_model=DecisionEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate canonical supplier offers",
    description=(
        "Evaluates caller-supplied canonical procurement data using relative Weighted "
        "Sum Model scores. Decision numeric values are decimal strings; excluded offers "
        "are not normalized or scored. The recommendation supports a human decision and "
        "does not select a supplier automatically, persist a decision, or write to Odoo."
    ),
)
def evaluate_procurement_offers(
    request: DecisionEvaluationRequest,
) -> DecisionEvaluationResponse:
    """Map canonical HTTP input to the application use case and its explained result."""

    try:
        requirement = PurchaseRequirement(
            requirement_id=request.requirement.requirement_id,
            requested_quantity=Decimal(request.requirement.requested_quantity),
        )
        offers = tuple(
            SupplierOffer(
                offer_id=offer.offer_id,
                supplier_id=offer.supplier_id,
                unit_price=Decimal(offer.unit_price),
                lead_time_days=Decimal(offer.lead_time_days),
                minimum_order_quantity=Decimal(offer.minimum_order_quantity),
            )
            for offer in request.offers
        )
        profile = StrategicProfile(
            name=request.profile.name,
            unit_price_weight=Decimal(request.profile.unit_price_weight),
            lead_time_weight=Decimal(request.profile.lead_time_weight),
        )
        result = evaluate_procurement_decision(requirement, offers, profile)
    except DomainValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_decision_input",
                "message": str(error),
            },
        ) from error

    return _to_response(result)


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


def _to_response(result: DecisionResult) -> DecisionEvaluationResponse:
    recommendation = result.recommended_offer
    return DecisionEvaluationResponse(
        requirement=DecisionRequirementResponse(
            requirement_id=result.requirement.requirement_id,
            requested_quantity=_decimal_string(result.requirement.requested_quantity),
        ),
        profile=StrategicProfileResponse(
            name=result.profile.name,
            unit_price_weight=_decimal_string(result.profile.unit_price_weight),
            lead_time_weight=_decimal_string(result.profile.lead_time_weight),
        ),
        recommended_offer=(
            RecommendedOfferResponse(
                offer_id=recommendation.offer.offer_id,
                supplier_id=recommendation.offer.supplier_id,
            )
            if recommendation is not None
            else None
        ),
        ranked_offers=[
            RankedOfferResponse(
                rank=ranked.rank,
                offer_id=ranked.offer.offer_id,
                supplier_id=ranked.offer.supplier_id,
                unit_price=_decimal_string(ranked.offer.unit_price),
                lead_time_days=_decimal_string(ranked.offer.lead_time_days),
                minimum_order_quantity=_decimal_string(ranked.offer.minimum_order_quantity),
                total_score=_decimal_string(ranked.total_score),
                contributions=[
                    CriterionContributionResponse(
                        criterion=contribution.criterion.value,
                        direction=contribution.direction.value,
                        raw_value=_decimal_string(contribution.raw_value),
                        normalized_value=_decimal_string(contribution.normalized_value),
                        weight=_decimal_string(contribution.weight),
                        weighted_contribution=_decimal_string(contribution.weighted_contribution),
                    )
                    for contribution in ranked.contributions
                ],
            )
            for ranked in result.ranked_offers
        ],
        excluded_offers=[
            ExcludedOfferResponse(
                offer_id=excluded.offer.offer_id,
                supplier_id=excluded.offer.supplier_id,
                failed_constraint=excluded.failed_constraint.value,
                explanation=excluded.explanation,
                requested_quantity=_decimal_string(excluded.requested_quantity),
                minimum_order_quantity=_decimal_string(excluded.minimum_order_quantity),
            )
            for excluded in result.excluded_offers
        ],
    )
