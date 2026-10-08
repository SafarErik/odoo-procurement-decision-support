"""RFQ ledger and controlled planning workspace through the FastAPI boundary."""

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
from frontend.rfq_client import fetch_rfq_dashboard

PAPER = "#F8F7F8"
SURFACE = "#FFFFFF"
INK = "#252129"
MUTED = "#716A74"
AUBERGINE = "#714B67"
CONNECTED = "#2F6F62"
HAIRLINE = "#DED9DF"
ERROR = "#A43E47"


class RfqState(rx.State):
    """Presentation state for the read-only RFQ ledger."""

    rfqs: list[dict[str, str]] = []
    connected: bool = False
    last_refreshed: str = "Not checked"
    error_message: str = ""
    is_loading: bool = False

    @rx.var
    def rfq_count(self) -> int:
        """Return the number of RFQs currently visible."""

        return len(self.rfqs)

    @rx.var
    def vendor_count(self) -> int:
        """Return the number of distinct vendors currently visible."""

        return len({rfq["vendor_name"] for rfq in self.rfqs})

    @rx.var
    def connection_label(self) -> str:
        """Describe the current upstream connection state."""

        if self.is_loading:
            return "Checking Odoo"
        return "Odoo connected" if self.connected else "Odoo unavailable"

    @rx.event
    async def refresh_rfqs(self) -> None:
        """Refresh the ledger through the documented backend endpoint."""

        self.is_loading = True
        result = await fetch_rfq_dashboard(settings.rfqs_url)
        self.rfqs = [
            {
                "source_id": item.source_id,
                "reference": item.reference,
                "vendor_name": item.vendor_name,
                "order_date": item.order_date,
                "status": item.status,
                "status_label": item.status_label,
                "total": item.total,
            }
            for item in result.items
        ]
        self.connected = result.connected
        self.last_refreshed = result.last_refreshed
        self.error_message = result.error_message
        self.is_loading = False


def _connection_badge() -> rx.Component:
    return rx.hstack(
        rx.box(
            width="0.55rem",
            height="0.55rem",
            border_radius="999px",
            background=rx.cond(RfqState.connected, CONNECTED, ERROR),
        ),
        rx.text(
            RfqState.connection_label,
            color=INK,
            font_size="0.875rem",
            font_weight="500",
        ),
        spacing="2",
        align="center",
    )


def _summary_item(label: str, value: rx.Var | str | int) -> rx.Component:
    return rx.vstack(
        rx.text(value, color=INK, font_size="1.4rem", font_weight="600"),
        rx.text(label, color=MUTED, font_size="0.82rem"),
        spacing="1",
        align="start",
        min_width="0",
    )


def _status_pill(label: rx.Var) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="0.78rem", font_weight="600", white_space="nowrap"),
        color=AUBERGINE,
        background="#F1EAF0",
        border="1px solid #E2D3DF",
        border_radius="999px",
        padding="0.25rem 0.6rem",
        width="fit-content",
    )


def _desktop_row(rfq: rx.Var) -> rx.Component:
    return rx.grid(
        rx.text(rfq["reference"], color=INK, font_weight="650"),
        rx.text(rfq["vendor_name"], color=INK, overflow="hidden", text_overflow="ellipsis"),
        rx.text(rfq["order_date"], color=MUTED),
        _status_pill(rfq["status_label"]),
        rx.text(rfq["total"], color=INK, font_weight="600", text_align="right"),
        columns="1.05fr 1.65fr 1fr 1.1fr 1fr",
        gap="4",
        align_items="center",
        padding="1rem 1.25rem",
        border_top=f"1px solid {HAIRLINE}",
        width="100%",
    )


def _mobile_row(rfq: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text(rfq["reference"], color=INK, font_weight="650"),
                rx.text(rfq["vendor_name"], color=MUTED, font_size="0.88rem"),
                spacing="1",
                align="start",
                min_width="0",
            ),
            _status_pill(rfq["status_label"]),
            justify="between",
            align="start",
            width="100%",
        ),
        rx.hstack(
            rx.text(rfq["order_date"], color=MUTED, font_size="0.82rem"),
            rx.text(rfq["total"], color=INK, font_weight="600", font_size="0.9rem"),
            justify="between",
            width="100%",
        ),
        spacing="3",
        align="stretch",
        padding="1rem",
        border_top=f"1px solid {HAIRLINE}",
        width="100%",
    )


def _ledger() -> rx.Component:
    return rx.box(
        rx.grid(
            rx.text("Reference"),
            rx.text("Vendor"),
            rx.text("Order date"),
            rx.text("Status"),
            rx.text("Total", text_align="right"),
            columns="1.05fr 1.65fr 1fr 1.1fr 1fr",
            gap="4",
            color=MUTED,
            font_size="0.78rem",
            font_weight="600",
            padding="0.8rem 1.25rem",
            width="100%",
            display=["none", "none", "grid"],
        ),
        rx.box(
            rx.foreach(RfqState.rfqs, _desktop_row),
            display=["none", "none", "block"],
        ),
        rx.box(
            rx.foreach(RfqState.rfqs, _mobile_row),
            display=["block", "block", "none"],
        ),
        background=SURFACE,
        border=f"1px solid {HAIRLINE}",
        border_radius="0.7rem",
        overflow="hidden",
        width="100%",
    )


