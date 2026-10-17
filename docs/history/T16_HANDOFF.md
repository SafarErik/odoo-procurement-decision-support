# T16: controlled procurement workspace

## Current status — 2026-10-08, cockpit usability revision

User feedback reopened T16 after the functional checks below: the report layout
did not make the buyer's next action, cost/exposure trade-off or test procedure
clear enough. This revision keeps the thesis baseline and existing API/model/MILP/
persistence contracts. It changes presentation and frontend organization.

- **Workflow:** Start with Saved case / Odoo / Demo, then use Plans / What-if /
  Suppliers / Audit. Odoo input review gets full width; a successful save returns
  to the comparison. The embedded test guide and
  [expected-outcome walkthrough](LOCAL_DEVELOPMENT_AND_SSH.md#procurement-cockpit-a-short-test-with-expected-outcomes)
  explain what to enter and inspect.
- **Decisions:** the UI states the extra cost and simulated exposure difference
  directly; the plot is compact, with exact money and a table key. Plan quantities
  are visible before solver detail. The USD 350 premium reduces synthetic exposure
  by 26.7 points for the documented Q=200 case; it is not a failure probability.
- **Scenarios:** one composer supports the five existing types, original supplier
  terms, draft changes and specific validation errors. Draft inputs reset on a
  supplier/type change; uncertain saves freeze intent and require explicit replay.
  Saved base/scenario comparisons appear before the form. Demand changes retain
  the different-total-quantities warning; infeasibility fabricates no metrics.
- **Supplier explanation:** rounded branch conditions lead to the saved class;
  exact float32 values/thresholds, model identity and provenance remain available.
  The training explanation documents generated histories, two features, the
  next-30-day label, separated supplier/time partitions and uncalibrated leaf score.
- **Maintenance:** `frontend/app.py` is an 11-line composition root. The RFQ ledger
  lives in `frontend/rfq_page.py`; shared colors in `frontend/theme.py`; planning
  state, input forms, scenarios, results, audit and page composition are separate
  modules in `frontend/planning/`. The redundant outage handler was removed;
  regression tests use the unified composer. No dependency or backend/migration
  change was required.

**Verified final source:** 521 fast tests passed, 45 service/E2E tests deselected,
one existing upstream Starlette/httpx deprecation warning (final run: 61.01s). Actual offline
training/reload/inference and CBC execute. Ruff format (166 files)/lint, compileall,
pip check and quiet Compose configuration pass. The initial Compose probe lacked
the provider on PATH; the existing project-local provider resolves it.

**Browser and database evidence:** built-in browser on isolated 3111/8211 and
API 8111, retaining user 3000/8001/8000 and the Podman tunnel. Fresh Odoo creation
re-reads group/currency and saves USD 1,850/2,200 with synthetic ML history. All
five scenarios and demand-500 infeasibility were exercised through PostgreSQL.
Acquisition/inference were forbidden during the scenario stage. Independent GET
through user API 8000 verifies nine snapshots, original parents, unchanged base
hash and saved facts/assessments. Mobile Plans/What-if/Audit have document width
375px in a 390px viewport; override restored. RFQs still show 13 quotations and
8 vendors. Browser screenshots and verification output are ignored under
`.artifacts/t16-revamp/`. Full-page capture was unavailable; viewport screenshots
were inspected instead.

Production `reflex export --frontend-only --no-zip` passes all four build stages
in the isolated generated cache (compilation only). The shared service token is
absent from 39 generated client/export files. Stopping only the agent API produces
the safe service-unavailable message and clears the previous case/plot. Agent
preview processes/tabs are closed; user 3000/8001/8000, the Podman containers and
forwarding tunnel remain running. No resetting persistence suite was run against
the manual database. Hosted CI for this uncommitted diff remains unverified.

Pure synthetic browser creation also saves EUR 102/109 using the separately
configured synthetic model, without Odoo acquisition. Final runtime review caught
Reflex's number-event conversion; numeric text fields now retain exact draft
strings, including clean empty values, without new state type warnings.
Synthetic case: `3218a3fa-2c8b-4292-b5c5-ffa5c85b1264`.

Fresh base: `400a2b2f-7625-4876-a1e5-7f2eb7e255c7`, hash
`3d0cad9b260f6b6534e5f3c3cc036810ab63293d643eb1460100b1bab3e7c9d0`.
The original `e183f917-fc33-4e28-a7a8-0aea22679176` retains hash
`c25ff724c228409eb19287cf49776c634cc8a90d5db6726372398c0e1b3d98ce`.
The local test IDs/expected values are in the runbook and ignored `ids.json`.

**Boundary:** user acceptance/publication and new-diff hosted CI remain pending.
Changes are unstaged/uncommitted/unpushed on the existing T16 branch; Drive is
unchanged. Saved snapshots contain canonical IDs, not supplier/product business
names, so the UI uses neutral Supplier 51 / Product 54 labels with exact identity
in Audit. Mock data inside Odoo would still be synthetic; observed dataset/model
promotion requires a separate documented extraction/label/evaluation increment.
No Odoo writes, training in HTTP/Reflex, arbitrary quotation discovery, approval
or PDF were added. After user acceptance: synchronize relevant Hungarian Drive
status, then plan T17 approval/PDF with these limits explicit.

## Historical functional acceptance — 2026-10-08, before usability feedback

The controlled cockpit implementation is complete and local functional acceptance
passes. User testing, publication of this final diff and its exact-HEAD CI remain
pending; T16 is not merged and full V2 acceptance is not claimed. Drive was read
to check the accepted requirements and was not edited. The requirements baseline
is [06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit).
AC-V2-09 is locally satisfied for the controlled cockpit. FR-V2-09's human
approval/PDF behavior still belongs to T17; AC-V2-11/12/13 remain open.

### Final change and publication boundary

Add a responsive native HTML/CSS cost-versus-exposure plot using saved plans only,
with a numbered key, exact decimal money, approximate positions and fixed 0–100
exposure scale. No new chart package, backend endpoint, migration, model/solver
algorithm or runtime training was added. Cards retain exact exposure/premium
fractions. A single-plan result explicitly distinguishes no distinct alternative,
no requested alternatives and an incomplete alternative search. Infeasible cases
have no chart or fabricated zero metrics. Coincident points may overlap; every
saved plan remains individually listed in the key/cards.

The input audit now shows the current saved price, capacity, MOQ, promised date,
availability and price/delivery applicability, plus policy and recorded ML
quantity applicability. Scenario controls retain original-base terms independently
of those saved child inputs. GET/chart display never reacquires Odoo facts,
loads a model or solves a plan. Existing API/recovery and server-only token
boundaries remain unchanged.

Published PR [#18](https://github.com/SafarErik/odoo-procurement-decision-support/pull/18)
is open at `0a2cafbacef4adf45f97902df56d7aace21d8786`. Its exact-HEAD
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37806351589)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37806351546)
runs are independently verified successful. They cover the published five-scenario
workflow, not this final local chart/audit/acceptance diff. Changes remain unstaged,
uncommitted and unpushed. Historical records below retain their original boundaries.

