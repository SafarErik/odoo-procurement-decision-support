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

## Controlled planning workspace: create and test

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

4. Choose **Create a demo plan**, then **Load demo inputs**. Read the supplier
   prices/capacities and policy. Keep demand **10**, then **Create and save plan**.
   Expect EUR 102 minimum and EUR 109 alternative (+7 EUR / approximately 6.9%).
   The allocation bars show quantities, not probabilities. Schedule classes and
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
python -m compileall application backend frontend decision_core odoo_adapter optimization_adapter supplier_evaluation persistence migrations
$taskRun = Join-Path ".artifacts" ("pytest-run-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $taskRun | Out-Null
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
