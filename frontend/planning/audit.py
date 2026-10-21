"""Audit view: exact stored values, hashes, tree paths, provenance and solver records."""

import reflex as rx

from frontend.planning.pdf import ApprovedPDFViewer
from frontend.planning.state import PlanningState
from frontend.theme import ACCENT, HAIRLINE, MUTED
from frontend.ui import BUSY, card, muted, t


def _pair(label: str, value):
    return rx.flex(
        rx.text(t(label), size="2", color=MUTED, min_width="11rem"),
        rx.code(value, size="2", variant="ghost", overflow_wrap="anywhere"),
        gap="1rem",
        padding_y="0.3rem",
        border_bottom=f"1px solid {HAIRLINE}",
        wrap="wrap",
    )


def _table(headers: tuple[str, ...], rows, cells, label: str, min_width="40rem"):
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[rx.table.column_header_cell(t(h), white_space="nowrap") for h in headers]
                )
            ),
            rx.table.body(
                rx.foreach(rows, lambda row: rx.table.row(*[rx.table.cell(row[c]) for c in cells]))
            ),
            size="1",
            min_width=min_width,
        ),
        overflow="auto",
        max_height="24rem",
        role="region",
        aria_label=t(label),
        tab_index=0,
        width="100%",
    )


def _section(title: str, *children):
    return rx.el.details(
        rx.el.summary(t(title), font_weight="650"),
        rx.flex(*children, direction="column", gap="0.75rem", margin_top="0.75rem"),
        border_top=f"1px solid {HAIRLINE}",
        padding_y="0.5rem",
    )


def _audit_pdf() -> rx.Component:
    """Audit appendix PDF of the approved content; only for an approved base case."""
    return rx.cond(
        PlanningState.details["final_outcome"] == "Approved",
        rx.box(
            rx.flex(
                rx.button(
                    rx.cond(
                        PlanningState.is_loading,
                        rx.spinner(size="2"),
                        rx.icon("file-search", size=16),
                    ),
                    rx.cond(
                        PlanningState.audit_pdf_error != "", t("retry_audit_pdf"), t("audit_pdf")
                    ),
                    on_click=PlanningState.request_audit_pdf,
                    disabled=BUSY,
                    background=ACCENT,
                    color="white",
                ),
                rx.text(t("audit_pdf_note"), size="2", color=MUTED),
                gap="0.75rem",
                align="center",
                wrap="wrap",
            ),
            rx.cond(
                PlanningState.audit_pdf_error != "",
                rx.callout(
                    PlanningState.audit_pdf_error,
                    color_scheme="amber",
                    role="alert",
                    margin_top="1rem",
                ),
            ),
            rx.cond(
                PlanningState.audit_pdf_data_url != "",
                rx.box(
                    ApprovedPDFViewer.create(
                        data=PlanningState.audit_pdf_data_url,
                        filename=PlanningState.audit_pdf_filename,
                        lang=PlanningState.lang,
                        kind="audit",
                    ),
                    margin_top="1rem",
                ),
            ),
            margin_bottom="1rem",
        ),
    )


