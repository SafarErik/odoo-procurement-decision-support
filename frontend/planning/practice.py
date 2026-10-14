"""Curated entry into genuine saved planning; choosing a task never sends a POST."""

import reflex as rx

from frontend.planning.creation import creation_review, field_error
from frontend.planning.state import PlanningState
from frontend.workspace import workspace_shell

EXERCISES = (
    (
        "compare-plans",
        "Compare plans",
        "Compare exact allocations, total cost and synthetic exposure.",
    ),
    (
        "supplier-outage",
        "Test a supplier outage",
        "Save a fresh base, then test one supplier's outage in What-if.",
    ),
    (
        "infeasible-demand",
        "Make a case infeasible",
        "Save a fresh base, then increase demand to 25 in the prepared example.",
    ),
)


def practice_guidance():
    return rx.cond(
        (PlanningState.details["workspace"] == "practice")
        & (PlanningState.details["example_id"] != ""),
        rx.box(
            rx.heading("Practice exercise", as_="h3", size="3"),
            rx.text(
                rx.cond(
                    PlanningState.details["example_id"] == "compare-plans",
                    "Compare the saved minimum-cost and alternative allocations. "
                    "Exposure is a synthetic proxy, not a failure probability.",
                    rx.cond(
                        PlanningState.details["example_id"] == "supplier-outage",
                        "Test one supplier's outage against this original base. "
                        "Preparing the scenario only fills a draft; save it deliberately.",
                        "For the prepared 24-unit capacity example, increase demand to 25. "
                        "The saved outcome must explain infeasibility without inventing a plan.",
                    ),
                ),
                size="2",
                margin_top="0.5rem",
            ),
            rx.cond(
                (PlanningState.details["parent_id"] == "Base case")
                & (PlanningState.details["example_id"] != "compare-plans"),
                rx.button(
                    "Prepare exercise scenario",
                    id="prepare-exercise",
                    on_click=PlanningState.prepare_practice_scenario,
                    disabled=PlanningState.has_pending | PlanningState.is_loading,
                    margin_top="0.75rem",
                    variant="outline",
                ),
            ),
            padding="1rem",
            background="#f1eff8",
            margin_bottom="1rem",
        ),
    )


