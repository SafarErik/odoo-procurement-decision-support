"""Buyer workflow, navigation and request recovery."""

import reflex as rx

from frontend.planning.audit import audit_view
from frontend.planning.decision import decision_view, selection_review
from frontend.planning.inputs import _planning_controls
from frontend.planning.practice import practice_guidance
from frontend.planning.results import plans_view, suppliers_view
from frontend.planning.scenarios import _scenario_comparison, _scenario_form
from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, MUTED, SURFACE
from frontend.workspace import workspace_shell


def _test_guide() -> rx.Component:

    return rx.el.details(
        rx.el.summary("What should I test?", font_weight="650", cursor="pointer"),
        rx.el.ol(
            rx.el.li(
                "Open or create a base case. Check demand, price and supplier limits in Audit."
            ),
            rx.el.li(
                "Compare Plans: quantities must meet demand. Read the extra cost "
                "and exposure trade-off."
            ),
            rx.el.li(
                "In What-if, remove a supplier or reduce its capacity. Inspect the "
                "saved change from the base."
            ),
            rx.el.li(
                "Increase demand beyond available capacity. Expect No feasible "
                "plan, never invented allocations."
            ),
            rx.el.li(
                "Copy the new case ID, then reopen it. Costs, quantities and "
                "snapshot hash must stay the same."
            ),
            padding_left="1.2rem",
            line_height="1.7",
            font_size="0.875rem",
        ),
        rx.text(
            "Model accuracy is a separate evaluation; these checks validate the "
            "controlled decision workflow.",
            size="2",
            color=MUTED,
        ),
        padding="1rem",
        background=SURFACE,
        border=f"1px solid {HAIRLINE}",
        border_radius="8px",
    )


def _recovery() -> rx.Component:

    return rx.cond(
        PlanningState.has_pending & ~PlanningState.is_loading,
        rx.box(
            rx.heading(
                "Confirm the pending save before continuing",
                as_="h2",
                size="3",
                id="request-recovery-heading",
                tab_index=-1,
                on_mount=PlanningState.focus_pending_decision,
            ),
            rx.text(
                "The response is uncertain. Retry the identical request; changing "
                "inputs could create another case or conflict with a recorded decision.",
                size="2",
                margin_y="0.75rem",
            ),
            rx.button(
                "Retry the same request",
                on_click=PlanningState.recover_request,
                disabled=PlanningState.is_loading,
            ),
            rx.el.details(
                rx.el.summary("Copy recovery record before leaving", cursor="pointer"),
                rx.text(
                    "Idempotency key: ",
                    PlanningState.request_key,
                    size="2",
                    overflow_wrap="anywhere",
                ),
                rx.button(
                    "Copy exact request",
                    variant="soft",
                    on_click=rx.set_clipboard(PlanningState.recovery_json),
                ),
                rx.text_area(
                    value=PlanningState.recovery_json,
                    read_only=True,
                    aria_label="Exact request recovery JSON",
                    width="100%",
                    height="10rem",
                ),
                margin_top="1rem",
            ),
            padding="1rem",
            border="1px solid #956018",
            background="#FFF8EB",
            margin_bottom="1rem",
        ),
    )


