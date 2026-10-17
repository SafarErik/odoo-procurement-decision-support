# T15 terminal demonstration: create, disrupt, retrieve

This procedure demonstrates the existing controlled planning API using a generated
synthetic model and matched inputs. It uses Python, one Podman machine, the existing
disposable PostgreSQL service and FastAPI. Odoo and Reflex are unnecessary for this
controlled slice. It does not establish the complete Odoo/model or buyer-facing V2
workflow. Start from the repository root with Python 3.11 activated using the
[terminal runbook](LOCAL_DEVELOPMENT_AND_SSH.md).

## What you will see

The demand is 10 units of one synthetic product. At most two suppliers may be used,
and one supplier may cover at most 80%. The Decision Tree supplies an exposure
proxy; the MILP decides quantities. Prices, capacities, commercial validity and
policy remain explicit inputs, not outputs invented by ML.

| Plan | Quantities for fixture suppliers A / B / C | Cost | Meaning |
| --- | --- | --- | --- |
| Base minimum | 6 / 4 / 0 | EUR 102 | Cheapest valid allocation |
| Base alternative | 0 / 2 / 8 | EUR 109 | Lower exposure within the explicit 10% cost allowance |
| Supplier A unavailable | 0 / 8 / 2 | EUR 106 | Cheapest allocation after the disruption |

A/B/C refer to the supplier order in the generated request; the actual stable
supplier IDs are printed by the tool. Model scores are uncalibrated synthetic
exposure proxies. These figures are a reproducible technical example, not an
operational purchasing recommendation or evidence of predictive superiority.

## 1. Prepare matched inputs and the saved model offline

```powershell
python -m tools.t15_demo prepare
```

Expected: the tool creates `.artifacts/t15-demo/model/`, `create-request.json`
and `scenario-request.json`, then prints the synthetic simulation cutoff.
Preparation trains/saves outside HTTP, reusing the existing T14 pipeline. HTTP
requests later only reload/infer. The fixture generator is shared with the existing
T15 tests, so there is one source for the example.

Inspect the business inputs rather than reading all receipt evidence at once:

```powershell
$taskInput = Get-Content .artifacts/t15-demo/create-request.json -Raw | ConvertFrom-Json
$taskInput.requirement
$taskInput.policy
$taskInput.suppliers | Select-Object supplier_id, unit_price, capacity, available
```

Keep the generated `as_of` and required date for the reference example. Changing
only the date to today does not make the model operationally current. The files
and executable model are ignored local artifacts; use only your own generated
model. `prepare` overwrites its model/request files, so stop the backend before
regenerating them. The tool runs from this repository; it is not a deployment CLI.

## 2. Prepare the disposable database in terminal 1

Follow steps 1 and 2 of [the persistence guide](PERSISTENCE_DEVELOPMENT.md) in
this same terminal. Start/check the database, set `T11_TEST_DATABASE_URL` and run
the focused PostgreSQL acceptance if validating the implementation. Its resetting
tests must finish before manual API use. If the Windows port fails, follow the
guide's localhost-only tunnel procedure in another terminal; keep it running.

The following manual run will create durable cases in that disposable database.
Do not point resetting tests at a database containing cases you want to keep.
No new Podman machine or Compose service is needed.

## 3. Configure and serve FastAPI in terminal 1

After preparation/tests, with the test URL still exported in this terminal:

