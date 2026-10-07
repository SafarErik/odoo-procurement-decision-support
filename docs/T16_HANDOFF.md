# T16: controlled procurement workspace

## Current status — 2026-10-07, creation / outage / UX increment

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
