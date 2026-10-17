# Comparison saving, recovery and approval correction — 2026-10-14

## Problem, decision and implemented behavior

Owner O01 B08 recovered exactly one comparison, then approved because approval
was believed necessary to complete recovery. This was a critical understanding
failure, not a demonstrated database inconsistency. The original failed attempt,
observations, frozen protocol and B09 skip remain unchanged.

Implement the existing [correction brief](UX41_RECOVERY_CLARITY_BRIEF.md), preserving
FR-V2-09/10/11/12, AC-V2-09/10/11/12/13, NFR-V2-05/06/07 and UX-AC-11/13.
This supports thesis chapters 4/6/7; it is not a new lifecycle or architecture.

- **Unsaved draft:** review writes nothing. **Calculate and save comparison**
  explicitly calculates and persists; all three creation entries use the same label.
- **Saved comparison — awaiting a decision:** **Comparison saved. Approval is a
  separate choice.** Retrieval and recovery need no approval.
- **Selected plan — not yet approved:** selection and **Review selected plan**
  write nothing. **Review approval** prepares the existing read-only confirmation;
  **Approve plan** is the deliberate final action. No-award stays separate.
- **Final approved plan / Final No-award recorded:** existing immutable decision,
  audit and PDF eligibility apply. No-award has no approved-plan PDF.
- **Unconfirmed save:** the comparison may already exist. The original URL,
  payload/key, navigation guards and explicit retry are retained. The visible
  state does not call this an unsaved draft. Losing session recovery details does
  not delete backend cases. No outbox, automatic retry or replacement request.
- **Saved scenario:** analytical; decide on the original comparison. The status
  does not invite approving a child.

The shared new-comparison reset clears previous notice, selection and decision
review for both in-app navigation and a direct empty `/planning` bookmark. Pending
requests are guarded before either reset. Existing HTTP/idempotency/storage,
business/model/solver rules and backend-only PDF generation are unchanged.

## Publication/runtime baseline

Initial clean branch: `feature/T18-implementation`, local and PR #31 HEAD
`b94ff78014d03d3ee5f2253887830c3ef1e3e1ed`; main `ed4be413b11dc469307fc1bb1ed4bd6c16c17b88`.
PR #31 remains open; no merge is authorized by this work.

At that exact published HEAD, [Quality 38601702272](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38601702272)
failed the Python snippet formatting in `UX41_REASSESSMENT_RUNBOOK.md:96`;
subsequent quality steps were skipped. [Container/API 38601702451](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38601702451)
completed successfully. These are the published baseline results, not CI for this correction.

Fix only that snippet's wrapping. Local Python 3.11.16 has Reflex 0.9.12, the
runtime used in retained browser evidence. The unbounded frontend range let CI
resolve 0.10.0; the standalone requirements file still pinned 0.9.11.post1.
Both now pin 0.9.12. Refreshing the project-local editable install succeeded;
Ruff 0.17.0 matches the failing hosted formatter. No framework upgrade is performed.

## Executed checks and source identity

Broad fast gate: **677 PASS / 75 deselected**, latest broad run 206.24 s, with actual offline
ML and bundled CBC. One existing Starlette TestClient deprecation warning remains.
The deselected service/browser tests are not additional passes.

Ruff 0.17.0 format/check, compileall (including `document_adapter`), pip check,
quiet Odoo and disposable-persistence Compose config, and diff whitespace passed.
The project-local dependency refresh resolves Reflex 0.9.12. Final production
`reflex export --frontend-only --no-zip` passed; every Python file in the isolated
export copy was compared byte-for-byte with the current frontend. Node 24.20.0
was used locally; hosted integration's Node 22.22.0 remains a separate environment.

Ignored evidence root:
`.artifacts/ux41-clarity-final-727f63c0981b431f8986999a3c130505/`.
`quality-final.xml` records that broad gate. The final stale-conflict/error reset
also passed **54 focused checks**, 23.11 s, in `focus-final.xml`; the pending guard,
creation replay, decision and real CBC checks were included. Earlier passing and
failed runs remain separate. `evaluation.xml` records the separate 12-pass UTF-8
evaluation isolation. `source-final.json` records base commit, versions and exact
local on-disk source SHA-256 values.

