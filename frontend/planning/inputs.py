"""Procurement cockpit presentation components."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, MUTED


def _odoo_supplier_terms(row: rx.Var[dict[str, str]]) -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    return rx.box(
        rx.text(row["name"], font_weight="650", size="2"),
        rx.text(row["price"], " per unit", size="2", color=MUTED),
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
            rx.tabs.trigger("Saved case", value="stored"),
            rx.tabs.trigger("Odoo", value="odoo"),
            rx.tabs.trigger("Demo", value="create"),
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
        value=PlanningState.input_mode,
        on_change=PlanningState.change_input_mode,
        width="100%",
    )
