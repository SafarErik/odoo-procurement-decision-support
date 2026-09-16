# Odoo Procurement Decision Support

Development foundation for a BSc thesis proof of concept: an explainable,
ERP-independent procurement decision-support system integrated with Odoo. The
system will evaluate known supplier offers and provide a recommendation while
leaving the final selection to a human decision-maker.

**Current status:** T0 — development foundation and early Odoo capability spike.
T0 deliberately contains no procurement decision algorithm, ranking, scoring,
constraints, historical KPI calculation, production persistence, or Odoo adapter.

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
- Docker Desktop with Docker Compose v2, for the Odoo environment
- A supported Node.js version is installed automatically or required by Reflex,
  depending on the installed Reflex version

The project checks were run in the local `.venv` with Python 3.14.7. Docker and an
active Node.js runtime still need to be available before container and full frontend
runtime verification can be completed. See the implementation log for details.

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

## Local startup and shutdown

Start the Odoo and PostgreSQL environment from the repository root:

```powershell
docker compose --env-file .env -f infra/odoo/compose.yaml up -d
docker compose --env-file .env -f infra/odoo/compose.yaml ps
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
root `.env`; do not hard-code a deployment-specific URL in components.

```powershell
.\.venv\Scripts\Activate.ps1
Push-Location frontend
reflex run
Pop-Location
```

Stop containers while preserving persistent volumes:

```powershell
docker compose --env-file .env -f infra/odoo/compose.yaml down
```

The following command permanently removes local Odoo and PostgreSQL volumes. Use it
only when intentionally discarding local data:

```powershell
docker compose --env-file .env -f infra/odoo/compose.yaml down --volumes
```

## Service URLs and checks

- FastAPI health: <http://127.0.0.1:8000/api/v1/health>
- FastAPI OpenAPI UI: <http://127.0.0.1:8000/docs>
- Reflex frontend: the URL printed by `reflex run` (typically `http://localhost:3000`)
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
docker compose --env-file .env -f infra/odoo/compose.yaml config
```

Run these after every material change. The tests cover the FastAPI health contract
and the frontend's configured API URL. Full frontend and container runtime checks
require the respective locally installed runtimes.

## Troubleshooting

- **`docker` or `python` not found:** install Docker Desktop or Python 3.11+, reopen
  the terminal, and rerun the relevant version command.
- **Odoo waits for PostgreSQL:** inspect `docker compose ... logs db` and verify the
  three matching `POSTGRES_*` values in `.env`.
- **Database manager rejects the master password:** use `ODOO_MASTER_PASSWORD`, not
  the PostgreSQL password; recreate only deliberately disposable local volumes if
  this value changed after the first database creation.
- **Reflex says the backend is unavailable:** start FastAPI, confirm the health URL,
  then check `BACKEND_BASE_URL` in `.env`.
- **Port conflict:** change `ODOO_HTTP_PORT`; for the API or frontend, stop the
  conflicting local process or use their runtime-specific port options.

## Limitations

T0 has no production persistence layer, no authentication or authorization, no
Odoo adapter, no validated Odoo data mapping, and no procurement decision logic.
See [the implementation log](docs/IMPLEMENTATION_LOG.md) and
[the Odoo capability spike](docs/spikes/odoo-capability-spike.md) for verified
facts, assumptions, and open questions.
