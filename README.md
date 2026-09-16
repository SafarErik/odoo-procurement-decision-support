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
- Python 3.11 with `pip`; this is the shared local-development and CI compatibility
  baseline
- Node.js 22.22 or later only when running the production frontend export locally;
  the integration workflow provisions it automatically
- Podman on Windows with a running Linux-based Podman machine; Podman Desktop is not
  required for the command-line workflow
- A Compose provider for `podman compose`; the project `dev` extra installs the
  verified `podman-compose` provider

The package metadata permits Python 3.11 or later and Ruff targets Python 3.11.
The T0 closure checks used Python 3.14.7, which is additional compatibility evidence
rather than the CI baseline. They also used Podman client/server 6.0.2,
`podman-compose` 1.6.0, Reflex 0.9.11.post1, and Reflex-managed Bun 1.4.0.
Reflex manages Bun and its web dependencies on first run. The ordinary local T0
runtime was verified without treating a global Node.js installation as a general
prerequisite, but the locked production export toolchain currently requires Node.js
22.22 or later.

## Setup

Create local configuration and fill both blank password values with separate,
random local-development secrets. `.env` is ignored by Git and must never be
committed. The tracked example intentionally contains no password-like placeholder
values so secret scanners do not mistake documentation for credentials.

```powershell
Copy-Item .env.example .env
```

Compose will reject the configuration until both `POSTGRES_PASSWORD` and
`ODOO_MASTER_PASSWORD` are set in `.env`.

Create a virtual environment and install the API, frontend, and developer tools:

```powershell
py -3.11 -m venv .venv
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
python -m compileall backend frontend decision_core odoo_adapter
pytest -m "not integration and not e2e" -v
python -m pip check
podman compose --env-file .env -f infra/odoo/compose.yaml config
```

Run these after every material change. Unmarked tests are fast. Tests requiring
running application or infrastructure components use the `integration` marker;
browser-level full-flow tests use the reserved `e2e` marker. Strict marker checking
prevents misspelled categories from silently running in the wrong suite.

The fast tests cover the FastAPI health contract, frontend API URL configuration,
successful health-response mapping, unavailable or invalid backend responses, and
the separate Reflex state-backend port. With the documented runtime services
running, integration tests can be selected explicitly:

```powershell
pytest -m "integration and not e2e" -v
```

No browser E2E suite or static type checker is currently configured.

## Continuous integration

GitHub Actions runs two independent workflows on ephemeral Ubuntu runners:

- **Quality:** runs for every pull request, pushes to `main`, and manual dispatch.
  Its stable `quality` job performs the fast checks and validates the Compose model
  with temporary synthetic credentials.
- **Container and API integration:** runs only for relevant runtime paths on pull
  requests and `main`, plus manual dispatch. It starts PostgreSQL, Odoo, and FastAPI;
  runs only integration-marked tests; verifies frontend compilation; and checks
  technical named-volume persistence. It provisions Node.js 22.22 for the locked
  frontend build dependencies. Superseded runs are cancelled.

The integration workflow is not browser-level E2E coverage. In particular,
`reflex export --frontend-only --no-zip` proves that the frontend compiles, not that
the running Reflex UI successfully communicates with FastAPI.

Configure branch protection manually after the `quality` job has run at least once:

1. In the GitHub repository, open **Settings**, then the applicable branch rule or
   ruleset for `main`.
2. Enable required status checks and select the check named `quality`.
3. Do not make `container-api-integration` required at this stage.

The workflows do not change branch protection, repository settings, or any other
remote governance configuration. They require no cloud account, deployment token,
or persistent Google Cloud or AWS environment.

## Manual browser milestone acceptance

For milestone verification, start FastAPI and Reflex using the commands above and
confirm both states in a browser:

1. With FastAPI running, Reflex displays the `ok` status and API service/version
   detail returned over HTTP.
2. After stopping FastAPI, reloading the page or pressing **Check backend** displays
   `Unavailable` and a useful connection error.

Keep this manual evidence separate from frontend compilation until a dedicated E2E
workflow is implemented.

## Sources of truth

- This repository is the primary source of truth for executable implementation
  artifacts: source code, tests, workflows, Compose configuration, and technical
  implementation logs.
- Google Drive remains the primary source of truth for the Hungarian thesis living
  documentation, project status, roadmap, requirements baseline, and architectural
  decision records.

This CI increment does not modify Google Drive documents.

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
- **Frontend export reports no active Node.js version:** activate Node.js 22.22 or
  later before running `reflex export --frontend-only --no-zip`; CI configures this
  version explicitly.
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

The CI persistence check uses synthetic files to verify only that Docker named
volumes survive stack recreation. It does not establish persistence of an actual
Odoo business scenario. That evidence must come later from the implemented Odoo
integration flow.
