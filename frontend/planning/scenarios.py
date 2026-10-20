"""Scenarios tab: base-versus-scenario comparison and the change composer."""

import reflex as rx

from frontend.planning.charts import scenario_chart
from frontend.planning.state import PlanningState
from frontend.planning.state_base import focus
from frontend.theme import ACCENT, HAIRLINE, MUTED
from frontend.ui import BUSY, card, heading, muted, t

CHILD = PlanningState.details["parent_id"] != "Base case"
_INPUT = {
    "width": "100%",
    "padding": "0.65rem",
    "border": f"1px solid {HAIRLINE}",
    "border_radius": "8px",
    "background": "white",
    "min_height": "2.75rem",
}


def _number_field(field: str, label: str, hint, *, mode="numeric", pattern="[0-9]{1,4}"):
    combined = PlanningState.scenario_kind == "combined"
    return rx.box(
        rx.el.label(t(label), html_for="stress-" + field, display="block", font_weight="550"),
        rx.el.input(
            id="stress-" + field,
            name=field,
            type="text",
            input_mode=mode,
            pattern=pattern if mode == "numeric" else None,
            max_length=4 if mode == "numeric" else 64,
            value=getattr(PlanningState, "stress_" + field),
            on_change=lambda value: PlanningState.update_stress(field, value),
            required=~combined,
            disabled=BUSY,
            **_INPUT,
        ),
        rx.text(hint, size="2", color=MUTED, margin_top="0.35rem"),
        flex="1",
        min_width="12rem",
    )


def _scenario_form() -> rx.Component:
    kind = PlanningState.scenario_kind
    combined = kind == "combined"
    return card(
        heading("scenario_new", size="4"),
        muted("scenario_new_body", margin_y="0.35rem", max_width="70ch"),
        rx.el.form(
            rx.grid(
                rx.box(
                    rx.el.label(
                        t("scenario_type"),
                        html_for="stress-kind",
                        display="block",
                        font_weight="550",
                    ),
                    rx.el.select(
                        *[
                            rx.el.option(t("kind_" + value), value=value)
                            for value in (
                                "supplier_outage",
                                "capacity_change",
                                "demand_change",
                                "price_change",
                                "combined",
                            )
                        ],
                        id="stress-kind",
                        name="kind",
                        value=kind,
                        on_change=PlanningState.change_scenario_kind,
                        disabled=BUSY,
                        **_INPUT,
                    ),
                ),
                rx.cond(
                    kind != "demand_change",
                    rx.box(
                        rx.el.label(
                            t("scenario_supplier"),
                            html_for="stress-supplier",
                            display="block",
                            font_weight="550",
                        ),
                        rx.el.select(
                            rx.el.option(t("choose_supplier"), value="", disabled=True),
                            rx.foreach(
                                PlanningState.scenario_suppliers,
                                lambda row: rx.el.option(row["name"], value=row["supplier"]),
                            ),
                            id="stress-supplier",
                            name="supplier",
                            value=PlanningState.stress_supplier,
                            on_change=PlanningState.select_stress_supplier,
                            required=True,
                            disabled=BUSY,
                            **_INPUT,
                        ),
                        rx.cond(
                            PlanningState.stress_supplier != "",
                            rx.text(
                                t("original_terms"),
                                ": ",
                                PlanningState.selected_terms["capacity"],
                                " ",
                                PlanningState.details["unit_label"],
                                " · ",
                                PlanningState.selected_terms["price_display"],
                                size="2",
                                color=MUTED,
                                margin_top="0.35rem",
                            ),
                        ),
                    ),
                ),
                columns=rx.breakpoints(initial="1", md="2"),
                gap="1rem",
                margin_top="0.75rem",
            ),
            rx.flex(
                rx.cond(
                    (kind == "demand_change") | combined,
                    _number_field(
                        "quantity",
                        "new_demand",
                        rx.text(
                            t("original_demand"),
                            ": ",
                            PlanningState.details["base_quantity_display"],
                        ),
                    ),
                ),
                rx.cond(
                    (kind == "capacity_change") | combined,
                    _number_field("capacity", "new_capacity", t("capacity_hint")),
                ),
                rx.cond(
                    (kind == "price_change") | combined,
                    _number_field("price", "new_price", t("price_hint"), mode="decimal"),
                ),
                gap="1rem",
                flex_wrap="wrap",
                margin_y="1rem",
            ),
            rx.cond(combined, muted("combined_hint", margin_bottom="1rem")),
            rx.box(
                rx.text(t("draft_title"), font_weight="650", size="2"),
                rx.text(
                    PlanningState.scenario_draft,
                    size="2",
                    white_space="pre-line",
                    margin_top="0.35rem",
                ),
                muted("draft_note", margin_top="0.5rem"),
                padding="0.85rem 1rem",
                background="#f6f9f7",
                border_radius="8px",
                margin_bottom="1rem",
            ),
            rx.cond(
                (PlanningState.error_message != "") & (PlanningState.error_target == "scenario"),
                rx.callout(
                    PlanningState.error_message,
                    color_scheme="red",
                    role="alert",
                    id="scenario-error",
                    tab_index=-1,
                    on_mount=focus("scenario-error"),
                    margin_bottom="1rem",
                ),
            ),
            rx.button(
                rx.cond(PlanningState.is_loading, rx.spinner(size="2"), rx.icon("play", size=16)),
                t("run_scenario"),
                type="submit",
                disabled=BUSY,
                size="3",
                background=ACCENT,
                color="white",
            ),
            on_submit=PlanningState.run_scenario.throttle(500),
            reset_on_submit=False,
        ),
    )


