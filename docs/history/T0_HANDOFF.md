# T0 formal handoff

**Audit date:** 2026-09-16  
**Baseline:** `9af70cc` (`Establish T0 development foundation`)  
**Classification:** `COMPLETE`

T0 is complete because every required repository, automated, runtime, persistence,
and capability-spike check has executable or inspection evidence. The audit fixed
three bounded compatibility defects: Odoo 19 no longer accepts the legacy
`--admin-passwd` CLI option; Reflex needed an explicit flat app-module import and no
package marker in its app root; and the Reflex state backend needed a port separate
from FastAPI.

## Changes

- `infra/odoo/compose.yaml`: generate a mode-restricted Odoo runtime configuration
  containing the local master password, then invoke the official entrypoint.
- `frontend/rxconfig.py`: import the flat `app.py` module explicitly and use port
  8001 for Reflex state traffic.
- `frontend/__init__.py`: removed because Reflex 0.9 rejects an `__init__.py` in the
  app root; Python still imports `frontend.config` as an implicit namespace package.
- `frontend/.gitignore`, `frontend/requirements.txt`, and `frontend/reflex.lock/`:
  retained Reflex-generated project metadata required for a clean, reproducible app
  initialization.
- `tests/test_frontend_config.py`: cover the Reflex module and non-conflicting port.
- `pyproject.toml`: include the verified `podman-compose` provider in the development
  extra.
- `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_LOG.md`, and the Odoo capability
  spike: replace stale Docker-required/unverified-runtime guidance with the verified
  Podman workflow and results.

## Verification matrix

| T0 Definition of Done item | Status | Command or procedure | Result and evidence |
| --- | --- | --- | --- |
| Repository structure and architectural boundaries | PASS | Inspect repository and scan imports/references | FastAPI, Reflex, Decision Core, and Odoo adapter remain separate; no decision logic or direct Odoo database access was added. See `README.md`, `AGENTS.md`, `decision_core/README.md`, and `odoo_adapter/README.md`. |
| Useful `AGENTS.md` | PASS | Read and compare with implementation | Scope, architecture, secrets, language, documentation, and verified Podman check commands are explicit in `AGENTS.md`. |
| `.gitignore` coverage | PASS | `git check-ignore -v .env`; inspect generated/runtime paths | `.env`, virtual environments, Python caches, Reflex build state, IDE files, and logs are ignored; `.env.example` remains trackable. |
| No committed `.env` or real credentials | PASS | `git ls-files` plus credential-name scan | Only `.env.example` is tracked. The audit `.env` is ignored and contains synthetic local-only values. |
| Explicit container image versions | PASS | Compose inspection and `podman image inspect` | `postgres:16.15-bookworm` and `odoo:19.0-20260908` are explicit. Pulled image IDs are recorded in `docs/IMPLEMENTATION_LOG.md`. |
| Valid Compose configuration | PASS | `podman compose --env-file .env -f infra/odoo/compose.yaml config` | Parsed successfully with `podman-compose` 1.6.0. |
| Persistent named volumes | PASS | Compose config, `podman volume ls`, down/up probe | `odoo_db_data` and `odoo_data` existed after `down`; markers survived the subsequent `up`. |
| PostgreSQL not exposed to host | PASS | `podman compose ... ps` and rendered config | Database shows only container port `5432/tcp`; no host binding exists. |
| Environment-aware frontend/backend configuration | PASS | Inspect `.env.example`, settings objects, and tests | Frontend reads `BACKEND_BASE_URL`; API service name and both settings objects read the root `.env`. No deployment URL is hard-coded in a component. |
| Formatting | PASS | `.venv\Scripts\python.exe -m ruff format --check .` | All checked files formatted. |
| Linting | PASS | `.venv\Scripts\python.exe -m ruff check .` | Passed. |
| Type checking, if configured | PASS | Inspect `pyproject.toml` | Conditional item is not applicable: no type checker is configured. Python compilation and Ruff are the current static gates; this is documented technical debt. |
| Python tests | PASS | `.venv\Scripts\python.exe -m pytest -v` | Three tests passed after the closure fixes. Upstream deprecation warnings do not represent project failures. |
| FastAPI endpoint test | PASS | `tests/test_health.py` and live `Invoke-WebRequest` | Test contract passed; live endpoint returned HTTP 200 and the documented JSON body. |
| Frontend checks | PASS | `compileall`, Reflex compile/run, browser inspection | Reflex compiled, served the UI, and displayed both connected and unavailable states. |
| Compose validation | PASS | `podman compose ... config` | Successful with the external `podman-compose` provider. |
| PostgreSQL readiness | PASS | Compose health plus logs | Container became `healthy`; logs reported PostgreSQL 16.15 ready to accept connections. |
| Odoo startup and host reachability | PASS | Compose logs, in-container HTTP, then host `Invoke-WebRequest` through a localhost-only SSH tunnel | Odoo 19.0-20260908 started and `/web/database/selector` returned HTTP 200. The tunnel was required by an environment-specific Windows forwarding-helper failure; the Compose bind remains localhost-only. |
| `GET /api/v1/health` runtime | PASS | Uvicorn plus `Invoke-WebRequest` | HTTP 200: `{"status":"ok","service":"procurement-decision-support-api","api_version":"v1"}`. |
| Separate Reflex frontend calls FastAPI over HTTP | PASS | Run FastAPI on 8000 and Reflex state backend on 8001; inspect browser | UI displayed `ok procurement-decision-support-api (v1)`. Source inspection confirms the only integration call is HTTPX to the configured health URL. |
| No frontend access to Odoo or database | PASS | Source scan and architecture inspection | Frontend imports only Reflex, HTTPX, and frontend settings; no Odoo/database client or address is present. |
| Clear unavailable-backend state | PASS | Stop Uvicorn and click `Check backend` in the browser | UI changed to `Unavailable` with `Could not reach the backend: All connection attempts failed`. |
| Restart behaviour | PASS | `podman compose ... restart`, then `ps`, marker queries, and HTTP smoke test | Both containers restarted; PostgreSQL returned healthy; Odoo returned HTTP 200; markers remained. FastAPI stop/start also recovered in the UI. |
| Persistence across normal down/up | PASS | Write safe synthetic markers; `podman compose down`; verify volumes; `up -d`; query markers | PostgreSQL returned `T0-20260916-podman-persistence`; the Odoo volume returned the same marker. No `--volumes` operation was used. |
| Capability spike distinguishes evidence classes | PASS | Review and update `docs/spikes/odoo-capability-spike.md` | Verified facts, local observations, assumptions, unresolved questions, candidate concepts, and adapter implications are separate. |
| External Odoo API validation accurately stated | PASS | Review executed requests and spike | No external API call, API key, permission, model, or field was validated. The spike says this explicitly and does not promote candidates to contracts. |
| T0 scope preserved | PASS | Diff and source inspection | No WSM, normalization, ranking, hard constraints, historical KPI logic, production persistence, final adapter, or domain model was implemented. |

