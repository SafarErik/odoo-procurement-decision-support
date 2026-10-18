"""Cases: saved comparisons with filters, a context panel and scenarios on demand."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, MUTED
from frontend.ui import card, decision_badge, empty_state, error_state, loading_state, muted, t
from frontend.workspace import page_frame, workspace_shell

_SELECT = {
    "padding": "0.55rem 0.65rem",
    "border": f"1px solid {HAIRLINE}",
    "border_radius": "8px",
    "background": "white",
    "width": "100%",
    "min_height": "2.75rem",
}
BUSY = PlanningState.has_pending | PlanningState.is_loading


def _origin_badge(row):
    return rx.cond(
        row["badge"] != "", rx.badge(row["badge"], color_scheme="gray", variant="soft"), ""
    )


def _filters():
    disabled = ~PlanningState.library_loaded | PlanningState.library_loading
    return rx.form(
        rx.grid(
            rx.box(
                rx.el.label(t("search_label"), html_for="library-search", class_name="sr-only"),
                rx.input(
                    rx.input.slot(rx.icon("search", size=16)),
                    id="library-search",
                    name="q",
                    max_length=80,
                    default_value=PlanningState.library_search,
                    key=PlanningState.library_search,
                    placeholder=t("search_placeholder"),
                    disabled=disabled,
                    size="3",
                    width="100%",
                ),
                min_width="0",
            ),
            rx.el.select(
                *[
                    rx.el.option(t(label), value=value)
                    for value, label in (
                        ("all", "filter_all_decisions"),
                        ("draft", "decision_draft"),
                        ("approved", "decision_approved"),
                        ("no_award", "decision_no_award"),
                    )
                ],
                id="library-status",
                aria_label=t("filter_status"),
                value=PlanningState.library_status,
                on_change=lambda v: PlanningState.set_library_filter("status", v),
                disabled=disabled,
                **_SELECT,
            ),
            rx.el.select(
                *[
                    rx.el.option(t(label), value=value)
                    for value, label in (
                        ("all", "filter_all_sources"),
                        ("odoo", "filter_odoo"),
                        ("demo", "badge_synthetic"),
                    )
                ],
                id="library-origin",
                aria_label=t("filter_origin"),
                value=PlanningState.library_origin,
                on_change=lambda v: PlanningState.set_library_filter("origin", v),
                disabled=disabled,
                **_SELECT,
            ),
            rx.button(
                rx.icon("refresh-cw", size=16),
                t("refresh"),
                type="submit",
                disabled=disabled,
                variant="outline",
                size="3",
            ),
            columns=rx.breakpoints(initial="1", sm="2", md="minmax(0,2fr) 1fr 1fr auto"),
            gap="0.75rem",
            align_items="center",
        ),
        on_submit=PlanningState.refresh_library,
        reset_on_submit=False,
    )


def _actions(row):
    return rx.flex(
        rx.button(
            t("open_case"),
            on_click=PlanningState.open_saved_case(row["case_id"], "overview"),
            disabled=BUSY,
            size="2",
            variant="outline",
            color_scheme="iris",
        ),
        rx.button(
            rx.cond(
                PlanningState.expanded_case == row["case_id"],
                t("hide_scenarios"),
                t("show_scenarios"),
            ),
            on_click=PlanningState.expand_scenarios(row["case_id"], False),
            disabled=PlanningState.children_loading | PlanningState.library_loading,
            aria_expanded=PlanningState.expanded_case == row["case_id"],
            size="2",
            variant="ghost",
        ),
        gap="0.5rem",
        wrap="wrap",
        on_click=rx.stop_propagation,
    )


def _child(row):
    return rx.flex(
        rx.box(
            rx.text(row["scenario"], font_weight="650", size="2"),
            rx.text(row["quantity"], " · ", row["outcome"], size="2", color=MUTED),
            min_width="0",
        ),
        rx.button(
            t("open_scenario"),
            on_click=PlanningState.open_saved_case(row["case_id"], "scenarios"),
            disabled=BUSY,
            size="1",
            variant="outline",
        ),
        justify="between",
        align="center",
        gap="1rem",
        padding="0.6rem 0",
        border_top=f"1px solid {HAIRLINE}",
    )


def _children(row):
    return rx.cond(
        PlanningState.expanded_case == row["case_id"],
        rx.box(
            rx.text(t("saved_scenarios"), font_weight="650", size="2"),
            rx.cond(
                PlanningState.children_loading,
                rx.text(t("loading"), role="status", size="2", color=MUTED),
                rx.cond(
                    PlanningState.children_error != "",
                    rx.text(PlanningState.children_error, role="alert", size="2"),
                    rx.cond(
                        PlanningState.library_children.length() == 0,
                        muted("no_scenarios"),
                        rx.foreach(PlanningState.library_children, _child),
                    ),
                ),
            ),
            rx.cond(
                PlanningState.children_cursor != "",
                rx.button(
                    t("more_scenarios"),
                    on_click=PlanningState.expand_scenarios(row["case_id"], True),
                    disabled=PlanningState.children_loading,
                    size="1",
                    variant="ghost",
                ),
            ),
            background="#f6f9f7",
            padding="0.75rem 1rem",
            border_radius="8px",
            margin_top="0.5rem",
        ),
    )


def _table_row(row):
    selected = PlanningState.library_selection["case_id"] == row["case_id"]
    return rx.fragment(
        rx.table.row(
            rx.table.row_header_cell(
                rx.text(row["product"], font_weight="650"),
                rx.flex(_origin_badge(row), gap="0.35rem", margin_top="0.25rem"),
            ),
            rx.table.cell(row["quantity"], white_space="nowrap"),
            rx.table.cell(row["required"], white_space="nowrap"),
            rx.table.cell(row["minimum_cost"], white_space="nowrap", text_align="right"),
            rx.table.cell(decision_badge(row["status"])),
            rx.table.cell(_actions(row)),
            on_click=PlanningState.select_library_case(row["case_id"]),
            class_name="case-row",
            data_selected=selected,
            vertical_align="middle",
        ),
        rx.cond(
            PlanningState.expanded_case == row["case_id"],
            rx.table.row(rx.table.cell(_children(row), col_span=6)),
        ),
    )


def _desktop_table():
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(t("col_product")),
                    rx.table.column_header_cell(t("col_demand")),
                    rx.table.column_header_cell(t("col_required")),
                    rx.table.column_header_cell(t("col_min_cost"), text_align="right"),
                    rx.table.column_header_cell(t("col_decision")),
                    rx.table.column_header_cell(t("col_actions")),
                )
            ),
            rx.table.body(rx.foreach(PlanningState.library_rows, _table_row)),
            variant="ghost",
            width="100%",
        ),
        display=rx.breakpoints(initial="none", md="block"),
        overflow_x="auto",
    )


def _mobile_card(row):
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["product"], font_weight="650"),
                rx.text(row["quantity"], " · ", row["required"], size="2", color=MUTED),
                min_width="0",
            ),
            decision_badge(row["status"]),
            justify="between",
            align="start",
            gap="0.75rem",
        ),
        rx.flex(
            _origin_badge(row),
            rx.text(row["minimum_cost"], size="2", font_weight="650"),
            justify="between",
            align="center",
            margin_y="0.5rem",
        ),
        _actions(row),
        _children(row),
        padding="1rem 0",
        border_top=f"1px solid {HAIRLINE}",
    )


def _context_panel():
    row = PlanningState.library_selection
    return card(
        rx.text(t("selected_case"), size="2", color=MUTED),
        rx.heading(row["product"], as_="h2", size="5", margin_top="0.25rem"),
        rx.text(row["quantity"], size="2", color=MUTED),
        rx.grid(
            rx.text(t("col_required"), size="2", color=MUTED),
            rx.text(row["required"], size="2"),
            rx.text(t("col_min_cost"), size="2", color=MUTED),
            rx.text(row["minimum_cost"], size="2"),
            rx.text(t("col_outcome"), size="2", color=MUTED),
            rx.text(row["outcome"], size="2"),
            rx.text(t("col_saved"), size="2", color=MUTED),
            rx.text(row["saved"], size="2"),
            columns="auto 1fr",
            gap="0.5rem 1rem",
            margin_y="1rem",
        ),
        decision_badge(row["status"]),
        rx.flex(
            rx.button(
                t("open_case"),
                on_click=PlanningState.open_saved_case(row["case_id"], "overview"),
                disabled=BUSY,
                background=ACCENT,
                color="white",
                width="100%",
            ),
            rx.cond(
                row["status"] == "approved",
                rx.button(
                    rx.icon("file-text", size=16),
                    t("view_pdf"),
                    on_click=PlanningState.open_saved_case(row["case_id"], "decision"),
                    disabled=BUSY,
                    variant="outline",
                    width="100%",
                ),
            ),
            direction="column",
            gap="0.5rem",
            margin_top="1.25rem",
        ),
        rx.callout(t("cases_note"), icon="info", size="1", margin_top="1.25rem"),
        position="sticky",
        top="1.5rem",
    )


def _list():
    return rx.cond(
        ~PlanningState.library_loaded | PlanningState.library_loading,
        loading_state("loading_cases"),
        rx.cond(
            PlanningState.library_error != "",
            error_state(PlanningState.library_error, retry=PlanningState.refresh_library),
            rx.cond(
                PlanningState.library_rows.length() == 0,
                rx.cond(
                    (PlanningState.library_search != "")
                    | (PlanningState.library_status != "all")
                    | (PlanningState.library_origin != "all"),
                    empty_state("empty_filtered_title", "empty_filtered_body"),
                    empty_state(
                        "empty_cases_title",
                        "empty_cases_body",
                        rx.button(
                            t("new_comparison"),
                            on_click=PlanningState.new_comparison,
                            margin_top="1rem",
                            background=ACCENT,
                            color="white",
                        ),
                    ),
                ),
                rx.grid(
                    card(
                        _desktop_table(),
                        rx.box(
                            rx.foreach(PlanningState.library_rows, _mobile_card),
                            display=rx.breakpoints(initial="block", md="none"),
                        ),
                        rx.flex(
                            rx.text(
                                PlanningState.library_rows.length(),
                                " ",
                                t("cases_on_page"),
                                size="2",
                                color=MUTED,
                            ),
                            rx.cond(
                                PlanningState.library_cursor != "",
                                rx.button(
                                    t("next_page"),
                                    rx.icon("chevron-right", size=16),
                                    on_click=PlanningState.next_library_page,
                                    disabled=PlanningState.library_loading,
                                    variant="outline",
                                    size="2",
                                ),
                            ),
                            justify="between",
                            align="center",
                            margin_top="1rem",
                        ),
                        padding=["0.75rem 1rem", "1rem 1.25rem"],
                    ),
                    rx.box(_context_panel(), display=rx.breakpoints(initial="none", lg="block")),
                    columns=rx.breakpoints(initial="1", lg="minmax(0,1fr) 20rem"),
                    gap="1.25rem",
                    align_items="start",
                ),
            ),
        ),
    )


def library_page():
    return workspace_shell(
        page_frame(
            rx.flex(
                rx.box(
                    rx.heading(
                        t("cases_title"), as_="h1", size="7", id="library-heading", tab_index=-1
                    ),
                    muted("cases_subtitle", margin_top="0.35rem"),
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    t("new_comparison"),
                    id="new-comparison",
                    on_click=PlanningState.new_comparison,
                    disabled=BUSY,
                    background=ACCENT,
                    color="white",
                    size="3",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="start", sm="center"),
                gap="1rem",
                margin_bottom="1.25rem",
            ),
            card(_filters(), margin_bottom="1.25rem"),
            _list(),
        ),
        active="cases",
    )
