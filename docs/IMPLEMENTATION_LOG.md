# Implementation log

This log is organised by development increment. It records evidence and decisions,
not a commit-by-commit diary.

## T13/T14 — post-merge documentation reconciliation (2026-10-05)

Verified through authenticated GitHub branch/PR/workflow/job reads: T13 PR #15
merged at `ff8cc5bfebaef5f8d73751991101008830307012`; T14 PR #16 merged at
`247914ac05663d7358d53036c08750d9390d1baa`, which is current remote main and
the clean entry HEAD of `feature/T15-implementation`. Local ancestry confirms T13.
The local SSH alias lookup failed and `gh` was unavailable; no fetch or remote-ref
update is claimed. The GitHub connector supplied current remote evidence.

On exact main SHA `247914a`, post-merge
[Quality 37358433437](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37358433437)
and [Container/API 37358433349](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37358433349)
are SUCCESS. Job steps verify actual Python 3.11 T13 CBC and controlled T14
training/reload/inference/MILP, plus integration, frontend compilation and technical
volume persistence. Earlier documentation-SHA Container/API run 37190288285 also
completed successfully after the prior handoff. T13 merge-SHA Quality 37155058879
and Container/API 37155058875 passed. Exact links and distinctions are in
`docs/T14_HANDOFF.md`; no new test counts are inferred from job summaries.

Historical local checks, the Podman socket failure, skipped service/live/browser
tests and synthetic limitations below remain unchanged. Full V2 and observed
Odoo/model promotion remain OPEN. The current tree cannot accept observed input.

Synchronized and read back all ten active Hungarian Drive living documents in
`SZAKDOLGOZAT/00_Project_Control` (00–08 and 99; 05 date only). Current merge/CI,
controlled T14, ADR-025 and requirement status now agree. Contradictory task-sheet
draft/advisor statements follow the issued/approved baseline already in 00/05;
the official PDF was not independently reread. Preserved historical limitations,
requirement IDs, native document structure/resource links and archives. Corrected
duplicate sync dates to one Hungarian native October 5 date chip. Saved original
reads and paragraph-level before/after review evidence; exact links are in the
handoff. Full V2 and observed-model promotion remain open, independently of the
controlled synthetic demonstration.

Fresh local Python 3.11 verification: 394 passed / 37 deselected / one upstream
Starlette warning in 33.85 s; Ruff format (132 files), lint, compilation, pip check
and whitespace check passed. Read-only Compose configuration passed after the
user started Podman, using the existing local provider outside the sandbox;
initial sandbox launches were denied. No service/live tests were run, so the
historical Podman socket failure and unverified live/browser gates are retained.

Prepared `docs/T15_IMPLEMENTATION_PLAN.md`: controlled assembly, trusted saved-model
inference, unchanged T13 MILP, explicit scenario reruns, immutable V2 snapshots and
stored-only GET/exact retry. Defines three narrow API operations and meaningful
acceptance checks; no frontend, approval/PDF, Odoo writes or speculative services.
This is a documentation-only proposal; T15 implementation is not authorized here.

## Historical T14 — controlled Decision Tree supplier-evaluation pipeline (2026-10-04)

Verified current remote main/T13 merge `ff8cc5bfebaef5f8d73751991101008830307012`,
clean entry tree and Python 3.11.16 328-pass legacy/T13 baseline. Read current
original Drive 00/02/03/06/07; their pre-merge status remains a dated record.
Branch `feature/t14-decision-tree-pipeline` starts from that main. Saved
`docs/T14_ML_DESIGN.md` before source implementation; inspected isolated ML spike
ffa2939 without merging its cumulative code.

Added `supplier_evaluation/` with controlled receipts and separate future label
evidence, existing T8 Expected Arrival KPI calculation, strict as-of/identity/group/
duplicate gates, fixed training-only DecisionTreeClassifier fit, trusted local
artifact manifest/checksum/runtime validation, actual float32 tree paths, explicit
metrics and a narrow T13 risk-input/CBC demonstration. Two quantity-independent
historical features replace the spike's quantity-100 mismatch. Coefficients are
versioned uncalibrated exposure proxies with complete declared quantity coverage;
synthetic models reject observed contexts, missing scores never become zero.

