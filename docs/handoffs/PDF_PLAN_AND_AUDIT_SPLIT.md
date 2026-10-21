# Approved plan and audit appendix as two PDFs (ADR-036)

Date: 2026-10-21. Increment on `feature/pdf-cleanup` on top of `240f853` (merged PR #53):
code `0ca8d5b`, clean P4 evidence `5d0a6b2` (owner's commits, not pushed). Task clause: "finalize fixed
orders as PDF" (FR-V2-10/11/12, AC-V2-10/11/12; TRACEABILITY row 9).

## Problem

One approved PDF per (case, language) held the buyer's plan and the full audit appendix:
10 pages for the two-supplier P4 demo, pages 4–10 audit detail. Order lines printed the
internal product reference `(odoo:product.product:1)`, and the terms block read like
supplier commitments although the values are buyer-entered or kept-suggested (L6).

## Decision

Owner specification 2026-10-21, recorded as
[ADR-036](../adr/ADR-036-plan-and-audit-documents.md) (proposed; amends ADR-033): two
documents from the same approved snapshot and the same approved content hash —
`plan` for the buyer and `audit` for traceability. Stored artifacts stay immutable;
combined documents stored earlier become the `plan` of their case unchanged.

One deviation from the specification's wording, made for consistency with immutability:
the migration downgrade refuses not only when audit rows exist but also when v3 `plan`
rows exist, because the per-language code would reject their references and stored
artifacts are never deleted.

## Implemented behavior

| Area | Change |
| --- | --- |
| `migrations/versions/20261021_01_document_kinds.py` | `kind` column (`plan` \| `audit`, check `ck_planning_documents_kind`), PK `(case_id, language, kind)`, `reference` widened 128 → 160 (a v3 audit reference is 130 characters); existing rows become `plan` with unchanged bytes, reference and renderer version; immutability trigger disabled/enabled around the change; downgrade refuses while audit or v3 rows exist |
| `persistence/schema.py`, `persistence/planning_documents.py` | mapping and `get(case_id, language, kind)` |
| `application/planning_documents.py` | `approved_document(..., language="hu", kind="plan")`; `invalid_document_kind`; `DOCUMENT_VERSION = "t17-approved-pdf-v3"`, reference `…:{language}:{kind}:{hash}`; stored v2 (and v1 English) references accepted for `plan` only; filenames `jovahagyott-beszerzesi-terv-…`, `approved-procurement-plan-…`, `audit-melleklet-…`, `audit-appendix-…` |
| `backend/app/routes/planning_cases.py`, `dependencies.py` | `?kind=plan\|audit` (default `plan`), `X-Document-Kind` header, same error mapping (unknown kind → 422) |
| `document_adapter/approved_pdf.py` | `layout-v5`; `render_plan_pdf` / `render_audit_pdf` over one builder. Plan: summary + supplier assessment table (supplier, class, risk score) with „A pontszám nem kalibrált meghibásodási valószínűség.”; product by Odoo name only; „Tervezési feltételezések” / "Planning assumptions" with the L6 sentence; „Ellenőrzési azonosítók” / "Verification identifiers" (case ID, approved content hash, data origin, 12-character model ID, decision time, Audit-view pointer) kept together on the last order-line page when it fits. Audit: title „Audit melléklet – jóváhagyott beszerzési terv”, case ID and hash header, then the previous appendix sections unchanged |
| `frontend/planning_pdf_client.py` | `kind` parameter; accepts v3 references, plus v2/v1 only for `plan`; checks `X-Document-Kind` |
| `frontend/planning/state_decision.py`, `state_case.py`, `audit.py`, `i18n_ui.py` | Decision & PDF tab unchanged (fetches `plan`); Audit view button „Audit melléklet (PDF)” / "Audit appendix (PDF)" only for approved cases, same loading, retry and error callout as the plan PDF, inline viewer; keys `audit_pdf`, `retry_audit_pdf`, `audit_pdf_note` (HU/EN) |
| `tools/t17_demo.py`, `tools/demo.py` | demo downloads, records (bytes, pages, SHA-256, reference, content hash) and replays all four artifacts; No-award checked for both kinds |
| `tests/integration/conftest.py` | the module reset empties the disposable tables before `downgrade base` (the document downgrade now refuses while audit/v3 rows exist) |
| Docs | ADR-036, ARCHITECTURE (diagram, module and API rows), RUNBOOK (migration note, §5.4), TRACEABILITY rows 6 and 9 |

## Evidence (commands actually run)

All on `feature/pdf-cleanup` at `240f853` with this working tree (Python 3.11.15, Windows).

- Focused: `pytest tests/test_t21_documents.py` → 27 passed (new: both kinds × HU/EN with
  one content hash, four stored rows, byte-identical second download without renderer,
  model load or tree fitting; stored combined v2 row with `layout-v3`/`layout-v4` served
  unchanged as `plan` and an audit added beside it, a v2 reference refused as `audit`;
  unapproved base, scenario and No-award → 422 for both kinds; unknown kind → 422 in the
  API and `invalid_document_kind` in the application; plan text has order lines, the
  supplier table, the verification block and no provenance table, tree path, audit hashes
  or audit title; plan ≤ 1 + N + 1 pages; Audit-view state fetches `kind=audit` with the
  same failure/retry handling and requires an approved case; client rejects a wrong
  `X-Document-Kind`). `pytest tests/test_odoo_purchase_history.py -k pdf` → passed (Odoo
  case: no `odoo:product.product:` in the plan, present in the audit; HU translation and
  verbatim quotes now asserted on the audit document).
- `pytest tests/test_t17_demo.py tests/test_p4_validation.py tests/test_t17_decisions.py
  tests/test_architecture.py` → 60 passed.
- `python -m tools.dev check` (final tree) → format, lint, compile, 535 passed / 54
  deselected, `uv pip check` compatible.
- Postgres integration on the disposable test database (`planning_test`, port 55432):
  `pytest -m "integration and not e2e"` → 46 passed, 5 skipped (opt-in live Odoo
  contracts). Covers: migration upgrade keeps a combined v2 row (`layout-v3`, `layout-v4`)
  as `plan` with identical bytes, reference, renderer version and hash; audit created
  beside it; downgrade refused while an audit row exists (schema stays at head); the
  per-language downgrade round trip with v1/v2 rows seeded at `20261019_01`; four rows per
  approved case with `:{language}:{kind}:` references; UPDATE/DELETE and duplicate INSERT
  rejected (immutability trigger and PK). The first run failed with 503 on every store:
  the 130-character v3 audit reference exceeded `VARCHAR(128)`; fixed by widening to 160.
- `pytest tests/e2e -m e2e --browser chromium` → 3 passed (216 s).
- `python -m tools.dev demo` on the uncommitted tree (applied `20261021_01` to the
  development planning database, then ran the demo) → "Demonstration complete in
  20.755 s", exit 0, `dirty: true`; superseded by the owner's rerun below.
- Owner's rerun after committing the code (`0ca8d5b`; evidence committed alone as
  `5d0a6b2`): `P4_DEMO_REPORT.json` (2026-10-21T19:06:20Z, `0ca8d5b`, `dirty: false`,
  19.867 s): plans unchanged (80 + 120 at 288,608 HUF; 120 + 80 at 293,132; balanced
  100 + 100 at 295,800); approval of plan 1, separate No-award; four artifacts with the
  same approved content hash `526fd3ad…`: HU plan 3 pages / 29,453 bytes, HU audit 7 /
  35,587, EN plan 3 / 28,287, EN audit 7 / 34,110; stored replay without Odoo and model
  passed (13 operations; all four PDFs byte-identical; No-award 422 for both kinds).
  Previously the combined document was 10 pages. `P4_MILP_EVALUATION.json` was not rerun:
  it does not check the PDF.
- Text of the real Odoo plan (HU) read page by page: product „[PDSS-GEN-P1-PRD-01] [GEN]
  Steel bracket M8” without reference, supplier table with all four suppliers,
  „Tervezési feltételezések” + L6 sentence on each order-line page, verification block on
  page 3.
- Built-in browser against the running dev API (8000, `--reload`) and UI (3000): approved
  demo case → Audit view → „Audit melléklet (PDF)” loads the 7-page audit PDF in the viewer
  (title, case ID and hash header, model, tree paths visible); at 375 px no horizontal
  overflow, button and note wrap; error state verified by a temporary forced client
  failure (reverted, file re-checked and tests rerun): amber alert „A PDF most nem érhető
  el…” and label „Audit melléklet újra”, then a successful retry; No-award case: no
  button.
- `tools.dev demo` exit code: the earlier side finding (exit 0 after "Demonstration
  incomplete") was not reproduced — with `run` patched to raise, `tools.dev demo` exits 1.
  The 0 was most likely the exit status of a shell pipeline; no change made.

## Limitations and unrun gates

- The development planning database is now at `20261021_01` and holds audit rows, so its
  downgrade is refused by design; the integration fixture empties the disposable test
  tables before resetting the schema.
- Hosted CI not run (local evidence only). P4 MILP evaluation and ML report check not
  rerun (unaffected).
- Order-line pages still show supplier and quotation Odoo references in parentheses (only
  the product reference was removed, as specified). The shared PDF viewer's download link
  still reads „Jóváhagyott PDF letöltése” / "Download approved PDF" for the audit appendix.
- Cases approved before the split keep their combined (plan + appendix) document as
  `plan`; that is the immutability rule, not a defect.
- ADR-036 is proposed in the repository only; Drive updates (03 ADR-036, 06 FR-V2-12
  note, 07, 08 §9, 01 6.7) wait for the owner's request after merge.

## Thesis chapter

Chapter 4 (design: two documents from one approved snapshot, ADR-036), chapter 6
(implementation: storage kind, migration, renderer split, Audit-view download) and
chapter 7 (validation: P4 demo with four byte-identical stored artifacts).
