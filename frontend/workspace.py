"""The frame around every page: green sidebar or phone bar with the menu drawer, the
HU/EN switch, the discard dialog and the global workspace CSS."""

from string import Template

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.planning.state_base import focus
from frontend.theme import (
    ACCENT,
    DRAWER_OVERLAY,
    FONT_BODY,
    INK,
    LANGUAGE_SWITCH,
    PAGE_MAX_WIDTH,
    PAGE_PADDING,
    PAPER,
    RADIUS_NAV,
    RAIL,
    RAIL_WIDTH,
    SIDE_COLUMN,
    SURFACE,
    TOKENS,
)
from frontend.ui import t

# Global workspace rules; $NAME placeholders are the tokens in frontend/theme.py.
_CSS = Template(
    """
.workspace { font-variant-numeric:tabular-nums; -webkit-tap-highlight-color:transparent; }
.workspace { --accent-9:$ACCENT; --accent-10:$ACCENT_HOVER; --accent-11:$ACCENT;
    --accent-a11:$ACCENT; --accent-a9:$ACCENT; --accent-a8:$ACCENT_A8;
    caret-color:$ACCENT; }
.workspace h1 { letter-spacing:-.025em; line-height:1.14; text-wrap:balance; }
.workspace h2, .workspace h3 { letter-spacing:-.015em; }
.workspace a { text-underline-offset:3px; }
.workspace button { touch-action:manipulation; }
.workspace button:not(:disabled):active { transform:scale(.98); }
.workspace button:disabled { cursor:not-allowed; }
.workspace .rt-TextFieldRoot:focus-within { outline:2px solid $ACCENT; outline-offset:2px; }
.workspace .rt-TableColumnHeaderCell { color:$MUTED; font-weight:550; }
.workspace .rt-TableCell, .workspace .rt-TableRowHeaderCell {
    padding-top:1rem; padding-bottom:1rem; }
.brand-mark { display:grid; place-items:center; width:2.8rem; height:2.8rem;
    flex-shrink:0; border:1px solid $BRAND_BORDER; border-radius:$RADIUS_TERMS;
    color:$BRAND_ICON; }
.workflow-steps { display:flex; gap:.7rem; overflow-x:auto; padding:1.2rem 0;
    margin-bottom:1rem; }
.workflow-step { flex-shrink:0; gap:.55rem; margin:0!important; padding:.35rem .65rem!important; }
.step-number { display:grid; place-items:center; width:1.8rem; height:1.8rem;
    border-radius:$RADIUS_STEP; border:1px solid $HAIRLINE; font-size:.8rem; flex-shrink:0; }
@media(max-width:600px) {
    .workflow-steps { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.4rem; }
    .workflow-step { justify-content:flex-start; }
}
.workspace .decision-summary { border-top:3px solid $ACCENT; }
@media (hover:hover) and (pointer:fine) {
    .workspace button { transition:background-color 140ms ease, border-color 140ms ease; }
}
.workspace :focus-visible { outline:3px solid $ACCENT; outline-offset:3px; }
.workspace .rail :focus-visible, .workspace-drawer :focus-visible { outline-color:$SURFACE; }
.workspace-dialog :focus-visible { outline:3px solid $ACCENT; outline-offset:3px; }
.workspace button { min-height:$TOUCH_TARGET; white-space:normal; }
.workspace input, .workspace select, .workspace textarea { max-width:100%; min-width:0;
    font-size:max(16px, 1rem); }
.workspace .rt-TabsList { flex-wrap:nowrap; overflow-x:auto; height:auto; scrollbar-width:none; }
.workspace .rt-TabsTrigger { min-height:$TOUCH_TARGET; flex-shrink:0; }
.workspace summary { cursor:pointer; padding:.5rem 0; }
.workspace ::selection { background:$TEXT_SELECTION; color:$INK; }
.nav-item { display:flex; align-items:center; gap:.65rem; width:100%; color:$SURFACE;
    background:transparent; border:0; border-radius:$RADIUS_NAV; padding:.65rem .75rem;
    font:inherit; cursor:pointer; text-align:left; min-height:$TOUCH_TARGET; }
.nav-item:hover { background:$NAV_HOVER; }
.nav-item[aria-current=page] { background:$PAPER; color:$RAIL; font-weight:650; }
.nav-item:disabled { opacity:.6; cursor:not-allowed; }
/* Headings and messages take focus programmatically (tabindex=-1); keyboard users never
   tab to them, so the focus ring would only add noise after each navigation. */
.workspace [tabindex="-1"]:focus { outline:none; }
.workspace .lang-switch button { min-height:0; }
.sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0);
    white-space:nowrap; }
.case-row { cursor:pointer; }
.case-row:hover { background:$SUBTLE; }
.case-row[data-selected=true] { background:$SELECTED; }
.workspace-skip { position:absolute; top:-8rem; left:1rem; z-index:100; }
.workspace-skip:focus { top:1rem; background:$SURFACE; padding:.75rem; }
[data-vaul-overlay][data-state=closed], .workspace-drawer[data-state=closed] {
    pointer-events:none; }
@media (hover:none) { .nav-item:hover, .case-row:hover { background:inherit; } }
@media(prefers-reduced-motion:reduce) {
    /* Presence cleanup needs animationend even when motion is reduced. */
    *, *::before, *::after { animation-duration:.01ms!important;
        animation-iteration-count:1!important; transition-duration:.01ms!important;
        scroll-behavior:auto!important; }
    [data-vaul-overlay][data-state=closed], .workspace-drawer[data-state=closed] {
        display:none; }
}
"""
).substitute(TOKENS)