Seed 17; train 160 suppliers [43,117] at January 1, test 80 disjoint later suppliers
[24,56] at March 1. Confusion matrix [[23,1],[0,56]], accuracy 0.9875, macro F1
0.984937. Depth 3/five leaves. These measure an intentionally constructed noisy
synthetic mechanism, not real-world prediction quality. Actual inferred scores
produce a EUR 102 minimum-cost and EUR 109 lower-exposure plan under a 10% cost cap,
using unchanged T13 MILP semantics.

Required dependencies: sklearn 1.8.0, NumPy 2.3.5, SciPy 1.16.3, joblib 1.5.2 and
threadpoolctl 3.6.0, installed only under ignored project-local Python 3.11.16.
Quality CI installs and exercises real ML training/reload/inference/CBC, with no
optional runtime skips. Generated datasets/models/reports are ignored; the small
`docs/T14_EVALUATION.json` is reviewable evidence. README and AGENTS scope/commands
are updated. FR-V2-02/03, AC-V2-02/03 and FR-V2-07 tree explanation target LOCAL
PASS within controlled scope. Complete V2 and real prediction remain open.

Final full fast suite passed with 394 tests / 37 deselected in 48.22s, including
66 T14 tests; one upstream Starlette deprecation warning. Formatting (131 Python
files), lint, compileall, pip check and whitespace passed. Local Podman Compose validation FAILED with
127.0.0.1:64087 connection refused. Service/live Odoo/browser checks SKIPPED;
hosted T14 CI and real prediction UNVERIFIED. Exact executed evidence is in
`docs/T14_HANDOFF.md`, together with reproduction commands, measured metrics,
traceability, limitations and a proposed Drive synchronization summary.

No Decision Core/solver/WSM/API/history/persistence redesign, new Odoo assembly,
HTTP route, migration, Reflex, approval/PDF or Odoo mutation. T15 owns full
application/API/scenario/snapshot composition. Changes remain unstaged,
uncommitted and unpushed; no PR/merge or Drive write was performed.

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

## T6 — provenance-aware hybrid decision-input assembly

### Implementation on 2026-09-18

T6 starts from `main` commit `c2c4b18`, which contains the required T5 commit
`392e2482ce11aef9446722251b868d926f814a0a`. The unchanged baseline fast suite
passed 80 tests with 19 integration/E2E tests deselected.

The application now defines immutable typed Odoo comparison facts, supplemental
offer terms, per-field source attribution, a canonical input aggregate, a separate
provenance manifest, and `assemble_decision_input()`. The assembler accepts only the
explicit single-product T6 subset and raises stable `DecisionInputAssemblyError`
codes for incomplete, ambiguous, inconsistent, unsupported, or domain-invalid
input. It joins supplemental terms only by stable Odoo offer identity and passes no
provenance data into the unchanged Decision Core.

`OdooComparisonCaseReader` reads one explicit `purchase_group_id`, bounds the group
at 20 offers and 40 total lines, and retrieves orders, exact line identities, and
commercial-partner identities
through JSON-2. It requests quotation facts only. It does not request or map
`supplierinfo.min_qty`, `supplierinfo.delay`, or `date_planned`, and it preserves
unsupported states, discounts, and taxes so the application layer can reject the
complete case rather than silently dropping offers.

Fast tests cover the exact reference case, deterministic identity join, provenance,
all material fail-closed invariants, canonical domain errors, adapter transport and
mapping, and architectural boundaries. Two live contracts cover the controlled
fixture and complete Odoo-to-evaluation chain, but require both configured read-only
credentials and `RUN_T6_LIVE_CONTRACTS=true`.

The controlled fixture uses the specification's documented UI fallback rather than
an unvalidated administrator writer. Exact JSON-2 create/wizard defaults and safe
teardown semantics are not established in this repository, so automating those
writes would be a risky approximation. `docs/T6_FIXTURE_SETUP.md` defines exact
markers, values, rerun checks, read-only verification, and cleanup.

### Live acceptance closure on 2026-09-19