### Controlled acceptance matrix

| Requirement / check | Actual evidence and scope |
| --- | --- |
| Case creation and input review, FR-V2-01/09 | Fresh Reflex -> FastAPI -> read-only Odoo -> saved synthetic model -> unchanged MILP -> actual PostgreSQL: Q=200, USD 1,850/2,200. Captured quotation preview and supplied business terms remain separate; FastAPI independently re-reads group/currency before creation. Pure synthetic browser creation also passes at Q=10, EUR 102/109, using its matching owner-configured domain. |
| Plans, allocations, charts, FR-V2-06/09 | Chart/key/cards show USD 1,850 at 75.0/100 versus USD 2,200 at 48.3/100, exact money/premium and saved allocations. Outage/combined single-plan results display the explicit no-distinct-alternative message. Focused checks cover equal costs, endpoint exposure, close decimal costs, incomplete search and missing plans. |
| Explanation and input provenance, FR-V2-07/09 | Actual saved tree branches, history window, supplier classes, saved input/policy table, field sources and score applicability are visible. Sources remain Odoo quotations + supplied terms + separately synthetic history. |
| All five stress types, FR-V2-08/09 | Fresh browser children: outage USD 2,200; capacity 100 USD 2,200; demand 220 USD 2,040; price 11.00 USD 2,150; combined demand 220 + capacity 100 USD 2,400. Every child targets the original base, including when submitted from another child. Acquisition/inference are forbidden on the isolated API during this stage; saved assessments are reused. |
| Infeasibility, loading and errors, FR-V2-09 | Demand 500 saves infeasible with no chart, invented allocations or cost comparison. Browser loading is visible and controls are disabled. One-change combined input is rejected before POST. Stopping only the agent API gives the safe service error and clears prior chart/case; tests also cover invalid UUIDs, auth/not-found/malformed snapshots and definite/uncertain POST outcomes. |
| Immutable persistence/retrieval, FR-V2-10 | Independent HTTP GET from actual PostgreSQL verifies all children, original parent, unchanged base hash and identical saved facts/assessments. User API on 8000 reopens the fresh base with matching hash after the isolated API is stopped. Fast tests forbid source/model/solver calls on stored GET/exact replay and verify recovery retains exact intent/key. No resetting suite was run against manual cases. |
| Browser presentation / existing RFQs | Chart checked at 390px with no horizontal document overflow; viewport restored. Exact values remain in a table for accessibility. No visible framework connection error or browser warning/error at final successful rendering. Existing RFQ ledger reads 13 quotations / 8 vendors through the API. |
| Required Python 3.11 checks | **516 passed, 45 integration/E2E deselected**, one upstream Starlette/httpx deprecation warning, 74.58s. Real ML training/reload/inference and bundled CBC execute. Ruff format (156 files)/lint, compileall, pip check and quiet Odoo Compose configuration pass. |
| Frontend compilation / credential boundary | Production `reflex export --frontend-only --no-zip` passes four build stages in the isolated generated cache; compilation only. Shared token absent from 41 generated client/export files; public-state/recovery tests also pass. Browser/export reuse Python 3.14.7 / Reflex 0.9.11.post1; required validation uses Python 3.11.16 / Reflex 0.9.12. |

