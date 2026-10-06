"""Strict controlled V2 HTTP facts. Caller attribution is not authentication."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator

from application.decision_input_assembly import SourceAttribution
from application.planning_cases import ScenarioDelta, SupplierChange
from application.planning_input import PlanningFacts, SupplierFacts
from backend.app.decision_case_schemas import StrictModel, _explicit_utc_text
from decision_core.planning.models import (
    MinimumOrder,
    PlanningPolicy,
    ProcurementRequirement,
    QuantityRange,
    SupplierTerms,
)
from supplier_evaluation.contracts import SYNTHETIC, Context, LineEvidence, QuantityValidity

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
        return _explicit_utc_text(value)

    def attribution(self, field: str) -> SourceAttribution:
        return SourceAttribution(field, self.source_type, self.source_reference, self.observed_at)


class ReceiptRequest(StrictModel):
    line_id: Text
    expected_arrival: UtcTime
    completed_at: UtcTime
    available_at: UtcTime

    @field_validator("expected_arrival", "completed_at", "available_at", mode="before")
    @classmethod
    def utc_text(cls, value):
        return _explicit_utc_text(value)


class RangeRequest(StrictModel):
    minimum: PositiveCount
    maximum: PositiveCount


class ValidityRequest(RangeRequest):
    reference: Text


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
    epsilons: list[Money] = Field(min_length=1, max_length=3)


class SupplierRequest(StrictModel):
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
    receipts: list[ReceiptRequest] = Field(min_length=3, max_length=50)
    history_reference: Text
    score_quantities: ValidityRequest

    @field_validator("promised_date", mode="before")
    @classmethod
    def date_text(cls, value):
        return RequirementRequest.date_text(value)


class PlanningCreateRequest(StrictModel):
    source_type: Literal["t14_synthetic"]
    company_id: Text
    as_of: UtcTime
    approval_reference: Text
    requirement: RequirementRequest
    requirement_source: SourceRequest
    policy: PolicyRequest
    policy_source: SourceRequest
    suppliers: list[SupplierRequest] = Field(min_length=1, max_length=10)

    @field_validator("as_of", mode="before")
    @classmethod
    def utc_text(cls, value):
        return _explicit_utc_text(value)

    def to_facts(self) -> PlanningFacts:
        r, p = self.requirement, self.policy
        requirement = ProcurementRequirement(
            r.product_id, r.approved_quantity, r.quantity_unit, r.currency, r.required_date
        )
        policy = PlanningPolicy(
            p.max_suppliers,
            None if p.concentration_limit is None else Decimal(p.concentration_limit),
            tuple(Decimal(e) for e in p.epsilons),
        )
        suppliers = []
        for s in self.suppliers:
            context = Context(s.supplier_id, self.company_id, r.product_id, r.quantity_unit)
            terms = SupplierTerms(
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
            )
            receipts = tuple(
                LineEvidence(
                    line.line_id,
                    context,
                    line.expected_arrival,
                    line.completed_at,
                    line.available_at,
                )
                for line in s.receipts
            )
            suppliers.append(
                SupplierFacts(
                    s.offer_id,
                    terms,
                    s.source.attribution("commercial_terms"),
                    receipts,
                    s.history_reference,
                    QuantityValidity(
                        s.score_quantities.minimum,
                        s.score_quantities.maximum,
                        s.score_quantities.reference,
                    ),
                )
            )
        return PlanningFacts(
            self.company_id,
            self.as_of,
            requirement,
            self.approval_reference,
            self.requirement_source.attribution("requirement"),
            policy,
            self.policy_source.attribution("policy"),
            tuple(suppliers),
            SYNTHETIC,
        )


class ChangeRequest(StrictModel):
    supplier_id: Text
    available: bool | None = Field(default=None, strict=True)
    capacity: Count | None = None
    unit_price: Money | None = None


class ScenarioRequest(StrictModel):
    kind: Literal[
        "supplier_outage", "capacity_reduction", "demand_increase", "price_increase", "combined"
    ]
    source: SourceRequest
    suppliers: list[ChangeRequest] = Field(default_factory=list, max_length=10)
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
