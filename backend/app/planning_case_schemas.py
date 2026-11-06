"""Strict HTTP request facts. Caller attribution is not authentication.

Limits the application also enforces are read from the application constants, so the
schema rejects the same requests (HTTP 422) the use case would.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator

from application.planning_cases import SCENARIO_KINDS, ScenarioDelta, SupplierChange
from application.planning_decisions import (
    DECISION_OUTCOMES,
    MAX_ACTOR_LENGTH,
    MAX_RATIONALE_LENGTH,
)
from application.planning_input import (
    MAX_EPSILONS,
    MAX_SUPPLIERS,
    SCORE_QUANTITIES,
    OdooHistoryPlanningFacts,
    SupplierFacts,
)
from application.planning_serialization import SHA256_HEX
from application.provenance import SourceAttribution
from application.stored_contracts import PENDING_HISTORY_REFERENCE
from backend.app.api_common import StrictModel, explicit_utc_text
from decision_core.planning.models import (
    MinimumOrder,
    PlanningPolicy,
    ProcurementRequirement,
    QuantityRange,
    SupplierTerms,
)
from supplier_evaluation.contracts import HISTORY_SOURCE

Text = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=255, pattern=r"^\S(?:.*\S)?$")
]
Money = Annotated[
    str, StringConstraints(strict=True, max_length=64, pattern=r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
]
Count = Annotated[int, Field(strict=True, ge=0)]
PositiveCount = Annotated[int, Field(strict=True, ge=1)]
UtcTime = Annotated[datetime, Field()]


class SourceRequest(StrictModel):
    source_type: Text
    source_reference: Text
    observed_at: UtcTime

    @field_validator("observed_at", mode="before")
    @classmethod
    def utc_text(cls, value):
        return explicit_utc_text(value)

    def attribution(self, field: str) -> SourceAttribution:
        return SourceAttribution(field, self.source_type, self.source_reference, self.observed_at)


class RangeRequest(StrictModel):
    minimum: PositiveCount
    maximum: PositiveCount


class RequirementRequest(StrictModel):
    product_id: Text
    approved_quantity: PositiveCount
    quantity_unit: Text
    currency: Text
    required_date: date

    @field_validator("required_date", mode="before")
    @classmethod
    def date_text(cls, value):
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("An ISO date string is required.")
        return value


class PolicyRequest(StrictModel):
    max_suppliers: PositiveCount
    concentration_limit: Money | None
    epsilons: list[Money] = Field(min_length=1, max_length=MAX_EPSILONS)
    diversification_epsilon: Money | None = None


class CommercialSupplierRequest(StrictModel):
    supplier_id: Text
    offer_id: Text
    unit_price: Money
    capacity: Count
    available: bool = Field(strict=True)
    minimum_order_quantity: PositiveCount | None
    price_quantities: RangeRequest
    delivery_quantities: RangeRequest
    promised_date: date
    source: SourceRequest

    @field_validator("promised_date", mode="before")
    @classmethod
    def date_text(cls, value):
        return RequirementRequest.date_text(value)


class OdooHistoryTermsRequest(StrictModel):
    company_id: Text
    as_of: UtcTime
    approval_reference: Text
    requirement: RequirementRequest
    requirement_source: SourceRequest
    policy: PolicyRequest
    policy_source: SourceRequest
    suppliers: list[CommercialSupplierRequest] = Field(min_length=1, max_length=MAX_SUPPLIERS)

    @field_validator("as_of", mode="before")
    @classmethod
    def utc_text(cls, value):
        return explicit_utc_text(value)

    def to_facts(self):
        r, p = self.requirement, self.policy
        suppliers = tuple(
            SupplierFacts(
                s.offer_id,
                SupplierTerms(
                    s.supplier_id,
                    r.product_id,
                    r.quantity_unit,
                    r.currency,
                    Decimal(s.unit_price),
                    s.capacity,
                    s.available,
                    MinimumOrder(s.minimum_order_quantity),
                    QuantityRange(s.price_quantities.minimum, s.price_quantities.maximum),
                    QuantityRange(s.delivery_quantities.minimum, s.delivery_quantities.maximum),
                    s.promised_date,
                ),
                s.source.attribution("commercial_terms"),
                (),
                PENDING_HISTORY_REFERENCE,
                SCORE_QUANTITIES,
            )
            for s in self.suppliers
        )
        return OdooHistoryPlanningFacts(
            self.company_id,
            self.as_of,
            ProcurementRequirement(
                r.product_id, r.approved_quantity, r.quantity_unit, r.currency, r.required_date
            ),
            self.approval_reference,
            self.requirement_source.attribution("requirement"),
            PlanningPolicy(
                p.max_suppliers,
                None if p.concentration_limit is None else Decimal(p.concentration_limit),
                tuple(Decimal(e) for e in p.epsilons),
                None if p.diversification_epsilon is None else Decimal(p.diversification_epsilon),
            ),
            self.policy_source.attribution("policy"),
            suppliers,
            HISTORY_SOURCE,
        )


class OdooHistoryCreateRequest(StrictModel):
    purchase_group_id: int = Field(gt=0, strict=True)
    terms: OdooHistoryTermsRequest


class ChangeRequest(StrictModel):
    supplier_id: Text
    available: bool | None = Field(default=None, strict=True)
    capacity: Count | None = None
    unit_price: Money | None = None


class ScenarioRequest(StrictModel):
    kind: Literal[SCENARIO_KINDS]
    source: SourceRequest
    suppliers: list[ChangeRequest] = Field(default_factory=list, max_length=MAX_SUPPLIERS)
    approved_quantity: PositiveCount | None = None

    def to_delta(self) -> ScenarioDelta:
        return ScenarioDelta(
            self.kind,
            self.source.attribution("scenario_delta"),
            tuple(
                SupplierChange(
                    s.supplier_id,
                    s.available,
                    s.capacity,
                    None if s.unit_price is None else Decimal(s.unit_price),
                )
                for s in self.suppliers
            ),
            self.approved_quantity,
        )


class PlanningCaseResponse(StrictModel):
    case_id: str
    created_at: datetime
    parent_id: str | None
    snapshot_hash: str
    snapshot: dict
    idempotent_replay: bool
    final_decision: dict | None = None


class PlanningFinalDecisionRequest(StrictModel):
    snapshot_hash: str = Field(pattern=f"^{SHA256_HEX}$", min_length=64, max_length=64)
    outcome: Literal[DECISION_OUTCOMES]
    # At most five stored plans: minimum cost, three epsilon alternatives, the balanced plan.
    plan_index: int | None = Field(default=None, strict=True, ge=0, le=4)
    actor_reference: str = Field(min_length=1, max_length=MAX_ACTOR_LENGTH)
    rationale: str | None = Field(default=None, max_length=MAX_RATIONALE_LENGTH)
    demonstration_acknowledged: bool = Field(strict=True)
