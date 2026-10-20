"""Decision & PDF tab: one explicit decision on the base case, then its approved PDF."""

import reflex as rx

from frontend.planning.pdf import ApprovedPDFViewer
from frontend.planning.state import PlanningState
from frontend.planning.state_base import focus
from frontend.theme import ACCENT, HAIRLINE, INK, MUTED
from frontend.ui import BUSY, card, muted, t

NO_AWARD = PlanningState.final_choice == "No-award"


def _row(label: str, value):
    return rx.flex(
        rx.text(t(label), size="2", color=MUTED, min_width="9rem"),
        rx.text(value, size="2", font_weight="600", white_space="pre-wrap"),
        gap="1rem",
        padding_y="0.35rem",
        border_bottom=f"1px solid {HAIRLINE}",
        wrap="wrap",
    )


def saved_decision() -> rx.Component:
    approved = PlanningState.details["final_outcome"] == "Approved"
    return rx.box(
        rx.heading(
            PlanningState.details["final_outcome_label"],
            as_="h2",
            size="5",
            id="saved-decision-heading",
            tab_index=-1,
        ),
        rx.box(
            _row("decision_plan", PlanningState.details["final_plan_title"]),
            rx.cond(approved, _row("total_cost", PlanningState.selected_plan.get("cost", ""))),
            _row("decision_actor", PlanningState.details["final_actor"]),
            rx.cond(
                PlanningState.details["final_reason"] != "",
                _row("decision_reason", PlanningState.details["final_reason"]),
            ),
            _row("decision_recorded", PlanningState.details["final_recorded_display"]),
            margin_y="1rem",
        ),
        rx.cond(
            approved,
            rx.box(
                rx.text(t("approved_allocation"), font_weight="650", size="2"),
                rx.foreach(
                    PlanningState.allocations,
                    lambda row: rx.cond(
                        (row["plan"] == PlanningState.details["final_plan"])
                        & (row["quantity"] != "0"),
                        rx.text(
                            row["name"],
                            ": ",
                            row["quantity_display"],
                            " · ",
                            t("promised_short"),
                            " ",
                            row["promised"],
                            size="2",
                        ),
                    ),
                ),
                rx.flex(
                    rx.button(
                        rx.cond(
                            PlanningState.is_loading,
                            rx.spinner(size="2"),
                            rx.icon("file-text", size=16),
                        ),
                        rx.cond(PlanningState.pdf_error != "", t("retry_pdf"), t("view_pdf")),
                        on_click=PlanningState.request_pdf,
                        disabled=BUSY,
                        background=ACCENT,
                        color="white",
                    ),
                    rx.text(t("pdf_language_note"), size="2", color=MUTED),
                    gap="0.75rem",
                    align="center",
                    wrap="wrap",
                    margin_top="1.25rem",
                ),
                rx.cond(
                    PlanningState.pdf_error != "",
                    rx.callout(
                        PlanningState.pdf_error,
                        color_scheme="amber",
                        role="alert",
                        margin_top="1rem",
                    ),
                ),
                rx.cond(
                    PlanningState.pdf_data_url != "",
                    rx.box(
                        ApprovedPDFViewer.create(
                            data=PlanningState.pdf_data_url,
                            filename=PlanningState.pdf_filename,
                            lang=PlanningState.lang,
                        ),
                        margin_top="1rem",
                    ),
                ),
                margin_top="0.5rem",
            ),
            muted("no_award_no_pdf"),
        ),
        muted("no_odoo_order", margin_top="1rem"),
    )


def _confirmation() -> rx.Component:
    review = PlanningState.decision_review
    no_award = review.get("choice", "") == "No-award"
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(
                rx.cond(no_award, t("confirm_no_award"), t("confirm_approval")),
                id="decision-confirm-title",
                flex_shrink="0",
            ),
            rx.alert_dialog.description(t("confirm_body"), flex_shrink="0"),
            rx.box(
                rx.text(
                    PlanningState.details["product_label"], font_weight="650", margin_top="0.75rem"
                ),
                rx.text(
                    PlanningState.details["quantity_display"],
                    " · ",
                    t("required_short"),
                    " ",
                    PlanningState.details["required_display"],
                    size="2",
                    color=MUTED,
                ),
                rx.cond(
                    no_award,
                    rx.text(t("no_award_effect"), margin_top="0.75rem"),
                    rx.box(
                        rx.text(review.get("title", ""), font_weight="650"),
                        rx.text(review.get("cost", ""), size="6", font_weight="650"),
                        rx.text(review.get("allocation_summary", ""), size="2", margin_y="0.5rem"),
                        rx.text(
                            t("risk_exposure"), ": ", review.get("exposure_display", ""), size="2"
                        ),
                        margin_top="0.75rem",
                    ),
                ),
                rx.box(
                    _row("decision_actor", review.get("actor", "")),
                    _row("decision_reason", review.get("reason", "")),
                    margin_top="0.75rem",
                ),
                role="region",
                aria_label=t("confirm_approval"),
                tab_index=0,
                margin_y="1rem",
                overflow_wrap="anywhere",
                flex="1",
                min_height="0",
                overflow_y="auto",
            ),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(t("cancel"), id="decision-confirm-cancel", variant="outline"),
                    as_child=True,
                ),
                rx.button(
                    rx.cond(no_award, t("confirm_no_award"), t("approve_plan")),
                    on_click=PlanningState.confirm_final_decision.throttle(500),
                    disabled=BUSY,
                    background=rx.cond(no_award, INK, ACCENT),
                    color="white",
                ),
                gap="0.75rem",
                flex_wrap="wrap",
                justify="end",
                flex_shrink="0",
            ),
            on_open_auto_focus=focus("decision-confirm-cancel"),
            on_close_auto_focus=focus("decision-review-button"),
            max_width="min(40rem, calc(100vw - 2rem))",
            max_height="calc(100dvh - 2rem)",
            overflow="hidden",
            display="flex",
            flex_direction="column",
            class_name="workspace-dialog",
            aria_labelledby="decision-confirm-title",
        ),
        open=PlanningState.decision_open,
        on_open_change=PlanningState.change_decision_confirmation,
    )