A human administrator created the controlled fixture through the Odoo UI with exact
source markers `T6-COMP-001-A`, `T6-COMP-001-B`, and `T6-COMP-001-C`. Automated
tests did not trust that manual claim: using only the configured dedicated
integration identity, they found exactly those three RFQs, proved that they share
one persisted `purchase_group_id`, read the complete orders, lines, and commercial
partners, and validated every supported-subset invariant. The same identity's live
security contracts confirmed denied mutations, absence of the alternatives feature
group, and company-scoped line visibility.

The live full-chain contract assembled the exact reference case, passed the
canonical input unchanged to the existing evaluation use case, ranked eligible
offers A then B, and excluded C with an explanation. Its provenance assertion was
strengthened during closure to require the exact path set for the requirement ID,
requested quantity, all three profile fields, and all five canonical fields for
each actual live offer ID. Requested-quantity provenance is required once per offer.

Closure verification on the local Windows stack produced:

- focused T6 live contracts: 2 passed, 16 deselected;
- Ruff format and lint: passed, with 58 files already formatted;
- Python compilation and dependency consistency: passed;
- fast selection: 120 passed, 21 deselected;
- full integration selection: 21 passed, 120 deselected;
- Podman Compose configuration and final diff check: passed.

All 15 T6 acceptance criteria are therefore satisfied for the controlled local
proof-of-concept scope. The public RFQ ledger and caller-supplied decision endpoint
remain deliberately disconnected; the hybrid assembly path is internal and must be
explicitly invoked. No automatic or production Odoo-to-evaluation integration is
claimed. Supplemental provenance establishes attribution, not objective truth, and
the documented single-product, safety-bound, no-conversion limitations remain.

## T7 — historical supplier-performance capability spike

### Read-only discovery on 2026-09-19

T7 starts exactly from the T6 merge commit
`01b9ff16d77934c2164d75ae6f4d938d98eedee3`. It performed bounded live discovery
through the configured `Procurement Integration` JSON-2 credential and made no Odoo
write, administrator-key fallback, permission change, direct database access, or
browser-automated UI action.

Runtime metadata and official Odoo 19 source establish an explicit candidate path
from `purchase.order.line.move_ids` to `stock.move.purchase_line_id`, then
`stock.move.picking_id` to `stock.picking`. Line `date_planned` is **Expected
Arrival**, an editable operational schedule value rather than a supplier-confirmed
promise. For a done stock move, `date` changes from scheduled date to actual move
processing date. A defensible actual receipt still requires done state, positive
actual quantity, supplier-to-internal direction, exact line relationship, matching
product/UoM/company, no return relationship, and a done picking.

The identity can read purchase orders, purchase-order lines, stock move lines,
picking types, and locations. It cannot read `stock.move` or `stock.picking`;
bounded record queries return HTTP 403. Five confirmed orders contained eight lines,
all with zero received quantity and no completed receipt. No existing record was
joined heuristically.

The security probe also found that standard Odoo 19 grants `base.group_user` full
create/write/unlink rights on `stock.move.line`. The dedicated identity inherits
those rights through `Role / User`. No mutation was attempted, but the identity is
not read-only for inventory operation lines. Adding an ordinary read ACL cannot
revoke additive Odoo ACL rights, and broad Inventory roles remain prohibited.

Exactly one controlled candidate is retained:
`delivery_schedule_adherence`, the percentage of eligible completed PO-line receipt
obligations whose full current ordered quantity reaches the internal warehouse by
Expected Arrival. It groups by the T6 commercial-partner identity, uses one line as
the measurement grain, reports a separate completed-line sample size, uses a
trailing half-open 365-day window, rounds only presentation to two decimal places,
and withholds the value below sample size 3. Partial, backorder, multi-receipt,
return, cancellation, quantity-change, replacement, missing-date, timezone,
over-receipt, company, and ambiguous-relationship policies are explicit and
fail-closed where evidence is insufficient.

Odoo's computed `on_time_rate` is rejected because it has no separately exposed
sample size, groups by direct partner rather than the T6 commercial entity, applies
a quantity-weighted policy, and is unreadable through the integration identity.
`product.supplierinfo.delay`, first-receipt `effective_date`, aggregate
`qty_received`, coarse `receipt_status`, and `stock.move.line.date` are also rejected
as sole project KPI sources.

