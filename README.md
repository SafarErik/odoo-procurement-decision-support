# Odoo Procurement Decision Support

Development foundation for a BSc thesis proof of concept: an explainable,
ERP-independent procurement decision-support system integrated with Odoo. The
system will evaluate known supplier offers and provide a recommendation while
leaving the final selection to a human decision-maker.

**Current status:** T0 is complete and the first read-only Odoo integration
increment is implemented. The application can retrieve recent open RFQs from the
local Odoo 19 database through JSON-2, expose an ERP-neutral FastAPI response, and
display the result in a responsive Reflex procurement ledger. It still contains no
procurement decision algorithm, ranking, scoring, constraints, historical KPI
calculation, write operation, or production persistence. See
[the T1 handoff](docs/T1_HANDOFF.md) for the current verification matrix.

## Architecture

```text
Reflex frontend --HTTP--> FastAPI API --> application RFQ use case
                                               |
                                               +--> Odoo adapter --JSON-2--> Odoo

                         future Decision Core (still independent and empty)
```

The frontend has no direct Odoo or database access. The application contract is
ERP-neutral, while Odoo transport and payload mapping remain inside
`odoo_adapter/`. The Decision Core remains independent of Odoo, FastAPI, Reflex,
and database frameworks. Direct Odoo database access by this project is prohibited.

## Repository layout

```text
application/    ERP-neutral use cases and adapter ports
backend/        FastAPI boundary and dependency composition
frontend/       Separate Reflex procurement ledger
decision_core/  Reserved ERP-independent decision logic boundary
odoo_adapter/   Read-only Odoo JSON-2 transport and mapping
infra/odoo/     Local Odoo and PostgreSQL Compose configuration
tests/          Fast contract tests and optional live integration checks
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

For a condensed terminal-by-terminal startup reference and the Windows SSH-agent
setup used by this repository, see
[Local development and SSH quick start](docs/LOCAL_DEVELOPMENT_AND_SSH.md).

Create local configuration and fill both blank password values with separate,
random local-development secrets. After creating the Odoo database, generate an API
key in the Odoo user's preferences and set `ODOO_DATABASE` and `ODOO_API_KEY` in
`.env`. The implemented integration is read-only, but the API key still has all
permissions of its Odoo user; a dedicated least-privilege user is the target setup.
`.env` is ignored by Git and must never be committed. The tracked example keeps all
secret values blank so secret scanners do not mistake documentation for credentials.

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
database named `procurement_poc`, and use `ODOO_MASTER_PASSWORD` from `.env` when
asked for the master password. Install Purchase and Inventory, generate an API key,
and save it only as `ODOO_API_KEY` in the ignored `.env`. The current proof of
concept uses Odoo's demo RFQs; do not use production credentials or data.

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
- Open RFQs: <http://127.0.0.1:8000/api/v1/procurement/rfqs>
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
python -m compileall application backend frontend decision_core odoo_adapter
pytest -m "not integration and not e2e" -v
python -m pip check
podman compose --env-file .env -f infra/odoo/compose.yaml config
```

Run these after every material change. Unmarked tests are fast. Tests requiring
running application or infrastructure components use the `integration` marker;
browser-level full-flow tests use the reserved `e2e` marker. Strict marker checking
prevents misspelled categories from silently running in the wrong suite.

The fast tests cover the health contract, the ERP-neutral RFQ API, Odoo JSON-2
request and mapping behaviour, stable upstream error translation, frontend URL
configuration, RFQ presentation mapping, empty results, unavailable or invalid
responses, and the separate Reflex state-backend port. With the documented runtime
services running and the ignored `.env` configured, integration tests can be
selected explicitly:

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

1. With Odoo and FastAPI running, Reflex displays the open RFQs returned through the
   backend endpoint, including reference, vendor, order date, state, and total.
2. After stopping FastAPI, reloading the page or pressing **Refresh data** displays
   the Odoo-unavailable state and a useful recovery message.

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

The integration is deliberately read-only and limited to the validated
`purchase.order` summary fields required by the RFQ ledger. It has no pagination,
retry policy, write operation, application authentication/authorization, production
persistence, procurement decision logic, or validated purchase-line and inventory
receipt mapping. The current discovery API key belongs to the local administrator;
replace it with a dedicated least-privilege integration identity before treating
the setup as more than a local PoC. Image tags are explicit but are not
digest-pinned. The frontend has no automated browser end-to-end test suite.
See [the implementation log](docs/IMPLEMENTATION_LOG.md) and
[the Odoo capability spike](docs/spikes/odoo-capability-spike.md) for verified
facts, assumptions, and open questions.

The CI persistence check uses synthetic files to verify only that Docker named
volumes survive stack recreation. It does not establish persistence of an actual
Odoo business scenario. That evidence must come later from the implemented Odoo
integration flow.
