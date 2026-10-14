# Readable supplier assessments and exact Audit evidence — #39 handoff

Date: 2026-10-13. Parent: [#42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42).
Task: [#39](https://github.com/SafarErik/odoo-procurement-decision-support/issues/39).
Starting HEAD: `abff6af0bed5b3e63b6f060f44116d7a5f9baa6b`.
Local implementation and technical acceptance complete. Commit/push/merge and
issue closure remain user-controlled; no Drive or issue update was made.

## Problem → decision → implemented behavior

Reference timing/applicability were buried, ordinary plan notes included raw solver
prose, and Audit opened a large technical block without presenting all recorded
model/path/version fields. Keep the existing projections and stored-only HTTP flow,
and organize readable interpretation separately from exact records.

Suppliers now leads with the saved class, generated receipt sample, history window,
UTC reference and saved time/quantity applicability. Rounded exposure is explicitly
approximate and uncalibrated. Branch explanations remain optional; synthetic
history/authority limitations stay visible. For example, a zero minimum-cost
allocation says **not selected**, while an actual saved outage says **excluded:
declared unavailable**. Notes translate recorded codes, including MOQ, price/delivery
bounds and concentration; Reflex does not evaluate those rules. Infeasible children
retain saved assessments/diagnostics and original lineage without inventing plans
or reclassifying suppliers.

**Inspect exact evidence in Audit** uses existing guarded view navigation and
focuses the Audit heading. Native disclosures organize inputs/policy/allocations/
provenance, supplier tree/model evidence and the complete saved snapshot. All
recorded node/leaf IDs/support, feature/path values, model/training/dataset/mapping/
runtime metadata, solver records and scenario comparison remain accessible in JSON.
Pretty-printing preserves values, not canonical hash bytes. Exact final-decision/
approved content remains. Tables retain readable columns in labelled local scroll
regions; long JSON has bounded keyboard scrolling. The development checklist appears
in Practice/empty-entry help rather than every saved case.

Changes stay in the existing frontend HTTP projection and planning result/audit/page
modules. No backend/application/core/solver/model/Odoo/persistence, API contract,
migration, infrastructure or dependency changes. No training, executable artifact
selection, upstream refresh, source promotion or inspection write was introduced.
The older baseline routing guide's prospective approval/PDF status is dated;
current README/#38 evidence establishes those existing capabilities.

## Executed evidence

Python 3.11.16, Reflex 0.9.12, real PuLP 3.3.0/CBC and scikit-learn 1.8.0.
The [runbook](UX39_EVIDENCE_RUNBOOK.md) owns prerequisites, commands and cleanup.
Browser fixtures use disposable helper PostgreSQL, real FastAPI/Reflex/Chromium,
offline synthetic preparation and model-unconfigured stored reads. No application
or Odoo database reset was performed.

| Check | Actual result/scope | Retained evidence |
| --- | --- | --- |
| Required fast suite | 673 PASS, 73 service/browser tests deselected; mandatory ML training/reload/inference and CBC executed | `.artifacts/ux39-fast/result.xml` |
| Focused contracts | 57 PASS: complete exact projection/reference time, no mutation, missing identity/nonfinite/observed-source rejection, zero/exclusion/infeasibility distinction, existing selection/approval/recovery | `.artifacts/ux39-focus-confirm2/result.xml` |
| Final supplier/Audit browser | PASS: original plus feasible/infeasible outages; classes/count/cutoff; long non-Latin/unbroken identity and missing business-name fallback; source limits; keyboard disclosure/Audit focus; exact input fields/full JSON equality; unchanged saved cases/no inspection POST | `.artifacts/ux39-browser-verified/result.xml`; `.artifacts/t18-browser-d065b997274a/` |
| Reflow/zoom/feedback | Same final test PASS: 1280/1440/768/390/320, actual ArrowRight table and PageDown JSON scrolling, native 200% zoom, real stopped-API different-case GET alert/cleared stale content and stored reopening | Same root, `supplier-audit-*.png`, `supplier-audit-200-percent.png`, API/request logs |
| Approval regression | PASS in initial mixed run: #38 alternative review/cancel/single-save, immutable reopening/Audit IDs, No-award recovery and child rejection. Predates the table-width-only fix; new-test fixture failure means the mixed run is not an overall suite PASS | Passing test in `.artifacts/ux39-browser/result.xml`; `.artifacts/t18-browser-ab21d222d339/` |
| Built-in browser | Final desktop/320 Suppliers/Audit; visible limits/timing; Audit heading focus; 768px table inside a 198px focusable region, ArrowRight scroll 40; document width 305 at viewport 320 | `.artifacts/t18-browser-957e90748c48/builtin-suppliers-desktop.png`, `builtin-suppliers-320.png`, `builtin-audit-desktop.png`, `builtin-audit-320.png` |
| Static/runtime | Ruff format/check, compileall, pip check, Odoo Compose config and diff whitespace PASS; actual Reflex startup compilation; detector `[]` | Executed terminal gates; configuration check starts no Odoo services |

Fast/focused runs preceded the table-width-only correction; final browser, built-in
layout/keyboard and static checks verify it. Projection/business contracts were
unchanged afterward. No standalone transaction rerun or new timing benchmark was
needed: persistence/finalization/PDF contracts are untouched, and #38's real
PostgreSQL evidence remains historical. Browser storage equality is current read
evidence.

Owned fixture/preview records confirm API/Reflex/tunnel/Compose cleanup. The shared
Podman machine remains running. Viewport override was reset through a blank owned
tab, which was closed. Browser-control policy rejected the expired preview's
internal error-page URL and blocked its explicit tab closure; it remains unmarked
for normal turn cleanup. Automatic tab cleanup is not independently verified.
The user's original tab/data were not manipulated.

## Retained failures and corrections

Two sandboxed focused runs stalled and were stopped without a PASS claim. A retry
lacked its basetemp parent (35 setup errors/22 passes); the documented owned parent
resolved setup and 57 tests passed. Early Ruff formatting/import/line-length failures
were corrected. The initial browser fixture exceeded the existing 255-character
identity limit and correctly received HTTP 422; its long identity now stays within
that contract. The next run found squeezed narrow columns; scoped table minimum
widths resolve that. A later outage assertion reloaded the same cached Reflex case,
which legitimately required no fresh GET. The final test instead opens a different
case with the API stopped, verifies the failed GET/alert, then stored reopening.
No cache contract or backend validation was weakened. Failed XML/logs remain in
`.artifacts/ux39-*`, never relabelled passes. The preview expired before an additional
missing-case probe, so that probe did not verify application feedback; the final
browser verifies actual API-outage feedback. The existing Starlette/httpx deprecation
remains.

## Limits → traceability → next

Live Odoo, hosted/new-HEAD CI, physical phones, screen-reader speech and unfamiliar
participants were not assessed. This is technical acceptance, not whole-app WCAG,
calibrated model validity or final buyer-usability acceptance. Practice shares storage,
actor text is not authenticated identity and recovery remains session-local.
Impeccable reported an unset optional showcase build-path setting; this scoped Reflex
work uses existing code, with no design/config drift repair.

UX-AC-12; FR-V2-02/03/07/09, AC-V2-02/03/07/09; NFR-V2-03/07; UX29-04/10 support
chapters 4/6/7 through explainable saved evidence, source limits and measured technical
acceptance. Approved criteria and dependencies are unchanged. Next: #40 safe recovery
and approved-document reopening; #41 buyer reassessment and T19 closure remain separate.
