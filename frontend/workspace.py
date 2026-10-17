"""Shared editorial shell; navigation delegates to the HTTP-only planning state."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, INK, PAPER, RAIL


def _navigation(active: str, *, drawer: bool = False):
    return rx.el.nav(
        *[
            rx.button(
                label,
                id=("drawer-" if drawer else "nav-") + destination,
                on_click=PlanningState.navigate_global(destination),
                aria_current="page" if active == destination else "false",
                disabled=PlanningState.has_pending | PlanningState.is_loading,
                class_name="workspace-nav-button",
                background=ACCENT if active == destination else "transparent",
                color="white",
                justify_content="start",
                width="100%",
            )
            for destination, label in (
                ("cases", "Cases"),
                ("rfqs", "Open RFQs"),
            )
        ],
        aria_label="Workspace navigation",
        display="flex",
        flex_direction="column",
        gap="0.75rem",
    )


def _discard_dialog():
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Discard your unsaved draft?"),
            rx.alert_dialog.description(
                "Stay to continue editing, or discard the creation/scenario draft "
                "before navigating. "
                "Saved cases stay in application storage."
            ),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Stay", id="navigation-stay", on_click=PlanningState.stay_navigation(False)
                    ),
                    as_child=True,
                ),
                rx.alert_dialog.action(
                    rx.button("Discard draft", on_click=PlanningState.discard_navigation),
                    as_child=True,
                ),
                wrap="wrap",
                gap="1rem",
                margin_top="1.25rem",
            ),
            on_close_auto_focus=rx.call_script(
                "document.getElementById("
                + PlanningState.navigation_focus.to_string()
                + ")?.focus()"
            ),
            max_width="min(28rem, calc(100vw - 2rem))",
            on_open_auto_focus=rx.set_focus("navigation-stay"),
            class_name="workspace-dialog",
        ),
        open=PlanningState.navigation_open,
        on_open_change=PlanningState.stay_navigation,
    )


def workspace_shell(content: rx.Component, *, active: str) -> rx.Component:
    return rx.box(
        rx.el.style("""
            .workspace { font-variant-numeric:tabular-nums; }
            .workspace :focus-visible { outline:3px solid #413b76; outline-offset:3px; }
            .workspace nav :focus-visible { outline-color:white; }
            .workspace-dialog :focus-visible { outline:3px solid #413b76; outline-offset:3px; }
            .workspace-drawer :focus-visible { outline:3px solid white; outline-offset:3px; }
            .workspace-dialog button, .workspace-drawer button { min-height:2.75rem; }
            .workspace ::selection { background:#d8d2f0; color:#173e3d; }
            .workspace button { min-height:2.75rem; white-space:normal; }
            .workspace input, .workspace select { max-width:100%; min-width:0; }
            .workspace .rt-TabsList { flex-wrap:wrap; height:auto; }
            .workspace .rt-TabsTrigger { min-height:2.75rem; }
            .workspace-nav-button:hover { background:#2c5656; }
            .workspace-nav-button[aria-current=page]:hover { background:#514886; }
            .workspace-nav-button:disabled { opacity:.6; }
            .workspace-skip { position:absolute; top:-8rem; left:1rem; z-index:100; }
            .workspace-skip:focus { top:1rem; background:white; padding:.75rem; }
            [data-vaul-overlay][data-state=closed], .workspace-drawer[data-state=closed] {
                pointer-events:none;
            }
            @media(prefers-reduced-motion:reduce) {
                /* Presence cleanup needs animationend even when motion is reduced. */
                *, *::before, *::after { animation-duration:.01ms!important;
                    animation-iteration-count:1!important; transition-duration:.01ms!important;
                    scroll-behavior:auto!important; }
                [data-vaul-overlay][data-state=closed], .workspace-drawer[data-state=closed] {
                    display:none;
                }
            }
        """),
        rx.el.a("Skip to workspace", href="#workspace-main", class_name="workspace-skip"),
        rx.box(
            rx.text("Procurement workspace", font_weight="650", margin_bottom="2rem"),
            _navigation(active),
            background=RAIL,
            color="white",
            padding="1.5rem 1rem",
            display=rx.breakpoints(initial="none", lg="block"),
            position="fixed",
            top="0",
            bottom="0",
            width="12rem",
            overflow_y="auto",
        ),
        rx.box(
            rx.flex(
                rx.text("Procurement workspace", font_weight="650"),
                rx.drawer.root(
                    rx.drawer.trigger(
                        rx.button(
                            "Workspace menu", id="workspace-menu", background=ACCENT, color="white"
                        ),
                        as_child=True,
                    ),
                    rx.drawer.portal(
                        rx.drawer.overlay(background="rgba(21,63,64,.35)"),
                        rx.drawer.content(
                            rx.drawer.title("Workspace navigation", margin_bottom="1rem"),
                            rx.drawer.description(
                                "Choose Cases or Open RFQs.", margin_bottom="1rem"
                            ),
                            _navigation(active, drawer=True),
                            rx.drawer.close(
                                rx.button("Close menu", id="drawer-close", margin_top="2rem"),
                                as_child=True,
                            ),
                            background=RAIL,
                            color="white",
                            padding="1.5rem",
                            width="min(20rem, 90vw)",
                            height="100%",
                            display="flex",
                            flex_direction="column",
                            align_items="stretch",
                            overflow_y="auto",
                            position="fixed",
                            left="0",
                            top="0",
                            bottom="0",
                            class_name="workspace-drawer",
                            on_close_auto_focus=rx.set_focus("workspace-menu"),
                            on_open_auto_focus=rx.call_script(
                                "document.querySelector('.workspace-drawer "
                                "button:not(:disabled)')?.focus()"
                            ),
                        ),
                    ),
                    direction="left",
                    open=PlanningState.drawer_open,
                    on_open_change=PlanningState.change_drawer,
                ),
                justify="between",
                align="center",
                wrap="wrap",
                gap="1rem",
                padding="1rem",
                background=RAIL,
                color="white",
                display=rx.breakpoints(initial="flex", lg="none"),
            ),
            rx.el.main(content, id="workspace-main", tab_index=-1, min_width="0"),
            margin_left=rx.breakpoints(initial="0", lg="12rem"),
            min_width="0",
        ),
        _discard_dialog(),
        class_name="workspace",
        background=PAPER,
        color=INK,
        min_height="100vh",
        font_family='Aptos, "Segoe UI Variable", "Segoe UI", sans-serif',
        overflow_wrap="anywhere",
    )
