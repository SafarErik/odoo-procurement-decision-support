"""Scenario composer and immutable base-versus-scenario comparison."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, MUTED, SURFACE


def _scenario_form() -> rx.Component:
    busy = PlanningState.is_loading | PlanningState.has_pending
    combined = PlanningState.scenario_kind == "combined"
    return rx.box(
        rx.heading("Test changed assumptions. Save a new scenario.", as_="h2", size="4"),
        rx.text(
            "Each run starts from the original saved base, even when viewing a "
            "scenario. The same MILP runs with saved supplier scores. Odoo stays unchanged.",
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
                        ("Capacity change", "capacity_change"),
                        ("Demand change", "demand_change"),
                        ("Price change", "price_change"),
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
                PlanningState.scenario_kind != "demand_change",
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
                    (PlanningState.scenario_kind == "demand_change") | combined,
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
                            "Higher or lower than the original demand: ",
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
                    (PlanningState.scenario_kind == "capacity_change") | combined,
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
                            "Higher or lower than the original capacity. Zero removes capacity; "
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
                    (PlanningState.scenario_kind == "price_change") | combined,
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
                            "Higher or lower than the original price. This is a simulated quote, "
                            "not a fresh Odoo price.",
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
                rx.text(
                    "Original base: ",
                    PlanningState.details["base_id"],
                    size="1",
                    color=MUTED,
                ),
                rx.text(
                    "Changed-demand totals are not like-for-like savings. "
                    "What-if prices are simulated assumptions, not fresh quotations.",
                    size="2",
                    margin_top="0.5rem",
                    max_width="75ch",
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
                    id="scenario-error",
                    tab_index=-1,
                    on_mount=rx.set_focus("scenario-error"),
                    margin_bottom="1rem",
                ),
            ),
            rx.button("Create and save scenario", type="submit", disabled=busy, size="3"),
            on_submit=PlanningState.run_scenario.throttle(500),
            reset_on_submit=False,
        ),
        width="100%",
        margin_bottom="1.5rem",
    )


def _scenario_comparison() -> rx.Component:
    child = PlanningState.details["parent_id"] != "Base case"
    return rx.el.section(
        rx.heading(
            rx.cond(child, "Saved scenario comparison", "Original base before disruption"),
            as_="h2",
            size="5",
            id="scenario-result-heading",
            tab_index=-1,
        ),
        rx.text("Original base: ", PlanningState.details["base_id"], size="2", color=MUTED),
        rx.cond(
            child,
            rx.box(
                rx.text(
                    "Saved scenario: ", PlanningState.details["case_id"], size="2", color=MUTED
                ),
                rx.text(
                    "Saved assumptions: ",
                    PlanningState.details["assumptions"],
                    size="2",
                    margin_y="0.75rem",
                ),
                rx.button(
                    "Return to original base",
                    on_click=PlanningState.open_saved_case(PlanningState.details["base_id"]),
                    disabled=PlanningState.is_loading | PlanningState.has_pending,
                    variant="outline",
                    margin_bottom="1rem",
                ),
            ),
        ),
        rx.cond(
            PlanningState.original_error != "",
            rx.box(
                rx.callout(PlanningState.original_error, role="alert", color_scheme="red"),
                rx.button(
                    "Retry original-base retrieval",
                    on_click=PlanningState.retry_original,
                    disabled=PlanningState.is_loading | PlanningState.has_pending,
                    variant="outline",
                    margin_y="0.75rem",
                ),
            ),
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Result"),
                        rx.table.column_header_cell("Original base"),
                        rx.cond(child, rx.table.column_header_cell("Saved scenario")),
                        rx.cond(child, rx.table.column_header_cell("Change")),
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        PlanningState.scenario_metrics,
                        lambda row: rx.table.row(
                            rx.table.row_header_cell(row["metric"]),
                            rx.table.cell(row["base"]),
                            rx.cond(child, rx.table.cell(row["scenario"])),
                            rx.cond(child, rx.table.cell(row["change"])),
                        ),
                    ),
                    rx.foreach(
                        PlanningState.scenario_allocation_rows,
                        lambda row: rx.table.row(
                            rx.table.row_header_cell(row["name"]),
                            rx.table.cell(row["base"]),
                            rx.cond(child, rx.table.cell(row["scenario"])),
                            rx.cond(child, rx.table.cell(row["change"])),
                        ),
                    ),
                ),
                min_width=rx.cond(child, "38rem", "24rem"),
                width="100%",
            ),
            role="region",
            aria_label="Exact original-base and scenario comparison",
            tab_index=0,
            overflow_x="auto",
            width="100%",
            margin_y="1rem",
        ),
        rx.cond(
            child & (PlanningState.details["quantity"] != PlanningState.details["base_quantity"]),
            rx.text(
                "Demand changed: these totals cover different quantities, "
                "not a like-for-like saving.",
                size="2",
                margin_bottom="0.75rem",
                max_width="75ch",
            ),
        ),
        rx.cond(
            child & (PlanningState.plans.length() == 0),
            rx.callout(
                "No proven scenario minimum-cost plan is available. Its cost, exposure and "
                "allocations are unavailable, not zero. The original saved result remains above. "
                "Read the saved outcome and diagnostics in Audit.",
                color_scheme="amber",
                margin_bottom="0.75rem",
            ),
        ),
        rx.text(
            "Costs and allocations compare minimum-cost plans. Exposure is an uncalibrated "
            "synthetic proxy, not failure probability. What-if prices are simulated assumptions, "
            "not fresh quotations. Scenarios remain analytical and cannot be approved.",
            size="2",
            color=MUTED,
            max_width="75ch",
        ),
        aria_label="Original base and saved scenario",
        margin_bottom="1.5rem",
        width="100%",
    )
