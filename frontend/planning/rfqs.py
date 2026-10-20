"""Guided quotation selection, attributed buyer input, review and explicit case creation."""

import reflex as rx

from frontend.components.workflow import (
    creation_steps,
    field_hint,
    source_badge,
    source_explanation,
)
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


def _field(label, identity, name, *, hint, kind="number", minimum=None, required=True):
    props = {"min": minimum, "max": "1000", "step": "1"} if kind == "number" else {}
    suggested = PlanningState.creation_values.get(
        name, ""
    ) == PlanningState.creation_suggestions.get(name, "")
    return rx.box(
        rx.flex(
            rx.el.label(t(label), html_for=identity, font_weight="600", font_size="14px"),
            rx.cond(suggested, source_badge("suggested"), source_badge("buyer")),
            gap="0.5rem",
            wrap="wrap",
            align="center",
            margin_bottom="0.4rem",
        ),
        rx.input(
            id=identity,
            name=name,
            type=kind,
            input_mode="numeric" if kind == "number" else None,
            required=required,
            value=PlanningState.creation_values.get(name, ""),
            on_change=lambda value: PlanningState.update_creation_field(name, value),
            disabled=LOCKED,
            aria_invalid=PlanningState.creation_errors.get(identity, "") != "",
            aria_describedby=identity + "-hint " + identity + "-error",
            width="100%",
            size="3",
            **props,
        ),
        field_hint(hint, identity),
        field_error(identity),
        display="flex",
        flex_direction="column",
        gap="0.35rem",
        min_width="0",
    )


def _group_card(row):
    selected = PlanningState.selected_group == row["value"]
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["name"], size="2", color=MUTED),
                rx.heading(row["product"], as_="h3", size="4", margin_top="0.25rem"),
                rx.text(
                    row["supplier_count"],
                    " ",
                    t("suppliers_word"),
                    " · ",
                    row["currency"],
                    size="2",
                    color=MUTED,
                    margin_top="0.4rem",
                ),
                min_width="0",
                flex="1",
            ),
            rx.cond(selected, rx.icon("circle-check", size=20, color=ACCENT)),
            justify="between",
            gap="0.5rem",
            align="start",
        ),
        rx.text(row["date"], size="1", color=MUTED, margin_top="0.4rem"),
        rx.cond(
            row["selectable"] == "",
            rx.text(row["issue"], size="2", color=MUTED, margin_top="0.5rem"),
            rx.button(
                t("choose_group"),
                rx.icon("arrow-right", size=15),
                id="choose-" + row["value"],
                on_click=PlanningState.select_quotation_group(row["value"]),
                disabled=BUSY,
                variant="ghost",
                margin_top="0.65rem",
                aria_pressed=selected,
            ),
        ),
        padding="1.1rem",
        background=rx.cond(selected, "#f1eff8", "white"),
        border=f"1px solid {HAIRLINE}",
        border_color=rx.cond(selected, ACCENT, HAIRLINE),
        border_radius="12px",
        aria_label=row["label"],
    )


def _quotation(row):
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["supplier"], font_weight="650", size="2"),
                rx.text(
                    t("quotation_reference"),
                    ": ",
                    row["reference"],
                    size="1",
                    color=MUTED,
                    margin_top="0.25rem",
                ),
                min_width="0",
                flex="1",
            ),
            rx.text(row["price"], font_weight="650", white_space="nowrap"),
            justify="between",
            gap="0.75rem",
            wrap="wrap",
        ),
        rx.flex(
            rx.text(t("quotation_quantity"), ": ", row["quantity"], size="2", color=MUTED),
            rx.text(t("quotation_state"), ": ", row["status"], size="1", color=MUTED),
            justify="between",
            gap="0.5rem",
            wrap="wrap",
            margin_top="0.45rem",
        ),
        padding_y="0.85rem",
        border_bottom=f"1px solid {HAIRLINE}",
    )


def _group_details():
    row = PlanningState.selected_group_row
    return rx.cond(
        row.get("value", "") != "",
        card(
            rx.flex(
                heading(
                    "quotation_details", size="5", id="quotation-details-heading", tab_index=-1
                ),
                source_badge("odoo"),
                justify="between",
                wrap="wrap",
                gap="0.5rem",
            ),
            rx.text(row.get("name", ""), size="2", color=MUTED, margin_top="0.5rem"),
            rx.text(row.get("product", ""), size="3", font_weight="600", margin_top="0.25rem"),
            rx.button(
                t("start_comparison"),
                rx.icon("arrow-right", size=17),
                id="start-" + row.get("value", ""),
                on_click=PlanningState.prepare_odoo_history(row.get("value", "")),
                disabled=BUSY,
                background=ACCENT,
                color="white",
                size="3",
                margin_top="1rem",
            ),
            muted("quotation_quantity_note", margin_top="1rem"),
            rx.foreach(PlanningState.selected_quotations, _quotation),
            position=rx.breakpoints(initial="static", lg="sticky"),
            top="1.5rem",
        ),
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
                        rx.flex(
                            rx.foreach(PlanningState.quotation_groups, _group_card),
                            direction="column",
                            gap="0.75rem",
                            min_width="0",
                        ),
                        _group_details(),
                        columns=rx.breakpoints(initial="1", lg="minmax(0, 0.8fr) minmax(0, 1.2fr)"),
                        gap="1.5rem",
                        align_items="start",
                    ),
                    rx.cond(
                        PlanningState.groups_truncated,
                        muted("rfqs_truncated", margin_top="0.75rem"),
                    ),
                ),
            ),
        ),
    )