**All 11 distinct browser tests have passing results**, not one invented 11-pass
execution: `browser-final.xml` retains five passes and the superseded new-test
assertion failure; `browser-remaining-final.xml` has **6 PASS**, 582.79 s, after
the test corrections. A further final conflict-status check passed in
`conflict-final.xml`, **1 PASS**, 104.97 s. The new recovery proof in
`.artifacts/t18-browser-05eed7cd2eba/` confirms exactly one stored case, zero final
decisions and zero PDF artifacts after genuine API downtime, exact replay,
selection/review and reopening. Desktop/320 screenshots were inspected; the
palette remains unchanged. A built-in browser inspection verified the draft
label; its temporary tab was closed. The browser suite also exercises creation,
Practice, deliberate approval/No-award, library, scenarios, supplier evidence,
keyboard/narrow/native zoom, conflicts and exact PDF access/download.

All recorded browser harnesses report owned process/Compose cleanup; owner
services/data were untouched and the existing Podman machine remains running.
No new live Odoo, stand-alone service-suite, physical-phone, screen-reader or
human session was executed. Real helper PostgreSQL was exercised by the browser
tests. Retained transaction/live benchmarks were not rerun for this frontend slice.

Owner explicitly authorized commit/push to the existing branch after local
verification. PR #31 remains unmerged. The correction commit's exact SHA and
new-HEAD CI are reported at delivery; the old baseline CI above is not promoted
to that result. No issue closure or Drive update is implied.

## Retained failed setup attempts

- A sandboxed focused test process stalled and was interrupted; no PASS inferred.
- Initial owned browser recovery saved one case and zero decisions/documents,
  then could not select a plan because CBC returned solver unavailable. The first
  elevated focused run had 40 PASS / 8 FAIL for the same absent-plan condition.
  A direct CBC probe identified the cause: this task's TEMP path contained spaces,
  which the bundled CBC command parser split. No solver code was changed.
- Repeating with the task directory's verified space-free Windows 8.3 path gave
  53 focused PASS, including actual CBC execution. The original failures/artifacts
  are retained, not relabelled PASS.
- The first full fast run gave 667 PASS / 9 FAIL / 75 deselected. The evaluation
  metadata helper decoded a dirty Unicode `git diff` with Windows cp1252 and
  raised a decoding/None-output error. Subsequent Windows runs explicitly enable
  UTF-8; this is an execution-environment correction, not an evaluator change.
- An initial broad browser run stopped at 3 PASS / 1 FAIL: the comparison test
  still requested Review selected plan after explicitly choosing No-award. The
  UI correctly used Review No-award decision. Update the affected test locator;
  retain the failed run and rerun the affected browser contracts.
- The frozen-product browser run reached 5 PASS / 1 FAIL. The new recovery test
  proved one saved case, zero decisions/documents and read-only selection/review,
  then incorrectly required an in-session selection to clear on reload. That is
  not part of this increment's contract. Check the reopened undecided record
  instead; retain that failure and run the corrected test plus unrun cases.
- The next new-test attempt reached reopening but compared a GET response's
  `idempotent_replay=false` with the replay POST's `true`. This is response metadata,
  not changed stored content. Normalize that one flag for the whole-record check;
  the exact snapshot/decision and zero-finalization assertions remain unchanged.

## Remaining acceptance and next controlled live verification

Fresh owner B08 retest is required on this corrected source: fresh 10-unit case,
neutral task instructions, genuine owned API interruption, exact recovery, one
saved case and no approval to finish recovery. Ask save/selection/approval and
session-loss questions neutrally. Record as attempt 2, retaining attempt 1. Resume
B09 after the critical retest succeeds; do not rewrite its original skipped result.
The 3–5 unfamiliar-buyer gate remains NOT ASSESSED; owner retakes are excluded.

Next, use the existing T17 fixed-group preparation and full-flow guide in an owned
helper stack with real read-only Odoo transport and the matching separately
synthetic model. Capture source/versions and exact quotation expectations; create
from the prepared Odoo review with explicit Q/date/capacity/MOQ/promised terms;
compare actual allocations/premium, save one feasible and one infeasible disruption,
return to the original and deliberately approve a plan. Reopen through the saved
library and download the PDF; compare bytes/hash and approved terms. Restart only
the owned backend with acquisition/model unavailable to prove stored retrieval;
stage a document-access failure and recover without another approval. Keep a
separate original for No-award. Use existing Odoo data; if configuration is missing,
hand its UI steps to the owner and independently verify the read-only postcondition.

This proposes no arbitrary quotation selection, observed training/promotion,
schema, ERP write-back, full redesign or repeated workload benchmark. Physical
phone, screen-reader and human acceptance are not inferred from Chromium checks.
