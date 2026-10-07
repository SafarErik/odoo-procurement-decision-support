# Planning persistence: isolated PostgreSQL tests and explicit migrations

This is the current T11/T12/T15 database runbook. Use the existing Podman machine
and the separate Compose project `procurement-decision-support-t11-test` from
`infra/persistence/compose.test.yaml`. The historical T11 name remains to avoid
changing infrastructure; this service now tests both V1 decisions and V2 planning.
Start with [the terminal runbook](LOCAL_DEVELOPMENT_AND_SSH.md) to activate Python
3.11 and select the Compose provider. Odoo and a separately running backend/frontend
are unnecessary for these database tests.

## Why this database is separate

The test fixtures run `alembic downgrade base`, `alembic upgrade head` and truncate
case tables. **Use only this disposable database, never an Odoo, application,
shared or production-like database.** Tests do not mutate Odoo or need its credentials.
The service binds to localhost and has no named volume: removing/recreating its
container discards its test data. The Odoo Compose project's named volumes are
separate and must not be removed as part of persistence testing.

| Setting | Responsibility |
| --- | --- |
| `T11_POSTGRES_*` | Container test database/user/password and exposed port |
| `T11_TEST_DATABASE_URL` | PostgreSQL pytest fixture; read from the process environment |
| `DECISION_DATABASE_URL` | Backend persistence and explicit Alembic migration URL |
| `T12_TRUSTED_CALLER_TOKEN` | PoC bearer gate for V1 stored-case and V2 planning routes |
| `T15_TRUSTED_MODEL_DIRECTORY` | Owner-generated trusted saved ML artifact for new V2 base cases |

The names are inherited from earlier increments. Do not rename settings just for
cosmetics. Backend configuration loads `.env`; pytest's database fixture and
Alembic need an exported URL. The tests configure their own controlled token,
model and API composition, so you need not configure those to run them.

## 1. Start the disposable database

In an activated Python 3.11 PowerShell terminal at the repository root, after
starting Podman as described in the terminal runbook:

```powershell
$env:T11_POSTGRES_DB = "decision_cases_test"
$env:T11_POSTGRES_USER = "t11_test"
$env:T11_POSTGRES_PASSWORD = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:T11_POSTGRES_PORT = "55432"

podman compose -f infra/persistence/compose.test.yaml up -d
podman compose -f infra/persistence/compose.test.yaml ps
```

`up -d` starts/reuses the background test service. New credentials can recreate it;
do not run this setup while preserving a manual test case or while tests are running.
Wait for `decision-db` to show `healthy`; inspect startup if necessary:

```powershell
podman compose -f infra/persistence/compose.test.yaml logs --tail=50 decision-db
Test-NetConnection 127.0.0.1 -Port 55432
```

Expect PostgreSQL ready for connections and `TcpTestSucceeded: True`. In this same
terminal, set the URL without printing it:

```powershell
$env:T11_TEST_DATABASE_URL = `
  "postgresql+psycopg://t11_test:$env:T11_POSTGRES_PASSWORD@127.0.0.1:55432/decision_cases_test"
```

If you use another terminal, re-establish the same environment values there; shell
environment variables are not shared between existing terminal processes.

### Healthy container, Windows host port refused

Keep the credentials above. In a second terminal, run the temporary forwarding
workaround using an unused host port (55433 here):

```powershell
$machine = (podman machine inspect podman-machine-default | ConvertFrom-Json)[0]
ssh.exe -i $machine.SSHConfig.IdentityPath -p $machine.SSHConfig.Port -N `
  -L 127.0.0.1:55433:127.0.0.1:55432 `
  "$($machine.SSHConfig.RemoteUsername)@127.0.0.1"
```

The tunnel occupies that terminal until Ctrl+C. In the original test terminal:

```powershell
Test-NetConnection 127.0.0.1 -Port 55433
$env:T11_TEST_DATABASE_URL = `
  "postgresql+psycopg://t11_test:$env:T11_POSTGRES_PASSWORD@127.0.0.1:55433/decision_cases_test"
```