def _empty_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text("No open RFQs found", color=INK, font_weight="600", font_size="1.05rem"),
            rx.text(
                "Create one in Odoo, then refresh this ledger.",
                color=MUTED,
                text_align="center",
            ),
            spacing="2",
            align="center",
        ),
        min_height="15rem",
        background=SURFACE,
        border=f"1px solid {HAIRLINE}",
        border_radius="0.7rem",
        width="100%",
    )


def _error_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.box(width="2.5rem", height="0.2rem", background=ERROR, border_radius="999px"),
            rx.text(
                "RFQ data could not be loaded",
                color=INK,
                font_weight="600",
                font_size="1.05rem",
            ),
            rx.text(
                RfqState.error_message,
                color=MUTED,
                text_align="center",
                max_width="34rem",
                line_height="1.6",
            ),
            spacing="3",
            align="center",
        ),
        min_height="15rem",
        background=SURFACE,
        border=f"1px solid {HAIRLINE}",
        border_radius="0.7rem",
        padding="2rem",
        width="100%",
    )


def _loading_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(color=AUBERGINE, size="3"),
            rx.text("Loading open RFQs", color=MUTED),
            spacing="3",
            align="center",
        ),
        min_height="15rem",
        background=SURFACE,
        border=f"1px solid {HAIRLINE}",
        border_radius="0.7rem",
        width="100%",
    )


def _content() -> rx.Component:
    return rx.cond(
        RfqState.is_loading,
        _loading_state(),
        rx.cond(
            RfqState.error_message != "",
            _error_state(),
            rx.cond(RfqState.rfq_count == 0, _empty_state(), _ledger()),
        ),
    )


