# Save, recovery and approval clarity — #41 correction brief

Date: 2026-10-14. Status: implemented locally; technical verification/publication
recorded in [the correction handoff](UX41_CLARITY_HANDOFF.md). A fresh owner retest
is recorded in the [dated assessment](UX41_ASSESSMENT.md): technical recovery PASS
with assisted owner sign-off; independent comprehension remains unverified.
B08 attempt 1 remains FAIL and novice acceptance NOT ASSESSED.

## Observed problem

In owner O01 B08, exact request/key recovery created one new case and preserved
all earlier records. The owner then approved Alternative 1 because approval was
believed necessary for recovery. The owner did not understand an unconfirmed
response or session-loss limits. This is a critical UX finding, not evidence of
database inconsistency or an accidental click. Preserve the failed first attempt
in [owner observations](UX41_OWNER_OBSERVATIONS.csv) and the
[assessment](UX41_ASSESSMENT.md); clarification alone does not close it.

## Bounded correction

- Make three states distinct: unsaved draft; saved comparison with no final
  decision yet; permanent approved/No-award decision. A saved comparison remains
  available without approval; approved document eligibility is a separate outcome.
- Name creation **Calculate and save comparison**, and show clear saved feedback:
  **Comparison saved. Approval is a separate choice.** Keep a prominent route to
  review/reopen saved results; do not imply finalization completes the save.
- Explain uncertainty in buyer terms: the comparison may already be saved but its
  response was not received. Recover the same save to retrieve or complete it once.
  Preserve exact inputs/key and context guards; do not create a replacement.
- Explain the session boundary: losing the Reflex session can lose its pending
  recovery details; it does not delete an already saved case. Keep the existing
  copyable recovery record and support path. Promise no durable outbox or automatic
  restore. Keep detailed technical references progressively disclosed.
- Keep approval visibly separate and deliberate. Its review/confirmation records
  the chosen plan, approved terms and audit decision once. No ERP order is created.
  Clear stale success feedback when preparing a new comparison: the B08 review
  still displayed the preceding Final decision saved message.

## Architecture and verification

Reuse frontend planning state/components and existing HTTP contracts. Do not add
database rollback, an ephemeral-simulation endpoint, an outbox, Odoo writes or
frontend database access. The existing atomic/idempotent persistence contract stays.

Inspect shared callers before implementation. Verify any notice/reset state change,
update affected UI callers/tests, run required checks, and inspect desktop/narrow
views. Keep the active first-attempt runtime/source evidence intact until a revised
runtime is deliberately prepared. Record the actual copied source hashes.

Retest B08 on a fresh standard 10-unit case, retaining attempt 1 separately. Stage
the API outage after review; observe explicit recovery with the same key/intent and
one stored case, with no extra approval to complete recovery. Ask the save-versus-
approval and uncertainty/session-loss questions neutrally. Resume B09 only after
the critical finding is resolved through a recorded retest. Version the protocol
if prompts/fixtures/scoring change; never retrospectively rewrite the first attempt.

Owner retakes are excluded from the unfamiliar-buyer denominator. The 3–5-person
gate, zero unintended finalizations/unresolved critical misunderstandings and
remaining accessibility checks stay unchanged. Technical PASS is not human acceptance.
