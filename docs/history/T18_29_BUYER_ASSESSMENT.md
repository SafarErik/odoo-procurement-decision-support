# Buyer-task assessment and bounded feedback fixes — #29

Date: 2026-10-11. Branch: `feature/T18-implementation`; baseline `b3cf8f3`
(committed #28). [Issue #29](https://github.com/SafarErik/odoo-procurement-decision-support/issues/29)
implements the walkthrough slice of [specification #25](T18_EVALUATION_SPEC.md).
Status: **AGENT ASSESSMENT COMPLETED; BOUNDED FIXES LOCALLY VERIFIED**.
Owner walkthrough and actual browser text zoom remain pending. Unfamiliar-buyer
usability is **NOT ASSESSED**; external 3–5-person sessions remain **PENDING**.
This is not formal WCAG conformance, final T18 acceptance or a modern-UI acceptance.

## Problem → decision → implemented behavior

A functional browser smoke establishes a controlled procurement-to-PDF path,
but cannot show whether an unfamiliar buyer can understand and safely complete
the tasks. Assess the running application through the built-in browser using
real Reflex, FastAPI and disposable PostgreSQL, then fix only evidenced blockers.
Keep the substantial UX/UI increment separate and derive its priorities from
observed interaction friction and explicit, still-unvalidated hypotheses.

The walkthrough found dynamic feedback without programmatic roles: the PDF
failure was visible but absent from the alert tree; successful saves and PDF
readiness likewise lacked status roles. The shared saved-decision component now
exposes PDF failures as `alert` and readiness as `status`; the page's successful
save notice uses `status`. The shared component serves Plans and Audit. No API,
state/recovery, approval, document, database, dependency or CI contract changed.

The existing [Chromium smoke](../tests/e2e/test_planning_smoke.py) now checks the
successful-save role and adds a genuine owned-API outage before PDF generation:
the alert must appear, approval must remain visible and no download may appear.
An explicit retry after restoring the stored-only API must render/download the
actual approved document. This extends the existing test rather than adding
another browser harness or broad snapshot tests.

These semantics follow the [W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
DOM roles were verified; screen-reader speech was not tested. Existing backend
and scenario errors already expose alerts. No table rewrite was justified:
Chromium's audit overflow containers were reachable with Tab and horizontally
scrollable with arrow keys during the 320-pixel check.

## Session, actor and evidence boundary

The actor was one **source/runbook-informed agent**, with semantic browser
controls and direct keyboard input. No procurement owner or unfamiliar participant
completed these sessions. Source knowledge, known fixtures and saved IDs provided
assistance; successful agent comprehension cannot estimate novice task success,
time, satisfaction or error rates. No human assistance was supplied during the run.

Runtime: Windows, Python 3.11.16, Reflex 0.9.12, Playwright 1.63.0,
pytest-playwright 0.10.0, PuLP 3.3.0, scikit-learn 1.8.0, existing Node 24.20.0.
The walkthrough reused [#28's owned stack](T18_28_BROWSER_RUNBOOK.md), with a unique
frontend copy, offline matched fixture/model, fresh helper database and loopback
ports. Odoo URLs/keys were cleared in those processes; no Odoo request, write,
UI operation or observed-model promotion occurred. Separate live evidence remains
in [#27](T18_27_HANDOFF.md).

Raw screenshots, DOM observations, controlled case records, PDFs and task clocks
are local in `.artifacts/t18-browser-96f7af07bc03/`. The [small evidence record](T18_29_BUYER_EVIDENCE.json)
binds selected artifacts and exact changed source hashes. Repeated case payloads,
generated frontend files and screenshots stay outside Git. The manual driver is
an ignored one-off orchestration aid, not a supported application feature.

Task times below are monotonic **agent wall-clock seconds**, including reasoning,
tool calls, observations, fault setup and downloads. They are neither HTTP
measurements nor representative human task times. Creation/compare began in the
browser's default 534×764 viewport before the deliberate desktop 1280×900 setting.
Later responsive checks used 390×844 and 320×568. These are viewport checks,
not physical mobile/touch-device acceptance.

| Task / actor | Completion and evidence | Time (s) | Critical outcome errors / assistance |
| --- | --- | ---: | --- |
| Create and explain / informed agent | Minimum EUR 102: S226 6 + S184 4. Alternative EUR 109: S161 8 + S184 2. Exact alternative exposure `9661/50000`, premium `7/102`; synthetic proxy, not failure probability | 76.859 | 0 observed; source/runbook assistance; initial viewport changed |
| All disruptions and infeasibility / informed agent | All five types, original-base context, demand-change caveat, infeasible demand 1000 and return to unchanged base | 142.453 | 0 observed; explicit waits for updated scenario assumptions |
| Alternative approval and PDF recovery / informed agent | Empty required reason rejected; explicit Alternative 1 approval; real PDF outage preserved approval; explicit stored-only retry and download | 283.485 | 0 observed decision errors; known saved case and deliberate service control |
| Keyboard No-award / informed agent | Keyboard-only tab navigation, demo loading, creation, reason validation, separate No-award and stored reopen; no PDF control | 76.500 | 0 observed decision errors; focus fell to body after completed saves |
| Narrow recovery and document tasks / informed agent | Real GET/POST faults; same pending key/payload; 320-pixel audit scrolling, infeasible/base return; mobile approval/reopen/download; keyboard PDF scrolling at 200% viewer zoom | 207.062 | 0 observed decision errors; source-informed controls; browser text zoom unverified |
| Feedback fix recheck / informed agent | PDF alert at 320 pixels, preserved approval, explicit retry/readiness status, rendered document; saved-scenario status at desktop | 85.281 | 0 observed decision errors; changed source copied into owned frontend |

The alternative/PDF task clock ended after download; the separate rendered
canvas/text observation followed immediately and remains timestamped in its
artifact. The initially captured `mobile-recovered-base` still showed the previous
case while the asynchronous result settled; it is not completion proof. The later
expanded Audit record proves recovered case `84bf77cc-3908-4730-8315-8b369b595474`.
Tool targeting mistakes (a wait for nonexistent “Scenario saved.” copy and selecting
the PDF option by label as its value) were corrected against the visible DOM;
these are agent automation mistakes, not buyer error-rate observations.

## Task outcomes and comprehension

The original base `e55cb89e-272a-44ad-8607-b792817ea855` retained snapshot SHA-256
`1fe072c7b766b5a8333811f1b97000d004e20cd181281bc9cf637cbb4c2eb767` after
all scenario checks and approval. Alternative 1's EUR 7 premium accompanies a
displayed exposure reduction of 79.3 points; exact saved values remain in Audit.
Supplier classes and schedule-adherence explanations retain their synthetic
history and uncalibrated-model caveats. The actor reference is audit text, not
authenticated buyer identity or authority for an operational purchase.

| Scenario from original demand 10 / EUR 102 | Actual result | Interpretation |
| --- | --- | --- |
| S226 outage | EUR 106; +4 | Supplier unavailable; saved scores reused |
| S226 capacity 3 | EUR 103.5; +1.5 | Declared capacity assumption changed |
| Demand 12 | EUR 123; +21 | Different total demand, not like-for-like savings |
| S226 price 12 | EUR 106; +4 | Simulated price, not a fresh Odoo quotation |
| Combined demand 12, S226 capacity 3 and price 12 | EUR 128; +26 | Supported bounded combination, original-base lineage |
| Demand 1000 | No feasible plan | No invented allocation/cost; scenario cannot receive final approval; original remains saved |

Approval explicitly selected Alternative 1 and required a reason. The separate
keyboard-created base `3a312ec0-0e61-409e-94d2-6b383b5a61a8` recorded No-award,
required a reason, reopened with that outcome and offered no approved PDF.
The recovered mobile base separately approved Minimum cost and reopened it.
PDF download/rendering retained the saved date, selected allocation, actor,
reason, exact cost/exposure and synthetic limitation; viewing did not create
an Odoo Purchase Order.

Genuine owned-service faults produced visible GET, uncertain-save and PDF errors.
GET cleared a falsely usable result. The uncertain create disabled changed
submission and retained key `5f49c60c-8dfd-4aa8-abc4-1e54d586d56d` plus its exact
payload before explicit retry. This outage was **before dispatch**, not a newly
tested response lost after commit. Existing idempotency/fault tests and the
automated replay assertion remain separate proof. PDF failure preserved the
recorded approval and offered explicit retry of the same saved document.

Labels, native required-field validation, tab-arrow navigation, visible focus,
exact values and responsive overflow were inspected. Keyboard-only evidence
covers creation/No-award/reopen and focused audit/PDF scrolling; the all-five
scenario walkthrough used semantic pointer controls. PDF **viewer** 200% zoom
worked at 320 pixels, with keyboard scroll offsets 160 px horizontally / 120 px
vertically. Actual **browser text** zoom was attempted with Ctrl+plus/Ctrl+equal;
viewport width and device-pixel ratio did not change in the in-app browser.
That gate remains **NOT VERIFIED**, not inferred from responsive/PDF checks.
Touch, other engines, screen-reader output and formal accessibility remain untested.

## Observed findings and prioritized UX/UI follow-up

Priority reflects buyer impact and this controlled reproduction, not participant
frequency. The earlier [planning candidates](T18_EVALUATION_PLAN.md) remain
source-informed hypotheses unless this table records fresh running evidence.

| ID / priority / status | Reproduction and evidence | Buyer impact → intended improvement → reassessment |
| --- | --- | --- |
| UX29-01 / P1 / FIXED | Stop owned API on an approved base, View approved PDF; `desktop-pdf-failure-before` had no alert role. `narrow320-pdf-failure-fixed` exposes alert, preserves approval | Nonvisual users can miss failure → shared alert/status roles → affected browser recheck and genuine-fault regression passed; screen-reader speech still pending |
| UX29-02 / P2 / FIXED | Create a scenario or prepare a PDF; former notice/readiness lacked status roles. `desktop-scenario-status-fixed` and PDF recovery expose status | Save/document feedback lacks nonvisual semantics → status roles → DOM and browser assertions; human comprehension not established |
| UX29-03 / P1 / FOLLOW-UP | Open blank cockpit without a UUID: “First test? Start with a saved case”; known Demo/runbook needed. Start controls in desktop/mobile artifacts | Returning/first-time buyers need a recognizable entry → design recent-case/find/open flow and meaningful case labels; keep API capability changes separately scoped → novice unassisted find/reopen task |
| UX29-04 / P1 / FOLLOW-UP | At 390/320 pixels, setup, testing guide and evidence paragraphs precede result; approved/mobile pages are long. `mobile-approved-pdf`, `narrow320-exact-values` | Important action/outcome is distant → redesign buyer hierarchy, compact evidence disclosure and responsive workspace → task completion, scrolling and comprehension across desktop/mobile |
| UX29-05 / P1 / FOLLOW-UP | Final decision occurs below cards/chart; selection dropdown contains only plan labels. Alternative reason validation worked in `desktop-approved-before` | Irreversible choice deserves clear context; mistaken choice is a hypothesis → selected allocation/cost/exposure summary and deliberate confirmation, distinct No-award → unfamiliar buyer explains choice/irreversibility and avoids unintended approval |
| UX29-06 / P2 / FOLLOW-UP | Keyboard save removes focused create/finalize control; active element becomes body. Visible focus works on surviving controls | Position/context lost, extra navigation needed → purposeful result heading/focus or persistent action context without stealing focus → repeat keyboard save/scenario/approval/reopen with announced outcome and logical next action |
| UX29-07 / P2 / FOLLOW-UP | In infeasible comparison, original EUR 102 shown as “Not comparable”; `desktop-infeasible`, `narrow320-infeasible` | Preserved baseline becomes harder to compare → retain original facts, distinguish undefined scenario metrics from invalid deltas → buyer explains infeasibility/base facts without treating absent quantity as zero |
| UX29-08 / P2 / FOLLOW-UP | Pending-save recovery is expandable technical JSON/key; correct explanation and identical retry worked. `mobile-pending-save` | Correct recovery is safe but technical → buyer-oriented saved/pending/retry explanation and persistent recovery aid; preserve exact payload/key → outage task without changing/replacing intent |
| UX29-09 / P2 / FOLLOW-UP | Five-page approved PDF has exact provenance/model/solver audit; fit-width and keyboard 200% scrolling worked | Audit volume may obscure practical document use → clearer page/navigation and concise approved summary while retaining required exact audit → find chosen supplier/quantity/date, inspect provenance and download at narrow/zoomed sizes |
| UX29-10 / P2 / FOLLOW-UP | Persistent “What should I test?” and implementation/evidence wording in cockpit | Procurement buyers see developer/demo guidance → modern visual system and consistent buyer copy, keep required synthetic/authority limits visible → buyer tasks plus restrained evidence comprehension, not merely screenshot approval |

The subsequent substantial UX/UI increment should start with a buyer workflow
and coherent responsive visual system, then implement entry/retrieval, comparison,
scenario context, explicit final choice, recovery and PDF navigation as bounded
slices. Validate these with the owner first, then the planned unfamiliar
participants. Typography, spacing, hierarchy and interaction states should be
designed together; cosmetic restyling alone does not resolve the observed friction.
This table is a prioritized backlog proposal, not new approved requirements or
permission to broaden Odoo discovery/identity/model scope.

## Owner and unfamiliar-buyer sessions — pending run sheet

Use the [existing local terminal runbook](LOCAL_DEVELOPMENT_AND_SSH.md) and
[T17 full-flow demo](T17_FULL_FLOW_DEMO.md) to start only the required own backend,
Reflex and helper persistence; prepare the controlled fixture offline. Do not use
database-reset tests against owner cases/Odoo. The [browser smoke runbook](T18_28_BROWSER_RUNBOOK.md)
owns optional-tool installation, disposable test setup and automated cleanup.
The one-off agent driver is not a prerequisite for owner evaluation.

1. Record date, source commit, actor category (owner / unfamiliar participant),
   browser/device/viewport/zoom, fixture and known prior app knowledge. For every
   task, measure human elapsed time separately and record completion, assistance,
   mistakes, comprehension/comments and screenshot/case evidence. Leave unfinished
   tasks and unknown fields explicit. Never enter secrets in recordings.
2. Create a controlled plan; explain supplier quantities, EUR 7 premium and
   synthetic exposure. Inspect exact values without claiming failure probability.
3. Run all five disruption types and demand 1000; explain changed-demand totals,
   infeasibility, analytical-child status and return to the original base.
4. On separate fresh bases, approve an alternative with reason and record
   No-award with reason. Explain one-time finalization, actor limitations and
   No-award's lack of an approved PDF. Reopen each by retained case ID.
5. View/download the approved PDF and find selected allocation/date/audit. On
   owned test services only, stop FastAPI for GET/create/PDF and explicitly recover
   after restoring it; require preserved approval and exact retry intent/key.
   The automated smoke performs these faults safely if manual service control
   would interfere with another session.
6. Repeat essential actions with keyboard only and at narrow width. In a regular
   browser explicitly set **200% browser zoom**, inspect reflow/focus/errors and
   exact tables, then restore 100%. Distinguish it from PDF zoom. Record screenshots
   and any blocked controls; use [W3C keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html)
   and [reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)
   as assessment references, without declaring formal conformance.
7. Plan 3–5 unfamiliar people who understand procurement. Use neutral task prompts
   and record each intervention; do not substitute the informed owner/agent for
   these participants. Reassess the redesigned UX before claiming novice usability.

Cleanup only the services/project started for that session, retain needed case IDs
and restore browser zoom. Leave owner Odoo/data and the existing Podman machine
alone. Required pending gates do not become PASS through this run sheet.

## Verification, limitations and thesis relevance

Final extended real-stack Chromium smoke: **1 passed in 87.51 s**, including
ordinary teardown, real PDF/GET/create faults, explicit recovery and downloaded
PDF bytes equal to the backend artifact/hash. This is test duration, not latency.
Required fast gates: **591 passed, 60 deselected in 104.56 s**, actual CBC/ML,
Ruff 0.17.0 format (212 files)/lint, compileall, pip check, both existing Compose
configurations with secret output suppressed and whitespace checks. The existing
Starlette TestClient deprecation warning remains; no dependency upgrade was made.

The first fast attempt had 408 passes and 183 **setup errors**, all caused by
denied access to the default Windows pytest temp directory. Its log is retained.
The complete rerun with a fresh workspace-local `--basetemp` passed; this was a
test-runtime correction, not a production fix. Reproduction uses the standard
[required checks](../AGENTS.md#commands); if that temp problem occurs, use a fresh
unique `.artifacts` temp/cache directory as in the browser runbook, never an
existing owner data directory. The [evidence JSON](T18_29_BUYER_EVIDENCE.json)
records exact result/artifact hashes and distinguishes both attempts.

Both owned `t18-browser-*` projects/process trees were cleaned up, with no owned
HTTP listener remaining. Owner Odoo/database services, the existing 8069 listener
and running Podman machine were preserved. Browser viewport overrides were reset
and the agent-created tab closed. Manual readback assertions confirm unchanged
base snapshot, distinct No-award without approved content and both five-page PDFs'
matching case/snapshot/approved-content identities, actor and chosen exact cost.

No commit, push, PR, merge, issue mutation or Drive synchronization was performed.
Review/publication/new-SHA CI remain user-controlled. Owner/novice sessions,
actual browser text zoom, screen-reader output, hosted/Ubuntu browser and physical
mobile checks are pending/unverified. Local semantics and task completion do not
validate a modern first-time-buyer experience or establish operational ML accuracy.

Traceability: official task's Python web UI, stress analysis, stored decision and
approved document; FR-V2-07–12, AC-V2-08–13, NFR-V2-04–08, RQ-V2-04–07. This
adds bounded evidence to [the inventory](T18_EVIDENCE_MATRIX.md), without changing
canonical meanings or asserting full acceptance. Chapter 7 can report tasks,
fault/recovery, findings and these limitations; chapters 4/6 explain the HTTP-only
feedback/document behavior; further work derives from the observed UX backlog.

Next is **#30's consolidated controlled-scope AC/NFR/RQ assessment**, preserving
pending human/accessibility gates, followed by substantial buyer-focused UX/UI
development and reassessment before final acceptance and thesis closure.