def index() -> rx.Component:
    """Render a restrained, responsive RFQ procurement ledger."""

    return rx.box(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.box(
                            width="0.8rem",
                            height="1.7rem",
                            background=AUBERGINE,
                            border_radius="0.18rem",
                        ),
                        rx.text(
                            "Procurement decision support",
                            color=INK,
                            font_size="0.95rem",
                            font_weight="650",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    rx.hstack(
                        rx.link("Stored plans", href="/planning", color=AUBERGINE),
                        _connection_badge(),
                        spacing="4",
                        align="center",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.box(height="1px", background=HAIRLINE, width="100%"),
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            "Open requests for quotation",
                            color=INK,
                            font_size=["2rem", "2.5rem", "3rem"],
                            line_height="1.08",
                            font_weight="650",
                            letter_spacing="-0.035em",
                        ),
                        rx.text(
                            "A live, read-only ledger of purchasing activity in Odoo.",
                            color=MUTED,
                            font_size="1rem",
                            line_height="1.6",
                            max_width="42rem",
                        ),
                        spacing="3",
                        align="start",
                    ),
                    rx.button(
                        rx.icon("refresh-cw", size=16),
                        "Refresh data",
                        on_click=RfqState.refresh_rfqs,
                        disabled=RfqState.is_loading,
                        background=AUBERGINE,
                        color="white",
                        border_radius="0.5rem",
                        padding="0.65rem 1rem",
                        cursor="pointer",
                        _hover={"background": "#5D3E55"},
                        _focus_visible={"outline": f"3px solid {AUBERGINE}55"},
                    ),
                    justify="between",
                    align=rx.breakpoints(initial="start", md="center"),
                    direction=rx.breakpoints(initial="column", md="row"),
                    gap="5",
                    width="100%",
                    padding_top=["1.2rem", "2rem"],
                ),
                rx.grid(
                    _summary_item("Open RFQs", RfqState.rfq_count),
                    _summary_item("Vendors", RfqState.vendor_count),
                    _summary_item("Last refreshed", RfqState.last_refreshed),
                    columns=rx.breakpoints(initial="1", md="3"),
                    gap="5",
                    padding="1.15rem 0",
                    border_top=f"1px solid {HAIRLINE}",
                    border_bottom=f"1px solid {HAIRLINE}",
                    width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("Latest open RFQs", color=INK, font_weight="650"),
                        rx.text("Newest first", color=MUTED, font_size="0.82rem"),
                        justify="between",
                        width="100%",
                    ),
                    _content(),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Source: Odoo 19", color=MUTED, font_size="0.78rem"),
                    rx.text("Read-only integration", color=MUTED, font_size="0.78rem"),
                    justify="between",
                    width="100%",
                    padding_top="1rem",
                ),
                spacing="6",
                align="stretch",
                width="100%",
            ),
            max_width="72rem",
            margin="0 auto",
            padding=["1.25rem", "2rem", "2.5rem"],
            width="100%",
        ),
        background=PAPER,
        color=INK,
        font_family='"Segoe UI Variable", Aptos, "Segoe UI", sans-serif',
        min_height="100vh",
        width="100%",
    )


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
    error_message: str = ""
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
    _demo_payload: dict = {}
    _odoo_payload: dict = {}
    # ponytail: recovery intent lives in the Reflex session; copy JSON before leaving.
    _pending: dict = {}

    def _show(self, result):
        self.details = result.details
        self.plans = result.plans
        self.allocations = result.allocations
        self.assessments = result.assessments
        self.provenance = result.provenance
        self.scenario_suppliers = result.scenario_suppliers
        self.comparison_rows = result.comparison_rows
        self.has_case = True

    @rx.event
    def prepare_demo(self):
        if self.is_loading or self.has_pending:
            return
        self.error_message = ""
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
            self.notice = "Case saved. Keep its case ID to reopen this exact result."

    def _prepare_request(self, url: str, payload: dict):
        self.request_key = str(uuid4())
        self._pending = {"url": url, "payload": deepcopy(payload), "key": self.request_key}
        self.recovery_json = json.dumps(self._pending, indent=2, allow_nan=False)
        self.has_pending = True
        self.error_message = ""
        self.notice = ""
        self.is_loading = True

    @rx.event
    async def create_demo(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
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
    async def run_outage(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending:
            return
        selected = form_data.get("supplier", "")
        if not self.has_case or selected not in {s["supplier"] for s in self.assessments}:
            self.error_message = "Load a case and choose one of its suppliers."
            return
        payload = {
            "kind": "supplier_outage",
            "source": {
                "source_type": "controlled_business_terms",
                "source_reference": "t16-ui-supplier-outage-v1",
                "observed_at": self.details["as_of"],
            },
            "suppliers": [{"supplier_id": selected, "available": False}],
        }
        self._prepare_request(
            f"{settings.planning_cases_url}/{self.details['base_id']}/scenarios", payload
        )
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
            and value in {"capacity_reduction", "demand_increase", "price_increase", "combined"}
        ):
            self.scenario_kind = value

    @rx.event
    async def run_scenario(self, form_data: dict[str, Any]):
        # ponytail: combined changes one supplier plus demand; extend for a multi-supplier case.
        if self.is_loading or self.has_pending:
            return
        try:
            if not self.has_case:
                raise ValueError("Load a base or scenario first")
            kind = form_data.get("kind")
            if kind not in {"capacity_reduction", "demand_increase", "price_increase", "combined"}:
                raise ValueError("Unsupported scenario")
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
                        raise ValueError("Demand must increase")
                    payload["approved_quantity"] = demand
                    changes += 1
            supplier_change = {}
            if kind in {"capacity_reduction", "price_increase", "combined"}:
                selected = form_data.get("supplier", "")
                terms = next(s for s in self.scenario_suppliers if s["supplier"] == selected)
                supplier_change["supplier_id"] = selected
                if kind in {"capacity_reduction", "combined"}:
                    value = form_data.get("capacity", "")
                    if kind == "capacity_reduction" or value != "":
                        capacity = _bounded_form_integer(value, minimum=0)
                        if capacity >= int(terms["capacity"]):
                            raise ValueError("Capacity must decrease")
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
                            raise ValueError("Price must increase")
                        supplier_change["unit_price"] = value
                        changes += 1
            if kind == "combined" and changes < 2:
                raise ValueError("Choose at least two disturbances")
            if len(supplier_change) > 1:
                payload["suppliers"] = [supplier_change]
        except (ValueError, TypeError, KeyError, StopIteration, InvalidOperation):
            self.error_message = (
                "Choose a base supplier and enter a strict change from the original base: "
                "higher demand (1–1,000), lower capacity (0–1,000), or a higher decimal "
                "price per unit. Combined scenarios need at least two changes; leave unused "
                "values blank."
            )
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
        raise ValueError("Invalid quantity")
    return int(value)


def _form_date(value: Any) -> str:
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Invalid date")
    return value


def _allocation_bar(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.cond(
        row["quantity"] != "0",
        rx.box(
            rx.hstack(
                rx.text(row["name"], size="2"),
                rx.text(row["quantity"], font_weight="650"),
                justify="between",
            ),
            rx.box(
                rx.box(
                    width=row["share"] + "%",
                    height="0.4rem",
                    background=AUBERGINE,
                    border_radius="3px",
                ),
                background="#EEE8EF",
                margin_top="0.4rem",
                border_radius="3px",
            ),
            margin_bottom="0.85rem",
        ),
    )


def _recorded_plan(plan: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading(plan["label"], as_="h3", size="4"),
            rx.badge("Saved plan", color_scheme="gray"),
            justify="between",
        ),
        rx.text(
            plan["cost"], size="8", font_weight="650", letter_spacing="-0.04em", margin_top="1rem"
        ),
        rx.text(plan["premium_display"], color=MUTED, size="2", margin_bottom="1.5rem"),
        rx.text("Quantity by supplier", font_weight="600", size="2", margin_bottom="0.75rem"),
        rx.foreach(
            PlanningState.allocations,
            lambda row: rx.cond(row["plan"] == plan["label"], _allocation_bar(row)),
        ),
        rx.hstack(
            rx.text("Schedule-watch exposure", size="2"),
            rx.text(plan["exposure_display"], font_weight="650", color=INK),
            justify="between",
            margin_top="1.5rem",
        ),
        rx.text(
            "Lower means less exposure in this simulation. This is not a failure probability.",
            color=MUTED,
            size="2",
            margin_top="0.5rem",
        ),
        rx.el.details(
            rx.el.summary("What shapes this allocation?", cursor="pointer"),
            rx.text(plan["buyer_notes"], white_space="pre-line", size="2", margin_top="0.75rem"),
            margin_top="1.25rem",
        ),
        rx.el.details(
            rx.el.summary("Exact values and solver notes", cursor="pointer"),
            rx.text("Exposure: ", plan["exposure"], size="2", margin_top="0.75rem"),
            rx.text("Cost premium: ", plan["premium"], size="2"),
            rx.text(plan["explanations"], size="2", white_space="pre-line", margin_top="0.75rem"),
            margin_top="0.75rem",
            color=MUTED,
        ),
        border=f"1px solid {HAIRLINE}",
        background=SURFACE,
        border_radius="0.75rem",
        padding=["1.25rem", "1.75rem"],
    )


def _recorded_assessment(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["name"], font_weight="650"),
                rx.text(row["history_summary"], color=MUTED, size="2"),
            ),
            rx.box(
                rx.badge(row["class_label"], color_scheme="plum"),
                rx.text("Exposure ", row["score_display"], size="2", margin_top="0.3rem"),
            ),
            justify="between",
            gap="1rem",
            flex_wrap="wrap",
        ),
        rx.el.details(
            rx.el.summary("How did the tree classify this supplier?", cursor="pointer"),
            rx.text("History window: ", row["history_window"], size="2", margin_top="0.75rem"),
            rx.text(
                "These conditions trace the saved model's branches. They are not receipt records.",
                size="2",
                color=MUTED,
            ),
            rx.text(row["path"], white_space="pre-line", size="2", margin_y="0.75rem"),
            rx.text("Exact supplier ID: ", row["supplier"], size="2"),
            rx.text("Recorded class: ", row["class"], " · Score: ", row["score"], size="2"),
            rx.text("Recorded validity end: ", row["valid_until"], size="2"),
            rx.text(
                "Synthetic history reference: ", row["source"], size="2", overflow_wrap="anywhere"
            ),
            rx.text("Model: ", row["model"], size="2", overflow_wrap="anywhere"),
            margin_top="0.75rem",
        ),
        padding_y="1.25rem",
        border_bottom=f"1px solid {HAIRLINE}",
    )


