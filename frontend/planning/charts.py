"""Recharts views of stored values; every chart has a table or text equivalent nearby."""

import reflex as rx

from frontend.planning.state import PlanningState
from frontend.theme import GRID, MUTED, SERIES_1, SERIES_2
from frontend.ui import t

_TICK = {"fill": MUTED, "fontSize": 12}
_TOOLTIP = {
    "content_style": {"borderRadius": "8px", "border": "1px solid #d1ded6", "fontSize": "13px"},
}


def cost_exposure_chart() -> rx.Component:
    """Each saved plan as a point: total cost (x) against risk exposure 0–100 (y)."""
    return rx.box(
        rx.recharts.scatter_chart(
            rx.recharts.cartesian_grid(stroke=GRID, stroke_dasharray="3 3"),
            rx.recharts.x_axis(
                data_key="cost",
                type_="number",
                name=t("chart_cost"),
                domain=["auto", "auto"],
                tick=_TICK,
                stroke=GRID,
            ),
            rx.recharts.y_axis(
                data_key="exposure",
                type_="number",
                name=t("chart_exposure"),
                domain=[0, 100],
                tick=_TICK,
                stroke=GRID,
                width=40,
            ),
            rx.recharts.graphing_tooltip(**_TOOLTIP),
            rx.recharts.legend(icon_type="circle", vertical_align="bottom"),
            rx.recharts.scatter(
                data=PlanningState.chart_minimum,
                name=t("plan_minimum"),
                fill=SERIES_1,
                shape="circle",
            ),
            rx.recharts.scatter(
                data=PlanningState.chart_alternatives,
                name=t("chart_alternatives"),
                fill=SERIES_2,
                shape="diamond",
            ),
            width="100%",
            height=260,
            margin={"top": 10, "right": 16, "bottom": 0, "left": 0},
        ),
        role="img",
        aria_label=t("chart_tradeoff_aria"),
        width="100%",
        min_width="0",
    )


def scenario_chart() -> rx.Component:
    """Minimum-cost quantity per supplier: original base versus the saved scenario."""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke=GRID, vertical=False),
            rx.recharts.x_axis(data_key="name", tick=_TICK, stroke=GRID, interval=0),
            rx.recharts.y_axis(tick=_TICK, stroke=GRID, width=40, allow_decimals=False),
            rx.recharts.graphing_tooltip(**_TOOLTIP),
            rx.recharts.legend(icon_type="square", vertical_align="bottom"),
            rx.recharts.bar(
                data_key="base", name=t("chart_base"), fill=SERIES_1, radius=[4, 4, 0, 0]
            ),
            rx.recharts.bar(
                data_key="scenario",
                name=t("chart_scenario"),
                fill=SERIES_2,
                radius=[4, 4, 0, 0],
            ),
            data=PlanningState.scenario_chart,
            width="100%",
            height=260,
            bar_gap=2,
            margin={"top": 10, "right": 8, "bottom": 0, "left": 0},
        ),
        role="img",
        aria_label=t("chart_scenario_aria"),
        width="100%",
        min_width="0",
    )


def kpi_chart(feature: str, title: str, unit: str) -> rx.Component:
    """One KPI compared across the case's suppliers (single series, so no legend)."""
    return rx.box(
        rx.text(t(title), size="2", font_weight="650"),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke=GRID, horizontal=False),
            rx.recharts.x_axis(type_="number", tick=_TICK, stroke=GRID, unit=unit),
            rx.recharts.y_axis(
                data_key="name", type_="category", tick=_TICK, stroke=GRID, width=110
            ),
            rx.recharts.graphing_tooltip(**_TOOLTIP),
            rx.recharts.bar(
                data_key="value",
                name=t(title),
                fill=SERIES_1,
                radius=[0, 4, 4, 0],
                bar_size=14,
                unit=unit,
            ),
            data=PlanningState.supplier_charts[feature],
            layout="vertical",
            width="100%",
            height=rx.cond(
                PlanningState.supplier_cards.length() > 4,
                PlanningState.supplier_cards.length() * 36 + 40,
                180,
            ),
            margin={"top": 8, "right": 16, "bottom": 0, "left": 0},
        ),
        role="img",
        aria_label=t(title),
        min_width="0",
    )
