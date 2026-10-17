# Runbook

Windows PowerShell at the repository root. Start only what the task needs.

| Task | Needs |
| --- | --- |
| Change code and run fast checks | Python 3.11 |
| Use the web UI with saved cases | + planning database, FastAPI, Reflex, trained model |
| Read live quotations | + Odoo (Podman) |
| Database integration tests | + disposable test database (Podman) |

## 1. One-time setup

Python 3.11 is the project baseline. With [uv](https://docs.astral.sh/uv/):

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -e ".[frontend,dev]"
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env   # only if .env does not exist; then fill the blanks
```

Podman: `podman machine start` once per boot. If `podman compose` needs a provider,
`tools.dev` uses the `podman-compose` installed in the venv automatically.

## 2. Fast quality gate (no services)

```powershell
python -m tools.dev check
```

Runs `ruff format --check`, `ruff check`, `compileall`, the fast test suite
(`not integration and not e2e`, with real CBC and scikit-learn) and a dependency
check. Run it before every handoff.

## 3. Train the supplier model and prepare demo input

```powershell
python -m tools.t15_demo prepare
```

Generates the demo dataset, trains and saves the Decision Tree under
`.artifacts/t15-demo/model` and writes the demo request used by the UI. Set
`SUPPLIER_MODEL_DIRECTORY` in `.env` to the absolute path of that `model` folder.
(P1 replaces this with training on Odoo history.)

## 4. Planning database, API and UI

```powershell
python -m tools.dev db-up   # starts infra/app/compose.yaml and runs migrations
python -m tools.dev api     # terminal 2: FastAPI on http://127.0.0.1:8000 (docs at /docs)
python -m tools.dev ui      # terminal 3: Reflex on http://localhost:3000
```

Before `db-up`, set `APP_POSTGRES_PASSWORD` and the matching `DECISION_DATABASE_URL`,
plus `API_SERVICE_TOKEN` and `PLANNING_LIBRARY_COMPANY_ID` in `.env`. The database
keeps its data in a named volume; `python -m tools.dev db-down` stops it.

After a schema change that squashes migrations (as on 2026-10-18), recreate the
volume: `podman compose -f infra/app/compose.yaml down -v`, then `db-up`.

## 5. Odoo

```powershell
python -m tools.dev odoo-up    # Odoo on http://127.0.0.1:8069 with its own database
python -m tools.dev odoo-down
```

Odoo setup, integration users and fixtures are manual and documented in
[history/T0_HANDOFF.md](history/T0_HANDOFF.md), [history/T6_FIXTURE_SETUP.md](history/T6_FIXTURE_SETUP.md),
[history/T7S_MANUAL_SETUP.md](history/T7S_MANUAL_SETUP.md) and
[history/T7_FIXTURE_SETUP.md](history/T7_FIXTURE_SETUP.md). The backend uses
restricted, read-only API keys only.

## 6. Database integration tests

```powershell
$env:TEST_POSTGRES_PASSWORD = python -c "import secrets; print(secrets.token_urlsafe(32))"
podman compose -f infra/persistence/compose.test.yaml up -d --wait
$env:TEST_DATABASE_URL = "postgresql+psycopg://planning_test:$env:TEST_POSTGRES_PASSWORD@127.0.0.1:55432/planning_test"
python -m pytest -m "integration and not e2e" -v
podman compose -f infra/persistence/compose.test.yaml down
```

These tests drop and recreate the schema of the disposable test database only.
If the container is healthy but Windows refuses port 55432, see the SSH tunnel
workaround in [history/PERSISTENCE_DEVELOPMENT.md](history/PERSISTENCE_DEVELOPMENT.md).

## 7. Troubleshooting

- **CBC fails with a temp path error**: CBC cannot use a temp directory with spaces;
  `tools.dev check` sets a safe one. For manual runs set `$env:TEMP`/`$env:TMP`.
- **Saved case shows "planning data unavailable"**: check `/api/v1/health`, that the
  planning database container runs, and that FastAPI was restarted after `.env` edits.
- **Unicode errors in tooling**: set `$env:PYTHONUTF8 = "1"`.
