"""Curated entry into genuine saved planning; choosing a task never sends a POST."""

import reflex as rx

from frontend.planning.state import PlanningState

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
    return rx.box(
        rx.el.style("""
            .practice :focus-visible { outline:3px solid #413b76; outline-offset:3px; }
            .practice button { min-height:2.75rem; white-space:normal; }
            .practice ::selection { background:#d8d2f0; color:#173e3d; }
            @media(prefers-reduced-motion:reduce) {
                .practice * { animation:none!important; transition:none!important; }
            }
        """),
        rx.flex(
            rx.text("Procurement workspace", font_weight="650"),
            rx.button(
                "Saved cases",
                on_click=PlanningState.open_library,
                disabled=busy,
                variant="soft",
                color="white",
                background="#413b76",
                style={"&:focus-visible": {"outline_color": "white"}},
            ),
            justify="between",
            wrap="wrap",
            gap="1rem",
            padding="1rem 1.5rem",
            background="#153f40",
            color="white",
        ),
        rx.box(
            rx.heading("Practice", as_="h1", size="7"),
            rx.text(
                "Learn with a fresh synthetic comparison.", color="#536964", margin_top="0.5rem"
            ),
            rx.text(
                "Practice uses real planning and application storage. "
                "Choosing an exercise saves nothing. "
                "Calculate/save and scenario saves persist only when you explicitly request them. "
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
                        "Fresh Practice draft",
                        as_="h2",
                        size="4",
                        id="practice-draft-heading",
                        tab_index=-1,
                    ),
                    rx.text(PlanningState.demo_details, size="2", margin_y="0.75rem"),
                    rx.text(PlanningState.demo_policy, size="2", color="#536964"),
                    rx.cond(
                        PlanningState.practice_run_saved
                        & PlanningState.has_case
                        & (PlanningState.details["workspace"] == "practice")
                        & (PlanningState.details["example_id"] == PlanningState.practice_task),
                        rx.box(
                            rx.text(
                                "Practice case saved. Reopening uses this stored run; choosing "
                                "an exercise again starts a fresh draft, even after finalization.",
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
                            rx.el.input(type="hidden", name="quantity", value="10"),
                            rx.text(
                                "The prepared demand is 10 pieces. "
                                "Review exact saved facts in Audit after calculation.",
                                size="2",
                            ),
                            rx.button(
                                "Calculate and save fresh Practice case",
                                type="submit",
                                disabled=busy | ~PlanningState.demo_ready,
                                background="#413b76",
                                color="white",
                                margin_top="1rem",
                            ),
                            on_submit=PlanningState.create_demo,
                        ),
                    ),
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
        min_height="100vh",
        color="#173e3d",
        background="#eff5f1",
        overflow_wrap="anywhere",
    )
