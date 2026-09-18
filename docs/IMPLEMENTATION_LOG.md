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
- A portable Compose local environment, verified with Podman, for Odoo 19.0 and
  PostgreSQL, with named volumes, an internal network, localhost-only Odoo exposure,
  and a PostgreSQL health check.
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

Those initial gaps were closed by the formal audit below. The earlier result is
retained here as chronological evidence, not as the current project status.

### Formal T0 closure audit — 2026-09-16

The audit used the committed T0 baseline `9af70cc` and preserved all existing work.
The installed Podman CLI was not initially on `PATH`; its local installation
directory was prepended for the audit. The existing WSL machine was started through
the CLI, without relying on Podman Desktop operations.

Verified versions:

- Python 3.14.7; Ruff 0.16.7; Pytest 8.4.2.
- FastAPI 0.141.1; Uvicorn 0.53.0; Reflex 0.9.11.post1; HTTPX 0.28.1;
  Pydantic 2.13.5; Reflex-managed Bun 1.4.0.
- Podman client/server 6.0.2, Windows/amd64 client and Linux/amd64 server on the
  WSL provider.
- `podman-compose` 1.6.0, invoked by `podman compose` as its external provider.
- `postgres:16.15-bookworm` image ID
  `5f71c21b69a7977b82247582e2e731ed76bdebaadb7dd7945ed76bcc9ed06632`.
- `odoo:19.0-20260908` image ID
  `400a621198ea355394df4a328b0f65043ffd1f4e79a5025ba16edf03cb26893d`.

Representative commands actually executed:

```text
podman version
podman info
podman machine list
podman system connection list
podman compose version
podman compose --env-file .env -f infra/odoo/compose.yaml config
podman compose --env-file .env -f infra/odoo/compose.yaml up -d --build
podman compose --env-file .env -f infra/odoo/compose.yaml ps
podman compose --env-file .env -f infra/odoo/compose.yaml logs --no-color --tail=100
podman compose --env-file .env -f infra/odoo/compose.yaml restart
podman compose --env-file .env -f infra/odoo/compose.yaml down
podman compose --env-file .env -f infra/odoo/compose.yaml up -d
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m compileall -q backend frontend decision_core odoo_adapter
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Push-Location frontend; ..\.venv\Scripts\reflex.exe run --loglevel info; Pop-Location
```

Runtime results:

- Compose configuration parsed successfully. PostgreSQL 16.15 became healthy and
  Odoo 19.0 started after replacing its removed `--admin-passwd` CLI option with a
  mode-restricted runtime configuration file.
- Odoo's database selector returned HTTP 200. The Windows forwarding helper on this
  particular Podman machine failed to expose the declared localhost binding, so the
  host smoke test used a temporary SSH tunnel bound only to `127.0.0.1`. A broader
  network bind was explicitly rejected.
- FastAPI returned the documented JSON at `GET /api/v1/health` with HTTP 200.
- Reflex compiled and ran after declaring the flat app-module import, moving its
  state backend to port 8001, and removing the package marker that Reflex forbids in
  the app root. Browser inspection displayed the FastAPI `ok` state, a clear
  `Unavailable` state while FastAPI was stopped, and recovery to `ok` after restart.
- Container restart succeeded. Synthetic markers in both the PostgreSQL and Odoo
  named volumes survived a normal Compose down/up cycle. No volume deletion command
  was executed.
- Final static results after the closure fixes are recorded in `docs/T0_HANDOFF.md`.

**Closure decision: COMPLETE.** Every T0 Definition of Done item has executable or
inspection evidence. The Podman Windows forwarding-helper issue is an
environment-specific limitation with a localhost-only verification path, not an
unverified T0 feature.

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

- Image tags are explicit but not digest-pinned; a future reproducibility/security
  decision may pin multi-platform image digests after validating the target host.
- The frontend has a successful browser smoke test but no automated browser-level
  end-to-end test suite.
