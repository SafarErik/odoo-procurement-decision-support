"""Stress scenarios: one change set against the original base, the same MILP, saved as a child."""

import re
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from typing import Any

import reflex as rx

from frontend.config import settings
from frontend.i18n import money, number, tr
from frontend.planning.state_base import focus
from frontend.planning.state_creation import _bounded_form_integer

KINDS = ("supplier_outage", "capacity_change", "demand_change", "price_change", "combined")


class ScenarioMixin(rx.State, mixin=True):
    scenario_kind: str = "capacity_change"
    stress_supplier: str = ""
    stress_capacity: str = ""
    stress_quantity: str = ""
    stress_price: str = ""

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

    @rx.var
    def scenario_metrics(self) -> list[dict[str, str]]:
        if not self.has_case:
            return []
        lang = self.lang if self.lang in ("hu", "en") else "hu"
        missing = tr("unavailable", lang)
        child = self.details.get("parent_id") != "Base case"
        currency = self.details.get("currency", "")
        right = self.plans[0] if child and self.plans else {}
        left = self.original_plan
        cost_delta = exposure_delta = missing
        if left and right:
            with localcontext() as context:
                context.prec = max(28, len(left["cost_exact"]) + len(right["cost_exact"]))
                delta = Decimal(right["cost_exact"]) - Decimal(left["cost_exact"])
            cost_delta = money(delta, currency, lang, signed=True)
            points = (Fraction(right["exposure_exact"]) - Fraction(left["exposure_exact"])) * 100
            exposure_delta = ("+" if points > 0 else "") + number(
                Decimal(points.numerator) / Decimal(points.denominator), lang, 1
            )
        quantity_change = missing
        if self.original_details and child:
            change = int(self.details["quantity"]) - int(self.original_details["quantity"])
            quantity_change = f"{change:+d} {self.details.get('unit_label', '')}"
        return [
            {
                "metric": tr("metric_outcome", lang),
                "base": self.original_details.get("status_label", missing),
                "scenario": self.details.get("status_label", missing),
                "change": "",
            },
            {
                "metric": tr("metric_demand", lang),
                "base": self.original_details.get("quantity_display", missing),
                "scenario": self.details.get("quantity_display", missing),
                "change": quantity_change,
            },
            {
                "metric": tr("metric_min_cost", lang),
                "base": left.get("cost", missing),
                "scenario": right.get("cost", missing),
                "change": cost_delta,
            },
            {
                "metric": tr("metric_exposure", lang),
                "base": left.get("exposure_display", missing),
                "scenario": right.get("exposure_display", missing),
                "change": exposure_delta,
            },
        ]

    @rx.var
    def scenario_allocation_rows(self) -> list[dict[str, str]]:
        if not self.has_case:
            return []
        missing = tr("unavailable", self.lang if self.lang in ("hu", "en") else "hu")
        before = {r["supplier"]: r["quantity"] for r in self.original_allocations}
        after = {
            r["supplier"]: r["quantity"] for r in self.allocations if r["plan"] == "Minimum cost"
        }
        return [
            {
                "name": supplier["name"],
                "base": before.get(supplier["supplier"], missing),
                "scenario": after.get(supplier["supplier"], missing),
                "change": (
                    f"{int(after[supplier['supplier']]) - int(before[supplier['supplier']]):+d}"
                    if supplier["supplier"] in before and supplier["supplier"] in after
                    else missing
                ),
            }
            for supplier in self.scenario_suppliers
        ]

    @rx.var
    def scenario_chart(self) -> list[dict[str, Any]]:
        """Minimum-cost quantity per supplier, base versus scenario (0 when not planned)."""
        if self.details.get("parent_id", "Base case") == "Base case":
            return []
        before = {r["supplier"]: int(r["quantity"]) for r in self.original_allocations}
        after = {
            r["supplier"]: int(r["quantity"])
            for r in self.allocations
            if r["plan"] == "Minimum cost"
        }
        return [
            {
                "name": s["name"],
                "base": before.get(s["supplier"], 0),
                "scenario": after.get(s["supplier"], 0),
            }
            for s in self.scenario_suppliers
        ]

    @rx.var
    def selected_terms(self) -> dict[str, str]:
        return next(
            (s for s in self.scenario_suppliers if s["supplier"] == self.stress_supplier),
            {"name": "—", "capacity": "—", "price": "—", "price_display": "—"},
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
        lang = self.lang if self.lang in ("hu", "en") else "hu"
        terms = self.selected_terms
        unit_label = self.details.get("unit_label", "")
        if self.scenario_kind == "supplier_outage":
            return (
                tr("assume_outage", lang, name=terms["name"])
                if self.stress_supplier
                else tr("draft_choose_supplier", lang)
            )
        rows = []
        if self.scenario_kind in {"demand_change", "combined"} and self.stress_quantity:
            rows.append(
                tr(
                    "draft_demand",
                    lang,
                    old=self.details.get("base_quantity", "—"),
                    new=self.stress_quantity,
                    unit=unit_label,
                )
            )
        if self.scenario_kind in {"capacity_change", "combined"} and self.stress_capacity:
            rows.append(
                tr(
                    "draft_capacity",
                    lang,
                    name=terms["name"],
                    old=terms["capacity"],
                    new=self.stress_capacity,
                    unit=unit_label,
                )
            )
        if self.scenario_kind in {"price_change", "combined"} and self.stress_price:
            rows.append(
                tr(
                    "draft_price",
                    lang,
                    name=terms["name"],
                    old=terms["price_display"],
                    new=self.stress_price,
                )
            )
        return "\n".join(rows) or tr("draft_empty", lang)

    @rx.event
    def change_scenario_kind(self, value: str):
        if not self.is_loading and not self.has_pending and value in KINDS:
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
        unit_label = self.details.get("unit_label", "")
        try:
            if not self.has_case:
                raise ValueError(self._tr("err_scenario_load"))
            kind = form_data.get("kind")
            if kind not in KINDS:
                raise ValueError(self._tr("err_scenario_kind"))
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
                    try:
                        demand = _bounded_form_integer(value, minimum=1)
                    except ValueError as error:
                        raise ValueError(self._tr("err_quantity")) from error
                    if demand == int(self.details["base_quantity"]):
                        raise ValueError(
                            self._tr(
                                "err_scenario_demand_same",
                                quantity=self.details["base_quantity"],
                                unit=unit_label,
                            )
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
                    raise ValueError(self._tr("err_scenario_supplier"))
                supplier_change["supplier_id"] = selected
                if kind == "supplier_outage":
                    supplier_change["available"] = False
                if kind in {"capacity_change", "combined"}:
                    value = form_data.get("capacity", "")
                    if kind == "capacity_change" or value != "":
                        try:
                            capacity = _bounded_form_integer(value, minimum=0)
                        except ValueError as error:
                            raise ValueError(self._tr("err_capacity")) from error
                        if capacity == int(terms["capacity"]):
                            raise ValueError(
                                self._tr(
                                    "err_scenario_capacity_same",
                                    name=terms["name"],
                                    capacity=terms["capacity"],
                                    unit=unit_label,
                                )
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
                                self._tr(
                                    "err_scenario_price",
                                    name=terms["name"],
                                    price=terms["price_display"],
                                )
                            )
                        supplier_change["unit_price"] = value
                        changes += 1
            if kind == "combined" and changes < 2:
                raise ValueError(self._tr("err_scenario_combined"))
            if len(supplier_change) > 1:
                payload["suppliers"] = [supplier_change]
        except ValueError as error:
            self.error_message = str(error)
            return
        except (TypeError, KeyError, StopIteration, InvalidOperation):
            self.error_message = self._tr("err_scenario_fields")
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
            yield rx.redirect(f"/planning?case_id={self.details['case_id']}&view=scenarios")
            yield focus("scenario-result-heading")
