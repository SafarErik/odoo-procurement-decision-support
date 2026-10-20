"""Small shared building blocks: translated text, cards, badges and states."""

import reflex as rx

from frontend.i18n import TEXT
from frontend.planning.state import PlanningState
from frontend.theme import ERROR, HAIRLINE, INK, MUTED, SURFACE

BUSY = PlanningState.is_loading | PlanningState.has_pending


def t(key: str):
    """Text in the UI language; compiled to a client-side switch, no server round trip."""
    hu, en = TEXT[key]
    return rx.cond(PlanningState.lang == "en", en, hu)


def card(*children, **props):
    style = {
        "background": SURFACE,
        "border": f"1px solid {HAIRLINE}",
        "border_radius": "14px",
        "padding": ["1rem", "1.25rem"],
        "min_width": "0",
        "width": "100%",
    }
    style.update(props)
    return rx.box(*children, **style)


def heading(key_or_var, *, level: str = "h2", size: str = "4", **props):
    text = t(key_or_var) if isinstance(key_or_var, str) else key_or_var
    return rx.heading(text, as_=level, size=size, color=INK, **props)


def muted(text, **props):
    return rx.text(t(text) if isinstance(text, str) else text, size="2", color=MUTED, **props)


def kpi(label: str, value, sub=None, **props):
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
        ("scenario", rx.badge(t("badge_scenario"), color_scheme="iris", size="2")),
        rx.badge(t("decision_draft"), color_scheme="amber", size="2"),
    )


def loading_state(key: str = "loading"):
    return rx.box(
        rx.text(t(key), color=MUTED, size="2", margin_bottom="1rem"),
        rx.skeleton(height="1rem", width="38%", margin_bottom="0.75rem"),
        rx.skeleton(height="1rem", width="74%", margin_bottom="0.75rem"),
        rx.skeleton(height="1rem", width="56%"),
        role="status",
        padding="2rem 0",
    )


def error_state(message, *, retry=None, title: str = "error_title"):
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
    return card(
        rx.heading(t(title), as_="h2", size="4"),
        rx.text(t(body), size="2", color=MUTED, margin_top="0.5rem", max_width="60ch"),
        action if action is not None else rx.fragment(),
        padding="2rem",
    )