## Runtime results

- **PostgreSQL:** 16.15, healthy, internal-only port, persistent marker verified.
- **Odoo:** 19.0-20260908, connected to PostgreSQL, HTTP 200 database selector,
  persistent Odoo-volume marker verified.
- **FastAPI:** HTTP 200 with the stable documented health response.
- **Reflex:** 0.9.11.post1 compiled and ran; frontend and state backend remained
  separate from FastAPI.
- **Frontend/backend communication:** live browser displayed the FastAPI service and
  version via HTTP.
- **Failure state:** live browser displayed a clear unavailable message while
  FastAPI was stopped and recovered after restart.
- **Restart:** Compose restart passed for both containers.
- **Persistence:** both named volumes retained synthetic markers through normal
  Compose down/up.

## Podman environment

- Client/server: Podman 6.0.2.
- Machine: `podman-machine-default`, WSL provider, Linux/amd64 server.
- Compose provider: external `podman-compose` 1.6.0 from `.venv`.
- Images: explicit dated/versioned tags; exact image IDs are in the implementation
  log.
- Host limitation: Podman's Windows forwarding helper did not create a listener for
  the reported localhost mapping. The audit used a temporary SSH tunnel bound only
  to Windows localhost. The Compose file was not weakened to bind all interfaces.

## Odoo findings

### Verified facts

- The pinned image starts against PostgreSQL 16.15 using the official entrypoint.
- Odoo 19 removed the `--admin-passwd` server flag even though `admin_passwd`
  remains a configuration-file setting.
- The local database selector is reachable, and both persistent volumes survive the
  required lifecycle operations.

### Environment-specific observations

- Podman was installed outside the initial shell `PATH`.
- `podman compose` selected `podman-compose` 1.6.0.
- The Windows port-forward helper failed; a secure local tunnel supplied host HTTP
  evidence.

### Assumptions

- A future dedicated integration identity can be granted only the required read
  permissions.
- JSON-2 is the preferred candidate if the selected environment actually exposes it
  with acceptable entitlement and behaviour.

### Unresolved questions

- Edition, plan, installed apps, JSON-2 availability, and API-key permissions.
- Exact models, fields, record rules, pagination, errors, and multi-company rules.
- Authoritative promised/receipt dates and partial receipt, return, backorder, and
  unit-conversion semantics.

## Remaining work

There are no unresolved T0 gaps. Known technical debt is limited to image tags not
being digest-pinned, no configured static type checker, no automated browser E2E
suite, and the host-specific Podman forwarding-helper problem.

The recommended next increment is a bounded Odoo integration-contract spike using
an initialized synthetic database and a dedicated least-privilege user: inspect the
database's supported API documentation, execute one read-only external API call,
and record real model/field/permission evidence. It should still not implement the
Decision Core, WSM scoring, ranking, constraints, or historical KPI calculations.
