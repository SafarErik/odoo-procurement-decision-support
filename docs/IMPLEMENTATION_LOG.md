# Implementation log

## T16 procurement cockpit usability and decomposition (2026-10-08)

**Problem:** functional success left buyers interpreting raw IDs, long tree/solver
records, sparse chart points and a generic scenario rejection. The single Reflex
module also mixed the RFQ ledger, HTTP state and all planning components.

**Decision:** revise the buyer workflow within the existing controlled scope.
Use separate Plans / What-if / Suppliers / Audit views, full-width Odoo input
review, direct cost/exposure wording, original-value scenario validation and an
embedded reproducible test guide. Split source by responsibility rather than
introducing a frontend framework, chart dependency or backend abstraction.

**Implemented behavior:** `frontend/app.py` composes pages; `rfq_page.py` owns the
ledger; `planning/` owns state, inputs, scenarios, saved results, audit and layout.
The unified composer includes outage and preserves original-base targeting,
immutable children and exact uncertain-request recovery. Supplier conditions are
readable while exact branch records remain available. Captured Odoo quotations
are labelled as captured; synthetic history/model provenance remains explicit.

**Evidence:** final Python 3.11 fast suite 521 passed / 45 deselected, one existing
Starlette/httpx deprecation warning, final run 61.01s; actual ML/CBC execute. Ruff format/lint,
compileall, pip check and Compose config pass. A failed initial fixture-temp probe
lacked its parent directory; focused checks pass after creating the documented
isolated directory. The Compose provider initially lacked PATH and passes using
the existing local environment. Browser critique caught and corrected stacked
desktop plan cards, a premature uncertain-save notice, comparison placement and
Reflex numeric event types; final draft inputs retain exact text without new warnings.
Actual read-only Odoo creation saves USD 1,850/2,200; all five scenarios and
infeasibility pass through the original-base PostgreSQL flow with acquisition and
inference forbidden. Independent HTTP retrieval verifies eight cases and unchanged
base evidence across nine cases; separate synthetic browser creation saves EUR
102/109, mobile layouts do not overflow and the RFQ ledger still works.
Production frontend export passes four stages; shared token absent from 39
generated client/export files. The stopped-agent-backend browser check clears the
previous result and shows the safe service error. Only agent previews were closed;
the user's services, containers, tunnel and saved records remain available.
See [T16 handoff](T16_HANDOFF.md) for exact scope, IDs and remaining gates.

**Limitations / thesis relevance:** this strengthens the implemented web interface,
explanation and reproducible decision-process evaluation (FR-V2-07/08/09/10), not
observed ML validity or full V2 acceptance. Snapshot business names are absent;
neutral readable labels retain exact identities for audit. Odoo mock receipts
would still be synthetic evidence. User acceptance, publication/new-diff CI and
Hungarian Drive synchronization remain pending; T17 approval/PDF follows planning.
No Odoo writes, observed-model promotion, commit, push or merge occurred.

## Repeated local planning unavailability: machine/container/tunnel recovery (2026-10-08)

**Problem -> cause:** the user's stored-case view reports planning data unavailable.
FastAPI/Reflex still listen on 8000/8001/3000, but the existing Podman machine is
stopped, all three development containers are exited, and Windows 8069/55433 have
no listeners. Health returns 200 while RFQs return 503 and planning GET times out;
health alone does not establish dependency readiness. Machine startup again reports
the recurring `win-sshproxy.exe` failure.

**Decision -> recovery:** start `podman-machine-default` and the existing Odoo DB,
planning DB and Odoo containers without recreating them. Verify planning
`pg_isready` and Odoo HTTP 200 inside the VM. Restore one localhost-only SSH tunnel
from current machine SSH configuration for 8069 -> VM 8069 and 55433 -> VM 55432.
Leave it running for the user's application session (observed process 26708;
the PID is session-specific, not a reusable command).