def _recorded_sources(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["field"]),
        rx.table.cell(row["type"]),
        rx.table.cell(row["reference"]),
        rx.table.cell(row["observed_at"]),
    )


def _outage_form() -> rx.Component:
    return rx.box(
        rx.heading("Test a supplier outage", as_="h2", size="4"),
        rx.text(
            (
                "Remove one supplier and save a new scenario against the original base "
                "case. The base stays unchanged; saved scores are reused."
            ),
            color=MUTED,
            size="2",
            max_width="65ch",
            margin_y="0.75rem",
        ),
        rx.el.form(
            rx.flex(
                rx.box(
                    rx.el.label(
                        "Unavailable supplier",
                        html_for="outage-supplier",
                        display="block",
                        margin_bottom="0.4rem",
                    ),
                    rx.el.select(
                        rx.el.option("Choose a supplier", value="", disabled=True),
                        rx.foreach(
                            PlanningState.assessments,
                            lambda row: rx.el.option(row["name"], value=row["supplier"]),
                        ),
                        name="supplier",
                        id="outage-supplier",
                        default_value="",
                        required=True,
                        disabled=PlanningState.is_loading | PlanningState.has_pending,
                        width="100%",
                        padding="0.65rem",
                        border=f"1px solid {HAIRLINE}",
                        border_radius="0.35rem",
                        background=SURFACE,
                    ),
                    min_width="14rem",
                    flex="1",
                ),
                rx.button(
                    "Run outage scenario",
                    type="submit",
                    disabled=PlanningState.is_loading | PlanningState.has_pending,
                    size="3",
                ),
                align="end",
                gap="1rem",
                flex_wrap="wrap",
            ),
            on_submit=PlanningState.run_outage,
            reset_on_submit=False,
        ),
        background="#F0EBF2",
        padding="1.5rem",
        border_radius="0.65rem",
    )


def _scenario_form() -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    combined = PlanningState.scenario_kind == "combined"
    return rx.box(
        rx.heading("Test other what-if changes", as_="h2", size="4"),
        rx.text(
            "Every scenario starts from the original saved base, including when viewing a child. "
            "These are assumptions: Odoo is neither reread nor updated, "
            "and saved ML scores are reused.",
            size="2",
            color=MUTED,
            max_width="75ch",
            margin_y="0.75rem",
        ),
        rx.text(
            "Original demand: ",
            PlanningState.details["base_quantity"],
            " ",
            PlanningState.details["unit"],
            size="2",
            margin_bottom="1rem",
        ),
        rx.el.form(
            rx.el.label("Scenario type", html_for="stress-kind", display="block"),
            rx.el.select(
                rx.el.option("Capacity reduction", value="capacity_reduction"),
                rx.el.option("Demand increase", value="demand_increase"),
                rx.el.option("Price increase", value="price_increase"),
                rx.el.option("Combined changes", value="combined"),
                id="stress-kind",
                name="kind",
                value=PlanningState.scenario_kind,
                on_change=PlanningState.change_scenario_kind,
                disabled=busy,
                padding="0.65rem",
                width="100%",
                border=f"1px solid {HAIRLINE}",
                border_radius="0.35rem",
                background=SURFACE,
            ),
            rx.cond(
                PlanningState.scenario_kind != "demand_increase",
                rx.box(
                    rx.el.label(
                        "Supplier to change (original terms)",
                        html_for="stress-supplier",
                        display="block",
                    ),
                    rx.el.select(
                        rx.el.option("Choose a supplier", value="", disabled=True),
                        rx.foreach(
                            PlanningState.scenario_suppliers,
                            lambda row: rx.el.option(
                                row["name"]
                                + " · capacity "
                                + row["capacity"]
                                + " · "
                                + row["price"]
                                + " "
                                + PlanningState.details["currency"]
                                + "/unit",
                                value=row["supplier"],
                            ),
                        ),
                        id="stress-supplier",
                        name="supplier",
                        default_value="",
                        required=True,
                        disabled=busy,
                        padding="0.65rem",
                        width="100%",
                        border=f"1px solid {HAIRLINE}",
                        border_radius="0.35rem",
                        background=SURFACE,
                    ),
                    margin_top="1rem",
                ),
            ),
            rx.flex(
                rx.cond(
                    (PlanningState.scenario_kind == "demand_increase") | combined,
                    rx.box(
                        rx.el.label(
                            "New demand quantity", html_for="stress-quantity", display="block"
                        ),
                        rx.input(
                            id="stress-quantity",
                            name="quantity",
                            type="number",
                            min="1",
                            max="1000",
                            step="1",
                            required=~combined,
                            disabled=busy,
                            width="100%",
                        ),
                        flex="1",
                        min_width="12rem",
                    ),
                ),
                rx.cond(
                    (PlanningState.scenario_kind == "capacity_reduction") | combined,
                    rx.box(
                        rx.el.label(
                            "New capacity limit", html_for="stress-capacity", display="block"
                        ),
                        rx.input(
                            id="stress-capacity",
                            name="capacity",
                            type="number",
                            min="0",
                            max="1000",
                            step="1",
                            required=~combined,
                            disabled=busy,
                            width="100%",
                        ),
                        flex="1",
                        min_width="12rem",
                    ),
                ),
                rx.cond(
                    (PlanningState.scenario_kind == "price_increase") | combined,
                    rx.box(
                        rx.el.label("New price per unit", html_for="stress-price", display="block"),
                        rx.input(
                            id="stress-price",
                            name="price",
                            type="text",
                            input_mode="decimal",
                            max_length=64,
                            placeholder="e.g. 11.50",
                            required=~combined,
                            disabled=busy,
                            width="100%",
                        ),
                        flex="1",
                        min_width="12rem",
                    ),
                ),
                gap="1rem",
                flex_wrap="wrap",
                margin_y="1rem",
            ),
            rx.cond(
                combined,
                rx.text(
                    "Enter at least two changes above. Capacity and price apply to the "
                    "selected supplier; leave unused values blank.",
                    size="2",
                    color=MUTED,
                    margin_bottom="1rem",
                ),
            ),
            rx.button("Create and save scenario", type="submit", disabled=busy, size="3"),
            on_submit=PlanningState.run_scenario,
            reset_on_submit=False,
        ),
        background="#F0EBF2",
        padding="1.5rem",
        border_radius="0.65rem",
        width="100%",
    )


