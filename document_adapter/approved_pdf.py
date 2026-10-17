"""Paginated procurement record from validated immutable approved content only."""

import json
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from threading import Lock
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from application.planning_cases import fingerprint

FONT = "ProcurementDejaVu"
_font_lock = Lock()


def render_approved_pdf(content):
    with _font_lock:
        if FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(
                TTFont(FONT, str(Path(__file__).parent / "fonts/DejaVuSans.ttf"))
            )
    font = pdfmetrics.getFont(FONT)
    body = ParagraphStyle(
        "Body", fontName=FONT, fontSize=9, leading=13, spaceAfter=6, splitLongWords=True
    )
    heading = ParagraphStyle(
        "Heading",
        parent=body,
        fontSize=13,
        leading=18,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
        textColor=colors.HexColor("#153d55"),
    )
    title = ParagraphStyle("Title", parent=heading, fontSize=21, leading=26)
    warning = ParagraphStyle(
        "Warning",
        parent=body,
        backColor=colors.HexColor("#fff2cf"),
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=14,
    )
    story = []

    def paragraph(value, style=body):
        text = str(value)
        if any(ord(c) not in font.face.charWidths for c in text if c not in "\n\r\t"):
            raise ValueError("Text contains glyphs outside the bundled font.")
        return Paragraph(escape(text).replace("\n", "<br/>").replace("\t", "    "), style)

    def section(name):
        story.append(paragraph(name, heading))

    def fields(rows):
        for label, value in rows:
            story.append(paragraph(f"{label}: {value}"))

    def saved_json(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def rational(value):
        return f"{value['numerator']}/{value['denominator']}"

    snapshot, audit, plan = (
        content[k] for k in ("planning_snapshot", "human_decision", "selected_plan")
    )
    request = snapshot["request"]
    demand, policy = request["requirement"], request["policy"]
    assessments = {a["snapshot"]["context"]["supplier_id"]: a for a in snapshot["assessments"]}
    suppliers = {s["supplier_id"]: s for s in request["suppliers"]}
    coefficients = {r["supplier_id"]: r["value"] for r in request["risk_coefficients"]}
    story.append(paragraph("Approved procurement plan", title))
    story.append(paragraph(audit["demonstration"], warning))
    story.append(
        paragraph(
            "Approved original base. Only the selected allocation below is approved. "
            "Stress scenarios remain separate analytical cases."
        )
    )
    if audit["incomplete_comparison"]:
        story.append(
            paragraph(
                "INCOMPLETE COMPARISON: the selected plan was proven, but a later "
                "comparison calculation failed. Saved solver outcome: " + audit["solver_outcome"],
                warning,
            )
        )
    fields(
        [
            ("Product", demand["product_id"]),
            ("Approved demand", f"{demand['approved_quantity']} {demand['quantity_unit']}"),
            ("Required date (saved)", demand["required_date"]),
            ("Planning reference time (saved)", audit["planning_reference_time"]),
            ("Decision recorded at (UTC)", audit["recorded_at"]),
            ("Total cost (exact)", f"{plan['total_cost']} {demand['currency']}"),
            ("Risk exposure (exact rational)", rational(plan["risk_exposure"])),
        ]
    )
    story.append(
        paragraph(
            "Exposure is an uncalibrated synthetic proxy, not a supplier-failure "
            "probability. No current operational validity is asserted."
        )
    )
    section("Approved allocation")
    rows = [
        [paragraph(v) for v in ("Saved supplier identity", "Quantity", "Unit price", "Line cost")]
    ]
    for allocation in plan["allocations"]:
        identity, quantity = allocation["supplier_id"], allocation["quantity"]
        price = suppliers[identity]["unit_price"]
        rows.append(
            [
                paragraph(identity),
                paragraph(f"{quantity} {demand['quantity_unit']}"),
                paragraph(f"{price} {demand['currency']}"),
                paragraph(f"{Decimal(price) * quantity:f} {demand['currency']}"),
            ]
        )
    table = Table(rows, colWidths=[201, 80, 100, 100], repeatRows=1, hAlign="LEFT", splitInRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7f0f4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccd6dc")),
            ]
        )
    )
    story.append(table)
    section("Human decision")
    fields(
        [
            ("Outcome", audit["outcome"]),
            ("Selected plan index", content["plan_index"]),
            ("Actor audit reference", audit["actor_reference"]),
            ("Actor attribution", audit["actor_attribution"]),
            ("Reason", audit["rationale"] or "No rationale supplied for minimum-cost selection"),
        ]
    )
    history = snapshot["facts"].get("input_kind") == "odoo_quotations_odoo_history"
    if history:
        capture = json.loads(snapshot["facts"]["history"])
        section("Saved Odoo history provenance")
        fields(
            [
                ("Acquisition database", capture["evidence"]["database"]),
                (
                    "Record origin",
                    snapshot["model_manifest"]["metadata"]["data_origin"],
                ),
                ("History cutoff (UTC)", capture["evidence"]["cutoff"]),
                ("History capture SHA-256", capture["capture_hash"]),
                ("Model training source", snapshot["model_manifest"]["metadata"]["source_type"]),
            ]
        )
    section(
        "Saved supplier terms and assessments"
        if history
        else "Saved supplier terms and synthetic assessments"
    )
    for identity, supplier in suppliers.items():
        assessment = assessments[identity]
        fields(
            [
                ("Supplier identity / saved label", identity),
                ("Availability", supplier["available"]),
                ("Capacity", supplier["capacity"]),
                ("MOQ", saved_json(supplier["minimum_order"])),
                ("Price quantity validity", saved_json(supplier["price_quantities"])),
                ("Delivery quantity validity", saved_json(supplier["delivery_quantities"])),
                ("Promised date", supplier["promised_date"]),
                ("Class", assessment["predicted_class"]),
                ("Score (exact)", assessment["score"]),
                ("Risk coefficient (exact)", coefficients[identity]),
                ("ML source type", assessment["snapshot"]["source_type"]),
            ]
        )
        if history:
            feature = assessment["snapshot"]
            fields(
                [
                    (
                        "Schedule adherence (%) / eligible completed lines",
                        saved_json(feature["values"]),
                    ),
                    ("History reference", feature["source_reference"]),
                    (
                        "History window (UTC)",
                        feature["history_start"] + " to " + feature["history_end"],
                    ),
                ]
            )
        story.append(Spacer(1, 8))
    section("Saved policy and model references")
    fields(
        [
            ("Policy", saved_json(policy)),
            ("Model metadata", saved_json(snapshot["model_manifest"]["metadata"])),
            ("Model artifact SHA-256", snapshot["model_manifest"]["artifact_sha256"]),
            ("Solver evidence", saved_json(snapshot["solver"])),
            ("Solver outcome", audit["solver_outcome"]),
        ]
    )
    section("Approved content identity")
    fields(
        [
            ("Content version", content["content_version"]),
            ("Case ID", content["case_id"]),
            ("Planning snapshot SHA-256", content["snapshot_hash"]),
            ("Approved content SHA-256", fingerprint(content)),
        ]
    )
    section("Saved field provenance")
    for source in snapshot["provenance"]["entries"]:
        fields(
            [
                (
                    source["canonical_path"],
                    f"{source['source_type']} | {source['source_reference']} | "
                    f"observed at {source['observed_at']} | field {source['field_name']}",
                )
            ]
        )
    story.append(
        paragraph(
            "This planning record does not create an Odoo Purchase Order. "
            "Supplier labels do not establish legal names, addresses or tax details."
        )
    )
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=51,
        rightMargin=51,
        topMargin=45,
        bottomMargin=45,
        title="Approved procurement plan",
        author="Procurement Decision Support",
    )

    def footer(canvas, document):
        canvas.setFont(FONT, 8)
        canvas.setFillColor(colors.HexColor("#52616b"))
        canvas.drawString(51, 26, "Controlled demonstration | Approved original base")
        canvas.drawRightString(A4[0] - 51, 26, f"Page {document.page}")

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue(), f"{reportlab.Version}/{FONT}/layout-v1"
