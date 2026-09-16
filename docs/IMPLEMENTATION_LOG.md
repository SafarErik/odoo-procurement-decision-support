# Implementation log

This log is organised by development increment. It records evidence and decisions,
not a commit-by-commit diary.

## T0 — Development foundation and early Odoo capability spike

### Objective

Establish a reproducible, maintainable local foundation before any procurement
decision logic is implemented. The increment covers repository conventions, a local
Odoo environment definition, thin FastAPI and Reflex boundaries, basic automated
checks, and an evidence-based assessment of Odoo integration capability.

### Implemented components

- Root development conventions in `AGENTS.md`, including architecture, language,
  secrets, documentation, and Google Drive constraints.
- A Python project definition in `pyproject.toml`, with FastAPI, Reflex, test, and
  linting dependencies.
- A typed `GET /api/v1/health` FastAPI endpoint that has no database, Odoo, or
  procurement-logic dependency.
- A separate Reflex app that calls the documented health endpoint over HTTP using
  environment-aware `BACKEND_BASE_URL` configuration and displays an unavailable
  backend state clearly. Its state-changing handlers use `@rx.event` so Reflex and
  static type checkers treat them as valid UI event handlers.
- Explicit empty boundary directories for the future Decision Core and Odoo adapter.
- A Docker Compose local environment for Odoo 19.0 and PostgreSQL, with named
  volumes, an internal network, localhost-only Odoo exposure, and a PostgreSQL
  health check.
- Automated tests for the API response contract and frontend API URL configuration.
- An initial Odoo capability spike at `docs/spikes/odoo-capability-spike.md`.

### Affected requirements

- **NFR-01:** explicit module and infrastructure boundaries.
- **NFR-02:** no Decision Core implementation is coupled to Odoo; the Odoo adapter
  is separated and unimplemented pending validation.
- **NFR-05:** deterministic API and configuration tests, plus standard lint/format
  commands.
- **NFR-06:** Reflex is a separate component that uses the API only.
- **NFR-07:** adapter documentation requires a dedicated least-privilege user and
  external API access; no credentials are committed.
- **NFR-08:** pinned image tags, `.env.example`, Compose, named volumes, and startup
  procedures support reproducible local execution.
- **AC-08:** supported indirectly: the spike identifies validation work required
  before constructing a complete ERP-independent decision input.

### Commands and verification performed

Initial read-only assessment on 2026-09-16:

```text
Get-Location
git status --short --branch
Get-ChildItem -Force
rg --files -g README* -g AGENTS.md -g *.md -g *.yml -g *.yaml -g *.toml -g *.json -g *.env*
Get-Content -Raw README.md
git log --oneline -5
docker --version
docker compose version
python --version
py --version
uv --version
poetry --version
node --version
npm --version
```

Results: the repository was clean on branch `codex/t0-initial-setup`, contained only
a project-specific README and an initial commit, and had no `AGENTS.md`, config, or
implementation files. The initial agent-shell `PATH` did not expose Docker, Docker
Compose, Python, `py`, `uv`, or Poetry. Node/npm reported that no active Node.js
version was configured.

Subsequent local Python environment setup and verification:

```text
C:\Users\Erik Safar\AppData\Local\Microsoft\WindowsApps\python.exe --version
C:\Users\Erik Safar\AppData\Local\Microsoft\WindowsApps\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[frontend,dev]"
.\.venv\Scripts\python.exe -c "import fastapi, httpx, pydantic, pydantic_settings, reflex, uvicorn"
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
```

Results: Python 3.14.7 created the ignored project-local `.venv`. FastAPI,
Pydantic, Pydantic Settings, HTTPX, Reflex, Uvicorn, Pytest, and Ruff import from
that environment. Ruff formatting and linting pass. Pytest passes **2/2** tests.
`pip check` reports no broken requirements, and importing the Reflex application
from its runtime directory succeeds. Pytest emits two upstream deprecation warnings
from FastAPI/Starlette test-client dependencies; no project-code test failure occurs.

Post-implementation static checks executed:

```text
git diff --check
git check-ignore -v .env
git check-ignore -v .env.example
rg -n "odoo|postgres|sqlalchemy|psycopg|sqlite" backend frontend decision_core odoo_adapter tests
rg -n "5432:" infra README.md
rg -n "BACKEND_BASE_URL|/api/v1/health" frontend tests README.md .env.example
rg -n "[ \\t]+$" -g "*.py" .
git status --short
```

Results: `git diff --check` completed without whitespace errors. `.env` is ignored
while `.env.example` is intentionally not ignored. The source-boundary scan found no
Odoo, PostgreSQL, SQLAlchemy, psycopg, or SQLite references in backend, frontend,
Decision Core, adapter, or test code. The infrastructure documentation/configuration
scan found no host PostgreSQL port exposure, and the frontend configuration and API
health route references were present where expected. These are static checks only;
they do not validate Compose parsing or runtime behaviour.