def _scenario_comparison() -> rx.Component:
    return rx.box(
        rx.heading("Change from the base case", as_="h3", size="4"),
        rx.text(
            "What-if assumptions: ",
            PlanningState.details["assumptions"],
            size="2",
            margin_y="0.5rem",
        ),
        rx.text(PlanningState.details["comparison_display"], size="2", margin_bottom="1rem"),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Result"),
                        rx.table.column_header_cell("Original base"),
                        rx.table.column_header_cell("Scenario"),
                    )
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.row_header_cell("Feasibility"),
                        rx.table.cell(PlanningState.details["base_status_label"]),
                        rx.table.cell(PlanningState.details["scenario_status_label"]),
                    ),
                    rx.table.row(
                        rx.table.row_header_cell("Demand quantity"),
                        rx.table.cell(PlanningState.details["base_quantity"]),
                        rx.table.cell(PlanningState.details["quantity"]),
                    ),
                    rx.table.row(
                        rx.table.row_header_cell("Minimum total cost"),
                        rx.table.cell(PlanningState.details["base_cost"]),
                        rx.table.cell(PlanningState.details["scenario_cost"]),
                    ),
                    rx.table.row(
                        rx.table.row_header_cell("Schedule-watch exposure"),
                        rx.table.cell(PlanningState.details["base_exposure"]),
                        rx.table.cell(PlanningState.details["scenario_exposure"]),
                    ),
                ),
            ),
            overflow_x="auto",
            width="100%",
        ),
        rx.cond(
            PlanningState.comparison_rows.length() > 0,
            rx.box(
                rx.text("Minimum-cost allocation changes", font_weight="600", margin_y="0.75rem"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Supplier"),
                            rx.table.column_header_cell("Base quantity"),
                            rx.table.column_header_cell("Scenario quantity"),
                            rx.table.column_header_cell("Change"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            PlanningState.comparison_rows,
                            lambda row: rx.table.row(
                                rx.table.row_header_cell(row["name"]),
                                rx.table.cell(row["base"]),
                                rx.table.cell(row["scenario"]),
                                rx.table.cell(row["change"]),
                            ),
                        )
                    ),
                ),
                overflow_x="auto",
                width="100%",
            ),
            rx.text(
                "No comparable proven minimum-cost allocation is available. View the base "
                "case to inspect its saved result; missing values are not zero allocations.",
                size="2",
                color=MUTED,
                margin_top="0.75rem",
            ),
        ),
        width="100%",
        padding="1rem",
        border_left=f"3px solid {CONNECTED}",
    )


