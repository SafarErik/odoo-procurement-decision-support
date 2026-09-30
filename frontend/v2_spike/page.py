"""Compact case workspace composed exclusively from native Reflex components."""

import reflex as rx

from frontend.v2_spike.presentation import PlanView
from frontend.v2_spike.service import MODES
from frontend.v2_spike.state import OPERATIONS, SUPPLIERS
from frontend.v2_spike.state import CockpitState as S

INK = "#243B53"
MUTED = "#526978"
LINE = "#D8E3EA"
TEAL = "#0B7773"
CANVAS = "#F1F5F8"


def panel(*children, **props):
    return rx.box(
        *children,
        background="white",
        border=f"1px solid {LINE}",
        border_radius="8px",
        padding="1.25rem",
        **props,
    )


def section_title(title, detail=""):
    return rx.vstack(
        rx.heading(title, size="4", color=INK),
        rx.text(detail, size="2", color=MUTED),
        spacing="1",
        margin_bottom="1rem",
    )


def metric(label, value):
    return rx.vstack(
        rx.text(label, size="1", color=MUTED),
        rx.text(value, size="3", weight="medium", color=INK),
        spacing="1",
    )


def suppliers_panel():
    def row(s):
        return rx.table.row(
            rx.table.cell(rx.text(s.name, weight="medium"), rx.text(s.supplier_id, size="1")),
            rx.table.cell("€", s.unit_price),
            rx.table.cell(s.capacity),
            rx.table.cell(s.minimum_quantity),
            rx.table.cell(s.commitment),
            rx.table.cell(s.historical_indicator),
            rx.table.cell(
                rx.cond(
                    s.risk_score != None,  # noqa: E711
                    rx.vstack(
                        rx.text(s.risk_score, weight="medium"),
                        rx.text(s.predicted_class, size="1"),
                        spacing="1",
                    ),
                    rx.badge("Risk unavailable", color_scheme="gray"),
                )
            ),
            rx.table.cell(s.source_status),
        )

    def details(s):
        return rx.accordion.item(
            header=f"{s.name} · evaluation details",
            content=rx.vstack(
                rx.foreach(s.explanation, lambda text: rx.text(text, size="2")),
                spacing="2",
                align="stretch",
            ),
            value=s.supplier_id,
        )

    return panel(
        section_title(
            "Supplier evaluation", "Original case terms; scenario changes appear in Stress test."
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[
                            rx.table.column_header_cell(label)
                            for label in (
                                "Supplier",
                                "Unit price",
                                "Capacity",
                                "MOQ",
                                "Delivery condition",
                                "Prior schedule adherence",
                                "ML risk score",
                                "Data status",
                            )
                        ]
                    )
                ),
                rx.table.body(rx.foreach(S.suppliers, row)),
                size="2",
                width="100%",
            ),
            overflow_x="auto",
        ),
        rx.accordion.root(
            rx.foreach(S.suppliers, details),
            type="multiple",
            variant="outline",
            color_scheme="gray",
            margin_top="1rem",
        ),
        rx.text(
            "Scores are uncalibrated model outputs from a synthetic experiment. "
            "Predictive usefulness is not established.",
            size="1",
            color=MUTED,
            margin_top="0.8rem",
        ),
    )


def plan_card(plan: rx.Var[PlanView]):
    return rx.box(
        rx.hstack(
            rx.box(width="8px", height="8px", background=plan.color, border_radius="50%"),
            rx.heading(plan.title, size="3"),
            align="center",
        ),
        rx.text(plan.cost_display, font_size="1.65rem", weight="medium", margin_top="0.7rem"),
        rx.grid(
            metric("Cost premium", plan.premium_display),
            metric("ML exposure", plan.risk_display),
            metric("Largest share", plan.share_display),
            metric("Suppliers", plan.supplier_count),
            columns="2",
            gap="3",
            margin="0.8rem 0",
        ),
        rx.hstack(
            rx.badge("Feasible", color_scheme="teal"),
            rx.button(
                rx.cond(S.selected_id == plan.plan_id, "Selected", "Select plan"),
                on_click=S.select_plan(plan.plan_id),
                disabled=S.locked | S.busy,
                variant=rx.cond(S.selected_id == plan.plan_id, "solid", "outline"),
                color_scheme="teal",
                size="2",
            ),
            justify="between",
            align="center",
        ),
        padding="1rem",
        border=rx.cond(S.selected_id == plan.plan_id, f"2px solid {TEAL}", f"2px solid {LINE}"),
        border_radius="6px",
        background="white",
        width="100%",
    )