def _supplier_terms(row):
    supplier = row["supplier"]
    expanded = PlanningState.expanded_suppliers.contains(supplier)
    return rx.box(
        rx.button(
            rx.box(
                rx.text(row["name"], font_weight="650", text_align="left"),
                rx.text(
                    t("offer_price"),
                    ": ",
                    row["price"],
                    " · ",
                    t("capacity_label"),
                    ": ",
                    PlanningState.creation_values.get(supplier + "_capacity", ""),
                    size="2",
                    color=MUTED,
                    text_align="left",
                ),
                min_width="0",
                flex="1",
            ),
            rx.icon(rx.cond(expanded, "chevron-up", "chevron-down"), size=18),
            on_click=PlanningState.toggle_supplier_terms(supplier),
            aria_expanded=expanded,
            aria_controls="terms-" + supplier,
            type="button",
            variant="ghost",
            width="100%",
            margin="0",
            box_sizing="border-box",
            padding="1rem",
            height="auto",
            color=INK,
        ),
        rx.box(
            rx.grid(
                _field(
                    "capacity_label",
                    supplier + "_capacity",
                    supplier + "_capacity",
                    hint="capacity_help",
                    minimum="0",
                ),
                _field(
                    "moq_label",
                    supplier + "_moq",
                    supplier + "_moq",
                    hint="moq_help",
                    minimum="1",
                    required=False,
                ),
                _field(
                    "promised_label",
                    supplier + "_promised_date",
                    supplier + "_promised_date",
                    hint="promised_help",
                    kind="date",
                ),
                columns=rx.breakpoints(initial="1", md="3"),
                gap="1rem",
            ),
            rx.grid(
                *[
                    rx.el.fieldset(
                        rx.el.legend(t(f"{name}_range_label"), font_weight="600", font_size="14px"),
                        rx.grid(
                            *[
                                _field(
                                    f"range_{end}",
                                    supplier + f"_{name}_{end}",
                                    supplier + f"_{name}_{end}",
                                    hint="range_help",
                                    minimum="1",
                                )
                                for end in ("min", "max")
                            ],
                            columns="2",
                            gap="0.75rem",
                            margin_top="0.5rem",
                        ),
                        border="none",
                        padding="0",
                        margin="0",
                        min_width="0",
                    )
                    for name in ("price", "delivery")
                ],
                columns=rx.breakpoints(initial="1", lg="2"),
                gap="1.5rem",
                margin_top="1.25rem",
            ),
            id="terms-" + supplier,
            display=rx.cond(expanded, "block", "none"),
            padding="0.5rem 1rem 1.25rem",
        ),
        border=f"1px solid {HAIRLINE}",
        border_radius="12px",
        background="white",
        min_width="0",
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
            muted("review_sources", margin_top="0.5rem"),
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
            rx.el.details(
                rx.el.summary(t("suggested_terms"), font_weight="600"),
                rx.text(
                    t("demand_title"),
                    ": ",
                    review.get("suggested_requirements", ""),
                    size="2",
                    margin_top="0.5rem",
                ),
                rx.foreach(
                    PlanningState.review_suppliers,
                    lambda row: rx.text(
                        row["name"], ": ", row["suggested"], size="2", margin_top="0.35rem"
                    ),
                ),
                margin_top="1rem",
                open=True,
            ),
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
                    rx.text(t("selected_group"), size="1", color=MUTED),
                    rx.text(
                        PlanningState.selected_group_row.get("product", ""),
                        font_weight="650",
                        size="3",
                    ),
                    rx.text(PlanningState.odoo_details, size="1", color=MUTED),
                    rx.cond(
                        (PlanningState.creation_origin != "")
                        & (PlanningState.creation_origin != "observed"),
                        rx.badge(t("badge_generated"), color_scheme="amber", margin_top="0.4rem"),
                    ),
                ),
                rx.button(
                    t("change_group"),
                    on_click=PlanningState.go_creation_step(0),
                    disabled=BUSY,
                    variant="ghost",
                ),
                justify="between",
                wrap="wrap",
                align="center",
                gap="0.75rem",
                padding_y="1rem",
                border_bottom=f"1px solid {HAIRLINE}",
                margin_bottom="1.5rem",
            ),
            rx.heading(
                rx.match(
                    PlanningState.creation_step,
                    (1, t("demand_title")),
                    (2, t("supplier_terms_title")),
                    t("review_title"),
                ),
                as_="h2",
                size="6",
                id="creation-step-heading",
                tab_index=-1,
                margin_bottom="0.75rem",
                display=rx.cond(PlanningState.creation_step == 3, "none", "block"),
            ),
            rx.form(
                rx.box(
                    muted("demand_intro", margin_bottom="1.5rem"),
                    rx.grid(
                        _field(
                            "demand_label",
                            "odoo-quantity",
                            "odoo_quantity",
                            hint="demand_help",
                            minimum="1",
                        ),
                        _field(
                            "required_label",
                            "odoo-required-date",
                            "odoo_required_date",
                            hint="date_help",
                            kind="date",
                        ),
                        columns=rx.breakpoints(initial="1", md="2"),
                        gap="1.5rem",
                    ),
                    rx.button(
                        t("continue_terms"),
                        rx.icon("arrow-right", size=17),
                        type="submit",
                        background=ACCENT,
                        color="white",
                        size="3",
                        disabled=LOCKED,
                        margin_top="1.5rem",
                    ),
                    display=rx.cond(PlanningState.creation_step == 1, "block", "none"),
                    max_width="54rem",
                ),
                rx.box(
                    muted("terms_guidance", margin_bottom="1rem"),
                    rx.flex(
                        rx.foreach(PlanningState.odoo_offers, _supplier_terms),
                        direction="column",
                        gap="0.75rem",
                    ),
                    rx.el.details(
                        rx.el.summary(t("show_history"), font_weight="600"),
                        muted("history_note", margin_y="0.5rem"),
                        _history_table(),
                        margin_top="1rem",
                    ),
                    rx.box(
                        rx.text(
                            t("policy_label"),
                            ": ",
                            PlanningState.odoo_policy,
                            size="2",
                            font_weight="600",
                        ),
                        muted("policy_explanation", margin_top="0.4rem"),
                        padding="1rem",
                        background="#e7eeea",
                        border_radius="12px",
                        margin_top="1rem",
                    ),
                    rx.flex(
                        rx.button(
                            t("back_demand"),
                            on_click=PlanningState.go_creation_step(1),
                            type="button",
                            variant="outline",
                            disabled=BUSY,
                        ),
                        rx.button(
                            t("review_terms"),
                            rx.icon("arrow-right", size=17),
                            type="submit",
                            background=ACCENT,
                            color="white",
                            disabled=LOCKED | (PlanningState.odoo_history_readiness != "ready"),
                        ),
                        gap="0.75rem",
                        wrap="wrap",
                        margin_top="1.25rem",
                    ),
                    display=rx.cond(PlanningState.creation_step == 2, "block", "none"),
                ),
                on_submit=PlanningState.advance_creation,
                no_validate=True,
                reset_on_submit=False,
            ),
            _review(),
            muted("draft_session_note", margin_top="1.25rem"),
        ),
    )


