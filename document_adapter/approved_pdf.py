"""Approved procurement plan and audit appendix PDFs from validated approved content only.

Two documents from the same approved content (ADR-036):

- ``plan`` (``plan_document.py``): a summary page with a compact supplier assessment
  table, one order-line page ("Rendelési tétel – jóváhagyott terv") per supplier with a
  non-zero approved quantity, and short verification identifiers at the end; for the buyer.
- ``audit`` (``audit_document.py``): the readable audit appendix (data source, model,
  assessments with tree paths, optimization, decision log, content identity, field-level
  provenance).

Hungarian or English (``texts.py``, ``formatting.py``); no raw JSON. Neither document is
an Odoo Purchase Order.
"""

from io import BytesIO

import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from document_adapter.audit_document import audit_story
from document_adapter.formatting import Formatter
from document_adapter.layout import FONT, GREY, LAYOUT_VERSION, check_glyphs, register_font
from document_adapter.plan_document import plan_story
from document_adapter.texts import TEXT

MARGIN = 51


def render_plan_pdf(content, language="hu"):
    """The approved procurement plan for the buyer: summary and one page per supplier."""
    return _render(content, language, "plan")


def render_audit_pdf(content, language="hu"):
    """The audit appendix of the same approved content, for traceability."""
    return _render(content, language, "audit")


def _render(content, language, kind):
    """Build one document; return the PDF bytes and the renderer version stored with them."""
    if language not in TEXT:
        raise ValueError("Unsupported document language.")
    register_font()
    f = Formatter(content, language)
    t = f.t
    story = audit_story(content, f) if kind == "audit" else plan_story(content, f)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=45,
        bottomMargin=45,
        title=t["audit_title" if kind == "audit" else "doc_title"],
        author="Procurement Decision Support",
        lang=language,
    )
    footer_text = t["audit_footer" if kind == "audit" else "footer"].format(case=content["case_id"])
    check_glyphs(footer_text)

    def footer(canvas, document):
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(GREY)
        canvas.drawString(MARGIN, 26, footer_text)
        canvas.drawRightString(A4[0] - MARGIN, 26, t["page"].format(page=document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue(), f"{reportlab.Version}/{FONT}/{LAYOUT_VERSION}"
