"""Open RFQs: pick an open Odoo quotation group, set business terms, review, save a case."""

import reflex as rx

from frontend.planning.recovery import recovery
from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, INK, MUTED
from frontend.ui import card, empty_state, error_state, heading, loading_state, muted, t
from frontend.workspace import page_frame, workspace_shell

BUSY = PlanningState.is_loading | PlanningState.has_pending
LOCKED = BUSY | (PlanningState.creation_review.get("kind", "") != "")


def field_error(identity):
    error = PlanningState.creation_errors.get(identity, "")
    return rx.cond(
        error != "",
        rx.text(error, id=identity + "-error", role="alert", color="#92313b", size="2"),
    )


def _field(label, identity, name, *, default, kind="number", minimum=None, required=True):
    props = {"min": minimum, "max": "1000", "step": "1"} if kind == "number" else {}
    return rx.box(
        rx.el.label(t(label), html_for=identity, display="block", size="2", font_weight="550"),
        rx.input(
            id=identity,
            name=name,
            type=kind,
            input_mode="numeric" if kind == "number" else None,
            required=required,
            default_value=default,
            on_change=PlanningState.mark_creation_dirty,
            disabled=LOCKED,
            aria_invalid=PlanningState.creation_errors.get(identity, "") != "",
            aria_describedby=identity + "-error",
            width="100%",
            size="3",
            **props,
        ),
        field_error(identity),
        min_width="0",
    )


def _group_card(row):
    selected = PlanningState.selected_group == row["value"]
    return card(
        rx.flex(
            rx.box(
                rx.text(row["name"], size="2", color=MUTED),
                rx.heading(row["product"], as_="h3", size="4", margin_top="0.15rem"),
                rx.text(
                    row["quantity"],
                    " · ",
                    row["currency"],
                    " · ",
                    row["supplier_count"],
                    " ",
                    t("suppliers_word"),
                    size="2",
                    color=MUTED,
                    margin_top="0.25rem",
                ),
                min_width="0",
                flex="1",
            ),
            rx.cond(
                row["selectable"] == "",
                rx.badge(t("not_usable"), color_scheme="gray", variant="soft"),
                rx.text(row["date"], size="2", color=MUTED, white_space="nowrap"),
            ),
            justify="between",
            align="start",
            gap="1rem",
        ),
        rx.text(row["offers"], size="2", margin_top="0.75rem"),
        rx.cond(
            row["selectable"] == "",
            rx.text(row["issue"], size="2", color=MUTED, margin_top="0.5rem"),
            rx.button(
                rx.cond(
                    selected & PlanningState.odoo_ready,
                    t("terms_below"),
                    t("start_comparison"),
                ),
                id="start-" + row["value"],
                on_click=PlanningState.prepare_odoo_history(row["value"]),
                disabled=BUSY,
                background=rx.cond(selected & PlanningState.odoo_ready, "white", ACCENT),
                color=rx.cond(selected & PlanningState.odoo_ready, ACCENT, "white"),
                border=f"1px solid {ACCENT}",
                margin_top="1rem",
            ),
        ),
        border=rx.cond(
            selected & PlanningState.odoo_ready, f"2px solid {ACCENT}", f"1px solid {HAIRLINE}"
        ),
        aria_label=row["label"],
    )


def _groups():
    return rx.cond(
        PlanningState.is_loading & ~PlanningState.groups_loaded,
        loading_state("loading_rfqs"),
        rx.cond(
            PlanningState.groups_error != "",
            error_state(PlanningState.groups_error, retry=PlanningState.load_quotation_groups),
            rx.cond(
                PlanningState.quotation_groups.length() == 0,
                empty_state("empty_rfqs_title", "empty_rfqs_body"),
                rx.box(
                    rx.grid(
                        rx.foreach(PlanningState.quotation_groups, _group_card),
                        columns=rx.breakpoints(initial="1", md="2", xl="3"),
                        gap="1rem",
                    ),
                    rx.cond(
                        PlanningState.groups_truncated,
                        muted("rfqs_truncated", margin_top="0.75rem"),
                    ),
                ),
            ),
        ),
    )


def _history_table():
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[
                        rx.table.column_header_cell(t(key), white_space="nowrap")
                        for key in (
                            "col_supplier",
                            "kpi_on_time",
                            "kpi_lateness",
                            "kpi_fill",
                            "kpi_lines",
                        )
                    ]
                )
            ),
            rx.table.body(
                rx.foreach(
                    PlanningState.odoo_history_rows,
                    lambda r: rx.table.row(
                        rx.table.row_header_cell(r["supplier"]),
                        rx.table.cell(r["on_time"]),
                        rx.table.cell(r["lateness"]),
                        rx.table.cell(r["fill"]),
                        rx.table.cell(r["lines"]),
                    ),
                )
            ),
            variant="surface",
            size="1",
        ),
        overflow_x="auto",
        role="region",
        aria_label=t("history_title"),
        tab_index=0,
    )


