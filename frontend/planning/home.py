"""Task-oriented home, using bounded saved-case queries without invented totals."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, INK, MUTED
from frontend.ui import BUSY, card, decision_badge, error_state, loading_state, t
from frontend.workspace import page_frame, workspace_shell


def _case(row):
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["product"], font_weight="650"),
                rx.text(row["context"], color=MUTED, size="2", margin_top="0.25rem"),
                rx.text(
                    row["short_id"],
                    " · ",
                    row["saved"],
                    size="1",
                    color=MUTED,
                    margin_top="0.35rem",
                ),
                min_width="0",
                flex="1",
            ),
            rx.flex(
                decision_badge(row["status"]),
                rx.cond(row["badge"] != "", rx.badge(row["badge"], color_scheme="gray")),
                direction="column",
                align="end",
                gap="0.35rem",
            ),
            gap="1rem",
            align="start",
        ),
        rx.flex(
            rx.text(row["minimum_cost"], font_weight="600", size="2"),
            rx.button(
                t("continue_case"),
                rx.icon("arrow-up-right", size=16),
                on_click=PlanningState.open_saved_case(row["case_id"], "overview"),
                disabled=BUSY,
                variant="ghost",
                size="2",
                aria_label=t("continue_case") + ": " + row["product"] + " · " + row["short_id"],
            ),
            justify="between",
            align="center",
            gap="0.5rem",
            margin_top="0.5rem",
        ),
        padding="1rem 0",
        border_bottom=f"1px solid {HAIRLINE}",
    )


def _section(title, rows, error, empty):
    return card(
        rx.heading(t(title), as_="h2", size="5"),
        rx.cond(
            error != "",
            error_state(error, retry=PlanningState.home_on_load),
            rx.cond(
                rows.length() > 0,
                rx.foreach(rows, _case),
                rx.text(t(empty), color=MUTED, size="2", padding_y="2rem"),
            ),
        ),
        rx.button(
            t("all_cases"),
            rx.icon("arrow-right", size=16),
            on_click=PlanningState.navigate_global("cases"),
            variant="ghost",
            margin_top="1rem",
            disabled=BUSY,
        ),
    )


def home_page():
    return workspace_shell(
        page_frame(
            rx.flex(
                rx.box(
                    rx.heading(t("home_title"), as_="h1", size="8", letter_spacing="-0.03em"),
                    rx.text(
                        t("home_intro"),
                        size="3",
                        color=MUTED,
                        max_width="58ch",
                        margin_top="0.75rem",
                    ),
                ),
                rx.button(
                    rx.icon("plus", size=19),
                    t("new_procurement"),
                    on_click=PlanningState.new_comparison,
                    background=ACCENT,
                    color="white",
                    size="3",
                    disabled=BUSY,
                ),
                justify="between",
                align="center",
                gap="1.5rem",
                wrap="wrap",
                padding_y="1.5rem",
            ),
            rx.flex(
                *[
                    rx.flex(
                        rx.icon(icon, size=19, color=ACCENT),
                        rx.box(
                            rx.text(t(title), size="2", font_weight="650", color=INK),
                            rx.text(t(body), size="2", color=MUTED),
                        ),
                        gap="0.65rem",
                        align="start",
                        flex="1",
                        min_width="12rem",
                    )
                    for icon, title, body in (
                        ("files", "home_source_title", "home_source_body"),
                        ("chart-no-axes-combined", "home_compare_title", "home_compare_body"),
                        ("file-check-2", "home_decide_title", "home_decide_body"),
                    )
                ],
                gap="1.5rem",
                wrap="wrap",
                padding_y="1.5rem",
                border_top=f"1px solid {HAIRLINE}",
                border_bottom=f"1px solid {HAIRLINE}",
                margin_bottom="2rem",
            ),
            rx.cond(
                PlanningState.home_loading,
                loading_state("loading_cases"),
                rx.grid(
                    _section(
                        "home_pending",
                        PlanningState.home_pending,
                        PlanningState.home_pending_error,
                        "home_pending_empty",
                    ),
                    _section(
                        "home_recent",
                        PlanningState.home_recent,
                        PlanningState.home_recent_error,
                        "home_recent_empty",
                    ),
                    columns=rx.breakpoints(initial="1", lg="2"),
                    gap="1.5rem",
                    align_items="start",
                ),
            ),
            rx.text(t("home_scope"), color=MUTED, size="1", margin_top="1.25rem"),
        ),
        active="home",
    )
