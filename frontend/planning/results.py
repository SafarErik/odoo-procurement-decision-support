"""Procurement cockpit presentation components."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, INK, MUTED, SURFACE


def _allocation_bar(row: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.cond(
        row["quantity"] != "0",
        rx.box(
            rx.hstack(
                rx.text(row["name"], size="2"),
                rx.text(row["quantity"], font_weight="650"),
                justify="between",
            ),
            rx.box(
                rx.box(
                    width=row["share"] + "%",
                    height="0.4rem",
                    background=ACCENT,
                    border_radius="3px",
                ),
                background="#EEE8EF",
                margin_top="0.4rem",
                border_radius="3px",
            ),
            margin_bottom="0.85rem",
        ),
    )


def _recorded_plan(plan: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading(plan["label"], as_="h3", size="4"),
            rx.badge("Saved plan", color_scheme="gray"),
            justify="between",
        ),
        rx.text(
            plan["cost"], size="8", font_weight="650", letter_spacing="-0.04em", margin_top="1rem"
        ),
        rx.text(plan["premium_display"], color=MUTED, size="2", margin_bottom="1.5rem"),
        rx.text("Quantity by supplier", font_weight="600", size="2", margin_bottom="0.75rem"),
        rx.foreach(
            PlanningState.allocations,
            lambda row: rx.cond(row["plan"] == plan["label"], _allocation_bar(row)),
        ),
        rx.hstack(
            rx.text("Schedule-watch exposure", size="2"),
            rx.text(plan["exposure_display"], font_weight="650", color=INK),
            justify="between",
            margin_top="1.5rem",
        ),
        rx.el.details(
            rx.el.summary("What shapes this allocation?", cursor="pointer"),
            rx.text(plan["buyer_notes"], white_space="pre-line", size="2", margin_top="0.75rem"),
            margin_top="1.25rem",
        ),
        border=f"1px solid {HAIRLINE}",
        background=SURFACE,
        border_radius="0.75rem",
        padding=["1.25rem", "1.75rem"],
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
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        PlanningState.plans,
                        lambda plan: rx.table.row(
                            rx.table.cell(plan["number"], ". ", plan["label"]),
                            rx.table.cell(plan["cost"]),
                            rx.table.cell(plan["exposure_display"]),
                        ),
                    )
                ),
            ),
            overflow_x="auto",
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
                rx.cond(
                    PlanningState.details["decision_summary"] != "",
                    rx.callout(
                        PlanningState.details["decision_summary"],
                        color_scheme="blue",
                        margin_bottom="1rem",
                    ),
                ),
                rx.grid(
                    rx.foreach(PlanningState.plans, _recorded_plan),
                    columns=rx.breakpoints(initial="1", md="2"),
                    gap="1rem",
                    align_items="start",
                ),
                rx.text(
                    "Exposure is the quantity-weighted saved supplier score. Lower "
                    "means less simulated exposure; it is not a failure probability. "
                    "Exact values are in Audit.",
                    size="2",
                    color=MUTED,
                    margin_y="1rem",
                    max_width="75ch",
                ),
                _plan_tradeoff_chart(),
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
