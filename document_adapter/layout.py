"""Font, paragraph styles and the two table shapes both approved PDFs are built from.

``fields`` is a two-column label/value table; ``grid`` is a table with a shaded header
row and an optional emphasized total row. Every text goes through ``paragraph``, which
refuses characters the bundled DejaVu font cannot draw instead of printing empty boxes.
"""

from pathlib import Path
from threading import Lock
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle

FONT = "ProcurementDejaVu"
# Part of the stored renderer version; raise it whenever the rendered output changes.
LAYOUT_VERSION = "layout-v6"
_font_lock = Lock()

DARK_BLUE = colors.HexColor("#153d55")
GREY = colors.HexColor("#52616b")
LIGHT_BLUE = colors.HexColor("#e7f0f4")
RULE = colors.HexColor("#ccd6dc")

BODY = ParagraphStyle(
    "Body", fontName=FONT, fontSize=9, leading=13, spaceAfter=5, splitLongWords=True
)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=7.5, leading=10, spaceAfter=0)
CELL = ParagraphStyle("Cell", parent=BODY, spaceAfter=0)
HEAD = ParagraphStyle("Head", parent=CELL, fontSize=8, leading=10)
HEADING = ParagraphStyle(
    "Heading",
    parent=BODY,
    fontSize=12.5,
    leading=17,
    spaceBefore=12,
    spaceAfter=6,
    keepWithNext=True,
    textColor=DARK_BLUE,
)
SUBHEADING = ParagraphStyle("Subheading", parent=HEADING, fontSize=10.5, leading=14, spaceBefore=8)
TITLE = ParagraphStyle("Title", parent=HEADING, fontSize=20, leading=25, spaceBefore=0)
NOTICE = ParagraphStyle(
    "Notice",
    parent=BODY,
    backColor=colors.HexColor("#fff2cf"),
    borderPadding=7,
    spaceBefore=6,
    spaceAfter=12,
)


def register_font() -> None:
    """Register the bundled DejaVu font once per process (renders may run in threads)."""
    with _font_lock:
        if FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(
                TTFont(FONT, str(Path(__file__).parent / "fonts/DejaVuSans.ttf"))
            )


def check_glyphs(text: str) -> None:
    """Raise ValueError when the font has no glyph for a character (line breaks and tabs pass)."""
    widths = pdfmetrics.getFont(FONT).face.charWidths
    if any(ord(c) not in widths for c in text if c not in "\n\r\t"):
        raise ValueError("Text contains glyphs outside the bundled font.")


def paragraph(value, style=BODY) -> Paragraph:
    """Any value as plain text: markup characters are escaped, newlines kept."""
    text = str(value)
    check_glyphs(text)
    return Paragraph(escape(text).replace("\n", "<br/>").replace("\t", "    "), style)


def fields(rows) -> Table:
    """Label/value pairs, labels in grey on the left."""
    table = Table(
        [[paragraph(label, CELL), paragraph(value, CELL)] for label, value in rows],
        colWidths=[175, 318],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TEXTCOLOR", (0, 0), (0, -1), GREY),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def grid(header, rows, widths, total=None) -> Table:
    """A header row repeated on every page, data rows and an optional ruled total row."""
    data = [[paragraph(v, HEAD) for v in header]]
    data += [[paragraph(v, CELL) for v in row] for row in rows]
    if total is not None:
        data.append([paragraph(v, CELL) for v in total])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitInRow=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
    ]
    if total is not None:
        style.append(("LINEABOVE", (0, -1), (-1, -1), 0.9, DARK_BLUE))
    table.setStyle(TableStyle(style))
    return table