def _supplier_terms(row):
    return card(
        rx.text(row["name"], font_weight="650"),
        rx.text(t("offer_price"), ": ", row["price"], size="2", color=MUTED),
        rx.grid(
            _field(
                "capacity_label",
                row["supplier"] + "_capacity",
                row["supplier"] + "_capacity",
                default=row["capacity"],
                minimum="0",
            ),
            _field(
                "moq_label",
                row["supplier"] + "_moq",
                row["supplier"] + "_moq",
                default=row["moq"],
                minimum="1",
                required=False,
            ),
            *[
                rx.el.fieldset(
                    rx.el.legend(
                        t(f"{name}_range_label"), font_size="14px", font_weight="650", padding="0"
                    ),
                    rx.grid(
                        *[
                            _field(
                                f"range_{end}",
                                row["supplier"] + f"_{name}_{end}",
                                row["supplier"] + f"_{name}_{end}",
                                default=row[f"{name}_{end}"],
                                minimum="1",
                            )
                            for end in ("min", "max")
                        ],
                        columns="2",
                        gap="0.5rem",
                        margin_top="0.25rem",
                    ),
                    border="none",
                    margin="0",
                    padding="0",
                    min_width="0",
                )
                for name in ("price", "delivery")
            ],
            _field(
                "promised_label",
                row["supplier"] + "_promised_date",
                row["supplier"] + "_promised_date",
                default=row["promised_date"],
                kind="date",
            ),
            columns="1",
            gap="0.75rem",
            margin_top="0.75rem",
        ),
        padding="1rem",
    )


REVIEW_COLUMNS = (
    ("offer_price", "price"),
    ("capacity_label", "capacity"),
    ("moq_label", "moq"),
    ("price_range_label", "price_range"),
    ("delivery_range_label", "delivery_range"),
    ("promised_label", "promised"),
    ("availability", "available"),
)
NOWRAP = {"price", "promised"}


def _review_supplier_card(r):
    return rx.box(
        rx.text(r["name"], as_="p", font_weight="650"),
        rx.el.dl(
            *[
                item
                for key, field in REVIEW_COLUMNS
                for item in (
                    rx.el.dt(t(key), color=MUTED, font_size="14px"),
                    rx.el.dd(r[field], margin="0", font_size="14px"),
                )
            ],
            display="grid",
            grid_template_columns="minmax(0, 1fr) minmax(0, 1fr)",
            column_gap="0.75rem",
            row_gap="0.35rem",
            margin="0.5rem 0 0",
        ),
        border="1px solid var(--gray-a5)",
        border_radius="8px",
        padding="0.75rem",
    )


def _review():
    review = PlanningState.creation_review
    return rx.cond(
        review.get("kind", "") == "odoo",
        card(
            heading(
                "review_title",
                size="5",
                id="creation-review-heading",
                tab_index=-1,
            ),
            muted("review_body", margin_top="0.35rem"),
            rx.grid(
                *[
                    rx.box(
                        rx.text(t(label), size="2", color=MUTED), rx.text(value, font_weight="650")
                    )
                    for label, value in (
                        ("col_product", review.get("product", "")),
                        ("col_demand", review.get("quantity_display", "")),
                        ("col_required", review.get("required_display", "")),
                        ("currency", review.get("currency", "")),
                    )
                ],
                columns=rx.breakpoints(initial="2", md="4"),
                gap="1rem",
                margin_y="1rem",
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(t("col_supplier"), white_space="nowrap"),
                            *[
                                rx.table.column_header_cell(t(key), white_space="nowrap")
                                for key, _ in REVIEW_COLUMNS
                            ],
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            PlanningState.review_suppliers,
                            lambda r: rx.table.row(
                                rx.table.row_header_cell(r["name"]),
                                *[
                                    rx.table.cell(
                                        r[field],
                                        white_space="nowrap" if field in NOWRAP else "normal",
                                    )
                                    for _, field in REVIEW_COLUMNS
                                ],
                            ),
                        )
                    ),
                    variant="surface",
                    size="1",
                ),
                overflow_x="auto",
                role="region",
                aria_label=t("review_title"),
                tab_index=0,
                display=rx.breakpoints(initial="none", md="block"),
            ),
            # Narrow screens: one card per supplier, so no term hides behind a scroll.
            rx.box(
                rx.foreach(PlanningState.review_suppliers, _review_supplier_card),
                display=rx.breakpoints(initial="grid", md="none"),
                gap="0.75rem",
            ),
            rx.text(t("policy_label"), ": ", review.get("policy", ""), size="2", margin_top="1rem"),
            rx.callout(
                rx.cond(PlanningState.has_pending, t("review_pending"), t("review_note")),
                icon="info",
                size="1",
                margin_top="1rem",
            ),
            rx.flex(
                rx.button(
                    t("edit_terms"),
                    id="creation-edit-terms",
                    on_click=PlanningState.edit_creation_terms,
                    variant="outline",
                    disabled=BUSY,
                ),
                rx.button(
                    rx.cond(
                        PlanningState.is_loading,
                        rx.spinner(size="2"),
                        rx.icon("calculator", size=16),
                    ),
                    t("calculate_save"),
                    id="calculate-save",
                    on_click=PlanningState.save_reviewed_creation,
                    disabled=BUSY,
                    background=ACCENT,
                    color="white",
                ),
                gap="0.75rem",
                wrap="wrap",
                margin_top="1.25rem",
            ),
            border=f"2px solid {ACCENT}",
            margin_top="1.25rem",
        ),
    )


