"""Case page: breadcrumb and header with the case's business facts, messages, the five tabs
(Overview … Decision & PDF) and Audit as a secondary view."""

import reflex as rx

from frontend.planning.audit import audit_view
from frontend.planning.decision import decision_view
from frontend.planning.overview import overview_view
from frontend.planning.recovery import recovery
from frontend.planning.results import plans_view
from frontend.planning.scenarios import scenarios_view
from frontend.planning.state import PlanningState
from frontend.planning.suppliers import suppliers_view
from frontend.theme import MUTED
from frontend.ui import BUSY, decision_badge, error_state, loading_state, primary_button, t
from frontend.workspace import page_frame, workspace_shell

TABS = (
    ("overview", "tab_overview"),
    ("suppliers", "tab_suppliers"),
    ("plans", "tab_plans"),
    ("scenarios", "tab_scenarios"),
    ("decision", "tab_decision"),
)
DETAILS = PlanningState.details


def _status_code():
    """Badge code of the open case: scenario, approved, no_award or draft."""
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


def _breadcrumb() -> rx.Component:
    """ "Cases / product" line linking back to the case library."""
    return rx.flex(
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
        rx.text(DETAILS["product_label"], size="2", color=MUTED, truncate=True),
        gap="0.5rem",
        align="center",
        min_width="0",
    )


def _case_facts() -> rx.Component:
    """Demand, currency and required date with the decision, scenario and origin badges."""
    return rx.flex(
        rx.text(
            DETAILS["quantity_display"],
            " · ",
            DETAILS["currency"],
            " · ",
            t("required_short"),
            " ",
            DETAILS["required_display"],
            size="2",
            color=MUTED,
        ),
        decision_badge(_status_code()),
        rx.cond(
            DETAILS["scenario_label"] != "",
            rx.badge(DETAILS["scenario_label"], color_scheme="iris", variant="soft"),
        ),
        rx.cond(
            DETAILS["origin_badge"] != "",
            rx.badge(DETAILS["origin_badge"], color_scheme="gray", variant="soft"),
        ),
        gap="0.6rem",
        align="center",
        wrap="wrap",
        margin_top="0.35rem",
    )


def _header() -> rx.Component:
    """Breadcrumb, product heading with the case facts, and the Audit button."""
    return rx.box(
        _breadcrumb(),
        rx.flex(
            rx.box(
                rx.heading(
                    DETAILS["product_label"],
                    as_="h1",
                    size="7",
                    id="saved-case-heading",
                    tab_index=-1,
                    margin_top="0.35rem",
                ),
                _case_facts(),
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
    """Error, recovery, success and pending-state lines above the case."""
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
    """The loaded case: header and the tab strip with its six views."""
    return rx.box(
        _header(),
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
    """The case page: messages, then the case, its loading or its error."""
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
                            primary_button(
                                t("back_to_cases"),
                                on_click=PlanningState.navigate_global("cases"),
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