def _recorded_case() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.flex(
                rx.box(
                    rx.heading(PlanningState.details["status_label"], as_="h2", size="6"),
                    rx.text(
                        PlanningState.details["scenario_label"], color=MUTED, margin_top="0.4rem"
                    ),
                ),
                rx.box(
                    rx.text(
                        PlanningState.details["quantity"],
                        " ",
                        PlanningState.details["unit"],
                        font_weight="650",
                        size="5",
                    ),
                    rx.text(
                        "Required ", PlanningState.details["required_date"], color=MUTED, size="2"
                    ),
                ),
                justify="between",
                gap="1rem",
                flex_wrap="wrap",
            ),
            rx.text(PlanningState.details["product"], color=MUTED, size="2", margin_top="0.75rem"),
            rx.flex(
                rx.text(
                    "Case ID: ",
                    PlanningState.details["case_id"],
                    size="2",
                    overflow_wrap="anywhere",
                ),
                rx.button(
                    "Copy case ID",
                    variant="soft",
                    size="1",
                    on_click=rx.set_clipboard(PlanningState.details["case_id"]),
                ),
                rx.cond(
                    PlanningState.details["parent_id"] != "Base case",
                    rx.button(
                        "View base case",
                        variant="soft",
                        size="1",
                        on_click=PlanningState.load_case(
                            {"case_id": PlanningState.details["base_id"]}
                        ),
                        disabled=PlanningState.is_loading | PlanningState.has_pending,
                    ),
                ),
                gap="0.75rem",
                align="center",
                flex_wrap="wrap",
                margin_top="0.75rem",
            ),
            rx.text(PlanningState.details["input_kind"], size="2", margin_top="0.75rem"),
            padding_y="1rem",
            width="100%",
        ),
        rx.cond(
            PlanningState.plans.length() > 0,
            rx.grid(
                rx.foreach(PlanningState.plans, _recorded_plan),
                columns=rx.breakpoints(initial="1", md="2"),
                gap="1rem",
                width="100%",
            ),
            rx.callout(
                rx.cond(
                    PlanningState.details["status"] == "infeasible",
                    "These constraints cannot produce a proven plan. Review demand and "
                    "supplier limits before creating another case.",
                    "No proven result is available. Check the recorded status and diagnostics; "
                    "this does not establish that the constraints are infeasible.",
                ),
                color_scheme="amber",
            ),
        ),
        rx.cond(
            PlanningState.details["comparison"] != "",
            _scenario_comparison(),
        ),
        _outage_form(),
        _scenario_form(),
        rx.box(
            rx.heading("Supplier schedule assessment", as_="h2", size="5"),
            rx.text(
                (
                    "The Decision Tree uses prior delivery adherence and completed-receipt "
                    "count. These are saved synthetic assessments; opening this case does not "
                    "refresh them."
                ),
                color=MUTED,
                size="2",
                max_width="72ch",
                margin_top="0.5rem",
            ),
            rx.foreach(PlanningState.assessments, _recorded_assessment),
            width="100%",
        ),
        rx.el.details(
            rx.el.summary("Audit details and sources", cursor="pointer", font_weight="650"),
            rx.vstack(
                rx.text("Case ID: ", PlanningState.details["case_id"], overflow_wrap="anywhere"),
                rx.text(
                    "Base / parent: ", PlanningState.details["parent_id"], overflow_wrap="anywhere"
                ),
                rx.text("Company: ", PlanningState.details["company"]),
                rx.text("Saved at: ", PlanningState.details["created_at"]),
                rx.text("Simulation cutoff: ", PlanningState.details["as_of"]),
                rx.text(
                    "Snapshot hash: ",
                    PlanningState.details["snapshot_hash"],
                    overflow_wrap="anywhere",
                ),
                rx.text(PlanningState.details["explanations"], white_space="pre-line"),
                rx.text(PlanningState.details["comparison"], white_space="pre-line"),
                rx.heading("All allocations, including unselected suppliers", as_="h3", size="3"),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Plan"),
                                rx.table.column_header_cell("Supplier ID"),
                                rx.table.column_header_cell("Quantity"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                PlanningState.allocations,
                                lambda row: rx.table.row(
                                    rx.table.cell(row["plan"]),
                                    rx.table.cell(row["supplier"]),
                                    rx.table.cell(row["quantity"]),
                                ),
                            )
                        ),
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                rx.heading("Field provenance", as_="h3", size="3"),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Field"),
                                rx.table.column_header_cell("Source"),
                                rx.table.column_header_cell("Reference"),
                                rx.table.column_header_cell("Observed at"),
                            )
                        ),
                        rx.table.body(rx.foreach(PlanningState.provenance, _recorded_sources)),
                    ),
                    overflow="auto",
                    max_height="24rem",
                    width="100%",
                ),
                spacing="3",
                align="stretch",
                margin_top="1rem",
                font_size="0.875rem",
            ),
            width="100%",
            padding="1.25rem",
            border=f"1px solid {HAIRLINE}",
            border_radius="0.5rem",
        ),
        spacing="6",
        align="stretch",
        width="100%",
    )


def _odoo_supplier_terms(row: rx.Var[dict[str, str]]) -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    return rx.box(
        rx.text(row["supplier"], font_weight="650", size="2"),
        rx.text(row["price"], " per unit · ", row["offer"], size="2", color=MUTED),
        rx.text("Captured Odoo price; checked again when saving.", size="1", color=MUTED),
        rx.text(row["ranges"], size="1", color=MUTED, margin_y="0.5rem"),
        rx.el.label(
            "Capacity (explicit limit)", html_for=row["supplier"] + "_capacity", display="block"
        ),
        rx.input(
            id=row["supplier"] + "_capacity",
            name=row["supplier"] + "_capacity",
            type="number",
            min="0",
            max="1000",
            step="1",
            required=True,
            default_value=row["capacity"],
            disabled=busy,
            width="100%",
        ),
        rx.el.label(
            "MOQ (blank means none)",
            html_for=row["supplier"] + "_moq",
            display="block",
            margin_top="0.75rem",
        ),
        rx.input(
            id=row["supplier"] + "_moq",
            name=row["supplier"] + "_moq",
            type="number",
            min="1",
            max="1000",
            step="1",
            default_value=row["moq"],
            disabled=busy,
            width="100%",
        ),
        rx.el.label(
            "Promised date",
            html_for=row["supplier"] + "_promised_date",
            display="block",
            margin_top="0.75rem",
        ),
        rx.input(
            id=row["supplier"] + "_promised_date",
            name=row["supplier"] + "_promised_date",
            type="date",
            required=True,
            default_value=row["promised_date"],
            disabled=busy,
            width="100%",
        ),
        padding="1rem",
        border=f"1px solid {HAIRLINE}",
        border_radius="8px",
    )