```powershell
$env:DECISION_DATABASE_URL = $env:T11_TEST_DATABASE_URL
$env:T15_TRUSTED_MODEL_DIRECTORY = (Resolve-Path .artifacts/t15-demo/model).Path
$env:T12_TRUSTED_CALLER_TOKEN = [guid]::NewGuid().ToString("N")
# A temporary ignored local file lets terminal 2 use the same token without printing it.
Set-Content -LiteralPath .artifacts/t15-demo/caller-token.txt -Value $env:T12_TRUSTED_CALLER_TOKEN -NoNewline
python -m alembic upgrade head
python -m alembic current
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Expected: Alembic reports `20261005_01`, then Uvicorn listens on localhost:8000.
Requests/startup do not migrate. The environment values override backend `.env`
without editing it. The bearer token proves possession only, not a buyer identity.
Uvicorn occupies this terminal until Ctrl+C. No reload watcher is needed for the demo.

## 4. Create the base and disruption from terminal 2

Open another PowerShell terminal at the repository root and activate the same
Python 3.11 environment. Load the temporary token and run:

```powershell
$env:T12_TRUSTED_CALLER_TOKEN = Get-Content .artifacts/t15-demo/caller-token.txt -Raw
python -m tools.t15_demo run
```

Expected: the printed base minimum/alternative and outage minimum match the table.
The tool POSTs a base (`201`) and an immutable scenario child (`201`), GETs both
(`200`), then repeats the base POST with its original key (`200`). It checks that
the retrieved cases and replayed base retain their saved snapshot/hash and that
the child references the base. The parent remains unchanged.

A unique `.artifacts/t15-demo/run-<base-key>.json` contains the original replay
keys, complete base/child responses and successful verification flag. It does not
contain the bearer token. The replay keys are saved before the first POST and
responses are saved as received, so a partial run remains inspectable. The CLI
performs no automatic POST retry; a rerun uses new keys and creates another pair.
Do not mistake an interrupted request for proof that no case was stored.

Inspect the latest completed record:

```powershell
$taskReportFile = Get-ChildItem .artifacts/t15-demo -Filter 'run-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$taskReport = Get-Content -LiteralPath $taskReportFile.FullName -Raw | ConvertFrom-Json
$taskReport.base.snapshot.result.minimum_cost_plan
$taskReport.scenario.snapshot.comparison
$taskReport.stored_retrieval_and_replay_verified
```

Expect a recorded cost delta of EUR 4 for the outage minimum and a true verification
flag. Full tree paths, source attribution and solver/model identity are retained
in each snapshot. Source IDs describe synthetic evidence, not real Odoo suppliers.

## 5. Retrieve after restarting the backend without a configured model

In terminal 1, stop Uvicorn with Ctrl+C. Keep the database running, then:

```powershell
$env:T15_TRUSTED_MODEL_DIRECTORY = ""
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In terminal 2, retaining the loaded token/report:

```powershell
$taskHeaders = @{Authorization = "Bearer $env:T12_TRUSTED_CALLER_TOKEN"}
$taskStored = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/procurement/planning-cases/$($taskReport.base.case_id)" -Headers $taskHeaders
$taskStored.snapshot_hash -eq $taskReport.base.snapshot_hash
```

Expect HTTP 200 and `True`, even though the backend has no configured model for
new bases. This exercises stored retrieval across a process restart. Existing
regression tests additionally trap assembly/inference/solver calls during GET and
exact replay. To create another base, stop/restart Uvicorn with the model setting
restored to the generated directory; rerunning the demo while it is blank gives 503.

<a id="controlled-odoo-quotation-demo"></a>

## Controlled live Odoo quotation variant — 2026-10-07

This alternative reads the existing T6 comparison fixture and independently
rechecks it on the backend. It uses **synthetic ML history**, never the unrelated
T7 receipts. No Odoo record changes are needed. Keep Odoo running with the working
read-only `ODOO_API_KEY` in ignored `.env`; Reflex remains unnecessary.

Skip the pure-synthetic preparation above. In terminal 1, with Python 3.11 active:

```powershell
python -m tools.t15_odoo_demo prepare --group-id 2
```

Expected: `.artifacts/t15-odoo-demo/` contains a newly trained/saved synthetic
model and dataset scoped to the quotation domain, a matched request and C-outage
delta. This is offline preparation, not observed-model training or prediction.
Review `create-request.json` → `controlled_input`: Q=200, capacities 120/100/160,
hard MOQ 50/100/150, max suppliers 2, concentration 80%, epsilon 20%, controlled
price/delivery bounds and promise. Quotation Q=100 is not treated as approved Q.
Generated history references explicitly identify the simulated profiles.