- No static type checker is configured. Ruff and Python compilation are the current
  static gates.
- The audited Podman Windows forwarding helper did not expose a localhost-published
  port. The runtime itself was verified through a temporary localhost-only SSH
  tunnel; the Compose file remains portable and securely bound to localhost.

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
- `docs/T0_HANDOFF.md` — final Definition of Done matrix and runtime handoff.

### Suggested thesis chapter destinations

- System architecture and modularity: high-level architecture and T0 boundaries.
- Implementation methodology: Compose reproducibility, test strategy, and quality
  gates.
- ERP integration design: capability spike, API selection, least privilege, and
  unresolved data-mapping questions.
- Limitations and future work: environment-specific Podman forwarding, missing
  browser automation, and deferred decision logic.

### Explicitly unimplemented functionality

- Weighted Sum Model, normalization, scoring, supplier ranking, strategy profiles,
  hard constraints, historical KPI calculation, and final decision explanations.
- Canonical domain model and production persistence schema.
- Odoo adapter, authentication setup, validated model/field mapping, and synthetic
  Odoo data.
- Authentication/authorization, dashboard design, cloud deployment, queues,
  background workers, SaaS features, and LLM functionality.

## T0 automation follow-up — CI verification boundaries

### Objective and implementation

Automate repeatable verification without provisioning Google Cloud, AWS, or a
persistent deployment. GitHub Actions now defines two independent Ubuntu workflows:

- `quality` is the fast gate for pull requests, `main`, and manual dispatch. It uses
  Python 3.11, checks Ruff formatting and linting, compiles Python sources, runs only
  fast tests, checks installed dependencies and whitespace, and validates Compose
  configuration with temporary synthetic credentials.
- `container-api-integration` is path-filtered and cancellable. It starts Odoo and
  PostgreSQL through Docker Compose, starts FastAPI, runs only integration-marked
  tests, verifies Reflex frontend compilation with Node.js 22.22 as required by the
  locked frontend dependencies, and checks that synthetic files in both named
  volumes survive stack recreation. Failure logs are retained briefly.

Pytest now rejects unknown markers. Unmarked tests are fast, `integration` identifies
tests requiring running components, and `e2e` is reserved for a future browser-level
suite. The frontend HTTP mapping was isolated from Reflex state mutation so fast
tests cover successful responses, connection failures, and incomplete payloads.

### Compatibility and governance decisions

Python 3.11 is the single local and CI compatibility baseline because it is the
declared minimum in `pyproject.toml` and Ruff already targets `py311`. The earlier
successful Python 3.14.7 T0 run remains additional compatibility evidence. No
version matrix is introduced yet.

Only the stable `quality` check is intended to become mandatory. Maintainers must
configure that branch-protection requirement manually; this increment does not
modify GitHub settings or any other remote governance configuration. The heavier
integration workflow remains informative and manually dispatchable.

### Evidence limits

`reflex export --frontend-only --no-zip` verifies compilation only. Actual
Reflex-to-FastAPI success and unavailable-backend states remain documented browser
milestone checks, not automated E2E evidence. Likewise, synthetic marker files prove
technical named-volume persistence only; a real Odoo business scenario must be
verified later through the implemented Odoo adapter flow.

The repository remains the primary source of truth for executable implementation
artifacts and technical logs. Google Drive remains the primary source of truth for
the Hungarian thesis living documentation, project status, roadmap, requirements
baseline, and architectural decision records. No Google Drive document was changed
by this follow-up.

### Verification performed

Local verification on 2026-09-16 used the existing Python 3.14.7 environment because
Python 3.11 is not installed on this workstation. Ruff format and lint checks,
Python compilation, dependency checking, whitespace checking, and all six selected
fast tests passed; the two integration tests were excluded from the fast selection
and collected by `integration and not e2e`. The workflow YAML parsed successfully,
its trigger/job/concurrency structure was asserted, and Podman Compose accepted the
Compose configuration.