def _odoo_creation_controls() -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    return rx.tabs.content(
        rx.text(
            "Use the prepared Odoo quotation comparison. FastAPI reads Odoo again before saving. "
            "You supply demand and supplier limits; the Decision Tree uses synthetic history, "
            "so this is a controlled demonstration, not an observed supplier assessment.",
            color=MUTED,
            size="2",
            max_width="75ch",
            margin_bottom="1rem",
        ),
        rx.button(
            "Load prepared Odoo comparison",
            on_click=PlanningState.prepare_odoo,
            disabled=busy,
            variant="soft",
        ),
        rx.cond(
            PlanningState.odoo_ready,
            rx.box(
                rx.text(PlanningState.odoo_details, size="2", color=MUTED, margin_y="1rem"),
                rx.el.form(
                    rx.flex(
                        rx.box(
                            rx.el.label(
                                "Demand quantity", html_for="odoo-quantity", display="block"
                            ),
                            rx.input(
                                id="odoo-quantity",
                                name="odoo_quantity",
                                type="number",
                                min="1",
                                max="1000",
                                step="1",
                                required=True,
                                default_value=PlanningState.odoo_quantity,
                                disabled=busy,
                            ),
                        ),
                        rx.box(
                            rx.el.label(
                                "Required date", html_for="odoo-required-date", display="block"
                            ),
                            rx.input(
                                id="odoo-required-date",
                                name="odoo_required_date",
                                type="date",
                                required=True,
                                default_value=PlanningState.odoo_required_date,
                                disabled=busy,
                            ),
                        ),
                        gap="1rem",
                        flex_wrap="wrap",
                        margin_bottom="1rem",
                    ),
                    rx.text("Your business terms", font_weight="650", margin_bottom="0.5rem"),
                    rx.text(
                        "Capacity and MOQ are supplied limits, not Odoo stock or quotation "
                        "quantities. Review every promised date.",
                        size="2",
                        color=MUTED,
                        margin_bottom="1rem",
                    ),
                    rx.grid(
                        rx.foreach(PlanningState.odoo_offers, _odoo_supplier_terms),
                        columns={"initial": "1", "md": "3"},
                        spacing="3",
                    ),
                    rx.text(
                        PlanningState.odoo_policy,
                        size="2",
                        color=MUTED,
                        max_width="75ch",
                        margin_y="1rem",
                    ),
                    rx.button("Create and save Odoo plan", type="submit", disabled=busy, size="3"),
                    on_submit=PlanningState.create_odoo,
                    reset_on_submit=False,
                ),
            ),
        ),
        value="odoo",
        padding_top="1.25rem",
    )


def _planning_controls() -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("Create a demo plan", value="create"),
            rx.tabs.trigger("Plan from Odoo", value="odoo"),
            rx.tabs.trigger("Open a saved case", value="stored"),
        ),
        _odoo_creation_controls(),
        rx.tabs.content(
            rx.text(
                (
                    "Use the prepared synthetic fixture to test input assembly, the saved "
                    "Decision Tree and MILP. No Odoo data is acquired in this form."
                ),
                color=MUTED,
                size="2",
                max_width="70ch",
                margin_bottom="1rem",
            ),
            rx.button(
                "Load demo inputs",
                on_click=PlanningState.prepare_demo,
                disabled=busy,
                variant="soft",
            ),
            rx.cond(
                PlanningState.demo_ready,
                rx.box(
                    rx.text(PlanningState.demo_details, size="2", color=MUTED, margin_y="1rem"),
                    rx.flex(
                        rx.foreach(
                            PlanningState.demo_offers,
                            lambda row: rx.box(
                                rx.text(row["name"], font_weight="600", size="2"),
                                rx.text(
                                    row["price"],
                                    " per unit · capacity ",
                                    row["capacity"],
                                    size="2",
                                    color=MUTED,
                                ),
                                padding_right="1.5rem",
                            ),
                        ),
                        flex_wrap="wrap",
                        gap="1rem",
                        margin_bottom="1rem",
                    ),
                    rx.el.form(
                        rx.flex(
                            rx.box(
                                rx.el.label(
                                    "Demand quantity",
                                    html_for="demo-quantity",
                                    display="block",
                                    margin_bottom="0.4rem",
                                ),
                                rx.input(
                                    id="demo-quantity",
                                    name="quantity",
                                    type="number",
                                    min="1",
                                    max="1000",
                                    step="1",
                                    default_value=PlanningState.demo_quantity,
                                    required=True,
                                    disabled=busy,
                                    width="10rem",
                                ),
                            ),
                            rx.button(
                                "Create and save plan", type="submit", disabled=busy, size="3"
                            ),
                            align="end",
                            gap="1rem",
                            flex_wrap="wrap",
                        ),
                        on_submit=PlanningState.create_demo,
                        reset_on_submit=False,
                    ),
                    rx.text(
                        PlanningState.demo_policy,
                        size="2",
                        color=MUTED,
                        margin_top="1rem",
                        max_width="70ch",
                    ),
                ),
            ),
            value="create",
            padding_top="1.25rem",
        ),
        rx.tabs.content(
            rx.text(
                (
                    "Retrieve an immutable saved result. This does not call Odoo, run the "
                    "model or recalculate the plan."
                ),
                size="2",
                color=MUTED,
                margin_bottom="1rem",
            ),
            rx.el.form(
                rx.flex(
                    rx.box(
                        rx.el.label(
                            "Case ID",
                            html_for="planning-case-id",
                            display="block",
                            margin_bottom="0.4rem",
                        ),
                        rx.input(
                            id="planning-case-id",
                            name="case_id",
                            required=True,
                            placeholder="Paste the saved case UUID",
                            width="100%",
                            disabled=busy,
                        ),
                        flex="1",
                        min_width="14rem",
                    ),
                    rx.button("Load stored case", type="submit", disabled=busy, size="3"),
                    align="end",
                    gap="1rem",
                    flex_wrap="wrap",
                ),
                on_submit=PlanningState.load_case,
                reset_on_submit=False,
            ),
            value="stored",
            padding_top="1.25rem",
        ),
        default_value="stored",
        width="100%",
    )


