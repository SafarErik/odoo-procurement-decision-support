"""One saved case: loading, tabs, original base, supplier overview and chart data."""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

import reflex as rx

from frontend.config import settings
from frontend.planning.state_base import VIEW_ALIASES, VIEWS, focus
from frontend.planning_client import _map_case, fetch_planning_case
from frontend.supplier_overview_client import fetch_supplier_overview


@dataclass
class KpiRow:
    label: str = ""
    display: str = ""


@dataclass
class SupplierCard:
    supplier: str = ""
    name: str = ""
    class_key: str = ""
    class_label: str = ""
    score_display: str = ""
    summary: str = ""
    price: str = ""
    capacity: str = ""
    moq: str = ""
    promised: str = ""
    available: str = ""
    offer: str = ""
    planned: str = ""
    window: str = ""
    share_text: str = ""
    metrics: list[KpiRow] = field(default_factory=list)
    path: list[str] = field(default_factory=list)


def _card(row: dict) -> SupplierCard:
    values = {k: v for k, v in row.items() if k not in ("metrics", "path")}
    return SupplierCard(
        **values, metrics=[KpiRow(**m) for m in row["metrics"]], path=list(row["path"])
    )


class CaseMixin(rx.State, mixin=True):
    details: dict[str, str] = {}
    plans: list[dict[str, str]] = []
    allocations: list[dict[str, str]] = []
    assessments: list[dict[str, str]] = []
    provenance: list[dict[str, str]] = []
    scenario_suppliers: list[dict[str, str]] = []
    comparison_rows: list[dict[str, str]] = []
    original_details: dict[str, str] = {}
    original_plan: dict[str, str] = {}
    original_allocations: list[dict[str, str]] = []
    original_error: str = ""
    view: str = "overview"
    has_case: bool = False
    supplier_cards: list[SupplierCard] = []
    supplier_charts: dict[str, list[dict[str, Any]]] = {}
    suppliers_error: str = ""
    suppliers_loading: bool = False
    _case_raw: dict = {}
    _original_raw: dict = {}

    def _clear_comparison_context(self):
        self.has_case = False
        self.details = {}
        self.notice = ""
        self.error_message = self.error_target = ""
        self.decision_conflict = False
        self.final_choice = ""
        self._clear_decision_review()

    def _apply(self, result):
        """Display lists of a mapped case; selections and drafts are left alone."""
        self.details = result.details
        self.plans = result.plans
        self.allocations = result.allocations
        self.assessments = result.assessments
        self.provenance = result.provenance
        self.scenario_suppliers = result.scenario_suppliers
        self.comparison_rows = result.comparison_rows
        self._case_raw = result.raw

    def _show(self, result):
        self._clear_decision_review()
        self._clear_review()
        self.creation_errors = {}
        self.creation_dirty = self.scenario_dirty = False
        self._apply(result)
        self.has_case = True
        self.decision_conflict = False
        self.view = "overview" if self.details["parent_id"] == "Base case" else "scenarios"
        self.stress_supplier = ""
        self.final_choice = ""
        self.pdf_data_url = self.pdf_error = self.pdf_reference = ""
        self.pdf_filename = ""
        self.stress_capacity = self.stress_quantity = self.stress_price = ""
        self.original_error = ""
        self.supplier_cards, self.supplier_charts, self.suppliers_error = [], {}, ""
        self._clear_base_scenarios()
        if self.details["parent_id"] == "Base case":
            self._set_original(result)
        elif not self._original_matches_context(self.original_details):
            self.original_details = {}
            self.original_plan = {}
            self.original_allocations = []
            self._original_raw = {}

    def _relabel_case(self):
        if not self.has_case or not self._case_raw:
            return None
        lang = self._lang()
        try:
            self._apply(_map_case(self._case_raw, self.details["case_id"], lang))
            if self._original_raw:
                original = _map_case(self._original_raw, self._original_raw["case_id"], lang)
                self.original_details = deepcopy(original.details)
                self.original_plan = deepcopy(original.plans[0]) if original.plans else {}
                self.original_allocations = [
                    r for r in original.allocations if r["plan"] == "Minimum cost"
                ]
        except (ValueError, KeyError, TypeError, ArithmeticError):
            return None
        self.pdf_data_url = self.pdf_error = self.pdf_reference = self.pdf_filename = ""
        return type(self).load_supplier_overview

    def _set_original(self, result):
        original = result.details
        if not self._original_matches_context(original) or {
            s["supplier"] for s in result.scenario_suppliers
        } != {s["supplier"] for s in self.scenario_suppliers}:
            raise ValueError("The original base does not match this saved case's context.")
        self.original_details = deepcopy(original)
        self.original_plan = deepcopy(result.plans[0]) if result.plans else {}
        self.original_allocations = [
            deepcopy(row) for row in result.allocations if row["plan"] == "Minimum cost"
        ]
        self._original_raw = result.raw

    def _original_matches_context(self, original):
        return (
            original.get("parent_id") == "Base case"
            and original.get("case_id") == self.details.get("base_id")
            and original.get("quantity") == self.details.get("base_quantity")
            and all(
                original.get(key) == self.details.get(key)
                for key in (
                    "company",
                    "product",
                    "unit",
                    "currency",
                    "required_date",
                    "as_of",
                    "origin",
                )
            )
        )

    async def _ensure_original(self, *, refresh=False):
        if self._original_matches_context(self.original_details) and not refresh:
            return
        result, error = await fetch_planning_case(
            settings.planning_cases_url,
            self.details["base_id"],
            settings.api_service_token.get_secret_value(),
            lang=self._lang(),
        )
        try:
            if result is None:
                raise ValueError(error)
            self._set_original(result)
            self.original_error = ""
        except (ValueError, KeyError, TypeError):
            self.original_error = self._tr("err_original")

    @rx.event
    async def retry_original(self):
        if self.is_loading or self.has_pending or not self.has_case:
            return
        self.is_loading = True
        yield
        try:
            await self._ensure_original(refresh=True)
        finally:
            self.is_loading = False
        yield focus("scenario-result-heading")

    @rx.event
    async def load_supplier_overview(self):
        """Read-only GET of the stored snapshot's supplier view; never re-scores."""
        if not self.has_case or self.suppliers_loading:
            return
        self.suppliers_loading = True
        self.suppliers_error = ""
        yield
        try:
            overview, self.suppliers_error = await fetch_supplier_overview(
                settings.planning_cases_url,
                self.details["case_id"],
                settings.api_service_token.get_secret_value(),
                lang=self._lang(),
            )
            if overview is not None:
                self.supplier_cards = [_card(c) for c in overview["cards"]]
                self.supplier_charts = overview["charts"]
        finally:
            self.suppliers_loading = False

    @rx.event
    def change_view(self, value: str):
        value = VIEW_ALIASES.get(value, value)
        if value in VIEWS and value != self.view:
            return self._guard_navigation("view", value, "view-" + self.view)

    @rx.event
    async def load_bookmark(self):
        if self.has_pending or self.is_loading:
            route = self.router.url.path + (
                "?" + self.router.url.query if self.router.url.query else ""
            )
            if route != self._pending_route:
                yield rx.redirect(self._pending_route)
            return
        params = self.router.url.query_parameters
        if "case_id" not in params:
            self._clear_comparison_context()
            yield rx.redirect("/cases")
            return
        view = VIEW_ALIASES.get(params.get("view", "overview"), params.get("view", "overview"))
        view = view if view in VIEWS else "overview"
        if self.has_case and params.get("case_id") == self.details.get("case_id"):
            self.view = view
            if not self.supplier_cards and not self.suppliers_error:
                yield type(self).load_supplier_overview
            return
        async for event in self._load_case({"case_id": params.get("case_id", "")}):
            yield event
        if self.has_case:
            self.view = view
            yield type(self).load_supplier_overview
            yield focus("saved-case-heading")

    @rx.event
    async def load_case(self, form_data: dict[str, Any]):
        if self.creation_dirty or self.scenario_dirty:
            yield self.open_saved_case(form_data.get("case_id", "").strip())
            return
        async for event in self._load_case(form_data):
            yield event

    async def _load_case(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.decision_conflict = False
        self.error_target = ""
        self.view = "overview"
        self.recovery_json = self.request_key = ""
        self.has_case = False
        self.details = {}
        self.plans = []
        self.allocations = []
        self.assessments = []
        self.provenance = []
        self.scenario_suppliers = []
        self.comparison_rows = []
        self.error_message = ""
        self.notice = ""
        self.is_loading = True
        yield
        try:
            case_id = form_data.get("case_id", "")
            result, self.error_message = await fetch_planning_case(
                settings.planning_cases_url,
                case_id.strip() if isinstance(case_id, str) else "",
                settings.api_service_token.get_secret_value(),
                lang=self._lang(),
            )
            if result is not None:
                self._show(result)
                await self._ensure_original()
            else:
                self.original_details = {}
                self.original_plan = {}
                self.original_allocations = []
                self._original_raw = {}
        finally:
            self.is_loading = False

    # Chart and panel data (numbers stay numbers; text is already localized).

    @rx.var
    def chart_minimum(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p["title"],
                "cost": float(p["cost_number"]),
                "exposure": float(p["exposure_number"]),
            }
            for p in self.plans[:1]
        ]

    @rx.var
    def chart_alternatives(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p["title"],
                "cost": float(p["cost_number"]),
                "exposure": float(p["exposure_number"]),
            }
            for p in self.plans[1:]
        ]

    @rx.var
    def focus_plan(self) -> dict[str, str]:
        """The plan the buyer looks at: the chosen one, else the lowest-risk alternative."""
        chosen = self.selected_plan
        if chosen:
            return chosen
        return next((p for p in self.plans if p["hint"]), self.plans[0] if self.plans else {})

    @rx.var
    def focus_allocation(self) -> list[dict[str, str]]:
        label = self.focus_plan.get("label", "")
        return [row for row in self.allocations if row["plan"] == label and row["quantity"] != "0"]

    @rx.var
    def supplier_class_counts(self) -> dict[str, str]:
        problematic = sum(a["class"] == "1" for a in self.assessments)
        return {
            "total": str(len(self.assessments)),
            "flagged": str(problematic),
        }

    @rx.var
    def next_step(self) -> int:
        """1 saved → 2 choose a plan → 3 record the decision; 4 when everything is done."""
        if self.details.get("final_outcome"):
            return 4
        return 3 if self.final_choice else 2