Browser evidence and independent stored GET output are ignored under
`.artifacts/t16-closure/`: `ids.json`, `cases.json`, `tradeoff.jpg`, `mobile.jpg`
and `verify.py`. Fresh base `233b8b59-10cf-43ee-aaa0-61eef4a00a30` remains available
through the user's API. Children: outage `c6cbb68b-5d8d-4171-87ee-b29f14d76f0f`,
capacity `470b69c9-5735-4baa-b0e5-c86e1785b1be`, demand
`c02adda1-118f-4360-9fac-e44bcac2c6d4`, price
`40f521de-a41d-4e56-8c2a-c90a284f99ad`, combined
`df0e619b-4b1a-4491-adcb-f2af82b53896`, infeasible
`e87a42ae-9440-4fb3-92ab-ca96b7ecbc02`. Fresh synthetic base:
`a8723891-cf95-45d2-b046-0246bdb6ee70`. UUIDs describe this local database;
the prepared runbooks are the reproducible procedure for another environment.

Agent preview listeners 3111/8211/8111 are stopped and the acceptance tab is closed.
The existing user services 3000/8001/8000 and localhost-only forwarding process
2876 on 8069/55433 remain running. No user `.env`, default prepared artifact,
generated `.web` cache, Podman machine, container or database volume was replaced.
The isolated preparation generated matching models offline and added eight own
planning snapshots, without changing Odoo records. The resetting database suite,
new-diff hosted CI, production browser run and formal accessibility audit were
not rerun/performed; they are not implied by compilation or scoped local acceptance.

### User handoff and remaining scope

Repeat [T16 final user validation](LOCAL_DEVELOPMENT_AND_SSH.md#t16-final-user-validation),
then publish and verify CI for the new exact SHA under user control. Synchronize
Hungarian Drive documents on the user's next explicit request, then plan T17
human approval/no-award and approved immutable snapshot PDF. No new API key or
Odoo data entry is needed for this T16 review.

Arbitrary Odoo discovery, broader multi-supplier combinations and observed receipt
dataset/model promotion remain explicitly unimplemented. They are outside this
controlled T16 closure, not silently accepted capabilities. Full system evaluation
belongs to T18; the full visual redesign remains later work. The model still uses
synthetic evidence and its score is an uncalibrated exposure proxy. No Odoo writes,
direct Odoo database access, seeding, approval/PDF or cloud infrastructure was added.

## Prior status — 2026-10-08, scenario controls and comparison

The prepared-Odoo increment is now published in open PR #18 at
`ad8aeb2358470fba2fa386851bd140b70f72dbfb`. Its
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37779183516)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37779183536)
runs completed successfully, independently verified. The following addition is
local, unstaged and uncommitted; those checks do not cover this diff. No commit,
push, merge or Drive synchronization occurred. Earlier records below retain their
historical publication, scope, checks and limitations.

### Buyer capability and boundary

The existing outage control is joined by capacity reduction, demand increase,
price increase and a bounded combined form. Combined accepts at least two changes
among demand and one selected supplier's capacity/price. Every scenario uses the
original saved base, even from a child. Original supplier terms are displayed for
validation; simulated prices are labelled what-if assumptions, never fresh Odoo
facts. The resulting child retains immutable lineage, attribution and assessments.
No new backend contract, migration, solver/model algorithm, service or dependency
was added. Odoo acquisition and inference are unnecessary for scenarios/GET.

The stored comparison shows original/scenario feasibility, demand, minimum total
cost, exposure and per-supplier quantities/deltas. It uses the existing recorded
comparison and result, not new solving or scoring. Exact fractions remain in audit
details. Demand comparisons explicitly warn that total quantities differ; a cost
delta is not a like-for-like saving. No proven minimum means unavailable metrics
and allocations, never fabricated zero values. Solver failure is distinct from
proven infeasibility. The full base is accessible through stored GET.

Exact URL/body/key recovery, explicit retry, changed-intent blocking and server-only
credentials are preserved. Returned comparison rows must join the base suppliers,
match recorded demand totals and agree with the scenario's saved allocations.
The combined UI deliberately covers one supplier plus demand; broader combinations
remain unimplemented rather than hidden behind a generic editor.

### Verification

