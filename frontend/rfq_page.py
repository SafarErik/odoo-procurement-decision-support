"""Read-only RFQ ledger."""

import reflex as rx

from frontend.config import settings
from frontend.rfq_client import fetch_rfq_dashboard
from frontend.theme import ACCENT, CONNECTED, ERROR, HAIRLINE, INK, MUTED, PAPER, SURFACE


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
        color=ACCENT,
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
            rx.spinner(color=ACCENT, size="3"),
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
                            background=ACCENT,
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
                        rx.link("Saved cases", href="/cases", color=ACCENT),
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
                        background=ACCENT,
                        color="white",
                        border_radius="0.5rem",
                        padding="0.65rem 1rem",
                        cursor="pointer",
                        _hover={"background": "#5D3E55"},
                        _focus_visible={"outline": f"3px solid {ACCENT}55"},
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