def _navigation(active: str, *, drawer: bool = False):
    """The three destinations (Home, Cases, New procurement); the current one is highlighted."""
    return rx.el.nav(
        *[
            rx.el.button(
                rx.icon(icon, size=18),
                t(label),
                id=("drawer-" if drawer else "nav-") + destination,
                on_click=PlanningState.navigate_global(destination),
                aria_current="page" if active == destination else "false",
                disabled=PlanningState.has_pending | PlanningState.is_loading,
                class_name="nav-item",
            )
            for destination, label, icon in (
                ("home", "nav_home", "house"),
                ("cases", "nav_cases", "folder-open"),
                ("rfqs", "new_procurement", "file-text"),
            )
        ],
        aria_label=t("nav_label"),
        display="flex",
        flex_direction="column",
        gap="0.35rem",
    )


def language_switch(*, dark: bool = True):
    """The HU/EN segmented switch; relabels the screen without a server request."""
    return rx.box(
        rx.segmented_control.root(
            rx.segmented_control.item("HU", value="hu"),
            rx.segmented_control.item("EN", value="en"),
            value=PlanningState.lang,
            on_change=PlanningState.set_language,
            size="1",
            aria_label=t("language"),
        ),
        class_name="lang-switch",
        color_scheme="gray",
        background=LANGUAGE_SWITCH if dark else "transparent",
        border_radius=RADIUS_NAV,
        width="fit-content",
    )


