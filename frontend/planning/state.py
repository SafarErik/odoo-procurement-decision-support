"""Reflex HTTP orchestration; no model, Odoo or database access."""

import json
import re
from base64 import b64encode
from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from typing import Any
from uuid import UUID, uuid4

import reflex as rx

from frontend.config import settings
from frontend.odoo_history_client import fetch_odoo_history, fetch_quotation_groups
from frontend.planning_client import (
    FINAL_DECISION_CONFLICT,
    _supplier_label,
    fetch_planning_case,
    submit_planning_request,
)
from frontend.planning_library_client import fetch_library
from frontend.planning_pdf_client import fetch_planning_pdf


class PlanningState(rx.State):
    """HTTP-client state; secrets and executable artifacts stay server-side."""

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
    scenario_kind: str = "capacity_change"
    view: str = "plans"
    input_mode: str = "stored"
    stress_supplier: str = ""
    stress_capacity: str = ""
    stress_quantity: str = ""
    stress_price: str = ""
    error_message: str = ""
    error_target: str = ""
    is_loading: bool = False
    has_case: bool = False
    odoo_ready: bool = False
    odoo_details: str = ""
    odoo_policy: str = ""
    odoo_quantity: str = "200"
    odoo_required_date: str = ""
    odoo_offers: list[dict[str, str]] = []
    odoo_history_mode: bool = False
    odoo_history_readiness: str = ""
    odoo_history_rows: list[dict[str, str]] = []
    quotation_groups: list[dict[str, str]] = []
    selected_group: str = ""
    has_pending: bool = False
    request_key: str = ""
    recovery_json: str = ""
    notice: str = ""
    final_choice: str = ""
    decision_open: bool = False
    decision_conflict: bool = False
    decision_review: dict[str, str] = {}
    _decision_payload: dict = {}
    pdf_data_url: str = ""
    pdf_error: str = ""
    pdf_reference: str = ""
    pdf_filename: str = ""
    # Document language; P3 binds it to the UI language toggle (Hungarian default).
    document_language: str = "hu"
    _odoo_payload: dict = {}
    # shortcut: recovery is session-local; copy JSON before leaving until durable recovery exists.
    _pending: dict = {}
    _pending_route: str = "/planning"
    library_rows: list[dict[str, str]] = []
    library_children: list[dict[str, str]] = []
    library_origin: str = "all"
    library_status: str = "all"
    library_search: str = ""
    library_cursor: str = ""
    children_cursor: str = ""
    expanded_case: str = ""
    library_error: str = ""
    children_error: str = ""
    library_loading: bool = False
    children_loading: bool = False
    library_loaded: bool = False
    _library_params: dict = {}
    creation_dirty: bool = False
    scenario_dirty: bool = False
    navigation_open: bool = False
    navigation_focus: str = ""
    drawer_open: bool = False
    _navigation: tuple[str, str] = ("", "")
    creation_errors: dict[str, str] = {}
    creation_review: dict[str, str] = {}
    review_suppliers: list[dict[str, str]] = []
    _review_payload: dict = {}
    _review_url: str = ""

    def _clear_review(self):
        self.creation_review = {}
        self.review_suppliers = []
        self._review_payload = {}
        self._review_url = ""

    def _guard_navigation(self, action: str, value: str, focus: str = ""):
        if self.has_pending or self.is_loading:
            return None
        if self.creation_dirty or self.scenario_dirty:
            self._navigation = (action, value)
            self.navigation_focus = "workspace-menu" if self.drawer_open else focus
            self.drawer_open = False
            self.navigation_open = True
            return None
        return self._navigate(action, value)

    def _navigate(self, action: str, value: str):
        self.drawer_open = False
        if action == "route":
            if value == "/planning":
                self._clear_comparison_context()
            return rx.redirect(value)
        if action == "view":
            self.view = value
            if self.has_case:
                return rx.redirect(f"/planning?case_id={self.details['case_id']}&view={value}")
        elif action == "input":
            self.input_mode = value
        elif action == "odoo-history":
            return PlanningState.load_odoo_history

    def _clear_comparison_context(self):
        self.has_case = False
        self.details = {}
        self.input_mode = "stored"
        self.notice = ""
        self.error_message = self.error_target = ""
        self.decision_conflict = False
        self.final_choice = ""
        self._clear_decision_review()

    def _discard_drafts(self):
        self._clear_review()
        self.creation_errors = {}
        self.creation_dirty = self.scenario_dirty = False
        self.odoo_ready = False
        self.odoo_history_mode = False
        self.odoo_history_rows = []
        self._odoo_payload = {}
        self.stress_supplier = self.stress_capacity = self.stress_quantity = self.stress_price = ""
        self.error_message = self.error_target = ""

    @rx.event
    def stay_navigation(self, opened: bool = False):
        if not opened:
            self.navigation_open = False
            self._navigation = ("", "")

    @rx.event
    def discard_navigation(self):
        if self.has_pending or self.is_loading or not self.navigation_open:
            return
        action, value = self._navigation
        # Restoring the old tab's focus would automatically select it again after Discard.
        self.navigation_focus = (
            action + "-" + value if action in {"view", "input"} else "workspace-main"
        )
        self.navigation_open = False
        self._navigation = ("", "")
        self._discard_drafts()
        return self._navigate(action, value)

    @rx.event
    def change_drawer(self, opened: bool):
        self.drawer_open = opened

    @rx.event
    def mark_creation_dirty(self, value: str):
        if not self.has_pending and not self.is_loading:
            self.creation_dirty = True
            self._clear_review()
            self.creation_errors = {}

    @rx.event
    def navigate_global(self, destination: str):
        routes = {"cases": "/cases", "rfqs": "/"}
        if destination in routes:
            return self._guard_navigation("route", routes[destination], "nav-" + destination)

    @rx.event
    async def rfq_on_load(self):
        if self.has_pending or self.is_loading:
            yield rx.redirect(self._pending_route)
            return
        from frontend.rfq_page import RfqState

        yield RfqState.refresh_rfqs

    @rx.event
    def open_library(self):
        return self.navigate_global("cases")

    @rx.event
    def open_saved_case(self, case_id: str):
        try:
            if str(UUID(case_id)) != case_id:
                return
        except (ValueError, TypeError, AttributeError):
            return
        return self._guard_navigation("route", "/planning?case_id=" + case_id + "&view=plans", "")

    @rx.event
    def new_comparison(self):
        return self._guard_navigation("route", "/planning", "new-comparison")

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
        if "case_id" not in params and "view" not in params:
            self._clear_comparison_context()
            return
        view = params.get("view", "plans")
        if (
            view in {"plans", "whatif", "suppliers", "audit"}
            and self.has_case
            and params.get("case_id") == self.details.get("case_id")
        ):
            self.view = view
            return
        async for event in self._load_case(
            {
                "case_id": params.get("case_id", "")
                if view in {"plans", "whatif", "suppliers", "audit"}
                else ""
            }
        ):
            yield event
        if self.has_case:
            self.view = view
            yield rx.set_focus("saved-case-heading")

    @rx.event
    async def library_on_load(self):
        if self.has_pending or self.is_loading:
            yield rx.redirect(self._pending_route)
            return
        async for event in self.refresh_library():
            yield event

    @rx.event
    async def refresh_library(self, form_data: dict[str, Any] | None = None):
        if self.library_loading or self.has_pending or self.is_loading:
            return
        if form_data is not None:
            self.library_origin = form_data.get("origin", "all")
            self.library_status = form_data.get("status", "all")
            self.library_search = form_data.get("q", "").strip()
        self._library_params = {
            "origin": self.library_origin,
            "status": self.library_status,
            "q": self.library_search,
        }
        self.expanded_case = self.children_cursor = self.children_error = ""
        self.library_children = []
        async for event in self._load_library_page(""):
            yield event

    @rx.event
    async def next_library_page(self):
        if self.library_cursor and not self.library_loading:
            self.expanded_case = ""
            self.library_children = []
            async for event in self._load_library_page(self.library_cursor):
                yield event
            yield rx.set_focus("library-heading")

    async def _load_library_page(self, cursor):
        self.library_loading = True
        self.library_error = self.library_cursor = ""
        self.library_rows = []
        yield
        try:
            params = dict(self._library_params)
            if cursor:
                params["cursor"] = cursor
            page, self.library_error = await fetch_library(
                settings.planning_cases_url,
                settings.api_service_token.get_secret_value(),
                params,
            )
            self.library_loaded = True
            if page is not None:
                self.library_rows, self.library_cursor = page["items"], page["next_cursor"]
        finally:
            self.library_loading = False

    @rx.event
    async def expand_scenarios(self, case_id: str, more: bool = False):
        if self.children_loading or self.library_loading or self.has_pending or self.is_loading:
            return
        if case_id == self.expanded_case and not more:
            self.expanded_case = ""
            self.library_children = []
            return
        cursor = self.children_cursor if more and case_id == self.expanded_case else ""
        self.expanded_case = case_id
        self.library_children = []
        self.children_loading = True
        self.children_error = self.children_cursor = ""
        yield
        try:
            params = {"origin": self._library_params.get("origin", "all")}
            if cursor:
                params["cursor"] = cursor
            page, self.children_error = await fetch_library(
                f"{settings.planning_cases_url}/{case_id}/scenarios",
                settings.api_service_token.get_secret_value(),
                params,
            )
            if page is not None:
                self.library_children, self.children_cursor = page["items"], page["next_cursor"]
        finally:
            self.children_loading = False

    @rx.event
    def change_view(self, value: str):
        if value in {"plans", "whatif", "suppliers", "audit"} and value != self.view:
            return self._guard_navigation("view", value, "view-" + self.view)

    @rx.event
    def change_input_mode(self, value: str):
        if value in {"stored", "odoo"} and value != self.input_mode:
            return self._guard_navigation("input", value, "input-" + self.input_mode)

    @rx.event
    def update_stress(self, field: str, value: str):
        if (
            not self.is_loading
            and not self.has_pending
            and field in {"quantity", "capacity", "price"}
            and isinstance(value, str)
        ):
            setattr(self, "stress_" + field, value)
            self.scenario_dirty = True
            self.error_message = ""

    def _show(self, result):
        self._clear_decision_review()
        self._clear_review()
        self.creation_errors = {}
        self.creation_dirty = self.scenario_dirty = False
        self.details = result.details
        self.plans = result.plans
        self.allocations = result.allocations
        self.assessments = result.assessments
        self.provenance = result.provenance
        self.scenario_suppliers = result.scenario_suppliers
        self.comparison_rows = result.comparison_rows
        self.has_case = True
        self.decision_conflict = False
        self.input_mode = "stored"
        self.view = "plans" if self.details["parent_id"] == "Base case" else "whatif"
        self.stress_supplier = ""
        self.final_choice = ""
        self.pdf_data_url = self.pdf_error = self.pdf_reference = ""
        self.pdf_filename = ""
        self.stress_capacity = self.stress_quantity = self.stress_price = ""
        self.original_error = ""
        if self.details["parent_id"] == "Base case":
            self._set_original(result)
        elif not self._original_matches_context(self.original_details):
            self.original_details = {}
            self.original_plan = {}
            self.original_allocations = []

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
        )
        try:
            if result is None:
                raise ValueError(error)
            self._set_original(result)
            self.original_error = ""
        except (ValueError, KeyError, TypeError) as error:
            self.original_error = "Original-base data is unavailable. " + str(error)

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
        yield rx.set_focus("scenario-result-heading")

    @rx.var
    def scenario_metrics(self) -> list[dict[str, str]]:
        if not self.has_case:
            return []
        child = self.details.get("parent_id") != "Base case"
        unit = self.details.get("unit", "")
        right = self.plans[0] if child and self.plans else {}
        left = self.original_plan
        cost_delta = exposure_delta = "Unavailable"
        if left and right:
            with localcontext() as context:
                context.prec = max(28, len(left["cost_exact"]) + len(right["cost_exact"]))
                cost_delta = (
                    f"{Decimal(right['cost_exact']) - Decimal(left['cost_exact']):+,f} "
                    f"{self.details['currency']}"
                )
            delta = Fraction(right["exposure_exact"]) - Fraction(left["exposure_exact"])
            exposure_delta = f"{delta.numerator}/{delta.denominator}"
        return [
            {
                "metric": "Feasibility",
                "base": self.original_details.get("status_label", "Unavailable"),
                "scenario": self.details.get("status_label", "Unavailable"),
                "change": "See saved outcome",
            },
            {
                "metric": "Demand quantity",
                "base": self.original_details.get("quantity", "Unavailable") + " " + unit,
                "scenario": self.details.get("quantity", "Unavailable") + " " + unit,
                "change": (
                    f"{int(self.details['quantity']) - int(self.original_details['quantity']):+d} "
                    f"{unit}"
                    if self.original_details and child
                    else "Unavailable"
                ),
            },
            {
                "metric": "Minimum total cost",
                "base": left.get("cost", "Unavailable"),
                "scenario": right.get("cost", "Unavailable"),
                "change": cost_delta,
            },
            {
                "metric": "Synthetic exposure (exact fraction)",
                "base": left.get("exposure_exact", "Unavailable"),
                "scenario": right.get("exposure_exact", "Unavailable"),
                "change": exposure_delta,
            },
        ]

    @rx.var
    def scenario_allocation_rows(self) -> list[dict[str, str]]:
        if not self.has_case:
            return []
        before = {r["supplier"]: r["quantity"] for r in self.original_allocations}
        after = {
            r["supplier"]: r["quantity"] for r in self.allocations if r["plan"] == "Minimum cost"
        }
        return [
            {
                "name": supplier["name"],
                "base": before.get(supplier["supplier"], "Unavailable"),
                "scenario": after.get(supplier["supplier"], "Unavailable"),
                "change": (
                    f"{int(after[supplier['supplier']]) - int(before[supplier['supplier']]):+d}"
                    if supplier["supplier"] in before and supplier["supplier"] in after
                    else "Unavailable"
                ),
            }
            for supplier in self.scenario_suppliers
        ]

    @rx.event
    async def request_pdf(self):
        if self.is_loading or self.has_pending:
            return
        if not self.has_case or self.details.get("final_outcome") != "Approved":
            self.pdf_error = "Only an approved original base has a procurement PDF."
            return
        self.is_loading = True
        self.pdf_error = ""
        self.pdf_data_url = ""
        yield
        try:
            document, self.pdf_error = await fetch_planning_pdf(
                settings.planning_cases_url,
                self.details["case_id"],
                self.details["final_content_hash"],
                settings.api_service_token.get_secret_value(),
                language=self.document_language,
            )
            if document is not None:
                self.pdf_reference = document.reference
                self.pdf_filename = document.filename
                self.pdf_data_url = "data:application/pdf;base64," + b64encode(
                    document.data
                ).decode("ascii")
        finally:
            self.is_loading = False

    @rx.event
    def set_document_language(self, value: str):
        if value in ("hu", "en") and not self.is_loading and not self.has_pending:
            self.document_language = value
            self.pdf_data_url = self.pdf_error = self.pdf_reference = self.pdf_filename = ""

    @rx.var
    def selected_terms(self) -> dict[str, str]:
        return next(
            (s for s in self.scenario_suppliers if s["supplier"] == self.stress_supplier),
            {"name": "Choose a supplier", "capacity": "—", "price": "—"},
        )

    @rx.event
    def select_stress_supplier(self, value: str):
        if not self.is_loading and not self.has_pending:
            self.scenario_dirty = True
            self.stress_supplier = value
            self.stress_capacity = self.stress_price = ""
            self.error_message = ""

    @rx.var
    def scenario_draft(self) -> str:
        terms = self.selected_terms
        if self.scenario_kind == "supplier_outage":
            return (
                f"{terms['name']}: unavailable"
                if self.stress_supplier
                else "Choose the supplier to remove."
            )
        rows = []
        if self.scenario_kind in {"demand_change", "combined"} and self.stress_quantity:
            rows.append(
                f"Demand: {self.details.get('base_quantity', '—')} → {self.stress_quantity} units"
            )
        if self.scenario_kind in {"capacity_change", "combined"} and self.stress_capacity:
            rows.append(
                f"{terms['name']} capacity: {terms['capacity']} → {self.stress_capacity} units"
            )
        if self.scenario_kind in {"price_change", "combined"} and self.stress_price:
            rows.append(
                f"{terms['name']} price: {terms['price']} → {self.stress_price} "
                f"{self.details.get('currency', '')}/unit"
            )
        return "\n".join(rows) or "Enter the new value above to review your assumptions."

    def _odoo_request(self, form_data):
        self.creation_errors = {}
        if not self.odoo_ready:
            self.error_message = "Load an Odoo quotation group before reviewing terms."
            return None
        payload = deepcopy(self._odoo_payload)
        facts = payload["controlled_input"]

        def field(name, identity, parser, message):
            try:
                return parser(form_data.get(name))
            except (ValueError, TypeError):
                self.creation_errors[identity] = message
                return None

        quantity = field(
            "odoo_quantity",
            "odoo-quantity",
            lambda value: _bounded_form_integer(value, minimum=1),
            "Enter a whole-number demand from 1 to 1,000.",
        )
        required = field(
            "odoo_required_date", "odoo-required-date", _form_date, "Enter a valid required date."
        )
        now = datetime.now(UTC)
        if required and date.fromisoformat(required) < now.date():
            self.creation_errors["odoo-required-date"] = "Required date must be today or later."
        for supplier in facts["suppliers"]:
            prefix = supplier["supplier_id"]
            supplier["capacity"] = field(
                prefix + "_capacity",
                prefix + "_capacity",
                lambda value: _bounded_form_integer(value, minimum=0),
                "Enter a whole-number capacity from 0 to 1,000.",
            )
            supplier["minimum_order_quantity"] = field(
                prefix + "_moq",
                prefix + "_moq",
                lambda value: None if value == "" else _bounded_form_integer(value, minimum=1),
                "Leave MOQ blank for none, or enter a whole number from 1 to 1,000.",
            )
            supplier["promised_date"] = field(
                prefix + "_promised_date",
                prefix + "_promised_date",
                _form_date,
                "Enter a valid promised date.",
            )
        if self.creation_errors:
            self.error_message = "Review the highlighted terms before calculating."
            return None
        facts["as_of"] = now.isoformat()
        facts["requirement"]["approved_quantity"] = quantity
        facts["requirement"]["required_date"] = required
        facts["approval_reference"] = f"controlled-demand-{quantity}-t16-odoo-v1"
        source = {
            "source_type": "controlled_business_terms",
            "source_reference": "t16-ui-odoo-terms-v1",
            "observed_at": facts["as_of"],
        }
        facts["requirement_source"] = source.copy()
        for supplier in facts["suppliers"]:
            supplier["source"] = source.copy()
        return {"purchase_group_id": payload["purchase_group_id"], "terms": facts}

    @rx.event
    async def load_quotation_groups(self):
        if self.is_loading or self.has_pending:
            return
        self.is_loading = True
        yield
        try:
            rows, error = await fetch_quotation_groups(
                settings.quotation_groups_url, settings.api_service_token.get_secret_value()
            )
            self.error_message = error
            self.quotation_groups = rows or []
            usable = [r["value"] for r in self.quotation_groups if r["selectable"]]
            if self.selected_group not in usable:
                self._switch_group(usable[0] if usable else "")
        finally:
            self.is_loading = False

    @rx.event
    def select_quotation_group(self, value: str):
        if (
            not self.is_loading
            and not self.has_pending
            and any(r["value"] == value and r["selectable"] for r in self.quotation_groups)
        ):
            self._switch_group(value)

    def _switch_group(self, value: str):
        """A preview belongs to one group: drop it (and its review) when the group changes."""
        if value == self.selected_group:
            return
        self.selected_group = value
        self._clear_review()
        self.creation_errors = {}
        self.odoo_ready = self.odoo_history_mode = False
        self.odoo_history_readiness = ""
        self.odoo_history_rows = []
        self.odoo_offers = []
        self._odoo_payload = {}

    @rx.event
    def prepare_odoo_history(self):
        return self._guard_navigation("odoo-history", "", "load-odoo-history")

    @rx.event
    async def load_odoo_history(self):
        if self.is_loading or self.has_pending:
            return
        self._clear_review()
        self.is_loading = True
        self.odoo_ready = False
        self.odoo_history_rows = []
        yield
        try:
            group = self.selected_group
            if not group.isdecimal() or int(group) <= 0:
                self.error_message = "Load and choose an open Odoo quotation group first."
                return
            data, error = await fetch_odoo_history(
                settings.planning_cases_url
                + f"/odoo-history/preview?purchase_group_id={int(group)}",
                settings.api_service_token.get_secret_value(),
            )
            if data is None:
                self.error_message = error
                return
            facts = data["terms"]
            self.odoo_history_mode = True
            self.odoo_history_readiness = data["model_readiness"]
            self._odoo_payload = {
                "controlled_input": facts,
                "purchase_group_id": data["purchase_group_id"],
            }
            self.odoo_offers = [
                {
                    "supplier": s["supplier_id"],
                    "name": _supplier_label(s["supplier_id"]),
                    "offer": s["offer_id"],
                    "price": s["unit_price"] + " " + facts["requirement"]["currency"],
                    "capacity": str(s["capacity"]),
                    "moq": str(s["minimum_order_quantity"])
                    if s["minimum_order_quantity"] is not None
                    else "",
                    "promised_date": s["promised_date"],
                    "ranges": "Price and delivery applicability: 1–1,000 units (default terms).",
                }
                for s in facts["suppliers"]
            ]
            self.odoo_history_rows = [
                {
                    "supplier": _supplier_label(r["supplier_id"]),
                    "summary": f"{r['on_time_rate'] * 100:.0f}% on time · average lateness "
                    f"{r['mean_lateness_days']:.1f} days · fill rate {r['fill_rate'] * 100:.0f}%"
                    f" · {r['order_count']:g} settled lines",
                }
                for r in data["history"]
            ]
            self.odoo_quantity = str(facts["requirement"]["approved_quantity"])
            self.odoo_required_date = facts["requirement"]["required_date"]
            self.odoo_details = (
                "Live Odoo capture: " + data["database"] + " · " + data["captured_at"]
            )
            self.odoo_policy = (
                "Maximum 2 suppliers; 80% share limit; alternative cost allowance 20%. "
                "Default terms; Odoo quotations and history are reread when saving."
            )
            self.odoo_ready = True
            self.creation_dirty = True
            self.error_message = (
                ""
                if data["model_readiness"] == "ready"
                else "Odoo history is available, but its compatible saved model is unavailable. "
                "Case creation is blocked."
            )
        except (KeyError, TypeError, ValueError):
            self.error_message = (
                "Odoo history preview is incomplete. Reload before creating a case."
            )
        finally:
            self.is_loading = False

    @rx.event
    async def create_odoo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.error_target = ""
        payload = self._odoo_request(form_data)
        if payload is None:
            return
        self._prepare_request(
            settings.planning_cases_url + "/from-odoo-history",
            payload,
        )
        yield
        try:
            await self._send_pending()
        finally:
            self.is_loading = False

    def _set_review(self, payload):
        try:
            facts = payload["terms"]
            if any(type(s["available"]) is not bool for s in facts["suppliers"]):
                raise ValueError("Invalid prepared availability")
            r = facts["requirement"]
            self._review_payload = deepcopy(payload)
            self._review_url = settings.planning_cases_url + "/from-odoo-history"
            self.creation_review = {
                "kind": "odoo",
                "product": r["product_id"],
                "company": facts["company_id"],
                "quantity": str(r["approved_quantity"]),
                "unit": r["quantity_unit"],
                "currency": r["currency"],
                "required_date": r["required_date"],
                "cutoff": facts["as_of"],
                "captured": self._odoo_payload["controlled_input"]["as_of"],
                "origin": "Odoo",
                "policy": self.odoo_policy,
                "history_source": "Odoo purchase history (generated test data)",
            }
            self.review_suppliers = [
                {
                    "name": _supplier_label(s["supplier_id"]),
                    "price": str(s["unit_price"]),
                    "capacity": str(s["capacity"]),
                    "moq": "None (no MOQ)"
                    if s["minimum_order_quantity"] is None
                    else str(s["minimum_order_quantity"]),
                    "promised": s["promised_date"],
                    "available": "Available" if s["available"] else "Unavailable",
                    "ranges": (
                        f"Price: {s['price_quantities']['minimum']}–"
                        f"{s['price_quantities']['maximum']} {r['quantity_unit']}; "
                        f"delivery: {s['delivery_quantities']['minimum']}–"
                        f"{s['delivery_quantities']['maximum']} {r['quantity_unit']}"
                    ),
                    "offer": s["offer_id"],
                }
                for s in facts["suppliers"]
            ]
            self.error_message = ""
            self.error_target = "creation"
            return rx.set_focus("creation-review-heading")

        except (KeyError, TypeError, ValueError):
            self._clear_review()
            self.error_message = (
                "Prepared input data is incomplete. Reload a valid offline fixture."
            )
            return None

    @rx.event
    def review_odoo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self._clear_review()
        payload = self._odoo_request(form_data)
        if payload is None:
            if self.creation_errors:
                # Foreach supplier inputs have dynamic IDs, without static Reflex refs.
                identity = json.dumps(next(iter(self.creation_errors)))
                return rx.call_script(f"document.getElementById({identity})?.focus()")
            return
        return self._set_review(payload)

    @rx.event
    def edit_creation_terms(self):
        if self.is_loading or self.has_pending:
            return
        self._clear_review()
        return rx.set_focus("odoo-quantity")

    @rx.event
    async def save_reviewed_creation(self):
        if self.is_loading or self.has_pending or not self._review_payload:
            return
        if (
            self.creation_review.get("kind") == "odoo"
            and date.fromisoformat(self.creation_review["required_date"]) < datetime.now(UTC).date()
        ):
            self.error_message = "The required date is now past. Edit terms and review again."
            self.creation_errors = {"odoo-required-date": self.error_message}
            yield rx.set_focus("creation-edit-terms")
            return
        self._prepare_request(self._review_url, self._review_payload)
        yield
        try:
            await self._send_pending()
        finally:
            self.is_loading = False
        if self.has_case and not self.has_pending and not self._review_payload:
            for event in self._creation_saved_events():
                yield event

    def _creation_saved_events(self):
        return [
            rx.redirect(f"/planning?case_id={self.details['case_id']}&view=plans"),
            rx.set_focus("saved-case-heading"),
        ]

    async def _send_pending(self, *, recovering: bool = False):
        result, self.error_message, uncertain = await submit_planning_request(
            self._pending["url"],
            self._pending["payload"],
            self._pending["key"],
            settings.api_service_token.get_secret_value(),
        )
        self.decision_conflict = self.error_message == FINAL_DECISION_CONFLICT
        self.has_pending = uncertain or (recovering and result is None)
        if not self.has_pending:
            self._pending = {}
        if result is not None:
            self._show(result)
            self.notice = (
                "Final decision saved. Reopening preserves its selected plan and audit."
                if self.details["final_outcome"]
                else "Comparison saved. Approval is a separate choice."
            )
        return result

    def _prepare_request(self, url: str, payload: dict):
        self._pending_route = (
            self.router.url.path + ("?" + self.router.url.query if self.router.url.query else "")
            or "/planning"
        )
        self.request_key = str(uuid4())
        self._pending = {"url": url, "payload": deepcopy(payload), "key": self.request_key}
        self.recovery_json = json.dumps(self._pending, indent=2, allow_nan=False)
        self.has_pending = True
        self.decision_conflict = False
        self.error_message = ""
        self.notice = ""
        self.is_loading = True

    @rx.event
    def choose_final_plan(self, value: str):
        if (
            self.has_case
            and not self.is_loading
            and not self.has_pending
            and not self.decision_open
            and not self.details.get("final_outcome")
            and value in [p["label"] for p in self.plans] + ["", "No-award"]
            and (value != "No-award" or self.details.get("parent_id") == "Base case")
        ):
            self.final_choice = value
            self._clear_decision_review()
            if value in {"", "No-award"}:
                return rx.set_focus("final-decision-heading")

    @rx.var
    def comparison_state(self) -> str:
        if self.decision_conflict:
            return "Decision conflict — reopen the saved comparison"
        if self.has_pending:
            return (
                "Saving — awaiting confirmation"
                if self.is_loading
                else "Save response unconfirmed — recover the same request"
            )
        if not self.has_case:
            return "Unsaved draft"
        outcome = self.details.get("final_outcome", "")
        if outcome == "Approved":
            return "Final approved plan"
        if outcome == "No-award":
            return "Final No-award recorded — no plan approved"
        if self.details.get("parent_id", "Base case") != "Base case":
            return "Saved scenario — analytical; decide on the original comparison"
        if self.final_choice == "No-award":
            return "No-award selected — not yet recorded"
        if self.final_choice:
            return "Selected plan — not yet approved"
        return "Saved comparison — awaiting a decision"

    @rx.var
    def selected_plan(self) -> dict[str, str]:
        choice = (
            self.details.get("final_plan", "")
            if self.details.get("final_outcome") == "Approved"
            else self.final_choice
        )
        return next((p for p in self.plans if p["label"] == choice), {})

    @rx.event
    def review_final_decision(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending or self.decision_conflict:
            return
        self._clear_decision_review()
        self.error_target = "decision"
        self.error_message = ""
        try:
            if (
                not self.has_case
                or self.details["parent_id"] != "Base case"
                or self.details["final_outcome"]
            ):
                raise ValueError("Only an undecided original base can be finalized.")
            choice = form_data.get("choice", "")
            actor = form_data.get("actor", "")
            reason = form_data.get("reason", "")
            if choice not in [p["label"] for p in self.plans] + ["No-award"]:
                raise ValueError("Explicitly choose a saved plan or No-award.")
            index = next((i for i, p in enumerate(self.plans) if p["label"] == choice), None)
            if not isinstance(actor, str) or not 1 <= len(actor.strip()) <= 255:
                raise ValueError("Enter an actor audit reference (1–255 characters).")
            if (
                not isinstance(reason, str)
                or len(reason) > 2000
                or (index != 0 and not reason.strip())
            ):
                raise ValueError(
                    "Alternative approval and No-award need a reason (up to 2,000 characters)."
                )
            if form_data.get("demonstration") != "on":
                raise ValueError(
                    "Acknowledge this controlled demonstration and synthetic ML evidence."
                )
            payload = {
                "snapshot_hash": self.details["snapshot_hash"],
                "outcome": "no_award" if choice == "No-award" else "approve",
                "plan_index": index,
                "actor_reference": actor,
                "rationale": reason or None,
                "demonstration_acknowledged": True,
            }
        except (ValueError, KeyError) as error:
            self.error_message = str(error)
            return rx.set_focus("decision-error")
        self.final_choice = choice
        self._decision_payload = payload
        self.decision_review = {
            "case_id": self.details["case_id"],
            "choice": choice,
            "actor": actor.strip(),
            "reason": reason.strip() or "Not provided",
            **deepcopy(self.selected_plan),
        }
        self.decision_open = True

    def _clear_decision_review(self):
        self.decision_open = False
        self.decision_review = {}
        self._decision_payload = {}

    @rx.event
    def focus_pending_save(self):
        if self.has_pending or self.decision_conflict:
            return rx.set_focus("request-recovery-heading")

    @rx.event
    def change_decision_confirmation(self, opened: bool):
        if not opened and not self.is_loading and not self.has_pending:
            self._clear_decision_review()

    @rx.event
    async def confirm_final_decision(self):
        if self.is_loading or self.has_pending or self.decision_conflict or not self.decision_open:
            return
        if (
            not self.has_case
            or self.details.get("parent_id") != "Base case"
            or self.details.get("final_outcome")
            or self.decision_review.get("case_id") != self.details.get("case_id")
            or self.decision_review.get("choice") != self.final_choice
            or self._decision_payload.get("snapshot_hash") != self.details.get("snapshot_hash")
        ):
            self._clear_decision_review()
            self.error_target = "decision"
            self.error_message = "The reviewed case changed. Review the saved decision again."
            return
        self._prepare_request(
            f"{settings.planning_cases_url}/{self.details['case_id']}/final-decision",
            self._decision_payload,
        )
        self._clear_decision_review()
        yield
        try:
            saved = await self._send_pending()
        finally:
            self.is_loading = False
        if saved is not None:
            yield rx.set_focus("saved-decision-heading")
        elif self.has_pending:
            yield rx.set_focus("request-recovery-heading")

    @rx.event
    def change_scenario_kind(self, value: str):
        if (
            not self.is_loading
            and not self.has_pending
            and value
            in {
                "supplier_outage",
                "capacity_change",
                "demand_change",
                "price_change",
                "combined",
            }
        ):
            self.scenario_kind = value
            self.scenario_dirty = True
            self.stress_capacity = self.stress_quantity = self.stress_price = ""
            self.error_message = ""

    @rx.event
    async def run_scenario(self, form_data: dict[str, Any]):
        # shortcut: combined changes one supplier plus demand; extend for a multi-supplier case.
        if self.is_loading or self.has_pending:
            return
        self.error_target = "scenario"
        try:
            if not self.has_case:
                raise ValueError("Load a base or scenario first")
            kind = form_data.get("kind")
            if kind not in {
                "supplier_outage",
                "capacity_change",
                "demand_change",
                "price_change",
                "combined",
            }:
                raise ValueError("Choose one of the supported scenario types.")
            payload = {
                "kind": kind,
                "source": {
                    "source_type": "controlled_business_terms",
                    "source_reference": "t16-ui-what-if-v1",
                    "observed_at": self.details["as_of"],
                },
                "suppliers": [],
            }
            changes = 0
            if kind in {"demand_change", "combined"}:
                value = form_data.get("quantity", "")
                if kind == "demand_change" or value != "":
                    demand = _bounded_form_integer(value, minimum=1)
                    if demand == int(self.details["base_quantity"]):
                        raise ValueError(
                            f"New demand must differ from the original "
                            f"{self.details['base_quantity']} units (1 to 1,000)."
                        )
                    payload["approved_quantity"] = demand
                    changes += 1
            supplier_change = {}
            if kind in {"supplier_outage", "capacity_change", "price_change", "combined"}:
                selected = form_data.get("supplier", "")
                terms = next(
                    (s for s in self.scenario_suppliers if s["supplier"] == selected), None
                )
                if terms is None:
                    raise ValueError("Select the original-base supplier to change.")
                supplier_change["supplier_id"] = selected
                if kind == "supplier_outage":
                    supplier_change["available"] = False
                if kind in {"capacity_change", "combined"}:
                    value = form_data.get("capacity", "")
                    if kind == "capacity_change" or value != "":
                        capacity = _bounded_form_integer(value, minimum=0)
                        if capacity == int(terms["capacity"]):
                            raise ValueError(
                                f"{terms['name']}: capacity must differ from its original "
                                f"{terms['capacity']} units. Enter 0 to remove its capacity."
                            )
                        supplier_change["capacity"] = capacity
                        changes += 1
                if kind in {"price_change", "combined"}:
                    value = form_data.get("price", "")
                    if kind == "price_change" or value != "":
                        if (
                            not isinstance(value, str)
                            or len(value) > 64
                            or re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value) is None
                            or Decimal(value) <= 0
                            or Decimal(value) == Decimal(terms["price"])
                        ):
                            raise ValueError(
                                f"{terms['name']}: enter a positive decimal price different from "
                                f"the original {terms['price']} {self.details['currency']} per "
                                "unit (for example 12.50)."
                            )
                        supplier_change["unit_price"] = value
                        changes += 1
            if kind == "combined" and changes < 2:
                raise ValueError(
                    "Combined changes need at least two changes: demand, capacity "
                    "or price. Leave unused fields blank."
                )
            if len(supplier_change) > 1:
                payload["suppliers"] = [supplier_change]
        except ValueError as error:
            self.error_message = str(error)
            return
        except (TypeError, KeyError, StopIteration, InvalidOperation):
            self.error_message = "Review the scenario fields and select an original-base supplier."
            return
        self._prepare_request(
            f"{settings.planning_cases_url}/{self.details['base_id']}/scenarios", payload
        )
        yield
        try:
            saved = await self._send_pending()
            if saved is not None:
                await self._ensure_original()
        finally:
            self.is_loading = False
        if saved is not None:
            yield rx.redirect(f"/planning?case_id={self.details['case_id']}&view=whatif")
            yield rx.set_focus("scenario-result-heading")

    @rx.event
    async def recover_request(self):
        if self.is_loading or self.decision_conflict or not self.has_pending or not self._pending:
            return
        self.is_loading = True
        reviewed_creation = bool(self._review_payload)
        scenario = self._pending["url"].endswith("/scenarios")
        decision = self._pending["url"].endswith("/final-decision")
        self.error_message = ""
        yield
        try:
            saved = await self._send_pending(recovering=True)
            if saved is not None and scenario:
                await self._ensure_original()
        finally:
            self.is_loading = False
        if (
            reviewed_creation
            and self.has_case
            and not self.has_pending
            and not self._review_payload
        ):
            for event in self._creation_saved_events():
                yield event
        elif saved is not None and scenario:
            yield rx.redirect(f"/planning?case_id={self.details['case_id']}&view=whatif")
            yield rx.set_focus("scenario-result-heading")
        elif saved is not None and decision:
            yield rx.set_focus("saved-decision-heading")

    @rx.event
    async def reopen_conflicted_decision(self):
        if self.is_loading or not self.decision_conflict or not self.has_case:
            return
        self.is_loading = True
        yield
        try:
            saved, error = await fetch_planning_case(
                settings.planning_cases_url,
                self.details["case_id"],
                settings.api_service_token.get_secret_value(),
            )
            if saved is not None and saved.details["final_outcome"]:
                self.has_pending = False
                self._pending = {}
                self.decision_conflict = False
                self._show(saved)
                self.notice = "Recorded decision reopened. Review its saved actor and terms."
            else:
                self.error_message = error or (
                    "No recorded decision was returned. Keep the recovery record and contact "
                    "the owner about the conflicting request key. Do not approve again."
                )
        finally:
            self.is_loading = False
        if not self.decision_conflict:
            yield rx.set_focus("saved-decision-heading")

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
        self.view = "plans"
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
            )
            if result is not None:
                self._show(result)
                await self._ensure_original()
            else:
                self.original_details = {}
                self.original_plan = {}
                self.original_allocations = []
        finally:
            self.is_loading = False


def _bounded_form_integer(value: Any, *, minimum: int) -> int:
    if (
        not isinstance(value, str)
        or not value.isascii()
        or not value.isdecimal()
        or len(value) > 4
        or not minimum <= int(value) <= 1000
    ):
        raise ValueError(f"Enter a whole-number quantity from {minimum} to 1,000.")
    return int(value)


def _form_date(value: Any) -> str:
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Invalid date")
    return value