def _decision_form() -> rx.Component:
    return rx.box(
        rx.heading(
            t("record_decision"), as_="h2", size="5", id="final-decision-heading", tab_index=-1
        ),
        muted("record_decision_body", margin_y="0.35rem", max_width="70ch"),
        rx.cond(
            (PlanningState.details["status_code"] != "optimal")
            & (PlanningState.plans.length() > 0),
            rx.callout(t("incomplete_body"), color_scheme="amber", margin_bottom="0.75rem"),
        ),
        rx.form(
            rx.flex(
                rx.cond(
                    NO_AWARD,
                    rx.box(
                        rx.el.input(type="hidden", name="choice", value="No-award"),
                        rx.text(t("no_award_effect"), font_weight="650"),
                        rx.button(
                            t("choose_plan_instead"),
                            type="button",
                            variant="outline",
                            on_click=PlanningState.choose_final_plan(""),
                            disabled=BUSY,
                            margin_top="0.5rem",
                        ),
                    ),
                    rx.box(
                        rx.el.label(
                            t("plan_for_approval"),
                            html_for="final-choice",
                            display="block",
                            font_weight="550",
                        ),
                        rx.el.select(
                            rx.el.option(t("choose_plan"), value="", disabled=True),
                            rx.foreach(
                                PlanningState.plans,
                                lambda p: rx.el.option(
                                    p["title"] + " – " + p["cost"], value=p["label"]
                                ),
                            ),
                            name="choice",
                            id="final-choice",
                            value=PlanningState.final_choice,
                            on_change=PlanningState.choose_final_plan,
                            required=True,
                            disabled=BUSY,
                            width="100%",
                            padding="0.6rem",
                            border=f"1px solid {HAIRLINE}",
                            border_radius="8px",
                            min_height="2.75rem",
                            background="white",
                        ),
                        rx.button(
                            t("record_no_award"),
                            type="button",
                            variant="ghost",
                            on_click=PlanningState.choose_final_plan("No-award"),
                            disabled=BUSY,
                            margin_top="0.5rem",
                        ),
                    ),
                ),
                rx.box(
                    rx.el.label(
                        t("decision_actor"),
                        html_for="final-actor",
                        display="block",
                        font_weight="550",
                    ),
                    rx.input(
                        name="actor",
                        id="final-actor",
                        placeholder=t("actor_placeholder"),
                        max_length=255,
                        required=True,
                        width="100%",
                        size="3",
                        disabled=BUSY,
                    ),
                ),
                rx.box(
                    rx.el.label(
                        t("decision_reason"),
                        html_for="final-reason",
                        display="block",
                        font_weight="550",
                    ),
                    rx.text_area(
                        name="reason",
                        id="final-reason",
                        max_length=2000,
                        width="100%",
                        placeholder=t("reason_placeholder"),
                        required=True,
                        disabled=BUSY,
                    ),
                ),
                rx.el.label(
                    rx.el.input(
                        type="checkbox",
                        name="demonstration",
                        required=True,
                        disabled=BUSY,
                        margin_right="0.5rem",
                        width="1.1rem",
                        height="1.1rem",
                    ),
                    t("ack_label"),
                    font_size="0.875rem",
                    display="flex",
                    align_items="start",
                    gap="0.25rem",
                ),
                rx.button(
                    rx.cond(NO_AWARD, t("review_no_award"), t("review_approval")),
                    id="decision-review-button",
                    type="submit",
                    disabled=BUSY | (PlanningState.final_choice == ""),
                    background=ACCENT,
                    color="white",
                    size="3",
                    width="fit-content",
                ),
                rx.cond(
                    (PlanningState.error_target == "decision")
                    & (PlanningState.error_message != "")
                    & ~PlanningState.has_pending,
                    rx.callout(
                        PlanningState.error_message,
                        role="alert",
                        color_scheme="red",
                        id="decision-error",
                        tab_index=-1,
                        on_mount=focus("decision-error"),
                    ),
                ),
                direction="column",
                gap="1rem",
                margin_top="1rem",
            ),
            on_submit=PlanningState.review_final_decision,
            reset_on_submit=False,
            width="100%",
        ),
        _confirmation(),
    )


def decision_view() -> rx.Component:
    return card(
        rx.cond(
            PlanningState.details["parent_id"] != "Base case",
            rx.box(
                rx.callout(t("scenario_no_decision"), icon="info"),
                rx.button(
                    t("back_to_base"),
                    on_click=PlanningState.open_saved_case(
                        PlanningState.details["base_id"], "decision"
                    ),
                    disabled=BUSY,
                    variant="outline",
                    margin_top="1rem",
                ),
            ),
            rx.cond(
                PlanningState.decision_conflict,
                rx.text(t("decision_paused")),
                rx.cond(
                    PlanningState.details["final_outcome"] != "",
                    saved_decision(),
                    _decision_form(),
                ),
            ),
        ),
        max_width="52rem",
    )