| Check | Actual evidence |
| --- | --- |
| Focused/regression | Existing frontend suites: 47 passed. Initial new scenario suite: 28 passed; the added comparison/result mismatch regression is covered by the final full run (29 new tests total). Actual API/CBC, all four new controls, repeated scenarios from children, exact recovery after lost committed response, invalid inputs, malformed comparison and what-if provenance. |
| Required Python 3.11 checks | 509 passed, 45 integration/E2E deselected, one upstream Starlette/httpx warning, 55.58s. Actual ML training/reload/inference and CBC execute. Ruff format (155 files)/lint, compileall, pip check and patch whitespace pass. |
| Real browser/API/PostgreSQL | Stored hybrid base `e183f917-fc33-4e28-a7a8-0aea22679176` stays USD 1,850. Capacity 100 -> USD 2,200; demand 220 -> USD 2,040; supplier 53 price 11.00 -> USD 2,150; demand 220 + capacity 100 -> USD 2,400; demand 500 -> stored infeasible. API preview forbids Odoo acquisition/inference. Independent GET verifies all five children, original parent, identical saved assessments/facts and unchanged base snapshot/hash. |
| Browser presentation | Stored combined-case reopening shows original/scenario quantity, cost, exposure and allocation changes. Final labels use readable status text. At the 390px viewport override, page has no horizontal overflow; override reset. No visible framework connection notice or console warning/error after final reload. |
| Browser failure/compilation | One-change combined form rejected before POST. Stopped API gives safe service error and clears comparison. Production frontend-only export passed four build stages; compilation only. |
| Static/credential boundary | Odoo Compose config and required static checks pass. Server token absent from 41 generated client/export files and public state/recovery JSON. |
| Remaining gates | New hosted CI, the resetting database suite, arbitrary quotation discovery, broader combined changes, observed model promotion and full T16/V2 acceptance remain open. Approval/PDF belongs to T17. |

Live evidence is ignored under `.artifacts/t16-scenarios-check/`: `cases.json` and
`comparison.jpg`. Saved children: capacity `579192b3-0e0f-49dd-aa0d-4705e94a1c28`,
demand `2204e8de-33b1-4b87-95c1-b49423c7bdde`, price
`e66407ec-3040-40da-8e4c-135845e7b3ad`, combined
`dd643faf-3f72-499b-86b4-f1202bcc550a`, infeasible
`07eb3b3b-f0d4-4540-937d-c3752d4deb08`. No resetting test or Odoo operation was
performed against user data. Runtime/export/cleanup details are in the log.

### Review and next step

Use the [scenario walkthrough](LOCAL_DEVELOPMENT_AND_SSH.md#what-if-scenarios-and-stored-comparisons).
Only the planning database, FastAPI and Reflex are needed for an existing base.
No new API key or manual Odoo change is required. Commit/publication/merge remain
with the user; check CI for the resulting exact SHA. Then assess the complete
controlled workflow against T16 acceptance requirements before claiming closure.
General Odoo selection and observed-model promotion are not solved by these forms;
T17 approval/PDF remains separate. Drive stays unchanged until explicitly requested.

## Prior prepared Odoo creation — 2026-10-08

PR [#18](https://github.com/SafarErik/odoo-procurement-decision-support/pull/18)
is open at `de7ac92820e367e28b79dd0f7073f5b8c4191397`. Its
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37753212085)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37753212092)
runs are completed/success, independently verified on 2026-10-08. These checks
cover the published synthetic creation/outage workspace, not the following local
diff. No commit, push, merge or Drive edit was performed. Historical records below
retain the scope and limitations of their dates.

### Capability and boundary

At `/planning`, **Plan from Odoo** loads the fixed owner-prepared three-quotation
comparison. The buyer reviews captured Odoo price/context expectations and enters
explicit demand, required date, supplier capacity, MOQ and promised dates. Blank
MOQ explicitly means none. Policy, availability, applicability ranges and synthetic
history retain the prepared values. Prices and identities cannot be edited in the
form. Capacity is a controlled limit, not stock; quotation quantity is not demand
approval. The controlled authority reference is not T17 human plan approval.

Loading this preview reads local JSON only. Creation uses the existing authenticated
`/from-odoo` route: FastAPI independently reads Odoo/currency, checks expectations,
loads the matching trusted saved Decision Tree, runs unchanged MILP and persists
an immutable case. Changed quotations fail closed without silently substituting
prices. The browser chooses neither files/models nor arbitrary comparison groups.
No new backend contract, infrastructure, migration or dependency was added.

New UI terms receive `controlled_business_terms` / `t16-ui-odoo-terms-v1` attribution
and a server timestamp. Odoo identity/price provenance and separately synthetic
history remain distinct. The Decision Tree is real; its training/history here are
synthetic, so its output is an uncalibrated exposure proxy. This does not establish
observed supplier-model validity. Training remains offline. One configured model
serves one compatible domain; switch/restart FastAPI between pure synthetic and
Odoo-domain creation. Saved GET/outage flows need neither model nor Odoo.

Existing uncertainty handling retains the exact body/key, blocks changed intent
and requires explicit retry. A successful response must identify the requested
Odoo comparison and hybrid input kind. Shared authentication stays on the Reflex
server; recovery JSON contains no token. Recovery remains session-scoped.

### Verification