def _discard_dialog():
    """The "discard unsaved input?" dialog shown before leaving a dirty wizard or scenario."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(t("discard_title")),
            rx.alert_dialog.description(t("discard_body")),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(
                        t("stay"),
                        id="navigation-stay",
                        on_click=PlanningState.stay_navigation(False),
                    ),
                    as_child=True,
                ),
                rx.alert_dialog.action(
                    rx.button(
                        t("discard"), variant="outline", on_click=PlanningState.discard_navigation
                    ),
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
            on_open_auto_focus=focus("navigation-stay"),
            max_width="min(28rem, calc(100vw - 2rem))",
            class_name="workspace-dialog",
        ),
        open=PlanningState.navigation_open,
        on_open_change=PlanningState.stay_navigation,
    )


def _brand():
    """App name with its mark and the "Odoo 19" line, on the rail and the phone bar."""
    return rx.flex(
        rx.box(rx.icon("git-compare-arrows", size=23), class_name="brand-mark"),
        rx.box(
            rx.text(t("app_name"), font_weight="650", line_height="1.25"),
            rx.text("Odoo 19", size="1", opacity="0.8", margin_top="0.35rem"),
        ),
        gap="0.75rem",
        align="center",
    )


def _menu_drawer(active: str):
    """Phone menu: the purple menu button and the green left drawer with the navigation."""
    return rx.drawer.root(
        rx.drawer.trigger(
            rx.icon_button(
                rx.icon("menu", size=20),
                id="workspace-menu",
                aria_label=t("menu"),
                title=t("menu"),
                background=ACCENT,
                color=SURFACE,
                size="3",
            ),
            as_child=True,
        ),
        rx.drawer.portal(
            rx.drawer.overlay(background=DRAWER_OVERLAY),
            rx.drawer.content(
                rx.drawer.title(t("nav_label"), margin_bottom="1rem"),
                _navigation(active, drawer=True),
                rx.drawer.close(
                    rx.button(t("close_menu"), id="drawer-close", margin_top="2rem"),
                    as_child=True,
                ),
                background=RAIL,
                color=SURFACE,
                padding="1.5rem",
                width=f"min({SIDE_COLUMN}, 85vw)",
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
                on_close_auto_focus=focus("workspace-menu"),
                on_open_auto_focus=rx.call_script(
                    "document.querySelector('.workspace-drawer button:not(:disabled)')?.focus()"
                ),
            ),
        ),
        direction="left",
        open=PlanningState.drawer_open,
        on_open_change=PlanningState.change_drawer,
    )


def _mobile_bar(active: str):
    """Sticky green top bar below the lg breakpoint: brand, language switch, menu."""
    return rx.flex(
        rx.box(_brand(), min_width="0", flex="1"),
        rx.flex(
            language_switch(),
            _menu_drawer(active),
            gap="0.5rem",
            align="center",
            flex_shrink="0",
        ),
        justify="between",
        align="center",
        gap="1rem",
        padding="0.75rem 1rem",
        padding_top="max(0.75rem, env(safe-area-inset-top))",
        background=RAIL,
        color=SURFACE,
        display=rx.breakpoints(initial="flex", lg="none"),
        position="sticky",
        top="0",
        z_index="10",
    )


def _rail(active: str):
    """Fixed green sidebar from the lg breakpoint: brand, navigation, language switch."""
    return rx.flex(
        _brand(),
        _navigation(active),
        rx.box(flex="1"),
        language_switch(),
        direction="column",
        gap="2rem",
        class_name="rail",
        background=RAIL,
        color=SURFACE,
        padding="1.5rem 1rem",
        display=rx.breakpoints(initial="none", lg="flex"),
        position="fixed",
        top="0",
        bottom="0",
        width=RAIL_WIDTH,
        overflow_y="auto",
    )


def workspace_shell(content: rx.Component, *, active: str) -> rx.Component:
    """Every page's frame: skip link, rail or phone bar, the main region and the dialog."""
    return rx.box(
        rx.el.style(_CSS),
        rx.el.a(t("skip"), href="#workspace-main", class_name="workspace-skip"),
        _rail(active),
        rx.box(
            _mobile_bar(active),
            rx.el.main(content, id="workspace-main", tab_index=-1, min_width="0"),
            margin_left=rx.breakpoints(initial="0", lg=RAIL_WIDTH),
            min_width="0",
        ),
        _discard_dialog(),
        class_name="workspace",
        background=PAPER,
        color=INK,
        min_height="100dvh",
        font_family=FONT_BODY,
        overflow_wrap="anywhere",
        lang=PlanningState.lang,
    )


def page_frame(*children, **props):
    """Centred page column with the responsive page padding; ``props`` override the style."""
    style = {
        "max_width": PAGE_MAX_WIDTH,
        "margin": "0 auto",
        "padding": PAGE_PADDING,
        "min_width": "0",
        "width": "100%",
    }
    style.update(props)
    return rx.box(*children, **style)
