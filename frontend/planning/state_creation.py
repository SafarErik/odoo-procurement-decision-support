"""State of the New procurement wizard: the Odoo quotation groups, the chosen group's
preview, the buyer's form values and errors, the review, and the save. Parsing and wording
live in ``creation_rules``; this mixin holds the values and runs the requests."""

import json
from copy import deepcopy
from datetime import UTC, date, datetime
from typing import Any

import reflex as rx

from frontend.api import cases, odoo_history
from frontend.api.labels import supplier_label
from frontend.api.odoo_history import group_row, quotation_rows
from frontend.i18n import moment, tr, unit
from frontend.planning import creation_rules as rules
from frontend.planning.state_base import focus


class CreationMixin(rx.State, mixin=True):
    creation_step: int = 0
    creation_values: dict[str, str] = {}
    creation_suggestions: dict[str, str] = {}
    expanded_suppliers: list[str] = []
    groups_retrieved_at: str = ""
    creation_origin: str = ""
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
        return supplier_label(identity, self._lang(), self._group_names.get(self.selected_group))

    @rx.var
    def selected_group_row(self) -> dict[str, str]:
        return next((g for g in self.quotation_groups if g["value"] == self.selected_group), {})

    @rx.var
    def selected_quotations(self) -> list[dict[str, str]]:
        group = next(
            (g for g in self._groups_raw if str(g["purchase_group_id"]) == self.selected_group),
            None,
        )
        return quotation_rows(group, self._lang()) if group else []

    @rx.var
    def groups_retrieved_display(self) -> str:
        return moment(self.groups_retrieved_at, self._lang()) if self.groups_retrieved_at else ""

    @rx.event
    def update_creation_field(self, name: str, value: str):
        if self.is_loading or self.has_pending or self._review_payload:
            return
        if name in self.creation_values:
            self.creation_values[name] = value
            self.creation_dirty = True
            self.creation_errors = {}

    def _demand_valid(self) -> bool:
        *_, errors = rules.read_demand(self.creation_values, datetime.now(UTC).date())
        self.creation_errors = {identity: self._tr(key) for identity, key in errors.items()}
        return not self.creation_errors

    @rx.event
    def go_creation_step(self, step: int):
        if self.is_loading or self.has_pending or step not in (0, 1, 2, 3):
            return
        if step > 0 and not self.odoo_ready:
            return
        if step == 3 and not self._review_payload:
            return
        if step == 2 and not self._demand_valid():
            self.creation_step = 1
            return focus(next(iter(self.creation_errors)))
        if step < 3:
            self._clear_review()
        self.creation_step = step
        return focus(
            {0: "quotation-details-heading", 3: "creation-review-heading"}.get(
                step, "creation-step-heading"
            )
        )

    @rx.event
    def advance_creation(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending or self._review_payload:
            return
        self.creation_values.update(
            {k: str(v) for k, v in form_data.items() if k in self.creation_values}
        )
        if self.creation_step == 1:
            return self.go_creation_step(2)
        return self.review_odoo(dict(self.creation_values))

    @rx.event
    def toggle_supplier_terms(self, supplier: str):
        if supplier not in {r["supplier"] for r in self.odoo_offers}:
            return
        if supplier in self.expanded_suppliers:
            self.expanded_suppliers.remove(supplier)
        else:
            self.expanded_suppliers.append(supplier)

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
    async def rfqs_on_load(self):
        if self.has_pending or self.is_loading:
            yield rx.redirect(self._pending_route)
            return
        self.error_message = ""  # a banner from an earlier page or attempt is no longer current
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
            listing, error = await odoo_history.fetch_quotation_groups(lang=self._lang())
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
                self.groups_retrieved_at = listing.get("retrieved_at", "")
            usable = [r["value"] for r in self.quotation_groups if r["selectable"]]
            if self.selected_group not in usable:
                self._switch_group(usable[0] if usable else "")
        finally:
            self.is_loading = False

    @rx.event
    def select_quotation_group(self, value: str):
        if value == self.selected_group:
            return
        if (
            not self.is_loading
            and not self.has_pending
            and any(r["value"] == value and r["selectable"] for r in self.quotation_groups)
        ):
            return self._guard_navigation("select-group", value, "choose-" + value)

    def _switch_group(self, value: str):
        """A preview belongs to one group: drop it (and its review) when the group changes."""
        if value == self.selected_group:
            return
        self.selected_group = value
        self.creation_values = {}
        self.creation_suggestions = {}
        self.creation_step = 0
        self.expanded_suppliers = []
        self.creation_origin = ""
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
        if group and group == self.selected_group and self.odoo_ready:
            return self.go_creation_step(1)
        if group and group != self.selected_group:
            if any(g["value"] == group and g["selectable"] for g in self.quotation_groups):
                return self._guard_navigation("prepare-group", group, "start-" + group)
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
            data, error = await odoo_history.fetch_odoo_history(int(group), lang=self._lang())
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
            self.creation_step = 1
            self.error_message = (
                "" if data["model_readiness"] == "ready" else self._tr("err_model_unavailable")
            )
        except (KeyError, TypeError, ValueError, ArithmeticError):
            self.error_message = self._tr("err_preview_incomplete")
        finally:
            self.is_loading = False
        if self.odoo_ready:
            yield focus("creation-step-heading")

    def _apply_preview(self, data):
        """Display strings for a verified preview; called again when the language changes."""
        lang = self._lang()
        facts = data["terms"]
        self._preview = data
        self.creation_origin = data.get("data_origin", "")
        self.odoo_history_mode = True
        self.odoo_history_readiness = data["model_readiness"]
        self.odoo_offers = rules.preview_offers(facts, self._name, lang)
        if not self.creation_values:
            self.creation_values = rules.suggested_values(facts, self.odoo_offers)
            self.creation_suggestions = dict(self.creation_values)
        self.odoo_history_rows = rules.history_rows(data["history"], self._name, lang)
        self.odoo_details = tr("captured_at", lang, time=data["captured_at"][:16].replace("T", " "))
        self.odoo_policy = rules.policy_text(facts["policy"], lang)

    def _odoo_request(self, form_data):
        """The save request from the form, or None with ``creation_errors`` filled."""
        self.creation_errors = {}
        if not self.odoo_ready:
            self.error_message = self._tr("err_load_group")
            return None
        request, errors = rules.reviewed_terms(form_data, self._odoo_payload, datetime.now(UTC))
        self.creation_errors = {identity: self._tr(key) for identity, key in errors.items()}
        if self.creation_errors:
            self.error_message = self._tr("err_fix_fields")
            return None
        return request

    def _set_review(self, payload):
        try:
            facts = payload["terms"]
            if any(type(s["available"]) is not bool for s in facts["suppliers"]):
                raise ValueError("Invalid prepared availability")
            lang = self._lang()
            group = self.selected_group_row
            self._review_payload = deepcopy(payload)
            self._review_url = cases.from_odoo_history_url()
            self.creation_review = rules.review_summary(
                facts,
                group,
                group.get("unit", "") or unit("Units", lang),
                self.odoo_policy,
                self._odoo_payload["controlled_input"]["as_of"],
                lang,
            )
            self.review_suppliers = rules.review_rows(facts, self._name, lang)
            self.error_message = ""
            self.error_target = "creation"
            self.creation_step = 3
            return focus("creation-review-heading")
        except (KeyError, TypeError, ValueError, ArithmeticError):
            self._clear_review()
            self.error_message = self._tr("err_preview_incomplete")
            return None

    @rx.event
    def review_odoo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        self._clear_review()
        payload = self._odoo_request(form_data)
        if payload is None:
            if self.creation_errors:
                self.creation_step = (
                    1 if any(k.startswith("odoo-") for k in self.creation_errors) else 2
                )
                self.expanded_suppliers = [
                    row["supplier"]
                    for row in self.odoo_offers
                    if any(k.startswith(row["supplier"] + "_") for k in self.creation_errors)
                ]
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
        self.creation_step = 1
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
        self.creation_values = {}
        self.creation_suggestions = {}
        self.creation_step = 0
        return [
            rx.redirect(f"/planning?case_id={self.details['case_id']}&view=overview"),
            focus("saved-case-heading"),
        ]
