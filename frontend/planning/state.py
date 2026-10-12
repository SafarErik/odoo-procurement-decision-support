"""Reflex HTTP orchestration; no model, Odoo or database access."""

import json
import re
from base64 import b64encode
from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid4

import reflex as rx

from frontend.config import settings
from frontend.planning_client import _supplier_label, fetch_planning_case, submit_planning_request
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
    scenario_kind: str = "capacity_reduction"
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
    demo_ready: bool = False
    demo_details: str = ""
    demo_policy: str = ""
    demo_quantity: str = "10"
    demo_offers: list[dict[str, str]] = []
    odoo_ready: bool = False
    odoo_details: str = ""
    odoo_policy: str = ""
    odoo_quantity: str = "200"
    odoo_required_date: str = ""
    odoo_offers: list[dict[str, str]] = []
    has_pending: bool = False
    request_key: str = ""
    recovery_json: str = ""
    notice: str = ""
    final_choice: str = ""
    pdf_data_url: str = ""
    pdf_error: str = ""
    pdf_reference: str = ""
    pdf_filename: str = ""
    _demo_payload: dict = {}
    _odoo_payload: dict = {}
    # shortcut: recovery is session-local; copy JSON before leaving until durable recovery exists.
    _pending: dict = {}
    _pending_route: str = "/planning"
    library_rows: list[dict[str, str]] = []
    library_children: list[dict[str, str]] = []
    library_workspace: str = "controlled"
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
    practice_task: str = ""
    practice_run_saved: bool = False
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
                self.has_case = False
                self.details = {}
                self.input_mode = "stored"
            return rx.redirect(value)
        if action == "view":
            self.view = value
            if self.has_case:
                return rx.redirect(f"/planning?case_id={self.details['case_id']}&view={value}")
        elif action == "input":
            self.input_mode = value
            if value == "create":
                self.practice_task = ""
                self.practice_run_saved = False
        elif action == "practice":
            return self._choose_practice_task(value)
        elif action == "demo":
            self._prepare_demo()
        elif action == "odoo":
            self._prepare_odoo()
        elif action == "scenario":
            self._prepare_practice_scenario()

    def _discard_drafts(self):
        self._clear_review()
        self.creation_errors = {}
        self.creation_dirty = self.scenario_dirty = False
        self.demo_ready = self.odoo_ready = False
        self._demo_payload = self._odoo_payload = {}
        self.practice_task = ""
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
        routes = {"cases": "/cases", "rfqs": "/", "practice": "/practice"}
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
    def open_practice(self):
        return self.navigate_global("practice")

    @rx.event
    async def practice_on_load(self):
        if self.has_pending or self.is_loading:
            if self._pending_route != "/practice":
                yield rx.redirect(self._pending_route)

    @rx.event
    def choose_practice_task(self, value: str):
        if self.is_loading or self.has_pending:
            return
        if value not in {"compare-plans", "supplier-outage", "infeasible-demand"}:
            self.error_message = "Choose a supported Practice exercise."
            return
        return self._guard_navigation("practice", value, "choose-" + value)

    def _choose_practice_task(self, value: str):
        self.practice_task = value
        self.practice_run_saved = False
        self.has_case = False
        self.details = {}
        self.notice = ""
        self._prepare_demo()
        return rx.set_focus("practice-draft-heading")

    @rx.event
    def prepare_practice_scenario(self):
        return self._guard_navigation("scenario", "", "prepare-exercise")

    def _prepare_practice_scenario(self):
        if (
            self.is_loading
            or self.has_pending
            or not self.has_case
            or self.details.get("parent_id") != "Base case"
        ):
            return
        task = self.details.get("example_id")
        if task not in {"supplier-outage", "infeasible-demand"}:
            return
        self.stress_supplier = self.stress_capacity = self.stress_quantity = self.stress_price = ""
        if task == "supplier-outage":
            self.scenario_kind = "supplier_outage"
            self.stress_supplier = self.scenario_suppliers[0]["supplier"]
        elif task == "infeasible-demand":
            self.scenario_kind = "demand_increase"
            self.stress_quantity = "25"
        else:
            return
        self.view = "whatif"
        self.scenario_dirty = True

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
            self.library_workspace = form_data.get("workspace", "controlled")
            self.library_status = form_data.get("status", "all")
            self.library_search = form_data.get("q", "").strip()
        self._library_params = {
            "workspace": self.library_workspace,
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
                settings.t12_trusted_caller_token.get_secret_value(),
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
            params = {"workspace": self._library_params.get("workspace", "controlled")}
            if cursor:
                params["cursor"] = cursor
            page, self.children_error = await fetch_library(
                f"{settings.planning_cases_url}/{case_id}/scenarios",
                settings.t12_trusted_caller_token.get_secret_value(),
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
        if value in {"stored", "odoo", "create"} and value != self.input_mode:
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
        self.input_mode = "stored"
        self.view = "plans" if self.details["parent_id"] == "Base case" else "whatif"
        self.stress_supplier = ""
        self.final_choice = ""
        self.pdf_data_url = self.pdf_error = self.pdf_reference = ""
        self.pdf_filename = ""
        self.stress_capacity = self.stress_quantity = self.stress_price = ""

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
                settings.t12_trusted_caller_token.get_secret_value(),
            )
            if document is not None:
                self.pdf_reference = document.reference
                self.pdf_filename = document.filename
                self.pdf_data_url = "data:application/pdf;base64," + b64encode(
                    document.data
                ).decode("ascii")
        finally:
            self.is_loading = False

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
        if self.scenario_kind in {"demand_increase", "combined"} and self.stress_quantity:
            rows.append(
                f"Demand: {self.details.get('base_quantity', '—')} → {self.stress_quantity} units"
            )
        if self.scenario_kind in {"capacity_reduction", "combined"} and self.stress_capacity:
            rows.append(
                f"{terms['name']} capacity: {terms['capacity']} → {self.stress_capacity} units"
            )
        if self.scenario_kind in {"price_increase", "combined"} and self.stress_price:
            rows.append(
                f"{terms['name']} price: {terms['price']} → {self.stress_price} "
                f"{self.details.get('currency', '')}/unit"
            )
        return "\n".join(rows) or "Enter the new value above to review your assumptions."

    @rx.event
    def prepare_demo(self):
        return self._guard_navigation("demo", "", "load-demo")

    def _prepare_demo(self):
        if self.is_loading or self.has_pending:
            return
        self.error_message = ""
        self.notice = ""
        self._clear_review()
        self.creation_errors = {}
        self.error_target = ""
        self.demo_ready = False
        self._demo_payload = {}
        try:
            path = settings.controlled_demo_file
            if path.stat().st_size > 256 * 1024:
                raise ValueError("Oversized demo")
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["source_type"] != "t14_synthetic":
                raise ValueError("Unsupported fixture")
            r = data["requirement"]
            offers = [
                {
                    "supplier": s["supplier_id"],
                    "name": _supplier_label(s["supplier_id"]),
                    "price": f"{s['unit_price']} {r['currency']}",
                    "capacity": str(s["capacity"]),
                }
                for s in data["suppliers"]
            ]
            self.demo_details = (
                f"{r['product_id']} · {r['quantity_unit']} · required {r['required_date']} "
                f"· simulation cutoff {data['as_of'][:10]}"
            )
            policy = data["policy"]
            concentration = policy["concentration_limit"]
            share = (
                "No supplier share limit"
                if concentration is None
                else (f"At most {Decimal(concentration) * 100:g}% from one supplier")
            )
            premiums = ", ".join(f"{Decimal(e) * 100:g}%" for e in policy["epsilons"])
            self.demo_policy = (
                f"Maximum suppliers: {policy['max_suppliers']}. "
                f"{share}. Alternative cost allowances: {premiums}. "
                "Dates and history stay fixed to the prepared simulation."
            )
            self.demo_quantity = str(r["approved_quantity"])
            self.demo_offers = offers
            self._demo_payload = data
            self.demo_ready = True
            self.creation_dirty = True
        except (OSError, ValueError, KeyError, TypeError, InvalidOperation):
            self.error_message = (
                "The controlled demo is missing or invalid. Run the offline T15 prepare "
                "command before using this form."
            )

    @rx.event
    def prepare_odoo(self):
        return self._guard_navigation("odoo", "", "load-odoo")

    def _prepare_odoo(self):
        if self.is_loading or self.has_pending:
            return
        self.error_message = ""
        self.notice = ""
        self._clear_review()
        self.creation_errors = {}
        self.error_target = ""
        self.odoo_ready = False
        self._odoo_payload = {}
        try:
            path = settings.controlled_odoo_file
            if path.stat().st_size > 256 * 1024:
                raise ValueError("Oversized comparison")
            data = json.loads(path.read_text(encoding="utf-8"))
            facts = data["controlled_input"]
            group = data["purchase_group_id"]
            if type(group) is not int or group <= 0 or facts["source_type"] != "t14_synthetic":
                raise ValueError("Unsupported comparison")
            suppliers = facts["suppliers"]
            if len(suppliers) != 3 or len({s["supplier_id"] for s in suppliers}) != 3:
                raise ValueError("Expected the prepared three-supplier comparison")
            r = facts["requirement"]
            self.odoo_offers = [
                {
                    "supplier": s["supplier_id"],
                    "name": _supplier_label(s["supplier_id"]),
                    "offer": s["offer_id"],
                    "price": f"{s['unit_price']} {r['currency']}",
                    "capacity": str(s["capacity"]),
                    "moq": ""
                    if s["minimum_order_quantity"] is None
                    else str(s["minimum_order_quantity"]),
                    "promised_date": s["promised_date"],
                    "ranges": (
                        f"Price applies to {s['price_quantities']['minimum']}–"
                        f"{s['price_quantities']['maximum']} units; delivery applies to "
                        f"{s['delivery_quantities']['minimum']}–"
                        f"{s['delivery_quantities']['maximum']} units."
                    ),
                }
                for s in suppliers
            ]
            self.odoo_details = (
                f"Comparison group {group} · {facts['company_id']} · {r['product_id']} "
                f"· {r['quantity_unit']} · {r['currency']} · captured {facts['as_of'][:10]}"
            )
            self.odoo_quantity = str(r["approved_quantity"])
            self.odoo_required_date = r["required_date"]
            policy = facts["policy"]
            share = policy["concentration_limit"]
            self.odoo_policy = (
                f"Maximum suppliers: {policy['max_suppliers']}. "
                + (
                    "No share limit. "
                    if share is None
                    else f"At most {Decimal(share) * 100:g}% from one supplier. "
                )
                + "Alternative cost allowances: "
                + ", ".join(f"{Decimal(e) * 100:g}%" for e in policy["epsilons"])
                + ". Prepared suppliers remain available; policy, applicability ranges "
                "and synthetic history stay fixed."
            )
            self._odoo_payload = data
            self.odoo_ready = True
            self.creation_dirty = True
        except (OSError, ValueError, KeyError, TypeError, InvalidOperation):
            self.error_message = (
                "The prepared Odoo comparison is missing or invalid. Run the offline "
                "Odoo prepare command and configure its matching saved model on FastAPI."
            )

    def _odoo_request(self, form_data):
        self.creation_errors = {}
        if not self.odoo_ready:
            self.error_message = "Load the prepared comparison before reviewing terms."
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
        payload["catalog_context"] = {"workspace": "controlled"}
        return payload

    @rx.event
    async def create_odoo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.error_target = ""
        payload = self._odoo_request(form_data)
        if payload is None:
            return
        self._prepare_request(settings.planning_cases_url + "/from-odoo", payload)
        yield
        try:
            await self._send_pending()
        finally:
            self.is_loading = False

    def _set_review(self, payload, *, odoo: bool):
        try:
            facts = payload["controlled_input"] if odoo else payload
            if any(type(s["available"]) is not bool for s in facts["suppliers"]):
                raise ValueError("Invalid prepared availability")
            r = facts["requirement"]
            self._review_payload = deepcopy(payload)
            self._review_url = settings.planning_cases_url + ("/from-odoo" if odoo else "")
            self.creation_review = {
                "kind": "odoo" if odoo else "demo",
                "product": r["product_id"],
                "company": facts["company_id"],
                "quantity": str(r["approved_quantity"]),
                "unit": r["quantity_unit"],
                "currency": r["currency"],
                "required_date": r["required_date"],
                "cutoff": facts["as_of"],
                "captured": self._odoo_payload["controlled_input"]["as_of"]
                if odoo
                else facts["as_of"],
                "workspace": "Controlled work" if odoo else "Practice",
                "policy": self.odoo_policy if odoo else self.demo_policy,
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
    def review_demo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self._clear_review()
        payload = self._demo_request(form_data)
        if payload is None:
            return rx.set_focus("demo-quantity")
        return self._set_review(payload, odoo=False)

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
        return self._set_review(payload, odoo=True)

    @rx.event
    def edit_creation_terms(self):
        if self.is_loading or self.has_pending:
            return
        kind = self.creation_review.get("kind")
        self._clear_review()
        return rx.set_focus("odoo-quantity" if kind == "odoo" else "demo-quantity")

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
        if self.router.url.path == "/practice":
            return [rx.set_focus("practice-saved-heading")]
        return [
            rx.redirect(f"/planning?case_id={self.details['case_id']}&view=plans"),
            rx.set_focus("saved-case-heading"),
        ]

    async def _send_pending(self, *, recovering: bool = False):
        result, self.error_message, uncertain = await submit_planning_request(
            self._pending["url"],
            self._pending["payload"],
            self._pending["key"],
            settings.t12_trusted_caller_token.get_secret_value(),
        )
        self.has_pending = uncertain or (recovering and result is None)
        if (
            result is not None
            and self._pending["payload"].get("catalog_context", {}).get("workspace") == "practice"
        ):
            self.practice_run_saved = True
        if not self.has_pending:
            self._pending = {}
        if result is not None:
            self._show(result)
            self.notice = (
                "Final decision saved. Reopening preserves its selected plan and audit."
                if self.details["final_outcome"]
                else "Case saved. Keep its case ID to reopen this exact result."
            )

    def _prepare_request(self, url: str, payload: dict):
        self._pending_route = (
            self.router.url.path + ("?" + self.router.url.query if self.router.url.query else "")
            or "/planning"
        )
        self.request_key = str(uuid4())
        self._pending = {"url": url, "payload": deepcopy(payload), "key": self.request_key}
        self.recovery_json = json.dumps(self._pending, indent=2, allow_nan=False)
        self.has_pending = True
        self.error_message = ""
        self.notice = ""
        self.is_loading = True

    @rx.event
    def choose_final_plan(self, value: str):
        if not self.is_loading and not self.has_pending:
            self.final_choice = value

    @rx.event
    async def finalize_case(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.error_target = ""
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
            return
        self._prepare_request(
            f"{settings.planning_cases_url}/{self.details['case_id']}/final-decision", payload
        )
        yield
        try:
            await self._send_pending()
        finally:
            self.is_loading = False

    def _demo_request(self, form_data):
        self.creation_errors = {}
        try:
            quantity = _bounded_form_integer(form_data.get("quantity"), minimum=1)
            if not self.demo_ready:
                raise ValueError("Prepare the demo")
        except (ValueError, TypeError):
            self.creation_errors["demo-quantity"] = "Enter a whole-number demand from 1 to 1,000."
            self.error_message = "Prepare the demo and review the highlighted demand."
            return None
        payload = deepcopy(self._demo_payload)
        payload["catalog_context"] = {
            "workspace": "practice",
            "example_id": self.practice_task or None,
        }
        payload["requirement"]["approved_quantity"] = quantity
        payload["approval_reference"] = f"controlled-demand-{quantity}-t16-v1"
        payload["requirement_source"] = {
            "source_type": "controlled_business_terms",
            "source_reference": "t16-ui-demand-v1",
            "observed_at": payload["as_of"],
        }
        return payload

    @rx.event
    async def create_demo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.error_target = ""
        payload = self._demo_request(form_data)
        if payload is None:
            return
        self._prepare_request(settings.planning_cases_url, payload)
        yield
        try:
            await self._send_pending()
        finally:
            self.is_loading = False

    @rx.event
    def change_scenario_kind(self, value: str):
        if (
            not self.is_loading
            and not self.has_pending
            and value
            in {
                "supplier_outage",
                "capacity_reduction",
                "demand_increase",
                "price_increase",
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
                "capacity_reduction",
                "demand_increase",
                "price_increase",
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
            if kind in {"demand_increase", "combined"}:
                value = form_data.get("quantity", "")
                if kind == "demand_increase" or value != "":
                    demand = _bounded_form_integer(value, minimum=1)
                    if demand <= int(self.details["base_quantity"]):
                        raise ValueError(
                            f"New demand must exceed the original {self.details['base_quantity']} "
                            "units (maximum 1,000)."
                        )
                    payload["approved_quantity"] = demand
                    changes += 1
            supplier_change = {}
            if kind in {"supplier_outage", "capacity_reduction", "price_increase", "combined"}:
                selected = form_data.get("supplier", "")
                terms = next(
                    (s for s in self.scenario_suppliers if s["supplier"] == selected), None
                )
                if terms is None:
                    raise ValueError("Select the original-base supplier to change.")
                supplier_change["supplier_id"] = selected
                if kind == "supplier_outage":
                    supplier_change["available"] = False
                if kind in {"capacity_reduction", "combined"}:
                    value = form_data.get("capacity", "")
                    if kind == "capacity_reduction" or value != "":
                        capacity = _bounded_form_integer(value, minimum=0)
                        if capacity >= int(terms["capacity"]):
                            raise ValueError(
                                f"{terms['name']}: capacity must be below its original "
                                f"{terms['capacity']} units. Enter 0 to remove its capacity."
                            )
                        supplier_change["capacity"] = capacity
                        changes += 1
                if kind in {"price_increase", "combined"}:
                    value = form_data.get("price", "")
                    if kind == "price_increase" or value != "":
                        if (
                            not isinstance(value, str)
                            or len(value) > 64
                            or re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value) is None
                            or Decimal(value) <= Decimal(terms["price"])
                        ):
                            raise ValueError(
                                f"{terms['name']}: enter a decimal price above the original "
                                f"{terms['price']} {self.details['currency']} per unit "
                                "(for example 12.50)."
                            )
                        supplier_change["unit_price"] = value
                        changes += 1
            if kind == "combined" and changes < 2:
                raise ValueError(
                    "Combined changes need at least two changes: higher demand, lower "
                    "capacity, or higher price. Leave unused fields blank."
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
            await self._send_pending()
        finally:
            self.is_loading = False

    @rx.event
    async def recover_request(self):
        if self.is_loading or not self.has_pending or not self._pending:
            return
        self.is_loading = True
        reviewed_creation = bool(self._review_payload)
        self.error_message = ""
        yield
        try:
            await self._send_pending(recovering=True)
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
        self.error_target = ""
        self.view = "plans"
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
                settings.t12_trusted_caller_token.get_secret_value(),
            )
            if result is not None:
                self._show(result)
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
