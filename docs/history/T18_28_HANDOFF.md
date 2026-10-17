# Real buyer-flow browser smoke and backend recovery — #28

Date: 2026-10-11. Branch: `feature/T18-implementation`.
Baseline: committed #27 at `6082741`. This increment is uncommitted; tested source
hashes and local artifacts are bound in [the small evidence record](T18_28_BROWSER_EVIDENCE.json).
Status: **IMPLEMENTED AND LOCALLY VERIFIED** for
[issue #28](https://github.com/SafarErik/odoo-procurement-decision-support/issues/28).
Overall T18, user publication, new-SHA CI and final acceptance remain separate.

## Problem → decision → implemented behavior

Compilation and backend tests cannot establish that a buyer can submit a form,
read allocations, approve a plan and receive the backend's actual PDF through
Reflex. Browser request interception also cannot prove an outage of the API
called by Reflex's server-side client.

Add one bounded Chromium test with optional `e2e` dependencies. It reuses the
existing synthetic preparation, production Reflex/FastAPI modules, persistence
Compose file and migrations. [The harness](../tests/e2e/conftest.py) creates a
unique ignored workspace/frontend copy and disposable helper database, starts
owned services, waits with bounded readiness and tears down owned process trees
and that unique database project on success or ordinary failure. Windows uses
the documented localhost SSH workaround through the existing Podman machine.
Generated credentials live only in memory/process environment; Odoo keys and
URLs are cleared in those processes. Owner `.env`, frontend cache, demo/model
artifacts, application cases, Odoo services/data and named volumes are preserved.

[The buyer test](../tests/e2e/test_planning_smoke.py) uses real browser controls and
asserts displayed cost and per-supplier quantities against actual saved results.
It selects Alternative 1 explicitly, records actor/reason/acknowledgement and
checks the immutable original snapshot and saved selected plan. It restarts owned
FastAPI with the model directory empty, reloads the browser, reopens by case ID,
renders the PDF canvas/text and downloads bytes equal to the backend artifact and
its SHA-256. No HTTP browser mock or Odoo acquisition is used.

It then stops the owned FastAPI process for two error paths: stored GET must show
an error and clear false approval success; an interrupted create must retain its
payload/key and disable changed submission. Restoring the service requires an
explicit buyer action. The recovered create's identical payload/key returns HTTP
200 with `idempotent_replay=true`, referencing the case shown by the browser.

No production source, API contract, business rule, database schema, UI behavior
or CI workflow changed. The source addition is test setup plus one browser test,
not a new application subsystem. See [the runbook](T18_28_BROWSER_RUNBOOK.md) for
installation, startup, expected outcome, artifact location and cleanup.

## Actual local evidence

The final complete real-stack Chromium test **passed in 82.10 s**, including teardown.
This duration includes offline preparation, database migration, dependency setup,
compilation and browser actions; it is not a latency target or percentile.
Runtime: Windows, Python 3.11.16, Reflex 0.9.12, pytest-playwright 0.10.0,
Playwright 1.63.0/matching Chromium, existing Node 24.20.0, PuLP 3.3.0 and
scikit-learn 1.8.0; PostgreSQL image `16.15-bookworm` on the existing Podman machine.
Synthetic demand 10 produced the expected minimum cost EUR 102 and a distinct
alternative. Approval used caller audit reference `t18-browser-buyer`; it is not
an authenticated buyer identity.

| Acceptance area | Actual result |
| --- | --- |
| Optional Chromium tooling / fast collection | PASS: plugin-disabled collection selected 591 fast tests; explicitly selecting E2E without the plugin failed before services with installation instructions |
| Missing browser prerequisite | PASS: an empty process-only browser-cache path caused a clear missing-executable/install error before database/services started; not a skipped acceptance |
| Owned real stack and isolated persistence | PASS: fresh frontend/model/input and unique disposable project; migration/readiness and owned teardown executed |
| Create → compare → approve → stored reopen → PDF | PASS: displayed costs/quantities, selected alternative/actor, unchanged snapshot, model-unconfigured reopening, rendered canvas/text and byte/hash-identical download |
| Actual backend-unavailable error/recovery | PASS: owned API stopped for GET and POST, visible failure, no false GET approval, pending payload/key preserved and explicit idempotent recovery |
| Failure artifacts and bounded local scope | PASS: screenshots, traces and service logs retained locally; trace scanned for generated secrets, logs redacted; hosted/visual/novice claims excluded |

Final successful raw evidence is in `.artifacts/t18-browser-9c9777032b9d/`; pytest log/XML
are in `.artifacts/t18-28-pytest-6506c05d/`. The small repository JSON records
outcomes, IDs, source hashes and local artifact hashes, without copying browser
traces or repeated snapshots into the Git diff. PDF and pending-save screenshots
are retained alongside `trace.zip`. The owner's existing Odoo/listener remained
running; no `t18-browser-*` container or owned API/frontend listener remained.

Three initial development runs failed in **test assertions**, not application
behavior: the decision envelope was initially read at the wrong level, the intent
uses `approve` rather than the displayed `Approved`, and the actual error text is
`unconfirmed` rather than the test's `uncertain`. Their logs/screenshots/traces
remain bound separately. Each used a fresh disposable project with teardown; no
automatic workflow retry, hidden resubmission or production workaround was added.
The final run tests the actual existing contract and user-facing copy.

An earlier complete PASS (81.73 s) is retained separately. Final cleanup review
changed bounded Compose/migration commands to reuse the owned process-tree
launcher, so a timeout stops descendants as well as the parent. A focused probe
shortened only its command wait and verified real Windows parent/child termination
and absent child listener; the final full E2E run then passed on the changed
harness. This is a test-lifecycle fix, not a procurement behavior change.

Required fast gates passed: **591 tests, 60 deselected**, actual CBC/ML and the
independent T13 oracle; Ruff 0.17.0 format (211 files)/lint, compileall, pip check,
both credential-suppressed Compose configurations and whitespace. One existing
Starlette TestClient deprecation warning remains. Results are bound in the JSON
and implementation log. The full fast gates preceded that E2E-only timeout
refinement; focused Ruff/compilation, timeout probe and full E2E passed afterwards.
Fast-test code/selection did not change, so those passing tests were not repeated.
The production defaults are unchanged; optional browser imports happen only
inside selected E2E execution. Required Quality remains unchanged. The runtime
warning that Reflex has a newer release did not trigger a dependency upgrade.

## Limits, thesis relevance and next capability

This is one deterministic synthetic desktop Chromium flow. It does not establish
Ubuntu/hosted browser execution, Firefox/WebKit support, visual/accessibility
conformance, mobile/keyboard usability or unfamiliar-buyer validation. Novice
usability remains **NOT ASSESSED**. No-award and stress scenarios retain their
existing backend/manual evidence; this small browser test does not cover them.
The create outage occurs before dispatch; a response lost after commit is not
new browser evidence. Existing uncertain-response/idempotency tests remain
separate. Odoo quotations and history security retain #27's separate live proof;
this test does not use Odoo or promote an observed model.

Ordinary assertion/setup failure runs fixture teardown. Force-killing pytest can
prevent teardown; inspect the printed unique project/process logs before manual
cleanup. First frontend setup needs registry access; generated dependencies stay
in the ignored run directory until manually removed. Traces contain controlled
synthetic inputs/IDs/actor text and should stay local. These are PoC trust/runtime
limits, not authenticated business approval or production SLA claims.

Traceability: FR-V2-07/09–12, AC-V2-09–13, NFR-V2-02/04–08, RQ-V2-06/07.
Chapter 7 gains reproducible functional browser/recovery evidence; chapters 4/6
can describe the API-only interaction and saved document boundary. This does not
replace task-based usability evaluation or satisfy full thesis acceptance.

Review/publication remain user-controlled; no commit, push, PR, merge, issue
mutation or Drive edit. Next is **#29's buyer-task/keyboard/mobile walkthrough
and evidenced blocker fixes**, then #30's consolidated conclusions. Substantial
modern UX/UI work and reassessment still follow before final acceptance.