def tradeoff_chart():
    return panel(
        section_title("Cost and model-risk trade-off", "Click a point or use Select plan above."),
        rx.recharts.scatter_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke=LINE),
            rx.recharts.x_axis(
                data_key="cost",
                type_="number",
                name="Total cost",
                unit=" EUR",
                domain=["dataMin - 10", "dataMax + 10"],
            ),
            rx.recharts.y_axis(
                data_key="risk",
                type_="number",
                name="ML score exposure",
                domain=[0, 0.35],
                width=60,
            ),
            rx.recharts.tooltip(),
            rx.recharts.scatter(
                data=S.minimum_point,
                name="Minimum Cost",
                fill="#397BA6",
                shape="circle",
                on_click=S.select_plan("minimum"),
                is_animation_active=False,
            ),
            rx.recharts.scatter(
                data=S.balanced_point,
                name="Balanced",
                fill=TEAL,
                shape="diamond",
                on_click=S.select_plan("balanced"),
                is_animation_active=False,
            ),
            rx.recharts.scatter(
                data=S.lower_point,
                name="Lower-Risk",
                fill="#AF782B",
                shape="square",
                on_click=S.select_plan("lower"),
                is_animation_active=False,
            ),
            width="100%",
            height=240,
        ),
        rx.hstack(
            rx.text("Horizontal: total cost (EUR)", size="1"),
            rx.text("Vertical: weighted ML score exposure", size="1"),
            justify="between",
            color=MUTED,
            wrap="wrap",
        ),
    )


def allocation_panel():
    def allocation(a):
        return rx.table.row(
            rx.table.cell(
                rx.hstack(
                    rx.box(width="9px", height="9px", background=a.color),
                    rx.text(a.name),
                    align="center",
                )
            ),
            rx.table.cell(a.quantity),
            rx.table.cell(a.share, "%"),
        )

    return panel(
        section_title(S.selected.title, "Selected allocation and recorded explanation"),
        rx.recharts.bar_chart(
            rx.recharts.x_axis(type_="number", domain=[0, 100], unit="%"),
            rx.recharts.y_axis(type_="category", data_key="name", hide=True),
            rx.recharts.tooltip(),
            rx.recharts.bar(
                data_key="A",
                name="Northline",
                stack_id="allocation",
                fill="#397BA6",
                is_animation_active=False,
            ),
            rx.recharts.bar(
                data_key="B",
                name="Danube",
                stack_id="allocation",
                fill=TEAL,
                is_animation_active=False,
            ),
            rx.recharts.bar(
                data_key="C",
                name="Pannon",
                stack_id="allocation",
                fill="#AF782B",
                is_animation_active=False,
            ),
            data=S.allocation_data,
            layout="vertical",
            width="100%",
            height=110,
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Supplier"),
                    rx.table.column_header_cell("Quantity"),
                    rx.table.column_header_cell("Share"),
                )
            ),
            rx.table.body(rx.foreach(S.selected.allocations, allocation)),
            width="100%",
            size="2",
        ),
        rx.vstack(
            rx.foreach(S.selected.explanations, lambda text: rx.text(text, size="2")),
            spacing="2",
            align="stretch",
            margin_top="1rem",
        ),
    )


