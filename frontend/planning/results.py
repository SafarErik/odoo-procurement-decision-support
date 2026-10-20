"""Plans tab: aligned comparison, cost–exposure chart and the selected allocation."""

import reflex as rx

from frontend.planning.charts import cost_exposure_chart
from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, INK, MUTED, SERIES_1
from frontend.ui import BUSY, card, heading, muted, t

SELECTED_BG = "#f1eff8"
DECIDED = PlanningState.details["final_outcome"] != ""


def _is_selected(plan):
    return PlanningState.selected_plan.get("label", "") == plan["label"]


def _selection_button(plan):
    return rx.button(
        rx.cond(
            _is_selected(plan),
            rx.cond(
                PlanningState.details["final_outcome"] == "Approved",
                t("approved_plan"),
                t("selected_for_review"),
            ),
            t("select_for_review"),
        ),
        aria_pressed=_is_selected(plan),
        on_click=PlanningState.choose_final_plan(plan["label"]),
        disabled=BUSY | DECIDED | (PlanningState.details["parent_id"] != "Base case"),
        variant=rx.cond(_is_selected(plan), "solid", "outline"),
        color_scheme="iris",
        size="2",
        width="100%",
        margin_top="0.5rem",
    )


def _cell(plan, *content, **props):
    return rx.table.cell(
        *content,
        background=rx.cond(_is_selected(plan), SELECTED_BG, "transparent"),
        vertical_align="top",
        **props,
    )


