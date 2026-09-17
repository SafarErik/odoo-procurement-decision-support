"""Stable HTTP response schemas owned by the API boundary."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

_DECIMAL_STRING_PATTERN = r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$"
DecimalString = Annotated[
    str,
    StringConstraints(strict=True, pattern=_DECIMAL_STRING_PATTERN),
]

_DECISION_REQUEST_EXAMPLE = {
    "requirement": {
        "requirement_id": "REQ-100",
        "requested_quantity": "100",
    },
    "offers": [
        {
            "offer_id": "Offer A",
            "supplier_id": "Supplier A",
            "unit_price": "10",
            "lead_time_days": "10",
            "minimum_order_quantity": "50",
        },
        {
            "offer_id": "Offer B",
            "supplier_id": "Supplier B",
            "unit_price": "12",
            "lead_time_days": "5",
            "minimum_order_quantity": "100",
        },
        {
            "offer_id": "Offer C",
            "supplier_id": "Supplier C",
            "unit_price": "9",
            "lead_time_days": "8",
            "minimum_order_quantity": "150",
        },
    ],
    "profile": {
        "name": "cost-focused",
        "unit_price_weight": "0.7",
        "lead_time_weight": "0.3",
    },
}


class HealthResponse(BaseModel):
    """Status response for service discovery and lightweight integration checks."""

    status: Literal["ok"]
    service: str
    api_version: str


class MoneyResponse(BaseModel):
    """Currency-aware amount represented without floating-point ambiguity."""

    amount: str
    currency: str


class RfqSummaryResponse(BaseModel):
    """ERP-neutral read model for an open request for quotation."""

    source_id: str
    reference: str
    vendor_name: str
    order_date: datetime
    status: Literal["draft", "sent", "awaiting_approval", "unknown"]
    total: MoneyResponse


class RfqListResponse(BaseModel):
    """Bounded collection returned by the procurement API."""

    items: list[RfqSummaryResponse]
    count: int
    retrieved_at: datetime


class DecisionRequirementRequest(BaseModel):
    """Canonical purchase requirement supplied by the caller."""

    requirement_id: str = Field(description="Caller-owned requirement identifier.")
    requested_quantity: DecimalString = Field(
        description="Requested quantity as a canonical decimal string.",
        examples=["100"],
    )


class SupplierOfferRequest(BaseModel):
    """Canonical supplier offer independent of any ERP representation."""

    offer_id: str = Field(description="Caller-owned offer identifier.")
    supplier_id: str = Field(description="Caller-owned supplier identifier.")
    unit_price: DecimalString = Field(
        description="Unit price as a canonical decimal string.",
        examples=["10"],
    )
    lead_time_days: DecimalString = Field(
        description="Lead time in days as a canonical decimal string.",
        examples=["10"],
    )
    minimum_order_quantity: DecimalString = Field(
        description="Minimum order quantity as a canonical decimal string.",
        examples=["50"],
    )


class StrategicProfileRequest(BaseModel):
    """Named criterion weights supplied for this evaluation."""

    name: str = Field(description="Caller-owned strategic-profile name.")
    unit_price_weight: DecimalString = Field(
        description="Unit-price weight as a canonical decimal string.",
        examples=["0.7"],
    )
    lead_time_weight: DecimalString = Field(
        description="Lead-time weight as a canonical decimal string.",
        examples=["0.3"],
    )


class DecisionEvaluationRequest(BaseModel):
    """Complete canonical input for one procurement decision evaluation."""

    model_config = ConfigDict(json_schema_extra={"example": _DECISION_REQUEST_EXAMPLE})

    requirement: DecisionRequirementRequest
    offers: list[SupplierOfferRequest]
    profile: StrategicProfileRequest


class DecisionRequirementResponse(BaseModel):
    """Purchase requirement returned with the explained result."""

    requirement_id: str
    requested_quantity: str = Field(
        description="Requested quantity represented as a decimal string."
    )


class StrategicProfileResponse(BaseModel):
    """Strategic profile returned with the explained result."""

    name: str
    unit_price_weight: str = Field(description="Unit-price weight represented as a decimal string.")
    lead_time_weight: str = Field(description="Lead-time weight represented as a decimal string.")


class RecommendedOfferResponse(BaseModel):
    """Identity of the first-ranked eligible offer."""

    offer_id: str
    supplier_id: str


class CriterionContributionResponse(BaseModel):
    """Trace of one criterion's contribution to a relative WSM score."""

    criterion: Literal["unit_price", "lead_time_days"]
    direction: Literal["cost", "benefit"]
    raw_value: str = Field(description="Original value represented as a decimal string.")
    normalized_value: str = Field(
        description="Eligible-set normalized value represented as a decimal string."
    )
    weight: str = Field(description="Applied weight represented as a decimal string.")
    weighted_contribution: str = Field(
        description="Normalized value times weight, represented as a decimal string."
    )


class RankedOfferResponse(BaseModel):
    """Eligible offer with its deterministic rank and complete explanation."""

    rank: int
    offer_id: str
    supplier_id: str
    unit_price: str = Field(description="Original unit price as a decimal string.")
    lead_time_days: str = Field(description="Original lead time as a decimal string.")
    minimum_order_quantity: str = Field(
        description="Original minimum order quantity as a decimal string."
    )
    total_score: str = Field(description="Relative WSM score as a decimal string.")
    contributions: list[CriterionContributionResponse]


class ExcludedOfferResponse(BaseModel):
    """Offer excluded by a hard constraint before normalization and scoring."""

    offer_id: str
    supplier_id: str
    failed_constraint: Literal["minimum_order_quantity"]
    explanation: str
    requested_quantity: str = Field(description="Requested quantity as a decimal string.")
    minimum_order_quantity: str = Field(
        description="Offer minimum order quantity as a decimal string."
    )


class DecisionEvaluationResponse(BaseModel):
    """Complete explained decision-support result for caller-supplied data."""

    requirement: DecisionRequirementResponse
    profile: StrategicProfileResponse
    recommended_offer: RecommendedOfferResponse | None
    ranked_offers: list[RankedOfferResponse]
    excluded_offers: list[ExcludedOfferResponse]
