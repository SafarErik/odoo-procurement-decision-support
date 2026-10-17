"""Immutable input and provenance audit."""

import reflex as rx

from frontend.planning.decision import saved_decision
from frontend.planning.results import _recorded_sources
from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, MUTED


def audit_view() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Audit evidence",
            as_="h2",
            size="4",
            id="audit-evidence-heading",
            tab_index=-1,
            on_mount=rx.set_focus("audit-evidence-heading"),
        ),
        rx.text(
            "Inspect the saved record. Opening these sections does not refresh Odoo, "
            "train the model or recalculate plans.",
            size="2",
            color=MUTED,
            max_width="75ch",
        ),
        rx.callout(
            "Quotations and explicit terms retain their own source references. History references "
            "identify separately generated inputs or Odoo receipts of controlled synthetic origin. "
            "The model retains synthetic training provenance. Practice shares "
            "application storage; neither classification nor actor text establishes authority.",
            color_scheme="amber",
        ),
        rx.el.details(
            rx.el.summary(
                "Saved inputs, policy and allocations", cursor="pointer", font_weight="650"
            ),
            rx.vstack(
                rx.cond(
                    PlanningState.details["final_outcome"] != "",
                    rx.box(
                        saved_decision(),
                        rx.text(
                            "Approved content hash: ",
                            PlanningState.details["final_content_hash"],
                            overflow_wrap="anywhere",
                        ),
                        rx.el.details(
                            rx.el.summary(
                                "Exact final decision and approved content", cursor="pointer"
                            ),
                            rx.text(
                                PlanningState.details["final_audit"],
                                white_space="pre-wrap",
                                overflow_wrap="anywhere",
                                size="1",
                            ),
                        ),
                    ),
                ),
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
                        min_width="48rem",
                    ),
                    overflow_x="auto",
                    role="region",
                    aria_label="Exact saved supplier inputs",
                    tab_index=0,
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
                        rx.text(
                            plan["explanations"], white_space="pre-line", overflow_wrap="anywhere"
                        ),
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
                        min_width="24rem",
                    ),
                    overflow_x="auto",
                    role="region",
                    aria_label="Exact saved allocations",
                    tab_index=0,
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
                        min_width="48rem",
                    ),
                    overflow="auto",
                    role="region",
                    aria_label="Exact field provenance",
                    tab_index=0,
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
        rx.el.details(
            rx.el.summary(
                "Supplier tree paths and model evidence", cursor="pointer", font_weight="650"
            ),
            rx.foreach(
                PlanningState.assessments,
                lambda row: rx.el.details(
                    rx.el.summary(row["name"] + " — exact tree record", cursor="pointer"),
                    rx.text("Supplier ID: ", row["supplier"]),
                    rx.text("Recorded class: ", row["class"], " · Exact score: ", row["score"]),
                    rx.text("Model: ", row["model"]),
                    rx.text("Saved history reference: ", row["source"]),
                    rx.text(row["path"], white_space="pre-line"),
                    rx.text(
                        "Node/leaf IDs, support, features, thresholds and version metadata "
                        "are retained in Complete saved snapshot JSON.",
                        size="2",
                        color=MUTED,
                    ),
                    padding_y="0.75rem",
                ),
            ),
        ),
        rx.el.details(
            rx.el.summary("Complete saved snapshot JSON", cursor="pointer", font_weight="650"),
            rx.text(
                "Exact stored facts, request/policy, assessments/paths/versions, solver "
                "records, provenance and scenario comparison. Presentation labels above "
                "do not replace this record.",
                size="2",
                color=MUTED,
                margin_y="0.75rem",
            ),
            rx.el.pre(
                PlanningState.details["snapshot_json"],
                overflow="auto",
                max_height="24rem",
                width="100%",
                min_width="0",
                role="region",
                tab_index=0,
                aria_label="Complete saved snapshot JSON",
                font_size="0.875rem",
            ),
        ),
        spacing="4",
        align="stretch",
        width="100%",
        min_width="0",
        overflow_wrap="anywhere",
    )