def _comparison_table():
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(t("col_metric"), min_width="8rem"),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: rx.table.column_header_cell(
                            rx.text(
                                plan["title"],
                                font_weight="650",
                                color=INK,
                                overflow_wrap="normal",
                                hyphens="auto",
                            ),
                            rx.cond(
                                plan["hint"] != "",
                                rx.text(plan["hint"], size="1", color=MUTED),
                            ),
                            min_width="7.5rem",
                            vertical_align="top",
                            background=rx.cond(_is_selected(plan), SELECTED_BG, "transparent"),
                        ),
                    ),
                ),
            ),
            rx.table.body(
                rx.table.row(
                    rx.table.row_header_cell(t("total_cost")),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: _cell(plan, rx.text(plan["cost"], font_weight="650")),
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell(t("premium")),
                    rx.foreach(
                        PlanningState.plans, lambda plan: _cell(plan, plan["premium_absolute"])
                    ),
                ),
                rx.foreach(
                    PlanningState.scenario_suppliers,
                    lambda supplier: rx.table.row(
                        rx.table.row_header_cell(supplier["name"]),
                        rx.foreach(
                            PlanningState.plans,
                            lambda plan: _cell(
                                plan,
                                rx.foreach(
                                    PlanningState.allocations,
                                    lambda row: rx.cond(
                                        (row["plan"] == plan["label"])
                                        & (row["supplier"] == supplier["supplier"]),
                                        rx.text(
                                            row["quantity_display"],
                                            color=rx.cond(row["quantity"] == "0", MUTED, INK),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell(t("demand_covered")),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: _cell(plan, PlanningState.details["quantity_display"]),
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell(t("risk_exposure")),
                    rx.foreach(
                        PlanningState.plans, lambda plan: _cell(plan, plan["exposure_display"])
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell(t("largest_share_label")),
                    rx.foreach(
                        PlanningState.plans, lambda plan: _cell(plan, plan["largest_share"])
                    ),
                ),
            ),
            variant="ghost",
            size="2",
            width="100%",
        ),
        role="region",
        aria_label=t("plan_comparison"),
        tab_index=0,
        overflow_x="auto",
        width="100%",
    )


def _allocation_bar(row):
    return rx.box(
        rx.flex(
            rx.text(row["name"], size="2", min_width="0"),
            rx.text(
                row["quantity_display"], " · ", row["share_display"], size="2", white_space="nowrap"
            ),
            justify="between",
            gap="0.75rem",
        ),
        rx.box(
            rx.box(
                width=row["share"] + "%",
                height="100%",
                background=SERIES_1,
                border_radius="4px",
            ),
            height="0.5rem",
            background="#e6ece8",
            border_radius="4px",
            margin_top="0.35rem",
            role="presentation",
        ),
        margin_bottom="0.85rem",
    )


def _plan_summary(plan):
    return rx.box(
        rx.flex(
            rx.heading(plan["title"], as_="h3", size="4"),
            rx.flex(
                rx.cond(plan["hint"] != "", rx.badge(plan["hint"], color_scheme="jade")),
                rx.cond(plan["balanced"] != "", rx.badge(plan["balanced"], color_scheme="iris")),
                gap="0.35rem",
                wrap="wrap",
            ),
            justify="between",
            wrap="wrap",
            gap="0.5rem",
        ),
        rx.cond(plan["budget"] != "", rx.text(plan["budget"], size="1", color=MUTED)),
        rx.text(plan["cost"], size="7", font_weight="650", margin_top="0.75rem", color=INK),
        rx.text(plan["premium_display"], size="2", color=MUTED, margin_top="0.25rem"),
        rx.flex(
            rx.text(t("risk_exposure"), size="2", color=MUTED),
            rx.text(plan["exposure_display"], font_weight="650", size="2"),
            justify="between",
            gap="0.75rem",
            margin_top="1rem",
        ),
        rx.flex(
            rx.text(t("largest_share_label"), size="2", color=MUTED),
            rx.text(plan["largest_share"], font_weight="650", size="2"),
            justify="between",
            gap="0.75rem",
            margin_top="0.35rem",
        ),
        rx.text(plan["allocation_summary"], size="2", margin_top="0.75rem"),
        _selection_button(plan),
        padding="1.25rem",
        min_width="0",
        border=f"1px solid {HAIRLINE}",
        border_color=rx.cond(_is_selected(plan), ACCENT, HAIRLINE),
        background=rx.cond(_is_selected(plan), SELECTED_BG, "white"),
        border_radius="12px",
    )


def _selected_panel():
    plan = PlanningState.focus_plan
    return card(
        rx.text(
            rx.cond(
                PlanningState.selected_plan.get("label", "") != "",
                rx.cond(DECIDED, t("approved_plan"), t("selected_allocation")),
                t("suggested_look"),
            ),
            size="2",
            color=MUTED,
        ),
        rx.heading(plan.get("title", ""), as_="h2", size="4", margin_top="0.15rem"),
        rx.text(plan.get("cost", ""), size="7", font_weight="650", color=INK),
        rx.text(plan.get("premium_display", ""), size="2", color=MUTED, margin_bottom="1rem"),
        rx.flex(
            rx.text(t("chart_exposure"), size="2", color=MUTED),
            rx.text(plan.get("exposure_display", ""), size="2", font_weight="650"),
            justify="between",
            gap="0.5rem",
            margin_bottom="1rem",
        ),
        rx.foreach(PlanningState.focus_allocation, _allocation_bar),
        rx.flex(
            rx.text(t("total"), size="2", font_weight="650"),
            rx.text(PlanningState.details["quantity_display"], size="2", font_weight="650"),
            justify="between",
            border_top=f"1px solid {HAIRLINE}",
            padding_top="0.6rem",
        ),
        rx.cond(
            (PlanningState.details["parent_id"] == "Base case") & ~DECIDED,
            rx.button(
                t("review_decision"),
                on_click=PlanningState.change_view("decision"),
                disabled=BUSY | (PlanningState.final_choice == ""),
                background=ACCENT,
                color="white",
                width="100%",
                margin_top="1.25rem",
            ),
        ),
        rx.cond(
            (PlanningState.details["parent_id"] == "Base case") & ~DECIDED,
            muted("selection_not_approval", margin_top="0.5rem", text_align="center"),
        ),
        id="selection-review",
        class_name="decision-summary",
        role="status",
        aria_live="polite",
    )


def _constraint_notes():
    return rx.el.details(
        rx.el.summary(t("what_shapes")),
        rx.cond(
            PlanningState.details["buyer_diagnostics"] != "",
            rx.text(PlanningState.details["buyer_diagnostics"], white_space="pre-line", size="2"),
        ),
        rx.foreach(
            PlanningState.plans,
            lambda plan: rx.box(
                rx.text(plan["title"], font_weight="650", size="2", margin_top="0.75rem"),
                rx.text(
                    rx.cond(plan["buyer_notes"] != "", plan["buyer_notes"], t("no_binding")),
                    white_space="pre-line",
                    size="2",
                    color=MUTED,
                ),
            ),
        ),
        muted(PlanningState.details["policy"], margin_top="0.75rem"),
    )


def plans_view() -> rx.Component:
    return rx.cond(
        PlanningState.plans.length() > 0,
        rx.grid(
            rx.flex(
                rx.box(
                    heading("plan_comparison", size="5"),
                    muted("plans_intro", margin_y="0.5rem"),
                    rx.grid(
                        rx.foreach(PlanningState.plans, _plan_summary),
                        columns=rx.breakpoints(initial="1", sm="2"),
                        gap="0.75rem",
                        margin_top="1rem",
                    ),
                ),
                card(
                    heading("allocation_details", size="4"),
                    _comparison_table(),
                    rx.cond(
                        PlanningState.details["alternative_notice"] != "",
                        muted(PlanningState.details["alternative_notice"], margin_top="0.75rem"),
                    ),
                    rx.cond(
                        PlanningState.details["status_code"] != "optimal",
                        rx.callout(t("incomplete_body"), color_scheme="amber", margin_top="1rem"),
                    ),
                ),
                card(
                    heading("chart_tradeoff", size="4"),
                    muted("chart_tradeoff_note", margin_y="0.35rem"),
                    cost_exposure_chart(),
                    rx.el.details(
                        rx.el.summary(t("chart_exposure"), font_weight="550"),
                        muted("exposure_explained", margin_top="0.5rem"),
                    ),
                    rx.el.details(
                        rx.el.summary(t("largest_share_label"), font_weight="550"),
                        muted("balanced_explained", margin_top="0.5rem"),
                    ),
                ),
                card(_constraint_notes()),
                direction="column",
                gap="1rem",
                min_width="0",
            ),
            rx.box(
                _selected_panel(),
                position=rx.breakpoints(initial="static", lg="sticky"),
                top="1rem",
            ),
            columns=rx.breakpoints(initial="1", lg="minmax(0,1fr) 20rem"),
            gap="1rem",
            align_items="start",
        ),
        rx.callout(
            rx.cond(
                PlanningState.details["status_code"] == "infeasible",
                t("infeasible_body"),
                t("no_result_body"),
            ),
            color_scheme="amber",
        ),
    )