def _workspace() -> rx.Component:

    return rx.box(
        rx.flex(
            rx.box(
                rx.heading(
                    PlanningState.details["product_label"],
                    as_="h1",
                    size="7",
                    id="saved-case-heading",
                    tab_index=-1,
                    on_mount=rx.set_focus("saved-case-heading"),
                ),
                rx.text(
                    PlanningState.details["quantity"],
                    " ",
                    PlanningState.details["unit"],
                    " · ",
                    PlanningState.details["currency"],
                    " · required ",
                    PlanningState.details["required_date"],
                    size="2",
                    color=MUTED,
                ),
            ),
            rx.box(
                rx.badge(PlanningState.details["status_label"], color_scheme="green"),
                rx.text(
                    rx.cond(
                        PlanningState.details["final_outcome"] == "",
                        "Awaiting decision",
                        PlanningState.details["final_outcome"],
                    ),
                    font_weight="650",
                ),
                rx.text(PlanningState.details["scenario_label"], size="2", margin_top="0.25rem"),
            ),
            justify="between",
            flex_wrap="wrap",
            gap="1rem",
        ),
        rx.text(
            "Workspace: ",
            PlanningState.details["workspace_label"],
            font_weight="650",
            margin_top="0.75rem",
        ),
        rx.text(
            "Captured cutoff: ",
            PlanningState.details["as_of"],
            " · Saved: ",
            PlanningState.details["created_at"],
            size="2",
            color=MUTED,
        ),
        rx.text("Original base: ", PlanningState.details["base_id"], size="1", color=MUTED),
        rx.flex(
            rx.text(
                "Saved case ",
                PlanningState.details["case_id"],
                size="1",
                color=MUTED,
                overflow_wrap="anywhere",
            ),
            rx.button(
                "Copy case ID",
                variant="soft",
                size="1",
                on_click=rx.set_clipboard(PlanningState.details["case_id"]),
            ),
            rx.cond(
                PlanningState.details["parent_id"] != "Base case",
                rx.button(
                    "View base case",
                    variant="soft",
                    size="1",
                    disabled=PlanningState.is_loading | PlanningState.has_pending,
                    on_click=PlanningState.open_saved_case(PlanningState.details["base_id"]),
                ),
            ),
            gap="0.6rem",
            align="center",
            flex_wrap="wrap",
            margin_y="0.75rem",
        ),
        rx.text(PlanningState.details["input_kind"], size="2", color=MUTED, margin_bottom="1rem"),
        rx.cond(
            PlanningState.details["workspace"] == "practice",
            rx.text(
                "Practice persists in application storage. No isolation or reset is provided.",
                size="2",
                color=MUTED,
                margin_bottom="1rem",
            ),
        ),
        rx.tabs.root(
            rx.tabs.list(
                *[
                    rx.tabs.trigger(
                        label,
                        value=value,
                        id="view-" + value,
                        disabled=PlanningState.has_pending | PlanningState.is_loading,
                    )
                    for label, value in (
                        ("Plans", "plans"),
                        ("What-if", "whatif"),
                        ("Suppliers", "suppliers"),
                        ("Audit", "audit"),
                    )
                ]
            ),
            rx.tabs.content(plans_view(), value="plans", padding_top="1.25rem"),
            rx.tabs.content(
                _scenario_comparison(),
                _scenario_form(),
                value="whatif",
                padding_top="1.25rem",
            ),
            rx.tabs.content(suppliers_view(), value="suppliers", padding_top="1.25rem"),
            rx.tabs.content(audit_view(), value="audit", padding_top="1.25rem"),
            value=PlanningState.view,
            on_change=PlanningState.change_view,
            width="100%",
        ),
        selection_review(),
        decision_view(),
        practice_guidance(),
        background=SURFACE,
        border=f"1px solid {HAIRLINE}",
        border_radius="10px",
        padding=["1rem", "1.5rem"],
        min_width="0",
    )


def planning_page() -> rx.Component:

    return workspace_shell(
        rx.box(
            rx.cond(
                ~PlanningState.has_case,
                rx.heading("Start a comparison", as_="h1", size="7", margin_bottom="1rem"),
            ),
            rx.cond(
                PlanningState.is_loading,
                rx.hstack(
                    rx.spinner(),
                    rx.text("Waiting for the planning API..."),
                    role="status",
                    margin_bottom="1rem",
                ),
            ),
            rx.cond(
                (PlanningState.error_message != "")
                & (
                    (PlanningState.error_target != "decision")
                    | ~PlanningState.has_case
                    | PlanningState.has_pending
                )
                & ((PlanningState.view != "whatif") | (PlanningState.error_target != "scenario")),
                rx.callout(
                    PlanningState.error_message,
                    color_scheme="red",
                    role="alert",
                    margin_bottom="1rem",
                ),
            ),
            _recovery(),
            rx.cond(
                PlanningState.notice != "",
                rx.callout(
                    PlanningState.notice, color_scheme="green", role="status", margin_bottom="1rem"
                ),
            ),
            rx.cond(PlanningState.has_case, _workspace()),
            rx.el.details(
                rx.el.summary(
                    "Open or create a comparison",
                    font_weight="650",
                    cursor="pointer",
                    padding=".75rem 0",
                ),
                _planning_controls(),
                open=~PlanningState.has_case,
                background=SURFACE,
                border=f"1px solid {HAIRLINE}",
                padding="1rem",
                margin_top="1.5rem",
            ),
            _test_guide(),
            rx.el.details(
                rx.el.summary("Evidence boundary", padding=".75rem 0"),
                rx.text(
                    "Odoo quotations may be live. Supplier history and model evidence remain "
                    "synthetic. What-if changes are assumptions, not Odoo updates.",
                    size="2",
                    color=MUTED,
                    max_width="75ch",
                ),
                rx.text(
                    "Original bases support saved human approval or No-award. Approved plans "
                    "have a viewable and downloadable PDF.",
                    size="2",
                    color=MUTED,
                    max_width="75ch",
                ),
            ),
            max_width="88rem",
            margin="auto",
            padding=["1rem", "1.5rem", "2rem"],
            min_width="0",
            class_name="cockpit",
        ),
        active="cases",
    )