The local Reflex export reached the production build but could not complete because
the workstation's Node version-manager shim has no active Node.js version. The
integration workflow therefore provisions Node.js 22.22 explicitly. A full Python
3.11 run, frontend export, and container lifecycle remain to be confirmed by the
first GitHub Actions execution; they are not recorded here as locally passed.

The two password assignments in `.env.example` are intentionally blank. Earlier
human-readable replacement strings were not credentials, but resembled passwords
closely enough to trigger secret scanning. Compose's required-variable expressions
still prevent startup until a developer supplies separate local values in the
ignored `.env` file; no scanner-wide ignore rule was added.

### Developer operations guide and code navigation

`docs/LOCAL_DEVELOPMENT_AND_SSH.md` provides a concise PowerShell reference for
starting and stopping PostgreSQL, Odoo, FastAPI, and Reflex, running fast checks,
and configuring the Windows OpenSSH agent to cache the protected GitHub key across
restarts. The instructions keep the key passphrase and align Git for Windows with
the native Windows OpenSSH agent rather than introducing another agent process.

The repository now has a user-managed `.codegraph/` index. The generated local
index is ignored by Git, while `AGENTS.md` requires a focused CodeGraph query before
broad code searches or multi-file reads whenever that index is available. `rg`
remains the fallback for exact-text and non-code lookup. This reduces unnecessary
repository scanning and context use without treating the index as authoritative
for prose.

## T1 — Read-only Odoo RFQ vertical slice

### Objective

Demonstrate one complete but deliberately narrow business-data path: Odoo JSON-2 to
an isolated adapter, an ERP-neutral application use case, a thin FastAPI endpoint,
and a useful Reflex view. This increment remains read-only and does not implement
supplier evaluation or a recommendation.

### Implemented components

- An ERP-neutral `application/` contract containing the bounded open-RFQ use case,
  immutable RFQ and money DTOs, and an adapter protocol.
- A read-only `OdooRfqReader` using the validated Odoo 19 JSON-2
  `purchase.order/search_read` method with explicit fields, open-state filtering,
  newest-first ordering, a timeout, payload validation, and stable error translation.
- A FastAPI `GET /api/v1/procurement/rfqs` route with a 1–50 result bound. The route
  exposes no raw Odoo field names or payloads and maps upstream unavailability to
  HTTP 503 and invalid/rejected responses to HTTP 502.
- A restrained, responsive Reflex procurement ledger showing RFQ reference, vendor,
  order date, neutral status, and currency-aware total, plus explicit loading, empty,
  and unavailable states.
- Fast tests for the adapter request contract and mapping, API boundary and errors,
  frontend endpoint construction and presentation mapping, valid empty results, and
  invalid responses. Integration-marked tests perform a live read and verify that
  the configured identity is non-admin with read-only `purchase.order` access.

### Local evidence

On 2026-09-16, the `procurement_poc` Odoo 19 Community database had Purchase and
Inventory installed with demo data. The database-specific `/doc` page and live
JSON-2 calls confirmed `purchase.order/search_read` and the seven fields used by the
adapter: `id`, `name`, `partner_id`, `date_order`, `state`, `amount_total`, and
`currency_id`. User ID 2 was used only for the initial discovery.

The durable key now authenticates as user ID 7, `Procurement Integration`. The user
is internal, limited to company ID 1, is not a Settings administrator, and has a
custom read-only `purchase.order` ACL. Live access probes returned read `True` and
create/write/unlink `False` without performing a write operation.

All four integration tests passed with the local services running: least-privilege
access, the live adapter read, the separately served FastAPI health contract, and
Odoo HTTP availability. The FastAPI RFQ route returned HTTP 200 with seven mapped
RFQs. Eighteen fast tests passed, with all four integration tests excluded by the
fast marker expression. Ruff, Python compilation, dependency checking, Compose
configuration validation, whitespace checking, and the Reflex production export
passed. The export used the already installed Node.js 24.20.0; CI retains its
declared Node.js 22.22 baseline.

