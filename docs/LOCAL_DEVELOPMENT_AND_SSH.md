# Local development: choose a task, then start its services

Use PowerShell at the repository root. This is the current terminal runbook;
[README](../README.md) owns current capability/status and [the documentation index](README.md)
links designs and historical evidence. Commands below explain their purpose and
expected result. Follow the scenario you need rather than starting the full stack.

## Which processes do I need?

There is one Podman Linux machine and two separate Compose projects. Separate
containers/projects are not separate Podman machines.

| Task | Needed processes | What it proves |
| --- | --- | --- |
| Fast tests, including T15 API | Python only | Business/API contracts; real saved ML/CBC; memory persistence where used |
| Offline ML/MILP demonstration | Python only | Synthetic training, saved reload/inference and allocation |
| PostgreSQL persistence acceptance | Python + disposable `decision-db` | Actual database round-trip, immutability, rollback and concurrency |
| Odoo/RFQ ledger or controlled live contracts | Odoo + its internal `db`; FastAPI/Reflex only for their flows | Documented read-only mappings or the existing RFQ UI |
| Manual T15 API inspection | FastAPI + own planning database + trusted saved model | Controlled HTTP planning/scenario/stored retrieval; Odoo/Reflex unnecessary |
| Stored planning view | FastAPI + database containing saved cases + Reflex | Recorded base/scenario display; no Odoo or configured ML model needed for GET |
| Saved human decision | FastAPI + migrated planning database + Reflex | Original-base approval/No-award and stored audit/retry; no Odoo, model or solver required |

The Odoo Compose project stores ERP data in named volumes. The planning-test project
is disposable and has no named volume. Its tests reset the schema. Keep them separate;
never reuse Odoo's PostgreSQL or a database containing saved application cases for
resetting tests. A persistent application database has not been packaged as a new
local Compose service; this consolidation adds no infrastructure.

## Activate Python and configure once

```powershell
Set-Location "$env:USERPROFILE\personal-projects\odoo-procurement-decision-support"
# Reuse the existing compatible environment; create only if it is absent.
$taskVenv = ".venv\t13-check"
if (-not (Test-Path "$taskVenv\Scripts\python.exe")) {
    py -3.11 -m venv $taskVenv
}
& "$taskVenv\Scripts\Activate.ps1"
python --version
python -m pip install -e ".[frontend,dev]"
```

Expect Python 3.11 and a successful editable installation with no missing dependency.
The older root `.venv` may use another Python version; do not overwrite it or mix
interpreters for saved artifacts. Reactivate this Python 3.11 environment in each
new terminal; installation is only needed initially or when dependencies change.
Reflex manages its web dependencies. Production frontend export additionally needs
the Node.js 22.22 toolchain documented in CI.

```powershell
# Preserve an existing .env; create it only on first setup.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set the values required for your selected task; the example documents each setting.
Generate separate local passwords with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Keep secrets in ignored `.env`. Backend settings load it; shell processes and
Alembic do not automatically load it. Process environment variables override backend
`.env` values. Never print real database URLs or keys into shared logs.

Existing Odoo users/fixtures do not need recreation. For missing business data or
permissions, follow the precise linked manual fixture procedures and confirm the
postconditions. Do not grant broad Purchase/Inventory roles as a shortcut.

## Python-only development loop

For a T15 change, the focused API tests exercise actual saved inference/CBC and
all five scenarios without external services:

```powershell
$taskRun = Join-Path ".artifacts" ("pytest-run-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $taskRun | Out-Null
python -m pytest tests/test_t15_planning_api.py -v --basetemp "$taskRun/temp" -o "cache_dir=$taskRun/cache"
```

Expect successful assertions. An HTTP `201` in a test means a case was stored in its
configured repository; the result status separately indicates optimality/infeasibility.
The fast API tests use an in-memory repository and do not prove real database storage.

To see the existing offline synthetic model and allocation demonstration:

```powershell
python -m supplier_evaluation.cli reproduce
```

This generates data, trains offline, saves/reloads, evaluates and solves. Outputs
stay in ignored `.artifacts/t14/`. The controlled allocation example has EUR 102
minimum cost and a EUR 109 lower-exposure alternative. Later `infer`/`demo` commands
reload the saved model without training. Synthetic accuracy is not real-world validity.

## Start Podman only for a service task

```powershell
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    $env:Path = "$env:LOCALAPPDATA\Programs\Podman;$env:Path"
}
podman machine list
# Run the next command only when the existing machine is stopped.
podman machine start podman-machine-default
$env:PODMAN_COMPOSE_PROVIDER = Join-Path $env:VIRTUAL_ENV "Scripts\podman-compose.exe"
podman compose version
```

Expect the existing Linux machine to be running and the project-local provider to
respond. Do not create another machine to run another Compose project. To run real
persistence tests, continue with the [persistence guide](PERSISTENCE_DEVELOPMENT.md);
no Odoo, separately served FastAPI or Reflex process is needed by those tests.

## Existing Odoo/RFQ UI: three terminals

In terminal 1, with Podman running and `.env` configured:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml up -d db odoo
podman compose --env-file .env -f infra/odoo/compose.yaml ps
podman compose --env-file .env -f infra/odoo/compose.yaml logs --tail=50 odoo
```

`up -d` starts/reuses the two containers in the background. `ps` shows status;
`logs` diagnoses startup. Expect healthy PostgreSQL and Odoo HTTP at port 8069
unless configured otherwise. Odoo's database is internal to Compose; the helper
must access Odoo's API rather than that database. Initial Odoo setup is manual;
see the [T0 handoff](T0_HANDOFF.md) and subsequent [T6 fixture/setup](T6_FIXTURE_SETUP.md)
for the validated integration scope, rather than creating arbitrary credentials.

In terminal 2, activate Python 3.11 as above and run:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

FastAPI serves the HTTP API; `--reload` restarts it after source edits. Use another
terminal for checks while this foreground process runs:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Expect `status: ok`. Health proves the API is running, not Odoo/model/database readiness.
OpenAPI is at <http://127.0.0.1:8000/docs>; RFQs are at
<http://127.0.0.1:8000/api/v1/procurement/rfqs>.

In terminal 3, activate the same environment:

```powershell
Push-Location frontend
reflex run
Pop-Location
```

Open the printed URL, normally <http://localhost:3000>. Reflex's state backend uses
8001 and calls FastAPI on 8000. The root page is the RFQ ledger; `/planning` is the
separate stored planning view below. Check RFQ rendering/refresh, stop FastAPI to inspect the error
state, then restart it and confirm recovery. Record browser evidence separately
from `reflex export --frontend-only --no-zip`, which checks compilation only.

