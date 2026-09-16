# Odoo Procurement Decision Support

Development foundation for a BSc thesis proof of concept: an explainable,
ERP-independent procurement decision-support system integrated with Odoo. The
system will evaluate known supplier offers and provide a recommendation while
leaving the final selection to a human decision-maker.

**Current status:** T0 is complete. The development foundation, local Podman
runtime, API/frontend boundary, persistence behaviour, and capability spike were
verified on 2026-09-16. T0 deliberately contains no procurement decision algorithm,
ranking, scoring, constraints, historical KPI calculation, production persistence,
or Odoo adapter. See [the T0 handoff](docs/T0_HANDOFF.md) for the verification matrix.

## Architecture

```text
Reflex frontend --HTTP--> FastAPI application/API --> future Decision Core
                                  |
                                  +--> future Odoo integration adapter --supported external API--> Odoo
```

The frontend has no direct Odoo or database access. The Decision Core will remain
independent of Odoo, FastAPI, Reflex, and database frameworks. Odoo database access
by this project is prohibited; the later adapter must use a validated supported
external interface.

## Repository layout

```text
backend/        Minimal FastAPI boundary
frontend/       Minimal, separate Reflex frontend
decision_core/  Reserved ERP-independent decision logic boundary
odoo_adapter/   Reserved Odoo integration boundary
infra/odoo/     Local Odoo and PostgreSQL Compose configuration
tests/          Automated T0 checks
docs/           Implementation log and capability evidence
```

## Prerequisites

- Git
- Python 3.11 or later with `pip`
- Podman on Windows with a running Linux-based Podman machine; Podman Desktop is not
  required for the command-line workflow
- A Compose provider for `podman compose`; the project `dev` extra installs the
  verified `podman-compose` provider

The T0 closure checks used Python 3.14.7, Podman client/server 6.0.2,
`podman-compose` 1.6.0, Reflex 0.9.11.post1, and Reflex-managed Bun 1.4.0.
Reflex manages the web toolchain on first run, so a globally active Node.js version
is not a prerequisite for this verified workflow.

## Setup

Create local configuration and replace both placeholder passwords. `.env` is ignored
by Git and must never be committed.

```powershell
Copy-Item .env.example .env
```

Create a virtual environment and install the API, frontend, and developer tools:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[frontend,dev]"
```

Ensure the Podman CLI is on `PATH`, start the existing machine, and confirm the
Compose provider. The temporary `PATH` adjustment is needed only when the installer
has not updated the current shell.

```powershell
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    $env:Path = "$env:LOCALAPPDATA\Programs\Podman;$env:Path"
}
podman version
podman machine list
podman machine start podman-machine-default
podman compose version
```

## Local startup and shutdown

Start the Odoo and PostgreSQL environment from the repository root:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml up -d --build
podman compose --env-file .env -f infra/odoo/compose.yaml ps
podman compose --env-file .env -f infra/odoo/compose.yaml logs --tail=100
```

On the first Odoo start, open the database manager, create a local development
database, and use `ODOO_MASTER_PASSWORD` from `.env` when asked for the master
password. Use synthetic data only during the capability spike.

Start the API in a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```

Start Reflex in a third terminal. It reads `BACKEND_BASE_URL` from the repository
root `.env`; do not hard-code a deployment-specific URL in components. Reflex uses
port 8001 for its own state backend so it does not collide with FastAPI on port 8000.

```powershell
.\.venv\Scripts\Activate.ps1
Push-Location frontend
reflex run
Pop-Location
```

Stop containers while preserving persistent volumes:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml down
```

This normal shutdown preserves both named volumes. Do not add `--volumes` unless
local Odoo and PostgreSQL data are intentionally being discarded; T0 verification
did not use that destructive option.

## Service URLs and checks

- FastAPI health: <http://127.0.0.1:8000/api/v1/health>
- FastAPI OpenAPI UI: <http://127.0.0.1:8000/docs>
- Reflex frontend: the URL printed by `reflex run` (normally `http://localhost:3000`)
- Odoo: `http://127.0.0.1:<ODOO_HTTP_PORT>` (default `http://127.0.0.1:8069`)

The API health response is stable and infrastructure-free:

```json
{"status":"ok","service":"procurement-decision-support-api","api_version":"v1"}
```

PostgreSQL has a container health check. Odoo's official image does not expose a
documented, image-level health command in this setup, so verify it through the web
UI and container logs after startup.

## Formatting, linting, testing, and configuration validation

```powershell
ruff format --check .
ruff check .
pytest
podman compose --env-file .env -f infra/odoo/compose.yaml config
```

Run these after every material change. The tests cover the FastAPI health contract,
the frontend's configured API URL, and the separate Reflex state-backend port. No
static type checker is currently configured.

## Troubleshooting

- **`podman` not found:** prepend `$env:LOCALAPPDATA\Programs\Podman` to the current
  shell `PATH`, or reinstall the Podman CLI with its `PATH` integration enabled.
- **No Compose provider:** activate `.venv`, rerun
  `python -m pip install -e ".[frontend,dev]"`, and check `podman compose version`.
- **Machine is stopped:** run `podman machine start podman-machine-default`.
- **Odoo waits for PostgreSQL:** inspect `podman compose ... logs db` and verify the
  three matching `POSTGRES_*` values in `.env`.
- **Database manager rejects the master password:** use `ODOO_MASTER_PASSWORD`, not
  the PostgreSQL password; recreate only deliberately disposable local volumes if
  this value changed after the first database creation.
- **Reflex says the backend is unavailable:** start FastAPI, confirm the health URL,
  then check `BACKEND_BASE_URL` in `.env`.
- **Odoo is healthy in the container but localhost refuses the connection:** restart
  the Podman machine and inspect its Windows forwarding helper. The audited host had
  this Podman-machine proxy issue; a temporary localhost-only SSH tunnel was used for
  the host HTTP smoke test. Do not broaden the Compose bind address as a workaround.
- **Port conflict:** change `ODOO_HTTP_PORT`; for the API or frontend, stop the
  conflicting local process or use their runtime-specific port options.

## Limitations

T0 has no production persistence layer, no authentication or authorization, no
Odoo adapter, no validated Odoo data mapping, and no procurement decision logic.
The local Odoo database manager was reached, but no Odoo database, external API
authentication, model, field, or licensing behaviour was validated. Image tags are
explicit but are not digest-pinned. The frontend has browser smoke evidence but no
automated browser end-to-end test suite.
See [the implementation log](docs/IMPLEMENTATION_LOG.md) and
[the Odoo capability spike](docs/spikes/odoo-capability-spike.md) for verified
facts, assumptions, and open questions.