Manual browser acceptance also passed. The connected ledger displayed seven RFQs
with reference, vendor, order date, status, total, and currency. After FastAPI was
stopped, Refresh data cleared the prior rows and showed the explicit unavailable
state. Restarting FastAPI and refreshing restored the ledger. A temporary invalid
key produced HTTP 502 with code `odoo_response_error`; the UI showed the same safe
unavailable state and recovered after the correct process restarted.

### Security and scope decisions

- The API key exists only in the ignored `.env`; `.env.example` leaves the key blank
  to avoid both credential exposure and misleading secret-scanner findings.
- The durable API key belongs to the dedicated read-only integration user. The
  administrator discovery key is no longer required and should be revoked.
- The adapter performs no Odoo writes and never accesses PostgreSQL directly.
- No raw upstream response or credential is returned through API errors.
- The working demo records are capability evidence, not canonical thesis data.

### Deferred work

- Purchase-order lines, products, receipts, promised and actual delivery dates,
  partial receipts, returns, units, and multi-company record rules remain unvalidated.
- There is no pagination, retry policy, application authentication, browser E2E
  automation, or procurement decision logic.
- A real Odoo business-persistence scenario must be designed after an actual write or
  state-transition use case exists; synthetic volume markers still prove only
  technical named-volume persistence.

## T2 — ERP-independent Decision Core

### Objective and boundary

Implement the first deterministic procurement decision pipeline on canonical,
synthetic domain input without extending the Odoo adapter, application RFQ use case,
FastAPI routes, Reflex frontend, or persistence. The Decision Core imports none of
those delivery or infrastructure layers, and the existing RFQ projection is not
reused as a supplier offer.

### Implemented decision model

- Immutable `PurchaseRequirement`, `SupplierOffer`, `StrategicProfile`, exclusion,
  contribution, ranked-offer, and decision-result objects.
- Explicit validation for identifiers, quantities, price, lead time, MOQ, offer-ID
  uniqueness, non-empty offer sets, finite values, non-negative weights, and the
  supported weight total. All calculation values use `Decimal`.
- MOQ eligibility is evaluated before normalization. An offer is eligible only when
  requested quantity is at least its minimum order quantity; exclusions preserve the
  constraint, relevant values, and a human-readable explanation.
- Reusable cost and benefit min-max normalization. Unit price and lead time are both
  cost criteria in this increment. Equal values normalize to `1`, and bounds use
  eligible offers only.
- Weighted Sum Model scoring preserves raw value, normalized value, applied weight,
  and weighted contribution for each criterion. Total score is the exact sum of the
  recorded Decimal contributions.
- Ranking is score descending, then offer identifier ascending. Input ordering does
  not affect the result. When every offer is excluded, the result contains the
  exclusions and no recommendation.

### Reference evidence

For a quantity of 100, Offer A (price 10, lead time 10, MOQ 50) and Offer B
(price 12, lead time 5, MOQ 100) are eligible; Offer C (price 9, lead time 8,
MOQ 150) is excluded before bounds are calculated. Cost-focused weights rank A at
0.7 above B at 0.3. Urgent weights rank B at 0.7 above A at 0.3. Balanced weights
produce 0.5 each and the offer-ID tie-break ranks A first. The unit tests verify the
full contribution trace and all specified validation and edge cases.

### Verification performed on 2026-09-17

- Ruff formatting and lint: passed.
- Python compilation for all five source packages: passed.
- Fast tests: 57 passed, 4 integration tests deselected. This includes 39 Decision
  Core cases and the unchanged T0/T1 fast suite.
- Dependency consistency and whitespace checks: passed.
- Podman Compose configuration with the ignored local `.env`: passed using Podman
  6.0.2 and project-local `podman-compose` 1.6.0.
