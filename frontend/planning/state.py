"""Reflex HTTP orchestration; no model, Odoo or database access."""

import json
import re
from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

import reflex as rx

from frontend.config import settings
from frontend.planning_client import _supplier_label, fetch_planning_case, submit_planning_request


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
    _demo_payload: dict = {}
    _odoo_payload: dict = {}
    # shortcut: recovery is session-local; copy JSON before leaving until durable recovery exists.
    _pending: dict = {}

    @rx.event
    def change_view(self, value: str):
        if value in {"plans", "whatif", "suppliers", "audit"}:
            self.view = value

    @rx.event
    def change_input_mode(self, value: str):
        if not self.is_loading and not self.has_pending and value in {"stored", "odoo", "create"}:
            self.input_mode = value

    @rx.event
    def update_stress(self, field: str, value: str):
        if (
            not self.is_loading
            and not self.has_pending
            and field in {"quantity", "capacity", "price"}
            and isinstance(value, str)
        ):
            setattr(self, "stress_" + field, value)
            self.error_message = ""

    def _show(self, result):
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
        self.stress_capacity = self.stress_quantity = self.stress_price = ""

    @rx.var
    def selected_terms(self) -> dict[str, str]:
        return next(
            (s for s in self.scenario_suppliers if s["supplier"] == self.stress_supplier),
            {"name": "Choose a supplier", "capacity": "—", "price": "—"},
        )

    @rx.event
    def select_stress_supplier(self, value: str):
        if not self.is_loading and not self.has_pending:
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
        if self.is_loading or self.has_pending:
            return
        self.error_message = ""
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
        except (OSError, ValueError, KeyError, TypeError, InvalidOperation):
            self.error_message = (
                "The controlled demo is missing or invalid. Run the offline T15 prepare "
                "command before using this form."
            )

    @rx.event
    def prepare_odoo(self):
        if self.is_loading or self.has_pending:
            return
        self.error_message = ""
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
        except (OSError, ValueError, KeyError, TypeError, InvalidOperation):
            self.error_message = (
                "The prepared Odoo comparison is missing or invalid. Run the offline "
                "Odoo prepare command and configure its matching saved model on FastAPI."
            )

    @rx.event
    async def create_odoo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.error_target = ""
        try:
            if not self.odoo_ready:
                raise ValueError("Prepare the comparison first")
            payload = deepcopy(self._odoo_payload)
            facts = payload["controlled_input"]
            quantity = _bounded_form_integer(form_data.get("odoo_quantity"), minimum=1)
            required = _form_date(form_data.get("odoo_required_date"))
            now = datetime.now(UTC)
            if date.fromisoformat(required) < now.date():
                raise ValueError("Required date must be today or later")
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
                prefix = supplier["supplier_id"]
                supplier["capacity"] = _bounded_form_integer(
                    form_data.get(prefix + "_capacity"), minimum=0
                )
                moq = form_data.get(prefix + "_moq")
                supplier["minimum_order_quantity"] = (
                    None if moq == "" else _bounded_form_integer(moq, minimum=1)
                )
                supplier["promised_date"] = _form_date(form_data.get(prefix + "_promised_date"))
                supplier["source"] = source.copy()
        except (ValueError, TypeError, KeyError):
            self.error_message = (
                "Load the comparison and review every term: demand and MOQ 1–1,000 "
                "(blank MOQ means none), capacity 0–1,000, valid dates and a required date "
                "of today or later."
            )
            return
        self._prepare_request(settings.planning_cases_url + "/from-odoo", payload)
        yield
        try:
            await self._send_pending()
        finally:
            self.is_loading = False

    async def _send_pending(self, *, recovering: bool = False):
        result, self.error_message, uncertain = await submit_planning_request(
            self._pending["url"],
            self._pending["payload"],
            self._pending["key"],
            settings.t12_trusted_caller_token.get_secret_value(),
        )
        self.has_pending = uncertain or (recovering and result is None)
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

    @rx.event
    async def create_demo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.error_target = ""
        quantity = form_data.get("quantity", "")
        if (
            not self.demo_ready
            or not isinstance(quantity, str)
            or not quantity.isascii()
            or not quantity.isdecimal()
            or len(quantity) > 4
            or not 1 <= int(quantity) <= 1000
        ):
            self.error_message = (
                "Prepare the demo and enter a whole-number quantity from 1 to 1,000."
            )
            return
        payload = deepcopy(self._demo_payload)
        payload["requirement"]["approved_quantity"] = int(quantity)
        payload["approval_reference"] = f"controlled-demand-{int(quantity)}-t16-v1"
        payload["requirement_source"] = {
            "source_type": "controlled_business_terms",
            "source_reference": "t16-ui-demand-v1",
            "observed_at": payload["as_of"],
        }
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
        self.error_message = ""
        yield
        try:
            await self._send_pending(recovering=True)
        finally:
            self.is_loading = False

    @rx.event
    async def load_case(self, form_data: dict[str, Any]):
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
