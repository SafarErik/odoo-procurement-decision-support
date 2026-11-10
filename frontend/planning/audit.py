"""Audit view: the exact stored values, hashes, tree paths, provenance and solver records of
the open case, each in a collapsible section, plus the audit appendix PDF."""

import reflex as rx

from frontend.planning.pdf import pdf_panel
from frontend.planning.state import PlanningState
from frontend.theme import HAIRLINE, MUTED
from frontend.ui import BUSY, card, muted, t

DETAILS = PlanningState.details


def _pair(label: str, value):
    """One "label: exact value" line of the case identity block."""
    return rx.flex(
        rx.text(t(label), size="2", color=MUTED, min_width="11rem"),
        rx.code(value, size="2", variant="ghost", overflow_wrap="anywhere"),
        gap="1rem",
        padding_y="0.3rem",
        border_bottom=f"1px solid {HAIRLINE}",
        wrap="wrap",
    )


def _table(headers: tuple[str, ...], rows, cells, label: str, min_width="40rem"):
    """Scrollable, keyboard-focusable table of stored rows."""
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
    """Collapsed section with a bold summary line."""
    return rx.el.details(
        rx.el.summary(t(title), font_weight="650"),
        rx.flex(*children, direction="column", gap="0.75rem", margin_top="0.75rem"),
        border_top=f"1px solid {HAIRLINE}",
        padding_y="0.5rem",
    )


def _pre(text, **props):
    """Monospaced stored text that keeps its line breaks."""
    return rx.el.pre(text, font_size="0.8rem", white_space="pre-wrap", **props)


def _audit_pdf() -> rx.Component:
    """Audit appendix PDF button and viewer; only for an approved base case."""
    return rx.cond(
        DETAILS["final_outcome"] == "Approved",
        rx.box(
            pdf_panel(
                on_click=PlanningState.request_audit_pdf,
                error=PlanningState.audit_pdf_error,
                data_url=PlanningState.audit_pdf_data_url,
                filename=PlanningState.audit_pdf_filename,
                icon="file-search",
                label="audit_pdf",
                retry_label="retry_audit_pdf",
                note="audit_pdf_note",
                kind="audit",
            ),
            margin_bottom="1rem",
        ),
    )


def _header() -> rx.Component:
    """Audit heading, its introduction and the way back to Overview."""
    return rx.flex(
        rx.box(
            rx.heading(t("audit"), as_="h2", size="5", id="audit-evidence-heading", tab_index=-1),
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
    )


def _identity() -> rx.Component:
    """Case id, base case, snapshot hash, company, product and dates, with a copy button."""
    return rx.box(
        _pair("audit_case_id", DETAILS["case_id"]),
        _pair("base_case", DETAILS["base_id"]),
        _pair("audit_snapshot_hash", DETAILS["snapshot_hash"]),
        _pair("audit_company", DETAILS["company"]),
        _pair("audit_product", DETAILS["product"]),
        _pair("audit_cutoff", DETAILS["as_of"]),
        _pair("audit_saved", DETAILS["created_at"]),
        _pair("audit_input_kind", DETAILS["input_kind"]),
        rx.cond(
            DETAILS["final_content_hash"] != "",
            _pair("audit_content_hash", DETAILS["final_content_hash"]),
        ),
        rx.button(
            rx.icon("copy", size=14),
            t("copy_case_id"),
            variant="soft",
            size="1",
            on_click=rx.set_clipboard(DETAILS["case_id"]),
            margin_top="0.75rem",
        ),
        margin_bottom="1rem",
    )


def _inputs() -> rx.Component:
    """Saved supplier terms the solver received, with the policy line."""
    return _section(
        "audit_inputs",
        rx.text(DETAILS["policy"], size="2"),
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
    )


def _plan_record(plan):
    """One plan's exact cost, exposure, premium and solver explanation."""
    return rx.box(
        rx.text(plan["title"], font_weight="650", size="2"),
        rx.text(t("audit_cost_exact"), ": ", plan["cost_exact"], size="2"),
        rx.text(t("audit_exposure_exact"), ": ", plan["exposure"], size="2"),
        rx.text(t("audit_premium_exact"), ": ", plan["premium"], size="2"),
        _pre(plan["explanations"]),
    )


def _plans() -> rx.Component:
    """Every plan's exact numbers, the comparison text and the allocation table."""
    return _section(
        "audit_plans",
        rx.foreach(PlanningState.plans, _plan_record),
        rx.text(DETAILS["explanations"], white_space="pre-line", size="2"),
        rx.text(DETAILS["comparison"], white_space="pre-line", size="2"),
        _table(
            ("plan", "audit_supplier_id", "audit_quantity"),
            PlanningState.allocations,
            ("plan", "supplier", "quantity"),
            "audit_plans",
            min_width="24rem",
        ),
    )


def _assessment(row):
    """One supplier's class, score, model, history window and decision-tree path."""
    return rx.box(
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
        _pre(row["path"]),
        rx.text(PlanningState.supplier_paths[row["supplier"]], white_space="pre-line", size="2"),
        padding_y="0.5rem",
        border_bottom=f"1px solid {HAIRLINE}",
    )


def _stored_texts() -> rx.Component:
    """Decision record, last request and the full snapshot; the first two only if present."""
    return rx.fragment(
        rx.cond(
            DETAILS["final_audit"] != "",
            _section(
                "audit_decision",
                _pre(DETAILS["final_audit"], max_height="24rem", overflow="auto"),
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
                _pre(PlanningState.recovery_json),
            ),
        ),
        _section(
            "audit_snapshot",
            muted("audit_snapshot_note"),
            rx.el.pre(
                DETAILS["snapshot_json"],
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


def audit_view() -> rx.Component:
    """The Audit card: identity, audit PDF and the collapsible evidence sections."""
    return card(
        _header(),
        _identity(),
        _audit_pdf(),
        _inputs(),
        _plans(),
        _section("audit_tree", rx.foreach(PlanningState.assessments, _assessment)),
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
        _stored_texts(),
    )