| Check | Actual result |
| --- | --- |
| New focused checks | 15 passed: real saved tree/CBC through ASGI; edited-term attribution; changed Odoo price rejects before persistence; invalid terms never POST; source/group mismatch fails closed; lost response after commit recovers the same row without Odoo/inference, then outage/GET reuse stored inputs. |
| Required Python 3.11 checks | 480 passed, 45 integration/E2E tests deselected, one upstream Starlette/httpx warning, 46.28s. Ruff format/lint, compileall, pip check and diff whitespace pass. |
| Real browser/Odoo/API/PostgreSQL | Base `e183f917-fc33-4e28-a7a8-0aea22679176`: USD 1,850 and USD 2,200; allocations 50/0/150 and 100/100/0. Supplier 53 outage `71958fa0-8583-4393-a787-39c1f7bee1f5`: USD 2,200 and +350 USD. Stored base reopening returns USD 1,850/2,200. Independent GET confirms lineage, reused assessments and separate Odoo/controlled/synthetic provenance. |
| Browser failure/layout | Stopped FastAPI produces the safe unavailable-service message and clears previous results. At a 390px viewport override, the new supplier grid has one column and no horizontal page overflow; override reset. No visible framework connection notice or console warning/error at successful retrieval. |
| Frontend export | Production frontend-only export passed all four build stages; compilation only. |
| Credential boundary | Shared service token absent from 41 generated client/export files and from public state/recovery JSON. |
| Unrun gates | Hosted checks for this new diff, the resetting database suite and observed-model promotion were not run. Existing user cases/volumes were preserved. No Odoo writes occurred. |

The first sandbox pytest invocation stalled without output and was stopped; a
fresh ignored basetemp under the normal Windows identity ran successfully. Early
test assertions were corrected for formatted money, streamed ASGI responses and
canonical JSON snapshot storage. No application workaround weakened those contracts.

Live verification prepared matching Python 3.11 assets under ignored
`.artifacts/t16-odoo-check/live/`, preserving default demo artifacts. Preview
FastAPI ran on 8109; Reflex ran on 3109/8209 using the existing frontend environment
(Python 3.14.7 / Reflex 0.9.11.post1). Validation remains Python 3.11.16 / Reflex
0.9.12. The stopped existing Podman machine/containers were started; healthy
containers needed a localhost SSH tunnel because Windows forwarding failed.
No database-reset test ran against the manual planning database.

Ignored evidence: `.artifacts/t16-odoo-check/cases.json` and
`stored-odoo-plan.jpg`. Preview processes/tab were stopped; runtime cleanup is
recorded in the implementation log. The saved controlled cases remain available.

### User review and next capability

