"""Open RFQs: list Odoo quotation groups, preview history, review terms, save a case."""

import json
from copy import deepcopy
from datetime import UTC, date, datetime
from typing import Any

import reflex as rx

from frontend.config import settings
from frontend.i18n import day, money, number, percent, tr, unit
from frontend.odoo_history_client import fetch_odoo_history, fetch_quotation_groups, group_row
from frontend.planning.state_base import focus
from frontend.planning_client import _supplier_label


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


class CreationMixin(rx.State, mixin=True):
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
    groups_loaded: bool = False
    groups_truncated: bool = False
    groups_error: str = ""
    selected_group: str = ""
    creation_errors: dict[str, str] = {}
    creation_review: dict[str, str] = {}
    review_suppliers: list[dict[str, str]] = []
    _review_payload: dict = {}
    _review_url: str = ""
    _odoo_payload: dict = {}
    _preview: dict = {}
    _groups_raw: list = []
    _group_names: dict = {}

    def _clear_review(self):
        self.creation_review = {}
        self.review_suppliers = []
        self._review_payload = {}
        self._review_url = ""

    def _name(self, identity: str) -> str:
        return _supplier_label(identity, self._lang(), self._group_names.get(self.selected_group))

    @rx.var
    def selected_group_row(self) -> dict[str, str]:
        return next((g for g in self.quotation_groups if g["value"] == self.selected_group), {})

    def _relabel_creation(self):
        try:
            self.quotation_groups = [group_row(g, self._lang()) for g in self._groups_raw]
        except (ValueError, TypeError, KeyError, ArithmeticError):
            self.quotation_groups = []
        if self._preview:
            self._apply_preview(self._preview)
        if self._review_payload:
            self._set_review(self._review_payload)
        return None

    @rx.event
    def mark_creation_dirty(self, value: str):
        if not self.has_pending and not self.is_loading:
            self.creation_dirty = True
            self._clear_review()
            self.creation_errors = {}

    @rx.event
    async def rfqs_on_load(self):
        if self.has_pending or self.is_loading:
            yield rx.redirect(self._pending_route)
            return
        if not self.groups_loaded:
            async for event in self.load_quotation_groups():
                yield event

    @rx.event
    async def load_quotation_groups(self):
        if self.is_loading or self.has_pending:
            return
        self.is_loading = True
        self.groups_error = ""
        yield
        try:
            listing, error = await fetch_quotation_groups(
                settings.quotation_groups_url,
                settings.api_service_token.get_secret_value(),
                lang=self._lang(),
            )
            self.groups_error = error
            self.error_message = error
            self.groups_loaded = True
            if listing is None:
                self.quotation_groups, self._groups_raw = [], []
            else:
                self.quotation_groups = listing["rows"]
                self._groups_raw = listing["raw"]
                self._group_names = listing["names"]
                self.groups_truncated = listing["truncated"]
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
        self._preview = {}

    @rx.event
    def prepare_odoo_history(self, group: str = ""):
        if group:
            self.select_quotation_group(group)
            if self.selected_group != group:
                return
        return self._guard_navigation("odoo-history", "", "load-odoo-history")

    @rx.event
    async def load_odoo_history(self):
        if self.is_loading or self.has_pending:
            return
        self._clear_review()
        self.is_loading = True
        self.odoo_ready = False
        self.odoo_history_rows = []
        self.error_message = ""
        yield
        try:
            group = self.selected_group
            if not group.isdecimal() or int(group) <= 0:
                self.error_message = self._tr("err_choose_group")
                return
            data, error = await fetch_odoo_history(
                settings.planning_cases_url
                + f"/odoo-history/preview?purchase_group_id={int(group)}",
                settings.api_service_token.get_secret_value(),
                lang=self._lang(),
            )
            if data is None:
                self.error_message = error
                return
            self._apply_preview(data)
            facts = data["terms"]
            self._odoo_payload = {
                "controlled_input": facts,
                "purchase_group_id": data["purchase_group_id"],
            }
            self.odoo_quantity = str(facts["requirement"]["approved_quantity"])
            self.odoo_required_date = facts["requirement"]["required_date"]
            self.odoo_ready = True
            self.creation_dirty = True
            self.error_message = (
                "" if data["model_readiness"] == "ready" else self._tr("err_model_unavailable")
            )
        except (KeyError, TypeError, ValueError, ArithmeticError):
            self.error_message = self._tr("err_preview_incomplete")
        finally:
            self.is_loading = False
        if self.odoo_ready:
            yield focus("creation-terms-heading")

    def _apply_preview(self, data):
        """Display strings for a verified preview; called again when the language changes."""
        lang = self._lang()
        facts = data["terms"]
        currency = facts["requirement"]["currency"]
        self._preview = data
        self.odoo_history_mode = True
        self.odoo_history_readiness = data["model_readiness"]
        self.odoo_offers = [
            {
                "supplier": s["supplier_id"],
                "name": self._name(s["supplier_id"]),
                "offer": s["offer_id"],
                "price": money(s["unit_price"], currency, lang),
                "capacity": str(s["capacity"]),
                "moq": str(s["minimum_order_quantity"])
                if s["minimum_order_quantity"] is not None
                else "",
                "promised_date": s["promised_date"],
            }
            for s in facts["suppliers"]
        ]
        self.odoo_history_rows = [
            {
                "supplier": self._name(r["supplier_id"]),
                "on_time": percent(r["on_time_rate"], lang, 0),
                "lateness": tr("days", lang, value=number(r["mean_lateness_days"], lang, 1)),
                "fill": percent(r["fill_rate"], lang, 0),
                "lines": number(r["order_count"], lang, 0),
            }
            for r in data["history"]
        ]
        self.odoo_details = tr("captured_at", lang, time=data["captured_at"][:16].replace("T", " "))
        policy = facts["policy"]
        self.odoo_policy = tr(
            "policy_text",
            lang,
            suppliers=policy["max_suppliers"],
            share=percent(policy["concentration_limit"], lang, 0),
            allowance=", ".join(percent(e, lang, 0) for e in policy["epsilons"]),
        )

    def _odoo_request(self, form_data):
        self.creation_errors = {}
        if not self.odoo_ready:
            self.error_message = self._tr("err_load_group")
            return None
        payload = deepcopy(self._odoo_payload)
        facts = payload["controlled_input"]

        def field(name, identity, parser, message):
            try:
                return parser(form_data.get(name))
            except (ValueError, TypeError):
                self.creation_errors[identity] = self._tr(message)
                return None

        quantity = field(
            "odoo_quantity",
            "odoo-quantity",
            lambda value: _bounded_form_integer(value, minimum=1),
            "err_quantity",
        )
        required = field("odoo_required_date", "odoo-required-date", _form_date, "err_date")
        now = datetime.now(UTC)
        if required and date.fromisoformat(required) < now.date():
            self.creation_errors["odoo-required-date"] = self._tr("err_date_past")
        for supplier in facts["suppliers"]:
            prefix = supplier["supplier_id"]
            supplier["capacity"] = field(
                prefix + "_capacity",
                prefix + "_capacity",
                lambda value: _bounded_form_integer(value, minimum=0),
                "err_capacity",
            )
            supplier["minimum_order_quantity"] = field(
                prefix + "_moq",
                prefix + "_moq",
                lambda value: None if value == "" else _bounded_form_integer(value, minimum=1),
                "err_moq",
            )
            supplier["promised_date"] = field(
                prefix + "_promised_date", prefix + "_promised_date", _form_date, "err_date"
            )
        if self.creation_errors:
            self.error_message = self._tr("err_fix_fields")
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

    def _set_review(self, payload):
        try:
            facts = payload["terms"]
            if any(type(s["available"]) is not bool for s in facts["suppliers"]):
                raise ValueError("Invalid prepared availability")
            lang = self._lang()
            r = facts["requirement"]
            currency = r["currency"]
            unit_name = self.selected_group_row.get("unit", "") or unit("Units", lang)
            self._review_payload = deepcopy(payload)
            self._review_url = settings.planning_cases_url + "/from-odoo-history"
            group = self.selected_group_row
            self.creation_review = {
                "kind": "odoo",
                "product": group.get("product", r["product_id"]),
                "group": group.get("name", ""),
                "company": facts["company_id"],
                "quantity": str(r["approved_quantity"]),
                "quantity_display": tr(
                    "pieces", lang, quantity=number(r["approved_quantity"], lang), unit=unit_name
                ),
                "unit": r["quantity_unit"],
                "currency": currency,
                "required_date": r["required_date"],
                "required_display": day(r["required_date"], lang),
                "cutoff": facts["as_of"],
                "captured": self._odoo_payload["controlled_input"]["as_of"],
                "origin": "Odoo",
                "policy": self.odoo_policy,
            }
            self.review_suppliers = [
                {
                    "name": self._name(s["supplier_id"]),
                    "price": money(s["unit_price"], currency, lang),
                    "capacity": str(s["capacity"]),
                    "moq": tr("none", lang)
                    if s["minimum_order_quantity"] is None
                    else str(s["minimum_order_quantity"]),
                    "promised": day(s["promised_date"], lang),
                    "available": tr("available" if s["available"] else "not_available", lang),
                    "offer": s["offer_id"],
                }
                for s in facts["suppliers"]
            ]
            self.error_message = ""
            self.error_target = "creation"
            return focus("creation-review-heading")
        except (KeyError, TypeError, ValueError, ArithmeticError):
            self._clear_review()
            self.error_message = self._tr("err_preview_incomplete")
            return None

    @rx.event
    async def create_odoo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self.error_target = ""
        payload = self._odoo_request(form_data)
        if payload is None:
            return
        self._prepare_request(settings.planning_cases_url + "/from-odoo-history", payload)
        yield
        try:
            await self._send_pending()
        finally:
            self.is_loading = False

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
        return focus("odoo-quantity")

    @rx.event
    async def save_reviewed_creation(self):
        if self.is_loading or self.has_pending or not self._review_payload:
            return
        if (
            self.creation_review.get("kind") == "odoo"
            and date.fromisoformat(self.creation_review["required_date"]) < datetime.now(UTC).date()
        ):
            self.error_message = self._tr("err_date_now_past")
            self.creation_errors = {"odoo-required-date": self.error_message}
            yield focus("creation-edit-terms")
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
        self._preview = {}
        self.odoo_ready = False
        self.creation_dirty = False
        return [
            rx.redirect(f"/planning?case_id={self.details['case_id']}&view=overview"),
            focus("saved-case-heading"),
        ]