**Evidence:** both Windows ports become reachable; actual FastAPI health, RFQs and
GET of `e183f917-fc33-4e28-a7a8-0aea22679176` return 200. Stored minimum cost is
still USD 1,850. No credentials, schema, saved cases, volumes or application code
were changed. Add the ordered startup/readiness/forwarding/API-verification and
cleanup procedure to [local development](LOCAL_DEVELOPMENT_AND_SSH.md#planning-data-unavailable-recover-the-local-stack)
and link it from README. Earlier recovery/acceptance evidence below is historical.
The actual user Reflex service on 3000 reloads the selected case as **Plans ready**,
USD 1,850/2,200, with the previous error absent. Screenshot:
`.artifacts/t16-runtime-recovery/repeated-restored-planning.jpg`. The documented
PowerShell authenticated GET succeeds, all six new command blocks parse, and
patch whitespace checks pass.

**Limit -> chapter relevance:** this restores a development session, not Podman's
native Windows proxy. The machine/containers/tunnel must remain running; a restart
requires repeating the checklist. No new full suite or hosted CI was run for this
runtime/documentation-only change. The record supports reproducibility and local
integration troubleshooting; T16 scope and synthetic-model limitations are unchanged.

## Controlled T16 cockpit completion and local acceptance (2026-10-08)

**Problem:** creation, five scenarios and retrieval were available, but the cockpit
lacked the required cost/exposure chart, an explicit single-plan outcome and a
consolidated requirements-to-evidence record. Saved cases also needed a clear view
of the actual terms/policy used, independently of the original-base scenario controls.

**Decision -> behavior:** reuse native Reflex/HTML/CSS and the existing saved API
response. Add a numbered cost-versus-exposure plot/key with exact decimal costs,
approximate positions and fixed 0–100 exposure scale. Preserve exact fractions in
solver details; do not recalibrate/recompute model scores or plans. Distinguish no
distinct alternative, no requested alternatives and incomplete alternative search.
Infeasibility produces no chart/fabricated zero values. The audit shows saved price,
capacity, MOQ, promised date, availability, applicability and policy; selectors
retain original base terms. Validate the saved supplier join and exposure bounds.
No endpoint, dependency, migration, model/solver algorithm or Odoo write was added.

**Evidence:** required Python 3.11 fast suite **516 passed, 45 integration/E2E
deselected**, one upstream Starlette/httpx warning, 74.58s; actual offline training,
saved reload/inference and bundled CBC execute. Ruff format/lint, compileall,
pip check, quiet Odoo Compose config and patch whitespace pass. The first focused
run caught four stale test assertions equating all displayed child terms with base
terms; assertions now separately check unchanged controls and actual saved child
inputs. Focused follow-ups pass; the final full suite covers the corrected tests.
Production frontend-only export passes four stages. Shared token absent from 41
generated client/export files, with public state/recovery boundary checks passing.

Fresh real browser/API/PostgreSQL acceptance creates the Odoo quotation base
`233b8b59-10cf-43ee-aaa0-61eef4a00a30`: USD 1,850/2,200, exposure 75.0/48.3 out of
100. Odoo is read-only; business terms and synthetic ML history retain independent
provenance. Restarting the agent API with acquisition/inference forbidden still
saves all five children: outage 2,200; capacity 100 -> 2,200; demand 220 -> 2,040;
price 11.00 -> 2,150; combined demand 220 + capacity 100 -> 2,400 USD. Demand 500
is stored infeasible without fabricated comparisons/chart. One-change combined
input is rejected before POST. Independent GET verifies original parents, identical
saved facts/assessments and unchanged base hash. Existing user API on 8000 reopens
the fresh base with HTTP 200 and matching hash. Pure synthetic browser creation
with its matching model gives EUR 102/109, base `a8723891-cf95-45d2-b046-0246bdb6ee70`.

Browser evidence covers chart/key, actual tree path, saved input/provenance audit,
single-plan message, loading/disabled controls, stored reopening and unavailable
API clearing prior results. At 390px there is no horizontal document overflow;
viewport restored. No visible framework connection notice or final console
warning/error. Existing RFQ ledger still reads 13 RFQs / 8 vendors. UUIDs, snapshots
and screenshots are ignored in `.artifacts/t16-closure/`; the
[T16 handoff](T16_HANDOFF.md) owns the acceptance matrix and full case list.

**Publication/runtime:** open PR #18 at `0a2cafbacef4adf45f97902df56d7aace21d8786`
has independently verified successful Quality `37806351589` and Container/API
`37806351546`. They cover the earlier published scenario workflow, not this local
closure diff. No staging, commit, push, merge or Drive edit occurred. Validation
uses Python 3.11.16 / Reflex 0.9.12; browser/export reuse Python 3.14.7 / Reflex
0.9.11.post1. Agent previews on 3111/8211/8111 are stopped; user services and
forwarding tunnel 2876 remain running. Existing configuration, generated user
cache, Odoo data and volumes are preserved. Eight new own planning snapshots were
saved; no reset suite was run against manual cases.

**Limit -> next -> chapter relevance:** controlled T16 implementation and local
AC-V2-09 acceptance are complete, pending user validation/publication/new-HEAD CI.
FR-V2-09 approval/PDF and AC11/12/13 remain open. Arbitrary discovery, broader
combinations and observed dataset/model promotion remain separate unimplemented
capabilities; synthetic exposure is not a calibrated failure probability. No
production browser run or formal accessibility audit is claimed. The full visual
revamp stays later. User validation -> explicit Hungarian Drive synchronization ->
T17 approval/no-award and approved-snapshot PDF planning. This record supports
frontend/integration architecture, explainability, verification and limitations
chapters; historical status/checks below remain unchanged.

## User-session localhost recovery (2026-10-08)

The user's FastAPI starts successfully, but RFQ GET returns 503 and stored planning
retrieval is unavailable. Both existing Podman services are healthy: Odoo responds
HTTP 200 inside the VM and planning PostgreSQL passes pg_isready. Windows has no
listeners on configured 8069/55433; the temporary verification tunnel had been
stopped. Restore one localhost-only SSH tunnel using the existing machine/key,
without changing settings, credentials, containers or data. The user's existing
API now returns HTTP 200 for health, RFQs and the stored hybrid base; actual Reflex
on 3000 loads USD 1,850/2,200 without a connection warning. Odoo RFQs and planning
GET use separate upstream dependencies; successful health alone proves neither.
The recovery tunnel is left running for the user's testing, with process cleanup
instructions provided in the handoff reply. This is a temporary Windows forwarding
workaround, not a repaired Podman proxy. No application code change or repeated
full suite was needed. Screenshot evidence is ignored under
`.artifacts/t16-runtime-recovery/restored-planning.jpg`.

## What-if scenario controls and stored base comparisons (2026-10-08)

**Problem -> decision -> behavior:** the buyer could run only an outage through
Reflex, while T15 already supported other disturbances. Reuse the existing scenario
API and recovery path. Add capacity reduction, demand increase, price increase
and a bounded combined form (at least two changes among demand and one supplier's
capacity/price). All scenarios target the original base, including from a child.
Original saved terms support strict-change validation. Simulated prices are
what-if assumptions; they never refresh/update Odoo quotations. Assessments and
historical facts stay stored. No backend contract, migration, algorithm, service,
dependency or Odoo write was introduced.

**Comparison:** render original/scenario feasibility, quantities, minimum cost,
exposure and per-supplier allocation changes from existing saved results/deltas.
Base cost/exposure are reconstructed from scenario values and recorded deltas;
display does not solve or score. Demand-total differences are explicitly not
like-for-like savings. Missing proven minima produce unavailable comparison cells,
not fabricated zero allocations. Solver failure is distinct from infeasibility.
Supplier joins, totals and scenario/result allocation agreement fail closed.
Exact fractions and audit notes remain available. Recovery retains exact body/key,
blocks changed intent and does not rescore/resolve sources on replay.

**Publication:** PR #18 is open at published prepared-Odoo commit
`ad8aeb2358470fba2fa386851bd140b70f72dbfb`; independently verified successful
Quality `37779183516` and Container/API `37779183536` cover that SHA. README and
handoff current status now reflect its publication; prior dated records retain
their original evidence/limitations. This scenario extension remains unstaged,
uncommitted and unpublished. No commit, push, merge or Drive edit occurred.

**Checks:** existing frontend regressions 47 passed; initial new focused suite
28 passed. Added allocation/result mismatch regression is covered by the final
full suite: 509 passed, 45 integration/E2E deselected, one upstream Starlette/httpx
warning, 55.58s. There are 29 new scenario tests; actual saved tree/CBC paths run.
Ruff format (155 files)/lint, compileall, pip check, diff whitespace and Odoo
Compose config pass. Production frontend-only export passes four build stages.
Shared service token is absent from 41 generated client/export files and public
state/recovery JSON. Missing services are not replaced with skipped runtime gates.

**Live evidence:** use existing healthy Podman/planning database, with temporary
localhost 55433 SSH forwarding. Preview FastAPI 8110 forbids Odoo acquisition and
inference; Reflex 3110/8210 creates real PostgreSQL children from hybrid base
`e183f917-fc33-4e28-a7a8-0aea22679176`. Capacity 100 -> USD 2,200; demand 220 ->
USD 2,040; price 11.00 -> USD 2,150; demand 220 + capacity 100 -> USD 2,400;
demand 500 -> saved infeasible. Independent GET confirms all parent links,
identical assessments/historical facts and unchanged original USD 1,850 base
snapshot/hash. UUIDs are in the T16 handoff; ignored `cases.json` and
`comparison.jpg` are under `.artifacts/t16-scenarios-check/`.

**Browser/runtime:** final combined-case reopening shows readable status and
cost/quantity/exposure/allocation comparison. A one-change combined form is
rejected before POST. Stopped API gives a safe service error and clears the old
comparison. At the 390px viewport override, page has no horizontal overflow;
override reset. Final successful rendering has no visible connection notice or
console warnings/errors. Validation uses Python 3.11.16/Reflex 0.9.12; browser/
export reuse Python 3.14.7/Reflex 0.9.11.post1. Agent preview ports/tab/tunnel were
stopped; existing Podman services, volumes and saved cases remain. No resetting
database test ran against manual cases. No default artifact, tracked lockfile or
ignored environment value changed.

**Limit -> next -> chapter relevance:** all five existing scenario types are
accessible through bounded controls, but arbitrary multi-supplier combinations,
quotation discovery, observed-model promotion and full T16/V2 acceptance remain
open. New hosted CI and the resetting suite were not run. No new credential or
manual Odoo operation is needed. User controls publication/merge, then assess the
controlled workflow against T16 acceptance before claiming closure; T17 approval/
PDF remains separate. Relevant to implementation, integration, usability,
provenance and testing chapters. Historical records below remain dated evidence.

## Prepared Odoo creation in the buyer workspace (2026-10-08)

**Problem -> decision -> behavior:** Reflex could create only synthetic-domain
cases although the Odoo planning API existed. Reuse the fixed offline-prepared
comparison and existing `/from-odoo` route. **Plan from Odoo** shows captured
quotation expectations and edits explicit demand/date/capacity/MOQ/promised-date
terms. FastAPI independently reads Odoo/currency, checks expectations, loads the
matching saved Decision Tree, runs unchanged CBC MILP and persists an immutable
case. New terms carry `t16-ui-odoo-terms-v1` attribution; Odoo prices/identities and
synthetic receipts remain distinct. Exact request/key recovery, outage and stored
GET are reused. Responses must match the hybrid input kind and prepared group.
No backend contract, migration, dependency, Odoo write or observed-model bypass
was introduced. See the current T16 handoff and Odoo workspace runbook.

**Published status:** authenticated GitHub reads verify PR #18 is open at
`de7ac92820e367e28b79dd0f7073f5b8c4191397`; Quality `37753212085` and Container/API
`37753212092` completed successfully. This extension remains local, unstaged,
uncommitted and unpublished; those checks do not cover it. No commit, push, merge
or Drive synchronization occurred. Historical records below remain unchanged.

**Checks:** 15 new focused tests pass. Python 3.11.16 required fast suite:
480 passed / 45 integration/E2E deselected / one upstream Starlette/httpx warning,
46.28s. Actual training/reload/inference and CBC execute. Ruff format (154 files),
lint, compileall, pip check, diff whitespace and production frontend-only export
(four build stages) pass. Odoo Compose config passes with the installed local
provider. The shared service token is absent from 41 generated client/export files
and public state/recovery JSON. The first Compose attempt lacked the
provider on PATH. A sandbox pytest run
stalled without output and was stopped; a fresh basetemp under the normal Windows
identity completed. Early assertion errors for formatted money, streamed ASGI
responses and canonical JSON storage were corrected without changing those contracts.

**Live evidence:** the existing stopped Podman machine and Odoo/planning containers
were started without resetting data. Windows forwarding failed despite healthy
containers; one localhost SSH tunnel supplied 8069 and 55433. Read-only group-2
acquisition prepared isolated matching Python 3.11 assets in
`.artifacts/t16-odoo-check/live/`, preserving default assets. Real Reflex -> FastAPI
-> Odoo -> saved model/CBC -> PostgreSQL: base `e183f917-fc33-4e28-a7a8-0aea22679176`,
USD 1,850/2,200, allocations 50/0/150 and 100/100/0; supplier 53 outage
`71958fa0-8583-4393-a787-39c1f7bee1f5`, USD 2,200 and +350 USD. Browser reopening
and independent GET verify lineage, assessment reuse and separate provenance.
Stopped-API retrieval clears old plans and shows the safe unavailable-service
message. The 390px viewport override gives one supplier column without horizontal
page overflow; reset afterward. No visible connection notice or console warnings/
errors during successful retrieval. Ignored evidence: `cases.json` and
`stored-odoo-plan.jpg` under `.artifacts/t16-odoo-check/`.

**Runtime/cleanup:** validation uses Python 3.11/Reflex 0.9.12; browser/export reuse
Python 3.14.7/Reflex 0.9.11.post1. Backend/ML remain Python 3.11. Agent preview
ports 3109/8209/8109, tab and temporary SSH tunnel were stopped; existing Podman
services and saved cases/volumes remain. Subsequent Windows manual review needs
the documented localhost tunnel. No tracked lockfile, default artifact or ignored
environment value changed; no resetting database test ran against manual cases.

**Limit -> next -> chapter relevance:** preview is captured, not live discovery;
IDs are shown without newly acquired supplier/product names. One model serves a
compatible domain at a time. Synthetic history/model exposure is not observed
supplier validation. Other scenario controls, arbitrary discovery and full T16/V2
acceptance remain open; approval/PDF belongs to T17. Hosted CI for this diff and
the resetting suite were not run. User reviews the Odoo walkthrough and controls
commit/publication/merge; the next small capability can expose another existing
stress scenario with stored comparison. Relevant to architecture, integration,
provenance, implementation, usability and testing chapters.

## Controlled Odoo quotations, synthetic model and immutable V2 completion (2026-10-07)

**Problem and decision:** the history credential was renewed, but the three selected
fixture suppliers have no visible confirmed company-1 orders in the bounded read;
known T7 receipts belong to another supplier/product. User delegated the fastest
sound path. Keep live Odoo quotation/context evidence and explicit business terms
separate from genuinely generated synthetic ML history. This closes the controlled
integration dependency without claiming an observed predictor or fabricating receipts.

**Implemented behavior:** a small V2 assembler validates exact group/offer/supplier/
line/context joins, common currency resolved through a bounded adapter read, and
explicit Q/business terms. Added `/from-odoo` creation with the existing strict
controlled schema. Independently read prices/context must match caller expectations;
they are not caller-certified upstream facts. A normalized caller intent and shared
locked transaction resolve exact retry before source acquisition, saved inference or
unchanged CBC. Existing scenario/GET paths, JSONB schema/immutability and V1 remain.
Snapshots retain field provenance, selection identity, acquisition cutoff and
`odoo_quotations_synthetic_history` kind. No infrastructure or migration added.

Offline generation accepts an explicit company/product/unit domain and still
produces synthetic data. The existing training pipeline creates a genuine new
artifact/model ID/checksum and saved dataset; source guards and mapping are unchanged.
The owner assigns simulated A/B/C profiles explicitly. Preparation and the shared
HTTP demo now support live quotations; printed currency comes from the snapshot.
CI path filters include the new tool. AGENTS/README, index, handoff, selected plan
and terminal instructions record the new controlled boundary, preserving history.

**Verification:** renewed history identity HTTP 200, uid 8; focused projection
security 1 passed / 19 deselected, 1.80 s. Hybrid/legacy API/demo checks 40 passed /
one warning, 16.77 s. Initial full fast suite 433 passed / 45 deselected, 42.23 s.
Review caught a missing stored comparison identity for its provenance path; added
that value and assertion. Final Python 3.11 fast suite **433 passed / 45 deselected /
one upstream warning, 39.46 s**. Actual PostgreSQL T15+V1 **22 passed / one warning,
25.90 s**, including hybrid round-trip and upstream-free replay. The isolated
verification helper initially lacked the checkout on `sys.path`, preventing only
its subsequent live demo; corrected the helper and ran migrations/live acceptance
without repeating the passed database suite.

Ruff format/lint, compileall, dependency consistency and whitespace checks passed.
Documentation verification resolved 72 local links/anchors and parsed all 12
PowerShell blocks in the demo guide.

Actual read-only Odoo group 2 + saved synthetic inference + CBC + PostgreSQL/API:
USD 1,850 minimum (A/B/C 50/0/150), USD 2,200 lower-exposure alternative (100/100/0),
C outage USD 2,200 (100/100/0). This uses explicit controlled Q=200, capacities
120/100/160, hard MOQ 50/100/150, 80% concentration and 20% epsilon, distinct from
quotation Q=100. Live acceptance used TestClient with real external services, not a
new Uvicorn/browser session. A fresh client context with Odoo/model access disabled
returned identical base/child GET and exact base/child replay (200); fresh base 503.
Fast checks also trap HTTP training/solver calls after invalid inputs and verify
context/price/tax/supplier mismatch, no source renaming, conflicts and sanitization.

The existing stopped test container was started without recreating it; a separate
temporary database protected user test cases. Windows forwarding still required a
hidden localhost tunnel. The temporary database, owned tunnel and ignored runtime
credential file were removed and the test container restored to stopped. Odoo is
unchanged and remains running. Ignored local run/restart evidence is under
`.artifacts/t15-odoo-demo/` and `.artifacts/t15-odoo-verify-00ee8a59ce1f4dd4b926f936e8e4bf43/`.

**Limits, thesis relevance and next step:** no commit/push/merge or Drive edit.
Published `ab8d7b2` CI is historical and does not cover these working-tree changes;
new-SHA CI awaits publication. The user's previous PostgreSQL retry is still
user-unconfirmed. Controlled T15 is locally complete and ready for review/closure;
observed receipt/model promotion and full V2 are not. Next: review/publish, verify
CI, user merge decision, then T16 controlled planning cockpit. Chapters 4/6/7 can
use source separation, real composition, disruption comparison and immutable
upstream-independent retrieval; synthetic exposure is not predictive superiority.

## V2 Odoo/model controlled-fixture readiness (2026-10-07)

**Goal:** connect the selected controlled Odoo comparison case to V2 assembly and
establish a legitimate saved-model compatibility boundary before planning/storage.
User selected reuse of the development fixture. The accepted baseline is unchanged.

**Evidence:** clean entry HEAD `ab8d7b21b18ac4b7323e0ed32f637ae351658786`, PR #17
open/unmerged; exact-head quality, container-api-integration and GitGuardian success
verified by authenticated GitHub metadata. Odoo localhost responds. Existing RFQ
key authenticates uid 7 and the comparison reader maps group 2 / orders 16–18 /
suppliers 51–53 / product 54 / company 1 / UoM 1 / currency 1. Four focused existing
RFQ/identity/T6 integration tests passed, 16 deselected, 1.68 s; fresh pytest
temporary/cache folders avoided the prior Windows ownership issue.

The separately configured history key returned HTTP 401; it may be expired or
invalid, but its precise cause is not proven. Known T7 fixture orders 19–22 / lines
31–34 belong to supplier 55 and product 57, not the comparison context. These
bounded reads do not establish absence of other matching history. Existing model
envelope/inference requires synthetic source and its trained domain; a controlled
Odoo business fixture alone does not make that artifact compatible.

**Decision and deliverable:** added the small
[Odoo compatibility readiness plan](T15_ODOO_COMPATIBILITY_PLAN.md): reuse existing
readers/KPI/core/storage, require explicit V2 business terms and exact contextual
history, check source/domain/schema/cutoff/range before solve/store, and require a
versioned compatible dataset/model contract for a positive flow. No always-failing
new endpoint or source-type bypass. Current README and handoff link the plan and
record publication/readiness separately from historical evidence.

**Limits and next step:** renew only the dedicated history API key through the
documented human UI procedure and ignored `.env`, confirm, then verify read-only.
Identify or manually provision matching controlled evidence and define the saved
model contract before positive inference implementation. No production code, Odoo
mutation, dependency/infrastructure change, database reset, commit/push/merge or
Drive update. Full fast/PostgreSQL acceptance was not rerun for this documentation
preflight; the user's prior PostgreSQL retry remains unverified. T15's implemented
synthetic slice and complete Odoo/model acceptance remain separate closure claims.
Thesis relevance: source semantics, contextual joins, model applicability and
negative integration gates support chapters 4/6/7.

## T15 published CI, user temporary-directory failure and Hungarian synchronization (2026-10-06)

**Publication:** the user committed/published `feature/T15-implementation` at
`200af3e79ac82640fac882b95c2cf85ed80ff588` and opened PR #17. Authenticated GitHub
reads confirm OPEN, not merged; main remains `247914ac05663d7358d53036c08750d9390d1baa`.
Exact-head [Quality 37523314998](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37523314998),
[Container/API 37523314994](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37523314994)
and GitGuardian succeeded. Workflow status is verified; no new CI test count is
inferred. Earlier unpublished records below remain dated historical evidence.

**User result and diagnosis:** terminal demo worked according to the user's report.
Their PostgreSQL selection gave 14 passed / 7 setup errors / 2 warnings, 11.81 s:
WinError 5 under Windows Temp. All seven T15 tests depend on one temporary model
fixture, so they fail before planning/database assertions. The inspected shared
pytest root owner is `CodexSandboxOffline`, strongly supporting different agent/
terminal identity permissions; the exact nested failure path is unconfirmed from
the truncated traceback. A non-destructive agent fixture probe passed one test,
while the default repository cache emitted its own permission warning.

**Minimal correction and verification:** documented fresh GUID-based ignored
workspace directories for each pytest run, with explicit parent creation,
`--basetemp` and `cache_dir`. Updated current README/runbook examples and demo
troubleshooting. No ACL changes, shared Temp deletion or runtime/test logic changes.
First local trial lacked the parent: 383 passed / 40 setup errors, WinError 3.
Corrected Python 3.11 fast run: **423 passed / 44 deselected / one upstream warning,
24.33 s**, actual ML training/reload/inference and CBC included. The user's
PostgreSQL retry remains pending; no database/service acceptance was rerun here.
Ruff format/lint, compilation, dependency consistency and patch whitespace passed;
36 current PowerShell examples parsed and local document links/anchors resolved.

**Explicitly authorized Drive synchronization:** updated Hungarian living docs
00/01/02/03/04/06/07/08/99, retaining official title/task baseline, IDs, archive links
and historical checks/limits. The writing guide 05 was read and retained. Current
documents consistently state T13/T14 merged; T15 controlled assembly/saved inference/
MILP/scenarios/immutable storage and stored-only retrieval implemented and published,
PR #17 open, exact-head CI successful. AC-V2-08/10 pass in the controlled slice;
complete Odoo assembly/model promotion, frontend, plan approval/PDF and full V2 open.
Resolved obsolete T15 assignments and split repository technical truth from Drive
Hungarian thesis truth. 99 carries the followable terminal-first, small-increment,
meaningful-test and concise handoff principles without changing application settings.

Native file-backed before/after reads and exact comparison verified all intended
paragraph edits, preserved heading/list roles, dates and native links; new PR/CI
links retain inherited typography. Review snapshots and a verification receipt are
local artifacts in the task's `t15-sync-20261006` visualization directory. Main living
entry: [00_THESIS_STATUS](https://docs.google.com/document/d/1X2WGVVYn0j1ymX0cv5kQQGIaJiEc7pcLSZYDIrXA3VU/edit);
detailed record: [07_DEVELOPMENT_STATUS](https://docs.google.com/document/d/1Xgphr_FEurdFlK651s2DTJWlubwt9vii1c5st9iO6E8/edit).

**Limits and next step:** current repo documentation changes remain unstaged,
uncommitted and unpushed; published CI does not cover them. No service was started,
Odoo changed, database reset, frontend or approval/PDF added, or Git merge performed.
User retries the documented PostgreSQL command, reviews PR #17, and retains merge
control. Next product work is the bounded V2 Odoo/model compatibility plan, followed
by T16 cockpit. Thesis chapters 6/7 can use controlled integration/reproducibility
evidence with explicit synthetic, local, hosted and user-confirmed boundaries.

This log is organised by development increment. It records evidence and decisions,
not a commit-by-commit diary.

## Reproducible controlled T15 terminal demonstration (2026-10-06)

**Problem:** the manual API flow depended on ignored, previously generated
request/model files and did not provide a fresh-checkout demonstration. Entry
HEAD was the user's consolidation commit `d1b7acd3070f4c10f58f5bf4b5a61897cf2314ba`
on `feature/T15-implementation`; the working tree was clean.

**Decision and behavior:** added repository-local `tools/t15_demo.py` with offline
`prepare` and loopback HTTP `run`. Moved the existing controlled fixture generator
from the test helper and re-exported it there so tests/demo share one implementation.
Preparation produces a trusted saved model and matched base/outage requests. The
run creates an immutable base/child, checks stored GET and exact base replay,
prints costs/allocations and records per-run keys/responses in ignored artifacts.
Keys are written before POSTs for manual recovery; there is no automatic POST retry.
Remote/credentialed origins and redirects are disallowed for this local demo.
Added one real composition check with a no-training trap and parameterized origin
boundary checks. New terminal procedure explains model/DB/API roles, expected
EUR 102/109/106 results, restart retrieval, failure interpretation and cleanup.
Integration workflow path filters include the shared demo fixture module so changes
to it also exercise the PostgreSQL consumers in hosted integration.
No new production endpoint, dependency, infrastructure, migration or business rule.

**Evidence:** fresh Python 3.11 fast suite **423 passed / 44 deselected / one upstream
Starlette warning, 37.82 s**. Actual PostgreSQL T15 plus legacy persistence acceptance
**21 passed / one warning, 22.11 s**. Actual loopback Uvicorn and CLI run produced
base minimum EUR 102 (6/4/0), alternative EUR 109 (0/2/8), outage minimum EUR 106
(0/8/2), using generated-request supplier order. Base/child retrieval and exact
replay matched. After restarting the backend without a model directory, both
stored GETs and exact base/child replays returned 200 with equal snapshots; fresh
base returned 503. Detailed synthetic run/restart records remain under ignored
`.artifacts/t15-demo/` and `.artifacts/t15-demo-verification/`.
Ruff format/lint, compilation (including the demo tool), dependency consistency,
patch whitespace, document-link/anchor and PowerShell example syntax checks passed.

The existing disposable PostgreSQL container was already running; verification
created a separate `t15_demo_verify_20261006_14a55ea1` database rather than resetting
the user's test database. Windows 55432 was still refused, so a task-owned
localhost-only SSH tunnel enabled access. The temporary database, owned backend/
tunnel processes and runtime credential file were removed; existing Odoo and test
containers remain running. The real user `.env` and Odoo business data were untouched.

**Limits and next step:** new changes are unstaged/uncommitted/unpushed. GitHub main
still resolves to `247914ac05663d7358d53036c08750d9390d1baa`; the local consolidation
SHA could not be resolved and had zero hosted workflow runs. Local verification
does not establish hosted CI, observed-model validity, live Odoo/browser acceptance
or complete V2. Drive is unchanged pending the agreed publication/request sequence.
Next: review/publish the increment, verify the published SHA's CI and synchronize
the affected Hungarian records when requested; resolve the V2 Odoo/model boundary
before further integration claims. Frontend, plan approval/PDF and full demo remain open.

**Thesis relevance:** reproducible artifact preparation, actual ML/MILP/HTTP/storage
composition, explicit disruption comparison and stored retrieval across process
restart can support implementation/evaluation chapters. Synthetic exposure and
local/hosted/observed acceptance remain distinct.

## Followable workflow and documentation consolidation (2026-10-06)

**Problem:** current capability, historical scope and execution instructions were
mixed across a 647-line README, incremental handoffs and stale Drive status. The
user requested enduring, understandable terminal-first development principles
while retaining meaningful tests and the accepted procurement/thesis baseline.

**Decision and implemented behavior:** condensed README to 123 lines with the
product flow, current capability/publication state and next steps. Added a small
documentation map; retained historical handoffs, spikes and their limitations.
Reworked the existing terminal/persistence guides around task selection, command
purpose, prerequisites, expected result and cleanup. Clarified that one Podman
machine hosts two Compose projects and that database-reset tests must remain
separate from Odoo/application data. Documented the Python 3.11 environment,
real-test versus manual API paths, explicit Alembic URL and forwarding workaround.
Added durable working principles and the requested handoff format to AGENTS.md;
saved one user-requested memory extension note for future-chat continuity.

Quality now executes the mandatory ML/CBC runtime tests once within the full fast
suite instead of repeating them in separate steps. Updated the two existing CI
guard tests to check the fast selection and that runtime tests are not excluded
as integration/E2E, retaining dependency/no-skip checks. No production code,
dependency, Compose service, migration or accepted requirement changed.

**Evidence:** authenticated GitHub reads found remote main `247914ac05663d7358d53036c08750d9390d1baa`
with successful post-merge Quality 37358433437 and Container/API 37358433349.
The clean entry local T15 commit was `921673493d63b3e5fadd9189f50ee5b644308871`;
GitHub could not resolve it and returned zero workflow runs for that SHA.
Added a dated T15 handoff status without rewriting its pre-commit evidence.

Initial fast verification caught the two obsolete CI string guards: 417 passed,
2 failed, 44 deselected, 33.65 s. After updating those guards, Python 3.11 fast
regression passed: **419 passed / 44 deselected / one upstream Starlette warning,
31.00 s**, with actual saved ML/CBC execution. Seven runtime tests were also
confirmed in the fast selection by collection, not run a second time. Ruff
format/lint, compilation, dependency consistency and whitespace checks passed.
Local relative document links resolve and documented PowerShell blocks parse.
Both existing Compose configurations passed quiet validation with the local
provider; no service was started. The default shell did not resolve Podman, so
validation used the known installed binary outside the sandbox. The first pytest
run also encountered cache write warnings; the successful run used a fresh ignored
`.artifacts/consolidation/pytest-cache`, without modifying the existing cache.

**Limits and next step:** changes are unstaged/uncommitted/unpushed. No PostgreSQL,
live Odoo or browser acceptance was rerun; the historical T15 service checks still
predate its audit fixes. The Podman forwarding issue remains a workaround, not a
repair. Drive is unchanged and still records the T15 proposal; synchronize affected
Hungarian documents only on explicit request, consistent with the previously
agreed post-publication sequence. A fresh-clone interactive T15 demonstration
remains the next small usability increment; current automated acceptance generates
its own matched controlled fixtures. Complete V2/observed integration and the
planning frontend/approval/PDF remain open.

**Thesis relevance:** development methodology and reproducibility can cite the
task-specific runbooks and the separation of technical synthetic acceptance from
observed Odoo/model acceptance. Results should connect problem, decision,
implemented behavior, evidence and limitation rather than only count tests.

## Repository audit fixes (2026-10-05)

Moved the T12 create HTTP handler to FastAPI's worker thread and run its existing
async orchestration with `asyncio.run`. The synchronous PostgreSQL transaction/key
lock and awaited Odoo reads stay together in that worker, preventing a second
same-key request from blocking the API event loop needed by the first. Added a
single-event-loop concurrent HTTP regression with bounded synchronous lock
contention, compute-once storage and exact replay; this is a controlled lock test,
not new live PostgreSQL acceptance.

The shared T12/T15 bearer guard rejects non-ASCII credentials with `401` and treats
non-ASCII configured tokens as unavailable (`503`). T15 translates unrepresentable
history/score-validity datetime arithmetic into `422` invalid input, and malformed
stored snapshots into the existing persistence-error contract. Added regression
coverage for both API guards and the year-0001/year-9999 cutoffs; rejected creates
store no case and never solve.

Removed the unused T0 frontend health client, its URL property and four obsolete
tests, retaining the Reflex configuration check and current RFQ client. Removed
the unused solver risk-scale field without changing the MILP formulation. Clarified
that Alembic requires a process/configuration URL; added the explicit PowerShell
export from the backend's ignored `.env` configuration to the T15 handoff.

Verification on the audit working tree: Python 3.11.16 fast suite **419 passed /
44 deselected / one upstream Starlette warning, 30.89 s**. Ruff format/lint,
compilation, dependency consistency, whitespace and both quiet Compose
configuration checks passed. Podman configuration checks required execution
outside the sandbox after its executable was denied; neither started services.

Changes remain unstaged, uncommitted and unpushed. No Odoo operation, database
migration, hosted CI, browser E2E or Google Drive change is part of these fixes.

## T15 — controlled planning API, scenarios and immutable cases (2026-10-05)

User authorized the reviewed controlled slice on `feature/T15-implementation`,
entry HEAD `aac86eb7c7081fc3a780efa4da351f5616cd1185` (user-committed documentation
proposal). Added V2 fact/field-provenance assembly, trusted saved T14 inference,
unchanged T13 planning, three guarded HTTP operations, five explicit stress types
and immutable JSONB case/key storage with stored-only GET/exact replay. One migration
`20261005_01`; V1 tables/decoding/routes preserved. Scenarios retain frozen scores,
revalidate full bounds, update source attribution and store new child snapshots.
No new dependency, Odoo read/write path, training route, frontend or approval/PDF.

Python 3.11 fast regression: 418 passed / 44 deselected / one upstream warning in
37.57 s. T15 plus legacy PostgreSQL persistence acceptance: 21 passed / one warning
in 22.14 s, including transactions, concurrent replay, immutability and rollback.
Real saved inference/CBC reproduced EUR 102/109; five scenarios match independent
small-instance enumeration. Actual loopback Uvicorn smoke proved create/retrieval/
retry/scenario behavior even with the model manifest temporarily unavailable;
new base failed safely with 503. Ruff, compilation, pip and whitespace checks passed.
The final blank model-setting normalization also passed its targeted API guard/
configuration check (1 passed, 3.50 s).

Used the existing isolated T11 test Compose service with synthetic credentials.
Windows forwarding to 55432 still failed; a temporary localhost-only SSH tunnel
to the healthy VM service enabled tests. Temporary server/tunnel/test container
were cleaned up; the user's Odoo stack and ignored user `.env` were unchanged.
No live Odoo, browser or full service suite was run. Detailed evidence/configuration
and API semantics are in `docs/T15_HANDOFF.md`; generated local proof is ignored.

Integration CI path filters now cover the consumed ML package. Hosted T15 CI remains
UNVERIFIED; T13/T14 run results below do not cover these edits. Changes are left
unstaged/uncommitted/unpushed for review. Drive synchronization is deferred until
review; full V2 and observed-model promotion remain separate open gates.

## T13/T14 — post-merge documentation reconciliation (2026-10-05)

Verified through authenticated GitHub branch/PR/workflow/job reads: T13 PR #15
merged at `ff8cc5bfebaef5f8d73751991101008830307012`; T14 PR #16 merged at
`247914ac05663d7358d53036c08750d9390d1baa`, which is current remote main and
the clean entry HEAD of `feature/T15-implementation`. Local ancestry confirms T13.
The local SSH alias lookup failed and `gh` was unavailable; no fetch or remote-ref
update is claimed. The GitHub connector supplied current remote evidence.

On exact main SHA `247914a`, post-merge
[Quality 37358433437](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37358433437)
and [Container/API 37358433349](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37358433349)
are SUCCESS. Job steps verify actual Python 3.11 T13 CBC and controlled T14
training/reload/inference/MILP, plus integration, frontend compilation and technical
volume persistence. Earlier documentation-SHA Container/API run 37190288285 also
completed successfully after the prior handoff. T13 merge-SHA Quality 37155058879
and Container/API 37155058875 passed. Exact links and distinctions are in
`docs/T14_HANDOFF.md`; no new test counts are inferred from job summaries.

Historical local checks, the Podman socket failure, skipped service/live/browser
tests and synthetic limitations below remain unchanged. Full V2 and observed
Odoo/model promotion remain OPEN. The current tree cannot accept observed input.

Synchronized and read back all ten active Hungarian Drive living documents in
`SZAKDOLGOZAT/00_Project_Control` (00–08 and 99; 05 date only). Current merge/CI,
controlled T14, ADR-025 and requirement status now agree. Contradictory task-sheet
draft/advisor statements follow the issued/approved baseline already in 00/05;
the official PDF was not independently reread. Preserved historical limitations,
requirement IDs, native document structure/resource links and archives. Corrected
duplicate sync dates to one Hungarian native October 5 date chip. Saved original
reads and paragraph-level before/after review evidence; exact links are in the
handoff. Full V2 and observed-model promotion remain open, independently of the
controlled synthetic demonstration.

Fresh local Python 3.11 verification: 394 passed / 37 deselected / one upstream
Starlette warning in 33.85 s; Ruff format (132 files), lint, compilation, pip check
and whitespace check passed. Read-only Compose configuration passed after the
user started Podman, using the existing local provider outside the sandbox;
initial sandbox launches were denied. No service/live tests were run, so the
historical Podman socket failure and unverified live/browser gates are retained.

Prepared `docs/T15_IMPLEMENTATION_PLAN.md`: controlled assembly, trusted saved-model
inference, unchanged T13 MILP, explicit scenario reruns, immutable V2 snapshots and
stored-only GET/exact retry. Defines three narrow API operations and meaningful
acceptance checks; no frontend, approval/PDF, Odoo writes or speculative services.
This is a documentation-only proposal; T15 implementation is not authorized here.

## Historical T14 — controlled Decision Tree supplier-evaluation pipeline (2026-10-04)

Verified current remote main/T13 merge `ff8cc5bfebaef5f8d73751991101008830307012`,
clean entry tree and Python 3.11.16 328-pass legacy/T13 baseline. Read current
original Drive 00/02/03/06/07; their pre-merge status remains a dated record.
Branch `feature/t14-decision-tree-pipeline` starts from that main. Saved
`docs/T14_ML_DESIGN.md` before source implementation; inspected isolated ML spike
ffa2939 without merging its cumulative code.

Added `supplier_evaluation/` with controlled receipts and separate future label
evidence, existing T8 Expected Arrival KPI calculation, strict as-of/identity/group/
duplicate gates, fixed training-only DecisionTreeClassifier fit, trusted local
artifact manifest/checksum/runtime validation, actual float32 tree paths, explicit
metrics and a narrow T13 risk-input/CBC demonstration. Two quantity-independent
historical features replace the spike's quantity-100 mismatch. Coefficients are
versioned uncalibrated exposure proxies with complete declared quantity coverage;
synthetic models reject observed contexts, missing scores never become zero.

Seed 17; train 160 suppliers [43,117] at January 1, test 80 disjoint later suppliers
[24,56] at March 1. Confusion matrix [[23,1],[0,56]], accuracy 0.9875, macro F1
0.984937. Depth 3/five leaves. These measure an intentionally constructed noisy
synthetic mechanism, not real-world prediction quality. Actual inferred scores
produce a EUR 102 minimum-cost and EUR 109 lower-exposure plan under a 10% cost cap,
using unchanged T13 MILP semantics.

Required dependencies: sklearn 1.8.0, NumPy 2.3.5, SciPy 1.16.3, joblib 1.5.2 and
threadpoolctl 3.6.0, installed only under ignored project-local Python 3.11.16.
Quality CI installs and exercises real ML training/reload/inference/CBC, with no
optional runtime skips. Generated datasets/models/reports are ignored; the small
`docs/T14_EVALUATION.json` is reviewable evidence. README and AGENTS scope/commands
are updated. FR-V2-02/03, AC-V2-02/03 and FR-V2-07 tree explanation target LOCAL
PASS within controlled scope. Complete V2 and real prediction remain open.

Final full fast suite passed with 394 tests / 37 deselected in 48.22s, including
66 T14 tests; one upstream Starlette deprecation warning. Formatting (131 Python
files), lint, compileall, pip check and whitespace passed. Local Podman Compose validation FAILED with
127.0.0.1:64087 connection refused. Service/live Odoo/browser checks SKIPPED;
hosted T14 CI and real prediction UNVERIFIED. Exact executed evidence is in
`docs/T14_HANDOFF.md`, together with reproduction commands, measured metrics,
traceability, limitations and a proposed Drive synchronization summary.

No Decision Core/solver/WSM/API/history/persistence redesign, new Odoo assembly,
HTTP route, migration, Reflex, approval/PDF or Odoo mutation. T15 owns full
application/API/scenario/snapshot composition. Changes remain unstaged,
uncommitted and unpushed; no PR/merge or Drive write was performed.

## T0 — Development foundation and early Odoo capability spike

### Objective

Establish a reproducible, maintainable local foundation before any procurement
decision logic is implemented. The increment covers repository conventions, a local
Odoo environment definition, thin FastAPI and Reflex boundaries, basic automated
checks, and an evidence-based assessment of Odoo integration capability.

### Implemented components

- Root development conventions in `AGENTS.md`, including architecture, language,
  secrets, documentation, and Google Drive constraints.
- A Python project definition in `pyproject.toml`, with FastAPI, Reflex, test, and
  linting dependencies.
- A typed `GET /api/v1/health` FastAPI endpoint that has no database, Odoo, or
  procurement-logic dependency.
- A separate Reflex app that calls the documented health endpoint over HTTP using
  environment-aware `BACKEND_BASE_URL` configuration and displays an unavailable
  backend state clearly. Its state-changing handlers use `@rx.event` so Reflex and
  static type checkers treat them as valid UI event handlers.
- Explicit empty boundary directories for the future Decision Core and Odoo adapter.
- A portable Compose local environment, verified with Podman, for Odoo 19.0 and
  PostgreSQL, with named volumes, an internal network, localhost-only Odoo exposure,
  and a PostgreSQL health check.
- Automated tests for the API response contract and frontend API URL configuration.
- An initial Odoo capability spike at `docs/spikes/odoo-capability-spike.md`.

### Affected requirements

- **NFR-01:** explicit module and infrastructure boundaries.
- **NFR-02:** no Decision Core implementation is coupled to Odoo; the Odoo adapter
  is separated and unimplemented pending validation.
- **NFR-05:** deterministic API and configuration tests, plus standard lint/format
  commands.
- **NFR-06:** Reflex is a separate component that uses the API only.
- **NFR-07:** adapter documentation requires a dedicated least-privilege user and
  external API access; no credentials are committed.
- **NFR-08:** pinned image tags, `.env.example`, Compose, named volumes, and startup
  procedures support reproducible local execution.
- **AC-08:** supported indirectly: the spike identifies validation work required
  before constructing a complete ERP-independent decision input.

### Commands and verification performed

Initial read-only assessment on 2026-09-16:

```text
Get-Location
git status --short --branch
Get-ChildItem -Force
rg --files -g README* -g AGENTS.md -g *.md -g *.yml -g *.yaml -g *.toml -g *.json -g *.env*
Get-Content -Raw README.md
git log --oneline -5
docker --version
docker compose version
python --version
py --version
uv --version
poetry --version
node --version
npm --version
```

Results: the repository was clean on branch `codex/t0-initial-setup`, contained only
a project-specific README and an initial commit, and had no `AGENTS.md`, config, or
implementation files. The initial agent-shell `PATH` did not expose Docker, Docker
Compose, Python, `py`, `uv`, or Poetry. Node/npm reported that no active Node.js
version was configured.

Subsequent local Python environment setup and verification:

```text
C:\Users\Erik Safar\AppData\Local\Microsoft\WindowsApps\python.exe --version
C:\Users\Erik Safar\AppData\Local\Microsoft\WindowsApps\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[frontend,dev]"
.\.venv\Scripts\python.exe -c "import fastapi, httpx, pydantic, pydantic_settings, reflex, uvicorn"
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
```

Results: Python 3.14.7 created the ignored project-local `.venv`. FastAPI,
Pydantic, Pydantic Settings, HTTPX, Reflex, Uvicorn, Pytest, and Ruff import from
that environment. Ruff formatting and linting pass. Pytest passes **2/2** tests.
`pip check` reports no broken requirements, and importing the Reflex application
from its runtime directory succeeds. Pytest emits two upstream deprecation warnings
from FastAPI/Starlette test-client dependencies; no project-code test failure occurs.

Post-implementation static checks executed:

```text
git diff --check
git check-ignore -v .env
git check-ignore -v .env.example
rg -n "odoo|postgres|sqlalchemy|psycopg|sqlite" backend frontend decision_core odoo_adapter tests
rg -n "5432:" infra README.md
rg -n "BACKEND_BASE_URL|/api/v1/health" frontend tests README.md .env.example
rg -n "[ \\t]+$" -g "*.py" .
git status --short
```

Results: `git diff --check` completed without whitespace errors. `.env` is ignored
while `.env.example` is intentionally not ignored. The source-boundary scan found no
Odoo, PostgreSQL, SQLAlchemy, psycopg, or SQLite references in backend, frontend,
Decision Core, adapter, or test code. The infrastructure documentation/configuration
scan found no host PostgreSQL port exposure, and the frontend configuration and API
health route references were present where expected. These are static checks only;
they do not validate Compose parsing or runtime behaviour.

A separate Python-source length check found no lines longer than the configured
100-character limit.

Those initial gaps were closed by the formal audit below. The earlier result is
retained here as chronological evidence, not as the current project status.

### Formal T0 closure audit — 2026-09-16

The audit used the committed T0 baseline `9af70cc` and preserved all existing work.
The installed Podman CLI was not initially on `PATH`; its local installation
directory was prepended for the audit. The existing WSL machine was started through
the CLI, without relying on Podman Desktop operations.

Verified versions:

- Python 3.14.7; Ruff 0.16.7; Pytest 8.4.2.
- FastAPI 0.141.1; Uvicorn 0.53.0; Reflex 0.9.11.post1; HTTPX 0.28.1;
  Pydantic 2.13.5; Reflex-managed Bun 1.4.0.
- Podman client/server 6.0.2, Windows/amd64 client and Linux/amd64 server on the
  WSL provider.
- `podman-compose` 1.6.0, invoked by `podman compose` as its external provider.
- `postgres:16.15-bookworm` image ID
  `5f71c21b69a7977b82247582e2e731ed76bdebaadb7dd7945ed76bcc9ed06632`.
- `odoo:19.0-20260908` image ID
  `400a621198ea355394df4a328b0f65043ffd1f4e79a5025ba16edf03cb26893d`.

Representative commands actually executed:

```text
podman version
podman info
podman machine list
podman system connection list
podman compose version
podman compose --env-file .env -f infra/odoo/compose.yaml config
podman compose --env-file .env -f infra/odoo/compose.yaml up -d --build
podman compose --env-file .env -f infra/odoo/compose.yaml ps
podman compose --env-file .env -f infra/odoo/compose.yaml logs --no-color --tail=100
podman compose --env-file .env -f infra/odoo/compose.yaml restart
podman compose --env-file .env -f infra/odoo/compose.yaml down
podman compose --env-file .env -f infra/odoo/compose.yaml up -d
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m compileall -q backend frontend decision_core odoo_adapter
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Push-Location frontend; ..\.venv\Scripts\reflex.exe run --loglevel info; Pop-Location
```

Runtime results:

- Compose configuration parsed successfully. PostgreSQL 16.15 became healthy and
  Odoo 19.0 started after replacing its removed `--admin-passwd` CLI option with a
  mode-restricted runtime configuration file.
- Odoo's database selector returned HTTP 200. The Windows forwarding helper on this
  particular Podman machine failed to expose the declared localhost binding, so the
  host smoke test used a temporary SSH tunnel bound only to `127.0.0.1`. A broader
  network bind was explicitly rejected.
- FastAPI returned the documented JSON at `GET /api/v1/health` with HTTP 200.
- Reflex compiled and ran after declaring the flat app-module import, moving its
  state backend to port 8001, and removing the package marker that Reflex forbids in
  the app root. Browser inspection displayed the FastAPI `ok` state, a clear
  `Unavailable` state while FastAPI was stopped, and recovery to `ok` after restart.
- Container restart succeeded. Synthetic markers in both the PostgreSQL and Odoo
  named volumes survived a normal Compose down/up cycle. No volume deletion command
  was executed.
- Final static results after the closure fixes are recorded in `docs/T0_HANDOFF.md`.

**Closure decision: COMPLETE.** Every T0 Definition of Done item has executable or
inspection evidence. The Podman Windows forwarding-helper issue is an
environment-specific limitation with a localhost-only verification path, not an
unverified T0 feature.

### Verified technical facts

- Odoo 19.0 documentation supports PostgreSQL 13.0 or above.
- Docker Hub publishes official Odoo 19.0 image tags; this increment pins the
  dated tag `odoo:19.0-20260908` rather than `latest`.
- Docker Hub publishes `postgres:16.15-bookworm`; PostgreSQL 16 satisfies Odoo's
  documented version requirement.
- The official Odoo 19.0 image entrypoint accepts database connection settings via
  `HOST`, `PORT`, `USER`, and `PASSWORD`, waits for PostgreSQL, and invokes Odoo.
- Odoo 19 introduces the JSON-2 external API; its documented endpoint shape uses
  `/json/2/<model>/<method>` with a bearer API key. Legacy XML-RPC and JSON-RPC are
  documented as deprecated.

Sources and evidence are recorded in the capability spike.

### Assumptions

- The current official Docker image can be used as a local Community-oriented PoC
  environment, subject to runtime verification.
- A separate Odoo API user and API key can be configured with only the eventual
  required read permissions. This has not been tested in the local instance.
- `reflex run` will work after the declared dependencies and required Node runtime
  are installed; no replacement frontend was introduced.

### Open questions

- Which Odoo edition, plan, modules, and user permissions will apply to the target
  integration environment?
- Is JSON-2 enabled and suitable in the selected environment, and what exact
  timeout, pagination, rate-limit, and error semantics apply?
- Which specific database-dependent models and fields are available after installing
  the required Purchase and Inventory modules?
- Which source records and date semantics form valid input for later historical
  delivery-performance calculations?

### Important decisions and trade-offs

- **FastAPI and Reflex are minimal proof boundaries only.** This validates the
  replaceable frontend rule without prematurely designing application use cases.
- **No application database was added.** There is no persistence use case in T0;
  a dedicated persistence layer remains a future responsibility.
- **PostgreSQL is not exposed to the host.** Only Odoo binds to localhost; this
  reinforces the no-direct-Odoo-database-access principle.
- **The Compose Odoo image has no health check.** Only PostgreSQL uses a reliable
  image-provided `pg_isready` check. Odoo HTTP verification is deliberately a
  runtime check rather than an unverified shell assumption.
- **No Odoo models or fields were hard-coded.** Candidate concepts are documented
  separately as items to validate, not as a canonical mapping.

### Rejected alternatives

- Implementing a preliminary weighted scoring, ranking, repository, or generic
  adapter framework was rejected as out of scope and speculative.
- Replacing Reflex before testing it was rejected; there is no verified
  incompatibility yet.
- Exposing PostgreSQL or accessing it directly from the decision-support
  application was rejected as architecturally invalid.

### Known limitations and technical debt

- Image tags are explicit but not digest-pinned; a future reproducibility/security
  decision may pin multi-platform image digests after validating the target host.
- The frontend has a successful browser smoke test but no automated browser-level
  end-to-end test suite.
- No static type checker is configured. Ruff and Python compilation are the current
  static gates.
- The audited Podman Windows forwarding helper did not expose a localhost-published
  port. The runtime itself was verified through a temporary localhost-only SSH
  tunnel; the Compose file remains portable and securely bound to localhost.

### Dependency-isolation update

The project declares its runtime and optional development dependencies in
`pyproject.toml`. They are intended to be installed with
`python -m pip install -e ".[frontend,dev]"` inside the ignored `.venv` directory,
not into the system Python installation. This local environment was created and
verified with Python 3.14.7. `pydantic` is listed explicitly because it is imported
directly by the API schema, even though FastAPI also depends on it.

### Evidence locations

- `README.md` — operating instructions and boundary overview.
- `AGENTS.md` — future-agent rules.
- `infra/odoo/compose.yaml` and `.env.example` — local environment definition.
- `tests/test_health.py` and `tests/test_frontend_config.py` — intended automated
  checks.
- `docs/spikes/odoo-capability-spike.md` — external-source and local-environment
  evidence.
- `docs/T0_HANDOFF.md` — final Definition of Done matrix and runtime handoff.

### Suggested thesis chapter destinations

- System architecture and modularity: high-level architecture and T0 boundaries.
- Implementation methodology: Compose reproducibility, test strategy, and quality
  gates.
- ERP integration design: capability spike, API selection, least privilege, and
  unresolved data-mapping questions.
- Limitations and future work: environment-specific Podman forwarding, missing
  browser automation, and deferred decision logic.

### Explicitly unimplemented functionality

- Weighted Sum Model, normalization, scoring, supplier ranking, strategy profiles,
  hard constraints, historical KPI calculation, and final decision explanations.
- Canonical domain model and production persistence schema.
- Odoo adapter, authentication setup, validated model/field mapping, and synthetic
  Odoo data.
- Authentication/authorization, dashboard design, cloud deployment, queues,
  background workers, SaaS features, and LLM functionality.

## T0 automation follow-up — CI verification boundaries

### Objective and implementation

Automate repeatable verification without provisioning Google Cloud, AWS, or a
persistent deployment. GitHub Actions now defines two independent Ubuntu workflows:

- `quality` is the fast gate for pull requests, `main`, and manual dispatch. It uses
  Python 3.11, checks Ruff formatting and linting, compiles Python sources, runs only
  fast tests, checks installed dependencies and whitespace, and validates Compose
  configuration with temporary synthetic credentials.
- `container-api-integration` is path-filtered and cancellable. It starts Odoo and
  PostgreSQL through Docker Compose, starts FastAPI, runs only integration-marked
  tests, verifies Reflex frontend compilation with Node.js 22.22 as required by the
  locked frontend dependencies, and checks that synthetic files in both named
  volumes survive stack recreation. Failure logs are retained briefly.

Pytest now rejects unknown markers. Unmarked tests are fast, `integration` identifies
tests requiring running components, and `e2e` is reserved for a future browser-level
suite. The frontend HTTP mapping was isolated from Reflex state mutation so fast
tests cover successful responses, connection failures, and incomplete payloads.

### Compatibility and governance decisions

Python 3.11 is the single local and CI compatibility baseline because it is the
declared minimum in `pyproject.toml` and Ruff already targets `py311`. The earlier
successful Python 3.14.7 T0 run remains additional compatibility evidence. No
version matrix is introduced yet.

Only the stable `quality` check is intended to become mandatory. Maintainers must
configure that branch-protection requirement manually; this increment does not
modify GitHub settings or any other remote governance configuration. The heavier
integration workflow remains informative and manually dispatchable.

### Evidence limits

`reflex export --frontend-only --no-zip` verifies compilation only. Actual
Reflex-to-FastAPI success and unavailable-backend states remain documented browser
milestone checks, not automated E2E evidence. Likewise, synthetic marker files prove
technical named-volume persistence only; a real Odoo business scenario must be
verified later through the implemented Odoo adapter flow.

The repository remains the primary source of truth for executable implementation
artifacts and technical logs. Google Drive remains the primary source of truth for
the Hungarian thesis living documentation, project status, roadmap, requirements
baseline, and architectural decision records. No Google Drive document was changed
by this follow-up.

### Verification performed

Local verification on 2026-09-16 used the existing Python 3.14.7 environment because
Python 3.11 is not installed on this workstation. Ruff format and lint checks,
Python compilation, dependency checking, whitespace checking, and all six selected
fast tests passed; the two integration tests were excluded from the fast selection
and collected by `integration and not e2e`. The workflow YAML parsed successfully,
its trigger/job/concurrency structure was asserted, and Podman Compose accepted the
Compose configuration.

The local Reflex export reached the production build but could not complete because
the workstation's Node version-manager shim has no active Node.js version. The
integration workflow therefore provisions Node.js 22.22 explicitly. A full Python
3.11 run, frontend export, and container lifecycle remain to be confirmed by the
first GitHub Actions execution; they are not recorded here as locally passed.

The two password assignments in `.env.example` are intentionally blank. Earlier
human-readable replacement strings were not credentials, but resembled passwords
closely enough to trigger secret scanning. Compose's required-variable expressions
still prevent startup until a developer supplies separate local values in the
ignored `.env` file; no scanner-wide ignore rule was added.

### Developer operations guide and code navigation

`docs/LOCAL_DEVELOPMENT_AND_SSH.md` provides a concise PowerShell reference for
starting and stopping PostgreSQL, Odoo, FastAPI, and Reflex, running fast checks,
and configuring the Windows OpenSSH agent to cache the protected GitHub key across
restarts. The instructions keep the key passphrase and align Git for Windows with
the native Windows OpenSSH agent rather than introducing another agent process.

The repository now has a user-managed `.codegraph/` index. The generated local
index is ignored by Git, while `AGENTS.md` requires a focused CodeGraph query before
broad code searches or multi-file reads whenever that index is available. `rg`
remains the fallback for exact-text and non-code lookup. This reduces unnecessary
repository scanning and context use without treating the index as authoritative
for prose.

## T1 — Read-only Odoo RFQ vertical slice

### Objective

Demonstrate one complete but deliberately narrow business-data path: Odoo JSON-2 to
an isolated adapter, an ERP-neutral application use case, a thin FastAPI endpoint,
and a useful Reflex view. This increment remains read-only and does not implement
supplier evaluation or a recommendation.

### Implemented components

- An ERP-neutral `application/` contract containing the bounded open-RFQ use case,
  immutable RFQ and money DTOs, and an adapter protocol.
- A read-only `OdooRfqReader` using the validated Odoo 19 JSON-2
  `purchase.order/search_read` method with explicit fields, open-state filtering,
  newest-first ordering, a timeout, payload validation, and stable error translation.
- A FastAPI `GET /api/v1/procurement/rfqs` route with a 1–50 result bound. The route
  exposes no raw Odoo field names or payloads and maps upstream unavailability to
  HTTP 503 and invalid/rejected responses to HTTP 502.
- A restrained, responsive Reflex procurement ledger showing RFQ reference, vendor,
  order date, neutral status, and currency-aware total, plus explicit loading, empty,
  and unavailable states.
- Fast tests for the adapter request contract and mapping, API boundary and errors,
  frontend endpoint construction and presentation mapping, valid empty results, and
  invalid responses. Integration-marked tests perform a live read and verify that
  the configured identity is non-admin with read-only `purchase.order` access.

### Local evidence

On 2026-09-16, the `procurement_poc` Odoo 19 Community database had Purchase and
Inventory installed with demo data. The database-specific `/doc` page and live
JSON-2 calls confirmed `purchase.order/search_read` and the seven fields used by the
adapter: `id`, `name`, `partner_id`, `date_order`, `state`, `amount_total`, and
`currency_id`. User ID 2 was used only for the initial discovery.

The durable key now authenticates as user ID 7, `Procurement Integration`. The user
is internal, limited to company ID 1, is not a Settings administrator, and has a
custom read-only `purchase.order` ACL. Live access probes returned read `True` and
create/write/unlink `False` without performing a write operation.

All four integration tests passed with the local services running: least-privilege
access, the live adapter read, the separately served FastAPI health contract, and
Odoo HTTP availability. The FastAPI RFQ route returned HTTP 200 with seven mapped
RFQs. Eighteen fast tests passed, with all four integration tests excluded by the
fast marker expression. Ruff, Python compilation, dependency checking, Compose
configuration validation, whitespace checking, and the Reflex production export
passed. The export used the already installed Node.js 24.20.0; CI retains its
declared Node.js 22.22 baseline.

Manual browser acceptance also passed. The connected ledger displayed seven RFQs
with reference, vendor, order date, status, total, and currency. After FastAPI was
stopped, Refresh data cleared the prior rows and showed the explicit unavailable
state. Restarting FastAPI and refreshing restored the ledger. A temporary invalid
key produced HTTP 502 with code `odoo_response_error`; the UI showed the same safe
unavailable state and recovered after the correct process restarted.

### Security and scope decisions

- The API key exists only in the ignored `.env`; `.env.example` leaves the key blank
  to avoid both credential exposure and misleading secret-scanner findings.
- The durable API key belongs to the dedicated read-only integration user. The
  administrator discovery key is no longer required and should be revoked.
- The adapter performs no Odoo writes and never accesses PostgreSQL directly.
- No raw upstream response or credential is returned through API errors.
- The working demo records are capability evidence, not canonical thesis data.

### Deferred work

- Purchase-order lines, products, receipts, promised and actual delivery dates,
  partial receipts, returns, units, and multi-company record rules remain unvalidated.
- There is no pagination, retry policy, application authentication, browser E2E
  automation, or procurement decision logic.
- A real Odoo business-persistence scenario must be designed after an actual write or
  state-transition use case exists; synthetic volume markers still prove only
  technical named-volume persistence.

## T2 — ERP-independent Decision Core

### Objective and boundary

Implement the first deterministic procurement decision pipeline on canonical,
synthetic domain input without extending the Odoo adapter, application RFQ use case,
FastAPI routes, Reflex frontend, or persistence. The Decision Core imports none of
those delivery or infrastructure layers, and the existing RFQ projection is not
reused as a supplier offer.

### Implemented decision model

- Immutable `PurchaseRequirement`, `SupplierOffer`, `StrategicProfile`, exclusion,
  contribution, ranked-offer, and decision-result objects.
- Explicit validation for identifiers, quantities, price, lead time, MOQ, offer-ID
  uniqueness, non-empty offer sets, finite values, non-negative weights, and the
  supported weight total. All calculation values use `Decimal`.
- MOQ eligibility is evaluated before normalization. An offer is eligible only when
  requested quantity is at least its minimum order quantity; exclusions preserve the
  constraint, relevant values, and a human-readable explanation.
- Reusable cost and benefit min-max normalization. Unit price and lead time are both
  cost criteria in this increment. Equal values normalize to `1`, and bounds use
  eligible offers only.
- Weighted Sum Model scoring preserves raw value, normalized value, applied weight,
  and weighted contribution for each criterion. Total score is the exact sum of the
  recorded Decimal contributions.
- Ranking is score descending, then offer identifier ascending. Input ordering does
  not affect the result. When every offer is excluded, the result contains the
  exclusions and no recommendation.

### Reference evidence

For a quantity of 100, Offer A (price 10, lead time 10, MOQ 50) and Offer B
(price 12, lead time 5, MOQ 100) are eligible; Offer C (price 9, lead time 8,
MOQ 150) is excluded before bounds are calculated. Cost-focused weights rank A at
0.7 above B at 0.3. Urgent weights rank B at 0.7 above A at 0.3. Balanced weights
produce 0.5 each and the offer-ID tie-break ranks A first. The unit tests verify the
full contribution trace and all specified validation and edge cases.

### Verification performed on 2026-09-17

- Ruff formatting and lint: passed.
- Python compilation for all five source packages: passed.
- Fast tests: 57 passed, 4 integration tests deselected. This includes 39 Decision
  Core cases and the unchanged T0/T1 fast suite.
- Dependency consistency and whitespace checks: passed.
- Podman Compose configuration with the ignored local `.env`: passed using Podman
  6.0.2 and project-local `podman-compose` 1.6.0.
- Live integration tests: not executed in this T2 run. The existing containers were
  stopped, and Podman's known Windows forwarding helper failed during machine start.
  No T2 code touches the live integration path.
- GitHub Actions: not yet executed for this branch at the time of local handoff.

See `docs/T2_HANDOFF.md` for formulas, the complete manual calculation, scope limits,
and the final review handoff.

## T3 — Application and HTTP decision boundary

### Objective and boundary

Expose the existing Decision Core through one narrow synchronous application use
case and `POST /api/v1/procurement/decisions/evaluate`. The endpoint evaluates only
canonical input supplied in the request body. It does not call Odoo, reuse the RFQ
projection as an offer, access a database or local file, persist a result, select a
supplier automatically, or perform a write operation.

The dependency direction is `backend -> application -> decision_core`.
`application.decisions.evaluate_procurement_decision` accepts the existing immutable
domain objects and delegates evaluation to the Decision Core. The FastAPI route owns
request validation, request/domain mapping, response mapping, and translation of
known domain validation failures; it contains no constraint, normalization, scoring,
or ranking logic.

### Public contract

- The request contains one requirement, one or more canonical supplier offers, and
  one strategic profile.
- Decision-relevant numeric values use strict decimal strings in JSON and `Decimal`
  internally. Exponent notation, non-finite values, non-strings, and malformed
  decimal syntax are rejected by request-schema validation without repair or
  coercion.
- HTTP 200 returns the requirement and profile, the first-ranked offer or `null`,
  every eligible ranked offer and its complete criterion contribution trace, and
  every excluded offer with its failed constraint and relevant quantities.
- Request-structure failures use FastAPI/Pydantic's standard HTTP 422 response.
  `DomainValidationError` uses HTTP 422 with code `invalid_decision_input` and a safe
  domain message.
- An all-excluded outcome is HTTP 200 with an empty ranking and no recommendation.

OpenAPI registers explicit request and response schemas, the reference request, the
POST operation, HTTP 200, and HTTP 422. Its operation description states that scores
are relative WSM results, excluded offers are not scored, and the endpoint provides
human decision support without persistence or an Odoo write.

### Reference evidence

For requested quantity `100` and cost-focused weights `0.7`/`0.3`, Offer C is
excluded by MOQ before normalization. Offer A ranks first at `0.7`; Offer B ranks
second at `0.3`; the recommendation identifies Offer A. The returned contribution
trace is deterministic and includes raw value, normalized value, weight, and weighted
contribution for both criteria. Balanced weights tie at `0.5` and retain Offer A
first through the offer-ID tie-break; urgent weights rank Offer B first.

### Verification performed on 2026-09-17

- Ruff formatting and lint: passed for all tracked Python sources.
- Python compilation for all five source packages: passed.
- Fast tests: 80 passed, 5 integration tests deselected. This includes 23 new
  application/API cases and the unchanged T0, T1, and T2 behavior.
- Dependency consistency and whitespace checks: passed.
- Static boundary scans found no forbidden framework, HTTP, Odoo adapter, database,
  or environment imports in `decision_core/` or the T3 application use case.
- Podman Compose configuration: passed with Podman 6.0.2 and project-local
  `podman-compose` 1.6.0.
- Served FastAPI smoke tests: health HTTP 200, reference evaluation HTTP 200, and
  invalid semantic input HTTP 422 with `invalid_decision_input`; both selected
  runtime integration tests passed.
- Odoo-dependent integration tests and the RFQ HTTP smoke call were not executed.
  The containers became healthy, but the known Windows `win-sshproxy.exe` failure
  prevented the localhost Odoo port from accepting connections. No T3 behavior
  depends on Odoo.
- GitHub Actions: pending branch push and pull-request creation at the time of this
  local record.

See `docs/T3_HANDOFF.md` for the complete contract, evidence, limitations, and review
handoff.

## T4 — Evidence-first Odoo decision-input mapping spike

### Objective and gate

Determine through supported, read-only Odoo 19 interfaces whether one procurement
requirement and multiple genuinely comparable supplier offers can be mapped to the
existing canonical `PurchaseRequirement` and `SupplierOffer` types. Production
adapter work was conditional on validating every critical grouping, product, UoM,
quantity, supplier, price, currency, lead-time, MOQ, state, and multi-line invariant.

### Runtime result on 2026-09-17

The branch was verified against fetched T3 merge commit
`f123446dac7994d9ea4727225c5fe4a9d0a39cd5`; the T3 handoff and decision endpoint
were present, and 62 focused Decision Core/application/API tests passed.

Podman client/server 6.0.2 started the existing PostgreSQL and Odoo services.
PostgreSQL became healthy and Odoo returned HTTP 200 through the documented
localhost-only SSH tunnel. The database-specific `/doc?db=procurement_poc` route was
present but redirected to interactive login; the JSON-2 bearer key did not establish
a web session.

After the dedicated key was renewed, `res.users/context_get` authenticated as the
non-admin `Procurement Integration` user, limited to company ID 1. The existing RFQ
contract passed again. Narrow `fields_get`, `check_access_rights`, `search_read`, and
module queries verified:

- read-only access to `purchase.order`, `product.product`, `product.template`,
  `product.supplierinfo`, `res.partner`, `res.currency`, and `uom.uom`;
- denied create, write, and unlink access for every candidate model;
- denied read access to `purchase.order.line`, with HTTP 403 from a bounded line
  query and from traversing `purchase.order.order_line`;
- installed Purchase and Inventory modules, but no installed
  `purchase_requisition`; and
- absence of the probed `alternative_po_ids`, `source_po_id`, and `requisition_id`
  fields on `purchase.order`.

Eleven bounded non-cancelled purchase documents were observed: seven open RFQs and
four confirmed orders, all in company 1 and USD. Supplier information exposed
configured `delay`, `min_qty`, price, currency, company, product template/variant,
date, and UoM concepts. Those master-data values cannot replace inaccessible actual
quotation-line values.

### Mapping decision

**SPIKE COMPLETE — CRITICAL MAPPING NOT AVAILABLE — ADAPTER DEFERRED**

The spike accepted source offer identity, observed commercial-supplier identity,
currency equality, and open-state mapping in isolation. It rejected heuristic
grouping, display names as stable identity, order total or supplier master price as
quoted unit price, line quantity as MOQ, silent conversions/defaults,
date-semantic conflation, and multi-line aggregation. Explicit grouping is not
available, and line-dependent mappings remain unresolved. The demo RFQs are not
treated as one comparison case.

No adapter, synthetic mapping fixture, new endpoint, frontend change, Decision Core
change, permission change, module install, direct database access, or Odoo business
write was introduced. See `docs/spikes/odoo-decision-input-mapping-spike.md` for the
complete evidence matrix and `docs/T4_HANDOFF.md` for the review handoff.

### Verification performed

- Focused T2/T3 baseline: 62 passed.
- Renewed-key existing live contract: 2 passed.
- Focused T4 live contract: 11 passed, including exact access and schema/grouping
  checks.
- Ruff formatting and lint, Python compilation, dependency consistency, whitespace,
  and Podman Compose configuration validation: passed.
- Full fast suite: 80 passed, 14 integration/E2E tests deselected.
- GitHub Actions: not executed because no pull request was created from this local
  handoff and branch pushes do not trigger the quality workflow.

## T5 — Odoo comparison-case enablement, Phase A

### Approval-checkpoint result on 2026-09-17

Phase A completed read-only and made no Odoo mutation. The branch starts exactly at
the T4 merge `e8eccf71f786e7a987fdbc47b0c3c88e8f40b5ef`.

The existing T4 live contract passed 11/11 before T5 changes. Additional bounded
JSON-2 discovery established that this exact Community database contains the
standard LGPL-3 `purchase_requisition` module, displayed as **Purchase Agreements**,
in `uninstalled` state. `res.config.settings` exposes
`module_purchase_requisition`. Matching Odoo 19 source defines
`purchase.order.group`, `purchase.order.purchase_group_id`, and related
`alternative_po_ids` as the supported call-for-tender grouping mechanism. These
expected post-install fields remain unvalidated in the database until installation
is explicitly approved.

The dedicated identity remains user ID 7, company ID 1 only, with direct groups
`Procurement RFQ API Reader` and `Role / User`. `purchase.order.line` read remains
denied. The minimal proposed access change is one read-only line ACL on the existing
custom group. The installed Purchase global line record rule already restricts rows
to `company_ids`; no broad Purchase or Inventory role and no duplicate rule is
proposed.

Runtime field metadata also sharpened two critical semantic gates:

- `product.supplierinfo.min_qty` is the quantity required to benefit from a
  vendor-price row, not a hard supplier order minimum. It is rejected as the current
  Decision Core MOQ source.
- `product.supplierinfo.delay` is configured time from PO confirmation to warehouse
  receipt, while line `date_planned` is Expected Arrival and defaults from that
  planning value. No supplier-offer promise or deterministic canonical lead-time
  transformation is yet established.

The adapter gate therefore remains `NO-GO`. Phase B may proceed only after explicit
approval for the exact module, ACL, human group, and controlled fixture mutations in
`docs/spikes/odoo-comparison-case-enablement.md`. No adapter, Decision Core change,
Odoo write, module installation, permission change, role assignment, business-data
mutation, PostgreSQL access, or Google Drive change occurred in Phase A.

### Phase B result on 2026-09-18

The user approved the exact Phase B proposal and confirmed a database backup. Using
the supported Odoo administrator UI, Phase B installed the standard Community
`purchase_requisition` module through **Purchase Agreements** and added one access
entry named `Purchase Order Line Read only access` for `purchase.order.line` on the
existing `Procurement RFQ API Reader` group. Only read is enabled; create, write,
and unlink remain denied.

The global **Purchase Alternatives** setting initially implied **Manage Purchase
Alternatives** to every internal user. A live contract detected that the integration
identity inherited the group. The setting was disabled immediately, and the group
was assigned directly to `Mitchell Admin`. Final validation proves that
`Procurement Integration` does not have the feature group and its direct groups
remain exactly `Procurement RFQ API Reader` and `Role / User`.

Final JSON-2 evidence verifies installed `purchase.order.purchase_group_id`,
`alternative_po_ids`, and `requisition_id`, plus `purchase.order.group.order_ids`.
The dedicated identity can read `purchase_group_id` and traverse permitted
`order_line` values without direct access to `purchase.order.group` or
`purchase.requisition`. Bounded line reads expose the exact product variant, UoM,
quantity, quotation unit price, discount, taxes, currency, company, expected
arrival, and selected supplier-price row. All observed rows belong to company 1,
and an explicit outside-company query returns no rows.

The semantic result remains `NO-GO`. `product.supplierinfo.min_qty` is still a
price-tier threshold rather than a hard supplier MOQ, and the available configured
delay and Expected Arrival fields do not establish authoritative supplier-offer lead
time. The approved pre-fixture stop gate therefore prevented creation of T5
suppliers, products, supplier rows, or alternative RFQs. No production adapter,
Decision Core change, direct database modification, application Odoo write, T6 work,
or Google Drive change was made.

Focused live Odoo verification passed 16 tests after the permission remediation.
Final verification also passed the full served integration selection with 19 tests,
the 80-test fast suite, Ruff format and lint, Python compilation, dependency
consistency, Podman Compose configuration, the Decision Core framework-import
boundary scan, the `.env` ignore check, and the final diff check. GitHub Actions
status is recorded in the external task handoff after the branch is pushed.

## T6 — provenance-aware hybrid decision-input assembly

### Implementation on 2026-09-18

T6 starts from `main` commit `c2c4b18`, which contains the required T5 commit
`392e2482ce11aef9446722251b868d926f814a0a`. The unchanged baseline fast suite
passed 80 tests with 19 integration/E2E tests deselected.

The application now defines immutable typed Odoo comparison facts, supplemental
offer terms, per-field source attribution, a canonical input aggregate, a separate
provenance manifest, and `assemble_decision_input()`. The assembler accepts only the
explicit single-product T6 subset and raises stable `DecisionInputAssemblyError`
codes for incomplete, ambiguous, inconsistent, unsupported, or domain-invalid
input. It joins supplemental terms only by stable Odoo offer identity and passes no
provenance data into the unchanged Decision Core.

`OdooComparisonCaseReader` reads one explicit `purchase_group_id`, bounds the group
at 20 offers and 40 total lines, and retrieves orders, exact line identities, and
commercial-partner identities
through JSON-2. It requests quotation facts only. It does not request or map
`supplierinfo.min_qty`, `supplierinfo.delay`, or `date_planned`, and it preserves
unsupported states, discounts, and taxes so the application layer can reject the
complete case rather than silently dropping offers.

Fast tests cover the exact reference case, deterministic identity join, provenance,
all material fail-closed invariants, canonical domain errors, adapter transport and
mapping, and architectural boundaries. Two live contracts cover the controlled
fixture and complete Odoo-to-evaluation chain, but require both configured read-only
credentials and `RUN_T6_LIVE_CONTRACTS=true`.

The controlled fixture uses the specification's documented UI fallback rather than
an unvalidated administrator writer. Exact JSON-2 create/wizard defaults and safe
teardown semantics are not established in this repository, so automating those
writes would be a risky approximation. `docs/T6_FIXTURE_SETUP.md` defines exact
markers, values, rerun checks, read-only verification, and cleanup.

### Live acceptance closure on 2026-09-19

A human administrator created the controlled fixture through the Odoo UI with exact
source markers `T6-COMP-001-A`, `T6-COMP-001-B`, and `T6-COMP-001-C`. Automated
tests did not trust that manual claim: using only the configured dedicated
integration identity, they found exactly those three RFQs, proved that they share
one persisted `purchase_group_id`, read the complete orders, lines, and commercial
partners, and validated every supported-subset invariant. The same identity's live
security contracts confirmed denied mutations, absence of the alternatives feature
group, and company-scoped line visibility.

The live full-chain contract assembled the exact reference case, passed the
canonical input unchanged to the existing evaluation use case, ranked eligible
offers A then B, and excluded C with an explanation. Its provenance assertion was
strengthened during closure to require the exact path set for the requirement ID,
requested quantity, all three profile fields, and all five canonical fields for
each actual live offer ID. Requested-quantity provenance is required once per offer.

Closure verification on the local Windows stack produced:

- focused T6 live contracts: 2 passed, 16 deselected;
- Ruff format and lint: passed, with 58 files already formatted;
- Python compilation and dependency consistency: passed;
- fast selection: 120 passed, 21 deselected;
- full integration selection: 21 passed, 120 deselected;
- Podman Compose configuration and final diff check: passed.

All 15 T6 acceptance criteria are therefore satisfied for the controlled local
proof-of-concept scope. The public RFQ ledger and caller-supplied decision endpoint
remain deliberately disconnected; the hybrid assembly path is internal and must be
explicitly invoked. No automatic or production Odoo-to-evaluation integration is
claimed. Supplemental provenance establishes attribution, not objective truth, and
the documented single-product, safety-bound, no-conversion limitations remain.

## T7 — historical supplier-performance capability spike

### Read-only discovery on 2026-09-19

T7 starts exactly from the T6 merge commit
`01b9ff16d77934c2164d75ae6f4d938d98eedee3`. It performed bounded live discovery
through the configured `Procurement Integration` JSON-2 credential and made no Odoo
write, administrator-key fallback, permission change, direct database access, or
browser-automated UI action.

Runtime metadata and official Odoo 19 source establish an explicit candidate path
from `purchase.order.line.move_ids` to `stock.move.purchase_line_id`, then
`stock.move.picking_id` to `stock.picking`. Line `date_planned` is **Expected
Arrival**, an editable operational schedule value rather than a supplier-confirmed
promise. For a done stock move, `date` changes from scheduled date to actual move
processing date. A defensible actual receipt still requires done state, positive
actual quantity, supplier-to-internal direction, exact line relationship, matching
product/UoM/company, no return relationship, and a done picking.

The identity can read purchase orders, purchase-order lines, stock move lines,
picking types, and locations. It cannot read `stock.move` or `stock.picking`;
bounded record queries return HTTP 403. Five confirmed orders contained eight lines,
all with zero received quantity and no completed receipt. No existing record was
joined heuristically.

The security probe also found that standard Odoo 19 grants `base.group_user` full
create/write/unlink rights on `stock.move.line`. The dedicated identity inherits
those rights through `Role / User`. No mutation was attempted, but the identity is
not read-only for inventory operation lines. Adding an ordinary read ACL cannot
revoke additive Odoo ACL rights, and broad Inventory roles remain prohibited.

Exactly one controlled candidate is retained:
`delivery_schedule_adherence`, the percentage of eligible completed PO-line receipt
obligations whose full current ordered quantity reaches the internal warehouse by
Expected Arrival. It groups by the T6 commercial-partner identity, uses one line as
the measurement grain, reports a separate completed-line sample size, uses a
trailing half-open 365-day window, rounds only presentation to two decimal places,
and withholds the value below sample size 3. Partial, backorder, multi-receipt,
return, cancellation, quantity-change, replacement, missing-date, timezone,
over-receipt, company, and ambiguous-relationship policies are explicit and
fail-closed where evidence is insufficient.

Odoo's computed `on_time_rate` is rejected because it has no separately exposed
sample size, groups by direct partner rather than the T6 commercial entity, applies
a quantity-weighted policy, and is unreadable through the integration identity.
`product.supplierinfo.delay`, first-receipt `effective_date`, aggregate
`qty_received`, coarse `receipt_status`, and `stock.move.line.date` are also rejected
as sole project KPI sources.

The result is **PENDING CONTROLLED LIVE ACCEPTANCE**. The new opt-in T7 contracts
default to skipped behind `RUN_T7_LIVE_CONTRACTS=false`. They require a separately
approved company-scoped read-only inventory-history boundary and four exact manual
fixture markers covering on-time, late, backorder, and return behaviour. Expected
controlled evidence is `33.33%` with sample size 3 and the return-affected line
excluded with a warning. No production KPI code, adapter, API, frontend, persistence,
Decision Core, `SupplierOffer`, `StrategicProfile`, T6 contract, or provenance change
was introduced. AC-07 remains unsatisfied.

See `docs/spikes/odoo-historical-supplier-performance.md` for the evidence matrix,
`docs/T7_FIXTURE_SETUP.md` for the mandatory security stop and human UI procedure,
and `docs/T7_HANDOFF.md` for the acceptance decision and T8 consequences.

Final local verification passed Ruff format and lint, Python compilation, dependency
consistency, Podman Compose configuration, whitespace checks, 121 fast tests, and
the complete available integration selection with 21 passed and the two gated T7
contracts skipped. Those contracts were not enabled because their documented
security and controlled-fixture prerequisites do not exist. Existing warnings were
limited to dependency deprecations, a local pytest-cache permission warning, and Git
line-ending conversion notices.

## T7-S — company-scoped read-only inventory-history projection

### Separate prerequisite implementation on 2026-09-19

T7-S is intentionally separate from the original T7 capability spike. It starts
from T7 commit `a47b035d48b89b604442a900b5f08a103bdd48a3` on branch
`codex/t7s-company-scoped-read-only-inventory-history-projection` and does not
retroactively expand T7's committed scope.

The implementation compares a generic `_auto = False` projection, a custom model
method, stored/transient projections, a custom controller, and direct stock-model
ACLs. It selects a public method on an Odoo `AbstractModel`. The addon creates no
table, stored copy, menu, view, or generic model ACL. Its custom group implies no
internal, Purchase, or Inventory role.

The existing internal `Procurement Integration` user remains unchanged for T6.
Because its standard internal-user role already carries additive
`stock.move.line` rights, T7-S instead defines a dedicated non-internal projection
caller and separate `ODOO_T7S_API_KEY`. The caller can invoke only the guarded
method and must remain denied generic access to the projection and to
`stock.picking`, `stock.move`, and `stock.move.line`.

`read_bounded_history` requires the active authorized company, a strict half-open
historical window no longer than 366 days, 1–50 exact purchase-order-line IDs, and a
result limit no greater than 200. The fixed response contains only stable company,
commercial supplier, PO/line, product/UoM, Expected Arrival, move/picking, done
processing timestamp, quantity, direction, backorder, and return evidence. Expected
Arrival remains an operational schedule and is not represented as a supplier
promise.

The dedicated caller deliberately lacks the underlying ACLs, so five private ORM
readers use elevated access. Every `sudo()` call is immediately followed by a fixed
`search_fetch` whose model, fields, company, exact relationships, date window, and
row bound were established before the read. No raw SQL or sudoed recordset leaves
the addon. Truncation, cross-company relations, unsupported states/directions,
missing or mismatched product/UoM/picking links, timestamp disagreement, and
backorder/return relationships outside the bounded result reject the entire call.

Fast policy tests cover bounds, exact output fields, company isolation, unsupported
states and directions, ambiguous returns and backorders, absence of raw SQL and
generic ACLs, and absence of implied broad roles. The opt-in live contract adds
same-company success, direct-model denials, projection CRUD denials, cross-company
rejection, and invalid-query rejection. The original T7 controlled test now reads
stock evidence only through the projection; it still computes no production KPI.

The Compose configuration mounts `infra/odoo/addons` read-only. A human
administrator installed the addon and configured the dedicated portal caller,
projection group, and short-lived API key; no Odoo UI action was automated.
`docs/T7S_MANUAL_SETUP.md` now documents both why the separate identity is required
and Odoo 19's temporary **Customers can generate API Keys** portal setting.

### Focused live security acceptance on 2026-09-20

The first focused run exposed a test-fixture selection error rather than a security
failure: the test chose an arbitrary purchased line whose `qty_received_method` was
`manual`, and the projection correctly failed closed with HTTP 422. The positive
security probe now selects a `stock_moves` line and uses a bounded known-empty
pre-fixture window, keeping semantic receipt evidence reserved for the controlled T7
fixture. The negative request assertions now expect Odoo 19's observed HTTP 422 for
model validation and unexpected method arguments.

The corrected focused command passed with **1 passed, 19 deselected**. It proved
same-company bounded access, a fixed response envelope, false generic CRUD rights on
the projection and all three stock models, HTTP 403 direct stock reads, HTTP 403
cross-company access, and HTTP 422 rejection of missing bounds, empty line IDs,
excessive limits, arbitrary arguments, and a 367-day window. The live gate was
immediately returned to `false`; the API key remains only in the ignored `.env`.

T7-S is now **COMPLETE — T7 LIVE VALIDATION MAY RESUME**. This permits the manual
controlled receipt fixture and original T7 live validation; it does not implement a
historical KPI or change T7 to `GO`.

### T7 controlled live acceptance on 2026-09-20

A human administrator created the four exact T7 receipt scenarios. The first live
run found a projection-policy contradiction rather than a fixture error: Odoo 19
represents the explicit internal-to-supplier return with an `outgoing` picking, while
the policy allowed the return move direction but required every picking to be
`incoming`. The correction permits `outgoing` only when every move in that picking
has the validated internal-to-supplier direction; the existing move and picking
return-link checks still require the exact original move and picking inside the
bounded result. New fast tests cover a complete accepted return and rejection of an
outgoing ordinary receipt.

After reloading only the Odoo service, the focused T7-S/T7 selection passed **2 of
2** and the complete integration selection passed **23 of 23**. Live evidence proved
one shared company, commercial supplier, product, and UoM; done move/picking
timestamp agreement; one on-time line; one late line; one late two-picking
backorder; and one explicit supplier return excluded from the candidate sample. The
controlled result is `delivery_schedule_adherence = 33.33%`, sample size `3`. Both
live gates were returned to `false`.

T7 is now **GO — CONTROLLED LIVE SUBSET ACCEPTED**. This authorizes only a later
narrow implementation over the accepted projection and edge-case policy. No KPI was
added to the Decision Core, application layer, API, frontend, or persistence, and
AC-07 remains unsatisfied.

## T8 — historical supplier-performance vertical slice

### Implemented on 2026-09-20

T8 starts from merged T7/T7-S `main` commit
`af8297c09a4043e2fa7f0a80e9b6ea795cc7ab85` on branch
`codex/t8-historical-kpi-vertical-slice`. The pre-change fast baseline was 141
passed and 23 deselected.

The increment adds an ERP-neutral `HistoricalPerformancePort`, bounded query,
receipt observation, snapshot, historical metric, availability, warning, and sourced
result contracts in `application/historical_performance.py`. The application
calculator implements the accepted line-count-weighted
`delivery_schedule_adherence` policy over an exact half-open 365-day window. It uses
the first cumulative full-receipt timestamp per line, keeps sample size separate,
rounds the percentage half up to two decimal places, excludes return-affected lines
with a structured warning, and withholds rather than substitutes a value below the
minimum sample size of three.

`OdooHistoricalPerformanceReader` implements the port using only
`procurement.inventory.history.projection.read_bounded_history`. It maps the fixed
T7-S response into neutral models after validating the full envelope/schema,
version, echoed company/window, count, requested line set, commercial supplier,
timestamps, state, direction, quantities, and stable identities. It adds no generic
stock-model read, Odoo mutation, direct database access, administrator credential,
or runtime fixture path. The T7-S addon and permissions are unchanged.

`CanonicalDecisionInput` now contains a tuple of contextual
`SupplierHistoricalPerformance` values. `attach_historical_performance()` joins by
stable supplier identity and requires a complete, unique mapping for the offer set.
It appends value, sample-size, and window provenance to the separate application
manifest. Source references identify the bounded projection context without secrets
or truth claims. Existing T6 callers remain compatible with an empty history tuple.

No Decision Core model, WSM formula, criterion, normalization, profile weight, MOQ
constraint, contribution, ranking, or explanation changed. Unit and controlled live
regressions compare the full result before and after history attachment.

Fast tests cover all-on-time, all-late, mixed, exact-deadline, immediately-late,
partial/multiple receipt, backorder, return, cancellation, zero denominator, sample
sizes 0/1/2/3, half-open boundaries, stable identities, warning order, rounding,
adapter request/response bounds, provenance, complete joins, and architecture.
Focused tests passed 72 of 72; the full fast selection passed 180 with 23
deselected. The focused live T7-S/T8 selection passed 2 of 2, and the complete live
integration selection passed 23 with 180 deselected.

The controlled production adapter/calculator result is
`delivery_schedule_adherence = 33.33`, sample size `3`: one on-time line, one late
line, one late two-picking backorder, and one return-affected line excluded with
`supplier_return_observed`. The same run revalidated company rejection, generic
stock access and mutation denials, canonical attachment, bounded provenance, and
unchanged ranking.

T8 is **GO — CONTROLLED VERTICAL SLICE IMPLEMENTED AND LIVE-VERIFIED**. AC-07 is
satisfied for the bounded internal slice. Public API/UI exposure, persistence,
arbitrary history discovery, and weighted scoring remain out of scope. Any future
scoring change requires explicit normalization, weights, missing-history policy,
sensitivity analysis, regression evidence, and an ADR or approved amendment.

## T9 — historical KPI scoring design and evaluation

### Implemented on 2026-09-20

T9 started from fetched, merged T8 `main` commit
`948c0928f74f6ec824a2185094164c1e59caf2eb` on branch
`codex/t9-historical-scoring-design-evaluation`. Before branching, the fast suite
passed with 180 tests and 23 deselected, `CanonicalDecisionInput` was confirmed to
contain contextual history, and the T8 AC-07 evidence was confirmed.

The increment adds an isolated Decimal-based evaluator under `tools/`, focused tests,
an ADR-style design/amendment proposal, and a handoff. It compares direct percentage,
comparison-set min–max, and illustrative band normalization; complete-case,
per-offer renormalization, neutral imputation, conservative imputation, and exclusion
policies; candidate weights for cost-focused, urgent, and risk-averse profiles; and
all 15 required deterministic scenarios. It also emits complete contribution traces,
baseline/candidate rankings, exact pairwise flip thresholds, missing-policy
sensitivity, and an add/remove-alternative experiment.

The evaluation recommends direct `value / 100` normalization and activation only
when every MOQ-eligible offer has usable history. Incomplete history falls back to
the exact current two-criterion scoring. Sample size remains an availability and
explanation field with the accepted minimum of three; T9 adds no confidence weighting
or bands because no defensible calibration exists. Candidate price/lead/history
weights are `.60/.25/.15` for cost-focused, `.25/.60/.15` for urgent, and
`.30/.30/.40` for a proposed risk-averse profile. They are PoC policy candidates,
not empirical optima.

Direct normalization remained stable in the controlled add/remove experiment,
whereas min–max reversed A and B after a third supplier changed only the historical
bound. The close-value case showed min–max expanding `79.99/80.00/80.01` to
`0/.5/1`. Missing-data alternatives changed rankings or removed an offer, supporting
the complete-case recommendation. The proposed profile matrix produced intentional
ranking changes in S04, S10, S11, and S15 while preserving MOQ-first exclusion and
deterministic tie-breaking.

T9 is **GO — BOUNDED POC SCORING IMPLEMENTATION AUTHORIZED** under the exact contract
in `docs/T9_SCORING_DESIGN.md`. This is not production validation. The minimum sample
size of three is not proof of statistical reliability, Expected Arrival remains an
operational schedule, and the weights are not learned. No Decision Core, runtime
profile, API, application/Odoo adapter, persistence, frontend, infrastructure, or
live fixture behaviour changed in T9.

## T10 — bounded, opt-in historical performance scoring

### Implemented on 2026-09-21

T10 started from fetched, merged T9 `main` commit
`58e3cfe92c8766093274571b87ad81af8b1bc8a1` on branch
`codex/t10-bounded-historical-scoring`. Before branching, local `main` equalled
`origin/main`, the accepted T9 design and handoff were present, and the fast baseline
passed with 197 tests and 23 deselected.

The Decision Core now has a small ERP-neutral historical input carrying stable
supplier identity, metric, value, sample size, and availability. A separate
`HistoricalScoringProfile` exposes the three accepted versioned policies, and
`evaluate_historical_decision()` is the only opt-in core entry point. The existing
`evaluate_decision()` and `StrategicProfile.cost_focused()`, `.urgent()`, and
`.balanced()` remain the default and preserve their weights and behaviour.

Both paths use one shared WSM scoring implementation. MOQ eligibility is partitioned
first. History activates only for a non-empty eligible set in which every offer's
supplier has one usable `delivery_schedule_adherence` value with `n >= 3`. Active
history is normalized only as `value / 100`; its contribution includes raw value,
sample size, normalized value, weight, weighted value, and deterministic text. If an
eligible offer lacks usable history, the wrapper returns the exact legacy
`DecisionResult` plus deterministic inactive context and sorted affected identities.
No value is imputed, no weight is redistributed, and no offer is penalized or
excluded for missing history.

The application adds an explicit mapper from T8 `SupplierHistoricalPerformance` to
the smaller core contract. It passes no source, warning, window, or provenance data
and rejects a selected historical policy whose fixed legacy fallback does not match
the canonical profile. Supplier joins use only stable IDs; duplicate and unknown
history fail closed, while multiple offers from one supplier share one history
result deterministically.

`tests/test_historical_scoring.py` converts the complete T9 S01–S15 matrix into
runtime parity regressions and adds validation for fallback equality, contribution
reconstruction, endpoints, the controlled `33.33`/`n=3` value, sample sizes 0–3,
invalid/non-finite values, duplicate and unknown suppliers, shared suppliers,
MOQ-ineligible history, all-excluded input, deterministic ordering, application
mapping, and unchanged legacy behaviour. Architecture tests prove the core remains
ERP/provenance independent and runtime packages do not import T9 tooling. Public API
schemas and routes, Odoo projection/adapter behaviour, persistence, and frontend are
unchanged.

The profile weights and `n >= 3` threshold remain PoC policy choices, not empirical
optimization or statistical reliability evidence. See `docs/T10_HANDOFF.md` for the
full command evidence, acceptance matrix, hosted CI status, limitations, and final
decision.

## T11 — decision-case persistence and human final-decision recording

### Implemented on 2026-09-22

T11 started from fetched, merged T10 `main` commit
`6f691ec31e64ad2763d477475b581c8c41bf2c3a`, the merge commit for PR #11. Local
`main` and `origin/main` matched after `git fetch --prune`; `docs/T10_HANDOFF.md`
contained the final merge-ready GO and passed hosted Quality, container/API, and
CodeRabbit evidence. The pre-change fast baseline passed with 222 tests and 23
deselected on Python 3.14.7.

The application now defines immutable `DecisionCase`, `HumanDecision`, and command
contracts, plus narrow repository/unit-of-work ports and three use cases: store an
evaluated case, retrieve it without recalculation, and record one human final
decision. Acceptance requires the stored recommendation; override requires a
different eligible offer and a non-empty rationale; no award forbids a selected
offer and requires a rationale. Unknown or excluded offers fail closed. Actor
references are caller-supplied attribution only.

Snapshot schema version `1` explicitly serializes canonical inputs, selected scoring
policy, legacy or T10 historical evaluation results, and provenance as separate JSON
documents. Decimal values use plain exact strings and times use UTC `Z` notation.
The historical form preserves activation/fallback context, affected identities,
sample sizes, deterministic explanations, rankings, exclusions, and ordered
criterion contributions. Unknown versions fail instead of being interpreted.

The concrete adapter uses SQLAlchemy 2.x and psycopg with PostgreSQL JSONB. Alembic
migration `20260922_01` creates the `decision_cases` table, relational lifecycle and
identity columns, checks, a unique idempotency key, and a trigger that rejects any
snapshot mutation and every post-finalization change. Final-decision fields and the
state transition commit in one transaction. Identical retries with the same key and
payload return the prior record; conflicting reuse or later decisions fail closed.
Application startup does not create schema objects.

Local focused unit/architecture checks passed with 35 tests. The full fast suite
passed with 246 tests and 32 deselected. The isolated PostgreSQL suite passed with 9
tests, including clean migration, three snapshot variants across separate sessions,
rollback, database immutability, uniqueness, sequential double-finalization, and
idempotency. Hosted CI remains pending until the branch is pushed and reviewed, so
T11 must not yet be described as final GO. See `docs/T11_HANDOFF.md` for the complete
acceptance status and excluded scope.

The complete integration selection also passed with 28 tests, 4 controlled live
fixture gates skipped because their opt-in flags were explicitly disabled, and 246
fast tests deselected. Both Compose models validated. The run used temporary
localhost-only tunnels for the known Podman Windows forwarding fault, then stopped
the backend, containers, tunnels, and Podman machine while preserving Odoo volumes.

## T12 — controlled end-to-end orchestration API (2026-09-22)

Starting `origin/main`: `0a1eee8a323f6cfe68a5cc30319d1f8c058d5c26`
(merged T11 / PR #12). Branch: `codex/t12-controlled-e2e-orchestration-api`.
Pre-change fast baseline: 246 passed, 32 deselected. Ruff format, Ruff check,
compileall, and pip check passed before implementation.

Added an application coordinator using the existing bounded comparison-case reader,
T6 supplemental assembler, optional T8/T7-S history path, accepted T10 policy
selection/evaluation, and T11 case repository. The three versioned decision-case
routes require a shared PoC bearer token; it does not authenticate the buyer or
`actor_reference`. GET reconstructs stored snapshots and never refreshes live data.
The original T3 evaluate route is unchanged. No Odoo write or frontend path was
added.

Alembic `20260922_02` adds durable creation idempotency with a canonical UUID key,
normalized SHA-256 request fingerprint, transaction advisory lock, and a unique
foreign key to the decision case. The key mapping and case commit atomically; exact
replay skips all upstream reads and scoring. T11's human-finalization idempotency and
immutable trigger remain separate and unchanged.

Verification and limitations are recorded in `docs/T12_HANDOFF.md`. This increment
does not discover arbitrary supplier history, verify supplemental values as facts,
provide production identity management, create a decision frontend, or write to
Odoo. The controlled T6 and T7 history fixtures are separate; no three-supplier
live historical-scoring claim is made.

## T13 — V2 domain and application-ready MILP procurement planning core

Live current Drive baseline, requirements, roadmap, development status and
ADR-024–027 were read before implementation. Entry GO followed verified remote
main `71396e8924f6a1f60daf8b45f02861adf21a25e5`, preservation of pre-existing
Reflex lockfile state, 271-pass legacy baseline and existing hosted-check review.
Branch `feature/t13-v2-milp-core` starts from that main; the cumulative experimental
PR #14 was selectively used as reference and remains unmerged.

Added frozen ERP-neutral requirement/supplier/policy/plan contracts under
`decision_core/planning/`, exact eligibility/output rules, a solver port and
deterministic minimum-cost/epsilon orchestration. `optimization_adapter/` implements
provisional PuLP/CBC with integer scaling, exact constraint checks, stable objective
locks, explicit solver statuses and one shared time budget. The thin application
entry point keeps external risk definition/assessment/validity context separate.
Coefficients must cover all allowed allocation quantities; missing scores never
become zero. No ML feature-schema decision or training was made.

PuLP 3.3.0 is required and the Python 3.11 quality job explicitly executes the
actual CBC runtime gate without optional skips. A project-local Python 3.11.16
environment verified CBC 2.10.3 and the entire fast suite: 328 passed, 37 deselected
in 10.47s, one upstream warning. All 57 T13 tests also passed on Python 3.14.7.
Ruff format/lint, compileall, pip check and whitespace checks passed. Podman Compose
validation FAILED because its machine socket refused connection; live integration
and browser checks were SKIPPED. Hosted T13 runs remain UNVERIFIED.

FR-V2-04–06 and AC-V2-04–07 are implemented/LOCAL PASS for this bounded core.
FR-V2-07 is PARTIAL because ML tree-path explanations belong to T14. Existing
WSM/API behavior and immutable version-1 T11/T12 snapshots, stored retrieval and
retry semantics remain unchanged. No new Odoo assembly/API, database migration,
Reflex integration, approval/PDF path or Odoo mutation was added. Changes are local,
uncommitted and unmerged. Design, exact evidence, file map and T14 questions are
recorded in `docs/T13_V2_MILP_DESIGN.md` and `docs/T13_HANDOFF.md`.

## T16 first increment — stored planning display (2026-10-07)

Problem: T15 results were accessible through the terminal/API but not a buyer-facing
planning page. Decision: reuse authenticated stored-only GET before adding creation
or scenario controls. Implemented `/planning` in the existing Reflex app, with saved
plans/allocations, exact money and rational exposure, explanations/tree paths,
parent lineage, provenance and safe loading/error/recovery. The shared credential
stays in Reflex server settings; synthetic ML remains clearly labelled.

Starting branch `feature/T16-reflex-frontend-implementation` at T15 merge
`3c19890bd17cd89ffd6d4fbdfca3152d07898f55`. Post-merge main Quality run
`37653141549` and Container/API run `37653141222` were rechecked successful for that
exact SHA. This supersedes older current-publication statements only; historical
local/hosted/live evidence and limitations above remain intact. T16 is uncommitted
and has no hosted result. The preceding user-requested Hungarian Drive sync on
2026-10-07 recorded merged T15 and controlled hybrid acceptance; no Drive write was
performed for this frontend increment.

Evidence: final Python 3.11 fast suite **451 passed, 45 deselected**, one upstream
warning, 41.33s; Ruff format/lint, compileall, pip check, whitespace, Odoo Compose
configuration and final production Reflex export passed. Actual browser checks
used Reflex/FastAPI with verified prior synthetic/hybrid snapshots in an isolated
memory repository, with upstream/model/solver disabled. Costs, scenario delta,
explanations/provenance, validation/missing/unavailable errors and recovery passed.
State/generated-browser-file checks excluded the service token. Browser checks
revealed and fixed paragraph nesting and a missing SQLAlchemy asyncio runtime
extra. A fresh ignored web/temp directory avoided the earlier Windows cache
permission failure. No new service was introduced.

Limitation: this is stored-case presentation and partial T16, not new live
Odoo/PostgreSQL browser acceptance, observed-model promotion or full V2. Creation,
scenario controls and charts remain T16 work; approval/PDF remains T17. Chapter
relevance: architecture (4), implementation (6), testing (7). Detailed boundary,
verification and next capability are in `docs/T16_HANDOFF.md`; executable terminal
steps are in `docs/LOCAL_DEVELOPMENT_AND_SSH.md`. User retains commit/push/merge control.

### T16 user startup recovery — 2026-10-07

The user's root `.venv` frontend run reported missing `app/routes.ts`, followed by
a cleanup `NoSuchProcess`. Inspection found an incomplete generated cache: Reflex's
actual `app/routes.js` and its generated Radix theme component were missing.
Restoring one template file removed startup failure but exposed an HTTP 500; the
complete cache was therefore preserved in ignored artifacts and regenerated by
the user's installed Reflex. Development startup, `/planning` HTTP 200 and browser
form rendering without console errors passed on Python 3.14.7 / Reflex 0.9.11.post1 /
Node 24.20.0, using temporary isolated ports. This does not alter the Python 3.11
ML/CI baseline or establish a new database acceptance. No application source,
dependency, tracked lockfile or business data changed; recovery procedures were
added to the terminal runbook. See the T16 handoff for the preserved cache path.

### T16 user stored-case connection recovery — 2026-10-07

Live FastAPI health returned 200, but authenticated planning GET returned 503:
the database URL was missing and the separate existing planning container was
stopped. Restarted that container without resetting/recreating it; its schema and
saved cases remained intact. Healthy PostgreSQL was still unreachable on Windows
55432, so the documented localhost-only 55433 SSH tunnel was started. Filled only
the empty ignored `.env` connection value with existing credentials, without
printing them or changing Odoo/configuration source.

A fresh in-process FastAPI stored GET -> actual PostgreSQL -> frontend mapper
verified the existing synthetic EUR 102/109 base and EUR 106 scenario with parent
lineage and EUR 4 delta. No training, Odoo read/write, migration or new case was
required. Database/tunnel remain running for user validation; the already running
FastAPI process needs a restart to load its settings. Its post-restart browser
acceptance remains pending. See `docs/T16_HANDOFF.md` for evidence/cleanup and the
terminal runbook for shared `.env` configuration and the forwarding procedure.

### T16 post-restart stored-display confirmation — 2026-10-07

The user confirmed the Reflex page now works. Independent live authenticated API
GET returned 200 against actual PostgreSQL for the EUR 102 synthetic base; its
stored provenance confirms controlled synthetic inputs and synthetic ML history.
Browser display is user-confirmed; live API/source provenance was agent-verified.
The prior hybrid report's UUID returned 404 in the current demo database. Historical
hybrid acceptance is retained without claiming that case is currently available.
This closes the local stored-display setup gap, not the remaining T16 creation,
scenario controls/charts, observed-model promotion or full V2 acceptance.


## 2026-10-07 — T16 controlled creation, supplier outage and buyer explanations

Problem: the first stored-view page exposed rational values and solver codes before
buyer quantities/trade-offs, while creation/scenarios required the terminal.
Decision: reuse the fixed offline T15 demo, existing authenticated POST/GET routes,
Reflex tabs/forms and CSS bars. No new backend contract, solver/model algorithm,
service, dependency, Odoo operation or broad restructuring was required.

Implemented: controlled synthetic demand creation, independent supplier-outage
children, base navigation, stored retrieval, quantity bars, exact cost/premium
presentation, schedule classes and receipt-history summaries. Expandable audit
sections preserve exact fractions, tree conditions, raw solver explanations,
identity and provenance. Tree conditions are not historical receipt rows; model
scores remain synthetic uncalibrated schedule-watch exposure. UI-edited demand has
an explicit controlled authority and source reference, retaining original commercial
terms/policy/history attribution. Human operational approval remains outside T16.

Trust/recovery: no token or artifact selector in browser state/forms; no training
in HTTP. Each action retains an exact payload/UUID key. Interrupted responses block
changed intent and require explicit recovery. An authentication failure during
recovery cannot discard earlier uncertainty. Copyable read-only JSON provides
manual recovery before the Reflex session ends; no durable request queue was added.

Evidence: focused suite 32 passed. Required Python 3.11 fast suite 465 passed /
45 deselected, one upstream Starlette/httpx warning; format/lint, compileall, pip
check and whitespace passed. Initial focused invocation lacked its basetemp parent
(WinError 3); creating a fresh ignored run parent fixed setup. A format-only mixed
line-ending check was corrected with Ruff. Later provenance/recovery logic changes
received focused checks and the required suite again; historical runs are retained.

Real isolated browser/API/PostgreSQL acceptance: base EUR 102/109
`8b64062b-b695-4ed9-b49c-52f43064c835`; S226-outage EUR 106 / +4 EUR
`ed2e23c1-c4e2-4c7a-90e0-0b3a6a1c6463`; edited demand 25 infeasible
`1e9c3368-d5db-4307-b7b9-1d2910199e31`. Independent stored GET verifies parent,
reused assessments and edited-demand references. Browser verifies constraint notes,
base navigation, service-down clear/recovery, disabled actions and exact-request
copy. 390px layout has one plan column and no page overflow; viewport restored.
Evidence files: `.artifacts/t16-next-browser/cases.json` and
`desktop-comparison.jpg`. Current manual cases/database were retained; no resetting
integration test or Odoo action was run against user data.

Runtime finding: default saved model failed the Python 3.11 manifest gate. A fresh
owner-generated model was prepared offline in the isolated verification folder;
its initial request equals the existing fixture. Original artifacts remained
unchanged. The preview API's process-only model setting was corrected; explicit
same-request retry recovered from 503. An unconfirmed in-app browser download was
replaced with native copy/read-only recovery JSON. Final browser inspection confirms the framework connection notice is hidden,
console warnings/errors are absent and requests succeed after reload. These are
local findings, not new hosted or production/browser automation acceptance.

Limit/next: controlled creation and one outage UI are complete locally; Odoo
quotation selection, other scenario controls and broader comparisons remain T16
work. Observed model promotion, approval/PDF and full V2 remain separate. No new
hosted CI was verified. First slice is committed as `b9987df`; this addition stays
unstaged/uncommitted/unpushed under user review. No Drive edits. Thesis relevance:
architecture, implementation, usability, provenance and testing chapters.

Final handoff checks: required suite 465 passed / 45 deselected / one warning in
45.85s after the final recovery fix; Ruff format/lint, compileall, pip check and
whitespace passed. Production frontend export passed all four build stages in the
isolated cache. Python 3.11.16 / Reflex 0.9.12 validates the baseline; live frontend
and export use existing Python 3.14.7 / Reflex 0.9.11.post1, with real FastAPI/model
on Python 3.11. Agent preview ports 3108/8208/8108 and browser tab were stopped;
user ports 3000/8001/8000 and database/tunnel 55433 remain available. No tracked
lockfile, default demo artifact, dependency or user environment value changed.

## 2026-10-09 - Matt Pocock skills aligned to the thesis baseline

Problem: installed engineering skills had no repository-specific issue tracker,
triage vocabulary or domain-document routing. Their generic defaults also needed
the official task, accepted Drive requirements and thesis evidence boundaries.

Decision: the user selected GitHub Issues and the five default triage labels,
reviewed the full setup draft, and approved applying it. Preserve the existing
AGENTS rules and canonical Drive FR-V2/NFR-V2/AC-V2 and ADR identifiers. Use one
domain context without creating an empty glossary or a competing ADR register.

Implemented: one appended Agent skills section; docs/agents/issue-tracker.md,
triage-labels.md, domain.md and project-baseline.md; README entry point. The
alignment guide maps every substantive official task clause to requirements,
evidence routes and thesis chapters. It distinguishes fixed principles from
replaceable implementation choices and preserves open V2 acceptance gates.
The user reaffirmed that all project living documentation and thesis material
on Drive stays Hungarian; repository engineering artifacts stay English. Each
increment records problem -> decision -> implemented behavior -> evidence ->
limitation -> chapter relevance. Future skills must refresh relevant sources.

Source review: supplied task sheet (423.589/25/140, dated 2026-09-22) extracted
and visually checked; current Drive 00/01/02/03/04/05/06/07/08/99 baseline and
relevant evidence sections reviewed, with departmental guidance for writing
context. This is requirements routing, not a completed thesis/prose audit or
an independent rerun of all historical acceptance evidence.

GitHub readback: PR #18 merged on 2026-10-09; local and remote main agree at
979b9b89e8517c65daefcf7e533c8b3f9c2c0ccd. Exact-SHA
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37923795850)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37923795924)
succeeded. Drive's 2026-10-08 status and repository pre-merge publication text
retain older statements; the alignment guide records the discrepancy. No Drive
correction or new hosted check was performed during this setup.

Label verification: GitHub already had wontfix. With gh unavailable in this
shell and the connector's generic label endpoint unsupported, the authenticated
GitHub browser UI created only needs-triage, needs-info, ready-for-agent and
ready-for-human. Readback verified all five labels; existing labels were retained.
No issues, comments or pull requests were created.

Local checks: Python 3.11.16; Ruff format (170 files), Ruff lint, compileall, pip
check, configuration/link assertions and git diff --check passed. Required fast
suite: 521 passed / 45 deselected / one existing Starlette-httpx deprecation
warning, 39.82 s. Two sandboxed test attempts stalled at the first FastAPI
TestClient test and were interrupted; sandbox escalation allowed completion.
These attempts are not passing suite results. No application logic changed;
no passing application checks were repeated after documentation-only edits.

Compose limitation: the initial guessed system installation path was absent;
Podman was subsequently found in the user's local Programs directory. The
sandboxed standalone provider check produced no result and was interrupted.
The documented podman compose config command failed on the local socket:
sandbox access was forbidden; outside the sandbox the existing endpoint
127.0.0.1:64087 refused the connection. Compose configuration acceptance is
therefore BLOCKED, not PASS. No machine/container was started and no database
was reset. Service/live/browser application checks were not run for this
documentation-only change; GitHub browser label verification is a separate scope.

Limitation and next capability: setup enables aligned skill use, not 100% thesis
completion. V2 plan approval/no-award, approved-snapshot PDF and full-flow
acceptance (AC-V2-11/12/13) remain open. Observed-model promotion and broader
quotation selection retain separate boundaries. The next buyer-visible step is
finalizing a saved valid plan and downloading its approved PDF, after its own
implementation authorization. Thesis relevance: chapter 3 requirements and
traceability, chapter 4 decisions, chapters 6/7 implementation and evidence,
chapters 8/9 conclusions and further development. No Odoo or Drive writes,
application dependencies, commit, push or merge were made.

## 2026-10-09 - V2 approval/PDF plan confirmed and implementation tickets published

Problem: saved V2 plans stop before human finalization and approved PDF; historical
V1 offer finalization does not satisfy the V2 allocation requirements.

Decision: use the explicitly invoked grill-with-docs, to-spec and to-tickets skills.
The user accepted base-only finalization, retained proven plans with incomplete-
comparison warnings, and labelled historical-demo approval with separate current
server-recorded decision time. Preserve official task 423.589/25/140, existing
FR/AC identifiers and accepted ADRs; no new accepted ADR was created.

Delivered: root glossary, confirmed T17 investigation/plan, complete specification,
approved ticket breakdown and [planning handoff](T17_PLANNING_HANDOFF.md).
[Specification #19](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19)
and implementation issues
[#20](https://github.com/SafarErik/odoo-procurement-decision-support/issues/20) ->
[#21](https://github.com/SafarErik/odoo-procurement-decision-support/issues/21) ->
[#22](https://github.com/SafarErik/odoo-procurement-decision-support/issues/22)
are published ready-for-agent. Bodies, labels, open states and explicit parent/
blocker links were read back and verified. Parent body/state/labels were unchanged
during ticket publication. Native relationship operations are unavailable; these
are text links, not native GitHub sub-issue or dependency objects.

Verification PASS: eight handoff files, 91 local links, 32 stories, three ticket
templates, source identifiers, dependency order and whitespace. Local spec/ticket
bodies match published content; git diff --check passed. No application tests were repeated after
documentation-only edits; the earlier 521-pass setup evidence above is historical.
No services, live Odoo or application browser checks ran, and the earlier blocked
Compose configuration gate is not resolved. New-commit hosted CI awaits user
publication. No procurement implementation, dependency/schema change, model
training, Odoo/Drive write, stage, commit, push, PR or merge was performed.

Next: review and commit the eight handoff artifacts on the existing skills branch,
publish/review its PR and verify exact-SHA CI under user control. After merge,
authorize #20 on updated main. Approval/PDF and AC-V2-11/12/13 remain open; observed
Odoo-history training, broader quotation selection and T18 evaluation are separate.
Thesis evidence: problem -> decision -> work definition/publication -> verified
issue/doc evidence -> implementation/runtime limits -> chapters 3/4/5 and later 6/7/8/9.

## 2026-10-09 - Saved V2 human approval and No-award (issue #20)

Problem: the buyer could compare immutable plans but could not record the final
allocation choice or reasoned No-award. A historical V1 single-offer decision
does not satisfy V2 allocation approval.

Decision: implement the first unblocked vertical slice from the user-supplied
[T17 planning handoff](T17_PLANNING_HANDOFF.md) on `feature/T17-implementation`,
starting at planning merge `f0c5552`. Reuse the HTTP recovery pipeline and
PostgreSQL transaction/locking patterns. Store human decision and versioned
approved content separately; preserve original planning rows and exact hashes.
No new dependency, accepted ADR, arbitrary Odoo selection or observed-model
promotion was introduced. Ponytail and Reflex documentation skills guided this slice.

Implemented behavior: explicit original-base minimum/alternative approval or
reasoned No-award, bounded non-authenticated actor audit text, explicit historical
demo acknowledgement, one server UTC decision time, pure saved-proof/constraint/
provenance checks, immutable canonical approved content, same-key semantic replay,
conflict protection and saved GET/creation recovery. Retained proven minimum and
earlier alternative remain eligible after later calculation failure with recorded
incomplete comparison. Stress children remain analytical. No-award creates no
approved content. The application does no Odoo acquisition, model load/inference,
training or solver execution during finalization/reopening/retry.

Migration `20261009_01` adds the base-linked `planning_final_decisions` table,
unique finalization keys, base-only insertion and UPDATE/DELETE protection.
Only a separate disposable database was migrated; applying the revision to the
user's helper database remains an explicit local setup step. Downgrade removes
human decisions/approved content. See [T17 handoff](T17_HANDOFF.md) and the
[decision walkthrough](LOCAL_DEVELOPMENT_AND_SSH.md#saved-human-decision).

Verification PASS on Python 3.11.16:

- Required fast suite: **562 passed, 54 deselected**, 48.08 s. Actual offline
  Decision Tree training/reload/inference and bundled CBC ran. One existing
  Starlette/httpx deprecation warning remains.
- Focused final API/Reflex/hybrid checks: **51 passed**, 8.03 s. Saved hybrid
  approval and creation recovery use a mocked read-only Odoo adapter for creation,
  then forbidden Odoo/model/solver dependencies during stored operations. One
  cache permission warning accompanied this passing run; final suites used a
  precreated cache directory and had no cache warning.
- Combined real PostgreSQL selection: **31 passed**, 35.38 s (V1, T15 and T17).
  Two requests genuinely wait on PostgreSQL advisory locks before release;
  identical intents return 201/200 and competing intents 201/409 with one row.
  Atomic rollback and direct immutable/base-only/unique-key enforcement passed.
- Ruff format (183 files), Ruff lint, compileall, pip check, Reflex production
  export, both Compose configs with `--quiet`, and patch whitespace passed.
  Export is compilation only; generated Reflex dependency-lock changes were
  restored to the clean starting versions, with no dependency update intended.
- Built-in browser -> real Reflex/FastAPI/PostgreSQL: minimum/alternative
  approval, mandatory reason, both No-award cases, stored reload, scenario
  restriction, desktop/mobile and uncertain-save recovery passed. The synthetic
  fixture yields EUR 102/109 plans. Mobile 390x844 showed no horizontal overflow.
  A test-only response wrapper returned 503 after successful commit; UI retained
  identical recovery JSON while FastAPI was subsequently stopped, and explicit
  retry after restart recovered the original timestamp/content hash with model
  configuration absent and acquisition/inference/solver sentinels enabled.
  Database evidence and screenshots were saved under ignored `.artifacts/t17/`.

Nonpassing attempts retained as limitations: sandbox TestClient stalled and was
interrupted before elevated execution; one focused invocation omitted its parent
temporary directory and produced setup errors, corrected before executing tests;
the initial concurrency observation reused PostgreSQL's cached statistics and
failed the waiter assertion, fixed with `pg_stat_clear_snapshot()` before the
passing contention checks. These attempts are not PASS evidence.

Runtime boundary: reused the existing Podman machine, with all existing Odoo and
helper/demo containers untouched/stopped. A separate
`procurement-decision-support-t17-acceptance` PostgreSQL container used VM 55434.
The Windows proxy failed; a created localhost-only SSH tunnel exposed host 55435.
Only this disposable database was reset. Acceptance servers, container and tunnel
were stopped/removed after verification; the initially stopped machine was
returned to stopped state. Local artifact evidence remains for inspection.

Limitation and next capability: this supplies local controlled FR-V2-09/10/11 and
AC-V2-11 evidence, plus AC-V2-10/V1 regression. Historical/synthetic inputs do not
establish current operational validity or production buyer authentication. PDF
render/download (issue #21 / AC-V2-12), the complete local hybrid demonstration
(#22 / AC-V2-13), user review and exact-new-SHA hosted CI remain open. GitHub
issues remain open. No Odoo/Drive writes, stage, commit, push, PR or merge were
performed. Next: render the immutable approved content without reacquisition or
approval mutation. Thesis relevance: chapters 3/4/5/6/7; later evaluation and
conclusions retain the synthetic/local scope limitation.

## 2026-10-10 — View and download the immutable approved PDF (#21)

Problem: an approved plan had an immutable content snapshot but no buyer-visible
document. Decision: render that exact content in the backend, store one PDF with
its approved-content reference/hash, and expose bounded authenticated retrieval
through the existing API-only Reflex workspace. This implements FR-V2-09/10/12
and supplies local AC-V2-12 evidence; #22/AC-V2-13 remains separate. The starting
branch was `feature/T17-implementation` at `294b312`, with #20 already committed.
The user's report that prior CI looked fine is not new-PDF CI evidence.

Implemented behavior: ReportLab 4.4.10 plus packaged DejaVu Sans produces paginated
allocations, exact money/currency and exposure, saved business terms, provenance,
human decision and audit identities. Synthetic/model/date and incomplete-comparison
limitations remain explicit. Migration `20261010_01` adds immutable binary PDF
artifacts linked to exact approved content. Advisory locking gives one artifact
under contention; rendering/storage failure preserves approval and leaves no
partial artifact. Stored retrieval does not reacquire Odoo data, load/train/infer
a model, optimize, render again or modify approval. No-award, unapproved bases
and scenario children have no approved-PDF action and are denied by the API.

Reflex retrieves and checks bounded MIME/identity/hash/bytes on its server. A
React-PDF 10.2.0 component displays these bytes with selectable text, fit-width,
zoom and keyboard scrolling, using a locally bundled worker. A native Blob link
saves the exact document; no browser token or document generation is introduced.
Frontend locks retain the viewer and current Reflex-generated requirements.
See [the closed dependency/storage spike](T17_PDF_SPIKE.md) and
[the PDF handoff](T17_PDF_HANDOFF.md) for decisions, artifacts and procedures.

Executed evidence:

- Required fast selection: **577 passed, 59 deselected**, 124.69 s. Actual CBC
  and ML runtime gates executed. One existing Starlette TestClient deprecation
  warning remains. Focused PDF/hybrid checks earlier passed **19 tests** (18.02 s).
- Real isolated PostgreSQL PDF acceptance: **5 passed**, 20.83 s. Genuinely
  contending requests wait before lock release, then one render/row serves both.
  Direct UPDATE/DELETE, wrong-content insertion, renderer failure, post-flush
  rollback and exact retry are tested. V1/T15/T17 PostgreSQL regressions:
  **31 passed**, 53.75 s.
- Ruff format (194 files), lint, compileall including `document_adapter`, pip
  check, both Compose configurations with `--quiet`, and patch whitespace passed.
  Built wheel contains the font and its upstream license.
- Production Reflex export passed after replacing a static React-PDF import
  with a client-effect import. Static import failed server prerendering; this
  failed attempt is not PASS evidence. Final focused PDF/frontend checks after
  that correction: **21 passed**, 18.43 s, with the same existing warning.
  Export is compilation evidence; the final browser view also rendered all five
  pages with stored retrieval and a forbidden renderer.
- Built-in browser -> real Reflex/FastAPI/PostgreSQL: minimum EUR 102 and
  alternative EUR 109 document views, actual desktop/mobile downloads, retained
  approval through renderer/backend failure, explicit same-content retry,
  forbidden-renderer cache retrieval, No-award/scenario restrictions, keyboard
  Page Down and 390x844 mobile zoom without outer overflow passed. Both actual
  downloaded files equal persisted bytes/SHA-256. Original case hashes and
  final-decision JSON remain identical. Evidence is ignored under `.artifacts/t21/`.
- All five standard and ten long/Unicode pages were rendered with Poppler and
  inspected for clipping, overlap, table wrapping, footers and pagination.
  Latin/Hungarian, Greek and Cyrillic content extracts correctly. Unsupported
  glyphs fail rendering rather than silently producing missing-glyph boxes.

Initial native iframe previews and scripted downloads failed browser acceptance;
the local display component/native download link replaced them. An initial
database invocation stalled before Windows tunnel recovery and was interrupted;
fresh connected runs provide the PostgreSQL PASS evidence. The final focused
selection was confirmed again because its earlier session output was unavailable.

Runtime cleanup: only a separate disposable
`procurement-decision-support-t21-acceptance` database was migrated/reset. Existing
Odoo and helper/demo containers stayed stopped and untouched. Windows forwarding
required a task-created localhost-only SSH tunnel (host 55435 -> VM 55434).
Acceptance servers, test container/network, verified tunnel and temporary browser
tab were stopped/removed; the initially stopped Podman machine is stopped again.
Synthetic downloaded PDFs and ignored evidence remain for review.

Limitations/user action: install declared dependencies and apply migration
`20261010_01` to the deliberately selected helper database before user validation;
no user application migration was performed. PDFs are controlled procurement-plan
records, not legally complete external Purchase Orders or calibrated real-world
supplier predictions. The two-MiB bound and bundled-font glyph coverage are
intentional. No fresh live-Odoo or hosted CI result is claimed. New hosted CI,
user review and #22/full AC-V2-13 remain open. GitHub issues stay open; no stage,
commit, push, PR, merge, Odoo UI/write, direct Odoo database access or Drive write
was performed. Thesis relevance: chapters 3/4/5/6/7; the next capability is the
reproducible controlled hybrid acquisition -> ML -> MILP -> stress -> base human
decision -> stored PDF demonstration.

## 2026-10-11 — Complete controlled procurement-to-approved-PDF flow (#22)

Problem: approval and PDF slices had independent evidence but no single repeatable
controlled acquisition-to-document acceptance. Decision: reuse the existing
read-only Odoo fixture, offline synthetic model, CBC, helper database and Reflex;
add a repository-local HTTP reproduction tool and a complete buyer walkthrough.
No product-layer, dependency, schema, model/solver or infrastructure correction
was necessary. Starting branch: `feature/T17-implementation`, clean at `cf20ada`.

Implemented behavior: `tools/t17_demo.py run` creates two original hybrid bases,
all five stress types and an infeasible demand case, records explicit alternative
approval and separately reasoned No-award, retrieves the matching PDF and verifies
stored retries. `reopen` verifies unchanged snapshots, decisions and document
bytes after restart. Exact payload/key is written before each POST; no token or
automatic retry is recorded. New tests use actual saved inference/CBC/rendering,
forbidden-call reopening, corrupted replay/PDF rejection and lost-response intent
retention. Integration path filters include the tool. See
[reproduction instructions](T17_FULL_FLOW_DEMO.md) and
[the dated acceptance handoff](T17_FULL_FLOW_HANDOFF.md).

Evidence:

- Final fast gate: **579 passed, 59 deselected**, 55.60 s; actual ML/CBC execute,
  one existing upstream TestClient warning. The first full selection passed in
  55.38 s with an additional Windows cache-permission warning. Following the
  distinct No-award-reason refinement, the final run used a precreated cache.
- Services: **57 passed, 2 skipped, 579 deselected**, 49.88 s. Real PostgreSQL
  concurrency/immutability/rollback, served API/Odoo health and authorized read-only
  T6/live contracts passed. Two dedicated T7-S projection gates were not enabled.
- Ruff format (196 files), lint, compileall including tools/document adapter,
  pip check, both quiet Compose configs and patch whitespace passed.
- Real browser -> Reflex/FastAPI -> read-only Odoo/saved ML/CBC/PostgreSQL:
  fresh USD 1,850/2,200 base, all five independently stored original-base scenarios,
  demand-500 infeasibility, supplier/audit provenance, reasoned alternative approval,
  separate No-award and scenario finalization restriction passed.
- Odoo stopped, model unconfigured and acquisition/inference/solver forbidden:
  saved base approval, stored reopening and exact approval/No-award retries passed.
  Forced renderer 503 retained approval; explicit retry generated its document.
  API-unavailable handling retained approval and removed stale download controls.
  Restart with renderer additionally forbidden still served the same five PDF pages.
- Actual browser download: **30,434 bytes**, equal persisted bytes/SHA-256
  `68e2851ccc2feb0467d82080bc472d37b9226cb8b3ea2f848c98c123f33cc5d3`.
  Original browser snapshots/decisions remain identical. Required PDF content was
  extracted; all five Poppler-rendered pages were inspected without clipping or
  overlap. A browser download tool took about 18 minutes to return; that delay
  is excluded from application/runtime measurements.
- Final HTTP exercise: **5.671 s**, excluding offline preparation/startup/browser
  actions and subsequent replay verification. All exact replays/PDF succeeded after
  model-unavailable restart with upstream/solver/renderer forbidden. Dataset bounds:
  240 generated observations, 160/80 train/held-out, 4,597 history and 1,200 outcome
  lines; explicit synthetic evidence, not observed Odoo history. Runtime/model/policy
  identities, request times, case IDs and artifact references are in the handoff.

Runtime/cleanup: used the existing initially stopped Podman machine and fixture
containers, plus separate `procurement-decision-support-t22-acceptance` helper
PostgreSQL. Only that disposable database was migrated/reset; demonstration records
were preserved before service resets. Windows forwarding required a task-created
localhost tunnel (55435 -> 55434 and 8069 -> 8069). Task servers, temporary browser
tab, helper container/network and tunnel were cleaned up; original Odoo containers
and machine returned to stopped state. The default preview JSON was restored from
its byte backup. Ignored evidence remains under `.artifacts/t22/`.

Limitation/review: controlled **AC-V2-13 is met locally**, with AC-V2-11/12 and
relevant V1/V2 regression retained. No new frontend compilation is claimed because
#22 changes no frontend/dependency; #21's export evidence remains historical.
Hosted CI for the unpublished changes, user review, merge/issue closure, T18
evaluation, observed-model validity and complete thesis acceptance remain separate.
No Odoo/UI write, direct Odoo database access, application-database reset/migration,
Drive edit, stage, commit, push, PR, merge or issue closure was performed. Stop
before Drive synchronization until the user's green light. Thesis relevance:
chapters 3/4/5/6/7; summarize T17 human decisions, immutable PDF and full-flow
evidence in Hungarian only after review, then plan the separate T18 evaluation.

## 2026-10-11 — Correct the Quality job's documentation formatting failure

The user published #22 as `06a3876` and supplied the failing Quality log. The job
stopped at `ruff format --check .`: CI's Ruff 0.17.0 checks Python examples in
Markdown, while the previous local Ruff 0.16.9 gate missed two blank lines around
the function in `T17_FULL_FLOW_DEMO.md`. Tests did not run in that failed job.

Reproduced the exact failure with isolated project-local Ruff 0.17.0, then applied
its two-line formatting correction. Matching-version whole-repository formatting
(198 files), lint and patch whitespace pass. The existing environment and project
dependencies are unchanged. No application code changed, so the previously passing
579 fast / 57 service tests were not repeated for this documentation-only fix.
README records the publication/correction state. The fix remains unstaged and
uncommitted; new hosted CI awaits user publication. Drive remains untouched until
the review boundary is cleared. No service, database, Odoo or GitHub mutation was
performed during this correction.

## 2026-10-11 — T17 issue evidence and confirmed T18 evaluation planning

The user merged T17 PR #24 and created `feature/T18-implementation` from main
`ed4be413b11dc469307fc1bb1ed4bd6c16c17b88`. GitHub readback confirms the merge;
exact post-merge Quality 38150351508 and Container/API 38150351451 are SUCCESS.
The user closed #19–#22. At their explicit request, updated the closed issue
bodies: #20's 14, #21's 12 and #22's eight acceptance items are checked, and #19
links its three completed slices. Each retains the specification/exclusions and
adds pinned handoffs, PR/CI evidence and limitations. Independent readback confirms
the exact bodies, all intended checkboxes and unchanged closed states.

Used the user-invoked grill-with-docs flow to investigate current evaluation
coverage and buyer friction. Two read-only fact investigations inspected existing
tests, code and historical screenshots; no new services, browser interaction or
tests were started. Existing negative/concurrency tests are substantial. Actual
gaps include repeated workload measurements, a consolidated AC/NFR/RQ assessment,
committed browser smoke and evidence about unfamiliar buyers. Source/visual
observations are not fresh browser defects or participant measurements.

The user confirmed all nine planning answers. [T18 plan](T18_EVALUATION_PLAN.md)
records the current controlled hybrid, 3/5/10-supplier and 1/3-epsilon workloads,
two warmups/30 measured attempts and operation-specific local p95 targets;
local-first Chromium smoke with optional pytest-playwright dependencies; existing
coverage reuse; agent/user walkthroughs; and fixes for evidenced blockers.
Unfamiliar-participant usability remains NOT ASSESSED. Substantial UX/UI
improvement and affected reassessment follow before final acceptance and thesis
closure; T18 is not treated as the final development increment. The confirmed
plan preserves accepted FR/AC/ADR meanings and read-only/API-only boundaries.

README/index now expose the actual merged status and plan. Earlier handoffs and
logs retain their dated evidence. No new glossary concept or substantive ADR was
needed. Specification/ticket synthesis and granularity review are next; no new
ticket, application implementation, dependency install, Drive edit, stage,
commit, push or merge was performed in this planning session. Planning quality
checks are recorded in the chat handoff; prior application-test evidence is not
presented as a new run.

## 2026-10-11 — Publish the confirmed T18 evaluation specification

The user explicitly invoked to-spec after confirming Q9. Refreshed the canonical
requirements, status, roadmap, ADR and research-question records; their pre-merge
publication wording remains historical and is reconciled with the T17 merged
baseline and confirmed later UX/UI stage. No accepted FR/AC/NFR/RQ meaning,
domain vocabulary, ADR or technology baseline changed.

[Specification #25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25)
is open with `ready-for-agent`; [repository copy](T18_EVALUATION_SPEC.md) contains
30 user stories, the agreed measurement and local-browser contracts, reused
HTTP/real-PostgreSQL/browser test boundaries and seven completion criteria.
Independent GitHub readback confirms the exact published body, state and label.
Unfamiliar-participant usability remains NOT ASSESSED; substantial UX/UI work
and reassessment precede final acceptance. Failed targets cannot become PASS
merely because a report exists.

README/index/plan now link the specification. Delivery-ticket granularity and
dependencies still need review before child publication. This stage changes
engineering documents only; no application code, dependencies, services, Drive
content, stage, commit, push or merge changed. Ruff 0.17.0 whole-repository
formatting (200 files) and lint pass, as do patch whitespace and local document
link/specification-structure checks. Application/service/browser tests were not
rerun for this documentation-only stage; historical runtime evidence stays dated.

## 2026-10-11 — Draft bounded T18 delivery tickets for review

The user invoked to-tickets. Read back the complete live specification #25 and
open issue list; #25 is the sole open issue, and its state/body were not changed.
[Draft breakdown](T18_TICKET_BREAKDOWN.md) proposes five independently verifiable
slices: a complete 3-supplier/1-epsilon HTTP measurement flow; extension to the
full workload/stress matrix and separate live validation; real-stack local
Chromium smoke; buyer-task/keyboard/mobile/recovery assessment with bounded
blocker fixes; and consolidated AC/NFR/RQ conclusions with a UX/UI follow-up.

Only the expanded measurements depend on the first measurement slice. Browser
smoke and manual assessment can start from the implemented workflow. The final
report depends on the three evidence-producing branches; measurement slice 1 is
a transitive blocker through slice 2. No preparatory refactor is justified.
The earlier four-area plan remains the scope; five tickets refine delivery size.
No specific code paths, speculative API/schema changes or general cleanup scope
are introduced in the child descriptions.

The skill requires user review of granularity and blocking edges before issue
publication, so no child issues have been created. Native sub-issue/dependency
mutation is not exposed by current connector metadata; if still unavailable at
publication, child bodies will record parent/blocker links. The skill explicitly
prohibits changing the parent, so no parent task list is added by this workflow.
README/index/plan expose the review draft. No implementation, dependency install,
runtime service, Drive write, stage, commit, push, merge or issue closure occurred.
Ruff 0.17.0 formatting (201 files), lint, patch whitespace and local draft-link/
structure checks pass. Application/service/browser gates were not rerun for
this documentation-only proposal; the ticket outcomes remain planned.

## 2026-10-11 — Publish approved T18 delivery tickets

The user approved all five proposed slices and dependencies. Published open
`ready-for-agent` children #26–#30 of specification #25 in dependency order.
#27 is blocked by #26; #30 is blocked by #27/#28/#29. #26, #28 and #29 can start
independently, with #26 recommended first. Each ticket has a complete behavior,
bounded acceptance criteria, canonical traceability and inherited safety/scope
boundaries; no implementation-only horizontal or speculative refactor ticket
was introduced.

Independent GitHub readback verifies exact bodies/titles, open states, labels,
parent references and blocker links. Relationships are explicit body links,
because native mutation is not exposed by the available connector. The parent
#25 body/state remain unchanged, as required by to-tickets. No issue was closed.
[Published breakdown](T18_TICKET_BREAKDOWN.md), plan, specification header,
README and index now show the executable order and actual publication state.
The earlier draft entry records the pre-approval moment, not a current blocker.

No T18 implementation, runtime measurement, participant result, dependency
installation, service startup, Drive write, stage, commit, push or merge is
claimed. Next capability: a complete repeatable three-supplier HTTP evaluation
through saved approval/PDF with raw timing/outcome evidence. Substantial UX/UI
improvement and affected reassessment remain later development; unfamiliar-user
usability stays NOT ASSESSED until real participant evidence exists.

Final documentation verification: Ruff 0.17.0 formatting passes (201 files);
lint passed for this documentation-only stage. Patch whitespace, published
ticket/local links and structure pass; the repository specification body still
matches unchanged parent #25 exactly. Application/service/browser tests were
not rerun, and no new runtime acceptance is claimed.

## 2026-10-11 — Implement #26's repeated three-supplier HTTP evaluation

The user authorized #26 on `feature/T18-implementation`, starting from published
planning HEAD `7536a54`. Added one bounded CLI reusing T15 offline synthetic
preparation and existing HTTP/core/PDF contracts, plus seven meaningful accounting,
failure, artifact-preservation and actual saved inference/CBC/API/PDF tests.
No production endpoint, schema, business policy, frontend or dependency changed.

The evaluator atomically retains exact POST intent before requests, distinguishes
failed/pending/unattempted observations and stops ambiguous writes without retry.
It measures seven operations separately, validates saved allocations/approval
and PDF identity, excludes validation/report IO from HTTP time and records model,
dataset/input/policy, solver/runtime, git/dirty-state and evaluator-source hashes.
The first full development run passed but duplicated large response snapshots;
compact identity/result reporting reduced checkpoint overhead. That first report
is retained as history; the subsequent final-source run is authoritative.

The existing Podman machine was stopped. Started it and only a fresh disposable
helper project `procurement-t18-26-b7580128`, using PostgreSQL 16.15; Windows
forwarding failed, so used a task-owned localhost SSH tunnel. Migrated that
database only to `20261010_01` and served FastAPI on unused port 8002 with the
matching offline model. Both warm-ups and all 210 measured operations passed;
p95 seconds were create 0.571495, outage 0.602628, approval 0.258946, GET 0.142419,
exact replay 0.281872, first PDF 0.244752 and cached PDF 0.172571. All agreed
local targets passed for this 3-supplier/1-epsilon synthetic workload.

Database readback found 128 base/child cases, 64 approvals and 64 artifacts across
the two 32-flow executions, consistent with exact replay and cached downloads.
[Raw timing/identity evidence](T18_26_EVALUATION.json),
[initial canonical inventory](T18_EVIDENCE_MATRIX.md),
[runbook](T18_26_EVALUATION_RUNBOOK.md) and [handoff](T18_26_HANDOFF.md) separate
new measurement from retained component/live/browser evidence. README/index and
planning headers now reflect the executed scope; original tracker bodies remain.

Initial focused setup errors came from an absent parent temp directory, followed
by a sandboxed Windows asyncio socket-pair stall before API startup. Fresh temp
directories and permitted execution outside the socket sandbox resolved them;
the focused five-test run passed. An earlier 584-pass fast run predates the final
compact/failure changes; final checks and service cleanup are recorded at handoff.
No Odoo read/write/UI mutation, application-database reset, Drive edit, GitHub
issue mutation, stage, commit, push, PR or merge was performed. #27's larger
matrix/live validation, #28 browser smoke, #29 usability and #30 final assessment
remain separate. Unfamiliar-participant usability is NOT ASSESSED; modern UX/UI
work and reassessment still precede final thesis acceptance.

Final checks: 586 fast tests passed, 59 service/browser cases deselected; all seven
new cases included. Ruff 0.17.0 formatting (206 files)/lint, compileall, pip check,
both credential-safe Compose config validations, whitespace/local links and raw
observation/summary/source-hash reproduction pass. No new hosted or browser/live
Odoo result is claimed. Task-owned API/tunnel and disposable Compose database were
stopped/removed; generated secret files deleted. No other containers were running,
so the Podman machine returned to its initially stopped state. #26's local scope
is complete; implementation changes remain unstaged/uncommitted for user review.

## 2026-10-11 — Supported workload/stress and separate live evaluation (#27)

Problem: repeated #26 evidence covered only three suppliers/one epsilon and
outage. Decision: extend the existing offline helper/HTTP evaluator to all six
supported sizes, five stress types and controlled infeasibility; reuse production
rules/contracts and the fixed live demo. Behavior: every epsilon/run reference,
exact allocation/cost/premium/exposure, original-base link, saved delta/provenance
and changed-demand comparison is validated. No new API, schema, dependency or
frontend behavior was introduced. Default T15 preparation remains compatible.

Evidence: all 2,160 measured and 144 warm-up operations succeeded; all 72 fixed
p95 gates passed. Highest p95 2.791729 s (10/3 price increase, target 5 s).
[Raw/summary export](T18_27_EVALUATION.json) retains observations, templates,
hashes and environment; [handoff](T18_27_HANDOFF.md) interprets them and links the
[runbook](T18_27_EVALUATION_RUNBOOK.md). The earlier #26 report remains historical.
The separate [live record](T18_27_LIVE_VALIDATION.json) reproduces fixed read-only
Odoo quotations plus synthetic ML, all stress types, alternative approval/PDF,
separate No-award and stored-only reopening with Odoo stopped/model unset.
Readback matched 1,352 evaluation cases/194 decisions/193 documents exactly;
three earlier integration-fixture cases and one decision/document are separated.

Verification: 591 fast tests/59 deselected; actual CBC/ML and independent T13
oracle executed. Ruff 0.17.0 formatting/lint, compileall, pip check, both safe
Compose config checks, whitespace, export/source identity and document links
passed. The existing Starlette TestClient deprecation remains. Real PostgreSQL
contracts passed 36 checks and primary live Odoo 18. The two previously disabled
T7-S/T8 gates were executed and failed HTTP 401 for the dedicated key: **current
history/security validation remains BLOCKED**, with earlier bounded-history
acceptance retained and no observed-model promotion or broader permissions.
The user was asked to renew only the existing dedicated key; no key, Odoo UI,
role, fixture or owner `.env` mutation was performed by the agent.

Limitations: deterministic fixture, warmed sequential HTTP, fixed execution order
and accumulating database; not arbitrary scaling, concurrent SLA, cold startup,
observed prediction/calibration or real business savings. Browser/participant
gates are separate; novice usability NOT ASSESSED. Initial focused source-type,
Compose-provider and local guard/report-path errors were corrected before their
dependent evidence; no hidden workflow retry or target relaxation occurred.
Owned runtime/secret cleanup restored initially stopped Odoo/Podman and preserved
owner artifacts/volumes. Changes remain uncommitted; no Drive/issue/PR/publication
mutation. Next: independent #28 browser smoke/recovery, then #29/#30 and later
substantial UX/UI reassessment. Chapter 7 owns measurements/limits; chapters
3/4/6 and conclusions use only the supported integration and traceability results.


## 2026-10-11 — #27 history/security credential gate resolved

Problem: the initial service run's two dedicated T7-S/T8 checks failed HTTP 401.
The user renewed the existing dedicated key in ignored local `.env`. Decision:
rerun only those two affected read-only contracts with process-local opt-in flags;
retain the original failure and all already passing measurements/tests.

Evidence: **2 passed in 2.21 s, no failures/skips**, using Python 3.11.16 and the
existing Odoo loopback listener on 8069. Bounded method-only projection, denied
generic CRUD/direct stock/cross-company access and invalid bounds passed. The
production history/KPI slice verified 33.33% adherence, sample 3, controlled
backorder relationships and supplier-return exclusion. The [live evidence](T18_27_LIVE_VALIDATION.json)
binds the rerun log/XML/source hashes separately from the original 54-pass/2-fail
run. [#27's handoff](T18_27_HANDOFF.md) now records all scoped local gates complete.

Limitations: no observed-model promotion or new supplier-promise semantics; keys
remain short-lived operational prerequisites. No code, .env, Odoo UI, ACL, fixture
or database mutation was performed by the agent. The user's already running
Podman/Odoo/listener were preserved; no helper process/service needed cleanup.
Previously passing quality/matrix/database checks were not repeated after this
credential-only change. Hosted CI, browser and novice usability remain separate.
No commit, publication, issue closure or Drive update. Chapter 7 gains fresh
controlled history/security evidence; next capability remains #28 browser smoke.


## 2026-10-11 — #28 real buyer-flow browser smoke and backend recovery

Problem: compiled Reflex and backend tests do not prove a buyer can complete the
real browser workflow or recover when Reflex's server-side API client loses its
backend. Decision: one optional local Chromium smoke with owned services and a
unique disposable helper database; reuse production modules and existing offline
synthetic preparation/Compose/migrations. Behavior: UI cost/supplier quantities
match saved results; explicit alternative approval preserves the original; browser
reload/reopening with no configured model renders/downloads the byte-identical
approved PDF. Actual owned FastAPI downtime gives GET and unconfirmed-create
errors; explicit recovery preserves exact intent/key and produces a stored
idempotent replay. No production API/UI/core/schema/CI changes.

Evidence: final full Chromium run **1 passed in 82.10 s**, including setup/teardown.
Earlier full PASS 81.73 s retained separately. Three development assertion failures
(envelope level, approve/Approved, unconfirmed/uncertain) remain recorded; no
application defect or automatic workflow retry was concealed. Final cleanup
refinement reuses owned process-tree handling for command timeouts; a real Windows
parent/child timeout probe and the final full E2E run passed. Plugin-disabled fast
collection selected 591/651 tests; selected E2E without plugin or browser binaries
failed clearly before service startup. [Handoff](T18_28_HANDOFF.md),
[runbook](T18_28_BROWSER_RUNBOOK.md) and [small evidence record](T18_28_BROWSER_EVIDENCE.json)
bind tested source/copy/PDF/log/trace hashes. Large screenshots/traces/service logs
remain ignored local artifacts; prior #27 evidence is preserved.

Required fast gates: **591 passed, 60 deselected**, actual ML/CBC and independent
T13 oracle; Ruff 0.17.0 formatting (211 files)/lint, compileall, pip check, both
credential-suppressed Compose configs and whitespace passed. One existing Starlette
TestClient deprecation remains. Those gates preceded the final E2E-only timeout
refinement; focused Ruff/compile, probe and full E2E passed afterwards, with fast
code/selection unchanged. No redundant fast-suite rerun. Owned database/projects
and API/Reflex/tunnel processes were removed; owner Podman/Odoo/8069 and saved
application data remain unchanged. Trace generated-secret scan and owner-secret
artifact checks passed; no generated credential file was written.

Limits: one controlled desktop Chromium flow, synthetic model, technical actor
text; no new live Odoo acquisition, hosted/Ubuntu browser, mobile/keyboard/visual
or accessibility acceptance, No-award/scenario browser test or lost-after-commit
browser claim. Novice usability NOT ASSESSED. Forced pytest termination can prevent
teardown; fresh frontend dependencies require registry access and remain local
until manually removed. User controls review/publication; no Drive/issue mutation,
commit/push/PR/merge. Next: #29 buyer-task/keyboard/mobile walkthrough and blockers,
then #30 synthesis and later substantial UX/UI reassessment. Chapter 7 gains
reproducible functional browser/recovery evidence; chapters 4/6 explain the saved
result/document and server-side credential boundary.

## 2026-10-11 — #29 buyer-task assessment and bounded feedback fixes

**Problem → decision → behavior:** The user authorized #29 on
`feature/T18-implementation`, clean at committed #28 `b3cf8f3`. Functional smoke
does not establish first-time-buyer usability. Assess real owned Reflex/FastAPI/
disposable PostgreSQL through the built-in browser; retain only bounded evidenced
fixes. PDF errors lacked alert semantics; save/PDF-ready feedback lacked status
semantics. Add those roles in the shared saved-decision component/page notice,
and extend the existing smoke with genuine API downtime before PDF viewing,
preserved approval, no false download and explicit stored-only recovery.

**Evidence:** [Assessment/run sheet](T18_29_BUYER_ASSESSMENT.md) and
[small artifact/source record](T18_29_BUYER_EVIDENCE.json) record informed-agent
creation/comparison, exact EUR 102/109 allocations/exposure, all five disruptions,
infeasible demand 1000, original-base return, alternative reason validation,
separate keyboard No-award/reopen, narrow 390/320-pixel audit/PDF tasks and genuine
GET/uncertain-create/PDF fault recovery. Original snapshot stayed unchanged;
pending create payload/key stayed identical. Keyboard focus, table horizontal
scroll and PDF 200% viewer zoom were exercised; successful save/PDF readiness and
failure roles were rechecked after the fix. Raw screenshots/DOM/PDF/case records
remain ignored locally; selected hashes are committed-document candidates.

Final extended Chromium smoke passed **1 test in 87.51 s**, including byte/hash-
identical actual PDF download and owned teardown. Required fast gates passed
**591 tests, 60 deselected in 104.56 s**, actual CBC/ML; Ruff 0.17 format (212
files)/lint, compileall, pip check, credential-suppressed Odoo/persistence Compose
configurations and whitespace checks passed. Existing Starlette warning remains.
The first fast attempt's 408 passes/183 setup errors (inaccessible Windows default
pytest temp) remain recorded; a full fresh workspace-local-temp rerun passed.
No dependency/CI/runtime baseline change. Both owned projects/process trees and
HTTP listeners were removed; owner Odoo/data/8069 listener and running machine
were preserved; browser viewport reset and temporary tab closed.

**Limits → chapter relevance → next:** Task clocks are agent/tool wall time, not
human usability times or API latency. Owner sessions PENDING; 3–5 unfamiliar
participants PENDING and novice usability NOT ASSESSED. In-app browser zoom
shortcuts had no effect; actual 200% browser text zoom NOT VERIFIED. Screen-reader
speech, formal accessibility, physical mobile, other engines/hosted browser and
new-SHA CI are unverified. Odoo was not read or changed; #27 live evidence remains
separate, synthetic ML stays synthetic. The report ranks entry/retrieval,
hierarchy, final-choice context, focus continuity, infeasible comparisons,
recovery, PDF navigation and buyer copy for substantial later UX/UI development.
Chapter 7 gains bounded task/fault/findings evidence; chapters 4/6 explain the
feedback/document boundary. #30 synthesis is next, retaining pending gates;
modern UX/UI and reassessment follow before final acceptance/thesis closure.
No commit/push/PR/merge, issue mutation or Drive edit; publication stays with user.

## 2026-10-11 — #30 consolidated controlled acceptance and UX/UI follow-up

**Problem → decision → delivered behavior:** The user authorized #30 after
publishing #29 and reporting green CI. Entry branch was clean at
`65acfbe9bf31d89f6ed5e3c94812ecf65a82764b`. Refresh canonical requirements/RQs
read-only and consolidate the dated evidence; add no runtime subsystem or broad
rerun. [Controlled assessment](T18_CONTROLLED_ASSESSMENT.md) maps every
FR-V2-01–12 / AC-V2-01–13 / NFR-V2-01–08, answers RQ-V2-01–07 and prioritizes
the next buyer-visible UX/UI work. Scoped controlled functional outcomes pass;
novice usability and final product/thesis acceptance do not follow from that.

**Evidence:** [Small reconciliation/gate record](T18_30_CONSOLIDATION_EVIDENCE.json)
binds refreshed Drive source reads, reports and current revision. All six original
#27 raw-report hashes, 2,304 exported timing/outcome observations, full-value
template identities, medians/maxima/p95 and 72 unchanged targets independently
reconciled. There are 2,160 measured successes and 144 warm-up successes, no
failed/pending/missing timings or partial solver proof. Slowest p95 is 2.791729 s
(10 suppliers/3 epsilons price increase), target 5 s. Hardware, sequential order,
warm-state/excluded work and separate live/browser/agent timings remain explicit.
The two initial T7-S/T8 401 failures and successful post-renewal two-test rerun,
prior test-setup/automation failures and existing warning remain historical evidence.

Current evaluator/helper/live-tool hashes and #29 post-fix source/artifact hashes
match recorded execution. Only the two frontend feedback-role files changed in
production since #27; HTTP/model/solver/storage/PDF behavior is unchanged. #29's
affected tasks and 87.51 s real-stack smoke are retained; no new local
service/live/browser/timing run was justified or started. Exact #29-SHA hosted
Quality run 38172043161/job 114566515649 and Container/API run 38172043167/job
114566485440 succeeded; connector job/step metadata confirms integration execution
and frontend compilation, not hosted browser or every optional live fixture.

New required local gates passed: **591 fast tests, 60 deselected in 103.93 s**,
actual CBC/ML; Ruff 0.17 format (213 files)/lint, compileall, pip check, both
credential-suppressed Compose configs and whitespace. Fresh workspace-local temp
avoided the earlier Windows pytest temp problem. Source/report/link/matrix
reconciliation checks verify this documentation-only increment; unchanged gates
were not repeated after passing. No new dependency, CI, migration or production
code; no owner/Odoo/data/service change.

**Limits → chapter relevance → handoff:** Owner walkthrough PENDING; unfamiliar
3–5 participants PENDING and novice usability NOT ASSESSED; actual browser text
zoom NOT VERIFIED; screen-reader output NOT ASSESSED. Focus loss/infeasible base
visibility and broader navigation/hierarchy/choice/recovery/document friction
remain ranked follow-up findings. Plan substantial modern buyer-focused UX/UI
development and reassess before final acceptance; preserve T19 thesis closure
after necessary development. Chapter 7 owns canonical assessment/measurements/
RQ answers; chapters 3/4/5/6 and conclusions use only supported scoped findings.
Drive's retained pre-merge T17/future-T18 status was explicitly reconciled, not
edited. Report is delivered for review; no commit/push/PR/merge, GitHub issue or
parent #25 mutation/closure, or Hungarian Drive edit. Publication remains user-controlled.

## 2026-10-12 — Approved buyer workspace specification and ticket publication

**Problem → decision:** T18's controlled workflow evidence does not establish an
understandable first-time buyer experience. The user confirmed Decision editorial,
a bounded saved-case library, curated Practice without reset, guided creation,
aligned comparison, deliberate approval, recovery/document access and reassessment.
Ten complete buyer slices refine the six specification areas without changing the
accepted baseline. The user approved all sizes/dependencies, a new parent and the
prospective library/usability gates before publication.

**Published behavior → evidence:** [Specification #42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42)
links delivery #32–#41; the [ticket index](UX_UI_TICKET_BREAKDOWN.md) records their
actual blockers. Readback verified all eleven exact bodies, titles, open states and
`ready-for-agent` labels, parent links and 48 unchecked delivery criteria. Explicit
Markdown relationships are used because native sub-issue/dependency tools are
unavailable. Only #32 is initially unblocked. Two temporary automatic-review rate
limits resolved through the same approval process; existing issues were untouched.

**Acceptance → limitation:** Library: 1,000 disposable bases plus children, two
warm-ups/30 measurements per selected 20-row query, local p95 ≤1s. Buyer tasks:
3–5 unfamiliar participants, ≥80% independent completion per essential task
(round successes up), zero unintended finalizations or unresolved critical source/
decision misunderstandings. These are future scoped gates, not measured results.
Missing participants remain NOT ASSESSED. Planning/document readback is not
implementation or buyer acceptance; no runtime services or application tests were
started for publication. No commit/push/merge, Drive write or existing-parent change.

**Chapter relevance → next:** Chapters 4/6 use the design/integration decisions;
chapter 7 needs actual task/query/browser evidence. Preserve read-only Odoo,
synthetic-model limitations, immutable stored decisions/PDF and T19 closure after
development/reassessment. Next capability is #32's saved-case library.

## 2026-10-12 — Find and reopen saved cases (#32)

**Problem → decision:** Returning buyers needed UUIDs to reopen saved work, while
test history had no purpose classification. Implement the first complete task of
parent #42 with bounded company-owned library queries and a working Reflex entry.
Reuse stored validation and existing API/repository seams; keep all legacy cases
unclassified instead of deriving Practice from synthetic model evidence.

**Implemented behavior:** `/cases` filters/pages original summaries, lazily expands
stored scenarios and opens bookmarkable saved results. Backend collections require
the service token and explicit `PLANNING_LIBRARY_COMPANY_ID`; unknown parameters,
bad/mismatched cursors and unsupported/corrupt saved data fail explicitly. Migration
`20261012_01` adds an empty immutable original-base catalog and workspace index.
Hashes, creation/replay, V1 records, approved content/PDF and read-only Odoo boundaries
remain unchanged. Pending navigation preserves the original route/key/payload and
explicit recovery. [Runbook](UX32_LIBRARY_RUNBOOK.md) owns configuration, migration,
commands, disposable benchmark and cleanup; [handoff](UX32_LIBRARY_HANDOFF.md) owns
the full dated evidence and failed-attempt record.

**Evidence:** 605 fast tests passed; final guard/recovery-focused checks passed 20.
32 real PostgreSQL integration checks passed, covering old migration/readability,
immutable V2 data and catalog constraints/joins. New library browser acceptance and
existing approval/PDF/recovery browser regression passed; the latter's final extension
verified blocked pending navigation and exact retry in a real browser. Library
find → expand → keyboard reopen/reload, 768/390/320 reflow, corruption and genuine
backend downtime/recovery passed with model/Odoo configuration cleared for stored
reads. Built-in browser visual inspection and the mechanical detector completed.
Format/lint/compileall/pip/Compose configuration passed. Owned test stacks/tunnels
were removed; no owner/Odoo database reset or application migration occurred.

**Measured gate → limitation:** The owned fixture contains 1,000 company bases and
60 children, plus cross-company and concurrent-insertion checks. Six 20-row queries,
two warm-ups and 30 observations each, passed local p95 ≤1 second (0.170–0.244s).
[Raw timings/query plans](UX32_LIBRARY_MEASUREMENTS.json) preserve all 192 observations.
No additional snapshot indexes were justified. This is a bounded PoC result, not a
production SLA or new business/ML evidence. Failed setup/compatibility/form/collection
attempts remain recorded alongside final PASS. Owner/novice usability, text zoom,
screen-reader speech, physical phones and hosted new-SHA CI remain unverified.

**Traceability → next:** UX-AC-01/03, FR/AC-V2-09/10, NFR-V2-04/05/06/07/08 and UX29-03;
chapters 4/6 explain architecture/UI choices, chapter 7 uses scoped verification.
Changes remain uncommitted; user controls commit/push/merge and owner migration.
Drive and GitHub issues were not edited. #33's explicit creation classification and
curated Practice is next; #34–#41 and final buyer/thesis acceptance remain open.

## 2026-10-12 — Curated Practice and explicit classification (#33)

**Problem → decision:** Synthetic evidence does not identify a saved case's purpose,
and a buyer needed deliberate exercises. Reuse #32's catalog storage and existing
prepared synthetic/scenario APIs; add presentation context outside hashed planning
facts and a labelled `/practice` entry. Preserve all accepted architecture/source
boundaries and old omitted-context intent fingerprints.

**Behavior:** Compare/outage/infeasibility selection fills a fresh draft without
saving. Explicit actions save genuine new bases/scenarios; finalized examples are
never silently reused as editable work. New synthetic UI saves use Practice, prepared
Odoo UI saves use controlled work, and legacy callers remain unclassified. Context
validation follows the server path; case/catalog commit atomically. Exact replay
writes no metadata, changed context/key conflicts, and children inherit the original.
Workspace/source remain separate in case/history/decision/document access, without
rewriting snapshots, approved content or PDF bytes. Pending requests keep exact
context/payload/key and explicit recovery. No new migration or dependency.

**Evidence:** 617 fast tests passed; affected recovery/frontend/API checks passed 59.
36 real PostgreSQL integration checks covered rollback/commit ambiguity/concurrency,
replay/conflict/inheritance and old V1/hash compatibility. The new real Practice
browser flow and existing approval/PDF/navigation regression passed separately;
entry selections wrote nothing, actual outage/infeasibility and model-unconfigured
library reopening/PDF download succeeded, and classified pending retry stayed exact.
Entry screenshots/reflow checks covered 1280/1440/768/390/320, with built-in-browser
desktop/focus/reflow/contrast inspection. Format/lint/compileall/pip/Compose gates
passed; owned test/preview services were removed. Failed assertions/setup/preview
attempts and Windows cache warnings remain in the [dated handoff](UX33_PRACTICE_HANDOFF.md).
[Runbook](UX33_PRACTICE_RUNBOOK.md) owns preparation/configuration/run/cleanup.

**Limitation → traceability → next:** Odoo path validation used controlled mocked
HTTP; fresh live Odoo, hosted CI, owner/novice/zoom/speech/physical-phone gates remain
unverified. Practice persists without isolation/reset or operational-validity claims.
No owner/Odoo database migration/reset, Drive update, commit/push/merge or issue edit.
UX-AC-02/03/05, FR/AC-V2-09/10, NFR-V2-05/06/07 and UX29-03/10 support chapters 4/6/7.
Next is #34's responsive workspace/navigation; broader UX and final acceptance remain open.


## 2026-10-12 — Responsive workspace and safe navigation (#34)

**Problem -> decision:** Buyers needed consistent destinations and case context,
and explicit navigation could lose unsaved creation/scenario drafts. Apply the
approved Decision editorial shell through existing frontend modules and put the
navigation guard in the existing HTTP-only planning state. Preserve the accepted
architecture, immutable contracts and legacy entries.

**Behavior:** Cases/Open RFQs/Practice share rail/drawer navigation. Saved product,
demand/unit/currency, source/dates, lineage and status lead the cockpit; case views
are bookmarkable. Stay retains a draft; Discard clears it before the requested
navigation and focuses the destination. Pending writes have no Discard, retain
exact request/key and return to the original recovery route. Exact tables keep
named keyboard scroll regions; drawer/reduced-motion cleanup and RFQ error roles
are verified. No backend, migration, dependency or Odoo mutation was added.

**Evidence:** 622 fast tests passed; affected 69 and final UI/RFQ 47 passed after
relevant corrections. Workspace, curated Practice and existing approval/PDF browser
flows passed separately against real disposable helper storage/API/Reflex. Scoped
keyboard, 1280/1440/768/390/320 reflow, drawer/dialog focus, reduced motion and actual
200% native Chromium zoom passed. Built-in-browser inspection confirmed the final
320 drawer geometry/focus. Required format/lint/compile/dependency/Compose checks
passed; owned stacks cleaned up. The [handoff](UX34_WORKSPACE_HANDOFF.md) preserves
failed runs, exact scope and limits; the [runbook](UX34_WORKSPACE_RUNBOOK.md) owns
execution and cleanup.

**Limitation -> chapter relevance -> next:** Hosted/live Odoo, speech, physical
phone and owner/novice gates remain unverified; session-local recovery is not a
closed-session outbox. UX-AC-04/06/13/15, FR/AC-V2-09/10, NFR-V2-05/06/07 and
UX29-03/04/06/08/10 support chapters 4/6/7. User controls commit/push/merge; Drive and
issues remain untouched. Next are attributed input review (#35), aligned comparison
(#36) or explanation (#39); final buyer acceptance and thesis closure remain open.

## 2026-10-12 — Review attributed inputs before saving (#35)

**Problem -> decision:** Immediate calculation made captured quotation facts,
explicit business terms and policy harder to review together. Reuse the existing
prepared requests and HTTP state for validate -> read-only review -> deliberate
save. Freeze reviewed intent; preserve accepted architecture and immutable contracts.

**Behavior:** Demo, curated Practice and prepared Odoo show exact context, supplier
terms/ranges/availability and policy. Review saves/solves nothing; Edit retains
values and invalidates review. Labelled inline errors focus the first invalid field;
review/saved headings receive purposeful focus and exact tables support keyboard
scrolling. Odoo preview stays captured/local until FastAPI rereads quotations on
save; ML history stays synthetic. Genuine saved classification and exact pending
payload/key/retry remain intact. No backend, migration or dependency change.

**Evidence:** Required 632 fast tests passed; final affected 42 passed after focus
and feedback corrections. New synthetic/controlled creation, existing Practice,
approval/PDF recovery and workspace browser flows passed in separately identified
runs against real HTTP/model/CBC/disposable helper PostgreSQL. Controlled quotation
transport is mocked, not live ERP evidence. Built-in-browser invalid-field/review
focus, desktop and 320-pixel keyboard table access passed. Static/runtime gates
passed; all owned stacks cleaned up. [Handoff](UX35_CREATION_HANDOFF.md) retains
failed runs, actual scope and limits; [runbook](UX35_CREATION_RUNBOOK.md) owns commands.

**Limitation -> chapter relevance -> next:** Fresh live Odoo, hosted CI, speech,
physical phones and owner/novice gates remain unverified. Practice shares storage;
session-local review/recovery does not establish closed-session durability. UX-AC-07,
FR/AC-V2-01/09, NFR-V2-05/07 and UX29-04/06/10 support chapters 4/6/7. User controls
commit/push/merge; Drive/issues remain untouched. Next is #36 aligned saved allocation
comparison and explicit selection; reassessment and thesis closure remain separate.

## 2026-10-12 — Compare and explicitly select saved allocations (#36)

**Problem -> decision:** Independent cards and a distant label-only selector made
allocation comparison and the contemplated decision harder to follow. Use aligned
saved-plan columns/supplier rows, labelled narrow sections and an exact in-flow
review strip through the existing HTTP-only frontend mapping/selection state.

**Behavior:** Costs, absolute/exact relative premium, zero/nonzero quantities,
promised dates, exact exposure and saved explanations align across plans. Selection
is explicit, semantically pressed and performs no write. Review mirrors the exact
saved plan/context across views and focuses the existing finalization form; original
reason/acknowledgement/No-award and immutable approval/PDF remain functional. The
chart stays subordinate with an exact table. Single/infeasible/incomplete outcomes
remain honest; bad allocation joins/totals fail mapping and tiny decimal cost
differences retain precision. No backend, solver/model, migration or dependency change.

**Evidence:** Required 646 fast tests passed; final affected 69 passed after
component/focus corrections. Real saved 3/5/10-supplier comparisons, variable
alternatives, long non-Latin identity, read-only selection across views, keyboard
review, five viewport widths and native 200% zoom passed. Genuine infeasibility and
separate No-award passed; existing alternative approval/immutable snapshot/PDF and
real outage/exact retry regression passed, as did curated Practice. Built-in-browser
desktop/320 inspection confirmed selected-state grammar and unobscured focus.
Static/runtime/Compose gates passed and owned stacks cleaned up. [Handoff](UX36_COMPARISON_HANDOFF.md)
retains failures and scope; [runbook](UX36_COMPARISON_RUNBOOK.md) owns execution/cleanup.

**Limitation -> chapter relevance -> next:** Live Odoo, hosted CI, speech, physical
phones and owner/novice sessions remain unverified. Draft selection/recovery stays
session-local; Practice shares storage. Incomplete solver states are mapping fixtures,
distinct from actual CBC saves; palette/DOM checks are not whole-app WCAG acceptance.
UX-AC-08/09, FR-V2-06/07/09, AC-V2-05/07/09, NFR-V2-07 and UX29-04/05/10 support
chapters 4/6/7. User controls commit/push/merge; Drive/issues remain untouched.
Next is #37 original-base disruption comparison, followed by #38 final review;
#39 explanation and later reassessment/thesis closure remain separate.

## 2026-10-12 — Test disruptions against the original base (#37)

**Problem -> decision:** An infeasible child lacks minimum-plan comparison deltas,
so reconstructed baseline values disappeared. Retrieve/retain the actual immutable
original through the existing HTTP GET and compare saved minimum-cost plans. Reuse
the existing five-type composer, validation and MILP scenario API.

**Behavior:** What-if aligns original/child feasibility, demand, exact cost/exposure
and supplier allocations. Missing child results say Unavailable; original values
remain. Context/class/Practice-group/supplier joins are checked. Original-only read
failure preserves the child and entered draft; explicit GET retry creates nothing.
New scenarios always target the original, inherit classification/grouping and run
the same MILP with saved assessments. Draft/caveat text, purposeful error/save focus,
bookmarking and explicit guarded return are visible. Immediate submit throttling
prevents rapid duplicate saves; uncertain requests retain exact URL/payload/key and
require explicit replay. No backend, model/solver, API, migration or dependency change.

**Evidence:** Required full fast run passed 656 tests; final affected 97 passed
after the submit refinement. Final scenario browser passed all five actual saves,
bounded combined rejection, exact allocation cells, genuine infeasibility, original
retention, class/lineage, single-save double-click, keyboard/focus, five viewport
widths, draft Stay, controlled original-GET 503 and real API process-outage recovery.
Final-source Practice and existing immutable approval/PDF recovery each passed in
a separately identified mixed run; its earlier new-test locator failure was resolved
by the final standalone scenario PASS, not relabelled a suite PASS. Built-in-browser
desktop/320 comparison, keyboard scroll and unobscured error focus passed. Required
static/runtime/Compose gates passed; owned stacks/tab/viewport cleaned up. The
[handoff](UX37_SCENARIO_HANDOFF.md) preserves failures, evidence scope and limits;
the [runbook](UX37_SCENARIO_RUNBOOK.md) owns execution and cleanup.

**Limitation -> chapter relevance -> next:** Live Odoo, hosted CI, speech, physical
phones and owner/novice sessions remain unverified. Practice shares storage and
recovery is session-local. Original-read outage is controlled HTTP fault injection;
POST uncertainty is a real stopped API, both on disposable helper storage. No new
timing workload or independent persistence rerun was needed. UX-AC-10, FR/AC-V2-08,
AC-V2-07/09, NFR-V2-06/07 and UX29-04/06/07 support chapters 4/6/7. User controls
commit/push/merge; Drive/issues remain untouched. Next is #38 deliberate approval/
No-award review; #39 explanations and later human reassessment/thesis closure remain
separate.

## 2026-10-13 — Deliberate original-base approval and separate No-award (#38)

**Problem -> decision:** Immediate final-form submission made the immutable choice
too easy to record without reviewing its exact saved allocation and attribution.
Keep the accepted backend contract and insert a read-only confirmation step.

**Implemented behavior:** Selecting a plan still writes nothing. Review validates
original-base eligibility, actor, demonstration acknowledgement and required reasons,
then freezes exact intent on the Reflex server. The confirmation shows original
identity/context/dates, selected quantities/cost/exposure, actor and reason; Cancel
or Escape preserves the form without a save/key. Confirm sends once with existing
snapshot/idempotency/conflict rules. No-award has a separate reasoned action, no
approved allocation and no PDF. Saved outcome focuses immutable choice/time/reason;
uncertain requests retain exact URL/body/key and guarded explicit retry. Safe Cancel
focus, named review, local error focus and separately scrolling narrow content keep
actions visible. Practice/source/identity limits and no Odoo order creation remain
explicit. No backend, model/solver, API, migration or dependency change.

**Evidence:** Required full fast suite: 668 PASS; final affected tests: 69 PASS
after focus/layout corrections. Final browser selection: 2 PASS, including actual
alternative review/cancel/single-save double-click, immutable model-unconfigured
reopening, separate No-award with stopped-API exact recovery, child UI/API rejection,
long labels, keyboard focus and 1280/1440/768/390/320 reflow. Updated comparison
regression also passes native 200% zoom. Existing Practice and approval/PDF passed
earlier in a mixed run whose new-test failure is preserved, not called a suite PASS.
Real PostgreSQL transaction/document regressions: 14 PASS with no skips. Built-in
browser confirms final desktop/320 review, visible actions and Cancel-retained form.
Required static/runtime/Compose checks pass; all owned stacks/tab/viewport cleaned
up. The [handoff](UX38_DECISION_HANDOFF.md) records exact artifacts, retained failures,
verification timing and limitations; the [runbook](UX38_DECISION_RUNBOOK.md) owns
prerequisites, commands, expected outcomes and cleanup.

**Limitation -> chapter relevance -> next:** Fresh live Odoo, hosted CI, speech,
physical phones and owner/novice usability remain unverified. Practice shares storage,
actor references are not authenticated identity and exact recovery is session-local.
UX-AC-11, FR/AC-V2-11, AC-V2-09/10/12, NFR-V2-06/07 and UX29-05/06 support chapters
4/6/7. Commit/push/merge remain user-controlled; Drive/issues were untouched.
Next: #39 readable explanations; #40 recovery/documents is also unblocked. #41 human
reassessment remains separate.

## 2026-10-13 — Readable supplier assessments and exact Audit evidence (#39)

**Problem -> decision:** Reference time/applicability were buried, raw solver prose
dominated expanded ordinary notes and Audit omitted some exact model/path fields.
Reuse the stored-only frontend projection and organize interpretation separately
from exact evidence.

**Implemented behavior:** Suppliers leads with saved classes, generated sample,
history/reference time and saved quantity/time applicability. Recorded exclusions
and binding constraints use readable wording; zero allocation alone is explicitly
not an exclusion. Child assessments remain unchanged even when no allocation is
feasible. Critical synthetic/source limits stay visible. Guarded navigation focuses
Audit, where native disclosures retain exact inputs/policy, paths/model references,
solver/allocations/provenance, final decision and complete snapshot JSON including
node/leaf support and versions. Pretty-printing preserves values, not hash bytes.
Tables and long JSON scroll in labelled keyboard regions; the workflow checklist
remains in Practice/empty-entry help. No backend/core/solver/model/API/persistence,
migration, dependency, upstream-refresh or source-promotion change.

**Evidence:** Required full fast suite: 673 PASS, 73 deselected; focused contracts:
57 PASS. Final supplier/Audit browser passes original/feasible/infeasible cases,
exact input/full JSON equality, long/non-Latin and missing-business-name labels,
keyboard disclosure/focus/local scrolling, five viewport widths, native 200% zoom,
model-unconfigured reads and real stopped-API different-case GET/reopening without
inspection writes. Approval/No-award regression passed in an earlier mixed run;
its new fixture failure is preserved, not relabelled a suite PASS. Built-in desktop/
320 inspection confirms visible limits/timing and a 768px table locally scrolling
40px within a 198px region, with document width 305. Required static/runtime/Compose
gates pass; owned service/tunnel/Compose cleanup and viewport restoration confirmed.
Browser policy blocked explicit closure of the expired unmarked preview tab; normal
turn cleanup is not independently verified. The [handoff](UX39_EVIDENCE_HANDOFF.md)
records failures/timing/limits, and the [runbook](UX39_EVIDENCE_RUNBOOK.md) owns execution.

**Limitation -> chapter relevance -> next:** Live Odoo, hosted CI, physical phones,
speech and unfamiliar participants remain unverified. Synthetic exposure is not
calibrated probability; Practice shares storage and recovery remains session-local.
UX-AC-12, FR-V2-02/03/07/09, AC-V2-02/03/07/09, NFR-V2-03/07 and UX29-04/10 support
chapters 4/6/7. No independent transaction rerun or timing benchmark was required
for unchanged contracts. Commit/push/merge remain user-controlled, with Drive/issues
untouched. Next: #40 recovery and approved documents; #41 human reassessment remains
separate before T19 thesis closure.

## 2026-10-13 — Safe recovery and approved document access (#40, parent #42)

**Problem -> decision:** Uncertain saves were technically safe but unclear, finalized
conflicts left approval controls available, and the PDF lacked page controls. Reuse
the existing HTTP state/projection and React-PDF; preserve immutable backend content.

**Implemented behavior:** Distinct rejection/conflict/pending/unavailable/document
copy supplies explicit actions and copyable original request/support identity.
Uncertain create/scenario/decision retains URL/payload/key and navigation guards;
retry remains explicit. Session-loss limits are visible, with no durable outbox.
Finalization conflict pauses approval for stored-only GET reopening; failed/no-record
GET preserves context/proof. Approved product/demand/date/cost/allocations remain
visible through document failure. One-page preview has announced page status,
previous/next/end states, fit/zoom and byte-identical full download. Practice/actor/
synthetic limits and PDF eligibility remain. No backend/core/model/solver/Odoo/
persistence/renderer/content contract, migration, dependency or service change.

**Evidence:** Final full fast 675 PASS, 74 deselected; focused development 72 PASS.
Both final real-stack browsers PASS: actual GET/create/scenario/finalization/PDF
outages; exact replay/guards; one child/decision and unchanged stored content; real
competing HTTP 409 and GET-only reopening; five rendered PDF pages and exact SHA-256
download; keyboard, narrow/long/non-Latin labels and native 200% browser zoom.
A fresh isolated browser context had no pending recovery while the original kept
its proof. Initial locator failures and passing reruns are preserved in the
[handoff](UX40_RECOVERY_HANDOFF.md); commands/cleanup are in the
[runbook](UX40_RECOVERY_RUNBOOK.md). Built-in desktop/320 inspection confirms page
navigation, scoped PDF zoom and saved terms/retry/support through a real owned API
failure. Fast/static/runtime/pip/Compose gates pass. Owned storage/process/tunnel
cleanup, explicit preview tab closure and viewport restoration confirmed.

**Limitation -> chapter relevance -> next:** Recovery is session-local; copied JSON
does not restore a session. Practice shares storage, exposure is uncalibrated and
actor attribution is not authenticated identity. Unchanged transaction contracts
retain historical #38 evidence; no standalone rollback/contention or benchmark
rerun was needed. Live Odoo, hosted CI, physical devices, speech and human tasks
remain unverified/NOT ASSESSED. UX-AC-13/14, FR/AC-V2-09/10/11/12, NFR-V2-05/06/07
and UX29-06/08/09 support chapters 4/6/7. Local #32–#40 technical delivery is complete;
#41 participant/owner reassessment remains next before T19 closure. Commit/push/merge
remain user-controlled; Drive/issues were untouched.

## 2026-10-13 — Complete buyer reassessment: technical delivery, human gate open (#41)

**Problem -> decision:** Passing slices/CI do not establish the redesigned buyer
experience. Consolidate one real original through the existing Practice browser
test, reuse unchanged slice evidence, and freeze neutral human tasks and scoring.

**Implemented behavior:** One original now traverses Practice creation, exact
supplier comparison, saved feasible disruption, return/explicit alternative
approval, product/status library reopening without UUID and PDF failure/recovery/
byte-identical download. Separate feasible/infeasible exercises, reasoned No-award
and actual uncertain-create exact retry remain; reduced-motion preference runs
throughout. Harness evidence adds Git HEAD and actual copied frontend hashes.
The versioned human protocol and blank nine-task observation template separate owner
pilot/visual judgment from 3–5 unfamiliar people and preserve the approved threshold.
No production code, architectural boundary, dependency, migration or CI workflow change.

**Evidence:** Current full fast 675 PASS, 74 deselected; consolidated real-stack
browser 1 PASS in 95.37s. Static/runtime/pip/Compose gates pass. Current built-in
desktop/320 reference review, reflow, drawer keyboard focus/return and sampled
foreground/focus contrast pass; 200% native browser zoom, long/non-Latin/missing
labels, variable supplier/alternative outcomes and transaction gates retain linked
slice evidence. All 192 retained library observations were rechecked (six ×2 warm-ups
+30 measurements, p95 0.170–0.244s); query functions are unchanged, so no new timed
workload was run. Exact baseline `6535b0e` GitHub Quality and Container/API overviews
report success; Container step details are inconsistent/partial and not claimed as
independently verified. Hosted browser remains deferred. Owned stack/preview cleanup,
explicit tab closure and viewport restoration are confirmed.

**Limitation -> chapter relevance -> next:** Owner pilot/visual approval and novice
participants have zero recorded sessions: NOT ASSESSED, no human success/time/error
rates. Required successes remain 3/3, 4/4 or 4/5 per essential task, plus zero
unintended finalizations/unresolved critical misunderstandings. No threshold
relaxation or fabricated observations. Speech/physical-device checks and new-HEAD
CI retain their gates. UX-AC-01–16, AC-V2-09/13, NFR-V2-04/08 and UX29-03–10 map
to the official Python UI/integrated demonstration and chapters 4/6/7 in the
[assessment/handoff](UX41_ASSESSMENT.md); [runbook](UX41_REASSESSMENT_RUNBOOK.md) owns
commands and the [frozen protocol](UX41_BUYER_PROTOCOL.md) owns human tasks/scoring.
#41 remains open for owner/novice observations, critical-finding fixes and affected
retests; T19/final buyer acceptance are not implied. Commit/push/merge and tracker/
Drive publication remain user-controlled.

### 2026-10-14 — #41 partial owner walkthrough evidence

The owner reported a successful demo save and a missing saved-UUID lookup. A
stored-only session export confirms the new optimal Practice original remains
awaiting decision. The first report and post-attempt source/storage correction
are retained in [owner observations](UX41_OWNER_OBSERVATIONS.csv) and the
[assessment](UX41_ASSESSMENT.md#owner-pilot-observation--2026-10-14). Human timing,
independence and complete comprehension remain unassessed; owner evidence does
not enter the 3–5 unfamiliar-buyer denominator. No production code, Odoo data or
frozen protocol changed.

### 2026-10-14 — #41 owner requests clearer buyer workspace

Problem: owner B03 feedback describes improved appearance but excess metadata,
unclear No-award wording, raw source UUIDs and a need for a clearer real-Odoo
workflow. Decision: preserve the first report/screenshot and discuss desktop
hierarchy and RFQ-versus-confirmed-PO discovery before a new design contract.
Evidence: [owner observations](UX41_OWNER_OBSERVATIONS.csv) and
[assessment](UX41_ASSESSMENT.md#b03-and-broader-owner-feedback--2026-10-14).
The exposure definition was understood in part; no selected plan, measured time
or complete B03 outcome was reported. Owner visual approval has not been given.
No production code, accepted scope or frozen novice protocol changed. This is
owner feedback relevant to thesis chapters 4/6/7, not final buyer acceptance.

### 2026-10-14 — owner confirms case-focused dashboard direction

The owner selected a primary single-case workspace with supplier evaluation, MILP
plans, scenarios, explanations and human approval, plus a lightweight quotation/
saved-case overview. Open RFQs/quotations lead the workflow; confirmed POs/receipts
are supporting historical context. Spacious layout, tabs, contextual panels and
progressive disclosure are agreed design constraints. The
[confirmed brief](UX41_ASSESSMENT.md#confirmed-case-workspace-direction--2026-10-14)
and PRODUCT.md retain this direction separately from implemented capability.
No UI/backend code or frozen protocol changed; observed-history/model promotion,
B03 completion and final buyer acceptance remain open.

### 2026-10-14 — critical owner recovery/approval finding

Problem: O01 approved the B08 recovered case believing final approval was needed
for recovery, and did not understand uncertainty/session-loss limits. Decision:
record a failed first attempt and one task-unintended additional finalization,
then stop before B09 under the frozen protocol. Technical exact-key/input recovery
and single-case persistence passed; no database consistency defect was established.
Evidence: [assessment](UX41_ASSESSMENT.md#b08-critical-first-attempt-finding--2026-10-14),
[raw observations](UX41_OWNER_OBSERVATIONS.csv), and
[proposed correction brief](UX41_RECOVERY_CLARITY_BRIEF.md). No product-code change,
rollback or retest was performed. Novice gate remains unassessed; buyer acceptance
is not given. Relevant to chapters 4/6/7, AC-V2-09/13 and UX-AC-11/13/16.

### 2026-10-14 — Requested Drive synchronization and B09 instruction feedback

Owner explicitly skipped B09, then explained that the facilitator instruction was
not understood. Preserve this as facilitation clarity feedback, not an inferred
PDF product failure or success. No PDF fault was staged. B08 remains a critical
first-attempt failure; no novice acceptance or measured human time is inferred.

User requested Hungarian Drive updates. Updated/read back 00_THESIS_STATUS,
02_ROADMAP and 06_REQUIREMENTS_BASELINE with dated technical capability, owner
findings, dashboard direction, source boundaries and open gates. Native tab identity,
exact added text, historical paragraphs and existing rich links were verified.
07_DEVELOPMENT_STATUS and 03_ARCHITECTURE_DECISIONS writes were rejected by automatic
approval review as sensitive external assessment export without exact-payload
approval. No workaround or retry; prepared reviewable local drafts and request user
approval for those two existing destinations. Drive metadata reports both not shared;
ownership fields were not returned, so ownership is not independently verified.

Detailed payloads/readback outcomes are in ignored .artifacts/ux41-drive-update-20261014.
No new runtime/fast/hosted check, rendered PDF layout check, production edit, Odoo
write or Git publication occurred during this documentation synchronization.

### 2026-10-14 — Approved Drive synchronization completed

After explicit user approval of the exact pending Hungarian draft and its two
existing Drive destinations, 07_DEVELOPMENT_STATUS and
03_ARCHITECTURE_DECISIONS were updated successfully. Readback verifies exact
approved additions, native headings, document/tab identity and preservation of
historical text and rich links. Together with the prior three verified writes,
the requested five-document sync is complete. The earlier approval-review
rejections remain in the historical partial record; no workaround was used.

B09's unclear facilitator instruction and owner-requested skip are recorded,
without inferred PDF failure or completion. B08 remains open, novice evidence is
absent and the new dashboard direction remains proposed. No application tests,
rendered PDF-layout check, ERP writes or Git publication occurred in this follow-up.
Completion/readback evidence: ignored .artifacts/ux41-drive-update-20261014/completed.json.

### 2026-10-14 — Dashboard references and case workspace design brief

The owner supplied eight visual references and confirmed keeping the existing
green/mint/purple palette. [The proposed design brief](CASE_WORKSPACE_DESIGN_BRIEF.md)
maps horizontal case/task layouts, focused tabs and contextual panels to the current
saved-data contracts. It separates UI work from general Odoo quotation selection,
supplier/history discovery and observed-model promotion, and retains the B08 fix/
retest and B09 facilitation feedback. Reference values, branding and unsupported
statuses are not adopted as facts. Original image identities/hashes are recorded
in ignored .artifacts/case-workspace-reference-20261014/references.json; images remain
unchanged outside the repository. No UI implementation, new application verification,
Drive update, issue mutation or Git publication occurred in this planning step.

### 2026-10-14 — Confirmed case structure and next implementation specification

The owner explicitly confirmed the lightweight RFQ/Saved cases overview and
Overview/Suppliers/Plans/Scenarios/Decision & PDF primary views with secondary Audit,
retaining green/mint/purple. Prepared [the local specification](CASE_WORKSPACE_INCREMENT_SPEC.md)
and [eight proposed delivery slices](CASE_WORKSPACE_TICKET_BREAKDOWN.md), with the
save/recovery/approval correction first and the existing #41 human gate carried
forward rather than duplicated. Five task views do not remove legacy case URLs;
new Overview/Decision routes extend the whitelist and Scenarios retains whatif.

Refreshed Drive 00/06/02/03 read-only, used CodeGraph first and inspected relevant
flagged/current code ranges. RFQ summaries currently expose reference/vendor/date/
status/total and returned count/time, not product quantities, due date or generic
comparison groups. New quotation selection, supporting supplier/history and
observed-model promotion retain separate evidence/contract investigations.
Local HEAD dc2cf57 contains the owner's #41 commit; Drive's earlier uncommitted
publication wording remains a dated snapshot, not a claim about the new draft.

Document/source/traceability/dependency checks verify planning consistency only.
No UI build, application/runtime/hosted tests, service mutation, new canonical
requirements/ADRs, GitHub publication/closure, Drive write or commit/push/merge
occurred. Thesis use: buyer problem → confirmed structure → specified behavior →
contract inspection → data/human limits; chapters 3/4/6/7.

### 2026-10-14 — Generated workspace concepts and implementation workflow guidance

User explicitly requested images in the retained palette and Ask Matt guidance.
Generated three raster concepts: case Overview, Plans and Saved cases overview.
Inspected all three; made one targeted source-label edit to each case screen and
re-inspected them. Final PNGs, exact prompts, metadata/hashes and a review gallery
are in ignored .artifacts/case-workspace-mockups-20261014; original generated/input
files remain unchanged. Numeric comparison, allocation percentages, source context
and approval-only library PDF affordances were visually checked. These are design
concepts, not implemented/approved UI, measured contrast or usability evidence.

Read ask-matt/phase-boundaries, grill-with-docs and its two primitives, implement
and reflex-docs. Recommend staying in this chat through image review and a focused
remaining-decision grilling pass, finalizing existing drafts, then a fresh same-project
chat per self-contained implementation ticket starting S1. No grilling interview,
new glossary/ADR, application code, runtime test, issue creation/closure, Drive write,
new chat, commit/push/merge or scope expansion was performed. The gallery includes
a starter prompt retaining owner Git control over the implement skill's default.

### 2026-10-14 — Stabilize T18 runtime and clarify comparison recovery

Problem: owner B08 recovered a saved comparison then approved under the mistaken
belief that finalization completed recovery. Implement the existing correction
brief without changing business/API/storage/PDF contracts. Creation consistently
uses Calculate and save comparison; saved, selected, final and unconfirmed states
are explicit. New-comparison navigation/bookmarks clear stale decision feedback;
pending guards and exact request/key replay remain. Practice uses the same save
wording and no longer labels a saved or uncertain comparison a fresh draft.

Publication baseline: PR #31/local b94ff780, Quality failed the runbook snippet's
formatting; Container/API passed. Fix that wrapping and pin both Reflex declarations
to the locally/browser-tested 0.9.12 instead of silently resolving hosted 0.10.0.
No framework, architecture, backend/schema or Odoo-write change is introduced.

Broad fast gate: 677 PASS / 75 deselected, latest broad run 206.24 s, actual ML/CBC; existing
Starlette warning retained. Static/dependency/quiet Compose and production export
checks passed. Final transition checks: 54 PASS in 23.11 s. Eleven distinct browser
tests passed across recorded runs; the six-case remainder passed in 582.79 s and
the further final conflict-status check in 104.97 s. Genuine comparison recovery
saved one case, zero final decisions and zero documents. The
[correction handoff](UX41_CLARITY_HANDOFF.md) records versions,
source identity, exact browser/publication outcomes, retained setup/test failures,
cleanup and the next fixed-group live-Odoo browser-to-PDF verification. Windows
checks use a space-free CBC temp path and UTF-8 for dirty-diff evaluation metadata.

Keep the original B08 failure, B09 skip and frozen first-attempt evidence unchanged.
Technical checks do not close fresh owner/novice acceptance or #41/#42. The owner
explicitly authorized committing/pushing this correction; merge and Hungarian
Drive updates remain user-controlled. Exact publication/CI is reported at delivery.
Thesis relevance:
FR/AC-V2-09/10/11/12/13, NFR-V2-05/06/07, UX-AC-11/13; chapters 4/6/7.


### 2026-10-14 — Corrected-source B08 owner retest and sign-off

The save/recovery clarity correction on `11979618fe3af0904c93cdf3ae06b5ed1e1f684d`
was exercised in fresh owned session `t18-browser-32a580aed5e8`. One case matched
the original pending key and replay returned that case; seeded records remained
unchanged. The owner subsequently approved Alternative 1 and viewed its PDF, then
explicitly accepted B08 and deferred further UI work. Record technical recovery
PASS and assisted owner acceptance, retaining incomplete independent comprehension
and unscored extra-approval purpose. Preserve attempt 1 FAIL and novice NOT ASSESSED.
See [dated assessment](UX41_ASSESSMENT.md#b08-corrected-source-owner-retest-and-directed-sign-off--2026-10-14)
and [owner observations](UX41_OWNER_OBSERVATIONS.csv) for evidence and deviations.
B09's full human document-recovery task remains pending. No application changes
or new regression runs were needed; this is an evidence-only append.


### 2026-10-14 — B09 document recovery/download owner check

Technical PASS and assisted owner completion on source
`11979618fe3af0904c93cdf3ae06b5ed1e1f684d`: fresh-tab library reopening, real
owned API unavailability during PDF access, preserved approved terms, restored
document access and an actual downloaded five-page PDF identical to the pre-fault
artifact. Full case/decision/document and record counts remained unchanged; no
additional approval occurred. Page 4 was observed; individual zoom changes and
independent source/eligibility comprehension were not continuously assessed.
The owner reported no problem. Preserve original failed/skipped attempts and
novice NOT ASSESSED. [Assessment](UX41_ASSESSMENT.md) and
[observations](UX41_OWNER_OBSERVATIONS.csv) hold the evidence and deviations.
Only documentation/evidence changed; no new application regression suite was run.

The completed owner session was exported and cleaned up: owned project/processes
stopped and listeners closed; the user download and evidence remain available.
Owner/Odoo services and the existing running Podman machine were preserved.
