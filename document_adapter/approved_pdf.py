"""Approved procurement plan PDF v2 from validated immutable approved content only.

Layout: a summary page, one purchase order proposal ("Megrendelési javaslat") page per
supplier with a non-zero approved quantity, and a readable audit appendix at the end.
Hungarian or English; no raw JSON. The document is not an Odoo Purchase Order.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
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
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from application.planning_cases import fingerprint
from application.planning_serialization import read_assessments
from application.supplier_overview import (
    class_label,
    feature_label,
    leaf_text,
    metric_display,
    money_text,
    path_steps,
    saved_labels,
)

FONT = "ProcurementDejaVu"
LAYOUT_VERSION = "layout-v2"
_font_lock = Lock()

TEXT = {
    "hu": {
        "doc_title": "Jóváhagyott beszerzési terv",
        "summary": "Összefoglaló",
        "footer": "Jóváhagyott beszerzési terv | {case}",
        "page": "{page}. oldal",
        "generated": (
            "Bemutató adatok: a beszállítói értékelés generált (szimulált) Odoo beszerzési "
            "előzményeken tanított döntési fából származik. Nem valós beszállítói teljesítmény."
        ),
        "observed": (
            "A beszállítói értékelés megfigyelt Odoo beszerzési előzményeken tanított döntési "
            "fából származik. A pontszám nem kalibrált meghibásodási valószínűség."
        ),
        "synthetic": (
            "Bemutató adatok: a beszállítói értékelés szintetikus bemutató modellből származik. "
            "Nem valós beszállítói teljesítmény."
        ),
        "scope": (
            "Ez a dokumentum a jóváhagyott eredeti tervet rögzíti. A stresszteszt-forgatókönyvek "
            "külön elemzési esetek maradnak. A dokumentum nem Odoo beszerzési rendelés."
        ),
        "incomplete": (
            "HIÁNYOS ÖSSZEHASONLÍTÁS: a kiválasztott terv igazolt, de egy későbbi "
            "összehasonlító számítás nem sikerült. Rögzített megoldói eredmény: {status}."
        ),
        "product": "Termék",
        "demand": "Jóváhagyott mennyiség",
        "required_date": "Szükséges határidő",
        "plan": "Kiválasztott terv",
        "minimum_plan": "Minimális költségű terv",
        "alternative_plan": "{n}. alternatív terv (alacsonyabb kockázati kitettség)",
        "total_cost": "Teljes költség",
        "supplier_count": "Beszállítók száma",
        "largest_share": "Legnagyobb beszállítói részarány",
        "exposure": "Kockázati kitettség",
        "exposure_note": (
            "A kockázati kitettség a beszállítói kockázati pontszámok mennyiséggel súlyozott "
            "átlaga; nem kalibrált meghibásodási valószínűség."
        ),
        "premium": "Költségtöbblet a minimális költséghez képest",
        "allocation": "Jóváhagyott elosztás",
        "supplier": "Beszállító",
        "quantity": "Mennyiség",
        "unit": "Mértékegység",
        "unit_price": "Egységár",
        "line_total": "Sor összesen",
        "share": "Részarány",
        "currency": "Pénznem",
        "total": "Összesen",
        "decision": "Emberi döntés",
        "outcome": "Döntés",
        "approved": "Jóváhagyva",
        "decided_by": "Döntéshozó (audit hivatkozás)",
        "recorded_at": "Rögzítve",
        "rationale": "Indoklás",
        "no_rationale": "Nincs megadva (minimális költségű terv kiválasztása)",
        "proposals_follow": (
            "A beszállítónkénti megrendelési javaslatok a következő oldalakon, az audit "
            "melléklet a dokumentum végén található."
        ),
        "proposal": "Megrendelési javaslat",
        "offer": "Ajánlat",
        "case": "Beszerzési eset",
        "line": "Rendelési tétel",
        "dates": "Határidők",
        "promised_date": "Vállalt szállítási dátum",
        "terms": "Feltételek",
        "moq": "Minimális rendelési mennyiség",
        "none": "nincs",
        "capacity": "Kapacitás",
        "price_range": "Ár érvényességi mennyiségi sávja",
        "delivery_range": "Szállítható mennyiségi sáv",
        "proposal_note": (
            "A javaslat a jóváhagyott tervből készült, nem Odoo beszerzési rendelés. A "
            "beszállító megnevezése nem helyettesíti a jogi adatokat (cím, adószám)."
        ),
        "appendix": "Audit melléklet",
        "data_source": "Adatforrás",
        "database": "Odoo adatbázis",
        "data_origin": "Adatok eredete",
        "origin_generated": "generált (szimulált) előzmények",
        "origin_observed": "megfigyelt előzmények",
        "origin_synthetic": "szintetikus bemutató adatok",
        "quotation_group": "Ajánlatcsoport",
        "history_cutoff": "Előzmények lezárási időpontja",
        "capture_hash": "Előzmény-rögzítés SHA-256",
        "model": "Beszállítóértékelő modell",
        "model_id": "Modellazonosító",
        "training_id": "Tanítási azonosító",
        "trained_through": "Tanítási adatok vége",
        "artifact_hash": "Modellfájl SHA-256",
        "assessments": "Beszállítói értékelések",
        "class": "Besorolás",
        "score": "Kockázati pontszám",
        "metrics": "Előzmény-mutatók",
        "path": "Döntési útvonal",
        "window": "Előzmény-ablak",
        "optimization": "Optimalizálás",
        "solver": "Megoldó",
        "solver_outcome": "Megoldói eredmény",
        "time_limit": "Időkorlát",
        "seconds": "mp",
        "max_suppliers": "Beszállítók maximális száma",
        "concentration": "Koncentrációs korlát (legnagyobb részarány)",
        "epsilons": "Megengedett költségtöbblet az alternatív tervekhez",
        "decision_audit": "Döntési napló",
        "attribution": "Döntéshozó azonosítása",
        "demonstration": "Rögzített nyilatkozat",
        "plan_index": "Terv sorszáma",
        "reference_time": "Tervezési referenciaidő",
        "identity": "Tartalmi azonosítók",
        "content_version": "Tartalomverzió",
        "snapshot_hash": "Tervpillanatkép SHA-256",
        "content_hash": "Jóváhagyott tartalom SHA-256",
        "provenance": "Mezőszintű adatforrások",
        "field": "Mező",
        "source": "Forrás",
        "reference": "Hivatkozás",
        "observed_at": "Időpont",
        "original_text": "(eredeti, rögzített szöveg)",
        "yes": "igen",
        "no": "nem",
        "available": "Elérhető",
    },
    "en": {
        "doc_title": "Approved procurement plan",
        "summary": "Summary",
        "footer": "Approved procurement plan | {case}",
        "page": "Page {page}",
        "generated": (
            "Demonstration data: supplier assessments come from a decision tree trained on "
            "generated (simulated) Odoo purchase history. Not real supplier performance."
        ),
        "observed": (
            "Supplier assessments come from a decision tree trained on observed Odoo purchase "
            "history. The score is not a calibrated failure probability."
        ),
        "synthetic": (
            "Demonstration data: supplier assessments come from a synthetic demonstration "
            "model. Not real supplier performance."
        ),
        "scope": (
            "This document records the approved original plan. Stress scenarios remain "
            "separate analytical cases. This document is not an Odoo Purchase Order."
        ),
        "incomplete": (
            "INCOMPLETE COMPARISON: the selected plan was proven, but a later comparison "
            "calculation failed. Saved solver outcome: {status}."
        ),
        "product": "Product",
        "demand": "Approved quantity",
        "required_date": "Required date",
        "plan": "Selected plan",
        "minimum_plan": "Minimum-cost plan",
        "alternative_plan": "Alternative plan {n} (lower risk exposure)",
        "total_cost": "Total cost",
        "supplier_count": "Number of suppliers",
        "largest_share": "Largest supplier share",
        "exposure": "Risk exposure",
        "exposure_note": (
            "Risk exposure is the quantity-weighted average of supplier risk scores; it is "
            "not a calibrated failure probability."
        ),
        "premium": "Cost premium over the minimum cost",
        "allocation": "Approved allocation",
        "supplier": "Supplier",
        "quantity": "Quantity",
        "unit": "Unit",
        "unit_price": "Unit price",
        "line_total": "Line total",
        "share": "Share",
        "currency": "Currency",
        "total": "Total",
        "decision": "Human decision",
        "outcome": "Outcome",
        "approved": "Approved",
        "decided_by": "Decided by (audit reference)",
        "recorded_at": "Recorded at",
        "rationale": "Rationale",
        "no_rationale": "Not given (minimum-cost plan selected)",
        "proposals_follow": (
            "One purchase order proposal per supplier follows; the audit appendix is at the end."
        ),
        "proposal": "Purchase order proposal",
        "offer": "Quotation",
        "case": "Procurement case",
        "line": "Order line",
        "dates": "Dates",
        "promised_date": "Promised delivery date",
        "terms": "Terms",
        "moq": "Minimum order quantity",
        "none": "none",
        "capacity": "Capacity",
        "price_range": "Price validity quantity range",
        "delivery_range": "Deliverable quantity range",
        "proposal_note": (
            "This proposal is derived from the approved plan and is not an Odoo Purchase "
            "Order. Supplier labels do not establish legal names, addresses or tax details."
        ),
        "appendix": "Audit appendix",
        "data_source": "Data source",
        "database": "Odoo database",
        "data_origin": "Data origin",
        "origin_generated": "generated (simulated) history",
        "origin_observed": "observed history",
        "origin_synthetic": "synthetic demonstration data",
        "quotation_group": "Quotation group",
        "history_cutoff": "History cutoff",
        "capture_hash": "History capture SHA-256",
        "model": "Supplier evaluation model",
        "model_id": "Model ID",
        "training_id": "Training ID",
        "trained_through": "Training data until",
        "artifact_hash": "Model artifact SHA-256",
        "assessments": "Supplier assessments",
        "class": "Class",
        "score": "Risk score",
        "metrics": "History metrics",
        "path": "Decision path",
        "window": "History window",
        "optimization": "Optimization",
        "solver": "Solver",
        "solver_outcome": "Solver outcome",
        "time_limit": "Time limit",
        "seconds": "s",
        "max_suppliers": "Maximum number of suppliers",
        "concentration": "Concentration limit (largest share)",
        "epsilons": "Allowed cost tolerance for alternative plans",
        "decision_audit": "Decision log",
        "attribution": "Actor attribution",
        "demonstration": "Recorded statement",
        "plan_index": "Plan index",
        "reference_time": "Planning reference time",
        "identity": "Content identity",
        "content_version": "Content version",
        "snapshot_hash": "Planning snapshot SHA-256",
        "content_hash": "Approved content SHA-256",
        "provenance": "Field-level data sources",
        "field": "Field",
        "source": "Source",
        "reference": "Reference",
        "observed_at": "Time",
        "original_text": "(original recorded text)",
        "yes": "yes",
        "no": "no",
        "available": "Available",
    },
}


def _fraction(value: dict) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def render_approved_pdf(content, language="hu"):
    if language not in TEXT:
        raise ValueError("Unsupported document language.")
    t = TEXT[language]
    with _font_lock:
        if FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(
                TTFont(FONT, str(Path(__file__).parent / "fonts/DejaVuSans.ttf"))
            )
    font = pdfmetrics.getFont(FONT)
    body = ParagraphStyle(
        "Body", fontName=FONT, fontSize=9, leading=13, spaceAfter=5, splitLongWords=True
    )
    small = ParagraphStyle("Small", parent=body, fontSize=7.5, leading=10, spaceAfter=0)
    cell = ParagraphStyle("Cell", parent=body, spaceAfter=0)
    head = ParagraphStyle("Head", parent=cell, fontSize=8, leading=10)
    heading = ParagraphStyle(
        "Heading",
        parent=body,
        fontSize=12.5,
        leading=17,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
        textColor=colors.HexColor("#153d55"),
    )
    subheading = ParagraphStyle(
        "Subheading", parent=heading, fontSize=10.5, leading=14, spaceBefore=8
    )
    title = ParagraphStyle("Title", parent=heading, fontSize=20, leading=25, spaceBefore=0)
    notice = ParagraphStyle(
        "Notice",
        parent=body,
        backColor=colors.HexColor("#fff2cf"),
        borderPadding=7,
        spaceBefore=6,
        spaceAfter=12,
    )

    def paragraph(value, style=body):
        text = str(value)
        if any(ord(c) not in font.face.charWidths for c in text if c not in "\n\r\t"):
            raise ValueError("Text contains glyphs outside the bundled font.")
        return Paragraph(escape(text).replace("\n", "<br/>").replace("\t", "    "), style)

    snapshot, audit, plan = (
        content[k] for k in ("planning_snapshot", "human_decision", "selected_plan")
    )
    request, facts = snapshot["request"], snapshot["facts"]
    demand, policy = request["requirement"], request["policy"]
    currency, unit_id = demand["currency"], demand["quantity_unit"]
    suppliers = {s["supplier_id"]: s for s in request["suppliers"]}
    offers = {s["terms"]["supplier_id"]: s["offer_id"] for s in facts["suppliers"]}
    names = saved_labels(snapshot)
    metadata = snapshot["model_manifest"]["metadata"]
    history = facts.get("input_kind") == "odoo_quotations_odoo_history"
    origin = metadata.get("data_origin", "generated") if history else "synthetic"
    origin = origin if origin in ("generated", "observed") or not history else "generated"

    def named(identity):
        name = names.get(identity)
        return identity if name is None else f"{name} ({identity})"

    def short(identity):
        return names.get(identity, identity)

    def number(value):
        return f"{value:,}".replace(",", " ") if language == "hu" else f"{value:,}"

    def money(value):
        return f"{money_text(Decimal(value), language)} {currency}"

    def percent(value: Fraction):
        text = f"{float(value) * 100:.1f}%"
        return text.replace(".", ",") if language == "hu" else text

    def decimal(value):
        return str(value).replace(".", ",") if language == "hu" else str(value)

    def ratio(value: Fraction):
        text = f"{float(value):.4f}"
        return text.replace(".", ",") if language == "hu" else text

    def day(value):
        parsed = date.fromisoformat(value)
        return parsed.strftime("%Y.%m.%d.") if language == "hu" else parsed.isoformat()

    def moment(value):
        parsed = datetime.fromisoformat(value)
        stamp = "%Y.%m.%d. %H:%M" if language == "hu" else "%Y-%m-%d %H:%M"
        return parsed.strftime(stamp) + " UTC"

    def quantity(value):
        return f"{number(value)} {short(unit_id)}"

    def quantity_range(value):
        return f"{number(value['minimum'])}–{number(value['maximum'])} {short(unit_id)}"

    def yes_no(value):
        return t["yes"] if value else t["no"]

    def fields(rows):
        table = Table(
            [[paragraph(label, cell), paragraph(value, cell)] for label, value in rows],
            colWidths=[175, 318],
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#52616b")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(table)

    def grid(header, rows, widths, total=None):
        data = [[paragraph(v, head) for v in header]]
        data += [[paragraph(v, cell) for v in row] for row in rows]
        if total is not None:
            data.append([paragraph(v, cell) for v in total])
        table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitInRow=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7f0f4")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccd6dc")),
        ]
        if total is not None:
            style.append(("LINEABOVE", (0, -1), (-1, -1), 0.9, colors.HexColor("#153d55")))
        table.setStyle(TableStyle(style))
        story.append(table)

    story = []
    selected = [a for a in plan["allocations"] if a["quantity"] > 0]
    plan_name = (
        t["minimum_plan"]
        if content["plan_index"] == 0
        else t["alternative_plan"].format(n=content["plan_index"])
    )

    # --- Summary page ---
    story.append(paragraph(t["doc_title"], title))
    story.append(paragraph(t["summary"], subheading))
    story.append(paragraph(t[origin], notice))
    if audit["incomplete_comparison"]:
        story.append(paragraph(t["incomplete"].format(status=audit["solver_outcome"]), notice))
    fields(
        [
            (t["product"], named(demand["product_id"])),
            (t["demand"], quantity(demand["approved_quantity"])),
            (t["required_date"], day(demand["required_date"])),
            (t["plan"], plan_name),
            (t["total_cost"], money(plan["total_cost"])),
            (t["supplier_count"], str(plan["supplier_count"])),
            (t["largest_share"], percent(_fraction(plan["largest_share"]))),
            (t["exposure"], ratio(_fraction(plan["risk_exposure"]))),
            (t["premium"], percent(_fraction(plan["cost_premium"]))),
        ]
    )
    story.append(paragraph(t["exposure_note"], small))
    story.append(paragraph(t["allocation"], heading))
    approved_quantity = demand["approved_quantity"]
    grid(
        (t["supplier"], t["quantity"], t["unit_price"], t["line_total"], t["share"]),
        [
            (
                short(a["supplier_id"]),
                quantity(a["quantity"]),
                money(suppliers[a["supplier_id"]]["unit_price"]),
                money(Decimal(suppliers[a["supplier_id"]]["unit_price"]) * a["quantity"]),
                percent(Fraction(a["quantity"], approved_quantity)),
            )
            for a in selected
        ],
        [140, 85, 85, 95, 68],
        total=(t["total"], quantity(approved_quantity), "", money(plan["total_cost"]), ""),
    )
    story.append(paragraph(t["decision"], heading))
    fields(
        [
            (t["outcome"], t["approved"]),
            (t["decided_by"], audit["actor_reference"]),
            (t["recorded_at"], moment(audit["recorded_at"])),
            (t["rationale"], audit["rationale"] or t["no_rationale"]),
        ]
    )
    story.append(Spacer(1, 8))
    story.append(paragraph(t["scope"], small))
    story.append(paragraph(t["proposals_follow"], small))

    # --- One purchase order proposal per supplier with a non-zero allocation ---
    for allocation in selected:
        identity = allocation["supplier_id"]
        terms = suppliers[identity]
        offer = offers.get(identity)
        story.append(PageBreak())
        story.append(paragraph(t["proposal"], title))
        story.append(paragraph(short(identity), subheading))
        fields(
            [
                (t["supplier"], named(identity)),
                (t["offer"], "—" if offer is None else named(offer)),
                (t["product"], named(demand["product_id"])),
                (t["case"], content["case_id"]),
                (t["recorded_at"], moment(audit["recorded_at"])),
            ]
        )
        story.append(paragraph(t["line"], heading))
        grid(
            (
                t["product"],
                t["quantity"],
                t["unit"],
                t["unit_price"],
                t["line_total"],
                t["currency"],
            ),
            [
                (
                    short(demand["product_id"]),
                    number(allocation["quantity"]),
                    short(unit_id),
                    money_text(Decimal(terms["unit_price"]), language),
                    money_text(Decimal(terms["unit_price"]) * allocation["quantity"], language),
                    currency,
                )
            ],
            [128, 62, 78, 66, 82, 60],
        )
        story.append(paragraph(t["dates"], heading))
        fields(
            [
                (t["required_date"], day(demand["required_date"])),
                (t["promised_date"], day(terms["promised_date"])),
            ]
        )
        story.append(paragraph(t["terms"], heading))
        moq = terms["minimum_order"]["quantity"]
        fields(
            [
                (t["moq"], t["none"] if moq is None else quantity(moq)),
                (t["capacity"], quantity(terms["capacity"])),
                (t["available"], yes_no(terms["available"])),
                (t["price_range"], quantity_range(terms["price_quantities"])),
                (t["delivery_range"], quantity_range(terms["delivery_quantities"])),
            ]
        )
        story.append(Spacer(1, 10))
        story.append(paragraph(t["proposal_note"], small))

    # --- Readable audit appendix ---
    story.append(PageBreak())
    story.append(paragraph(t["appendix"], title))
    story.append(paragraph(t["data_source"], heading))
    rows = [(t["data_origin"], t["origin_" + origin])]
    if history:
        capture = json.loads(facts["history"])
        rows += [
            (t["database"], capture["evidence"]["database"]),
            (t["quotation_group"], facts.get("comparison_case_id", "—")),
            (t["history_cutoff"], moment(capture["evidence"]["cutoff"])),
            (t["capture_hash"], capture["capture_hash"]),
        ]
    fields(rows)
    story.append(paragraph(t["model"], heading))
    fields(
        [
            (t["model_id"], metadata["model_id"]),
            (t["training_id"], metadata["training_id"]),
            (t["trained_through"], moment(metadata["trained_through"])),
            (t["artifact_hash"], snapshot["model_manifest"]["artifact_sha256"]),
        ]
    )
    story.append(paragraph(t["assessments"], heading))
    for assessment in read_assessments(snapshot["assessments"]):
        features = assessment.snapshot
        identity = features.context.supplier_id
        story.append(paragraph(short(identity), subheading))
        fields(
            [
                (t["class"], class_label(assessment, language)),
                (t["score"], decimal(assessment.score)),
                (
                    t["window"],
                    f"{moment(features.history_start.isoformat())} – "
                    f"{moment(features.history_end.isoformat())}",
                ),
                (
                    t["metrics"],
                    "\n".join(
                        f"{feature_label(name, language)}: {metric_display(name, value, language)}"
                        for name, value in zip(features.feature_names, features.values, strict=True)
                    ),
                ),
                (
                    t["path"],
                    "\n".join(
                        [s["text"] for s in path_steps(assessment, language)]
                        + [leaf_text(assessment, language)]
                    ),
                ),
            ]
        )
    story.append(paragraph(t["optimization"], heading))
    solver = snapshot["solver"]
    fields(
        [
            (
                t["solver"],
                f"{solver['adapter']} ("
                + ", ".join(f"{k} {v}" for k, v in sorted(solver["runtime"].items()))
                + ")",
            ),
            (t["time_limit"], f"{decimal(solver['time_limit_seconds'])} {t['seconds']}"),
            (t["solver_outcome"], audit["solver_outcome"]),
            (t["max_suppliers"], str(policy["max_suppliers"])),
            (
                t["concentration"],
                t["none"]
                if policy["concentration_limit"] is None
                else percent(Fraction(Decimal(policy["concentration_limit"]))),
            ),
            (
                t["epsilons"],
                ", ".join(percent(Fraction(Decimal(e))) for e in policy["epsilons"]),
            ),
        ]
    )
    story.append(paragraph(t["decision_audit"], heading))
    fields(
        [
            (t["outcome"], t["approved"]),
            (t["plan_index"], str(content["plan_index"])),
            (t["decided_by"], audit["actor_reference"]),
            (t["attribution"], f"{audit['actor_attribution']} {t['original_text']}"),
            (t["recorded_at"], moment(audit["recorded_at"])),
            (t["reference_time"], moment(audit["planning_reference_time"])),
            (t["rationale"], audit["rationale"] or t["no_rationale"]),
            (t["demonstration"], f"{audit['demonstration']} {t['original_text']}"),
        ]
    )
    story.append(paragraph(t["identity"], heading))
    fields(
        [
            (t["content_version"], content["content_version"]),
            (t["case"], content["case_id"]),
            (t["snapshot_hash"], content["snapshot_hash"]),
            (t["content_hash"], fingerprint(content)),
        ]
    )
    story.append(paragraph(t["provenance"], heading))
    entries = snapshot["provenance"]["entries"]
    data = [
        [paragraph(v, small) for v in (t["field"], t["source"], t["reference"], t["observed_at"])]
    ]
    data += [
        [
            paragraph(e["canonical_path"], small),
            paragraph(e["source_type"], small),
            paragraph(e["source_reference"], small),
            paragraph(moment(e["observed_at"]), small),
        ]
        for e in entries
    ]
    table = Table(data, colWidths=[160, 85, 168, 80], repeatRows=1, hAlign="LEFT", splitInRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7f0f4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#ccd6dc")),
            ]
        )
    )
    story.append(table)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=51,
        rightMargin=51,
        topMargin=45,
        bottomMargin=45,
        title=t["doc_title"],
        author="Procurement Decision Support",
        lang=language,
    )
    footer_text = t["footer"].format(case=content["case_id"])
    for c in footer_text:
        if ord(c) not in font.face.charWidths:
            raise ValueError("Text contains glyphs outside the bundled font.")

    def footer(canvas, document):
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(colors.HexColor("#52616b"))
        canvas.drawString(51, 26, footer_text)
        canvas.drawRightString(A4[0] - 51, 26, t["page"].format(page=document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue(), f"{reportlab.Version}/{FONT}/{LAYOUT_VERSION}"