Expect the host port to respond. The existing container and credentials are reused;
no additional Podman machine/database is needed. This is a documented workaround,
not a resolved Windows forwarding defect. Do not expose the service beyond localhost.

## 2. Run the database acceptance tests

```powershell
$taskRun = Join-Path ".artifacts" ("pytest-run-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $taskRun | Out-Null
python -m pytest tests/integration/test_t15_planning_postgres.py tests/integration/test_decision_case_postgres.py -v --basetemp "$taskRun/temp" -o "cache_dir=$taskRun/cache"
```

The fixtures create/reset the schema themselves. Expect tests to execute and pass;
`T11_TEST_DATABASE_URL is not set` skips mean configuration is missing, not acceptance.
The checks cover actual FastAPI-to-PostgreSQL round-trip, stored-only GET/replay,
V1 compatibility, immutable snapshots/keys, concurrent compute-once creation,
conflicting reuse and atomic rollback. Real controlled inference/CBC are exercised.
The initial T15 implementation recorded 21 passing database tests; newer execution
results belong to their own dated log entry rather than overwriting that evidence.

Do not run resetting tests concurrently with manual API experimentation. An API
TestClient is used within pytest; there is no need to start Uvicorn for this selection.

### Windows `PermissionError: [WinError 5]` during fixture setup

If the traceback points into `%LOCALAPPDATA%\Temp\pytest-*`, another user or
agent execution identity may own the shared pytest directory. The T15 tests
share one temporary model fixture, so one setup failure can produce seven errors
before the database/API assertions execute. This is not evidence of seven planning
defects. A cache permission warning can have the same ownership cause.

Run the three lines above in your normal activated terminal: they select fresh,
ignored workspace folders for temporary files and cache. Generate a new `$taskRun`
for **every** pytest invocation. Pytest clears `--basetemp` at startup; never point
it at model/demo output, existing data or the `.artifacts` root. No administrator
terminal or shared temporary-folder permission change is needed. Keep the original
failure and record the retry result separately.

<a id="apply-or-inspect-migrations"></a>

## 3. Optional manual API use, after the resetting tests

For deliberate inspection against this disposable database, export its URL under
the backend/Alembic setting and inspect/apply the current schema:

```powershell
$env:DECISION_DATABASE_URL = $env:T11_TEST_DATABASE_URL
python -m alembic upgrade head
python -m alembic current
```

Expect current revision `20261005_01`. The migration chain is:

| Revision | Behavior |
| --- | --- |
| `20260922_01` | V1 immutable evaluation snapshots with one-time human finalization |
| `20260922_02` | V1 creation keys/fingerprints, atomic mapping and advisory locking |
| `20261005_01` | V2 planning/scenario JSONB snapshots; shared creation-key namespace; UPDATE/DELETE protection |

Application startup and requests never migrate. For an already configured own
application database, export its URL before Alembic, as documented in
[the T15 handoff](T15_HANDOFF.md#configuration-and-verification), and never set it
as the resetting test URL.

For T15 inspection, configure the owner-generated saved model and a local bearer
token before starting Uvicorn in this same terminal. Use the matching controlled
payload; follow the [terminal demonstration](T15_DEMO.md) for fresh preparation,
two-terminal API use and retrieval after a backend restart. Changes to
process settings take effect when the backend starts. The token proves possession,
not a buyer's identity. Model checksums prove integrity, not authenticity.

## 4. Stop only the disposable service

After stopping any manual backend using this test database:

```powershell
podman compose -f infra/persistence/compose.test.yaml down
Remove-Item Env:T11_TEST_DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:DECISION_DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:T11_POSTGRES_PASSWORD -ErrorAction SilentlyContinue
```

`down` removes this test service and its disposable data; it does not stop Odoo's
separate project. Stop any SSH tunnel with Ctrl+C. Never add Odoo volume deletion
to this cleanup sequence.

This PoC storage is not a production backup, retention, identity-management or
regulatory-compliance solution. Those are outside the current local increment.
