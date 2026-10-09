"""Scenario composer and immutable base-versus-scenario comparison."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import CONNECTED, HAIRLINE, MUTED, SURFACE


def _scenario_form() -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    combined = PlanningState.scenario_kind == "combined"
    return rx.box(
        rx.heading("Change one assumption. Save a new scenario.", as_="h2", size="4"),
        rx.text(
            "Each run starts from the original saved base, even when viewing a "
            "scenario. Odoo stays unchanged; saved supplier scores are reused.",
            size="2",
            color=MUTED,
            max_width="75ch",
            margin_y="0.75rem",
        ),
        rx.el.form(
            rx.el.label("Scenario type", html_for="stress-kind", display="block"),
            rx.el.select(
                *[
                    rx.el.option(label, value=value)
                    for label, value in (
                        ("Supplier outage", "supplier_outage"),
                        ("Capacity reduction", "capacity_reduction"),
                        ("Demand increase", "demand_increase"),
                        ("Price increase", "price_increase"),
                        ("Combined changes", "combined"),
                    )
                ],
                id="stress-kind",
                name="kind",
                value=PlanningState.scenario_kind,
                on_change=PlanningState.change_scenario_kind,
                disabled=busy,
                padding="0.65rem",
                width="100%",
                border=f"1px solid {HAIRLINE}",
                border_radius="6px",
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
                            lambda row: rx.el.option(row["name"], value=row["supplier"]),
                        ),
                        id="stress-supplier",
                        name="supplier",
                        value=PlanningState.stress_supplier,
                        on_change=PlanningState.select_stress_supplier,
                        required=True,
                        disabled=busy,
                        padding="0.65rem",
                        width="100%",
                        border=f"1px solid {HAIRLINE}",
                        border_radius="6px",
                        background=SURFACE,
                    ),
                    rx.cond(
                        PlanningState.stress_supplier != "",
                        rx.text(
                            "Original capacity: ",
                            PlanningState.selected_terms["capacity"],
                            " units. Original price: ",
                            PlanningState.selected_terms["price"],
                            " ",
                            PlanningState.details["currency"],
                            "/unit.",
                            size="2",
                            color=MUTED,
                            margin_top="0.5rem",
                        ),
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
                        rx.el.input(
                            id="stress-quantity",
                            name="quantity",
                            type="text",
                            input_mode="numeric",
                            pattern="[0-9]{1,4}",
                            max_length=4,
                            value=PlanningState.stress_quantity,
                            on_change=lambda value: PlanningState.update_stress("quantity", value),
                            required=~combined,
                            disabled=busy,
                            width="100%",
                            padding="0.65rem",
                            border=f"1px solid {HAIRLINE}",
                            border_radius="6px",
                        ),
                        rx.text(
                            "Must exceed original demand: ",
                            PlanningState.details["base_quantity"],
                            " units.",
                            size="2",
                            color=MUTED,
                            margin_top="0.4rem",
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
                        rx.el.input(
                            id="stress-capacity",
                            name="capacity",
                            type="text",
                            input_mode="numeric",
                            pattern="[0-9]{1,4}",
                            max_length=4,
                            value=PlanningState.stress_capacity,
                            on_change=lambda value: PlanningState.update_stress("capacity", value),
                            required=~combined,
                            disabled=busy,
                            width="100%",
                            padding="0.65rem",
                            border=f"1px solid {HAIRLINE}",
                            border_radius="6px",
                        ),
                        rx.text(
                            "Must be lower than the original capacity. Zero removes capacity; "
                            "MOQ still applies.",
                            size="2",
                            color=MUTED,
                            margin_top="0.4rem",
                        ),
                        flex="1",
                        min_width="12rem",
                    ),
                ),
                rx.cond(
                    (PlanningState.scenario_kind == "price_increase") | combined,
                    rx.box(
                        rx.el.label("New price per unit", html_for="stress-price", display="block"),
                        rx.el.input(
                            id="stress-price",
                            name="price",
                            type="text",
                            input_mode="decimal",
                            max_length=64,
                            placeholder="e.g. 12.50",
                            value=PlanningState.stress_price,
                            on_change=lambda value: PlanningState.update_stress("price", value),
                            required=~combined,
                            disabled=busy,
                            width="100%",
                            padding="0.65rem",
                            border=f"1px solid {HAIRLINE}",
                            border_radius="6px",
                        ),
                        rx.text(
                            "Must exceed the original price. This is a simulated quote, not a "
                            "fresh Odoo price.",
                            size="2",
                            color=MUTED,
                            margin_top="0.4rem",
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
                    "Enter at least two changes; capacity and price apply to one "
                    "supplier. Leave unused fields blank.",
                    size="2",
                    color=MUTED,
                    margin_bottom="1rem",
                ),
            ),
            rx.box(
                rx.text("Draft assumptions", font_weight="650", size="2"),
                rx.text(
                    PlanningState.scenario_draft,
                    size="2",
                    white_space="pre-line",
                    margin_top="0.5rem",
                ),
                rx.text(
                    "The MILP run will establish feasibility. The base case will stay unchanged.",
                    size="1",
                    color=MUTED,
                    margin_top="0.5rem",
                ),
                padding="1rem",
                background="#EFF3F6",
                border_radius="6px",
                margin_bottom="1rem",
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
            rx.button("Create and save scenario", type="submit", disabled=busy, size="3"),
            on_submit=PlanningState.run_scenario,
            reset_on_submit=False,
        ),
        width="100%",
        margin_bottom="1.5rem",
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
        margin_bottom="1.5rem",
    )
