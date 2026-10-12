"""Recognizable, bounded saved work with scenarios expanded only on demand."""

import reflex as rx

from frontend.planning.state import PlanningState

INK = "#173e3d"
MUTED = "#536964"
PURPLE = "#413b76"


def _child(row):
    return rx.box(
        rx.heading(row["scenario"], as_="h4", size="3", text_transform="capitalize"),
        rx.text(row["context"], size="2"),
        rx.text(row["outcome"], font_weight="600"),
        rx.el.details(
            rx.el.summary("Changed assumptions"), rx.text(row["changes"], overflow_wrap="anywhere")
        ),
        rx.button(
            "Open scenario",
            on_click=PlanningState.open_saved_case(row["case_id"]),
            disabled=PlanningState.has_pending | PlanningState.is_loading,
            margin_top="0.75rem",
            variant="outline",
        ),
        padding="1rem",
        border_bottom="1px solid #d1ded6",
        width="100%",
    )


def _row(row):
    return rx.el.article(
        rx.flex(
            rx.box(
                rx.heading(row["product"], as_="h2", size="4", overflow_wrap="anywhere"),
                rx.text(row["context"], margin_top="0.35rem"),
                rx.text(
                    "Company ", row["company"], " · Saved ", row["saved"], size="2", color=MUTED
                ),
                rx.text(row["source"], size="2", color=MUTED),
                rx.text(
                    rx.cond(
                        row["workspace"] == "unclassified",
                        "Earlier case · Unclassified",
                        row["workspace"],
                    ),
                    size="2",
                    font_weight="600",
                ),
                min_width="0",
                flex="1",
            ),
            rx.box(
                rx.text(row["decision"], font_weight="650"),
                rx.text(row["outcome"], size="2", color=MUTED),
                rx.flex(
                    rx.button(
                        "Open case",
                        on_click=PlanningState.open_saved_case(row["case_id"]),
                        disabled=PlanningState.has_pending | PlanningState.is_loading,
                        background=PURPLE,
                        color="white",
                    ),
                    rx.button(
                        rx.cond(
                            PlanningState.expanded_case == row["case_id"],
                            "Hide scenarios",
                            "Show scenarios",
                        ),
                        on_click=PlanningState.expand_scenarios(row["case_id"], False),
                        disabled=PlanningState.children_loading | PlanningState.library_loading,
                        variant="outline",
                        aria_expanded=PlanningState.expanded_case == row["case_id"],
                    ),
                    wrap="wrap",
                    gap="0.5rem",
                    margin_top="0.75rem",
                ),
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            gap="1rem",
            width="100%",
        ),
        rx.el.details(
            rx.el.summary("Case reference"),
            rx.text(row["case_id"], size="2", overflow_wrap="anywhere"),
            rx.button(
                "Copy ID", size="1", variant="ghost", on_click=rx.set_clipboard(row["case_id"])
            ),
            margin_top="0.5rem",
            color=MUTED,
        ),
        rx.cond(
            PlanningState.expanded_case == row["case_id"],
            rx.box(
                rx.heading("Saved scenarios", as_="h3", size="3", margin_top="1rem"),
                rx.cond(
                    PlanningState.children_loading,
                    rx.text("Loading scenarios…", role="status"),
                    rx.cond(
                        PlanningState.children_error != "",
                        rx.text(PlanningState.children_error, role="alert"),
                        rx.cond(
                            PlanningState.library_children.length() == 0,
                            rx.text("No saved scenarios for this original case.", color=MUTED),
                            rx.foreach(PlanningState.library_children, _child),
                        ),
                    ),
                ),
                rx.cond(
                    PlanningState.children_cursor != "",
                    rx.button(
                        "Next scenarios",
                        on_click=PlanningState.expand_scenarios(row["case_id"], True),
                        disabled=PlanningState.children_loading,
                    ),
                ),
                background="#eff5f1",
                padding="0.75rem",
                margin_top="0.5rem",
            ),
        ),
        padding=["1rem", "1.5rem"],
        border_bottom="1px solid #d1ded6",
        background="white",
        width="100%",
    )


def library_page():
    return rx.box(
        rx.el.style("""
            .case-library { font-variant-numeric: tabular-nums; }
            .case-library :focus-visible { outline:3px solid #413b76; outline-offset:3px; }
            .case-library input, .case-library select { min-width:0; max-width:100%; }
            .case-library button { min-height:2.75rem; }
            .case-library summary { cursor:pointer; padding:.5rem 0; }
            .case-library ::selection { background:#d8d2f0; color:#173e3d; }
            @media(prefers-reduced-motion:reduce) {
                .case-library * { animation:none!important; transition:none!important; }
            }
        """),
        rx.flex(
            rx.text("Procurement workspace", font_weight="650"),
            rx.button(
                "Practice",
                on_click=PlanningState.open_practice,
                disabled=PlanningState.has_pending | PlanningState.is_loading,
                variant="soft",
                color="white",
                background="#413b76",
                style={"&:focus-visible": {"outline_color": "white"}},
            ),
            rx.link("Open RFQs", href="/", color="white"),
            justify="between",
            wrap="wrap",
            gap="1rem",
            background="#153f40",
            color="white",
            padding="1rem 1.5rem",
        ),
        rx.box(
            rx.flex(
                rx.box(
                    rx.heading(
                        "Saved cases", as_="h1", size="7", id="library-heading", tab_index=-1
                    ),
                    rx.text(
                        "Find a comparison. Reopen its saved result.",
                        color=MUTED,
                        margin_top="0.5rem",
                    ),
                ),
                rx.button(
                    "New comparison",
                    on_click=PlanningState.new_comparison,
                    disabled=PlanningState.has_pending | PlanningState.is_loading,
                    background=PURPLE,
                    color="white",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                gap="1rem",
                align="start",
            ),
            rx.text(
                "Earlier cases have no workspace classification. Source labels describe captured "
                "evidence; synthetic ML does not make a case Practice.",
                color=MUTED,
                max_width="72ch",
                margin_top="1rem",
            ),
            rx.form(
                rx.flex(
                    rx.box(
                        rx.el.label("Workspace", html_for="library-workspace"),
                        rx.el.select(
                            rx.el.option("Controlled work", value="controlled"),
                            rx.el.option("Practice", value="practice"),
                            rx.el.option("Earlier cases", value="unclassified"),
                            id="library-workspace",
                            name="workspace",
                            default_value=PlanningState.library_workspace,
                            key=PlanningState.library_workspace,
                            padding="0.65rem",
                            width="100%",
                        ),
                        min_width="0",
                    ),
                    rx.box(
                        rx.el.label("Decision status", html_for="library-status"),
                        rx.el.select(
                            *[
                                rx.el.option(label, value=value)
                                for label, value in [
                                    ("All decisions", "all"),
                                    ("Awaiting decision", "draft"),
                                    ("Approved", "approved"),
                                    ("No-award", "no_award"),
                                ]
                            ],
                            id="library-status",
                            name="status",
                            default_value=PlanningState.library_status,
                            key=PlanningState.library_status,
                            padding="0.65rem",
                            width="100%",
                        ),
                        min_width="0",
                    ),
                    rx.box(
                        rx.el.label("Product or case ID", html_for="library-search"),
                        rx.input(
                            id="library-search",
                            name="q",
                            max_length=80,
                            default_value=PlanningState.library_search,
                            key=PlanningState.library_search,
                            placeholder="Search saved identity",
                            width="100%",
                        ),
                        flex="1",
                        min_width="0",
                    ),
                    rx.button(
                        "Refresh",
                        type="submit",
                        disabled=PlanningState.library_loading,
                        background=PURPLE,
                        color="white",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    gap="1rem",
                    align="stretch",
                ),
                on_submit=PlanningState.refresh_library,
                margin="1.5rem 0",
            ),
            rx.cond(
                PlanningState.library_loading,
                rx.text("Loading saved cases…", role="status"),
                rx.cond(
                    PlanningState.library_error != "",
                    rx.text(PlanningState.library_error, role="alert", color="#92313b"),
                    rx.cond(
                        PlanningState.library_rows.length() > 0,
                        rx.foreach(PlanningState.library_rows, _row),
                        rx.cond(
                            PlanningState.library_loaded,
                            rx.box(
                                rx.heading("No saved cases in this view", as_="h2", size="4"),
                                rx.text(
                                    rx.cond(
                                        (PlanningState.library_search != "")
                                        | (PlanningState.library_status != "all"),
                                        "No matches. Change the filters and Refresh.",
                                        "Try Earlier cases for work saved before classification "
                                        "was available.",
                                    ),
                                    color=MUTED,
                                ),
                                padding="2rem 0",
                            ),
                        ),
                    ),
                ),
            ),
            rx.cond(
                PlanningState.library_cursor != "",
                rx.button(
                    "Next cases",
                    on_click=PlanningState.next_library_page,
                    disabled=PlanningState.library_loading,
                    margin_top="1rem",
                    variant="outline",
                ),
            ),
            max_width="72rem",
            margin="auto",
            padding=["1.25rem", "2rem"],
        ),
        class_name="case-library",
        min_height="100vh",
        background="#eff5f1",
        color=INK,
        overflow_wrap="anywhere",
    )
