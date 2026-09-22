"""Strict T12 request and stable stored-snapshot response contracts."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

DecimalText = Annotated[
    str, StringConstraints(strict=True, pattern=r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _explicit_utc_text(value: object) -> object:
    if not isinstance(value, str) or not value.endswith(("Z", "+00:00")):
        raise ValueError("An explicit UTC timestamp string is required.")
    return value


class SourcedDecimalRequest(StrictModel):
    value: DecimalText
    source_type: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    observed_at: datetime

    @field_validator("observed_at", mode="before")
    @classmethod
    def utc_text(cls, value: object) -> object:
        return _explicit_utc_text(value)

    @field_validator("observed_at")
    @classmethod
    def explicit_utc(cls, value: datetime) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
            or value.utcoffset().total_seconds() != 0
        ):
            raise ValueError("An explicit UTC timestamp is required.")
        return value


class SupplementalTermsRequest(StrictModel):
    offer_id: str = Field(min_length=1)
    hard_minimum_order_quantity: SourcedDecimalRequest
    supplier_promised_lead_time_days: SourcedDecimalRequest


class SupplierHistoryRequest(StrictModel):
    supplier_id: str = Field(min_length=1)
    purchase_line_ids: list[str] = Field(min_length=1, max_length=50)


class HistorySelectionRequest(StrictModel):
    window_end: datetime
    suppliers: list[SupplierHistoryRequest] = Field(min_length=1, max_length=20)

    @field_validator("window_end", mode="before")
    @classmethod
    def utc_text(cls, value: object) -> object:
        return _explicit_utc_text(value)

    @field_validator("window_end")
    @classmethod
    def explicit_utc(cls, value: datetime) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
            or value.utcoffset().total_seconds() != 0
        ):
            raise ValueError("An explicit UTC timestamp is required.")
        return value


class DecisionCaseCreateRequest(StrictModel):
    purchase_group_id: int = Field(gt=0, strict=True)
    supplemental_terms: list[SupplementalTermsRequest] = Field(min_length=1, max_length=20)
    scoring_policy_id: Literal[
        "cost-focused",
        "urgent",
        "balanced",
        "cost_focused_history_v1",
        "urgent_history_v1",
        "risk_averse_history_v1",
    ]
    history_selection: HistorySelectionRequest | None = None


class FinalDecisionRequest(StrictModel):
    outcome: Literal["accept_recommendation", "override_recommendation", "no_award"]
    selected_offer_id: str | None = None
    rationale: str | None = None
    decided_at: datetime
    actor_reference: str = Field(
        min_length=1,
        max_length=255,
        description="Caller-supplied audit text; not an authenticated identity.",
    )

    @field_validator("decided_at", mode="before")
    @classmethod
    def utc_text(cls, value: object) -> object:
        return _explicit_utc_text(value)

    @field_validator("decided_at")
    @classmethod
    def explicit_utc(cls, value: datetime) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
            or value.utcoffset().total_seconds() != 0
        ):
            raise ValueError("An explicit UTC timestamp is required.")
        return value


class HumanDecisionResponse(StrictModel):
    outcome: str
    selected_offer_id: str | None
    rationale: str | None
    decided_at: datetime
    actor_reference: str
    idempotency_key: str


class RequirementSnapshot(StrictModel):
    requirement_id: str
    requested_quantity: str


class OfferSnapshot(StrictModel):
    offer_id: str
    supplier_id: str
    unit_price: str
    lead_time_days: str
    minimum_order_quantity: str


class ProfileSnapshot(StrictModel):
    profile_type: Literal["strategic", "historical"]
    name: str
    unit_price_weight: str
    lead_time_weight: str
    delivery_schedule_adherence_weight: str | None = None
    fallback_profile: "ProfileSnapshot | None" = None


class HistoryWarningSnapshot(StrictModel):
    code: str
    message: str
    affected_line_ids: list[str]


class HistorySnapshot(StrictModel):
    metric_id: str
    value: str | None
    sample_size: int
    observation_window_start: datetime
    observation_window_end: datetime
    observed_at: datetime
    supplier_id: str
    availability: str
    warnings: list[HistoryWarningSnapshot]


class CanonicalInputSnapshot(StrictModel):
    snapshot_version: int
    requirement: RequirementSnapshot
    offers: list[OfferSnapshot]
    profile: ProfileSnapshot
    historical_performance: list[HistorySnapshot]


class ScoringPolicySnapshot(StrictModel):
    snapshot_version: int
    policy: ProfileSnapshot


class ContributionSnapshot(StrictModel):
    contribution_type: Literal["standard", "historical"]
    criterion: str
    direction: str
    raw_value: str
    normalized_value: str
    weight: str
    weighted_contribution: str
    sample_size: int | None = None
    explanation: str | None = None


class RankedOfferSnapshot(StrictModel):
    rank: int
    offer: OfferSnapshot
    total_score: str
    contributions: list[ContributionSnapshot]


class ExcludedOfferSnapshot(StrictModel):
    offer: OfferSnapshot
    failed_constraint: str
    explanation: str
    requested_quantity: str
    minimum_order_quantity: str


class DecisionResultSnapshot(StrictModel):
    requirement: RequirementSnapshot
    profile: ProfileSnapshot
    ranked_offers: list[RankedOfferSnapshot]
    excluded_offers: list[ExcludedOfferSnapshot]


class EvaluationSnapshotResponse(StrictModel):
    snapshot_version: int
    result_type: Literal["legacy", "historical"]
    decision_result: DecisionResultSnapshot
    historical_criterion_active: bool | None = None
    explanation: str | None = None
    affected_offer_ids: list[str] | None = None
    affected_supplier_ids: list[str] | None = None


class ProvenanceEntrySnapshot(StrictModel):
    canonical_path: str
    field_name: str
    source_type: str
    source_reference: str
    observed_at: datetime


class ProvenanceSnapshot(StrictModel):
    snapshot_version: int
    entries: list[ProvenanceEntrySnapshot]


class DecisionCaseResponse(StrictModel):
    decision_case_id: str
    snapshot_version: int
    created_at: datetime
    state: Literal["evaluated", "finalized"]
    canonical_input: CanonicalInputSnapshot
    scoring_policy: ScoringPolicySnapshot
    evaluation: EvaluationSnapshotResponse
    provenance: ProvenanceSnapshot
    recommended_offer_id: str | None
    human_decision: HumanDecisionResponse | None
    idempotent_replay: bool = False
