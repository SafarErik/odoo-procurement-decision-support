"""RFQ ledger and stored planning display through the documented FastAPI boundary."""

from typing import Any

import reflex as rx

from frontend.config import settings
from frontend.planning_client import fetch_planning_case
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
    """Browser-visible display values only; the service secret stays in config."""

    details: dict[str, str] = {}
    plans: list[dict[str, str]] = []
    allocations: list[dict[str, str]] = []
    assessments: list[dict[str, str]] = []
    provenance: list[dict[str, str]] = []
    error_message: str = ""
    is_loading: bool = False
    has_case: bool = False

    @rx.event
    async def load_case(self, form_data: dict[str, Any]):
        self.has_case = False
        self.details = {}
        self.plans = []
        self.allocations = []
        self.assessments = []
        self.provenance = []
        self.error_message = ""
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
                self.details = result.details
                self.plans = result.plans
                self.allocations = result.allocations
                self.assessments = result.assessments
                self.provenance = result.provenance
                self.has_case = True
        finally:
            self.is_loading = False


def _recorded_plan(plan: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.box(
        rx.heading(plan["label"], as_="h3", size="4", color=INK),
        rx.text(plan["cost"], size="7", font_weight="600", margin_y="0.75rem"),
        rx.text("Exposure proxy: ", plan["exposure"], color=MUTED),
        rx.text("Cost premium ratio: ", plan["premium"], color=MUTED),
        rx.el.details(
            rx.el.summary("Recorded plan explanations", cursor="pointer"),
            rx.text(plan["explanations"], white_space="pre-line", margin_top="0.75rem"),
            margin_top="1rem",
        ),
        border=f"1px solid {HAIRLINE}",
        background=SURFACE,
        border_radius="0.5rem",
        padding="1.25rem",
    )


def _recorded_assessment(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.el.details(
        rx.el.summary(row["supplier"], " — score ", row["score"], cursor="pointer"),
        rx.text("Class: ", row["class"], " · Recorded validity: ", row["valid_until"]),
        rx.text(row["path"], white_space="pre-line", margin_y="0.75rem"),
        rx.text("Synthetic source: ", row["source"], overflow_wrap="anywhere"),
        rx.text("Model: ", row["model"], overflow_wrap="anywhere"),
        padding="1rem",
        border_bottom=f"1px solid {HAIRLINE}",
    )


def _recorded_sources(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["field"]),
        rx.table.cell(row["type"]),
        rx.table.cell(row["reference"]),
        rx.table.cell(row["observed_at"]),
    )


def _recorded_case() -> rx.Component:
    return rx.vstack(
        rx.callout(
            rx.text(
                PlanningState.details["input_kind"],
                ". ML scores are synthetic exposure proxies, not failure probabilities.",
                as_="span",
            ),
            color_scheme="plum",
            width="100%",
        ),
        rx.heading(PlanningState.details["status"], as_="h2", size="5"),
        rx.text("Scenario: ", PlanningState.details["scenario"]),
        rx.text("Product: ", PlanningState.details["product"]),
        rx.text(
            "Demand: ",
            PlanningState.details["quantity"],
            " ",
            PlanningState.details["unit"],
            " · Required: ",
            PlanningState.details["required_date"],
        ),
        rx.cond(
            PlanningState.plans.length() > 0,
            rx.grid(
                rx.foreach(PlanningState.plans, _recorded_plan),
                columns=rx.breakpoints(initial="1", md="2"),
                gap="1rem",
                width="100%",
            ),
            rx.callout("No proven plan is recorded for this run.", color_scheme="amber"),
        ),
        rx.text(PlanningState.details["explanations"], white_space="pre-line"),
        rx.text(PlanningState.details["comparison"], white_space="pre-line"),
        rx.el.details(
            rx.el.summary("Stored case identity and timestamps", cursor="pointer"),
            rx.text("Case: ", PlanningState.details["case_id"], overflow_wrap="anywhere"),
            rx.text("Parent: ", PlanningState.details["parent_id"], overflow_wrap="anywhere"),
            rx.text("Company: ", PlanningState.details["company"]),
            rx.text("Created: ", PlanningState.details["created_at"]),
            rx.text("Recorded cutoff: ", PlanningState.details["as_of"]),
            rx.text(
                "Snapshot hash: ", PlanningState.details["snapshot_hash"], overflow_wrap="anywhere"
            ),
        ),
        rx.heading("Recorded allocations", as_="h2", size="4"),
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
                width="100%",
            ),
            overflow_x="auto",
            width="100%",
        ),
        rx.heading("Saved supplier evaluation and tree paths", as_="h2", size="4"),
        rx.text(
            "Recorded validity is historical; viewing this case does not refresh its scores.",
            color=MUTED,
        ),
        rx.box(rx.foreach(PlanningState.assessments, _recorded_assessment), width="100%"),
        rx.el.details(
            rx.el.summary("Field provenance", cursor="pointer"),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Field"),
                            rx.table.column_header_cell("Source type"),
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
            width="100%",
        ),
        spacing="4",
        align="stretch",
        width="100%",
    )


def planning_page() -> rx.Component:
    """Read an existing immutable case; no creation, scenario mutation or approval."""
    return rx.box(
        rx.vstack(
            rx.link("← Open RFQs", href="/", color=AUBERGINE),
            rx.heading("Stored procurement plans", size="8", color=INK),
            rx.text("Review a saved base or scenario case without recalculating it.", color=MUTED),
            rx.el.form(
                rx.vstack(
                    rx.el.label("Planning case UUID", html_for="planning-case-id"),
                    rx.input(
                        id="planning-case-id",
                        name="case_id",
                        required=True,
                        placeholder="Paste a case UUID from your completed terminal run",
                        width="100%",
                        disabled=PlanningState.is_loading,
                    ),
                    rx.button("Load stored case", type="submit", loading=PlanningState.is_loading),
                    align="stretch",
                    spacing="3",
                    width="100%",
                ),
                on_submit=PlanningState.load_case,
                reset_on_submit=False,
                width="100%",
            ),
            rx.box(
                rx.cond(
                    PlanningState.is_loading,
                    rx.hstack(rx.spinner(), rx.text("Loading stored case…")),
                    rx.cond(
                        PlanningState.error_message != "",
                        rx.callout(PlanningState.error_message, color_scheme="red", role="alert"),
                        rx.cond(
                            PlanningState.has_case,
                            _recorded_case(),
                            rx.text("Load a saved case to see its recorded results.", color=MUTED),
                        ),
                    ),
                ),
                aria_live="polite",
                width="100%",
            ),
            max_width="72rem",
            margin="0 auto",
            padding=["1.25rem", "2rem", "2.5rem"],
            spacing="5",
            align="stretch",
            width="100%",
        ),
        background=PAPER,
        color=INK,
        min_height="100vh",
        width="100%",
        font_family='"Segoe UI Variable", Aptos, "Segoe UI", sans-serif',
    )


app = rx.App()
app.add_page(index, route="/", on_load=RfqState.refresh_rfqs, title="Open RFQs")
app.add_page(planning_page, route="/planning", title="Stored procurement plans")