def rfqs_page() -> rx.Component:
    return workspace_shell(
        page_frame(
            rx.flex(
                rx.box(
                    rx.heading(
                        rx.cond(
                            PlanningState.creation_step == 0,
                            t("rfqs_title"),
                            t("prepare_title"),
                        ),
                        as_="h1",
                        size="7",
                        color=INK,
                    ),
                    rx.text(
                        rx.cond(
                            PlanningState.creation_step == 0,
                            t("rfqs_subtitle"),
                            t("prepare_subtitle"),
                        ),
                        size="2",
                        color=MUTED,
                        margin_top="0.5rem",
                    ),
                ),
                rx.cond(
                    PlanningState.creation_step == 0,
                    rx.button(
                        rx.icon("refresh-cw", size=16),
                        t("refresh"),
                        id="load-quotation-groups",
                        on_click=PlanningState.load_quotation_groups,
                        disabled=BUSY | PlanningState.creation_dirty,
                        variant="outline",
                    ),
                ),
                justify="between",
                align="center",
                gap="1rem",
                wrap="wrap",
            ),
            creation_steps(),
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
                loading_state("waiting_api"),
            ),
            rx.box(
                source_explanation(),
                rx.flex(
                    rx.text(
                        t("groups_updated"),
                        " ",
                        PlanningState.groups_retrieved_display,
                        size="1",
                        color=MUTED,
                    ),
                    rx.text(
                        t("group_company"), " ", PlanningState.groups_company, size="1", color=MUTED
                    ),
                    gap="1rem",
                    wrap="wrap",
                    margin_bottom="1rem",
                ),
                _groups(),
                display=rx.cond(PlanningState.creation_step == 0, "block", "none"),
            ),
            rx.box(_terms(), display=rx.cond(PlanningState.creation_step > 0, "block", "none")),
        ),
        active="rfqs",
    )