- Live integration tests: not executed in this T2 run. The existing containers were
  stopped, and Podman's known Windows forwarding helper failed during machine start.
  No T2 code touches the live integration path.
- GitHub Actions: not yet executed for this branch at the time of local handoff.

See `docs/T2_HANDOFF.md` for formulas, the complete manual calculation, scope limits,
and the final review handoff.

## T3 — Application and HTTP decision boundary

### Objective and boundary

Expose the existing Decision Core through one narrow synchronous application use
case and `POST /api/v1/procurement/decisions/evaluate`. The endpoint evaluates only
canonical input supplied in the request body. It does not call Odoo, reuse the RFQ
projection as an offer, access a database or local file, persist a result, select a
supplier automatically, or perform a write operation.

The dependency direction is `backend -> application -> decision_core`.
`application.decisions.evaluate_procurement_decision` accepts the existing immutable
domain objects and delegates evaluation to the Decision Core. The FastAPI route owns
request validation, request/domain mapping, response mapping, and translation of
known domain validation failures; it contains no constraint, normalization, scoring,
or ranking logic.

### Public contract

- The request contains one requirement, one or more canonical supplier offers, and
  one strategic profile.
- Decision-relevant numeric values use strict decimal strings in JSON and `Decimal`
  internally. Exponent notation, non-finite values, non-strings, and malformed
  decimal syntax are rejected by request-schema validation without repair or
  coercion.
- HTTP 200 returns the requirement and profile, the first-ranked offer or `null`,
  every eligible ranked offer and its complete criterion contribution trace, and
  every excluded offer with its failed constraint and relevant quantities.
- Request-structure failures use FastAPI/Pydantic's standard HTTP 422 response.
  `DomainValidationError` uses HTTP 422 with code `invalid_decision_input` and a safe
  domain message.
- An all-excluded outcome is HTTP 200 with an empty ranking and no recommendation.

OpenAPI registers explicit request and response schemas, the reference request, the
POST operation, HTTP 200, and HTTP 422. Its operation description states that scores
are relative WSM results, excluded offers are not scored, and the endpoint provides
human decision support without persistence or an Odoo write.

### Reference evidence

For requested quantity `100` and cost-focused weights `0.7`/`0.3`, Offer C is
excluded by MOQ before normalization. Offer A ranks first at `0.7`; Offer B ranks
second at `0.3`; the recommendation identifies Offer A. The returned contribution
trace is deterministic and includes raw value, normalized value, weight, and weighted
contribution for both criteria. Balanced weights tie at `0.5` and retain Offer A
first through the offer-ID tie-break; urgent weights rank Offer B first.

### Verification performed on 2026-09-17

- Ruff formatting and lint: passed for all tracked Python sources.
- Python compilation for all five source packages: passed.
- Fast tests: 80 passed, 5 integration tests deselected. This includes 23 new
  application/API cases and the unchanged T0, T1, and T2 behavior.
- Dependency consistency and whitespace checks: passed.
- Static boundary scans found no forbidden framework, HTTP, Odoo adapter, database,
  or environment imports in `decision_core/` or the T3 application use case.
- Podman Compose configuration: passed with Podman 6.0.2 and project-local
  `podman-compose` 1.6.0.
- Served FastAPI smoke tests: health HTTP 200, reference evaluation HTTP 200, and
  invalid semantic input HTTP 422 with `invalid_decision_input`; both selected
  runtime integration tests passed.
- Odoo-dependent integration tests and the RFQ HTTP smoke call were not executed.
  The containers became healthy, but the known Windows `win-sshproxy.exe` failure
  prevented the localhost Odoo port from accepting connections. No T3 behavior
  depends on Odoo.
- GitHub Actions: pending branch push and pull-request creation at the time of this
  local record.

See `docs/T3_HANDOFF.md` for the complete contract, evidence, limitations, and review
handoff.

## T4 — Evidence-first Odoo decision-input mapping spike