def audit_view() -> rx.Component:
    return card(
        rx.flex(
            rx.box(
                rx.heading(
                    t("audit_title"), as_="h2", size="5", id="audit-evidence-heading", tab_index=-1
                ),
                muted("audit_intro", margin_top="0.35rem", max_width="70ch"),
            ),
            rx.button(
                rx.icon("arrow-left", size=16),
                t("back_to_overview"),
                on_click=PlanningState.change_view("overview"),
                disabled=BUSY,
                variant="outline",
            ),
            justify="between",
            align="start",
            gap="1rem",
            wrap="wrap",
            margin_bottom="1rem",
        ),
        rx.box(
            _pair("audit_case_id", PlanningState.details["case_id"]),
            _pair("audit_base_id", PlanningState.details["base_id"]),
            _pair("audit_snapshot_hash", PlanningState.details["snapshot_hash"]),
            _pair("audit_company", PlanningState.details["company"]),
            _pair("audit_product", PlanningState.details["product"]),
            _pair("audit_cutoff", PlanningState.details["as_of"]),
            _pair("audit_saved", PlanningState.details["created_at"]),
            _pair("audit_input_kind", PlanningState.details["input_kind"]),
            rx.cond(
                PlanningState.details["final_content_hash"] != "",
                _pair("audit_content_hash", PlanningState.details["final_content_hash"]),
            ),
            rx.button(
                rx.icon("copy", size=14),
                t("copy_case_id"),
                variant="soft",
                size="1",
                on_click=rx.set_clipboard(PlanningState.details["case_id"]),
                margin_top="0.75rem",
            ),
            margin_bottom="1rem",
        ),
        _audit_pdf(),
        _section(
            "audit_inputs",
            rx.text(PlanningState.details["policy"], size="2"),
            _table(
                (
                    "col_supplier",
                    "offer_price",
                    "capacity_label",
                    "moq_label",
                    "promised_label",
                    "availability",
                    "audit_ranges",
                ),
                PlanningState.scenario_suppliers,
                (
                    "name",
                    "saved_price",
                    "saved_capacity",
                    "saved_moq",
                    "saved_date",
                    "saved_available",
                    "saved_ranges",
                ),
                "audit_inputs",
            ),
        ),
        _section(
            "audit_plans",
            rx.foreach(
                PlanningState.plans,
                lambda plan: rx.box(
                    rx.text(plan["title"], font_weight="650", size="2"),
                    rx.text(t("audit_cost_exact"), ": ", plan["cost_exact"], size="2"),
                    rx.text(t("audit_exposure_exact"), ": ", plan["exposure"], size="2"),
                    rx.text(t("audit_premium_exact"), ": ", plan["premium"], size="2"),
                    rx.el.pre(plan["explanations"], font_size="0.8rem", white_space="pre-wrap"),
                ),
            ),
            rx.text(PlanningState.details["explanations"], white_space="pre-line", size="2"),
            rx.text(PlanningState.details["comparison"], white_space="pre-line", size="2"),
            _table(
                ("audit_plan", "audit_supplier_id", "audit_quantity"),
                PlanningState.allocations,
                ("plan", "supplier", "quantity"),
                "audit_plans",
                min_width="24rem",
            ),
        ),
        _section(
            "audit_tree",
            rx.foreach(
                PlanningState.assessments,
                lambda row: rx.box(
                    rx.text(row["name"], " (", row["supplier"], ")", font_weight="650", size="2"),
                    rx.text(
                        t("audit_class"),
                        ": ",
                        row["class"],
                        " · ",
                        t("audit_score"),
                        ": ",
                        row["score"],
                        size="2",
                    ),
                    rx.text(t("audit_model"), ": ", row["model"], size="2"),
                    rx.text(t("audit_history_ref"), ": ", row["source"], size="2"),
                    rx.text(t("audit_window"), ": ", row["history_window"], size="2"),
                    rx.text(t("audit_valid_until"), ": ", row["valid_until"], size="2"),
                    rx.el.pre(row["path"], font_size="0.8rem", white_space="pre-wrap"),
                    rx.text(row["readable_path"], white_space="pre-line", size="2"),
                    padding_y="0.5rem",
                    border_bottom=f"1px solid {HAIRLINE}",
                ),
            ),
        ),
        _section(
            "audit_provenance",
            _table(
                ("audit_field", "audit_source", "audit_reference", "audit_observed"),
                PlanningState.provenance,
                ("field", "type", "reference", "observed_at"),
                "audit_provenance",
                min_width="48rem",
            ),
        ),
        rx.cond(
            PlanningState.details["final_audit"] != "",
            _section(
                "audit_decision",
                rx.el.pre(
                    PlanningState.details["final_audit"],
                    font_size="0.8rem",
                    white_space="pre-wrap",
                    max_height="24rem",
                    overflow="auto",
                ),
            ),
        ),
        rx.cond(
            PlanningState.recovery_json != "",
            _section(
                "audit_last_request",
                muted("audit_last_request_note"),
                rx.button(
                    t("copy_request"),
                    variant="soft",
                    on_click=rx.set_clipboard(PlanningState.recovery_json),
                    width="fit-content",
                ),
                rx.el.pre(PlanningState.recovery_json, font_size="0.8rem", white_space="pre-wrap"),
            ),
        ),
        _section(
            "audit_snapshot",
            muted("audit_snapshot_note"),
            rx.el.pre(
                PlanningState.details["snapshot_json"],
                overflow="auto",
                max_height="24rem",
                width="100%",
                min_width="0",
                role="region",
                tab_index=0,
                aria_label=t("audit_snapshot"),
                font_size="0.8rem",
            ),
        ),
    )