The result is **PENDING CONTROLLED LIVE ACCEPTANCE**. The new opt-in T7 contracts
default to skipped behind `RUN_T7_LIVE_CONTRACTS=false`. They require a separately
approved company-scoped read-only inventory-history boundary and four exact manual
fixture markers covering on-time, late, backorder, and return behaviour. Expected
controlled evidence is `33.33%` with sample size 3 and the return-affected line
excluded with a warning. No production KPI code, adapter, API, frontend, persistence,
Decision Core, `SupplierOffer`, `StrategicProfile`, T6 contract, or provenance change
was introduced. AC-07 remains unsatisfied.

See `docs/spikes/odoo-historical-supplier-performance.md` for the evidence matrix,
`docs/T7_FIXTURE_SETUP.md` for the mandatory security stop and human UI procedure,
and `docs/T7_HANDOFF.md` for the acceptance decision and T8 consequences.

Final local verification passed Ruff format and lint, Python compilation, dependency
consistency, Podman Compose configuration, whitespace checks, 121 fast tests, and
the complete available integration selection with 21 passed and the two gated T7
contracts skipped. Those contracts were not enabled because their documented
security and controlled-fixture prerequisites do not exist. Existing warnings were
limited to dependency deprecations, a local pytest-cache permission warning, and Git
line-ending conversion notices.

## T7-S — company-scoped read-only inventory-history projection

### Separate prerequisite implementation on 2026-09-19

T7-S is intentionally separate from the original T7 capability spike. It starts
from T7 commit `a47b035d48b89b604442a900b5f08a103bdd48a3` on branch
`codex/t7s-company-scoped-read-only-inventory-history-projection` and does not
retroactively expand T7's committed scope.

The implementation compares a generic `_auto = False` projection, a custom model
method, stored/transient projections, a custom controller, and direct stock-model
ACLs. It selects a public method on an Odoo `AbstractModel`. The addon creates no
table, stored copy, menu, view, or generic model ACL. Its custom group implies no
internal, Purchase, or Inventory role.

The existing internal `Procurement Integration` user remains unchanged for T6.
Because its standard internal-user role already carries additive
`stock.move.line` rights, T7-S instead defines a dedicated non-internal projection
caller and separate `ODOO_T7S_API_KEY`. The caller can invoke only the guarded
method and must remain denied generic access to the projection and to
`stock.picking`, `stock.move`, and `stock.move.line`.

`read_bounded_history` requires the active authorized company, a strict half-open
historical window no longer than 366 days, 1–50 exact purchase-order-line IDs, and a
result limit no greater than 200. The fixed response contains only stable company,
commercial supplier, PO/line, product/UoM, Expected Arrival, move/picking, done
processing timestamp, quantity, direction, backorder, and return evidence. Expected
Arrival remains an operational schedule and is not represented as a supplier
promise.

The dedicated caller deliberately lacks the underlying ACLs, so five private ORM
readers use elevated access. Every `sudo()` call is immediately followed by a fixed
`search_fetch` whose model, fields, company, exact relationships, date window, and
row bound were established before the read. No raw SQL or sudoed recordset leaves
the addon. Truncation, cross-company relations, unsupported states/directions,
missing or mismatched product/UoM/picking links, timestamp disagreement, and
backorder/return relationships outside the bounded result reject the entire call.

Fast policy tests cover bounds, exact output fields, company isolation, unsupported
states and directions, ambiguous returns and backorders, absence of raw SQL and
generic ACLs, and absence of implied broad roles. The opt-in live contract adds
same-company success, direct-model denials, projection CRUD denials, cross-company
rejection, and invalid-query rejection. The original T7 controlled test now reads
stock evidence only through the projection; it still computes no production KPI.

The Compose configuration mounts `infra/odoo/addons` read-only. A human
administrator installed the addon and configured the dedicated portal caller,
projection group, and short-lived API key; no Odoo UI action was automated.
`docs/T7S_MANUAL_SETUP.md` now documents both why the separate identity is required
and Odoo 19's temporary **Customers can generate API Keys** portal setting.

### Focused live security acceptance on 2026-09-20

The first focused run exposed a test-fixture selection error rather than a security
failure: the test chose an arbitrary purchased line whose `qty_received_method` was
`manual`, and the projection correctly failed closed with HTTP 422. The positive
security probe now selects a `stock_moves` line and uses a bounded known-empty
pre-fixture window, keeping semantic receipt evidence reserved for the controlled T7
fixture. The negative request assertions now expect Odoo 19's observed HTTP 422 for
model validation and unexpected method arguments.

