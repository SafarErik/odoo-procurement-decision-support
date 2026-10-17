# Deliberate approval and separate No-award — #38 handoff

Date: 2026-10-13. Parent: [#42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42).
Task: [#38](https://github.com/SafarErik/odoo-procurement-decision-support/issues/38).
Starting HEAD: `0acad1286f6691e697fc09babae7205eeae855d4`.
Local implementation and technical acceptance complete; commit/push/merge remain
with the user. No issue or Drive update was made.

## Problem → decision → implemented behavior

The original approval form submitted its irreversible intent immediately. A buyer
now reviews that exact saved allocation and attribution before confirming once.
For example, selecting Alternative 1 shows 109 EUR, the 8/2 supplier split with
promised dates, exact exposure `9661/50000`, the original identity/context, actor
and reason. Selection and review do not save a decision or allocate a request key.

The existing form validates the original-base eligibility, actor, demonstration
acknowledgement and required alternative/No-award reasons. A controlled alert
dialog freezes the reviewed intent privately on the Reflex server. Cancel/Escape
retains the entered form without writing. Confirm uses the existing HTTP route,
snapshot hash and idempotency mechanism, with immediate duplicate suppression,
loading/pending guards and stale-context rejection. An uncertain response retains
the original URL/body/key and requires explicit exact retry; navigation remains
guarded. Review clearing never alters the pending payload.

No-award has its own action and reasoned confirmation, approves no allocation and
offers no approved PDF. A saved outcome focuses its heading and replaces editing
with immutable choice, actor, reason and UTC record time. Global and Audit outcome
headings have distinct IDs. Practice/source and synthetic-exposure limitations,
caller-supplied attribution and no Odoo order creation are explicit before saving.
Existing approval PDF viewing/download remains unchanged for #40 to refine.

The dialog starts on Cancel, contains focus and returns it to Review when cancelled.
Its exact review scrolls separately so actions remain visible on narrow screens.
Validation alerts and uncertain-save recovery receive focus. Frontend composition
remains in `frontend/planning/`; FastAPI, application/core, solver/ML, Odoo adapter,
persistence, migrations, API contracts and dependencies were not changed.

## Evidence

Python 3.11.16, Reflex 0.9.12, PuLP 3.3.0/real CBC and scikit-learn 1.8.0.
Service checks used separately named disposable helper PostgreSQL projects with
synthetic credentials, real FastAPI/Reflex and owned localhost tunnels. Stored
reopening/retry worked with model configuration removed. No owner or Odoo database
was reset. Execution and cleanup are in the [decision runbook](UX38_DECISION_RUNBOOK.md).

| Check | Executed result and scope | Retained evidence |
| --- | --- | --- |
| Required full fast suite | 668 PASS, 72 service/browser tests deselected; mandatory ML/CBC actually executed | `.artifacts/ux38-fast/result.xml` |
| Final affected tests | 69 PASS after final focus/layout refinements: read-only review/cancel, frozen intent, required reasons, stale/child guards, exact lost-response replay, existing selection/retrieval/navigation | `.artifacts/ux38-final-focus/result.xml` |
| Final browser selection | 2 PASS: exact alternative/reason validation, Cancel/Escape, single-save double-click, immutable reopening/Audit, separate No-award with actual stopped-API uncertainty, guarded exact retry, no No-award PDF and UI/API child rejection; existing comparison selection callers updated | `.artifacts/ux38-browser-verified/result.xml`; `.artifacts/t18-browser-443332a1aac6/`, `t18-browser-8b613c2a64d4/` |
| Browser reflow/keyboard | Same final tests: long Hungarian actor/unbroken reason; safe Cancel, validation/recovery/saved focus; 1280/1440/768/390/320 without document overflow or offscreen Cancel. Comparison regression also passes native 200% zoom and 3/5/10 supplier cases | Same roots, `decision-confirmation-*.png`, `comparison-200-percent.png` and request/server logs |
| Existing Practice and approval/PDF | 2 PASS in the earlier mixed run: all Practice tasks, immutable alternative approval/PDF, model-unconfigured stored retrieval and real outage recovery. These preceded the final dialog/focus corrections; the mixed run's new-test failure is not an overall suite PASS | `.artifacts/ux38-browser2/result.xml`; `.artifacts/t18-browser-5470f7bca0c0/`, `t18-browser-1cf2a4ca2baa/` |
| Real PostgreSQL | 14 PASS, no skips: actual contending finalization, replay/conflict, immutable content, rollback, exact PDF binding, render-once contention and render rollback | `.artifacts/ux38-postgres/result.xml`; `.artifacts/t18-browser-6ce70c91b5d4/evidence.json` |
| Built-in browser | Final-source desktop/320 exact confirmation, named review, safe Cancel focus, keyboard body scrolling, visible actions and Cancel-retained actor/reason/selection | `.artifacts/t18-browser-0048a8865117/builtin-confirmation-desktop.png`, `builtin-confirmation-320.png` |
| Static/runtime | Ruff format/check, compileall, pip check, Odoo Compose configuration and whitespace checks PASS. Actual Reflex startup compiles changed UI; final Impeccable detector `[]` | Executed terminal checks; configuration check starts no Odoo services |

The full fast run preceded the final accessibility/focus/layout corrections; final
affected tests, two browser flows and static checks cover those corrections.
PostgreSQL contracts were unchanged afterward, so passing transaction checks were
not repeated. Native zoom evidence here covers the comparison/form, not a physical
phone or an independently zoomed confirmation dialog.

All owned stack evidence records process/tunnel/Compose cleanup. The preview tab
was closed and its viewport override reset; artifacts remain for inspection.
The existing shared Podman machine was started for service checks and remains
running. The user's existing browser tab and application data were left untouched.

## Retained failures and corrections

Initial focused assertions used an incorrect fixture cost and non-normalized
Reflex focus reference; the saved fixture is 109 EUR and focus refs use underscores.
Browser setup initially failed while the existing Podman machine was stopped.
The subsequent mixed run caught a dialog title ID breaking its accessible name;
explicit `aria-labelledby` fixes it. Installed Radix Title did not forward the
attempted focus attribute, so Cancel is the initial focus target. Browser/built-in
checks then caught premature saved-heading focus and an offscreen narrow Cancel;
mount-time focus and a separately scrolling review resolve both. A later browser
assertion compared equivalent `Z` and `+00:00` UTC formats; it now normalizes that
timestamp, while API retrieval still asserts the entire decision unchanged.
Failed XML/logs remain under `.artifacts/ux38-*`, without relabelling them passes.
No backend validation or accepted architectural boundary was relaxed. The existing
Starlette/httpx deprecation remains.

## Limits → traceability → next

Fresh live Odoo, hosted/new-HEAD CI, screen-reader speech, physical phones and
owner/novice usability sessions were not run. Keyboard/DOM/reflow evidence does
not establish whole-app WCAG or business-usability acceptance. Practice shares
application storage, actor references are not authenticated identities and recovery
is session-local. Browser refresh/session loss still needs the established recovery
record; durable recovery/document UX belongs to #40.

UX-AC-11; FR/AC-V2-11, AC-V2-09/10/12; NFR-V2-06/07; UX29-05/06 support thesis
chapters 4/6/7 through exact deliberate selection, immutable audit and measured
technical acceptance. The approved specification/FR/AC identifiers and published
dependency graph are unchanged. Next: #39 readable explanations; #40 safe recovery
and approved-document reopening is also unblocked. #41 human reassessment and
thesis closure remain separate.
