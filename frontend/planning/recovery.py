"""Uncertain save or decision conflict: retry the same request, never create a replacement."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.ui import t


def recovery() -> rx.Component:
    return rx.cond(
        (PlanningState.has_pending | PlanningState.decision_conflict) & ~PlanningState.is_loading,
        rx.box(
            rx.heading(
                rx.cond(
                    PlanningState.decision_conflict,
                    t("recovery_conflict_title"),
                    t("recovery_title"),
                ),
                as_="h2",
                size="4",
                id="request-recovery-heading",
                tab_index=-1,
                on_mount=PlanningState.focus_pending_save,
            ),
            rx.text(
                rx.cond(
                    PlanningState.decision_conflict,
                    t("recovery_conflict_body"),
                    t("recovery_body"),
                ),
                size="2",
                margin_y="0.75rem",
                max_width="70ch",
            ),
            rx.cond(
                PlanningState.decision_conflict,
                rx.callout(PlanningState.error_message, role="alert", color_scheme="red"),
            ),
            rx.cond(
                PlanningState.decision_conflict,
                rx.button(t("reopen_decision"), on_click=PlanningState.reopen_conflicted_decision),
                rx.button(t("retry_same"), on_click=PlanningState.recover_request),
            ),
            rx.text(t("recovery_session_note"), size="2", margin_top="0.75rem", max_width="70ch"),
            rx.el.details(
                rx.el.summary(t("recovery_copy")),
                rx.text(t("request_key"), ": ", PlanningState.request_key, size="2"),
                rx.button(
                    t("copy_request"),
                    variant="soft",
                    on_click=rx.set_clipboard(PlanningState.recovery_json),
                ),
                rx.text_area(
                    value=PlanningState.recovery_json,
                    read_only=True,
                    aria_label=t("recovery_copy"),
                    width="100%",
                    height="10rem",
                ),
                margin_top="0.75rem",
            ),
            padding="1rem 1.25rem",
            border="1px solid #956018",
            border_radius="10px",
            background="#FFF8EB",
            margin_bottom="1rem",
            role="region",
            aria_label=t("recovery_title"),
        ),
    )