### Objective and gate

Determine through supported, read-only Odoo 19 interfaces whether one procurement
requirement and multiple genuinely comparable supplier offers can be mapped to the
existing canonical `PurchaseRequirement` and `SupplierOffer` types. Production
adapter work was conditional on validating every critical grouping, product, UoM,
quantity, supplier, price, currency, lead-time, MOQ, state, and multi-line invariant.

### Runtime result on 2026-09-17

The branch was verified against fetched T3 merge commit
`f123446dac7994d9ea4727225c5fe4a9d0a39cd5`; the T3 handoff and decision endpoint
were present, and 62 focused Decision Core/application/API tests passed.

Podman client/server 6.0.2 started the existing PostgreSQL and Odoo services.
PostgreSQL became healthy and Odoo returned HTTP 200 through the documented
localhost-only SSH tunnel. The database-specific `/doc?db=procurement_poc` route was
present but redirected to interactive login; the JSON-2 bearer key did not establish
a web session.

After the dedicated key was renewed, `res.users/context_get` authenticated as the
non-admin `Procurement Integration` user, limited to company ID 1. The existing RFQ
contract passed again. Narrow `fields_get`, `check_access_rights`, `search_read`, and
module queries verified:

- read-only access to `purchase.order`, `product.product`, `product.template`,
  `product.supplierinfo`, `res.partner`, `res.currency`, and `uom.uom`;
- denied create, write, and unlink access for every candidate model;
- denied read access to `purchase.order.line`, with HTTP 403 from a bounded line
  query and from traversing `purchase.order.order_line`;
- installed Purchase and Inventory modules, but no installed
  `purchase_requisition`; and
- absence of the probed `alternative_po_ids`, `source_po_id`, and `requisition_id`
  fields on `purchase.order`.

Eleven bounded non-cancelled purchase documents were observed: seven open RFQs and
four confirmed orders, all in company 1 and USD. Supplier information exposed
configured `delay`, `min_qty`, price, currency, company, product template/variant,
date, and UoM concepts. Those master-data values cannot replace inaccessible actual
quotation-line values.

### Mapping decision

**SPIKE COMPLETE — CRITICAL MAPPING NOT AVAILABLE — ADAPTER DEFERRED**

The spike accepted source offer identity, observed commercial-supplier identity,
currency equality, and open-state mapping in isolation. It rejected heuristic
grouping, display names as stable identity, order total or supplier master price as
quoted unit price, line quantity as MOQ, silent conversions/defaults,
date-semantic conflation, and multi-line aggregation. Explicit grouping is not
available, and line-dependent mappings remain unresolved. The demo RFQs are not
treated as one comparison case.

No adapter, synthetic mapping fixture, new endpoint, frontend change, Decision Core
change, permission change, module install, direct database access, or Odoo business
write was introduced. See `docs/spikes/odoo-decision-input-mapping-spike.md` for the
complete evidence matrix and `docs/T4_HANDOFF.md` for the review handoff.

### Verification performed

- Focused T2/T3 baseline: 62 passed.
- Renewed-key existing live contract: 2 passed.
- Focused T4 live contract: 11 passed, including exact access and schema/grouping
  checks.
- Ruff formatting and lint, Python compilation, dependency consistency, whitespace,
  and Podman Compose configuration validation: passed.
- Full fast suite: 80 passed, 14 integration/E2E tests deselected.
- GitHub Actions: not executed because no pull request was created from this local
  handoff and branch pushes do not trigger the quality workflow.

## T5 — Odoo comparison-case enablement, Phase A

### Approval-checkpoint result on 2026-09-17

Phase A completed read-only and made no Odoo mutation. The branch starts exactly at
the T4 merge `e8eccf71f786e7a987fdbc47b0c3c88e8f40b5ef`.

