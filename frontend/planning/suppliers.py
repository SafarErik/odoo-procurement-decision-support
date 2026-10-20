"""Suppliers tab: KPI comparison charts and one card per supplier (P2 supplier overview)."""

import reflex as rx

from frontend.planning.charts import kpi_chart
from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, INK, MUTED
from frontend.ui import card, error_state, heading, loading_state, muted, t


def _class_badge(row):
    return rx.match(
        row["class_key"],
        ("problematic", rx.badge(row["class_label"], color_scheme="amber", size="2")),
        ("schedule_watch", rx.badge(row["class_label"], color_scheme="amber", size="2")),
        rx.badge(row["class_label"], color_scheme="teal", size="2"),
    )


def _fact(label: str, value):
    return rx.box(
        rx.text(t(label), size="1", color=MUTED),
        rx.text(value, size="2", font_weight="600", color=INK),
        min_width="0",
    )


def _supplier_card(row):
    return card(
        rx.flex(
            rx.box(
                rx.heading(row["name"], as_="h3", size="4"),
                rx.text(row["offer"], size="1", color=MUTED),
                min_width="0",
            ),
            _class_badge(row),
            justify="between",
            align="start",
            gap="0.75rem",
        ),
        rx.grid(
            _fact("offer_price", row["price"]),
            _fact("planned_quantity", rx.cond(row["planned"] != "", row["planned"], "—")),
            _fact("capacity_label", row["capacity"]),
            _fact("promised_label", row["promised"]),
            columns="2",
            gap="0.75rem 1rem",
            margin_y="1rem",
        ),
        rx.box(
            rx.text(t("history_kpis"), size="2", font_weight="650"),
            rx.text(row["window"], size="1", color=MUTED),
            rx.foreach(
                row["metrics"],
                lambda m: rx.flex(
                    rx.text(m["label"], size="2", color=MUTED),
                    rx.text(m["display"], size="2", font_weight="600", white_space="nowrap"),
                    justify="between",
                    gap="1rem",
                    padding_y="0.3rem",
                    border_bottom=f"1px solid {HAIRLINE}",
                ),
            ),
            margin_top="0.5rem",
        ),
        rx.el.details(
            rx.el.summary(t("why_class")),
            rx.el.ol(
                rx.foreach(row["path"], lambda step: rx.el.li(step, font_size="0.875rem")),
                padding_left="1.25rem",
                line_height="1.7",
            ),
            rx.text(row["summary"], size="2", margin_top="0.5rem"),
            muted("score_note", margin_top="0.5rem"),
            margin_top="0.75rem",
        ),
        role="region",
        aria_label=row["name"],
    )


def suppliers_view() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                heading("suppliers_title", size="5"),
                muted("suppliers_intro", margin_top="0.35rem", max_width="70ch"),
            ),
            justify="between",
            gap="1rem",
        ),
        rx.cond(
            PlanningState.details["origin_note"] != "",
            rx.callout(
                PlanningState.details["origin_note"],
                icon="info",
                color_scheme="amber",
                size="1",
                margin_top="1rem",
            ),
        ),
        rx.cond(
            PlanningState.suppliers_loading,
            loading_state("loading_suppliers"),
            rx.cond(
                PlanningState.suppliers_error != "",
                rx.box(
                    error_state(
                        PlanningState.suppliers_error,
                        retry=PlanningState.load_supplier_overview,
                    ),
                    margin_top="1rem",
                ),
                rx.box(
                    card(
                        heading("kpi_compare", size="4"),
                        muted("kpi_compare_note", margin_top="0.25rem"),
                        rx.text(
                            t("kpi_reference"),
                            ": ",
                            PlanningState.details.get("as_of_display", ""),
                            size="1",
                            color=MUTED,
                            margin_top="0.4rem",
                        ),
                        rx.el.details(
                            rx.el.summary(t("kpi_help_title"), font_weight="600"),
                            *[
                                muted(key, margin_top="0.6rem", max_width="75ch")
                                for key in (
                                    "kpi_help_rates",
                                    "kpi_help_lateness",
                                    "kpi_help_sample",
                                )
                            ],
                            margin_top="0.5rem",
                        ),
                        rx.grid(
                            kpi_chart("on_time_rate", "kpi_on_time", "%"),
                            kpi_chart("fill_rate", "kpi_fill", "%"),
                            kpi_chart("mean_lateness_days", "kpi_lateness", ""),
                            columns=rx.breakpoints(initial="1", md="3"),
                            gap="1.5rem",
                            margin_top="1rem",
                        ),
                        margin_top="1rem",
                    ),
                    rx.grid(
                        rx.foreach(PlanningState.supplier_cards, _supplier_card),
                        columns=rx.breakpoints(initial="1", md="2", xl="3"),
                        gap="1rem",
                        margin_top="1rem",
                    ),
                ),
            ),
        ),
        rx.cond(
            PlanningState.details["parent_id"] != "Base case",
            muted("scenario_same_scores", margin_top="1rem"),
        ),
    )
