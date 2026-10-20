"""Small, accessible workflow primitives composed entirely in Reflex."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, INK, MUTED
from frontend.ui import BUSY, t


def source_badge(kind: str):
    return rx.badge(
        rx.icon({"odoo": "database", "buyer": "pencil", "suggested": "info"}[kind], size=12),
        t("source_" + kind),
        color_scheme={"odoo": "jade", "buyer": "iris", "suggested": "amber"}[kind],
        variant="soft",
        size="1",
    )


def field_hint(key: str, identity):
    return rx.text(t(key), id=identity + "-hint", size="1", color=MUTED, line_height="1.5")


def creation_steps():
    return rx.el.nav(
        *[
            rx.button(
                rx.box(
                    str(index + 1),
                    class_name="step-number",
                    background=rx.cond(PlanningState.creation_step == index, ACCENT, "white"),
                    color=rx.cond(PlanningState.creation_step == index, "white", MUTED),
                ),
                t(label),
                on_click=PlanningState.go_creation_step(index),
                disabled=BUSY
                | ((index > 0) & ~PlanningState.odoo_ready)
                | ((index == 3) & (PlanningState.creation_review.get("kind", "") == "")),
                aria_current=rx.cond(PlanningState.creation_step == index, "step", "false"),
                variant="ghost",
                color=rx.cond(PlanningState.creation_step == index, INK, MUTED),
                font_weight=rx.cond(PlanningState.creation_step == index, "650", "450"),
                id=f"creation-step-{index}",
                class_name="workflow-step",
            )
            for index, label in enumerate(
                ("step_source", "step_demand", "step_terms", "step_review")
            )
        ],
        aria_label=t("creation_progress"),
        class_name="workflow-steps",
        border_bottom=f"1px solid {HAIRLINE}",
    )