def practice_page():
    from frontend.planning.page import _recovery

    busy = PlanningState.is_loading | PlanningState.has_pending
    saved = (
        PlanningState.practice_run_saved
        & PlanningState.has_case
        & (PlanningState.details["workspace"] == "practice")
        & (PlanningState.details["example_id"] == PlanningState.practice_task)
    )
    return workspace_shell(
        rx.box(
            rx.el.style("""
            .practice :focus-visible { outline:3px solid #413b76; outline-offset:3px; }
            .practice button { min-height:2.75rem; white-space:normal; }
            .practice ::selection { background:#d8d2f0; color:#173e3d; }
            @media(prefers-reduced-motion:reduce) {
                .practice * { animation:none!important; transition:none!important; }
            }
        """),
            rx.box(
                rx.heading("Practice", as_="h1", size="7"),
                rx.text(
                    "Learn with a fresh synthetic comparison.", color="#536964", margin_top="0.5rem"
                ),
                rx.text(
                    "Practice uses real planning and application storage. "
                    "Choosing an exercise saves nothing. "
                    "Calculate/save and scenario saves persist only when you "
                    "explicitly request them. "
                    "There is no separate database, reset or automatic cleanup.",
                    max_width="72ch",
                    margin_y="1rem",
                ),
                rx.text(
                    "Inputs, supplier history and ML evidence are synthetic. "
                    "Simulation dates stay fixed "
                    "to the offline example; current operational validity is not asserted.",
                    size="2",
                    color="#536964",
                    max_width="72ch",
                ),
                rx.vstack(
                    *[
                        rx.box(
                            rx.heading(title, as_="h2", size="4"),
                            rx.text(description, color="#536964", margin_y="0.5rem"),
                            rx.button(
                                "Choose " + title.lower(),
                                id="choose-" + identity,
                                on_click=PlanningState.choose_practice_task(identity),
                                disabled=busy,
                                background="#413b76",
                                color="white",
                            ),
                            padding="1.25rem 0",
                            border_bottom="1px solid #d1ded6",
                            width="100%",
                        )
                        for identity, title, description in EXERCISES
                    ],
                    align="stretch",
                    margin_y="1.5rem",
                ),
                rx.cond(
                    PlanningState.error_message != "",
                    rx.callout(PlanningState.error_message, role="alert", color_scheme="red"),
                ),
                _recovery(),
                rx.cond(PlanningState.is_loading, rx.text("Saving Practice case…", role="status")),
                rx.cond(
                    PlanningState.practice_task != "",
                    rx.box(
                        rx.heading(
                            rx.cond(
                                saved,
                                "Saved Practice comparison",
                                rx.cond(
                                    PlanningState.has_pending,
                                    "Practice save awaiting confirmation",
                                    "Fresh Practice draft",
                                ),
                            ),
                            as_="h2",
                            size="4",
                            id="practice-draft-heading",
                            tab_index=-1,
                        ),
                        rx.text(PlanningState.demo_details, size="2", margin_y="0.75rem"),
                        rx.text(PlanningState.demo_policy, size="2", color="#536964"),
                        rx.cond(
                            saved,
                            rx.box(
                                rx.heading(
                                    "Practice case saved",
                                    as_="h2",
                                    id="practice-saved-heading",
                                    tab_index=-1,
                                    on_mount=rx.set_focus("practice-saved-heading"),
                                    size="4",
                                ),
                                rx.text(
                                    "Comparison saved. Approval is a separate choice. "
                                    "Reopening uses this stored run; choosing "
                                    "an exercise again starts a fresh draft, even after "
                                    "finalization.",
                                    role="status",
                                ),
                                rx.button(
                                    "Open saved Practice case",
                                    on_click=PlanningState.open_saved_case(
                                        PlanningState.details["case_id"]
                                    ),
                                    disabled=busy,
                                    margin_top="0.75rem",
                                ),
                            ),
                            rx.form(
                                rx.el.label("Demand quantity", html_for="demo-quantity"),
                                rx.input(
                                    id="demo-quantity",
                                    name="quantity",
                                    type="number",
                                    min="1",
                                    max="1000",
                                    step="1",
                                    required=True,
                                    default_value=PlanningState.demo_quantity,
                                    on_change=PlanningState.mark_creation_dirty,
                                    disabled=busy
                                    | (PlanningState.creation_review.get("kind", "") != ""),
                                    aria_invalid=PlanningState.creation_errors.get(
                                        "demo-quantity", ""
                                    )
                                    != "",
                                    aria_describedby="demo-quantity-error",
                                    width="100%",
                                ),
                                field_error("demo-quantity"),
                                rx.text(
                                    "The prepared demand starts at 10 pieces. Dates and other "
                                    "terms stay fixed to this synthetic example.",
                                    size="2",
                                ),
                                rx.button(
                                    "Review Practice terms",
                                    type="submit",
                                    disabled=busy
                                    | ~PlanningState.demo_ready
                                    | (PlanningState.creation_review.get("kind", "") != ""),
                                    background="#413b76",
                                    color="white",
                                    margin_top="1rem",
                                ),
                                on_submit=PlanningState.review_demo,
                                no_validate=True,
                                reset_on_submit=False,
                            ),
                        ),
                        creation_review("demo"),
                        background="white",
                        padding="1.25rem",
                        margin_top="1rem",
                    ),
                ),
                max_width="72rem",
                margin="auto",
                padding=["1.25rem", "2rem"],
            ),
            class_name="practice",
            color="#173e3d",
            background="#eff5f1",
            overflow_wrap="anywhere",
        ),
        active="practice",
    )
