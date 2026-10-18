"""Procurement cockpit presentation components."""

import reflex as rx

from frontend.planning.creation import creation_review, field_error
from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, MUTED


def _odoo_supplier_terms(row: rx.Var[dict[str, str]]) -> rx.Component:
    busy = (
        PlanningState.is_loading
        | PlanningState.has_pending
        | (PlanningState.creation_review.get("kind", "") != "")
    )
    return rx.box(
        rx.text(row["name"], font_weight="650", size="2"),
        rx.text(row["price"], " per unit", size="2", color=MUTED),
        rx.text("Captured Odoo price; checked again when saving.", size="1", color=MUTED),
        rx.text("Captured offer: ", row["offer"], size="1", color=MUTED),
        rx.text(row["ranges"], size="1", color=MUTED, margin_y="0.5rem"),
        rx.el.label(
            "Capacity (explicit limit)", html_for=row["supplier"] + "_capacity", display="block"
        ),
        rx.input(
            id=row["supplier"] + "_capacity",
            aria_invalid=PlanningState.creation_errors.get(row["supplier"] + "_capacity", "") != "",
            aria_describedby=row["supplier"] + "_capacity-error",
            name=row["supplier"] + "_capacity",
            type="number",
            min="0",
            max="1000",
            step="1",
            required=True,
            on_change=PlanningState.mark_creation_dirty,
            default_value=row["capacity"],
            disabled=busy,
            width="100%",
        ),
        field_error(row["supplier"] + "_capacity"),
        rx.el.label(
            "MOQ (blank means none)",
            html_for=row["supplier"] + "_moq",
            display="block",
            margin_top="0.75rem",
        ),
        rx.input(
            id=row["supplier"] + "_moq",
            aria_invalid=PlanningState.creation_errors.get(row["supplier"] + "_moq", "") != "",
            aria_describedby=row["supplier"] + "_moq-error",
            name=row["supplier"] + "_moq",
            type="number",
            min="1",
            max="1000",
            step="1",
            on_change=PlanningState.mark_creation_dirty,
            default_value=row["moq"],
            disabled=busy,
            width="100%",
        ),
        field_error(row["supplier"] + "_moq"),
        rx.el.label(
            "Promised date",
            html_for=row["supplier"] + "_promised_date",
            display="block",
            margin_top="0.75rem",
        ),
        rx.input(
            id=row["supplier"] + "_promised_date",
            aria_invalid=PlanningState.creation_errors.get(row["supplier"] + "_promised_date", "")
            != "",
            aria_describedby=row["supplier"] + "_promised_date-error",
            name=row["supplier"] + "_promised_date",
            type="date",
            required=True,
            on_change=PlanningState.mark_creation_dirty,
            default_value=row["promised_date"],
            disabled=busy,
            width="100%",
        ),
        field_error(row["supplier"] + "_promised_date"),
        padding="1rem",
        border=f"1px solid {HAIRLINE}",
        border_radius="8px",
    )