def _comparison() -> rx.Component:
    return card(
        rx.flex(
            rx.box(
                rx.text(t("saved_scenario"), size="2", color=MUTED),
                rx.heading(
                    PlanningState.details["scenario_label"],
                    as_="h2",
                    size="5",
                    id="scenario-result-heading",
                    tab_index=-1,
                ),
                rx.text(PlanningState.details["assumptions"], size="2", margin_top="0.25rem"),
            ),
            rx.button(
                rx.icon("arrow-left", size=16),
                t("back_to_base"),
                on_click=PlanningState.open_saved_case(
                    PlanningState.details["base_id"], "overview"
                ),
                disabled=BUSY,
                variant="outline",
            ),
            justify="between",
            align="start",
            gap="1rem",
            wrap="wrap",
        ),
        rx.cond(
            PlanningState.original_error != "",
            rx.flex(
                rx.callout(PlanningState.original_error, role="alert", color_scheme="red"),
                rx.button(
                    t("retry"),
                    on_click=PlanningState.retry_original,
                    disabled=BUSY,
                    variant="outline",
                ),
                gap="0.75rem",
                align="center",
                margin_top="1rem",
                wrap="wrap",
            ),
        ),
        rx.cond(
            PlanningState.details["comparison_display"] != "",
            rx.callout(
                PlanningState.details["comparison_display"],
                icon="info",
                size="1",
                margin_top="1rem",
            ),
        ),
        rx.grid(
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(""),
                            rx.table.column_header_cell(t("chart_base")),
                            rx.table.column_header_cell(t("chart_scenario")),
                            rx.table.column_header_cell(t("change")),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            PlanningState.scenario_metrics,
                            lambda row: rx.table.row(
                                rx.table.row_header_cell(row["metric"]),
                                rx.table.cell(row["base"]),
                                rx.table.cell(row["scenario"]),
                                rx.table.cell(row["change"], white_space="nowrap"),
                            ),
                        ),
                        rx.foreach(
                            PlanningState.scenario_allocation_rows,
                            lambda row: rx.table.row(
                                rx.table.row_header_cell(row["name"]),
                                rx.table.cell(row["base"]),
                                rx.table.cell(row["scenario"]),
                                rx.table.cell(row["change"]),
                            ),
                        ),
                    ),
                    variant="ghost",
                    size="1",
                    min_width="30rem",
                ),
                overflow_x="auto",
                role="region",
                aria_label=t("scenario_table"),
                tab_index=0,
                min_width="0",
            ),
            rx.box(
                rx.text(t("chart_scenario_title"), size="2", font_weight="650"),
                scenario_chart(),
                min_width="0",
            ),
            columns=rx.breakpoints(initial="1", lg="2"),
            gap="1.5rem",
            margin_top="1rem",
        ),
        rx.cond(
            PlanningState.plans.length() == 0,
            rx.callout(t("scenario_no_plan_body"), color_scheme="amber", margin_top="1rem"),
        ),
        muted("scenario_footnote", margin_top="1rem", max_width="75ch"),
    )


def _saved_scenario(row) -> rx.Component:
    return rx.flex(
        rx.box(
            rx.text(row["scenario"], font_weight="650", size="2"),
            rx.text(
                t("col_demand"),
                ": ",
                row["quantity"],
                " · ",
                row["outcome"],
                size="2",
                color=MUTED,
            ),
            min_width="0",
        ),
        rx.button(
            t("open_scenario"),
            on_click=PlanningState.open_saved_case(row["case_id"], "scenarios"),
            disabled=BUSY,
            size="2",
            variant="outline",
            flex_shrink="0",
        ),
        justify="between",
        align="center",
        gap="1rem",
        padding="0.6rem 0",
        border_top=f"1px solid {HAIRLINE}",
    )


def _saved_scenarios() -> rx.Component:
    """The base case's saved scenarios: a read-only GET, loaded when this tab opens."""
    # Nothing requested yet counts as loading, so the empty text never flashes before the GET.
    loading = PlanningState.base_scenarios_loading | (PlanningState.base_scenarios_case == "")
    return card(
        heading("saved_scenarios", size="4", id="base-scenarios-heading"),
        rx.grid(
            rx.foreach(PlanningState.base_scenarios, _saved_scenario),
            columns=rx.breakpoints(initial="1", lg="2"),
            column_gap="2rem",
        ),
        rx.cond(
            loading,
            rx.flex(
                rx.spinner(size="2"),
                rx.text(t("loading_scenarios"), size="2", color=MUTED),
                role="status",
                align="center",
                gap="0.5rem",
                padding="0.6rem 0",
            ),
            rx.cond(
                PlanningState.base_scenarios_error != "",
                rx.flex(
                    rx.callout(
                        PlanningState.base_scenarios_error,
                        role="alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.button(
                        t("retry"),
                        on_click=PlanningState.load_base_scenarios(False),
                        variant="outline",
                        size="2",
                    ),
                    gap="0.75rem",
                    align="center",
                    wrap="wrap",
                    margin_top="0.5rem",
                ),
                rx.cond(
                    PlanningState.base_scenarios.length() == 0,
                    muted("no_scenarios", padding="0.6rem 0"),
                    rx.cond(
                        PlanningState.base_scenarios_cursor != "",
                        rx.button(
                            t("more_scenarios"),
                            on_click=PlanningState.load_base_scenarios(True),
                            size="2",
                            variant="ghost",
                            margin_top="0.5rem",
                        ),
                    ),
                ),
            ),
        ),
        on_mount=PlanningState.load_base_scenarios(False),
    )


def scenarios_view() -> rx.Component:
    return rx.flex(
        rx.cond(
            CHILD,
            _comparison(),
            rx.fragment(
                rx.callout(t("scenarios_intro"), icon="info", size="1"),
                _saved_scenarios(),
            ),
        ),
        _scenario_form(),
        direction="column",
        gap="1rem",
    )