Follow the [Odoo workspace procedure](LOCAL_DEVELOPMENT_AND_SSH.md#controlled-odoo-planning-workspace):
prepare group 2 offline, configure its matching model, restart FastAPI/Reflex,
review terms, create USD 1,850/2,200, run supplier 53's outage and reopen both IDs.
The existing read-only Odoo key is sufficient; no new credential or Odoo entry is
needed for the verified fixture. Commit/publication/merge remain with the user;
CI must run for the resulting SHA.

T16 is still partial: arbitrary quotation discovery, other scenario controls and
full acceptance remain open. The next small buyer capability is another existing
stress scenario control with stored base comparison. Observed Odoo history/model
promotion remains separate; approval/PDF belongs to T17. Drive remains unchanged
until explicitly requested.

## Prior creation / outage / UX increment — 2026-10-07

The first stored-view slice is committed as `b9987df`; the following addition is
local, unstaged and uncommitted on `feature/T16-reflex-frontend-implementation`.
No commit, push, merge or Drive synchronization was performed for this increment.
The records below remain dated historical evidence; their earlier scope/status
statements do not describe this new capability. T15 main/CI evidence still applies
to its exact merged SHA, not these new changes.

The buyer can now load the prepared synthetic inputs, inspect price/capacity/policy,
enter demand, create/save a plan through the existing POST API, run one explicit
supplier outage, return to the base and reopen either UUID through stored-only GET.
Every outage runs against the original base, never cumulatively against a child.
Editable demand receives its own controlled authority/source reference; commercial
terms/history/policy retain the prepared fixture attribution. This is a simulation,
not operational demand approval. Odoo acquisition is outside this creation form.

The workspace puts quantity allocations and cost trade-offs first. Supplier bars
show allocated quantities; scores use a labelled 0–100 exposure scale. The exact
rational values and original solver notes remain expandable. Plain-language notes
preserve the meaning of unselected suppliers and binding capacity/concentration
limits, without asserting causal explanations. Saved class labels, delivery
adherence, completed-receipt support and history windows explain the ML input.
Tree paths are model branch conditions, not receipt records. Audit details keep
identity, timestamps, model/source references and field provenance accessible.
Responsive tabs/forms use existing Reflex/native HTML components, without a chart
package, new dependency, custom JavaScript or additional infrastructure.

### Model meaning and API boundary

`DecisionTreeClassifier` predicts `schedule_regular` / `schedule_watch` using prior
Expected Arrival adherence and eligible completed-line count. The score is the
class-1 training fraction in the reached leaf, rounded according to the existing
T14 mapping. Plan exposure is the existing quantity-weighted score aggregate.
Synthetic training makes it a controlled exposure proxy; it is not a calibrated
failure probability, expected late quantity or validated real-world predictor.
UI presentation does not alter model, class, score, risk coefficients or MILP.

Reflex calls only existing authenticated routes: base POST, scenario POST and saved
GET. It reads the fixed owner-prepared demo JSON locally for the synthetic form;
the browser cannot choose executable artifacts or files. FastAPI alone loads the
owner-configured compatible saved model and performs inference/optimization.
Training stays offline. Shared bearer authentication remains server-side PoC access,
not buyer identity. No backend/core/API contract or migration changed here.

Each new action gets one canonical UUID idempotency key. Unknown POST outcomes
retain the exact URL/body/key, block changed intent and offer an explicit retry.
A failed recovery attempt (including authentication rejection) does not discard
previous uncertainty. There are no automatic retries or redirects. The readable,
copyable recovery JSON contains no token. Recovery intent lives in the Reflex
session: copy it before leaving/restarting. Durable multi-user request recovery is
a separate capability, not hidden infrastructure in this local slice.

### Verification and limits

| Check | Actual evidence |
| --- | --- |
| Focused frontend/API checks | 32 passed; actual saved model/CBC, ASGI create/GET/outage and state transitions. A response lost after commit, then rejected authentication during recovery, retains the same payload/key and recovers one row. Invalid demand, malformed snapshots, secrets, no redirects/retries and stored-only retrieval remain covered. |
| Required Python 3.11 checks | 465 passed, 45 service/browser tests deselected, one upstream Starlette/httpx deprecation warning. Ruff format/lint, compileall, pip check and diff whitespace pass. Final run details are in the implementation log. |
| Real browser / API / PostgreSQL | Isolated Reflex on 3108/8208 called real FastAPI on 8108 using the existing planning database/tunnel. Base `8b64062b-b695-4ed9-b49c-52f43064c835`: EUR 102/109. Supplier S226 outage `ed2e23c1-c4e2-4c7a-90e0-0b3a6a1c6463`: EUR 106 and +4 EUR. Reopening the original base returns EUR 102/109; independent GET verifies lineage, stored snapshots and reused assessments. |
| Edited demand / infeasibility | Demand 25 saves `1e9c3368-d5db-4307-b7b9-1d2910199e31` as infeasible. Independent GET verifies quantity 25, `controlled-demand-25-t16-v1` and `t16-ui-demand-v1`. This is a stored business result, not a service failure. |
| Browser UX and failures | Disabled in-flight controls, readable constraint notes, base navigation, stored-service unavailable/clear/recovery, and native exact-request copy verified. At 390px the plan grid has one column and no horizontal page overflow; the viewport override was reset. Final console is checked after development reload. |
| Production frontend export | `reflex export --frontend-only --no-zip` passed all four build stages in the isolated cache; compilation only, not production browser acceptance. |
| New hosted CI / live Odoo / resetting integration suite | Not run for this increment. The current manual planning database was preserved; no resetting tests ran against it. No new Odoo read/write or observed-model promotion was performed. |

Validation uses Python 3.11.16 / Reflex 0.9.12. The browser frontend and export
reuse the user's Python 3.14.7 / Reflex 0.9.11.post1 environment; FastAPI and the
model run under Python 3.11. No compatibility baseline was changed. Agent-owned
preview ports 3108/8208/8108 were stopped and the temporary tab closed. The user's
3000/8001/8000 services, existing database and 55433 tunnel remain running.

Ignored evidence is under `.artifacts/t16-next-browser/`: `cases.json`,
`desktop-comparison.jpg`, and a separately prepared Python 3.11 `demo/model/`.
The existing default demo model was incompatible with that runtime; the verification
model was prepared offline in the isolated folder, with identical original request
inputs. The original artifacts were preserved. First creation returned 503 and
retained intent; after pointing only the agent's preview API at the compatible
model, explicit retry succeeded. The runbook now explains this setup distinction.
An unconfirmed in-app browser download was replaced with verified native clipboard
copy plus a read-only JSON field. Final browser inspection found no visible connection warning and no console
warning/error; requests succeeded after reload. This does not establish production
E2E coverage. The generated preview cache and all newly saved cases are synthetic.

### User review and next capability

Follow the [current workspace walkthrough](LOCAL_DEVELOPMENT_AND_SSH.md#controlled-planning-workspace-create-and-test).
Creation requires the matching offline model configured on FastAPI; stored GET
and scenario reruns do not. No new Odoo API key is needed for this slice. Review
quantity 10, Supplier S226 outage, base reopening, saved UUIDs and quantity 25.
Commit/publication/merge remain under the user's control; verify hosted checks for
the published SHA before claiming them.

T16 remains partial. The next buyer capability is read-only Odoo quotation selection
with explicit supplemental terms through existing `/from-odoo`, preserving the
synthetic ML provenance. Then extend other existing scenario controls and visual
comparisons. Approval/PDF belongs to T17. Observed receipt/model promotion and full
V2/system acceptance remain separate open gates.

Thesis note: problem = a technical snapshot dump with terminal-only creation;
decision = progressive buyer explanations and reuse existing POST/GET contracts;
behavior = controlled create -> saved ML -> MILP -> immutable outage/retrieval;
evidence = API/state/CBC/browser/PostgreSQL checks; limitation = synthetic model,
one scenario control and session-scoped recovery; relevance = architecture,
implementation, usability and testing chapters.

## First stored-view increment — historical record


## Status — 2026-10-07

Implemented locally on `feature/T16-reflex-frontend-implementation`, starting at
T15 merge `3c19890bd17cd89ffd6d4fbdfca3152d07898f55`. Changes remain unstaged,
uncommitted and unpublished. This is the first T16 capability, not complete
T16 or V2 acceptance. No Drive documents were edited during this increment.

T15 PR #17 is merged. Its main SHA above has successful post-merge
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141549)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141222)
runs, independently rechecked through authenticated GitHub reads. These results
cover T15 main, not the uncommitted T16 changes. Earlier handoffs/log entries
retain their historical branch, checks and limitations.