def planning_page() -> rx.Component:
    """Controlled creation, explicit what-if scenarios and immutable stored retrieval."""
    return rx.box(
        rx.box(
            rx.hstack(
                rx.link("Procurement workspace", href="/planning", color=INK, font_weight="650"),
                rx.link("Open RFQs", href="/", color=AUBERGINE),
                justify="between",
                max_width="72rem",
                margin="0 auto",
                padding="1.1rem 1.5rem",
            ),
            border_bottom=f"1px solid {HAIRLINE}",
            background=SURFACE,
        ),
        rx.vstack(
            rx.box(
                rx.heading(
                    "Compare procurement plans", as_="h1", size="8", letter_spacing="-0.035em"
                ),
                rx.text(
                    (
                        "See who supplies what, compare cost and test an outage before making a "
                        "decision."
                    ),
                    color=MUTED,
                    max_width="65ch",
                    margin_top="0.65rem",
                ),
            ),
            rx.box(
                _planning_controls(),
                background=SURFACE,
                border=f"1px solid {HAIRLINE}",
                border_radius="0.75rem",
                padding=["1rem", "1.5rem"],
                width="100%",
            ),
            rx.box(
                rx.cond(
                    PlanningState.is_loading,
                    rx.hstack(
                        rx.spinner(), rx.text("Waiting for the planning API…"), role="status"
                    ),
                ),
                rx.cond(
                    PlanningState.error_message != "",
                    rx.callout(
                        PlanningState.error_message,
                        color_scheme="red",
                        role="alert",
                        margin_bottom="1rem",
                    ),
                ),
                rx.cond(
                    PlanningState.has_pending & ~PlanningState.is_loading,
                    rx.box(
                        rx.button(
                            "Retry the same request",
                            on_click=PlanningState.recover_request,
                            disabled=PlanningState.is_loading,
                        ),
                        rx.text(
                            (
                                "Keep this tab open. Copy the exact request before leaving; "
                                "it contains the recovery key and inputs, never the service token."
                            ),
                            size="2",
                            color=MUTED,
                            margin_top="0.5rem",
                        ),
                        margin_bottom="1rem",
                    ),
                ),
                rx.cond(
                    PlanningState.notice != "",
                    rx.callout(PlanningState.notice, color_scheme="green", margin_bottom="1rem"),
                ),
                rx.cond(
                    PlanningState.has_case,
                    _recorded_case(),
                    rx.box(
                        rx.heading("Your plan comparison will appear here", as_="h2", size="5"),
                        rx.text(
                            "Open a saved case, or load the controlled demo inputs to create one.",
                            color=MUTED,
                            margin_top="0.5rem",
                        ),
                        padding="2rem 0",
                    ),
                ),
                aria_live="polite",
                width="100%",
            ),
            rx.cond(
                PlanningState.recovery_json != "",
                rx.el.details(
                    rx.el.summary("Request recovery record", cursor="pointer"),
                    rx.text(
                        "Idempotency key: ",
                        PlanningState.request_key,
                        size="2",
                        overflow_wrap="anywhere",
                        margin_y="0.75rem",
                    ),
                    rx.button(
                        "Copy exact request",
                        variant="soft",
                        on_click=rx.set_clipboard(PlanningState.recovery_json),
                    ),
                    rx.text_area(
                        value=PlanningState.recovery_json,
                        read_only=True,
                        aria_label="Exact request recovery JSON",
                        width="100%",
                        height="12rem",
                        margin_top="0.75rem",
                    ),
                ),
            ),
            rx.text(
                (
                    "Controlled demonstration. Synthetic ML history supports technical "
                    "testing; observed Odoo model validation and human approval remain "
                    "separate steps."
                ),
                color=MUTED,
                size="2",
                max_width="80ch",
            ),
            max_width="72rem",
            margin="0 auto",
            padding=["1.25rem", "2rem", "2.5rem"],
            spacing="6",
            align="stretch",
            width="100%",
            role="main",
        ),
        background=PAPER,
        color=INK,
        min_height="100vh",
        width="100%",
        font_family='"Segoe UI Variable", Aptos, "Segoe UI", sans-serif',
    )


app = rx.App()
app.add_page(index, route="/", on_load=RfqState.refresh_rfqs, title="Open RFQs")
app.add_page(planning_page, route="/planning", title="Procurement workspace")