A separate Python-source length check found no lines longer than the configured
100-character limit.

The following checks are **not yet executed** and T0 is not complete:

- `docker compose --env-file .env -f infra/odoo/compose.yaml config`
- Odoo/PostgreSQL startup, health, persistence, and restart verification
- Reflex browser rendering and live HTTP connectivity verification

### Verified technical facts

- Odoo 19.0 documentation supports PostgreSQL 13.0 or above.
- Docker Hub publishes official Odoo 19.0 image tags; this increment pins the
  dated tag `odoo:19.0-20260908` rather than `latest`.
- Docker Hub publishes `postgres:16.15-bookworm`; PostgreSQL 16 satisfies Odoo's
  documented version requirement.
- The official Odoo 19.0 image entrypoint accepts database connection settings via
  `HOST`, `PORT`, `USER`, and `PASSWORD`, waits for PostgreSQL, and invokes Odoo.
- Odoo 19 introduces the JSON-2 external API; its documented endpoint shape uses
  `/json/2/<model>/<method>` with a bearer API key. Legacy XML-RPC and JSON-RPC are
  documented as deprecated.

Sources and evidence are recorded in the capability spike.

### Assumptions

- The current official Docker image can be used as a local Community-oriented PoC
  environment, subject to runtime verification.
- A separate Odoo API user and API key can be configured with only the eventual
  required read permissions. This has not been tested in the local instance.
- `reflex run` will work after the declared dependencies and required Node runtime
  are installed; no replacement frontend was introduced.

### Open questions

- Which Odoo edition, plan, modules, and user permissions will apply to the target
  integration environment?
- Is JSON-2 enabled and suitable in the selected environment, and what exact
  timeout, pagination, rate-limit, and error semantics apply?
- Which specific database-dependent models and fields are available after installing
  the required Purchase and Inventory modules?
- Which source records and date semantics form valid input for later historical
  delivery-performance calculations?

### Important decisions and trade-offs

- **FastAPI and Reflex are minimal proof boundaries only.** This validates the
  replaceable frontend rule without prematurely designing application use cases.
- **No application database was added.** There is no persistence use case in T0;
  a dedicated persistence layer remains a future responsibility.
- **PostgreSQL is not exposed to the host.** Only Odoo binds to localhost; this
  reinforces the no-direct-Odoo-database-access principle.
- **The Compose Odoo image has no health check.** Only PostgreSQL uses a reliable
  image-provided `pg_isready` check. Odoo HTTP verification is deliberately a
  runtime check rather than an unverified shell assumption.
- **No Odoo models or fields were hard-coded.** Candidate concepts are documented
  separately as items to validate, not as a canonical mapping.

### Rejected alternatives

- Implementing a preliminary weighted scoring, ranking, repository, or generic
  adapter framework was rejected as out of scope and speculative.
- Replacing Reflex before testing it was rejected; there is no verified
  incompatibility yet.
- Exposing PostgreSQL or accessing it directly from the decision-support
  application was rejected as architecturally invalid.

### Known limitations and technical debt

- Docker and a usable Node.js runtime remain unavailable to the agent shell, so
  Compose and full Reflex browser runtime verification remain blocking gaps for T0
  completion.
- Image tags are explicit but not digest-pinned; a future reproducibility/security
  decision may pin multi-platform image digests after validating the target host.
- The frontend does not yet have browser-level end-to-end coverage.

### Dependency-isolation update

The project declares its runtime and optional development dependencies in
`pyproject.toml`. They are intended to be installed with
`python -m pip install -e ".[frontend,dev]"` inside the ignored `.venv` directory,
not into the system Python installation. This local environment was created and
verified with Python 3.14.7. `pydantic` is listed explicitly because it is imported
directly by the API schema, even though FastAPI also depends on it.

### Evidence locations

- `README.md` — operating instructions and boundary overview.
- `AGENTS.md` — future-agent rules.
- `infra/odoo/compose.yaml` and `.env.example` — local environment definition.
- `tests/test_health.py` and `tests/test_frontend_config.py` — intended automated
  checks.
- `docs/spikes/odoo-capability-spike.md` — external-source and local-environment
  evidence.

### Suggested thesis chapter destinations

- System architecture and modularity: high-level architecture and T0 boundaries.
- Implementation methodology: Compose reproducibility, test strategy, and quality
  gates.
- ERP integration design: capability spike, API selection, least privilege, and
  unresolved data-mapping questions.
- Limitations and future work: unverified runtime checks and deferred decision logic.

### Explicitly unimplemented functionality

- Weighted Sum Model, normalization, scoring, supplier ranking, strategy profiles,
  hard constraints, historical KPI calculation, and final decision explanations.
- Canonical domain model and production persistence schema.
- Odoo adapter, authentication setup, validated model/field mapping, and synthetic
  Odoo data.
- Authentication/authorization, dashboard design, cloud deployment, queues,
  background workers, SaaS features, and LLM functionality.