def plans_panel():
    return rx.vstack(
        rx.hstack(
            rx.heading("Procurement plans", size="4"),
            rx.badge(S.active_context, color_scheme="gray"),
            justify="between",
            wrap="wrap",
            width="100%",
        ),
        rx.cond(
            S.infeasible,
            panel(
                rx.callout(
                    "No feasible procurement plan exists under the selected conditions.",
                    icon="circle-alert",
                    color_scheme="red",
                ),
                rx.foreach(S.reasons, lambda text: rx.text(text, size="2", margin_top="0.5rem")),
                rx.text(
                    "Feasibility changed: yes. No allocation is returned.",
                    size="2",
                    margin_top="0.5rem",
                ),
            ),
            rx.cond(
                S.plans.length() > 0,
                rx.vstack(
                    rx.grid(
                        rx.foreach(S.plan_views, plan_card),
                        columns=rx.breakpoints(initial="1", lg="3"),
                        gap="3",
                        width="100%",
                    ),
                    tradeoff_chart(),
                    rx.cond(
                        S.has_selection,
                        allocation_panel(),
                        panel(
                            rx.text(
                                "No plan selected. Select an alternative to inspect allocations.",
                                color=MUTED,
                            )
                        ),
                    ),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                panel(
                    rx.text(
                        rx.cond(
                            S.running,
                            "Waiting for scenario results…",
                            "No procurement plans are available for this review.",
                        ),
                        color=MUTED,
                    )
                ),
            ),
        ),
        spacing="4",
        align="stretch",
        width="100%",
    )


def scenario_panel():
    return panel(
        section_title(
            "Stress test", "Compare a disruption with the original case under the same plan policy."
        ),
        rx.grid(
            rx.vstack(
                rx.text("Change", size="2", weight="medium"),
                rx.select(
                    list(OPERATIONS),
                    value=S.operation,
                    on_change=S.set_operation,
                    disabled=S.locked | S.busy,
                    width="100%",
                ),
                align="stretch",
            ),
            rx.vstack(
                rx.text("Affected supplier", size="2", weight="medium"),
                rx.select(
                    list(SUPPLIERS),
                    value=S.supplier_choice,
                    on_change=S.set_supplier_choice,
                    disabled=S.locked
                    | S.busy
                    | (S.operation == "Demand increased to 120")
                    | (S.operation == "Combined supply disruption"),
                    width="100%",
                ),
                align="stretch",
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            gap="3",
        ),
        rx.hstack(
            rx.button(
                "Run scenario",
                on_click=S.run_scenario,
                loading=S.running,
                disabled=S.locked | S.busy,
                color_scheme="teal",
            ),
            rx.button(
                "Restore original case",
                on_click=S.load_case,
                disabled=S.locked | S.busy,
                variant="outline",
                color_scheme="gray",
            ),
            margin_top="1rem",
            wrap="wrap",
        ),
        rx.text(S.active_context, size="2", weight="medium", margin_top="1rem"),
        rx.foreach(S.scenario_delta, lambda text: rx.text(text, size="2", margin_top="0.3rem")),
        rx.text(
            "Scenario outputs are fixed synthetic examples. Scores are not re-estimated "
            "for changed quantities.",
            size="1",
            color=MUTED,
            margin_top="0.8rem",
        ),
    )


def approval_panel():
    return panel(
        rx.heading("Human approval", size="4"),
        rx.badge(
            S.approval_label, color_scheme=rx.cond(S.locked, "teal", "gray"), margin="0.8rem 0"
        ),
        rx.cond(
            S.has_selection,
            rx.vstack(
                rx.text(S.selected.title, weight="medium"),
                rx.text(S.selected_view.cost_display),
                rx.text(S.active_context, size="2"),
                spacing="2",
                align="stretch",
            ),
            rx.text("Select and inspect a feasible plan before approval.", size="2", color=MUTED),
        ),
        rx.text("Approval note (optional)", size="2", margin_top="1rem"),
        rx.text_area(
            value=S.note,
            on_change=S.set_note,
            placeholder="Why this plan meets the requirement",
            disabled=S.locked | S.busy,
            max_length=500,
            width="100%",
            margin="0.4rem 0",
        ),
        rx.button(
            "Approve selected plan",
            on_click=S.approve_plan,
            loading=S.approving,
            disabled=~S.can_approve,
            color_scheme="teal",
            width="100%",
            margin_top="0.5rem",
        ),
        rx.cond(
            S.approval_error != "",
            rx.callout(S.approval_error, color_scheme="red", margin_top="0.8rem"),
        ),
        rx.cond(
            S.locked,
            rx.vstack(
                rx.callout(
                    "Approved. This review is now read-only.", color_scheme="teal", icon="check"
                ),
                rx.text(S.approved_summary, size="2"),
                rx.text("Snapshot ", S.approved_hash, size="1"),
                spacing="2",
                align="stretch",
                margin_top="1rem",
            ),
        ),
        rx.separator(margin="1rem 0"),
        rx.button(
            "Export PDF",
            on_click=S.export_pdf,
            disabled=~S.locked | S.busy,
            loading=S.exporting,
            variant="outline",
            color_scheme="teal",
            width="100%",
        ),
        rx.cond(
            S.pdf_message != "", rx.callout(S.pdf_message, color_scheme="gray", margin_top="0.8rem")
        ),
        rx.text(
            "Local prototype approval only. No purchase order or external action is created.",
            size="1",
            color=MUTED,
            margin_top="1rem",
        ),
        height="fit-content",
        position="sticky",
        top="1rem",
    )


def workspace():
    return rx.box(
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon("layers", size=22, color=TEAL),
                    rx.text("Procurement workspace", weight="medium"),
                    align="center",
                ),
                rx.hstack(
                    rx.badge("Synthetic prototype", color_scheme="amber"),
                    rx.link("RFQ ledger", href="/", size="2"),
                    align="center",
                ),
                justify="between",
                wrap="wrap",
                max_width="1380px",
                margin="auto",
            ),
            padding="1rem 2rem",
            border_bottom=f"1px solid {LINE}",
            background="white",
        ),
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("V2-DEMO-001", color=MUTED, size="2"),
                    rx.heading("DC-100 drive coupling", size="7"),
                    rx.text(
                        "Compare supply options. Review the trade-offs. Approve a plan.",
                        color=MUTED,
                        size="2",
                    ),
                    spacing="2",
                ),
                rx.button(
                    "Reload case",
                    on_click=S.load_case,
                    disabled=S.locked | S.busy,
                    variant="outline",
                    color_scheme="gray",
                ),
                justify="between",
                align="center",
                wrap="wrap",
                width="100%",
            ),
            rx.grid(
                metric("Original requirement · supplemental", S.case_quantity),
                metric("Product / UoM · contextual", "DC-100 / Units"),
                metric("Delivery · supplemental", "By 21 Oct 2026"),
                metric("Allocation policy", "≤ 2 suppliers / ≤ 80% each"),
                metric("Cost-premium policy", "Balanced 2% / lower-risk 5%"),
                columns=rx.breakpoints(initial="1", md="3", xl="5"),
                gap="4",
                padding="1rem 0",
                border_top=f"1px solid {LINE}",
                border_bottom=f"1px solid {LINE}",
                width="100%",
            ),
            rx.cond(
                S.loading | S.running,
                rx.hstack(rx.spinner(size="2"), rx.text("Loading case results…"), padding="1rem"),
            ),
            rx.cond(
                S.error != "",
                rx.callout(S.error, icon="circle-alert", color_scheme="red", width="100%"),
            ),
            rx.cond(
                S.case != None,  # noqa: E711
                rx.grid(
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Procurement plans", value="plans"),
                            rx.tabs.trigger("Supplier evaluation", value="suppliers"),
                            rx.tabs.trigger("Stress test", value="stress"),
                        ),
                        rx.tabs.content(plans_panel(), value="plans", padding_top="1rem"),
                        rx.tabs.content(suppliers_panel(), value="suppliers", padding_top="1rem"),
                        rx.tabs.content(
                            scenario_panel(),
                            plans_panel(),
                            value="stress",
                            padding_top="1rem",
                            display="flex",
                            flex_direction="column",
                            gap="1rem",
                        ),
                        default_value="plans",
                        width="100%",
                    ),
                    approval_panel(),
                    grid_template_columns=rx.breakpoints(initial="1fr", xl="minmax(0,1fr) 300px"),
                    gap="5",
                    width="100%",
                    align_items="start",
                ),
            ),
            rx.accordion.root(
                rx.accordion.item(
                    header="Prototype service states",
                    value="states",
                    content=rx.hstack(
                        rx.select(
                            list(MODES),
                            value=S.preview_mode,
                            on_change=S.set_preview_mode,
                            disabled=S.locked | S.busy,
                        ),
                        rx.text(
                            "Choose a state, then Reload case. Approval is session-local.",
                            size="1",
                            color=MUTED,
                        ),
                        align="center",
                        wrap="wrap",
                    ),
                ),
                type="single",
                variant="outline",
                color_scheme="gray",
                collapsible=True,
                width="100%",
            ),
            spacing="5",
            align="stretch",
            max_width="1380px",
            margin="auto",
            padding="2rem",
        ),
        background=CANVAS,
        color=INK,
        font_family='"Segoe UI", Aptos, sans-serif',
        min_height="100vh",
    )
