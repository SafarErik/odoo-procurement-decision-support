# Safe recovery and approved document access — #40 handoff

Date: 2026-10-13. Parent: [#42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42).
Task: [#40](https://github.com/SafarErik/odoo-procurement-decision-support/issues/40).
Starting/current HEAD: `905e94474d72e27930425e807a1dcfc64464fe90`.
Local implementation and technical acceptance complete. Changes remain unstaged;
commit, push, merge and issue closure remain user-controlled. No Drive/issue write.

## Problem → decision → implemented behavior

Uncertain saves were safe but technical; a definitive finalized conflict still left
approval controls available. The PDF viewer rendered every page continuously and
offered no page indicator/previous/next. Keep existing HTTP projections/state and
React-PDF, with no document or persistence redesign.

Rejection, conflict, unavailable opening, uncertain save and document failure now
give distinct actions and support detail. An uncertain create/scenario/decision
keeps its original URL/payload/key and guarded context. Explicit retry resends that
exact intent; it never automatically retries or assumes failure means nothing was
saved. Copyable recovery proof and session-loss limits are visible. A finalization
HTTP 409 pauses approval and offers **Reopen saved decision**, a GET only. Failed
access or no recorded outcome preserves context/proof and paused actions. Reading
the saved outcome replaces stale controls and identifies its actor/terms; a competing
buyer's decision is not claimed as this buyer's successful approval.

For an approved original, **Saved approved terms** retains product, demand, required
date, exact cost and every supplier quantity/promised date. For example, the saved
109 EUR alternative remains visible when document GET fails. Practice access,
synthetic evidence and caller-supplied actor limits remain explicit. The viewer
renders one page with announced **Page n of N**, labelled previous/next and disabled
end controls. Fit/150/200/300% changes view scale inside its own scroll region.
Download still saves all original PDF bytes. **Retry approved PDF** retries document
GET only; case/content hash are available for support. Approval, selection and Audit
survive the failure. No-award, undecided bases and children retain existing eligibility.

Changes stay in frontend clients and existing planning state/page/decision/viewer,
plus meaningful tests and documentation. No backend/application/core/ML/solver/Odoo/
persistence contract, renderer/content migration, dependency or service change.
The dated baseline routing guide's prospective T17 text is historical; current
README and #38 establish the already implemented approval/PDF workflow.

## Executed verification

Python 3.11.16, Reflex 0.9.12, actual PuLP 3.3.0/CBC and scikit-learn 1.8.0.
Browser fixtures use real FastAPI/Reflex/Chromium and owned disposable PostgreSQL,
offline synthetic preparation and stored work with model configuration removed.
The [runbook](UX40_RECOVERY_RUNBOOK.md) owns prerequisites, commands and cleanup.

| Check | Actual result/scope | Evidence |
| --- | --- | --- |
| Final required fast suite | 675 PASS, 74 service/browser tests deselected; actual ML training/reload/inference and CBC; retained immutable decision/PDF tests | `.artifacts/ux40-fast-final/result.xml` |
| Focused development contracts | 72 PASS; lost-success ASGI response replay, definitive/recovering conflicts, stored guards and original approval/document contracts. Final fast adds focus/no-record assertions | `.artifacts/ux40-focus/result.xml` |
| Final real buyer/PDF browser | PASS: create, finalization, GET and PDF with actual stopped-API failures; explicit same payload/key replay; guarded navigation; immutable reopening; five PDF pages, keyboard previous/next/end controls and exact backend/download SHA-256 | `.artifacts/ux40-browser-final/result.xml`; `.artifacts/t18-browser-8a490d88e200/` |
| Final real scenario/conflict browser | PASS: actual scenario outage; retained original URL/payload/key across Cases bookmark; exactly one stored child and unchanged base; competing buyer's actual HTTP 409; paused approval/focused recovery; failed GET retained proof; explicit GET reopened recorded minimum-cost decision, no further finalization POST | Same JUnit; `.artifacts/t18-browser-50001af45c65/` |
| Session/edge/accessibility | Same final browsers PASS: fresh isolated context had no pending record/action while original retained proof; long non-Latin/unbroken supplier; 1440/768/390/320 document and 1280/390/320 conflict widths; native browser zoom 200% independently of PDF zoom | Same roots; `approved-document-*.png`, `approved-document-browser-200-percent.png`, `decision-conflict-*.png`, traces |
| Built-in browser | Desktop/320 PDF keyboard page 1→2→1 and scoped 200% PDF zoom; real owned API stopped; saved approval/109 EUR terms, retry/support identity and narrow error remained visible | `.artifacts/t18-browser-a985f3fb4d0d/builtin-approved-desktop.png`, `builtin-approved-320.png`, `builtin-document-error-desktop.png`, `builtin-document-error-320.png` |
| Static/runtime | Ruff format/check, compileall, pip check, Odoo Compose config, diff whitespace PASS; actual final Reflex startup/compilation; UI detector `[]` | Executed local gates; Compose configuration starts no Odoo service |

Final approved case: `14f021a7-2b73-4008-bb60-a89a0c15c7e1`.
Approved-content hash: `8231bfe62413e8deeae7e8a88b94ee1525191569a1cde1c3e74bf86dece475f0`.
Exact PDF SHA-256: `8fc2af5f8f06dcdb0a3d02b3bee7d2488b5ad659903e70733e48340e5bf8a39b`.
Scenario case: `3edd1e8b-29f4-42a1-a819-1c7f0eaf8618`, original
`b0b0ab43-1737-443f-8529-fe3f87691429`.

Initial browser run retained **2 failures**: the new checks used a Cases link locator
where the existing guarded control is a button. `.artifacts/ux40-browser/result.xml`
and roots `t18-browser-535423c5f713`, `t18-browser-3945a1021844` retain that evidence.
After correction, both tests passed in `.artifacts/ux40-browser-confirm/result.xml`
with roots `t18-browser-f31d71bbe268`, `t18-browser-480c62cae811`. The final rerun adds
fresh-session and long-label/focus assertions. The initial full fast suite also
passed 675; the final gate followed the recovery-focus/preview-status change and
additional no-record assertion. Built-in images predate those two small focus/status
changes; final compiled browsers/fast/static checks cover the final source.

Fixture/preview `evidence.json` confirms owned process/tunnel/Compose cleanup for
all runs. The preview's API process identity/port was verified before stopping it
for the error inspection. Its tab was explicitly closed and viewport reset while
the frontend was live, before service teardown. Owner services, the existing Cases
tab and application/Odoo data were untouched; shared Podman remains running.

## Limits, traceability and next capability

Recovery remains session-local; fresh-session evidence does not establish safe tab
closure, cross-tab coordination or durable restoration after a server restart.
Copied JSON is support evidence only. Synthetic exposure remains uncalibrated;
Practice shares application storage and does not rewrite PDF provenance. Actor
attribution is audit text, not authenticated buyer identity.

Standalone PostgreSQL rollback/contention tests were not repeated: their contracts
are unchanged and #38's evidence remains historical. Current real-stack browser
checks verify affected saves/conflict/retrieval and byte-identical stored documents.
Live Odoo, hosted/new-HEAD CI, physical devices, screen-reader speech, owner tasks and
unfamiliar participants remain unverified/NOT ASSESSED. No library benchmark rerun
was needed. Existing Starlette/httpx deprecation remains a warning; no upgrade was made.

UX-AC-13/14; FR/AC-V2-09/10/11/12; NFR-V2-05/06/07; UX29-06/08/09 support the official
Python UI, immutable storage/human decision and approved-document obligations, with
technical evidence for thesis chapters 4/6/7. Approved criteria remain unchanged.
Next: #41 complete buyer reassessment, including the approved 3–5 unfamiliar
participants/80% independent completion and zero unintended finalizations or
critical misunderstandings gates. Local technical PASS does not establish human
usability acceptance or close T19 thesis work. User action: review the diff and
commit/publish/merge when ready; no missing input blocks this local implementation.
