# T11 Persistence Development and Migration Guide

T11 uses PostgreSQL only through the `persistence/` adapter. Application use cases
depend on `DecisionCaseRepository` and `UnitOfWork` contracts, and the Decision Core
has no persistence dependency. Application startup never creates or changes the
schema; Alembic migration `20260922_01` is the only supported schema setup path.

## Safety boundary

The integration fixture deliberately runs `alembic downgrade base` followed by
`alembic upgrade head`. Use it only with the disposable service in
`infra/persistence/compose.test.yaml`. Do not set `T11_TEST_DATABASE_URL` to the
Odoo database, another shared development database, or any production-like system.

The test service binds only to `127.0.0.1` and uses a separate database name, user,
container, and Compose project. T11 does not need Odoo credentials and does not read
or write any Odoo model.

## Start the isolated database on Windows

From an activated project `.venv` in PowerShell:

```powershell
$env:T11_POSTGRES_DB = "decision_cases_test"
$env:T11_POSTGRES_USER = "t11_test"
$env:T11_POSTGRES_PASSWORD = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:T11_POSTGRES_PORT = "55432"

podman compose -f infra/persistence/compose.test.yaml up -d
podman compose -f infra/persistence/compose.test.yaml ps

$env:T11_TEST_DATABASE_URL = `
  "postgresql+psycopg://t11_test:$env:T11_POSTGRES_PASSWORD@127.0.0.1:55432/decision_cases_test"
```

If Podman cannot find Compose, use the project-local provider for that terminal:

```powershell
$env:PODMAN_COMPOSE_PROVIDER = `
  "$PWD\.venv\Scripts\podman-compose.exe"
```

If the container is healthy but the Windows host port is unavailable because
Podman's forwarding helper failed, use the established localhost-only SSH tunnel
procedure and point the URL at an unused local port such as `55433`:

```powershell
$machine = (podman machine inspect podman-machine-default | ConvertFrom-Json)[0]
ssh.exe `
  -i $machine.SSHConfig.IdentityPath `
  -p $machine.SSHConfig.Port `
  -N `
  -L 127.0.0.1:55433:127.0.0.1:55432 `
  "$($machine.SSHConfig.RemoteUsername)@127.0.0.1"
```

## Apply or inspect migrations

For the disposable database, either export the URL under the Alembic name or pass it
through configuration:

```powershell
$env:DECISION_DATABASE_URL = $env:T11_TEST_DATABASE_URL
python -m alembic upgrade head
python -m alembic current
```

Migration `20260922_01` creates `decision_cases`, JSONB snapshot columns, lifecycle
checks, the idempotency-key uniqueness constraint, and a trigger that rejects changes
to stored evaluation snapshots or any change after finalization.

## Run focused tests

```powershell
pytest tests/test_decision_case_serialization.py tests/test_decision_cases.py -v
pytest tests/integration/test_decision_case_postgres.py -v
```

The PostgreSQL tests cover a clean migration, legacy/active-history/fallback snapshot
round trips, separate sessions, rollback, uniqueness, immutable snapshot fields,
double finalization, and idempotency.

## Stop the isolated database

```powershell
podman compose -f infra/persistence/compose.test.yaml down
```

This preserves the test volume if one is later added. Use `down --volumes` only when
you deliberately intend to destroy disposable test data. Never use it for the Odoo
Compose project as part of T11 testing.

## Operational limitations

T11 provides no authentication, authorization, encryption-key management,
tamper-proof audit log, backup policy, retention policy, or regulatory-compliance
claim. `actor_reference` is caller-supplied attribution. Provenance records origin,
not objective truth. Database access control, secret distribution, backup, and
production operations remain future deployment concerns.
