"""Immutable input and provenance audit."""

import reflex as rx

from frontend.planning.results import _recorded_sources
from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE


def audit_view() -> rx.Component:
    return rx.el.details(
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
                "Product identity: ",
                PlanningState.details["product"],
                " · Quantity unit: ",
                PlanningState.details["unit"],
                overflow_wrap="anywhere",
            ),
            rx.heading("Saved inputs for this case", as_="h3", size="3"),
            rx.text(PlanningState.details["policy"]),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            *[
                                rx.table.column_header_cell(label)
                                for label in (
                                    "Supplier",
                                    "Unit price",
                                    "Capacity",
                                    "MOQ",
                                    "Promised",
                                    "Availability",
                                    "Quantity applicability",
                                )
                            ]
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            PlanningState.scenario_suppliers,
                            lambda row: rx.table.row(
                                rx.table.cell(row["name"]),
                                rx.table.cell(
                                    row["saved_price"], " ", PlanningState.details["currency"]
                                ),
                                rx.table.cell(row["saved_capacity"]),
                                rx.table.cell(row["saved_moq"]),
                                rx.table.cell(row["saved_date"]),
                                rx.table.cell(row["saved_available"]),
                                rx.table.cell(row["saved_ranges"]),
                            ),
                        )
                    ),
                ),
                overflow_x="auto",
                width="100%",
            ),
            rx.text(
                "Snapshot hash: ",
                PlanningState.details["snapshot_hash"],
                overflow_wrap="anywhere",
            ),
            rx.text(PlanningState.details["explanations"], white_space="pre-line"),
            rx.text(PlanningState.details["comparison"], white_space="pre-line"),
            rx.foreach(
                PlanningState.plans,
                lambda plan: rx.el.details(
                    rx.el.summary(
                        plan["label"] + " — exact values and solver notes", cursor="pointer"
                    ),
                    rx.text("Exposure: ", plan["exposure"]),
                    rx.text("Cost premium: ", plan["premium"]),
                    rx.text(plan["explanations"], white_space="pre-line", overflow_wrap="anywhere"),
                ),
            ),
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
        open=True,
    )
