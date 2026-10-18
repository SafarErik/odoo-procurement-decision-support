"""Overview tab: headline numbers, plan choice and the numbered next step."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, INK, MUTED
from frontend.ui import BUSY, card, heading, kpi, muted, t

BASE = PlanningState.details["parent_id"] == "Base case"
DECIDED = PlanningState.details["final_outcome"] != ""


def _plan_option(plan):
    chosen = PlanningState.selected_plan.get("label", "") == plan["label"]
    return rx.el.button(
        rx.flex(
            rx.box(
                width="1.1rem",
                height="1.1rem",
                border_radius="50%",
                border=rx.cond(chosen, f"5px solid {ACCENT}", "2px solid #9fb3ab"),
                flex_shrink="0",
            ),
            rx.box(
                rx.text(plan["title"], font_weight="650", color=INK),
                rx.cond(
                    plan["hint"] != "",
                    rx.text(plan["hint"], size="1", color=MUTED),
                ),
                flex="1",
                text_align="left",
                min_width="0",
            ),
            rx.box(
                rx.text(plan["cost"], font_weight="650", color=INK, white_space="nowrap"),
                rx.cond(
                    plan["index"] != "0",
                    rx.text(plan["premium_absolute"], size="1", color=MUTED, white_space="nowrap"),
                ),
                text_align="right",
            ),
            align="center",
            gap="0.85rem",
            width="100%",
        ),
        role="radio",
        aria_checked=chosen,
        on_click=PlanningState.choose_final_plan(plan["label"]),
        disabled=BUSY | DECIDED | ~BASE,
        width="100%",
        padding="0.85rem 1rem",
        border=rx.cond(chosen, f"2px solid {ACCENT}", f"1px solid {HAIRLINE}"),
        border_radius="8px",
        background=rx.cond(chosen, "#f1eff8", "white"),
        cursor="pointer",
        font="inherit",
        _disabled={"cursor": "default"},
    )


def _step(number: int, title: str, body: str):
    done = PlanningState.next_step > number
    current = PlanningState.next_step == number
    return rx.flex(
        rx.box(
            rx.cond(done, rx.icon("check", size=14), str(number)),
            width="1.75rem",
            height="1.75rem",
            border_radius="50%",
            display="flex",
            align_items="center",
            justify_content="center",
            font_size="0.85rem",
            font_weight="650",
            flex_shrink="0",
            background=rx.cond(done | current, ACCENT, "white"),
            color=rx.cond(done | current, "white", MUTED),
            border=rx.cond(done | current, "none", f"1px solid {HAIRLINE}"),
        ),
        rx.box(
            rx.text(t(title), font_weight="650", color=rx.cond(current | done, INK, MUTED)),
            rx.text(t(body), size="2", color=MUTED),
        ),
        gap="0.85rem",
        align="start",
        aria_current=rx.cond(current, "step", "false"),
    )


def _next_step():
    return card(
        heading("next_step", size="4"),
        rx.flex(
            _step(1, "step_saved", "step_saved_body"),
            _step(2, "step_choose", "step_choose_body"),
            _step(3, "step_decide", "step_decide_body"),
            direction="column",
            gap="1.1rem",
            margin_top="1rem",
        ),
        rx.cond(
            DECIDED,
            rx.button(
                rx.cond(
                    PlanningState.details["final_outcome"] == "Approved",
                    t("open_pdf_tab"),
                    t("open_decision_tab"),
                ),
                on_click=PlanningState.change_view("decision"),
                disabled=BUSY,
                variant="outline",
                width="100%",
                margin_top="1.25rem",
            ),
            rx.button(
                rx.cond(PlanningState.next_step == 3, t("review_decision"), t("compare_plans")),
                on_click=PlanningState.change_view(
                    rx.cond(PlanningState.next_step == 3, "decision", "plans")
                ),
                disabled=BUSY,
                background=ACCENT,
                color="white",
                width="100%",
                margin_top="1.25rem",
            ),
        ),
    )


def _options():
    return card(
        heading("compare_options", size="4"),
        rx.cond(
            PlanningState.details["decision_summary"] != "",
            muted(PlanningState.details["decision_summary"], margin_top="0.35rem"),
        ),
        rx.cond(
            PlanningState.plans.length() > 0,
            rx.box(
                rx.flex(
                    rx.foreach(PlanningState.plans, _plan_option),
                    direction="column",
                    gap="0.6rem",
                    role="radiogroup",
                    aria_label=t("compare_options"),
                    margin_y="1rem",
                ),
                rx.cond(
                    PlanningState.details["alternative_notice"] != "",
                    muted(PlanningState.details["alternative_notice"], margin_bottom="0.75rem"),
                ),
                muted(rx.cond(DECIDED, t("options_decided"), t("options_note"))),
                rx.button(
                    t("compare_plans"),
                    on_click=PlanningState.change_view("plans"),
                    disabled=BUSY,
                    variant="outline",
                    margin_top="1rem",
                ),
            ),
            rx.callout(
                rx.cond(
                    PlanningState.details["status_code"] == "infeasible",
                    t("infeasible_body"),
                    t("no_result_body"),
                ),
                color_scheme="amber",
                margin_top="1rem",
            ),
        ),
    )


def _suppliers_summary():
    counts = PlanningState.supplier_class_counts
    return card(
        rx.flex(
            rx.box(
                rx.text(
                    counts["total"],
                    " ",
                    t("suppliers_evaluated"),
                    font_weight="650",
                    color=INK,
                ),
                rx.text(
                    counts["flagged"],
                    " ",
                    t("suppliers_flagged"),
                    size="2",
                    color=MUTED,
                ),
            ),
            rx.button(
                t("inspect_suppliers"),
                rx.icon("arrow-right", size=16),
                on_click=PlanningState.change_view("suppliers"),
                disabled=BUSY,
                variant="ghost",
            ),
            justify="between",
            align="center",
            gap="1rem",
            wrap="wrap",
        ),
    )


def overview_view() -> rx.Component:
    return rx.box(
        rx.grid(
            kpi(
                "kpi_min_cost",
                rx.cond(
                    PlanningState.details["min_cost_display"] != "",
                    PlanningState.details["min_cost_display"],
                    "—",
                ),
            ),
            kpi("kpi_plans", PlanningState.details["plan_count"]),
            kpi("kpi_decision", PlanningState.details["final_outcome_label"]),
            columns=rx.breakpoints(initial="1", sm="3"),
            gap="1rem",
        ),
        rx.grid(
            rx.flex(_options(), _suppliers_summary(), direction="column", gap="1rem"),
            _next_step(),
            columns=rx.breakpoints(initial="1", lg="minmax(0,1.6fr) minmax(0,1fr)"),
            gap="1rem",
            margin_top="1rem",
            align_items="start",
        ),
    )