Follow section 2 for the existing disposable database and exported test URL. Finish
resetting tests before manual API use. Stop any earlier demo backend, then configure
terminal 1 with this variant's artifact and token location:

```powershell
$env:DECISION_DATABASE_URL = $env:T11_TEST_DATABASE_URL
$env:T15_TRUSTED_MODEL_DIRECTORY = (Resolve-Path .artifacts/t15-odoo-demo/model).Path
$env:T12_TRUSTED_CALLER_TOKEN = [guid]::NewGuid().ToString("N")
Set-Content -LiteralPath .artifacts/t15-odoo-demo/caller-token.txt -Value $env:T12_TRUSTED_CALLER_TOKEN -NoNewline
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In terminal 2, at the repository root with the same Python environment:

```powershell
$env:T12_TRUSTED_CALLER_TOKEN = Get-Content .artifacts/t15-odoo-demo/caller-token.txt -Raw
python -m tools.t15_odoo_demo run
$taskReportFile = Get-ChildItem .artifacts/t15-odoo-demo -Filter 'run-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$taskReport = Get-Content -LiteralPath $taskReportFile.FullName -Raw | ConvertFrom-Json
```

Expected: USD 1,850 minimum (A/B/C=50/0/150), USD 2,200 lower-exposure alternative
(100/100/0), and USD 2,200 after C's outage. The API POSTs to `/from-odoo` for the
base and reuses the existing scenario/GET routes. Stored provenance distinguishes
`odoo_json2` price/context, controlled terms and `t14_synthetic` ML evidence.
If Odoo prices/context changed, the new request is rejected; stop the backend and
prepare again after reviewing the change. Never edit model metadata to force a match.

The run record and restart procedure from sections 4/5 also apply, using this
variant's directory. Exact base retry uses the **same `/from-odoo` request and key**;
it does not re-read Odoo. GET and scenario replay need neither Odoo nor the model.
Fresh base creation does. The source/model compatibility of actual Odoo receipts
remains open; this demonstration establishes the chosen controlled integration.
During cleanup also remove `.artifacts/t15-odoo-demo/caller-token.txt`:

```powershell
Remove-Item -LiteralPath .artifacts/t15-odoo-demo/caller-token.txt -ErrorAction SilentlyContinue
```

## Failure interpretation and cleanup

| Symptom | Check |
| --- | --- |
| Connection refused | Backend process/port; for PostgreSQL, service health and Windows forwarding |
| HTTP 401 | Same bearer token exported to both terminals |
| HTTP 422 | Matching generated payload/model and simulation date; explicit terms and validity |
| HTTP 503 | Database/schema, configured artifact/runtime, or unconfigured bearer gate |
| CLI incomplete | Inspect the run record and API logs; no automatic POST retry occurred |
| Pytest WinError 5 in temporary model setup | Use the fresh per-run temp/cache paths in the [persistence guide](PERSISTENCE_DEVELOPMENT.md#windows-permissionerror-winerror-5-during-fixture-setup) |

Use `--base-url http://127.0.0.1:<port>` for another loopback API port. Redirects
are not followed and remote/credentialed URL origins are rejected. Never paste
real credentials into shared output. OpenAPI remains available at
<http://127.0.0.1:8000/docs> for optional inspection of the existing API.

Stop Uvicorn and any SSH tunnel with Ctrl+C. Use the persistence guide's separate
`down` command for the disposable database; keep the user's Odoo stack unchanged.
In each relevant terminal remove temporary process settings; remove the token file:

```powershell
Remove-Item Env:T12_TRUSTED_CALLER_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:T15_TRUSTED_MODEL_DIRECTORY -ErrorAction SilentlyContinue
Remove-Item Env:DECISION_DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item .artifacts/t15-demo/caller-token.txt -ErrorAction SilentlyContinue
```

Generated request/model/run files stay ignored for local review. The snapshots
are immutable database records; the exported local files are review copies.
The development agent leaves code/docs unstaged for user review and does not publish
or merge. Hosted CI and Drive synchronization are separate later steps.
