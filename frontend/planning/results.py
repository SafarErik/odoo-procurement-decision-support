"""Procurement cockpit presentation components."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, MUTED, SURFACE


def _selection_button(plan):
    return rx.button(
        rx.cond(
            PlanningState.selected_plan.get("label", "") == plan["label"],
            rx.cond(
                PlanningState.details["final_outcome"] == "Approved",
                "Approved plan",
                "Selected for review",
            ),
            "Select for review",
        ),
        aria_label="Select " + plan["label"] + " for review",
        aria_pressed=PlanningState.selected_plan.get("label", "") == plan["label"],
        on_click=PlanningState.choose_final_plan(plan["label"]),
        disabled=PlanningState.has_pending
        | PlanningState.is_loading
        | (PlanningState.details["final_outcome"] != ""),
        variant="outline",
        color=ACCENT,
        width="100%",
        margin_top="0.75rem",
    )


def _plan_notes(plan):
    return rx.el.details(
        rx.el.summary("What shapes this allocation?", cursor="pointer"),
        rx.text(plan["buyer_notes"], white_space="pre-line", size="2", margin_top="0.75rem"),
        rx.text(plan["explanations"], white_space="pre-line", size="2", margin_top="0.75rem"),
    )


def _metric(label, *content):
    return rx.box(
        rx.text(label, size="2", color=MUTED, margin_bottom="0.35rem"),
        *content,
        margin_top="1rem",
    )


def _recorded_plan(plan: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.el.section(
        rx.heading(plan["label"], as_="h3", size="5"),
        _selection_button(plan),
        _metric("Total cost", rx.text(plan["cost"], size="7", font_weight="650")),
        _metric(
            "Above minimum cost",
            rx.text(plan["premium_absolute"], font_weight="650"),
            rx.text(plan["premium_display"], size="2"),
            rx.text("Exact relative premium: ", plan["premium_exact"], size="2"),
        ),
        _metric(
            "Quantity by supplier",
            rx.foreach(
                PlanningState.allocations,
                lambda row: rx.cond(
                    row["plan"] == plan["label"],
                    rx.box(
                        rx.flex(
                            rx.text(row["name"], size="2", flex="1", min_width="0"),
                            rx.text(
                                row["quantity"],
                                " ",
                                PlanningState.details["unit"],
                                font_weight="650",
                            ),
                            gap="1rem",
                            wrap="wrap",
                            justify="between",
                        ),
                        rx.text("Promised ", row["promised"], size="1", color=MUTED),
                        border_bottom=f"1px solid {HAIRLINE}",
                        padding_y="0.5rem",
                    ),
                ),
            ),
            rx.text(
                "Demand covered: ",
                PlanningState.details["quantity"],
                " ",
                PlanningState.details["unit"],
                size="2",
                margin_top="0.5rem",
            ),
        ),
        _metric(
            "Synthetic model exposure",
            rx.text(plan["exposure_exact"], font_weight="650"),
            rx.text("Approximate scale: ", plan["exposure_display"], size="2"),
        ),
        rx.box(_plan_notes(plan), margin_top="1rem"),
        background=rx.cond(
            PlanningState.selected_plan.get("label", "") == plan["label"],
            "#f1eff8",
            SURFACE,
        ),
        border=f"1px solid {HAIRLINE}",
        padding="1.25rem",
        margin_bottom="1rem",
    )


def _plan_cell(plan, *content):
    return rx.table.cell(
        *content,
        background=rx.cond(
            PlanningState.selected_plan.get("label", "") == plan["label"],
            "#f1eff8",
            SURFACE,
        ),
        vertical_align="top",
        padding="1rem",
    )


def _comparison_table():
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Saved plan comparison", min_width="12rem"),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: rx.table.column_header_cell(
                            rx.heading(plan["label"], as_="h3", size="5"),
                            rx.text("Saved plan index ", plan["index"], size="1", color=MUTED),
                            _selection_button(plan),
                            min_width="16rem",
                            vertical_align="top",
                            padding="1rem",
                            background=rx.cond(
                                PlanningState.selected_plan.get("label", "") == plan["label"],
                                "#f1eff8",
                                SURFACE,
                            ),
                        ),
                    ),
                ),
            ),
            rx.table.body(
                rx.table.row(
                    rx.table.row_header_cell("Total cost"),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: _plan_cell(
                            plan, rx.text(plan["cost"], size="7", font_weight="650")
                        ),
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Above minimum cost"),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: _plan_cell(
                            plan,
                            rx.text(plan["premium_absolute"], font_weight="650"),
                            rx.text(plan["premium_display"], size="2"),
                            rx.text("Exact relative premium: ", plan["premium_exact"], size="2"),
                        ),
                    ),
                ),
                rx.foreach(
                    PlanningState.scenario_suppliers,
                    lambda supplier: rx.table.row(
                        rx.table.row_header_cell(
                            supplier["name"],
                            rx.text("Promised ", supplier["saved_date"], size="1", color=MUTED),
                            rx.text(supplier["saved_available"], size="1", color=MUTED),
                        ),
                        rx.foreach(
                            PlanningState.plans,
                            lambda plan: _plan_cell(
                                plan,
                                rx.foreach(
                                    PlanningState.allocations,
                                    lambda row: rx.cond(
                                        (row["plan"] == plan["label"])
                                        & (row["supplier"] == supplier["supplier"]),
                                        rx.text(
                                            row["quantity"],
                                            " ",
                                            PlanningState.details["unit"],
                                            font_weight="650",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Demand covered"),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: _plan_cell(
                            plan,
                            rx.text(
                                PlanningState.details["quantity"],
                                " ",
                                PlanningState.details["unit"],
                            ),
                        ),
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Synthetic model exposure"),
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: _plan_cell(
                            plan,
                            rx.text(plan["exposure_exact"], font_weight="650"),
                            rx.text("Approximate scale: ", plan["exposure_display"], size="2"),
                        ),
                    ),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Constraints and delivery"),
                    rx.foreach(
                        PlanningState.plans, lambda plan: _plan_cell(plan, _plan_notes(plan))
                    ),
                ),
            ),
            width="100%",
        ),
        role="region",
        aria_label="Aligned saved plan comparison",
        tab_index=0,
        overflow_x="auto",
        width="100%",
        display=rx.breakpoints(initial="none", md="block"),
    )


def _plan_tradeoff_chart() -> rx.Component:
    return rx.box(
        rx.heading("The cost–exposure trade-off", as_="h2", size="4"),
        rx.text(
            "Each point is a saved plan for the same demand. Left costs less; lower means "
            "less exposure in this simulation. Exposure is not a failure probability.",
            color=MUTED,
            size="2",
            max_width="72ch",
            margin_top="0.5rem",
        ),
        rx.box(
            *[
                rx.box(
                    rx.text(
                        label,
                        white_space="nowrap",
                        position="absolute",
                        right="100%",
                        padding_right="0.5rem",
                        transform="translateY(-50%)",
                        size="1",
                        color=MUTED,
                    ),
                    position="absolute",
                    top=top,
                    width="100%",
                    border_top=f"1px solid {HAIRLINE}",
                )
                for label, top in (("100", "10%"), ("50", "50%"), ("0", "90%"))
            ],
            rx.foreach(
                PlanningState.plans,
                lambda plan: rx.box(
                    plan["number"],
                    position="absolute",
                    left=plan["chart_x"],
                    top=plan["chart_y"],
                    transform="translate(-50%, -50%)",
                    width="1.75rem",
                    height="1.75rem",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    border_radius="50%",
                    background=ACCENT,
                    color=SURFACE,
                    font_size="0.8rem",
                    font_weight="650",
                    title=plan["label"] + ": " + plan["cost"] + "; " + plan["exposure_display"],
                ),
            ),
            position="relative",
            height="10rem",
            margin_left="2rem",
            margin_right="1rem",
            margin_top="1rem",
            role="img",
            aria_label="Saved plan cost versus exposure plot. Exact values follow.",
        ),
        rx.flex(
            rx.text(PlanningState.details["chart_min_cost"], size="2"),
            rx.text(PlanningState.details["chart_max_cost"], size="2"),
            justify="between",
            gap="1rem",
            flex_wrap="wrap",
            margin_left="2rem",
            margin_right="1rem",
        ),
        rx.text(
            rx.cond(
                PlanningState.details["chart_min_cost"] == PlanningState.details["chart_max_cost"],
                "All shown plans have the same total cost",
                "Total cost; axis spans the saved plan costs",
            ),
            size="1",
            color=MUTED,
            text_align="center",
            margin_y="0.75rem",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Point / plan"),
                        rx.table.column_header_cell("Total cost"),
                        rx.table.column_header_cell("Exposure / 100"),
                        rx.table.column_header_cell("Exact exposure"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: rx.table.row(
                            rx.table.cell(plan["number"], ". ", plan["label"]),
                            rx.table.cell(plan["cost"]),
                            rx.table.cell(plan["exposure_display"]),
                            rx.table.cell(plan["exposure_exact"]),
                        ),
                    )
                ),
            ),
            overflow_x="auto",
            role="region",
            aria_label="Saved plan chart values",
            tab_index=0,
            width="100%",
        ),
        rx.text(
            "Plot positions are approximate. Exact costs and exposure fractions are "
            "available in the saved plan details.",
            size="1",
            color=MUTED,
            margin_top="0.75rem",
        ),
        width="100%",
    )


def _recorded_assessment(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["name"], font_weight="650"),
                rx.text(row["history_summary"], color=MUTED, size="2"),
            ),
            rx.box(
                rx.badge(
                    row["class_label"], color_scheme=rx.cond(row["class"] == "0", "teal", "amber")
                ),
                rx.text("Exposure ", row["score_display"], size="2", margin_top="0.3rem"),
            ),
            justify="between",
            gap="1rem",
            flex_wrap="wrap",
        ),
        rx.el.details(
            rx.el.summary("How did the tree classify this supplier?", cursor="pointer"),
            rx.text("History window: ", row["history_window"], size="2", margin_top="0.75rem"),
            rx.text(
                "These conditions trace the saved model's branches. They are not receipt records.",
                size="2",
                color=MUTED,
            ),
            rx.text(
                row["readable_path"],
                white_space="pre-line",
                size="2",
                margin_y="0.75rem",
                line_height="1.8",
            ),
            rx.text("Result: ", row["class_label"], font_weight="650", size="2"),
            rx.text(
                "Thresholds above are rounded for reading. Exact branches and model "
                "identity follow.",
                size="1",
                color=MUTED,
            ),
            rx.el.details(
                rx.el.summary("Exact tree record", cursor="pointer"),
                rx.text(row["path"], white_space="pre-line", size="1", margin_y="0.75rem"),
                rx.text("Exact supplier ID: ", row["supplier"], size="2"),
                rx.text("Recorded class: ", row["class"], " · Score: ", row["score"], size="2"),
                rx.text("Recorded validity end: ", row["valid_until"], size="2"),
                rx.text("Recorded score applicability: ", row["quantity_range"], size="2"),
                rx.text(
                    "Synthetic history reference: ",
                    row["source"],
                    size="2",
                    overflow_wrap="anywhere",
                ),
                rx.text("Model: ", row["model"], size="2", overflow_wrap="anywhere"),
            ),
            margin_top="0.75rem",
        ),
        padding_y="1.25rem",
        border_bottom=f"1px solid {HAIRLINE}",
    )


def _recorded_sources(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["field"]),
        rx.table.cell(row["type"]),
        rx.table.cell(row["reference"]),
        rx.table.cell(row["observed_at"]),
    )


def plans_view() -> rx.Component:
    return rx.vstack(
        rx.cond(
            PlanningState.plans.length() > 0,
            rx.box(
                rx.heading("Your allocation options", as_="h2", size="5", margin_bottom="0.5rem"),
                rx.text(
                    "Same product · same ",
                    PlanningState.details["quantity"],
                    " ",
                    PlanningState.details["unit"],
                    " demand. Selection does not save or approve.",
                    size="2",
                    color=MUTED,
                    margin_bottom="1rem",
                ),
                rx.cond(
                    PlanningState.details["decision_summary"] != "",
                    rx.text(
                        PlanningState.details["decision_summary"],
                        size="2",
                        color=MUTED,
                        max_width="75ch",
                        margin_bottom="1rem",
                    ),
                ),
                _comparison_table(),
                rx.box(
                    rx.foreach(PlanningState.plans, _recorded_plan),
                    display=rx.breakpoints(initial="block", md="none"),
                ),
                rx.text(
                    "Exposure is the quantity-weighted saved supplier score. Lower "
                    "means less simulated exposure; it is not a failure probability. "
                    "Exact fractions are shown above and retained in Audit.",
                    size="2",
                    color=MUTED,
                    margin_y="1rem",
                    max_width="75ch",
                ),
                rx.cond(
                    PlanningState.details["status"] != "optimal",
                    rx.callout(
                        "Comparison is incomplete. Only retained proven plans are shown; "
                        "the saved solver outcome is available in Audit.",
                        color_scheme="amber",
                    ),
                ),
                rx.el.details(
                    rx.el.summary("Cost–exposure chart and exact values", cursor="pointer"),
                    _plan_tradeoff_chart(),
                    margin_y="1rem",
                ),
                width="100%",
            ),
            rx.callout(
                rx.cond(
                    PlanningState.details["status"] == "infeasible",
                    "These constraints cannot meet demand. Review the saved limits in "
                    "Audit, or compare the scenario with its original base in What-if. "
                    "No allocations or costs have been invented.",
                    "No proven result is available. Check the saved status and "
                    "diagnostics in Audit; this does not establish infeasibility.",
                ),
                color_scheme="amber",
            ),
        ),
        rx.cond(
            PlanningState.details["alternative_notice"] != "",
            rx.callout(PlanningState.details["alternative_notice"], color_scheme="gray"),
        ),
        align="stretch",
        spacing="4",
        width="100%",
    )


def suppliers_view() -> rx.Component:
    return rx.box(
        rx.heading("Why these supplier assessments?", as_="h2", size="4"),
        rx.text(
            "The saved Decision Tree classifies each supplier from its prior "
            "on-time delivery rate and completed-receipt count. The branch "
            "sequence explains the classification; it does not prove why a "
            "delivery was late.",
            size="2",
            color=MUTED,
            max_width="75ch",
            margin_y="0.75rem",
        ),
        rx.callout(
            "Synthetic history. These percentages describe generated receipts, "
            "including for Odoo suppliers. They are not performance measured "
            "from your Odoo database.",
            color_scheme="amber",
        ),
        rx.foreach(PlanningState.assessments, _recorded_assessment),
        rx.el.details(
            rx.el.summary("What was the model trained on?", font_weight="650", cursor="pointer"),
            rx.text(
                "Offline generated receipt histories with two features: on-time "
                "delivery rate and completed-receipt count. The label is Schedule "
                "watch when at least two of five completed receipts in the next 30 "
                "days are late; otherwise Schedule regular.",
                size="2",
                margin_y="0.75rem",
                max_width="75ch",
            ),
            rx.text(
                "Training and held-out examples use separate suppliers and a time "
                "boundary. Future outcomes form labels, never input features. The "
                "saved leaf's class-1 training support supplies the exposure score; "
                "it is uncalibrated, not a forecast probability.",
                size="2",
                color=MUTED,
                max_width="75ch",
            ),
            rx.text(
                "Observed Odoo training requires a documented dataset, available-at "
                "cutoffs, complete outcome labels and separate evaluation. Mock "
                "data entered in Odoo remains synthetic evidence.",
                size="2",
                color=MUTED,
                max_width="75ch",
                margin_top="0.75rem",
            ),
        ),
        width="100%",
    )