def _terms():
    return rx.cond(
        PlanningState.odoo_ready,
        rx.box(
            rx.flex(
                rx.box(
                    rx.text(PlanningState.selected_group_row["name"], size="2", color=MUTED),
                    heading(
                        "terms_title",
                        size="5",
                        id="creation-terms-heading",
                        tab_index=-1,
                    ),
                ),
                rx.text(PlanningState.odoo_details, size="1", color=MUTED),
                justify="between",
                align="end",
                gap="1rem",
                wrap="wrap",
            ),
            card(
                heading("history_title", size="3"),
                muted("history_note", margin_y="0.5rem"),
                _history_table(),
                margin_top="1rem",
            ),
            rx.form(
                card(
                    heading("demand_title", size="3"),
                    rx.grid(
                        _field(
                            "demand_label",
                            "odoo-quantity",
                            "odoo_quantity",
                            default=PlanningState.odoo_quantity,
                            minimum="1",
                        ),
                        _field(
                            "required_label",
                            "odoo-required-date",
                            "odoo_required_date",
                            default=PlanningState.odoo_required_date,
                            kind="date",
                        ),
                        columns=rx.breakpoints(initial="1", sm="2"),
                        gap="1rem",
                        margin_top="0.75rem",
                        max_width="32rem",
                    ),
                    margin_top="1rem",
                ),
                rx.box(
                    heading("supplier_terms_title", size="3"),
                    muted("supplier_terms_note", margin_y="0.5rem"),
                    rx.grid(
                        rx.foreach(PlanningState.odoo_offers, _supplier_terms),
                        columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                        gap="0.75rem",
                    ),
                    margin_top="1.25rem",
                ),
                rx.text(
                    t("policy_label"),
                    ": ",
                    PlanningState.odoo_policy,
                    size="2",
                    color=MUTED,
                    margin_top="1rem",
                ),
                rx.button(
                    t("review_terms"),
                    type="submit",
                    disabled=LOCKED
                    | (
                        PlanningState.odoo_history_mode
                        & (PlanningState.odoo_history_readiness != "ready")
                    ),
                    size="3",
                    margin_top="1rem",
                    background=ACCENT,
                    color="white",
                ),
                on_submit=PlanningState.review_odoo,
                no_validate=True,
                reset_on_submit=False,
            ),
            _review(),
            margin_top="2rem",
            padding_top="1.5rem",
            border_top=f"1px solid {HAIRLINE}",
        ),
    )


def rfqs_page() -> rx.Component:
    return workspace_shell(
        page_frame(
            rx.flex(
                rx.box(
                    rx.heading(t("rfqs_title"), as_="h1", size="7", color=INK),
                    muted("rfqs_subtitle", margin_top="0.35rem", max_width="62ch"),
                ),
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    t("refresh"),
                    id="load-quotation-groups",
                    on_click=PlanningState.load_quotation_groups,
                    disabled=BUSY,
                    variant="outline",
                    size="3",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="start", sm="center"),
                gap="1rem",
                margin_bottom="1.25rem",
            ),
            recovery(),
            rx.cond(
                (PlanningState.error_message != "")
                & (PlanningState.groups_error == "")
                & ~PlanningState.has_pending,
                rx.callout(
                    PlanningState.error_message,
                    color_scheme="red",
                    role="alert",
                    margin_bottom="1rem",
                ),
            ),
            rx.cond(
                PlanningState.is_loading & PlanningState.groups_loaded,
                rx.box(loading_state("waiting_api"), margin_bottom="0.5rem"),
            ),
            _groups(),
            _terms(),
        ),
        active="rfqs",
    )
