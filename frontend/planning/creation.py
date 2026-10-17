"""Attributed creation review and field feedback; all writes remain HTTP events."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, MUTED, SURFACE


def field_error(identity):
    error = PlanningState.creation_errors.get(identity, "")
    return rx.cond(
        error != "",
        rx.text(error, id=identity + "-error", role="alert", color="#92313b", size="2"),
    )


def creation_review(kind: str):
    return rx.cond(
        PlanningState.creation_review.get("kind", "") == kind,
        rx.box(
            rx.heading(
                "Review before calculating",
                as_="h3",
                size="5",
                id="creation-review-heading",
                tab_index=-1,
                on_mount=rx.set_focus("creation-review-heading"),
            ),
            rx.text(PlanningState.creation_review["product"], font_weight="650", margin_top="1rem"),
            rx.text(
                rx.cond(
                    PlanningState.has_pending,
                    "Save awaiting confirmation. Recover the same request; "
                    "do not approve to finish saving.",
                    "Unsaved draft. Calculating saves the comparison; it does not approve a plan.",
                )
            ),
            rx.text(
                PlanningState.creation_review["quantity"],
                " ",
                PlanningState.creation_review["unit"],
                " · ",
                PlanningState.creation_review["currency"],
                " · required ",
                PlanningState.creation_review["required_date"],
            ),
            rx.text(
                "Company: ",
                PlanningState.creation_review["company"],
                " · Purpose: ",
                PlanningState.creation_review["workspace"],
                size="2",
                color=MUTED,
            ),
            rx.text(
                "Prepared capture / simulation cutoff: ",
                PlanningState.creation_review["captured"],
                size="2",
                color=MUTED,
            ),
            rx.cond(
                kind == "odoo",
                rx.text(
                    rx.cond(
                        PlanningState.odoo_history_mode,
                        "This preview captures Odoo history. Saving reads it again. ",
                        "This local preview does not refresh Odoo. ",
                    ),
                    "FastAPI independently rereads quotations and any selected Odoo history "
                    "and checks captured expectations when saving. "
                    "Prices/identities are quotation facts; demand, capacity, MOQ and dates "
                    "are your supplied terms.",
                    size="2",
                    margin_y="1rem",
                ),
                rx.text(
                    "All prepared quotation facts, limits, dates and supplier history are "
                    "synthetic. Only demand is edited here; the other prepared terms stay fixed.",
                    size="2",
                    margin_y="1rem",
                ),
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            *[
                                rx.table.column_header_cell(label, white_space="nowrap")
                                for label in (
                                    "Supplier",
                                    "Offer identity",
                                    "Unit price",
                                    "Capacity",
                                    "MOQ",
                                    "Promised",
                                    "Availability",
                                    "Applicability",
                                )
                            ]
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            PlanningState.review_suppliers,
                            lambda row: rx.table.row(
                                rx.table.cell(row["name"]),
                                rx.table.cell(row["offer"]),
                                rx.table.cell(
                                    row["price"], " ", PlanningState.creation_review["currency"]
                                ),
                                *[
                                    rx.table.cell(row[field])
                                    for field in (
                                        "capacity",
                                        "moq",
                                        "promised",
                                        "available",
                                        "ranges",
                                    )
                                ],
                            ),
                        )
                    ),
                    min_width="60rem",
                ),
                width="100%",
                overflow_x="auto",
                role="region",
                tab_index=0,
                aria_label="Reviewed exact supplier terms",
            ),
            rx.text(
                "Prepared policy: ",
                PlanningState.creation_review["policy"],
                size="2",
                margin_y="1rem",
                max_width="75ch",
            ),
            rx.text(
                PlanningState.creation_review.get("history_source", "Separately synthetic history"),
                size="2",
                margin_top="0.75rem",
            ),
            rx.text(
                "Supplier history and Decision Tree evidence remain synthetic. "
                "The API checks applicability, policy and feasibility when calculating. "
                "Review does not save, solve or approve a plan.",
                size="2",
                max_width="75ch",
            ),
            rx.flex(
                rx.button(
                    "Edit terms",
                    id="creation-edit-terms",
                    on_click=PlanningState.edit_creation_terms,
                    variant="outline",
                    disabled=PlanningState.has_pending | PlanningState.is_loading,
                ),
                rx.button(
                    "Calculate and save comparison",
                    on_click=PlanningState.save_reviewed_creation,
                    disabled=PlanningState.has_pending | PlanningState.is_loading,
                    background=ACCENT,
                    color="white",
                ),
                gap="1rem",
                wrap="wrap",
                margin_top="1.25rem",
            ),
            background=SURFACE,
            border=f"1px solid {HAIRLINE}",
            padding="1rem",
            margin_top="1.25rem",
            min_width="0",
        ),
    )
