"""Small neutral mock API DTOs, separate from Reflex state and the Decision Core."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class DTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CaseDTO(DTO):
    case_id: str
    version: str
    product: str
    quantity: int
    uom: str
    currency: str
    required_date: str
    max_suppliers: int
    concentration_limit: str
    allowed_premium: str


class SupplierDTO(DTO):
    supplier_id: str
    name: str
    unit_price: str
    capacity: int
    minimum_quantity: int
    commitment: str
    historical_indicator: str
    risk_score: str | None
    predicted_class: str
    source_status: str
    color: str
    explanation: list[str]


class AllocationDTO(DTO):
    supplier_id: str
    name: str
    quantity: int
    share: float
    color: str


class PlanDTO(DTO):
    plan_id: str
    title: str
    feasible: bool
    quantity: int
    total_cost: str
    cost_premium: str
    risk_exposure: str
    largest_share: str
    supplier_count: int
    allocations: tuple[AllocationDTO, ...]
    explanations: tuple[str, ...]


class DeltaDTO(DTO):
    plan_id: str
    cost_change: str
    risk_change: str
    allocation_change: str
    feasibility_change: str


class ResultDTO(DTO):
    label: str
    quantity: int
    plans: list[PlanDTO]
    reasons: list[str]
    deltas: list[DeltaDTO]


class ApprovedDTO(DTO):
    approval_id: str
    case_id: str
    case_version: str
    scenario_key: str
    plan: PlanDTO
    note: str
    snapshot_hash: str
    status: str = "Approved locally"


class PdfDTO(DTO):
    status: Literal["pending", "ready"]
    approval_id: str
    snapshot_hash: str
    message: str
    download_url: str | None = None
    file_name: str = "approved-procurement-plan.pdf"


class ServiceError(Exception):
    """Safe mock-client error; raw transport/implementation details are never UI text."""