## Buyer-visible result and boundary

Open `/planning`, paste a UUID from a completed run and load the case. The page
shows the stored minimum-cost/alternative plans, integer allocations, exact money,
exposure/premium ratios, explanations, saved supplier scores/tree paths, identity,
parent lineage and field provenance. A saved scenario also shows its recorded
comparison. Ratios retain exact numerator/denominator alongside a clearly marked
four-decimal approximation; money is never converted to binary floating point.

The root RFQ ledger remains available, with navigation between the two pages.
Native form labels, heading hierarchy, live status/error announcements, disabled
loading controls, collapsible details and scrolling tables provide the basic
accessible/responsive presentation. A failed submission clears previous results.

```text
browser UUID submission -> Reflex Python state handler
  -> GET /api/v2/procurement/planning-cases/{case_id}
  -> existing immutable stored snapshot -> presentation values -> browser
```

The existing FastAPI route and DTO remain unchanged. There is one authenticated
GET, a seven-second HTTP timeout, no redirect following and no automatic retry.
UUID/token validation precedes transport; unsupported/incomplete responses fail
closed. Network/database failures, missing cases and rejected access receive safe,
actionable messages without raw response bodies or credentials.

`BACKEND_BASE_URL` and `T12_TRUSTED_CALLER_TOKEN` are trusted server settings. The
token is `SecretStr` and remains outside Reflex state/form fields/generated browser
code. The local shared service credential proves possession, not buyer identity;
bind the development servers to loopback. No browser-supplied token/URL selects
upstream access. Do not expose this PoC as an authenticated multi-user deployment.

Synthetic and hybrid banners retain the saved input kind. Hybrid Odoo quotations
remain separate from synthetic ML history; scores are exposure proxies, not
failure probabilities. Recorded ML validity is historical and viewing it does not
refresh inference. The frontend neither imports planning/Odoo/persistence logic
nor calls creation, replay or scenario POST routes.

## Verification

| Check | Actual result and scope |
| --- | --- |
| Focused frontend/API checks | 23 passed before the final runtime/HTML correction; covered safe transport, exact display, provenance and state recovery. |
| Final Python 3.11 fast suite | **451 passed, 45 deselected**, one upstream Starlette/httpx deprecation warning, 41.33s. Includes actual saved ML/CBC and real FastAPI GET mapping with assembly/Odoo/inference/solver traps. |
| Required static/environment checks | Ruff format (152 files), Ruff lint, compileall, pip check and `git diff --check` passed. |
| Odoo Compose configuration | `config --quiet` passed; no service or Odoo mutation. Sandbox executable access initially failed; the read-only validation passed with elevated tool execution. |
| Production frontend | `reflex export --frontend-only --no-zip` passed, four build stages. Final spacing was also checked in production-mode browser rendering with no console errors. Python 3.11, Reflex 0.9.12, installed Node.js 24.20.0; CI baseline remains Node.js 22.22. |
| Browser display | Actual Reflex web/state server -> FastAPI stored GET, using an isolated memory repository rehydrated from prior completed T15 reports with snapshot hashes verified. Synthetic EUR 102/109 and hybrid USD 1,850/2,200 base plans displayed; hybrid outage USD 2,200 and USD 350 delta displayed. Identity/tree paths/provenance expanded successfully. |
| Browser error/recovery | Invalid UUID, missing case and stopped-FastAPI errors displayed; loading disabled controls, cleared results and recovery after restart verified. |
| Credential boundary | State test excludes the service secret; separate scan found no token in 50 generated browser files. |
| New hosted CI / live Odoo / PostgreSQL browser flow | **Not run for T16.** The browser's memory repository is not new PostgreSQL persistence acceptance or a live Odoo acquisition. Existing T15 evidence remains separate. |

Browser verification disabled Odoo credentials, trusted model configuration,
inference and solver functions. The temporary harness exists only in ignored
`.artifacts/`; it is not a new runtime component or replacement database adapter.
Screenshot evidence is retained there as `stored-hybrid-plan.jpg`. The agent-owned
verification processes and temporary credential are cleaned up at handoff; user
Odoo/Podman services are not stopped.

