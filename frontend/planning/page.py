"""Case page: header with business facts, tabs, and Audit as a secondary view."""

import reflex as rx

from frontend.planning.audit import audit_view
from frontend.planning.decision import decision_view
from frontend.planning.overview import overview_view
from frontend.planning.recovery import recovery
from frontend.planning.results import plans_view
from frontend.planning.scenarios import scenarios_view
from frontend.planning.state import PlanningState
from frontend.planning.suppliers import suppliers_view
from frontend.theme import ACCENT, MUTED
from frontend.ui import BUSY, decision_badge, error_state, loading_state, t
from frontend.workspace import page_frame, workspace_shell

TABS = (
    ("overview", "tab_overview"),
    ("suppliers", "tab_suppliers"),
    ("plans", "tab_plans"),
    ("scenarios", "tab_scenarios"),
    ("decision", "tab_decision"),
)


def _status_code():
    return rx.cond(
        PlanningState.details["parent_id"] != "Base case",
        "scenario",
        rx.match(
            PlanningState.details["final_outcome"],
            ("Approved", "approved"),
            ("No-award", "no_award"),
            "draft",
        ),
    )


def _header() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.link(
                t("nav_cases"),
                on_click=PlanningState.navigate_global("cases"),
                href="#",
                color=MUTED,
                size="2",
                white_space="nowrap",
                flex_shrink="0",
            ),
            rx.text("/", size="2", color=MUTED),
            rx.text(PlanningState.details["product_label"], size="2", color=MUTED, truncate=True),
            gap="0.5rem",
            align="center",
            min_width="0",
        ),
        rx.flex(
            rx.box(
                rx.heading(
                    PlanningState.details["product_label"],
                    as_="h1",
                    size="7",
                    id="saved-case-heading",
                    tab_index=-1,
                    margin_top="0.35rem",
                ),
                rx.flex(
                    rx.text(
                        PlanningState.details["quantity_display"],
                        " · ",
                        PlanningState.details["currency"],
                        " · ",
                        t("required_short"),
                        " ",
                        PlanningState.details["required_display"],
                        size="2",
                        color=MUTED,
                    ),
                    decision_badge(_status_code()),
                    rx.cond(
                        PlanningState.details["scenario_label"] != "",
                        rx.badge(
                            PlanningState.details["scenario_label"],
                            color_scheme="iris",
                            variant="soft",
                        ),
                    ),
                    rx.cond(
                        PlanningState.details["origin_badge"] != "",
                        rx.badge(
                            PlanningState.details["origin_badge"],
                            color_scheme="gray",
                            variant="soft",
                        ),
                    ),
                    gap="0.6rem",
                    align="center",
                    wrap="wrap",
                    margin_top="0.35rem",
                ),
                min_width="0",
            ),
            rx.button(
                rx.icon("file-search", size=16),
                t("audit"),
                id="view-audit",
                on_click=PlanningState.change_view("audit"),
                disabled=BUSY,
                variant=rx.cond(PlanningState.view == "audit", "solid", "ghost"),
                color_scheme="gray",
            ),
            justify="between",
            align="end",
            gap="1rem",
            wrap="wrap",
        ),
        margin_bottom="1rem",
    )


def _messages() -> rx.Component:
    return rx.box(
        rx.cond(
            (PlanningState.error_message != "")
            & ~PlanningState.decision_conflict
            & PlanningState.has_case
            & (PlanningState.error_target != "decision")
            & (PlanningState.error_target != "scenario"),
            rx.callout(
                PlanningState.error_message, color_scheme="red", role="alert", margin_bottom="1rem"
            ),
        ),
        recovery(),
        rx.cond(
            PlanningState.notice != "",
            rx.callout(
                PlanningState.notice,
                icon="circle-check",
                color_scheme="green",
                role="status",
                margin_bottom="1rem",
            ),
        ),
        rx.cond(
            PlanningState.has_case
            & (PlanningState.comparison_state != "")
            & (PlanningState.has_pending | PlanningState.decision_conflict),
            rx.text(PlanningState.comparison_state, role="status", font_weight="650"),
        ),
    )


def _workspace() -> rx.Component:
    return rx.box(
        _header(),
        rx.flex(
            rx.icon("route", size=18, color=ACCENT),
            rx.text(PlanningState.next_action_text, size="2", font_weight="550"),
            gap="0.6rem",
            align="center",
            padding="0.85rem 1rem",
            background="#e5ede8",
            border_radius="10px",
            margin_bottom="1.25rem",
            role="status",
        ),
        rx.tabs.root(
            rx.tabs.list(
                *[
                    rx.tabs.trigger(t(label), value=value, id="view-" + value, disabled=BUSY)
                    for value, label in TABS
                ],
                size="2",
                color_scheme="iris",
                id="case-tablist",
            ),
            *[
                rx.tabs.content(view(), value=value, padding_top="1.25rem")
                for value, view in (
                    ("overview", overview_view),
                    ("suppliers", suppliers_view),
                    ("plans", plans_view),
                    ("scenarios", scenarios_view),
                    ("decision", decision_view),
                    ("audit", audit_view),
                )
            ],
            value=PlanningState.view,
            on_change=PlanningState.change_view,
            width="100%",
        ),
    )


def planning_page() -> rx.Component:
    return workspace_shell(
        page_frame(
            _messages(),
            rx.cond(
                PlanningState.has_case,
                _workspace(),
                rx.cond(
                    PlanningState.is_loading,
                    loading_state("loading_case"),
                    rx.cond(
                        (PlanningState.error_message != "") & ~PlanningState.has_pending,
                        rx.box(
                            error_state(PlanningState.error_message, title="case_error_title"),
                            rx.button(
                                t("back_to_cases"),
                                on_click=PlanningState.navigate_global("cases"),
                                background=ACCENT,
                                color="white",
                                margin_top="1rem",
                            ),
                        ),
                        loading_state("loading_case"),
                    ),
                ),
            ),
        ),
        active="cases",
    )
