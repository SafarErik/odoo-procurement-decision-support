"""Small shared building blocks every screen uses: translated text, cards, headings, the
primary button, native field styling, decision badges and loading/error/empty states."""

import reflex as rx

from frontend.i18n import TEXT
from frontend.planning.state import PlanningState
from frontend.theme import (
    ACCENT,
    CARD_PADDING,
    ERROR,
    HAIRLINE,
    INK,
    MUTED,
    RADIUS_CARD,
    RADIUS_NAV,
    SURFACE,
    TOUCH_TARGET,
)

BUSY = PlanningState.is_loading | PlanningState.has_pending
# Native <select>/<input> look shared by the Cases filter, what-if and decision forms;
# each form adds its own padding.
NATIVE_FIELD = {
    "border": f"1px solid {HAIRLINE}",
    "border_radius": RADIUS_NAV,
    "background": SURFACE,
    "min_height": TOUCH_TARGET,
    "width": "100%",
}


def t(key: str):
    """Text in the UI language; compiled to a client-side switch, no server round trip."""
    hu, en = TEXT[key]
    return rx.cond(PlanningState.lang == "en", en, hu)


def card(*children, **props):
    """White bordered surface holding one section; ``props`` override the style."""
    style = {
        "background": SURFACE,
        "border": f"1px solid {HAIRLINE}",
        "border_radius": RADIUS_CARD,
        "padding": CARD_PADDING,
        "min_width": "0",
        "width": "100%",
    }
    style.update(props)
    return rx.box(*children, **style)


def heading(key_or_var, *, level: str = "h2", size: str = "4", **props):
    """Section heading from a text key or an already translated var."""
    text = t(key_or_var) if isinstance(key_or_var, str) else key_or_var
    return rx.heading(text, as_=level, size=size, color=INK, **props)


def muted(text, **props):
    """Secondary grey explanation text from a text key or a var."""
    return rx.text(t(text) if isinstance(text, str) else text, size="2", color=MUTED, **props)


def kpi(label: str, value, sub=None, **props):
    """Card with a label and one large headline number."""
    return card(
        rx.text(t(label), size="2", color=MUTED),
        rx.text(value, size="7", font_weight="650", color=INK, margin_top="0.25rem"),
        rx.text(sub, size="2", color=MUTED) if sub is not None else rx.fragment(),
        **props,
    )


def decision_badge(status):
    """Badge for a decision status code: draft | approved | no_award | scenario."""
    return rx.match(
        status,
        ("approved", rx.badge(t("decision_approved"), color_scheme="green", size="2")),
        ("no_award", rx.badge(t("decision_no_award"), color_scheme="gray", size="2")),
        ("scenario", rx.badge(t("scenario"), color_scheme="iris", size="2")),
        rx.badge(t("decision_draft"), color_scheme="amber", size="2"),
    )


def loading_state(key: str = "loading"):
    """Status text above three skeleton lines while a request runs."""
    return rx.box(
        rx.text(t(key), color=MUTED, size="2", margin_bottom="1rem"),
        rx.skeleton(height="1rem", width="38%", margin_bottom="0.75rem"),
        rx.skeleton(height="1rem", width="74%", margin_bottom="0.75rem"),
        rx.skeleton(height="1rem", width="56%"),
        role="status",
        padding="2rem 0",
    )


def error_state(message, *, retry=None, title: str = "error_title"):
    """Alert card with a red rule, the message and an optional retry button."""
    return card(
        rx.box(width="2.5rem", height="0.2rem", background=ERROR, border_radius="999px"),
        rx.heading(t(title), as_="h2", size="4", margin_top="0.75rem"),
        rx.text(message, size="2", color=MUTED, margin_top="0.5rem", max_width="60ch"),
        rx.button(t("retry"), on_click=retry, variant="outline", margin_top="1rem")
        if retry is not None
        else rx.fragment(),
        role="alert",
    )


def empty_state(title: str, body: str, action=None):
    """Card explaining that a list is empty and what can happen next."""
    return card(
        rx.heading(t(title), as_="h2", size="4"),
        rx.text(t(body), size="2", color=MUTED, margin_top="0.5rem", max_width="60ch"),
        action if action is not None else rx.fragment(),
        padding="2rem",
    )


def primary_button(*children, **props):
    """Purple solid button for the main action of a screen (DESIGN.md button-primary)."""
    return rx.button(*children, background=ACCENT, color=SURFACE, **props)


def field_label(key: str, html_for: str):
    """Block label above a native form field."""
    return rx.el.label(t(key), html_for=html_for, display="block", font_weight="550")