The corrected focused command passed with **1 passed, 19 deselected**. It proved
same-company bounded access, a fixed response envelope, false generic CRUD rights on
the projection and all three stock models, HTTP 403 direct stock reads, HTTP 403
cross-company access, and HTTP 422 rejection of missing bounds, empty line IDs,
excessive limits, arbitrary arguments, and a 367-day window. The live gate was
immediately returned to `false`; the API key remains only in the ignored `.env`.

T7-S is now **COMPLETE — T7 LIVE VALIDATION MAY RESUME**. This permits the manual
controlled receipt fixture and original T7 live validation; it does not implement a
historical KPI or change T7 to `GO`.

### T7 controlled live acceptance on 2026-09-20

A human administrator created the four exact T7 receipt scenarios. The first live
run found a projection-policy contradiction rather than a fixture error: Odoo 19
represents the explicit internal-to-supplier return with an `outgoing` picking, while
the policy allowed the return move direction but required every picking to be
`incoming`. The correction permits `outgoing` only when every move in that picking
has the validated internal-to-supplier direction; the existing move and picking
return-link checks still require the exact original move and picking inside the
bounded result. New fast tests cover a complete accepted return and rejection of an
outgoing ordinary receipt.

After reloading only the Odoo service, the focused T7-S/T7 selection passed **2 of
2** and the complete integration selection passed **23 of 23**. Live evidence proved
one shared company, commercial supplier, product, and UoM; done move/picking
timestamp agreement; one on-time line; one late line; one late two-picking
backorder; and one explicit supplier return excluded from the candidate sample. The
controlled result is `delivery_schedule_adherence = 33.33%`, sample size `3`. Both
live gates were returned to `false`.

T7 is now **GO — CONTROLLED LIVE SUBSET ACCEPTED**. This authorizes only a later
narrow implementation over the accepted projection and edge-case policy. No KPI was
added to the Decision Core, application layer, API, frontend, or persistence, and
AC-07 remains unsatisfied.

## T8 — historical supplier-performance vertical slice

### Implemented on 2026-09-20

T8 starts from merged T7/T7-S `main` commit
`af8297c09a4043e2fa7f0a80e9b6ea795cc7ab85` on branch
`codex/t8-historical-kpi-vertical-slice`. The pre-change fast baseline was 141
passed and 23 deselected.

The increment adds an ERP-neutral `HistoricalPerformancePort`, bounded query,
receipt observation, snapshot, historical metric, availability, warning, and sourced
result contracts in `application/historical_performance.py`. The application
calculator implements the accepted line-count-weighted
`delivery_schedule_adherence` policy over an exact half-open 365-day window. It uses
the first cumulative full-receipt timestamp per line, keeps sample size separate,
rounds the percentage half up to two decimal places, excludes return-affected lines
with a structured warning, and withholds rather than substitutes a value below the
minimum sample size of three.

`OdooHistoricalPerformanceReader` implements the port using only
`procurement.inventory.history.projection.read_bounded_history`. It maps the fixed
T7-S response into neutral models after validating the full envelope/schema,
version, echoed company/window, count, requested line set, commercial supplier,
timestamps, state, direction, quantities, and stable identities. It adds no generic
stock-model read, Odoo mutation, direct database access, administrator credential,
or runtime fixture path. The T7-S addon and permissions are unchanged.

`CanonicalDecisionInput` now contains a tuple of contextual
`SupplierHistoricalPerformance` values. `attach_historical_performance()` joins by
stable supplier identity and requires a complete, unique mapping for the offer set.
It appends value, sample-size, and window provenance to the separate application
manifest. Source references identify the bounded projection context without secrets
or truth claims. Existing T6 callers remain compatible with an empty history tuple.

No Decision Core model, WSM formula, criterion, normalization, profile weight, MOQ
constraint, contribution, ranking, or explanation changed. Unit and controlled live
regressions compare the full result before and after history attachment.