Browser checks caught nested paragraph markup (fixed with a span) and Reflex's
event conversion import failing without SQLAlchemy asyncio/greenlet. The existing
frontend dependency extra now includes `sqlalchemy[asyncio]`; a runtime import
check guards this installation requirement. Reflex regenerated its existing web
lockfiles for the native form (`mergician`) and its 0.9.12 router template pins
(8.4.0). No bespoke JavaScript, chart library or new service was added.

The existing ignored `.web` cache initially failed with Windows `WinError 5`;
verification used a fresh ignored web/temp directory and a process-only Node PATH.
No global Node selection, cache ACL or user-owned directory was changed. See the
[terminal runbook](LOCAL_DEVELOPMENT_AND_SSH.md#stored-planning-view-two-terminals)
for setup, expected outputs, recovery and cleanup.

## Remaining work and next increment

Review this display with cases in the user's actual planning database, then publish
under user control and verify hosted checks for the published SHA. No new Odoo key
is required to view saved cases. Full T16 remains open: controlled case creation,
explicit scenario reruns and charts still need UI/acceptance. The next small
capability should submit an existing controlled input through the current create
route, retain its returned UUID, then run one explicit supplier outage and display
the immutable child. Preserve idempotency and uncertain-request handling.

Approval/PDF belongs to T17. Observed Odoo receipt/model promotion, production
identity management, Odoo writes and complete V2/system acceptance remain separate.
The accepted thesis baseline and V1 routes/snapshots are unchanged.

Thesis note: problem = terminal-only saved results; decision = reuse stored GET;
behavior = explainable immutable-case display; evidence = API/state/browser checks;
limitation = controlled retrieval, partial T16; relevance = architecture,
implementation and testing chapters (4/6/7).

## User frontend startup recovery — 2026-10-07

The user's normal root `.venv` run failed because its generated `.web` cache
was incomplete: `app/routes.js` and the generated Radix theme component were
absent. React Router reported its default `app/routes.ts` lookup; the subsequent
`psutil.NoSuchProcess` was cleanup after failure. Copying the installed template's
route file alone removed startup failure but exposed HTTP 500 for the other file.

The cache was preserved at ignored
`.artifacts/reflex-startup-a094f77c42a64d23b9f22244ab2bca90/web-before-repair/`, then
Reflex regenerated `frontend/.web`. With the user's existing Python 3.14.7,
Reflex 0.9.11.post1 and Node 24.20.0, development startup on isolated 3107/8207
passed; `/planning` returned HTTP 200 and rendered its form with no browser console
errors. The temporary processes were stopped. No application source/dependency,
tracked lockfile, Odoo data or stored planning case was changed by this recovery.
This is startup/rendering evidence only, not a new saved-case/database acceptance.
The runbook now describes cache recovery and explicit interpreter selection.

## User planning persistence recovery — 2026-10-07

After configuring the shared token, the user's live FastAPI returned HTTP 503 with
`planning_dependency_unavailable` while health returned 200. The ignored `.env`
had no `DECISION_DATABASE_URL`; the existing separate planning database container
was stopped. It was restarted without recreation/reset. PostgreSQL was healthy,
but Windows forwarding on 55432 still refused connections, so the documented
localhost-only SSH tunnel on 55433 was started. Its current helper PID is 14860;
stop it with `Stop-Process -Id 14860` when finished viewing these cases. A later
session can run the documented foreground SSH command instead; process IDs vary.

Only the empty database URL in `.env` was filled using the existing container's
credentials; other values were preserved and no credentials were printed. The
schema was already at `20261005_01`, and saved base
`cf86579d-0dd1-4837-b483-54fe982f15ad` remained present. A fresh in-process FastAPI
GET against actual PostgreSQL, followed by the frontend display mapper, verified
EUR 102/109 base plans and the EUR 106 outage minimum, parent lineage and EUR 4
delta. No model/Odoo reads, case creation, migration or resetting test was needed.
An initial diagnostic print hit Windows cp1252's unsupported approximation symbol;
the read-only comparison assertion then completed with safe ASCII output.

The existing live FastAPI process must be restarted to load the restored settings;
its post-restart browser result is pending user verification. The database and
tunnel are intentionally left running for that check. This extends local stored
API/PostgreSQL/display-mapping evidence, not hosted CI or a new live Odoo/browser
creation flow. The runbook now distinguishes missing token, unavailable persistence,
cached settings, stopped containers and the forwarding workaround.

### Post-restart stored display confirmation — 2026-10-07

The user confirmed the planning page works after restart. An independent live
authenticated GET returned 200 for `cf86579d-0dd1-4837-b483-54fe982f15ad`, with
`controlled_synthetic` input, `t14_synthetic` assessments, explicit controlled
business-term provenance and EUR 102 minimum cost. This completes the user's
stored-display check against the existing PostgreSQL database; the agent verified
the live API, while the browser result is user-confirmed.

The prior hybrid UUID `10eb4e39-2489-4c9c-af76-54dfb752930b` returned 404 in this
database. Its earlier report/acceptance remains historical evidence, not a currently
available stored case. No fresh Odoo read or new plan creation was performed. T16
remains partial: creation/scenario controls and charts are still open.