def _odoo_creation_controls() -> rx.Component:
    busy = (
        PlanningState.is_loading
        | PlanningState.has_pending
        | (PlanningState.creation_review.get("kind", "") != "")
    )
    return rx.tabs.content(
        rx.text(
            "Choose an open Odoo quotation group. FastAPI reads its quotations and the "
            "product's purchase history from Odoo, and reads them again before saving. "
            "You supply demand and supplier limits.",
            color=MUTED,
            size="2",
            max_width="75ch",
            margin_bottom="1rem",
        ),
        rx.flex(
            rx.button(
                "Load open quotation groups",
                id="load-quotation-groups",
                on_click=PlanningState.load_quotation_groups,
                disabled=busy,
                variant="soft",
            ),
            rx.el.label(
                "Quotation group",
                html_for="quotation-group",
                position="absolute",
                width="1px",
                height="1px",
                overflow="hidden",
            ),
            rx.el.select(
                rx.el.option("Choose a quotation group", value="", disabled=True),
                rx.foreach(
                    PlanningState.quotation_groups,
                    lambda row: rx.el.option(
                        row["label"], value=row["value"], disabled=row["selectable"] == ""
                    ),
                ),
                id="quotation-group",
                value=PlanningState.selected_group,
                on_change=PlanningState.select_quotation_group,
                disabled=busy | (PlanningState.quotation_groups.length() == 0),
                padding="0.5rem",
                border=f"1px solid {HAIRLINE}",
                border_radius="6px",
                max_width="100%",
                min_width="0",
                flex="1 1 16rem",
            ),
            rx.button(
                "Use history from Odoo",
                id="load-odoo-history",
                on_click=PlanningState.prepare_odoo_history,
                disabled=busy | (PlanningState.selected_group == ""),
                variant="soft",
            ),
            gap="0.75rem",
            flex_wrap="wrap",
            align="center",
        ),
        rx.cond(
            PlanningState.odoo_history_mode,
            rx.box(
                rx.text(
                    "Purchase history is read from Odoo. In this test database it is "
                    "generated test data. No training occurs here.",
                    size="2",
                ),
                rx.foreach(
                    PlanningState.odoo_history_rows,
                    lambda row: rx.text(
                        row["supplier"],
                        ": ",
                        row["summary"],
                        size="2",
                    ),
                ),
                rx.text("Model status: ", PlanningState.odoo_history_readiness, size="2"),
                margin_y="1rem",
            ),
        ),
        rx.cond(
            PlanningState.odoo_ready,
            rx.box(
                rx.heading("Prepared quotation facts", as_="h3", size="4"),
                rx.text(PlanningState.odoo_details, size="2", color=MUTED, margin_y="1rem"),
                rx.heading("Your demand", as_="h3", size="4"),
                rx.el.form(
                    rx.flex(
                        rx.box(
                            rx.el.label(
                                "Demand quantity", html_for="odoo-quantity", display="block"
                            ),
                            rx.input(
                                id="odoo-quantity",
                                aria_invalid=PlanningState.creation_errors.get("odoo-quantity", "")
                                != "",
                                aria_describedby="odoo-quantity-error",
                                name="odoo_quantity",
                                type="number",
                                min="1",
                                max="1000",
                                step="1",
                                required=True,
                                on_change=PlanningState.mark_creation_dirty,
                                default_value=PlanningState.odoo_quantity,
                                disabled=busy,
                            ),
                            field_error("odoo-quantity"),
                        ),
                        rx.box(
                            rx.el.label(
                                "Required date", html_for="odoo-required-date", display="block"
                            ),
                            rx.input(
                                id="odoo-required-date",
                                aria_invalid=PlanningState.creation_errors.get(
                                    "odoo-required-date", ""
                                )
                                != "",
                                aria_describedby="odoo-required-date-error",
                                name="odoo_required_date",
                                type="date",
                                required=True,
                                on_change=PlanningState.mark_creation_dirty,
                                default_value=PlanningState.odoo_required_date,
                                disabled=busy,
                            ),
                            field_error("odoo-required-date"),
                        ),
                        gap="1rem",
                        flex_wrap="wrap",
                        margin_bottom="1rem",
                    ),
                    rx.heading(
                        "Your business terms",
                        as_="h3",
                        size="4",
                        font_weight="650",
                        margin_bottom="0.5rem",
                    ),
                    rx.text(
                        "Capacity and MOQ are supplied limits, not Odoo stock or quotation "
                        "quantities. Review every promised date.",
                        size="2",
                        color=MUTED,
                        margin_bottom="1rem",
                    ),
                    rx.grid(
                        rx.foreach(PlanningState.odoo_offers, _odoo_supplier_terms),
                        columns=rx.breakpoints(initial="1", md="3"),
                        spacing="3",
                    ),
                    rx.text(
                        PlanningState.odoo_policy,
                        size="2",
                        color=MUTED,
                        max_width="75ch",
                        margin_y="1rem",
                    ),
                    rx.button(
                        "Review Odoo terms",
                        type="submit",
                        disabled=busy
                        | (
                            PlanningState.odoo_history_mode
                            & (PlanningState.odoo_history_readiness != "ready")
                        ),
                        size="3",
                    ),
                    on_submit=PlanningState.review_odoo,
                    no_validate=True,
                    reset_on_submit=False,
                ),
                creation_review("odoo"),
            ),
        ),
        value="odoo",
        padding_top="1.25rem",
    )


def _planning_controls() -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("Saved case", value="stored", id="input-stored", disabled=busy),
            rx.tabs.trigger("Odoo", value="odoo", id="input-odoo", disabled=busy),
        ),
        _odoo_creation_controls(),
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
        value=PlanningState.input_mode,
        on_change=PlanningState.change_input_mode,
        width="100%",
    )
