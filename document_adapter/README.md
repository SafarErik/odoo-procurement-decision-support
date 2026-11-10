# document_adapter

ReportLab rendering of the two approved documents (ADR-036), in Hungarian or English,
from validated approved content only: the **approved plan** (summary, supplier
assessment table, one purchase-order proposal page per supplier) and the separate
**audit appendix** (everything needed to trace how the plan was made).

## Entry points

- [approved_pdf.py](approved_pdf.py) — the entry point: `render_plan_pdf` and
  `render_audit_pdf` return the PDF bytes and the renderer version.
- [plan_document.py](plan_document.py), [audit_document.py](audit_document.py) — the pages
  of each document.
- [texts.py](texts.py) — every sentence and label of both PDFs, HU and EN.
- [formatting.py](formatting.py) — numbers, dates, money and recorded values.
- [layout.py](layout.py) — font ([fonts/](fonts/), DejaVu Sans), paragraph styles, tables.

The renderer version (ReportLab, font, `layout.LAYOUT_VERSION`) is stored with each
document; the document contract `t17-approved-pdf-v3` is in
`application/stored_contracts.py`.

## Imports

- May import: `application` (stored content, supplier-overview labels),
  `supplier_evaluation.contracts` (history vocabulary), ReportLab.
- Must not be imported by `decision_core` or `frontend`; the browser only receives bytes
  through the backend.

## Tests

`tests/test_approved_documents.py`, plus the PDF steps of `tests/test_full_http_flow.py`;
see [docs/TESTING.md](../docs/TESTING.md).