The existing T4 live contract passed 11/11 before T5 changes. Additional bounded
JSON-2 discovery established that this exact Community database contains the
standard LGPL-3 `purchase_requisition` module, displayed as **Purchase Agreements**,
in `uninstalled` state. `res.config.settings` exposes
`module_purchase_requisition`. Matching Odoo 19 source defines
`purchase.order.group`, `purchase.order.purchase_group_id`, and related
`alternative_po_ids` as the supported call-for-tender grouping mechanism. These
expected post-install fields remain unvalidated in the database until installation
is explicitly approved.

The dedicated identity remains user ID 7, company ID 1 only, with direct groups
`Procurement RFQ API Reader` and `Role / User`. `purchase.order.line` read remains
denied. The minimal proposed access change is one read-only line ACL on the existing
custom group. The installed Purchase global line record rule already restricts rows
to `company_ids`; no broad Purchase or Inventory role and no duplicate rule is
proposed.

Runtime field metadata also sharpened two critical semantic gates:

- `product.supplierinfo.min_qty` is the quantity required to benefit from a
  vendor-price row, not a hard supplier order minimum. It is rejected as the current
  Decision Core MOQ source.
- `product.supplierinfo.delay` is configured time from PO confirmation to warehouse
  receipt, while line `date_planned` is Expected Arrival and defaults from that
  planning value. No supplier-offer promise or deterministic canonical lead-time
  transformation is yet established.

The adapter gate therefore remains `NO-GO`. Phase B may proceed only after explicit
approval for the exact module, ACL, human group, and controlled fixture mutations in
`docs/spikes/odoo-comparison-case-enablement.md`. No adapter, Decision Core change,
Odoo write, module installation, permission change, role assignment, business-data
mutation, PostgreSQL access, or Google Drive change occurred in Phase A.

### Phase B result on 2026-09-18

The user approved the exact Phase B proposal and confirmed a database backup. Using
the supported Odoo administrator UI, Phase B installed the standard Community
`purchase_requisition` module through **Purchase Agreements** and added one access
entry named `Purchase Order Line Read only access` for `purchase.order.line` on the
existing `Procurement RFQ API Reader` group. Only read is enabled; create, write,
and unlink remain denied.

The global **Purchase Alternatives** setting initially implied **Manage Purchase
Alternatives** to every internal user. A live contract detected that the integration
identity inherited the group. The setting was disabled immediately, and the group
was assigned directly to `Mitchell Admin`. Final validation proves that
`Procurement Integration` does not have the feature group and its direct groups
remain exactly `Procurement RFQ API Reader` and `Role / User`.

Final JSON-2 evidence verifies installed `purchase.order.purchase_group_id`,
`alternative_po_ids`, and `requisition_id`, plus `purchase.order.group.order_ids`.
The dedicated identity can read `purchase_group_id` and traverse permitted
`order_line` values without direct access to `purchase.order.group` or
`purchase.requisition`. Bounded line reads expose the exact product variant, UoM,
quantity, quotation unit price, discount, taxes, currency, company, expected
arrival, and selected supplier-price row. All observed rows belong to company 1,
and an explicit outside-company query returns no rows.

The semantic result remains `NO-GO`. `product.supplierinfo.min_qty` is still a
price-tier threshold rather than a hard supplier MOQ, and the available configured
delay and Expected Arrival fields do not establish authoritative supplier-offer lead
time. The approved pre-fixture stop gate therefore prevented creation of T5
suppliers, products, supplier rows, or alternative RFQs. No production adapter,
Decision Core change, direct database modification, application Odoo write, T6 work,
or Google Drive change was made.

Focused live Odoo verification passed 16 tests after the permission remediation.
Final verification also passed the full served integration selection with 19 tests,
the 80-test fast suite, Ruff format and lint, Python compilation, dependency
consistency, Podman Compose configuration, the Decision Core framework-import
boundary scan, the `.env` ignore check, and the final diff check. GitHub Actions
status is recorded in the external task handoff after the branch is pushed.