Fast tests cover all-on-time, all-late, mixed, exact-deadline, immediately-late,
partial/multiple receipt, backorder, return, cancellation, zero denominator, sample
sizes 0/1/2/3, half-open boundaries, stable identities, warning order, rounding,
adapter request/response bounds, provenance, complete joins, and architecture.
Focused tests passed 72 of 72; the full fast selection passed 180 with 23
deselected. The focused live T7-S/T8 selection passed 2 of 2, and the complete live
integration selection passed 23 with 180 deselected.

The controlled production adapter/calculator result is
`delivery_schedule_adherence = 33.33`, sample size `3`: one on-time line, one late
line, one late two-picking backorder, and one return-affected line excluded with
`supplier_return_observed`. The same run revalidated company rejection, generic
stock access and mutation denials, canonical attachment, bounded provenance, and
unchanged ranking.

T8 is **GO — CONTROLLED VERTICAL SLICE IMPLEMENTED AND LIVE-VERIFIED**. AC-07 is
satisfied for the bounded internal slice. Public API/UI exposure, persistence,
arbitrary history discovery, and weighted scoring remain out of scope. Any future
scoring change requires explicit normalization, weights, missing-history policy,
sensitivity analysis, regression evidence, and an ADR or approved amendment.

## T9 — historical KPI scoring design and evaluation

### Implemented on 2026-09-20

T9 started from fetched, merged T8 `main` commit
`948c0928f74f6ec824a2185094164c1e59caf2eb` on branch
`codex/t9-historical-scoring-design-evaluation`. Before branching, the fast suite
passed with 180 tests and 23 deselected, `CanonicalDecisionInput` was confirmed to
contain contextual history, and the T8 AC-07 evidence was confirmed.

The increment adds an isolated Decimal-based evaluator under `tools/`, focused tests,
an ADR-style design/amendment proposal, and a handoff. It compares direct percentage,
comparison-set min–max, and illustrative band normalization; complete-case,
per-offer renormalization, neutral imputation, conservative imputation, and exclusion
policies; candidate weights for cost-focused, urgent, and risk-averse profiles; and
all 15 required deterministic scenarios. It also emits complete contribution traces,
baseline/candidate rankings, exact pairwise flip thresholds, missing-policy
sensitivity, and an add/remove-alternative experiment.

The evaluation recommends direct `value / 100` normalization and activation only
when every MOQ-eligible offer has usable history. Incomplete history falls back to
the exact current two-criterion scoring. Sample size remains an availability and
explanation field with the accepted minimum of three; T9 adds no confidence weighting
or bands because no defensible calibration exists. Candidate price/lead/history
weights are `.60/.25/.15` for cost-focused, `.25/.60/.15` for urgent, and
`.30/.30/.40` for a proposed risk-averse profile. They are PoC policy candidates,
not empirical optima.

Direct normalization remained stable in the controlled add/remove experiment,
whereas min–max reversed A and B after a third supplier changed only the historical
bound. The close-value case showed min–max expanding `79.99/80.00/80.01` to
`0/.5/1`. Missing-data alternatives changed rankings or removed an offer, supporting
the complete-case recommendation. The proposed profile matrix produced intentional
ranking changes in S04, S10, S11, and S15 while preserving MOQ-first exclusion and
deterministic tie-breaking.

T9 is **GO — BOUNDED POC SCORING IMPLEMENTATION AUTHORIZED** under the exact contract
in `docs/T9_SCORING_DESIGN.md`. This is not production validation. The minimum sample
size of three is not proof of statistical reliability, Expected Arrival remains an
operational schedule, and the weights are not learned. No Decision Core, runtime
profile, API, application/Odoo adapter, persistence, frontend, infrastructure, or
live fixture behaviour changed in T9.

## T10 — bounded, opt-in historical performance scoring

### Implemented on 2026-09-21

T10 started from fetched, merged T9 `main` commit
`58e3cfe92c8766093274571b87ad81af8b1bc8a1` on branch
`codex/t10-bounded-historical-scoring`. Before branching, local `main` equalled
`origin/main`, the accepted T9 design and handoff were present, and the fast baseline
passed with 197 tests and 23 deselected.

