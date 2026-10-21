# ADR-036 (proposed): Approved plan and audit appendix as two documents

Status: **proposed** — owner decision 2026-10-21; not yet registered in Drive
03_ARCHITECTURE_DECISIONS (Drive is the canonical ADR register; registration happens
after merge on the owner's request). Amends ADR-033 (one stored approved PDF per
case and language).

## Context

Under ADR-033 one PDF per (case, language) held both the buyer's plan and the full
audit appendix. For the two-supplier P4 demo that was 10 pages, of which pages 4–10
were audit detail (tree paths, provenance table, solver record, hashes). The buyer
who sends order lines to suppliers had to skip most of the document, and the order
lines showed internal references such as `(odoo:product.product:1)`.

## Decision

Render two documents from the same immutable approved content and the same approved
content hash:

1. **Approved procurement plan** (`kind = "plan"`, default): summary page with a
   compact supplier assessment table (supplier, class, risk score, "not a calibrated
   probability"), one order-line page per supplier with a non-zero quantity, and a
   short "Verification identifiers" block (case ID, approved content hash, data
   origin, short model ID, decision time, pointer to the Audit view). The product is
   shown by its Odoo name only. The terms block is called "Planning assumptions" and
   states that the values are buyer-recorded or kept-suggested planning terms, not
   supplier commitments (L6). Target: 1 + N suppliers + at most 1 page.
2. **Audit appendix** (`kind = "audit"`): title, case ID and approved content hash,
   then the previous appendix sections unchanged (data source, model, assessments with
   tree paths, optimization, decision log, content identity, field-level provenance,
   Hungarian translation plus verbatim quote of the fixed English record sentences).

Storage and API:

- `planning_documents` gains `kind` (`plan` | `audit`); primary key
  `(case_id, language, kind)`; `reference` widens to 160 characters. Migration
  `20261021_01` labels every existing row `plan` without touching bytes, reference
  or renderer version; its downgrade refuses while audit or v3 rows exist, because
  stored artifacts are never deleted.
- Reference `t17-approved-pdf-v3:{case}:{language}:{kind}:{hash}`. Combined documents
  stored earlier (v2 references, and the pre-P2 v1 English reference) remain valid and
  are served unchanged as `plan`; a case with only such a row still gets a v3 audit
  document on request.
- `GET /{case_id}/approved-pdf/{content_hash}?language=hu&kind=plan|audit`; `plan` is
  the default, so existing callers are unchanged. Response header `X-Document-Kind`.
  No-award, unapproved and scenario cases have no document of either kind (422);
  an unknown kind is 422.
- Renderer `layout-v5`: `render_plan_pdf` and `render_audit_pdf` share one builder.
- UI: the Decision & PDF tab keeps the plan; the Audit view offers "Audit melléklet
  (PDF)" / "Audit appendix (PDF)" for approved cases.

Unchanged: the immutable approved snapshot and decision records
(`t17-final-decision-v1`), the database immutability trigger, and the rule that a
download never reads Odoo, re-scores or re-optimizes (FR-V2-12, ADR-026).

## Alternatives considered

- Keep one document and move the appendix behind a bookmark: still a 10-page file sent
  to buyers and suppliers.
- Drop the PDF appendix and rely on the Audit view only: loses a durable, hash-bound
  audit artifact outside the system.
- Re-render stored combined documents as plan-only: breaks artifact immutability.

## Consequences

- Up to four stored artifacts per approved case (HU/EN × plan/audit), each rendered
  once on first request.
- Cases approved before the split keep their combined plan document; only their audit
  document is new.
- Two documents must be cited together in audit discussions; the shared approved
  content hash links them.