For repeatable local Chromium acceptance of create/compare/approval/stored
reopening/PDF and real backend-unavailable recovery, use the
[#28 browser runbook](T18_28_BROWSER_RUNBOOK.md). It owns a separate disposable
helper database, frontend copy and service processes; it does not reuse/reset
this application database or your running frontend. Optional browser tooling is
required only for selected E2E; required Quality remains unchanged.

### Controlled live tests are explicit fixture acceptance

Use [T6 fixture setup](T6_FIXTURE_SETUP.md), [T7-S manual setup](T7S_MANUAL_SETUP.md)
and [T7 historical fixture](T7_FIXTURE_SETUP.md) only for their documented local
cases. The respective `RUN_T6_LIVE_CONTRACTS`, `RUN_T7S_LIVE_CONTRACTS` and
`RUN_T7_LIVE_CONTRACTS` settings opt into those gates. They are false by default.
Read-only credentials alone do not establish that the required fixture is present.

With the intended services/credentials/fixtures available, the existing complete
service selection is `python -m pytest -m "integration and not e2e" -v`.
It includes persistence and running-service tests; prepare their dependencies too.
A skipped live contract remains skipped, not accepted. Prefer the focused selection
for the behavior you changed instead of blindly enabling every live flag.

## Manual T15 API inspection

[The T15 handoff](T15_HANDOFF.md) defines the DTOs, token, model, migration and
expected results. [The persistence guide](PERSISTENCE_DEVELOPMENT.md) explains the
safe disposable-database sequence. This manual flow needs a configured own database
and `T12_TRUSTED_CALLER_TOKEN` plus an owner-generated `T15_TRUSTED_MODEL_DIRECTORY`.
Apply migrations explicitly before requests. HTTP never trains or migrates.

Follow the [T15 terminal demonstration](T15_DEMO.md) to generate a trusted model
and matched request files from a fresh checkout, then create a base, run an outage
and retrieve/replay saved cases. `python -m tools.t15_demo prepare` trains offline;
`run` only calls the existing loopback API. The tests share the same fixture generator.
Generated `.artifacts/t15-demo/` files stay ignored. Do not substitute current dates
or observed Odoo data into this controlled model.

## Stored planning view: two terminals

Prerequisite: activate Python 3.11 in each terminal and install `.[frontend,dev]`
after pulling this increment. The frontend extra includes SQLAlchemy asyncio
support (`greenlet`), which Reflex requires while converting event payloads.
Reuse a completed [T15 demonstration](T15_DEMO.md) and its database; do not reset
that database while viewing its cases. No new Podman machine or Compose project
is needed. If you have no saved cases, complete that linked procedure first.

For an existing saved-case database, the simplest shared configuration is the
ignored root `.env`: FastAPI reads `DECISION_DATABASE_URL` and
`T12_TRUSTED_CALLER_TOKEN`; Reflex reads the same token and `BACKEND_BASE_URL`.
When using these persistent local settings, no demo `caller-token.txt` is needed.
Clear stale process environment overrides before restarting the affected server.
FastAPI caches settings/database composition at startup; editing `.env` alone
does not refresh an already running process. A model is unnecessary for stored GET.

If the existing disposable demo container is stopped, reuse it with
`podman start procurement-decision-support-t11-test_decision-db_1` to preserve its
cases. Do not recreate it with new credentials or run resetting tests while viewing
those cases. A healthy database whose Windows port 55432 refuses connections still
needs the [localhost 55433 tunnel](PERSISTENCE_DEVELOPMENT.md#healthy-container-windows-host-port-refused).
Keep that tunnel running while `DECISION_DATABASE_URL` uses 55433. This is a
development demonstration database; it is not Odoo's internal PostgreSQL.

In terminal 1 retain the demo's `DECISION_DATABASE_URL` and shared token, then
serve the existing API. A configured model is unnecessary for stored GET:

```powershell
$env:T15_TRUSTED_MODEL_DIRECTORY = ""
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In terminal 2, from the repository root, load the same ignored temporary token
file that the synthetic demo created and find a completed report:

```powershell
$env:BACKEND_BASE_URL = "http://127.0.0.1:8000"
$env:T12_TRUSTED_CALLER_TOKEN = Get-Content .artifacts/t15-demo/caller-token.txt -Raw
$taskReportFile = Get-ChildItem .artifacts/t15-demo -Filter 'run-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$taskReport = Get-Content -LiteralPath $taskReportFile.FullName -Raw | ConvertFrom-Json
$taskReport.stored_retrieval_and_replay_verified
$taskReport.base.case_id
$taskReport.scenario.case_id
Push-Location frontend
reflex run --backend-host 127.0.0.1
Pop-Location
```

Expect the verification flag to be true; otherwise select an earlier completed
report. Reflex serves its web page on 3000 and state backend on 8001; its Python
HTTP client calls FastAPI on 8000. Open <http://localhost:3000/planning> directly
to avoid starting the RFQ page's Odoo refresh. The token stays on the Reflex
server, outside browser forms/state. This shared service credential is a local
PoC access boundary, not buyer authentication; keep this flow on loopback.

1. Paste the base UUID and press **Load stored case**. Expect EUR 102 minimum,
   EUR 109 alternative and the saved allocations. Expand the plan explanations,
   supplier tree paths, stored identity and field provenance.
2. Load the scenario UUID. Expect EUR 106 minimum, parent lineage and the recorded
   EUR 4 cost delta. These are stored comparisons, not new calculations.
3. Submit `not-a-uuid`, then a canonical UUID absent from this database. Expect
   validation/not-found messages, with previous results removed.
4. Stop FastAPI with Ctrl+C and submit a saved UUID. Expect an unavailable-service
   message. Restart FastAPI with the same database/token and load again; expect
   recovery. A model and live Odoo remain unnecessary for this retrieval.

For a completed hybrid Odoo demonstration, use its own token/report paths under
`.artifacts/t15-odoo-demo/` and the same database/backend configuration as that
run. Its base shows USD 1,850/2,200 and Supplier C's outage shows USD 2,200.
The source banner must retain **Odoo quotations; synthetic ML history**.
Historical validity is displayed as recorded and does not refresh ML scores.

Stop Reflex and FastAPI with Ctrl+C. Follow the existing demo cleanup for its
database/tunnel and temporary token. Remove process-only credentials from each
terminal with `Remove-Item Env:T12_TRUSTED_CALLER_TOKEN -ErrorAction SilentlyContinue`.
Keep saved reports until their evidence is no longer needed. This slice has no
case creation, scenario controls, charts, approval or PDF UI.

If an existing ignored `frontend/.web` cache fails with Windows `WinError 5`, stop
its processes and use a fresh ignored workdir rather than deleting another
execution identity's cache. From `frontend/`, before rerunning Reflex:

```powershell
$taskWebRun = Join-Path (Resolve-Path ../.artifacts).Path ("reflex-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path "$taskWebRun/temp" -Force | Out-Null
$env:REFLEX_WEB_WORKDIR = "$taskWebRun/web"
$env:TEMP = "$taskWebRun/temp"
$env:TMP = "$taskWebRun/temp"
$env:TMPDIR = "$taskWebRun/temp"
```

These settings affect this terminal only. Close it after stopping Reflex to
restore normal temporary-directory settings. Use a working installed Node.js
on its process PATH; CI remains on Node.js 22.22. Production export verifies
compilation only; [the T16 handoff](T16_HANDOFF.md) records actual browser scope.

## Controlled Odoo history path

This opt-in path uses only the completed `procurement_v2_history_test_v1` fixture:
company 1, product 54, unit 1, quotation group 2 and suppliers 51/52/53. No further
fixture entry or credential renewal is needed while the existing readers work.
See [the qualification and acceptance handoff](ODOO_HISTORY_INTEGRATION_HANDOFF.md).

Prerequisites: the existing Odoo service and test copy, the Python 3.11 environment,
a working Node runtime, and the already configured **separate helper PostgreSQL**
database at the current Alembic head. Use the existing
[persistence procedure](PERSISTENCE_DEVELOPMENT.md); never point helper migrations
or reset tests at Odoo. This increment adds no SQL migration. The owner database
was not migrated, reset or populated during implementation acceptance.

The prepared ignored `.env.v2-history-runtime` contains the dedicated clone reader,
fixed database, qualified model directory and library company scope. Original
`.env` and `.env.v2-history-test` remain unchanged. It adds only the history
configuration; ordinary restricted RFQ access, helper database URL and shared
service token still come from existing `.env`/process configuration. Never use an
administrator key. The original candidate artifact remains unchanged under
`.artifacts/t15-odoo-demo/model`; the separately qualified package is under
`.artifacts/v2-odoo-history-integration/qualified-model`.

From the repository root in the activated environment, start the API:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --env-file .env.v2-history-runtime
```

In another activated terminal, using the same existing service token, start Reflex:

```powershell
$env:BACKEND_BASE_URL = "http://127.0.0.1:8000"
Push-Location frontend
../.venv/t13-check/Scripts/reflex.exe run --backend-host 127.0.0.1
Pop-Location
```

Open `http://localhost:3000/planning`, then **Odoo -> Use history from Odoo**.
Expect 100.00%, 66.67%, 33.33%, three eligible completed purchase lines each and
model status `ready`. Review demand/terms and choose **Review Odoo terms ->
Calculate and save comparison**. Creation rereads quotations and history after
idempotency locking; preview does not freeze those sources for later creation.
Inspect Suppliers/Audit, run a scenario, return to the original base for deliberate
approval and open its PDF. The history is Odoo-acquired, with controlled synthetic
record origin; model training remains synthetic. Classes/allocations are the actual
saved tree/MILP output, not assigned by the UI. Existing separately synthetic
creation still requires its own original model configuration.

New interfaces (existing trusted-caller authentication applies):

- `GET /api/v2/procurement/planning-cases/odoo-history/local-v1` captures live bounded
  history and returns KPIs, feature times/references, profile revision and readiness.
- `POST /api/v2/procurement/planning-cases/from-odoo-history` accepts only
  `profile_id`, `profile_revision`, explicit `terms`/quotation expectations and
  optional `catalog_context`. It rejects caller receipt vectors/model paths.

Wrong source/context, missing/changed records or incompatible models reject new
creation. Reload a changed profile; preserve the exact pending request/key after
an uncertain network outcome. Reopening, exact replay, scenarios, approval and PDF
use saved evidence. Stop API/Reflex with Ctrl+C after use; leave owner Odoo/data,
existing helper records and qualified artifacts intact. Do not copy `.env*` files
or credentials into reports.

Optional bounded real-stack regression (owned disposable helper DB/processes only):

```powershell
$env:PODMAN_COMPOSE_PROVIDER = (Resolve-Path .venv/t13-check/Scripts/podman-compose.exe).Path
$env:RUN_ODOO_HISTORY_E2E = "true"
python -m pytest tests/e2e/test_odoo_history_browser.py -v
Remove-Item Env:RUN_ODOO_HISTORY_E2E
```

Put a working installed Node executable and the environment's `Scripts` on the
process PATH if required. The harness removes only its disposable helper project;
it never stops the owner Odoo service. Local verification used bundled Node
24.19.0 because the normal shim failed; CI's Node 22.22 baseline is unchanged.

## Controlled planning workspace: create and test

For the complete current acquisition -> scenarios -> human decision -> PDF flow,
use [the T17 reproduction guide](T17_FULL_FLOW_DEMO.md). It includes all five
stress types, No-award, stored reopening, failure recovery and cleanup. The dated
[full-flow handoff](T17_FULL_FLOW_HANDOFF.md) records the actual acceptance scope.

The 2026-10-07 next T16 slice adds creation and one supplier outage to `/planning`.
The earlier stored-only walkthrough remains valid for retrieval. This form reads
only the fixed owner-prepared `.artifacts/t15-demo/create-request.json` on the
Reflex server; it never accepts an artifact path or trains a model. Odoo is not
needed for synthetic creation, scenarios or stored GET.

1. Keep the existing planning database/tunnel running. Stop FastAPI before
   preparing the default demo, since preparation overwrites its local model/request
   files. From the repository root, prepare with the Python 3.11 baseline:

   ```powershell
   .\.venv\t13-check\Scripts\python.exe -m tools.t15_demo prepare
   ```

   This generates synthetic history and a compatible saved Decision Tree **offline**.
   It changes ignored demo artifacts only; it creates no database case. Keep the
   simulation cutoff/required date. A model prepared under another Python/numerical
   runtime can be rejected even though previously stored cases still load.

2. In the FastAPI terminal, opt in to that owner-generated model and start the API:

   ```powershell
   $env:T15_TRUSTED_MODEL_DIRECTORY = (Resolve-Path .artifacts/t15-demo/model).Path
   .\.venv\t13-check\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   The existing ignored `.env` supplies `DECISION_DATABASE_URL` and the shared
   `T12_TRUSTED_CALLER_TOKEN`. Preserve the database containing cases you want to
   keep; do not run resetting integration tests against it. This model setting is
   process-only. Stored GET and scenarios reuse saved assessments and need no model.

3. Restart Reflex in its existing frontend environment; keep one version against
   its generated cache. In the user's existing root frontend environment:

   ```powershell
   $env:BACKEND_BASE_URL = "http://127.0.0.1:8000"
   Push-Location frontend
   ../.venv/Scripts/reflex.exe run --backend-host 127.0.0.1
   Pop-Location
   ```

   Python 3.11 remains the backend/ML/CI compatibility baseline; this command reuses
   the user's already verified frontend-only environment. Open
   <http://localhost:3000/planning>. Both servers read the same service token from
the ignored root `.env`; clear stale process overrides before restarting.

4. Choose **Demo**, then **Load demo inputs**. Read the supplier
   prices/capacities and policy. Keep demand **10**, then **Review demo terms**.
   Inspect the exact review, then **Create and save plan**. Review saves nothing;
   **Edit terms** returns to the preserved draft. See [creation review](UX35_CREATION_RUNBOOK.md).
   Expect EUR 102 minimum and EUR 109 alternative (+7 EUR / approximately 6.9%).
   Aligned supplier rows show quantities, including zero allocations. Use
   **Select for review**, then **Review decision** to inspect the exact saved
   selection without finalizing. See [comparison instructions](UX36_COMPARISON_RUNBOOK.md).
   Schedule classes and
   exposure use synthetic saved-model evidence; exact fractions remain expandable.
   Copy the returned case ID. Creation saves a new immutable case in the database.

5. Under **Test a supplier outage**, choose **Demo supplier S226**, then
   **Run outage scenario**. Expect EUR 106 minimum, +4 EUR against the base, a new
   UUID and parent lineage. **View base case** reopens the EUR 102/109 result.
   Every outage is applied to the original base, not cumulatively to a child.
   Repeat stored loading with both IDs; it performs GET only. Demand **25** in a
   separately created demo has no feasible plan under this fixture's constraints;
   a recorded infeasible result is distinct from API/service failure.

6. If a POST response is interrupted or the API returns an uncertain error,
   **Retry the same request** resends the retained exact payload/idempotency key.
   No automatic retry occurs and changed inputs cannot replace pending intent.
   Keep the tab/server session alive. Expand **Request recovery record** and use
   **Copy exact request**, or select its read-only JSON manually, before leaving.
   Save the JSON locally if needed. It contains URL/payload/key, never the service
   token. Session recovery is a local PoC limit; there is no durable request queue.
   For a copied recovery file, confirm its URL is your loopback planning endpoint
   and restore that API at the same port. Then perform an explicit exact replay:

   ```powershell
   $taskRecovery = Get-Content -LiteralPath ./planning-request-recovery.json -Raw | ConvertFrom-Json
   $taskToken = (& .\.venv\t13-check\Scripts\python.exe -c "from backend.app.config import settings; print(settings.t12_trusted_caller_token.get_secret_value())").Trim()
   $taskBody = $taskRecovery.payload | ConvertTo-Json -Depth 100 -Compress
   Invoke-RestMethod -Uri $taskRecovery.url -Method Post -ContentType 'application/json' -Body $taskBody -Headers @{Authorization="Bearer $taskToken"; 'Idempotency-Key'=$taskRecovery.key}
   Remove-Variable taskToken
   ```

   Capture the token into the variable; do not print it or store it in the recovery
   file. HTTP 200 is exact replay of an existing case; HTTP 201 is first successful
   creation. Both return the saved UUID. Do not change payload/key during recovery.

Stop only the FastAPI/Reflex processes you started with Ctrl+C. Remove the
process-only model setting with
`Remove-Item Env:T15_TRUSTED_MODEL_DIRECTORY -ErrorAction SilentlyContinue`.
Follow the persistence guide for database/tunnel cleanup when finished. Keep saved
case IDs/evidence. No Odoo writes, approval or PDF are performed by this slice.

## Procurement cockpit: a short test with expected outcomes

Updated 2026-10-08 after usability feedback. The earlier walkthroughs below record
the preceding layout; the cockpit now uses **Saved case / Odoo / Demo** to start,
then **Plans / What-if / Suppliers / Audit** for the loaded result. Open the
in-app **What should I test?** guide in Practice for the same workflow. The current
Suppliers → Audit inspection is documented in [#39's runbook](UX39_EVIDENCE_RUNBOOK.md).

Start only FastAPI, Reflex and the planning PostgreSQL service for saved-case and
scenario testing. Odoo is needed for new Odoo case creation, not saved retrieval
or stress scenarios. Keep the Podman machine and any forwarding tunnel running.
If dependencies fail, use [the recovery checklist](#planning-data-unavailable-recover-the-local-stack).
There is no new setup command or infrastructure for this UI revision.
After switching to this revised source, restart Reflex from `frontend/` using
`reflex run` in your existing activated frontend environment, then reload the
browser. State/component module paths changed; reopening your saved case avoids
carrying an old browser session across that change. FastAPI needs no source restart
for this frontend revision. The fresh local case
`400a2b2f-7625-4876-a1e5-7f2eb7e255c7` has the same documented Q=200 result.

The existing controlled Odoo base case `e183f917-fc33-4e28-a7a8-0aea22679176`
can be reopened if it remains in your local planning database. A UUID is not a
fixture generator: if that case is absent, create a new case using the prepared
comparison procedure below. Expected amounts here apply to the documented fixture
(200 units, prices 10/12/9 USD, capacities 120/100/160, MOQ 50/100/150).

| Action | Where to look / expected result |
| --- | --- |
| Saved case: paste the base UUID and Load stored case | Plans shows USD 1,850 (Supplier 51: 50; Supplier 53: 150) and USD 2,200 (Supplier 51: 100; Supplier 52: 100). Each split totals 200. |
| Read the blue comparison sentence | The alternative adds USD 350 / 18.9% and reduces simulated exposure from 75.0 to 48.3, or 26.7 points. This is not a failure probability. |
| Audit: inspect saved inputs and policy | Check price, capacity, MOQ, dates, unit identity, maximum 2 suppliers, 80% share and 20% alternative allowance. Raw IDs and exact fractions remain available. |
| What-if: Capacity reduction, Supplier 52, enter 200 | Rejected: its original capacity is 100. The field requires a reduction; no case is created. |
| What-if: Capacity reduction, Supplier 53, enter 100 | New saved scenario: USD 2,200, allocations 100/100/0. Capacity below that supplier's MOQ makes it unusable; the original base remains unchanged. |
| What-if: Supplier outage, Supplier 53 | New scenario: USD 2,200 and allocations 100/100/0. |
| What-if: Demand increase, enter 220 | USD 2,040 minimum, allocations 60/0/160. Demand differs, so the total-cost change is not a like-for-like saving. |
| What-if: Price increase, Supplier 53, enter 11 | USD 2,150 minimum. The new price is a scenario assumption, not an updated Odoo quote. |
| What-if: Combined changes, Supplier 53, demand 220 and capacity 100; leave price blank | USD 2,400 minimum, allocations 120/100/0. Two changes are required. |
| What-if: Demand increase, enter 500 | Saved No feasible plan. No invented allocations, chart points or zero-valued cost/exposure. View the base again to recover the original comparison. |
| Copy a child case ID and reopen it through Saved case | Same costs, allocations and Audit snapshot hash. Viewing does not call Odoo, run the Decision Tree or solve MILP. |
| Suppliers: expand a classification path and the training explanation | Readable branch conditions lead to the saved class; Audit → Supplier tree paths and model evidence / Complete saved snapshot JSON retains exact float32 inputs, thresholds, support and versions. Histories are explicitly synthetic. |

Scenarios always start from the original base, including when viewing a child.
The draft shows assumptions before saving; it does not promise feasibility.
After saving, the comparison appears first in What-if. If a POST response is
uncertain, keep the tab open and use **Retry the same request**. Do not alter the
payload/key; copy its recovery record before leaving. Never reset this database
to troubleshoot a display error.

The Decision Tree uses generated prior on-time delivery rate and completed-receipt
count, trained offline. Its next-30-day label requires five complete future outcomes
and flags Schedule watch at two or more late deliveries. Separate supplier groups
and a time boundary prevent leakage across the controlled training/test split.
The leaf's class-1 training proportion becomes an uncalibrated score. MILP exposure
is `sum(allocated_quantity * saved_score) / demand`, shown on a 0–100 scale.
Mock receipts entered in Odoo still provide synthetic evidence. Observed training
requires documented extraction, cutoffs/availability, complete labels, compatible
model scope and held-out evaluation in a separate increment; it is not part of
this frontend test. Approval/PDF follows in T17. Drive synchronization follows
user acceptance and is not implied by repository documentation changes.

## Controlled Odoo planning workspace

Added 2026-10-08. This uses the prepared three-quotation comparison from T15,
not a general quotation selector. **Load prepared Odoo comparison** reads a fixed
local JSON preview; it does not refresh Odoo. **Review Odoo terms** also uses only
the prepared draft. **Create and save Odoo plan** after review calls
`POST /api/v2/procurement/planning-cases/from-odoo`; FastAPI independently reads
the comparison and currency, checks expectations, runs the matching saved model
and unchanged MILP, then saves an immutable snapshot. There are no Odoo writes.

Prerequisites: the existing Podman machine, running Odoo and a separate planning
database with migrations applied, working localhost forwarding, the existing
read-only Odoo key/database/URL, and the same server-side service token for FastAPI
and Reflex. Use the earlier service procedures and the persistence guide; do not
reset the database holding your saved cases. No new Odoo API key is required if
the existing read-only configuration works.

If both containers are healthy but Windows refuses 8069 and 55432, use one
foreground tunnel terminal for both services (only if local 8069/55433 are free):

```powershell
$taskMachine = (podman machine inspect podman-machine-default | ConvertFrom-Json)[0]
ssh.exe -i $taskMachine.SSHConfig.IdentityPath -p $taskMachine.SSHConfig.Port `
  -o BatchMode=yes -o ExitOnForwardFailure=yes -N `
  -L 127.0.0.1:8069:127.0.0.1:8069 -L 127.0.0.1:55433:127.0.0.1:55432 `
  "$($taskMachine.SSHConfig.RemoteUsername)@127.0.0.1"
```

Expected: the command stays running; Odoo is reachable at 8069 and the existing
planning database at 55433. `DECISION_DATABASE_URL` must use that local database
port. Ctrl+C closes this tunnel; it does not stop containers or remove records.

1. Stop FastAPI before re-preparing its model/request files. With Odoo reachable,
   from the repository root run:

   ```powershell
   .\.venv\t13-check\Scripts\python.exe -m tools.t15_odoo_demo prepare --group-id 2
   ```

   This reads the controlled development quotations and generates synthetic
   history plus a compatible Decision Tree **offline** under the ignored
   `.artifacts/t15-odoo-demo/`. It replaces that directory's prepared request/model
   files; preserve earlier artifacts first if you need their exact evidence.
   It does not create a case or modify Odoo. Group 2 is the verified T6 fixture:
   suppliers 51/52/53, prices 10/12/9 USD, product 54, company 1 and UoM 1.
   Preparation fails if the supported comparison assumptions no longer hold.

2. Select this comparison's matching model in the FastAPI terminal:

   ```powershell
   $env:T15_TRUSTED_MODEL_DIRECTORY = (Resolve-Path .artifacts/t15-odoo-demo/model).Path
   .\.venv\t13-check\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   Keep the existing ignored `.env` database and service-token settings. The API
   has one owner-configured model: this Odoo-domain model cannot create the pure
   synthetic-domain demo. Switch back to `.artifacts/t15-demo/model` and restart
   FastAPI for that form. Stored GET and scenarios need neither model nor Odoo.
   Do not rename history source types to bypass the compatibility gate.

3. Restart Reflex with the same shared service token and backend URL:

   ```powershell
   $env:BACKEND_BASE_URL = "http://127.0.0.1:8000"
   Push-Location frontend
   ../.venv/Scripts/reflex.exe run --backend-host 127.0.0.1
   Pop-Location
   ```

   Open <http://localhost:3000/planning>, choose **Odoo**, then
   **Load prepared Odoo comparison**. Inspect the captured prices/context and
   dates. Supplier IDs identify the prepared suppliers; display names are not
   acquired by this form. Never enter either API credential in the browser.

4. Review demand **200**, capacities **120/100/160**, MOQ **50/100/150**, and the
   generated required/promised dates. These are explicit controlled business
   terms, not Odoo stock or approved demand inferred from quotation quantities.
   Demand/MOQ accept integers 1–1,000; blank MOQ explicitly means none; capacity
   accepts 0–1,000. Required date must be today or later. Policy, availability,
   applicability ranges and synthetic history remain the prepared values.
   Click **Review Odoo terms** to inspect exact facts, explicit terms and policy
   without saving or refreshing Odoo. Then **Create and save Odoo plan**.
   Expect USD 1,850 with allocations 50/0/150,
   and USD 2,200 with allocations 100/100/0 (+350 USD, approximately 18.9%).
   Keep the case UUID. The source banner must say **Live Odoo quotations;
   synthetic ML history**. The ML assessments are not observed supplier evidence.

5. Select **odoo:res.partner:53** under **Unavailable supplier** and run the
   outage. Expect a new child UUID, USD 2,200 and +350 USD against the original
   base. **View base case** or **Open a saved case** returns USD 1,850/2,200
   without acquiring Odoo facts or refreshing scores. Editable terms change only
   new cases; saved base/scenario inputs remain immutable.

6. Changed quotation prices/context or unsupported terms return a safe rejection.
   Review the terms; re-prepare changed quotations offline, restart FastAPI with
   the matching model and reload the comparison before a new attempt. Nothing
   silently substitutes fresh prices. For an uncertain POST outcome, preserve
   the exact request/key and use the earlier **Retry the same request** procedure
   first. Do not replace pending intent with refreshed inputs.

Stop your FastAPI/Reflex/tunnel processes with Ctrl+C when finished; remove the
process-only model setting as above. Keep saved UUIDs/evidence and named volumes.
This demonstrates live quotation acquisition with synthetic ML history. Arbitrary
comparison discovery, observed receipt/model promotion,
approval/PDF and full V2 acceptance remain separate work.

## What-if scenarios and stored comparisons

Current update, 2026-10-12 (#37): **Saved scenario comparison** now retrieves the
original immutable result through the existing stored GET, rather than reconstructing
it from deltas as described in the historical walkthrough below. The original's
cost/exposure/allocations remain visible when the child has no proven plan. A fresh
child bookmark may need one additional original GET; failure keeps the child visible,
labels missing original cells **Unavailable**, and offers **Retry original-base
retrieval** without rerunning the scenario. Save/recovery focuses the comparison
and bookmarks `view=whatif`. **Return to original base** is explicit; children remain
analytical. The five-type composer is headed **Test changed assumptions. Save a new
scenario.** See the [current scenario procedure](UX37_SCENARIO_RUNBOOK.md) and
[dated verification](UX37_SCENARIO_HANDOFF.md). This update supersedes the comparison
display/recovery wording below; fixture inputs/results remain applicable.

Added 2026-10-08. Open a saved base or child at `/planning`. This requires only
Reflex, FastAPI, the existing planning database/tunnel and matching server-side
service token. No Odoo access, configured model or training is needed for scenario
creation or GET. A fresh base still needs its own documented preparation/creation.
Use the original 200-unit Odoo fixture base for the examples below; synthetic
cases use their own saved terms and will have different results.

The existing **Test a supplier outage** control remains. Under **Test other
what-if changes**, choose a scenario type. Supplier options show the **original
base** capacity and unit price, even when viewing a scenario. Every submission
targets that base, never a cumulative child. Each action saves a new immutable
UUID with parent lineage and reuses the base's recorded supplier assessments.

| Scenario type | Inputs and expected fixture result |
| --- | --- |
| Capacity reduction | Select `odoo:res.partner:53`, set **New capacity limit** to `100`, and press **Create and save scenario**. Expect USD 2,200, allocations 100/100/0 and +350 USD against the USD 1,850 base. |
| Demand increase | Set **New demand quantity** to `220`. Expect USD 2,040, allocations 60/0/160 and +190 USD. The comparison explicitly states that these totals cover different demand quantities; it is not a like-for-like saving. |
| Price increase | Select supplier 53, enter **New price per unit** `11.00`. Expect USD 2,150 and +300 USD. This is an explicit simulated unit price, not a changed Odoo quotation. |
| Combined changes | Select supplier 53, set demand `220` and capacity `100`; leave price blank. Expect USD 2,400, allocations 120/100/0 and +550 USD. Capacity/price apply to this one selected supplier; at least two of demand/capacity/price must change. |
| Infeasible demand | Choose demand increase and enter `500`. Expect **No feasible plan** with a saved UUID. The original base remains saved; cost/exposure/allocation comparisons are unavailable, not zero. |

Demand must strictly exceed original demand; capacity must strictly decrease;
price must strictly increase. Quantity inputs accept bounded whole numbers up to
1,000 (capacity can be zero); price uses plain decimal text, without exponent,
comma, currency symbol or binary float conversion. The backend independently
validates changes and model quantity applicability. For combined changes, leave
unused values blank; this UI does not implement arbitrary multi-supplier mixtures.

**Change from the base case** shows the recorded what-if assumptions, original
and scenario feasibility, demand, minimum total cost, exposure and per-supplier
quantity changes. Exact fractions/solver notes remain expandable. Cost/exposure
values for the base are reconstructed from the stored scenario minimum and exact
stored deltas; no optimization or scoring runs during display. When either result
lacks a proven minimum, unavailable comparison cells are labelled honestly; use
**View base case** for its full saved result. A solver failure is not shown as
proven infeasibility.

After each run, retain the UUID. Reopen it with **Open a saved case**, then use
**View base case** to confirm the base is unchanged. Scenario source wording must
say **Saved Odoo quotations with what-if changes; synthetic ML history** for a
hybrid case. Neither the simulated terms nor stored classifications claim a fresh
Odoo read or validated observed prediction.

Try demand `200`, capacity `160` for supplier 53, price `9`, or a combined form
with only one change. Expect validation errors and no new POST. For uncertain
service outcomes, preserve the exact URL/body/key and use **Retry the same
request**, as documented earlier. Changed intent stays blocked until recovery;
there is no automatic retry or durable recovery queue. Stop only your preview
processes/tunnel with Ctrl+C and retain database volumes/cases. No Odoo writes,
approval or PDF are performed.

## T16 final user validation

Added 2026-10-08. The controlled cockpit is implemented and locally accepted;
this short review checks the buyer-visible result before publication. Reuse your
running Odoo/planning database, FastAPI and Reflex, with the shared service token
and matching Odoo-domain model configured as above. No new Odoo records, API key,
training during requests or database reset is required. Refresh `/planning` after
the code change; restart your Reflex process if it has not recompiled.

1. **Create or reopen the Odoo base.** The default prepared Q=200 fixture gives
   USD 1,850 and USD 2,200. Alternatively open the fresh acceptance base
   `233b8b59-10cf-43ee-aaa0-61eef4a00a30` in the current local database; UUIDs are
   local evidence, not portable fixtures. For new creation, review captured
   expectations and all supplied business terms before saving.
2. **Compare the chart and plan cards.** The lower-cost point is USD 1,850 with
   exposure 75.0/100; the USD 2,200 point has exposure 48.3/100 and a +350 USD
   premium. The exposure scale is fixed 0–100, not a probability. Plot positions
   are approximate; the key/cards preserve exact decimal costs, and expandable
   solver notes preserve exact fractions. If all costs match, points sit centrally;
   coincident metrics can overlap, with every plan still listed in the key.
3. **Inspect the evidence.** Expand a supplier's tree explanation and **Audit
   details and sources**. Check saved price/capacity/MOQ/promised date/availability,
   quantity applicability, policy, model applicability and field sources. These
   are the saved case's inputs; scenario selectors separately show original base
   terms. The generated ML history must remain explicitly synthetic.
4. **Run the five scenarios** using the table above. Supplier C outage/capacity
   100 -> USD 2,200; demand 220 -> USD 2,040; C price 11.00 -> USD 2,150; combined
   demand 220 and C capacity 100 -> USD 2,400. A one-plan result says that no
   distinct alternative was found within the recorded allowances. A failed
   alternative search is described as incomplete, not proof that none exists.
5. **Check infeasibility and retrieval.** Demand 500 saves **No feasible plan**;
   it shows no fabricated chart or allocation. Copy the UUID, reopen it and use
   **View base case** to return to USD 1,850/2,200. Even from a child, every rerun
   starts from that original base; demand changes are not like-for-like savings.
6. **Check validation.** A combined form with only one change, unchanged capacity
   or price, or demand no higher than the base must be rejected. If a service
   failure occurs, follow the recovery procedure above; never change pending
   intent or generate a new key to recover an uncertain POST.

The pure synthetic form still gives EUR 102/109 at Q=10 when FastAPI is restarted
with its matching synthetic-domain model. One owner-configured domain at a time
is intentional. Stored GET/scenarios work across those domains without choosing
or loading a model in the browser. Your stored cases and Odoo volumes stay intact.
Stop only processes you started, retaining the Windows forwarding tunnel while
you continue testing. Approval/no-award/PDF, observed-model promotion and the full
visual redesign are later work. Drive synchronization follows your validation.

### Missing generated route configuration at Reflex startup

`Route config file not found at "app/routes.ts"` can indicate an incomplete
generated `.web` cache. Reflex supplies `app/routes.js`, which React Router also
accepts. Do not add an application `routes.ts` to conceal the missing generated
file. The later `psutil.NoSuchProcess` traceback is cleanup after frontend failure.

On 2026-10-07 the user's cache lacked both `app/routes.js` and a generated Radix
theme component. Restoring only the route file allowed startup but still produced
HTTP 500. Preserving the whole cache and letting Reflex initialize/compile a fresh
one fixed the page. The existing root `.venv` (Python 3.14.7 / Reflex 0.9.11.post1)
and Node 24.20.0 then served `/planning` with HTTP 200 and no browser console errors.
This frontend startup check does not change the Python 3.11 ML/CI baseline.

Stop your Reflex process with Ctrl+C first. From the repository root, preserve the
generated cache under ignored artifacts and start with one explicitly chosen
interpreter. For the documented Python 3.11 environment:

```powershell
$taskCache = (Resolve-Path -LiteralPath frontend/.web).Path
$taskCacheBackup = Join-Path (Resolve-Path .artifacts).Path ("reflex-web-backup-" + [guid]::NewGuid().ToString("N"))
Move-Item -LiteralPath $taskCache -Destination $taskCacheBackup
Push-Location frontend
../.venv/t13-check/Scripts/reflex.exe run --backend-host 127.0.0.1
Pop-Location
```

The move is reversible and affects generated web files, not application source or
Odoo/planning database records. Expected: initialization, compilation, then the
printed frontend/state-server URLs. Verify `/planning` renders, not just that
startup prints success. Avoid alternating Reflex versions against the same cache.
If using the existing root frontend environment instead, use
`../.venv/Scripts/reflex.exe` consistently; the two environments are distinct.

## Planning data unavailable: recover the local stack

Use this checklist when `/planning` says **Planning data is unavailable. Check the
FastAPI service and planning database.** Run commands from the repository root
in your normal PowerShell terminal. Existing `.env` credentials and saved cases
are reused; no new data, model training, migration or database reset is required.
The error is not proof that the database is unconfigured: a stopped Podman machine,
stopped database container or lost Windows forwarding can cause the same message.

### 1. Check FastAPI, then the existing Podman machine

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
$taskPodman = Join-Path $env:LOCALAPPDATA "Programs\Podman\podman.exe"
& $taskPodman machine list
$taskMachine = (& $taskPodman machine inspect podman-machine-default | ConvertFrom-Json)[0]
if ($taskMachine.State -eq "stopped") {
    & $taskPodman machine start podman-machine-default
}
& $taskPodman ps -a --format '{{.Names}} {{.Status}} {{.Ports}}'
```

Health `status: ok` proves only that FastAPI runs; it does not test PostgreSQL or
Odoo. If health cannot connect, start FastAPI using the earlier runbook section.
The explicit Podman path handles a normal Windows terminal without Podman on PATH;
use your installation path if it differs. Reuse `podman-machine-default`, never
initialize another machine to repair this error. A `win-sshproxy.exe failed to
start` warning can leave the machine working while Windows forwarding remains broken.

### 2. Start only the existing containers you need

If the planning container is shown as **Exited**, restore it without recreating it:

```powershell
& $taskPodman start procurement-decision-support-t11-test_decision-db_1
& $taskPodman exec procurement-decision-support-t11-test_decision-db_1 pg_isready -h 127.0.0.1 -p 5432
```

Expect **accepting connections**; if startup is still in progress, repeat the
readiness check after a few seconds. Stored retrieval needs this planning database,
FastAPI and Reflex; it needs neither Odoo nor a configured ML model. Despite its
historical `t11-test` name, this existing container currently holds manual demo
cases. Do not run resetting pytest fixtures against it or recreate/remove it.
If your container names differ, use the verified names from `podman ps -a`.

For new Odoo plans or the RFQ ledger, also start these existing containers if exited,
with Odoo's own database first:

```powershell
& $taskPodman start procurement-decision-support-t0_db_1
& $taskPodman start procurement-decision-support-t0_odoo_1
& $taskPodman machine ssh podman-machine-default 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8069/web/login'
```

Expect internal Odoo HTTP **200** once startup finishes. This is API-service
readiness, not direct access to Odoo's database.

### 3. Restore missing Windows localhost forwarding

```powershell
Test-NetConnection 127.0.0.1 -Port 55433 -InformationLevel Quiet
Test-NetConnection 127.0.0.1 -Port 8069 -InformationLevel Quiet
Get-NetTCPConnection -LocalPort 55433,8069 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,OwningProcess
```

For this local setup, the planning container publishes **55432 inside the Podman
machine**, and FastAPI's configured database URL uses **55433 on Windows**. The SSH
tunnel bridges them. If internal PostgreSQL is ready but Windows 55433 is false,
restore the tunnel below in a **separate terminal and leave that terminal open**.
If both ports are missing, this one command also restores Odoo on 8069:

```powershell
$taskPodman = Join-Path $env:LOCALAPPDATA "Programs\Podman\podman.exe"
$taskMachine = (& $taskPodman machine inspect podman-machine-default | ConvertFrom-Json)[0]
ssh.exe -i $taskMachine.SSHConfig.IdentityPath -p $taskMachine.SSHConfig.Port `
  -o ExitOnForwardFailure=yes -N `
  -L 127.0.0.1:55433:127.0.0.1:55432 `
  -L 127.0.0.1:8069:127.0.0.1:8069 `
  "$($taskMachine.SSHConfig.RemoteUsername)@127.0.0.1"
```

No prompt/output while SSH remains running is normal. Repeat the Windows port
checks from another terminal; expect **True**. If one port already works, omit
that port's `-L` line rather than starting a duplicate forward or killing its
listener. `ExitOnForwardFailure=yes` makes bind failures visible. The machine SSH
port/key are discovered dynamically, not copied from an old session.

**Keep Podman and the tunnel running for the entire application session.** Closing
the tunnel terminal, pressing Ctrl+C, stopping Podman or restarting Windows removes
the connection. Saved `.env` settings do not restart these processes. After a
restart, repeat this checklist. The tunnel is a localhost-only development
workaround; it does not repair Podman's Windows proxy. Do not broaden binds or use
`down --volumes`, resetting tests or database recreation as a connectivity fix.

### 4. Verify the actual saved-case request

Reload the same case in Reflex. To test FastAPI independently, capture the configured
token into a PowerShell variable without displaying it, then request a known saved
UUID from this database:

```powershell
$taskServiceToken = & .\.venv\t13-check\Scripts\python.exe -c "from backend.app.config import settings; print(settings.t12_trusted_caller_token.get_secret_value())"
$taskHeaders = @{Authorization = "Bearer $taskServiceToken"}
$taskCaseId = "e183f917-fc33-4e28-a7a8-0aea22679176"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/procurement/planning-cases/$taskCaseId" -Headers $taskHeaders |
    Select-Object case_id, parent_id
Remove-Variable taskServiceToken,taskHeaders
```

Expect **HTTP 200** and the matching case ID, then **Load stored case** should show
USD 1,850/2,200 for this fixture. Use your own saved UUID on another database.
**401/403** means a service-token mismatch; **404** means the case is absent from
the selected database; **503** or a timeout means inspect the backend dependency
error and configured database host/port. Editing `.env` requires restarting the
affected server; restoring a tunnel alone normally only requires another request.
Do not paste tokens into the browser or shared logs. Stop the foreground tunnel
with Ctrl+C only when finished testing.

Verified recurrence on 2026-10-08: FastAPI/Reflex were running, Podman and all three
existing containers were stopped, and Windows 8069/55433 had no listeners.
Starting those existing services and one localhost-only tunnel restored health,
RFQ and the selected stored-case requests to HTTP 200 without changing credentials
or saved data. See the dated [implementation log](IMPLEMENTATION_LOG.md).

## Saved human decision

Current update, 2026-10-13 (#38): **Saved plan for approval** and the separate
**Record No-award** action replace the combined selector below. Enter actor/reason
and acknowledgement, then **Review approval** or **Review No-award**. The exact
confirmation dialog writes nothing until **Confirm approval** or **Confirm
No-award**; Cancel/Escape retain entered values. Actions remain visible while the
review scrolls on narrow screens. Saved outcome/time/reason replace controls and
receive focus; pending finalizations retain the existing exact-request recovery.
The [current decision runbook](UX38_DECISION_RUNBOOK.md) supersedes historical
control names below; backend eligibility, immutability, reasons and PDF rules remain.

T17 issue #20 extends the existing `/planning` workspace. First activate the
Python 3.11 environment, apply current revision `20261010_01` to the intended helper
database as described in the [persistence guide](PERSISTENCE_DEVELOPMENT.md#apply-or-inspect-migrations),
and start the documented FastAPI/Reflex services with matching server-side
`T12_TRUSTED_CALLER_TOKEN`. This migration creates the separate final-decision
table; it preserves saved planning rows. Do not run resetting tests against this
application database. Odoo, a model artifact and CBC are unnecessary for deciding
or reopening an already stored case; new case creation retains its existing prerequisites.

1. Open `/planning`, enter a saved **original-base** UUID and choose **Load stored
   case**, then **Plans**. Check allocations, exact costs, supplier classes and
   saved dates. Scenario children explain their analytical restriction and have
   no finalization action; open their original base instead.
2. Use **Select for review** beside a saved plan, check its exact selection summary,
   then **Review decision** to focus **Record the final decision**. Selection alone
   saves nothing. The compatible selector also offers **Minimum cost**, a saved
   alternative, or **No-award**. There is no selected default. Enter **Actor audit
   reference**; enter **Reason** for an alternative or No-award. No-award is also
   available on a base with no proven plan.
3. Acknowledge the controlled demonstration and synthetic ML evidence, then
   choose **Finalize this base**. The decision is one-time. The entered actor is
   audit text, not authenticated buyer identity. A retained proven plan can be
   approved after later comparison failure; the limitation accompanies approval.
4. Expect the saved outcome, selected plan, reason and server UTC **Recorded at**.
   **Audit** contains the exact human decision and approved-content hash.
   Saved simulation dates are separate. Reopen the UUID and check the same values.
   Approval produces immutable content for the PDF below. No-award creates no
   approved document content.
5. On an uncertain save response, preserve **Recovery data** and use **Retry same
   request** explicitly. The pending payload and key remain unchanged and block
   replacement submission. If the response was lost after commit, retry recovers
   the original decision/time. Restoring connectivity does not justify a new key.
   Recovery JSON contains no service token. After losing the Reflex session,
   reopen the case UUID to inspect its saved outcome; JSON-based resubmission is
   a server-side HTTP operation, not a browser token entry flow.

Backend contract: `POST /api/v2/procurement/planning-cases/{case_id}/final-decision`
uses the existing trusted caller gate and a UUID `Idempotency-Key`, separate from
creation keys. Its JSON fields are `snapshot_hash`, `outcome` (`approve` or
`no_award`), `plan_index` (0 = minimum, 1.. = saved alternative; null for
No-award), `actor_reference`, optional/required `rationale` and
`demonstration_acknowledged: true`. No client timestamp is accepted. A new decision
returns 201, exact retry 200, conflicting decision/key 409, invalid intent or
scenario 422, missing case 404, unavailable/invalid persisted evidence 503.
GET and creation replay include the additive `final_decision` field.

Stop these foreground services with Ctrl+C when finished. Only migrate the
database you intentionally selected; no Odoo write/configuration is part of
this walkthrough. See [local acceptance evidence](T17_HANDOFF.md).

## Approved PDF view and download

Issue #21 uses the existing FastAPI/database/Reflex processes above. Refresh the
Python environment with `python -m pip install -e ".[frontend,dev]"` to install
the declared renderer and test extractor. Apply `alembic upgrade head` to the
intended helper database and confirm `20261010_01`; this adds the separate PDF
table and leaves existing cases/approvals unchanged. The database URL must be
exported for Alembic. Never select that application database for resetting tests.
Restart the servers after code/settings changes. Reflex installs its declared
React-PDF viewer/worker during compilation; use the documented Node.js 22.22
toolchain. There is no additional service or Odoo/model/solver prerequisite for
already approved content.

1. Load an **approved original base**, then open **Plans** or **Audit**. Its saved
   human outcome, selected plan and original UTC decision time remain visible.
   **Saved approved terms** retains product/demand, required date, exact cost and
   supplier quantities/promised dates even while document access is unavailable.
2. Choose **View approved PDF**. FastAPI validates the saved content and either
   atomically stores its first rendered artifact or serves the existing one.
   Expect the document pages and **Download approved PDF** link. The viewer
   displays backend PDF bytes, with selectable text; it generates no document.
3. Check product/demand, saved dates, exact selected allocation/prices/cost,
   simulation label and actor/reason. Supporting source/model/policy references
   and exact case/content hashes follow. The document approves only the original
   base; stress results are analytical. An incomplete comparison warning appears
   when later calculations failed after the selected plan was proven.
4. **Previous PDF page** and **Next PDF page** show one page at a time with an
   announced page indicator and disabled end controls. Use keyboard focus/Enter.
   Use **PDF zoom** for fit-width, 150%, 200% or 300% viewing. The document region
   scrolls independently, including horizontal scrolling when zoomed. It is
   keyboard-focusable; Page Up/Down and arrow keys navigate. Mobile layout retains
   the download/zoom controls without expanding the whole page horizontally.
5. Choose the **Download approved PDF** link to save the exact displayed bytes.
   The safe filename contains case UUID and approved-content hash prefix. This
   explicit browser link avoids depending on a scripted download or native PDF
   plugin. The service token remains on the Reflex server and is absent from
   document URLs, browser state and the file.
6. On **PDF unavailable**, the saved approval stays visible. Restore the backend
   or renderer dependency, then choose **Retry approved PDF** explicitly.
   **Document identity for support** exposes the original case/content hash.
   Do not finalize again or replace its key/content. No-award, unapproved bases
   and stress children have no approved-PDF action and are rejected by the API.

See [#40 recovery/document procedures](UX40_RECOVERY_RUNBOOK.md) for distinct
rejection/conflict/uncertainty, exact explicit retry and session-loss limits.

Backend contract:
`GET /api/v2/procurement/planning-cases/{case_id}/approved-pdf/{approved_content_hash}`
uses the existing trusted caller gate. Default delivery is `inline`;
`?download=true` returns an `attachment`. Headers identify approved content
version/hash, stable PDF reference and binary SHA-256. Unknown case = 404,
ineligible/invalid identity = 422, mismatched approved-content hash = 409,
unavailable rendering/storage = sanitized 503. Rendering failure stores no
partial artifact. Existing PDF retrieval needs no renderer execution.

The bundled font covers verified Latin/Hungarian, Greek and Cyrillic examples.
Unsupported glyphs fail safely; arbitrary scripts/emoji are not promised. The
artifact is bounded to 2 MiB. Simulation evidence, dates and non-authenticated
actor attribution remain explicit; this is not a legally complete external
Purchase Order. See [closed spike](T17_PDF_SPIKE.md) and
[PDF acceptance evidence](T17_PDF_HANDOFF.md).

## Windows forwarding troubleshooting and cleanup

If the service is healthy in Podman but Windows localhost refuses a connection,
first check the relevant logs and host port. This is a known forwarding issue;
starting duplicate containers or broadening bind addresses does not resolve it.
The persistence guide shows the 55432 -> 55433 localhost tunnel. For default Odoo
port 8069, in a separate foreground terminal:

```powershell
$machine = (podman machine inspect podman-machine-default | ConvertFrom-Json)[0]
ssh.exe -i $machine.SSHConfig.IdentityPath -p $machine.SSHConfig.Port -N `
  -L 127.0.0.1:8069:127.0.0.1:8069 `
  "$($machine.SSHConfig.RemoteUsername)@127.0.0.1"
```

Use an unused local port if 8069 is occupied and update the client URL accordingly.
The tunnel stays alive until Ctrl+C; it is a workaround, not a repaired Podman proxy.

Stop foreground FastAPI, Reflex and any tunnel with Ctrl+C. Stop just the Odoo
project while retaining named volumes:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml down
```

For test-database shutdown, use its separate command in the persistence guide.
Do not use `down --volumes` against the Odoo project during testing.

## Required checks before handoff

```powershell
ruff format --check .
ruff check .
python -m compileall application backend frontend decision_core odoo_adapter optimization_adapter document_adapter supplier_evaluation persistence migrations
$taskRun = Join-Path ".artifacts" ("pytest-run-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path "$taskRun/cache" -Force | Out-Null
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
# CBC needs a temp path without spaces; resolve this owned directory's Windows short path.
$taskAbsoluteRun = (Resolve-Path $taskRun).Path
$taskShortTemp = @'
import ctypes, sys
buffer = ctypes.create_unicode_buffer(32768)
assert ctypes.windll.kernel32.GetShortPathNameW(sys.argv[1], buffer, len(buffer))
assert " " not in buffer.value, "Choose a writable temp directory without spaces."
print(buffer.value)
'@ | python -X utf8 - "$taskAbsoluteRun"
if ($LASTEXITCODE -ne 0) { throw "A space-free CBC temp path is required." }
$env:TEMP = $taskShortTemp
$env:TMP = $taskShortTemp
python -m pytest -m "not integration and not e2e" -v --basetemp "$taskRun/temp" -o "cache_dir=$taskRun/cache"
python -m pip check
git diff --check
```

These check formatting, lint, compilable source, fast regressions, installed
dependency consistency and patch whitespace. Actual ML/CBC execution is required;
missing runtimes fail. Run this selection once before handoff and repeat only after
relevant changes or unresolved failures. Python compilation is not a static type check.

The fresh ignored pytest folders avoid Windows ownership conflicts between your
terminal and an agent execution identity. Generate a new `$taskRun` for each run;
pytest clears its `--basetemp` directory. See the persistence guide's
[permission-error explanation](PERSISTENCE_DEVELOPMENT.md#windows-permissionerror-winerror-5-during-fixture-setup)
if fixture setup fails under the shared Windows temporary directory.

The UTF-8 settings also let evaluation metadata read a Unicode working-tree diff
without Windows cp1252 decoding failures. These are current-terminal settings, not
global configuration. Use the same space-free TEMP/TMP for browser tests; restore
your previous values or close this terminal after checking and preserving evidence.

When Compose configuration changed, or a service handoff needs configuration validation:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet
podman compose --env-file .env -f infra/persistence/compose.test.yaml config --quiet
```

For the latter set a synthetic `T11_POSTGRES_PASSWORD` as in the persistence guide.
These commands validate configuration only, start no services, and suppress expanded
configuration/secrets. Quality CI runs for pull requests, main pushes and manual
runs; a feature-branch push alone does not trigger that workflow. Container/API CI
is separately path-filtered. Local success does not establish hosted success.

## Cache the GitHub SSH key across restarts

Keep the private key passphrase. The safer solution is to let the Windows OpenSSH
agent store and provide the unlocked key. This repository currently uses the SSH
host alias `github.com-safarerik`.

### One-time setup

Open **PowerShell as Administrator** and configure the Windows agent service:

```powershell
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
Get-Service ssh-agent
```

Close the administrator terminal. In a normal PowerShell window, force Git for
Windows to use the same Windows OpenSSH client as that service:

```powershell
git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
```

This applies to all repositories for the current Windows account. If another
repository deliberately requires a different SSH implementation, use `--local`
instead of `--global` while inside this repository.

Add the existing key. This should ask for its passphrase once:

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" `
    "$env:USERPROFILE\.ssh\id_ed25519_safarerik"
```

Confirm that the agent and GitHub authentication work:

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" -l
ssh -T github.com-safarerik
```

GitHub normally answers that authentication succeeded but shell access is not
provided. That message is expected.

### Quick check after a later restart

```powershell
Get-Service ssh-agent
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" -l
git config --global --get core.sshCommand
ssh -T github.com-safarerik
```

If the agent is running and lists the key, `git pull` and `git push` should not ask
for the passphrase again. If the agent has no identities, add the key again with the
earlier `ssh-add` command. If the key is listed but Git still prompts, verify that
`core.sshCommand` points to `C:/Windows/System32/OpenSSH/ssh.exe`; Git for Windows
may otherwise use a separate bundled SSH agent.

Do not remove the key's passphrase and never commit a private key. To remove this
key from the agent deliberately:

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" -d `
    "$env:USERPROFILE\.ssh\id_ed25519_safarerik"
```

References:

- [Microsoft: Key-based authentication in OpenSSH for Windows](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement)
- [GitHub: Generating an SSH key and resolving Windows agent conflicts](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent?platform=windows)