The Decision Core now has a small ERP-neutral historical input carrying stable
supplier identity, metric, value, sample size, and availability. A separate
`HistoricalScoringProfile` exposes the three accepted versioned policies, and
`evaluate_historical_decision()` is the only opt-in core entry point. The existing
`evaluate_decision()` and `StrategicProfile.cost_focused()`, `.urgent()`, and
`.balanced()` remain the default and preserve their weights and behaviour.

Both paths use one shared WSM scoring implementation. MOQ eligibility is partitioned
first. History activates only for a non-empty eligible set in which every offer's
supplier has one usable `delivery_schedule_adherence` value with `n >= 3`. Active
history is normalized only as `value / 100`; its contribution includes raw value,
sample size, normalized value, weight, weighted value, and deterministic text. If an
eligible offer lacks usable history, the wrapper returns the exact legacy
`DecisionResult` plus deterministic inactive context and sorted affected identities.
No value is imputed, no weight is redistributed, and no offer is penalized or
excluded for missing history.

The application adds an explicit mapper from T8 `SupplierHistoricalPerformance` to
the smaller core contract. It passes no source, warning, window, or provenance data
and rejects a selected historical policy whose fixed legacy fallback does not match
the canonical profile. Supplier joins use only stable IDs; duplicate and unknown
history fail closed, while multiple offers from one supplier share one history
result deterministically.

`tests/test_historical_scoring.py` converts the complete T9 S01–S15 matrix into
runtime parity regressions and adds validation for fallback equality, contribution
reconstruction, endpoints, the controlled `33.33`/`n=3` value, sample sizes 0–3,
invalid/non-finite values, duplicate and unknown suppliers, shared suppliers,
MOQ-ineligible history, all-excluded input, deterministic ordering, application
mapping, and unchanged legacy behaviour. Architecture tests prove the core remains
ERP/provenance independent and runtime packages do not import T9 tooling. Public API
schemas and routes, Odoo projection/adapter behaviour, persistence, and frontend are
unchanged.

The profile weights and `n >= 3` threshold remain PoC policy choices, not empirical
optimization or statistical reliability evidence. See `docs/T10_HANDOFF.md` for the
full command evidence, acceptance matrix, hosted CI status, limitations, and final
decision.

## T11 — decision-case persistence and human final-decision recording

### Implemented on 2026-09-22

T11 started from fetched, merged T10 `main` commit
`6f691ec31e64ad2763d477475b581c8c41bf2c3a`, the merge commit for PR #11. Local
`main` and `origin/main` matched after `git fetch --prune`; `docs/T10_HANDOFF.md`
contained the final merge-ready GO and passed hosted Quality, container/API, and
CodeRabbit evidence. The pre-change fast baseline passed with 222 tests and 23
deselected on Python 3.14.7.

The application now defines immutable `DecisionCase`, `HumanDecision`, and command
contracts, plus narrow repository/unit-of-work ports and three use cases: store an
evaluated case, retrieve it without recalculation, and record one human final
decision. Acceptance requires the stored recommendation; override requires a
different eligible offer and a non-empty rationale; no award forbids a selected
offer and requires a rationale. Unknown or excluded offers fail closed. Actor
references are caller-supplied attribution only.

Snapshot schema version `1` explicitly serializes canonical inputs, selected scoring
policy, legacy or T10 historical evaluation results, and provenance as separate JSON
documents. Decimal values use plain exact strings and times use UTC `Z` notation.
The historical form preserves activation/fallback context, affected identities,
sample sizes, deterministic explanations, rankings, exclusions, and ordered
criterion contributions. Unknown versions fail instead of being interpreted.

The concrete adapter uses SQLAlchemy 2.x and psycopg with PostgreSQL JSONB. Alembic
migration `20260922_01` creates the `decision_cases` table, relational lifecycle and
identity columns, checks, a unique idempotency key, and a trigger that rejects any
snapshot mutation and every post-finalization change. Final-decision fields and the
state transition commit in one transaction. Identical retries with the same key and
payload return the prior record; conflicting reuse or later decisions fail closed.
Application startup does not create schema objects.

Local focused unit/architecture checks passed with 35 tests. The full fast suite
passed with 246 tests and 32 deselected. The isolated PostgreSQL suite passed with 9
tests, including clean migration, three snapshot variants across separate sessions,
rollback, database immutability, uniqueness, sequential double-finalization, and
idempotency. Hosted CI remains pending until the branch is pushed and reviewed, so
T11 must not yet be described as final GO. See `docs/T11_HANDOFF.md` for the complete
acceptance status and excluded scope.

