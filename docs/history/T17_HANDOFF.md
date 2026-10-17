# Saved human approval and No-award — 2026-10-09

## Result and implementation boundary

Issue [#20](https://github.com/SafarErik/odoo-procurement-decision-support/issues/20)
is implemented on the user-created `feature/T17-implementation` branch, starting
at planning merge `f0c5552`. The buyer explicitly selects a proven saved
original-base plan or records reasoned No-award through Reflex -> FastAPI ->
PostgreSQL. Reopening and exact retry return the original human outcome and
server-recorded UTC time. Changes are uncommitted; publication, issue closure,
merge and exact-new-SHA CI remain pending user review.

This is the first vertical slice from the [planning handoff](T17_PLANNING_HANDOFF.md)
and [published tickets](T17_TICKET_BREAKDOWN.md). It supplies local controlled
AC-V2-11 evidence and FR-V2-09/10/11 behavior, with AC-V2-10 and V1 regression
coverage. PDF/AC-V2-12 (#21) and complete controlled demonstration/AC-V2-13 (#22)
remain open. The official task, requirements and accepted architecture are unchanged.

## Behavior and integrity

- Plans has an explicit choice with no default, bounded actor audit reference,
  mandatory rationale for alternatives/No-award and explicit demonstration
  acknowledgement. Stress children have no action and backend finalization fails.
- Pure checks validate the saved contracts, source joins, risk mapping, plan
  constraints/metrics and recorded stage proof. There is no Odoo acquisition,
  model load/training/inference or solver execution during approval/reopening/retry.
  A retained minimum or earlier proven alternative remains eligible after later
  calculation failure; audit/content preserve the solver outcome and incomplete comparison.
- `20261009_01` adds `planning_final_decisions`, linked to the original base;
  case/key uniqueness and immutable UPDATE/DELETE triggers protect it. Original
  planning snapshots/hashes remain unchanged. Finalization advisory locks use
  their own namespace, and the audit/content are committed atomically in one row.
- `t17-final-decision-v1` records normalized intent, one-time server UTC audit,
  caller-supplied actor attribution and controlled-demo label. Approval embeds
  `t17-approved-planning-v1`: exact case/hash/index, selected allocation, complete
  saved planning evidence and human audit, identified by canonical SHA-256.
  No-award has neither approved content nor an approved-content hash.
- Same finalization key/semantic intent returns 200 with unchanged content/time.
  Different intent, cross-case key reuse or later competing finalization returns
  409. Malformed stored evidence fails closed with the sanitized existing 503
  convention. The PoC token remains on the Reflex server; the actor reference
  is explicitly **not authenticated buyer identity**.
- Reflex preserves the exact pending URL/payload/key after an uncertain response,
  blocks replacement submission and requires explicit retry. Stored GET and
  exact creation replay include any later saved final decision. Errors cannot
  present an unconfirmed save as approval.

Code follows the existing layers: `application/planning_decisions.py`, thin
planning routes/schemas, `persistence/planning_decisions.py` and the existing
planning unit of work; `frontend/planning/decision.py` composes the current state,
HTTP client, Plans and Audit. No new dependency or configuration option was added.
The run instructions are in [the decision walkthrough](LOCAL_DEVELOPMENT_AND_SSH.md#saved-human-decision)
and [persistence guide](PERSISTENCE_DEVELOPMENT.md).

## Verification

Current final counts/checks are recorded in the dated
[implementation log](IMPLEMENTATION_LOG.md). Focused HTTP/client/state checks
also cover invalid intent, missing/no-plan approval, corrupted evidence/content,
retained reference/alternative, commit failure, keys and authentication. The
controlled hybrid test acquires quotations through the mocked read-only adapter,
uses actual offline ML/CBC to create a case, then disables Odoo/model/solver before
approval and creation replay. This is no fresh live-Odoo claim.

Real disposable PostgreSQL checks cover V1/V2 regressions and T17. The race tests
hold an external advisory lock and observe both requests waiting in PostgreSQL
before release; identical requests yield 201/200, conflicting intents 201/409,
and exactly one row survives. They also test rollback after insert, direct
UPDATE/DELETE rejection, base-only insert and unique keys.

Built-in browser acceptance used real Reflex/FastAPI/PostgreSQL on localhost
with offline-prepared synthetic bases (EUR 102 minimum / EUR 109 alternative):

| Case | Observed result |
| --- | --- |
| Minimum approval | Explicit selection, actor and demo acknowledgement; saved UTC time and audit |
| Alternative approval | Mandatory reason; exact selected allocation and content hash shown; reload preserves time |
| No-award with plans | Saved outcome/reason with no approved content |
| Infeasible base on mobile | No-award saved; 390x844 viewport, no horizontal overflow |
| Stress child | Analytical restriction; zero actionable finalization controls |
| Lost successful response | Test-only wrapper returns 503 after the decision commits; UI stays unconfirmed and preserves recovery data |
| Backend stopped during retry | Same recovery JSON retained, no saved-success heading; explicit retry only |
| Backend restored, model unavailable | Same key recovers the original decision/time and content hash, then clears retry controls |

The recovery case `235454f1-3ef2-4667-b4e2-3804cc55d2c4` retained recorded time
`2026-10-09T15:10:17.536417Z` and content hash
`66bde23fca1b6d5bf85e85a8673600d53dad3470b911ce8b1b2a93f505954461`.
The alternative case `e146721f-b3f9-45b1-a4b1-decaf4c83d1a` retained time
`2026-10-09T15:07:09.333922Z` and content hash
`67e90c1bd70a6110acec79adda7378257fc8b9c4be881758654af3c30b2aa530`.
Ignored local evidence resides under `.artifacts/t17/`: `browser-evidence.json`,
`alternative-audit.jpg`, `uncertain-decision.jpg` and the test-only acceptance
wrapper/preparation files. These fixtures are disposable and are not production code.
Frontend export is a separate compilation gate, not automated browser E2E.

## Runtime, limitations and next capability

Only the existing Podman machine was used. All existing Odoo/application/demo
containers remained stopped and untouched. A separate Compose project,
`procurement-decision-support-t17-acceptance`, ran PostgreSQL on VM port 55434;
Windows forwarding failed, so a localhost-only SSH tunnel used host 55435.
Only this disposable database was migrated/reset. No user application migration,
Odoo UI/write, direct Odoo database access, Drive edit or model promotion occurred.
Acceptance servers, the separate database and the created tunnel are cleaned up
after verification; local evidence files remain for inspection.

Before running this branch against your own helper database, deliberately export
its `DECISION_DATABASE_URL`, apply `alembic upgrade head` and check revision
`20261009_01`. Do not run resetting tests there. Downgrade removes final decisions
and approved content; preserve a backup before any deliberate rollback.

Historical/synthetic evidence remains a controlled demonstration, with simulation
dates separate from current decision time. It does not prove current operational
validity, observed supplier prediction or production buyer authentication.
Browser acceptance is manual and local; hosted checks await publication.

Next: review this slice and its buyer workflow, then #21 renders/downloads the
immutable approved content without reacquiring facts or mutating approval. The
PDF spike, renderer, endpoint and error/retry UI belong to that next ticket.

Thesis note: missing human outcome -> immutable separate decision/content ->
explicit approve/No-award with stored-only recovery -> HTTP/PostgreSQL/browser
evidence -> synthetic/local/authentication/PDF limits -> chapters 3/4/5/6/7,
with evaluation and conclusions in later increments.
