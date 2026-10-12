"""Explicit original-base human decision and saved audit presentation."""

import reflex as rx

from frontend.planning.pdf import ApprovedPDFViewer
from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, MUTED, SURFACE


def saved_decision() -> rx.Component:
    return rx.vstack(
        rx.text("Workspace: ", PlanningState.details["workspace_label"], font_weight="650"),
        rx.cond(
            PlanningState.details["workspace"] == "practice",
            rx.text(
                "Practice document access. The backend's immutable PDF bytes retain their "
                "saved source/provenance; this label does not watermark or rewrite the PDF.",
                size="2",
                color=MUTED,
            ),
        ),
        rx.heading(PlanningState.details["final_outcome"], as_="h3", size="4"),
        rx.text("Selected plan: ", PlanningState.details["final_plan"]),
        rx.text("Actor audit reference: ", PlanningState.details["final_actor"]),
        rx.text("Reason: ", PlanningState.details["final_reason"], white_space="pre-wrap"),
        rx.text("Recorded at (UTC): ", PlanningState.details["final_recorded_at"]),
        rx.text(
            "Controlled demonstration with synthetic ML evidence. The actor is caller-supplied "
            "audit text, not authenticated buyer identity. Saved simulation dates remain separate "
            "from the decision record time.",
            color=MUTED,
            size="2",
        ),
        rx.cond(
            PlanningState.details["final_outcome"] == "Approved",
            rx.vstack(
                rx.flex(
                    rx.button(
                        "View approved PDF",
                        on_click=PlanningState.request_pdf,
                        disabled=PlanningState.is_loading | PlanningState.has_pending,
                    ),
                    wrap="wrap",
                    gap="0.75rem",
                ),
                rx.cond(
                    PlanningState.pdf_error != "",
                    rx.callout(PlanningState.pdf_error, color_scheme="amber", role="alert"),
                ),
                rx.cond(
                    PlanningState.pdf_data_url != "",
                    rx.vstack(
                        rx.text(
                            "The PDF is ready. Use Download approved PDF "
                            "to save this exact document.",
                            size="2",
                            color=MUTED,
                            role="status",
                        ),
                        ApprovedPDFViewer.create(
                            data=PlanningState.pdf_data_url,
                            filename=PlanningState.pdf_filename,
                        ),
                        align="stretch",
                        width="100%",
                    ),
                ),
                align="stretch",
                spacing="3",
                width="100%",
            ),
            rx.text("No-award has no approved procurement PDF.", size="2", color=MUTED),
        ),
        align="stretch",
        spacing="3",
        overflow_wrap="anywhere",
    )


def decision_view() -> rx.Component:
    return rx.box(
        rx.text(
            "Decision context: ",
            PlanningState.details["workspace_label"],
            font_weight="650",
            margin_bottom="0.75rem",
        ),
        rx.cond(
            PlanningState.details["parent_id"] != "Base case",
            rx.callout(
                "Stress scenarios remain analytical. Open the original base to record a human "
                "decision. Confirmed changed terms need a new base case.",
                color_scheme="gray",
            ),
            rx.cond(
                PlanningState.details["final_outcome"] != "",
                saved_decision(),
                rx.vstack(
                    rx.heading("Record the final decision", as_="h2", size="4"),
                    rx.text(
                        "Explicitly choose a saved plan or No-award. This one-time decision "
                        "cannot be replaced. Alternative approval and No-award require a reason.",
                        size="2",
                        color=MUTED,
                    ),
                    rx.cond(
                        (PlanningState.details["status"] != "optimal")
                        & (PlanningState.plans.length() > 0),
                        rx.callout(
                            "Comparison is incomplete. Retained proven plans remain eligible; "
                            "the recorded solver outcome and this limitation accompany approval.",
                            color_scheme="amber",
                        ),
                    ),
                    rx.form(
                        rx.vstack(
                            rx.el.label("Plan or No-award", html_for="final-choice"),
                            rx.el.select(
                                rx.el.option("Choose explicitly…", value="", disabled=True),
                                rx.foreach(
                                    PlanningState.plans,
                                    lambda p: rx.el.option(p["label"], value=p["label"]),
                                ),
                                rx.el.option("No-award", value="No-award"),
                                name="choice",
                                id="final-choice",
                                value=PlanningState.final_choice,
                                on_change=PlanningState.choose_final_plan,
                                required=True,
                                disabled=PlanningState.is_loading | PlanningState.has_pending,
                                width="100%",
                                padding="0.6rem",
                                border=f"1px solid {HAIRLINE}",
                            ),
                            rx.el.label("Actor audit reference", html_for="final-actor"),
                            rx.input(
                                name="actor",
                                id="final-actor",
                                placeholder="Buyer reference",
                                max_length=255,
                                required=True,
                                width="100%",
                                disabled=PlanningState.is_loading | PlanningState.has_pending,
                            ),
                            rx.el.label("Reason", html_for="final-reason"),
                            rx.text_area(
                                name="reason",
                                id="final-reason",
                                max_length=2000,
                                width="100%",
                                placeholder="Explain an alternative selection or No-award",
                                required=PlanningState.final_choice != "Minimum cost",
                                disabled=PlanningState.is_loading | PlanningState.has_pending,
                            ),
                            rx.el.label(
                                rx.el.input(
                                    type="checkbox",
                                    name="demonstration",
                                    required=True,
                                    disabled=PlanningState.is_loading | PlanningState.has_pending,
                                    margin_right="0.5rem",
                                ),
                                "I acknowledge this controlled demonstration, saved simulation "
                                "dates and synthetic ML evidence; current operational validity "
                                "is not asserted.",
                                font_size="0.875rem",
                            ),
                            rx.text(
                                "Actor attribution is audit text, not authenticated buyer identity."
                                " "
                                "Approval enables viewing and downloading "
                                "its saved procurement PDF.",
                                size="2",
                                color=MUTED,
                            ),
                            rx.button(
                                "Finalize this base",
                                type="submit",
                                disabled=PlanningState.is_loading
                                | PlanningState.has_pending
                                | (PlanningState.final_choice == ""),
                            ),
                            align="stretch",
                            spacing="3",
                        ),
                        on_submit=PlanningState.finalize_case,
                        reset_on_submit=False,
                        width="100%",
                    ),
                    align="stretch",
                    spacing="3",
                ),
            ),
        ),
        background=SURFACE,
        padding="1.25rem",
        border=f"1px solid {HAIRLINE}",
        border_radius="10px",
        width="100%",
    )
