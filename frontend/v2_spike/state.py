"""Session-local presentation workflow. All results cross the mock client abstraction."""

import reflex as rx

from frontend.v2_spike.contracts import (
    ApprovedDTO,
    CaseDTO,
    PlanDTO,
    ResultDTO,
    ServiceError,
    SupplierDTO,
)
from frontend.v2_spike.presentation import (
    EMPTY_PLAN,
    PlanView,
    allocation_series,
    plan_view,
    tradeoff_point,
)
from frontend.v2_spike.service import client

OPERATIONS = {
    "Supplier unavailable": "outage",
    "Capacity reduced to 30": "capacity",
    "Demand increased to 120": "demand",
    "Unit price increased by 20%": "price",
    "Combined supply disruption": "shortfall",
}
SUPPLIERS = {
    "A · Northline Components": "A",
    "B · Danube Supply": "B",
    "C · Pannon Industrial": "C",
}


class CockpitState(rx.State):
    case: CaseDTO | None = None
    suppliers: list[SupplierDTO] = []
    result: ResultDTO | None = None
    plans: list[PlanDTO] = []
    selected_id: str = ""
    scenario_key: str = "baseline"
    operation: str = "Supplier unavailable"
    supplier_choice: str = "A · Northline Components"
    preview_mode: str = "Ready"
    note: str = ""
    approved: ApprovedDTO | None = None
    loading: bool = False
    running: bool = False
    approving: bool = False
    exporting: bool = False
    error: str = ""
    approval_error: str = ""
    pdf_message: str = ""

    @rx.var
    def busy(self) -> bool:
        return self.loading or self.running or self.approving or self.exporting

    @rx.var
    def locked(self) -> bool:
        return self.approved is not None

    @rx.var
    def selected(self) -> PlanDTO:
        return next((plan for plan in self.plans if plan.plan_id == self.selected_id), EMPTY_PLAN)

    @rx.var
    def has_selection(self) -> bool:
        return self.selected.plan_id != "" and self.selected.feasible

    @rx.var
    def can_approve(self) -> bool:
        return (
            self.has_selection
            and not self.busy
            and not self.locked
            and not self.error
            and (self.preview_mode not in ("Risk unavailable", "No plans", "Service unavailable"))
        )

    @rx.var
    def plan_views(self) -> list[PlanView]:
        return [plan_view(plan) for plan in self.plans]

    @rx.var
    def selected_view(self) -> PlanView:
        return (
            plan_view(self.selected)
            if self.has_selection
            else PlanView(
                **EMPTY_PLAN.model_dump(),
                cost_display="—",
                premium_display="—",
                risk_display="—",
                share_display="—",
                color="#6C7C88",
            )
        )

    @rx.var
    def allocation_data(self) -> list[dict[str, str | float]]:
        return allocation_series(self.selected) if self.has_selection else []

    @rx.var
    def minimum_point(self) -> list[dict[str, str | float]]:
        return [tradeoff_point(p) for p in self.plans if p.plan_id == "minimum"]

    @rx.var
    def balanced_point(self) -> list[dict[str, str | float]]:
        return [tradeoff_point(p) for p in self.plans if p.plan_id == "balanced"]

    @rx.var
    def lower_point(self) -> list[dict[str, str | float]]:
        return [tradeoff_point(p) for p in self.plans if p.plan_id == "lower"]

    @rx.var
    def case_quantity(self) -> str:
        return f"{self.case.quantity} {self.case.uom}" if self.case else "—"

    @rx.var
    def active_context(self) -> str:
        if self.result is None:
            return "Updating case results…" if self.busy else "Case not loaded"
        return f"{self.result.label} · {self.result.quantity} Units"

    @rx.var
    def infeasible(self) -> bool:
        return bool(self.result and self.result.reasons and not self.plans)

    @rx.var
    def scenario_delta(self) -> list[str]:
        if self.result is None:
            return []
        delta = next((d for d in self.result.deltas if d.plan_id == self.selected_id), None)
        if delta is None:
            return []
        return [
            f"Cost change: €{delta.cost_change}",
            f"Score-exposure change: {delta.risk_change}",
            f"Allocation change: {delta.allocation_change}",
            delta.feasibility_change,
        ]

    @rx.var
    def reasons(self) -> list[str]:
        return self.result.reasons if self.result else []

    @rx.var
    def approval_label(self) -> str:
        return (
            f"{self.approved.approval_id} · read-only"
            if self.approved
            else "Awaiting human approval"
        )

    @rx.var
    def approved_summary(self) -> str:
        return f"{self.approved.plan.title} · {self.approved.scenario_key}" if self.approved else ""

    @rx.var
    def approved_hash(self) -> str:
        return self.approved.snapshot_hash[:16] if self.approved else ""

    @rx.event
    def select_plan(self, plan_id: str):
        if self.locked or self.busy or self.error:
            return
        if any(p.plan_id == plan_id and p.feasible for p in self.plans):
            self.selected_id = plan_id
            self.approval_error = ""
            self.pdf_message = ""

    @rx.event
    def set_note(self, value: str):
        if not self.locked and not self.busy:
            self.note = value[:500]

    @rx.event
    def set_operation(self, value: str):
        if not self.locked and not self.busy and value in OPERATIONS:
            self.operation = value

    @rx.event
    def set_supplier_choice(self, value: str):
        if not self.locked and not self.busy and value in SUPPLIERS:
            self.supplier_choice = value

    @rx.event
    def set_preview_mode(self, value: str):
        if not self.locked and not self.busy:
            self.preview_mode = value

    @rx.event
    async def load_case(self):
        if self.locked or self.busy:
            return
        self.loading = True
        self.error = self.approval_error = self.pdf_message = ""
        self.selected_id = ""
        self.case = self.result = None
        self.suppliers = []
        self.plans = []
        yield
        try:
            self.case, self.suppliers, self.result = await client.load(self.preview_mode)
            self.plans = self.result.plans
            self.scenario_key = "baseline"
        except ServiceError as exc:
            self.error = str(exc)
        finally:
            self.loading = False

    @rx.event
    async def run_scenario(self):
        if self.locked or self.busy or not self.case:
            return
        self.running = True
        self.error = self.approval_error = self.pdf_message = ""
        previous = self.selected_id
        self.selected_id = ""
        self.plans = []  # Never leave a stale plan approvable while a replacement is pending.
        self.result = None
        operation, supplier = OPERATIONS[self.operation], SUPPLIERS[self.supplier_choice]
        yield
        try:
            self.result = await client.scenario(operation, supplier, self.preview_mode)
            self.plans = self.result.plans
            self.scenario_key = f"{operation}_{supplier}"
            self.selected_id = previous if any(p.plan_id == previous for p in self.plans) else ""
        except ServiceError as exc:
            self.error = str(exc)
        finally:
            self.running = False

    @rx.event
    async def approve_plan(self):
        if not self.can_approve:
            return
        self.approving = True
        self.approval_error = ""
        yield
        try:
            response = await client.approve(
                self.scenario_key,
                self.selected_id,
                self.note,
                self.preview_mode,
                expected_plan=self.selected,
            )
            if (
                response.plan != self.selected
                or response.scenario_key != self.scenario_key
                or (
                    self.case is None
                    or response.case_id != self.case.case_id
                    or response.case_version != self.case.version
                )
            ):
                raise ServiceError("Approval response does not match the reviewed plan.")
            self.approved = response
        except ServiceError as exc:
            self.approval_error = str(exc)
        finally:
            self.approving = False

    @rx.event
    async def export_pdf(self):
        if self.approved is None or self.busy:
            return
        self.exporting = True
        self.pdf_message = ""
        yield
        try:
            response = await client.pdf(self.approved, self.preview_mode)
            if response.approval_id != self.approved.approval_id or (
                response.snapshot_hash != self.approved.snapshot_hash
            ):
                raise ServiceError("PDF response does not match the approved snapshot.")
            self.pdf_message = response.message
            if response.status == "ready":
                if not response.download_url:
                    raise ServiceError("PDF is marked ready but no download is available.")
                yield rx.download(url=response.download_url, filename=response.file_name)
        except ServiceError as exc:
            self.pdf_message = str(exc)
        finally:
            self.exporting = False