The complete integration selection also passed with 28 tests, 4 controlled live
fixture gates skipped because their opt-in flags were explicitly disabled, and 246
fast tests deselected. Both Compose models validated. The run used temporary
localhost-only tunnels for the known Podman Windows forwarding fault, then stopped
the backend, containers, tunnels, and Podman machine while preserving Odoo volumes.

## T12 — controlled end-to-end orchestration API (2026-09-22)

Starting `origin/main`: `0a1eee8a323f6cfe68a5cc30319d1f8c058d5c26`
(merged T11 / PR #12). Branch: `codex/t12-controlled-e2e-orchestration-api`.
Pre-change fast baseline: 246 passed, 32 deselected. Ruff format, Ruff check,
compileall, and pip check passed before implementation.

Added an application coordinator using the existing bounded comparison-case reader,
T6 supplemental assembler, optional T8/T7-S history path, accepted T10 policy
selection/evaluation, and T11 case repository. The three versioned decision-case
routes require a shared PoC bearer token; it does not authenticate the buyer or
`actor_reference`. GET reconstructs stored snapshots and never refreshes live data.
The original T3 evaluate route is unchanged. No Odoo write or frontend path was
added.

Alembic `20260922_02` adds durable creation idempotency with a canonical UUID key,
normalized SHA-256 request fingerprint, transaction advisory lock, and a unique
foreign key to the decision case. The key mapping and case commit atomically; exact
replay skips all upstream reads and scoring. T11's human-finalization idempotency and
immutable trigger remain separate and unchanged.

Verification and limitations are recorded in `docs/T12_HANDOFF.md`. This increment
does not discover arbitrary supplier history, verify supplemental values as facts,
provide production identity management, create a decision frontend, or write to
Odoo. The controlled T6 and T7 history fixtures are separate; no three-supplier
live historical-scoring claim is made.

## T13 — V2 domain and application-ready MILP procurement planning core

Live current Drive baseline, requirements, roadmap, development status and
ADR-024–027 were read before implementation. Entry GO followed verified remote
main `71396e8924f6a1f60daf8b45f02861adf21a25e5`, preservation of pre-existing
Reflex lockfile state, 271-pass legacy baseline and existing hosted-check review.
Branch `feature/t13-v2-milp-core` starts from that main; the cumulative experimental
PR #14 was selectively used as reference and remains unmerged.

Added frozen ERP-neutral requirement/supplier/policy/plan contracts under
`decision_core/planning/`, exact eligibility/output rules, a solver port and
deterministic minimum-cost/epsilon orchestration. `optimization_adapter/` implements
provisional PuLP/CBC with integer scaling, exact constraint checks, stable objective
locks, explicit solver statuses and one shared time budget. The thin application
entry point keeps external risk definition/assessment/validity context separate.
Coefficients must cover all allowed allocation quantities; missing scores never
become zero. No ML feature-schema decision or training was made.

PuLP 3.3.0 is required and the Python 3.11 quality job explicitly executes the
actual CBC runtime gate without optional skips. A project-local Python 3.11.16
environment verified CBC 2.10.3 and the entire fast suite: 328 passed, 37 deselected
in 10.47s, one upstream warning. All 57 T13 tests also passed on Python 3.14.7.
Ruff format/lint, compileall, pip check and whitespace checks passed. Podman Compose
validation FAILED because its machine socket refused connection; live integration
and browser checks were SKIPPED. Hosted T13 runs remain UNVERIFIED.

FR-V2-04–06 and AC-V2-04–07 are implemented/LOCAL PASS for this bounded core.
FR-V2-07 is PARTIAL because ML tree-path explanations belong to T14. Existing
WSM/API behavior and immutable version-1 T11/T12 snapshots, stored retrieval and
retry semantics remain unchanged. No new Odoo assembly/API, database migration,
Reflex integration, approval/PDF path or Odoo mutation was added. Changes are local,
uncommitted and unmerged. Design, exact evidence, file map and T14 questions are
recorded in `docs/T13_V2_MILP_DESIGN.md` and `docs/T13_HANDOFF.md`.
