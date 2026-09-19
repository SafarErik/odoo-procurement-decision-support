# Odoo Procurement Decision Support

Development foundation for a BSc thesis proof of concept: an explainable,
ERP-independent procurement decision-support system integrated with Odoo. The
system will evaluate known supplier offers and provide a recommendation while
leaving the final selection to a human decision-maker.

**Current status:** T0, the read-only T1 Odoo RFQ slice, the ERP-independent T2
Decision Core, and the narrow T3 decision API are implemented. T4 completed live,
read-only Odoo decision-input discovery. T5 installed the standard Purchase
Agreements capability and added least-privilege, company-scoped
`purchase.order.line` reads for the dedicated integration identity. The standard
`purchase_group_id` comparison key is now available, but Odoo's supplier quantity is
a price-tier threshold rather than a hard MOQ and the available dates do not prove
authoritative supplier-offer lead time. T5 therefore ended `NO-GO`; no production
adapter was implemented. T6 provides a narrow, fail-closed hybrid assembler:
validated Odoo comparison facts can be combined with explicitly supplied,
source-attributed hard MOQ and supplier-promised lead time while provenance stays
outside the Decision Core. The application can retrieve open RFQ summaries through
the existing public read-only ledger. Separately,
`POST /api/v1/procurement/decisions/evaluate` evaluates caller-supplied canonical
requirements, offers, and weights through the Decision Core. These public flows
remain deliberately unconnected. T6 provides only an internal, explicitly invoked
hybrid assembly path for the validated comparison-case subset; it does not provide
automatic RFQ evaluation or a production Odoo-to-decision pipeline. There is still
no decision UI, historical KPI calculation, write operation, or production
persistence. T7 completed read-only historical-performance discovery and identified
one candidate, `delivery_schedule_adherence`, but ended
`PENDING CONTROLLED LIVE ACCEPTANCE`: `stock.move` and `stock.picking` reads are
denied, the internal integration identity inherits mutation rights on
`stock.move.line`, and no completed controlled receipt history exists. No historical
KPI runtime code was added and AC-07 remains unsatisfied. See
[the T7 spike](docs/spikes/odoo-historical-supplier-performance.md),
[fixture procedure](docs/T7_FIXTURE_SETUP.md), and [T7 handoff](docs/T7_HANDOFF.md),
plus the separate T7-S [design](docs/T7S_DESIGN_SECURITY.md),
[manual setup](docs/T7S_MANUAL_SETUP.md), and [handoff](docs/T7S_HANDOFF.md).
T7-S implements a bounded method-only projection but remains
`PENDING MANUAL ODOO SETUP`; it does not change T7's pending outcome. See also
[the T6 design](docs/T6_DESIGN.md),
[T6 fixture procedure](docs/T6_FIXTURE_SETUP.md), and [T6 handoff](docs/T6_HANDOFF.md)
for the current boundary and evidence.

## Architecture

```text
Reflex frontend --HTTP--> FastAPI API --> application RFQ use case
                                               |
                                               +--> Odoo adapter --JSON-2--> Odoo

caller JSON --> FastAPI decision schemas --> application decision use case
                                             |
                                             +--> Decision Core --> explained result

Odoo facts + attributed supplemental terms --> application T6 assembler
                                                        |
                                                        +--> canonical input
                                                        +--> provenance manifest

dedicated non-internal T7-S caller --JSON-2--> guarded Odoo projection method
                                                    |
                                                    +--> bounded ORM evidence only
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
decision_core/  ERP-independent constraint, normalization, WSM, and ranking logic
odoo_adapter/   Read-only Odoo JSON-2 transport and mapping
infra/odoo/     Local Odoo/PostgreSQL Compose and isolated T7-S addon
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
random local-development secrets. The validated local setup uses the internal
`Procurement Integration` user, limited to the current company, with a custom
`Procurement RFQ API Reader` group granting the documented read-only order and
decision-input model access, including `purchase.order.line`. Mutation rights remain
denied.
Do not assign the standard Purchase User/Administrator or Inventory roles: they
grant broader capabilities than this adapter needs. Generate the API key from that
dedicated user's preferences and set `ODOO_DATABASE` and `ODOO_API_KEY` in `.env`.
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
- Decision evaluation: <http://127.0.0.1:8000/api/v1/procurement/decisions/evaluate>
- FastAPI OpenAPI UI: <http://127.0.0.1:8000/docs>
- Reflex frontend: the URL printed by `reflex run` (normally `http://localhost:3000`)
- Odoo: `http://127.0.0.1:<ODOO_HTTP_PORT>` (default `http://127.0.0.1:8069`)

The API health response is stable and infrastructure-free:

```json
{"status":"ok","service":"procurement-decision-support-api","api_version":"v1"}
```

## Decision evaluation API

The synchronous decision endpoint accepts only canonical data in its request body.
It does not query Odoo, read environment-specific business data, persist a result,
or perform any write operation. All decision-relevant numeric values are JSON
strings and are converted directly to `Decimal`; binary floating-point is not used.

```http
POST /api/v1/procurement/decisions/evaluate
Content-Type: application/json
```

```json
{
  "requirement": {"requirement_id": "REQ-1", "requested_quantity": "100"},
  "offers": [
    {
      "offer_id": "Offer A",
      "supplier_id": "Supplier A",
      "unit_price": "10",
      "lead_time_days": "10",
      "minimum_order_quantity": "50"
    }
  ],
  "profile": {
    "name": "balanced",
    "unit_price_weight": "0.5",
    "lead_time_weight": "0.5"
  }
}
```

HTTP 200 returns the requirement and profile, the first-ranked offer or `null`, all
eligible offers with their relative WSM scores and criterion contributions, and all
excluded offers with their failed constraints. Malformed request structure or
decimal syntax returns FastAPI's normal HTTP 422 validation response. Valid syntax
that violates a domain invariant returns HTTP 422 with code
`invalid_decision_input`. An all-excluded evaluation is a valid HTTP 200 result with
an empty ranking and no recommendation. The recommendation is decision support for a
human; it is not an automated supplier selection or purchase decision.

PostgreSQL has a container health check. Odoo's official image does not expose a
documented, image-level health command in this setup, so verify it through the web
UI and container logs after startup.

## Formatting, linting, testing, and configuration validation

```powershell
ruff format --check .
ruff check .
python -m compileall application backend frontend decision_core odoo_adapter infra/odoo/addons/t7s_inventory_history_projection
pytest -m "not integration and not e2e" -v
python -m pip check
podman compose --env-file .env -f infra/odoo/compose.yaml config
```

Run these after every material change. Unmarked tests are fast. Tests requiring
running application or infrastructure components use the `integration` marker;
browser-level full-flow tests use the reserved `e2e` marker. Strict marker checking
prevents misspelled categories from silently running in the wrong suite.

The fast tests cover Decision Core validation, constraints, normalization, WSM
contributions and deterministic ranking; the application decision use case and API
contract; the health contract; the ERP-neutral RFQ API; Odoo JSON-2 request and
mapping behaviour; stable upstream error translation; frontend configuration and
presentation states; the T6 supported-subset invariants, provenance, architectural
boundaries, read-only comparison-case mapping, and T7-S bounded projection security
policy; and the separate Reflex
state-backend port. With the documented runtime services running and the ignored
`.env` configured, integration tests can be selected explicitly:

```powershell
pytest -m "integration and not e2e" -v
```

The controlled T6 live contracts additionally require the exact fixture in
`docs/T6_FIXTURE_SETUP.md` and `RUN_T6_LIVE_CONTRACTS=true`. They skip otherwise and
must never be enabled against an arbitrary external database.

The T7-S security contract requires the manual addon, dedicated non-internal caller,
and key setup in `docs/T7S_MANUAL_SETUP.md`, plus
`RUN_T7S_LIVE_CONTRACTS=true`. Only after that focused contract passes may the T7
fixture be created. Final T7 validation requires both live gates and the exact
fixture in `docs/T7_FIXTURE_SETUP.md`. Both gates skip by default.

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

This milestone was manually verified on 2026-09-16: seven RFQs rendered with every
listed field, refresh succeeded, stopping FastAPI produced the unavailable state
without stale rows, and restarting it restored the ledger. A temporary invalid
integration key also produced the stable API error and the same safe UI state.

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
`purchase.order` summary fields required by the RFQ ledger. The Decision Core and
decision API currently support only MOQ eligibility plus unit-price and lead-time
criteria on caller-supplied canonical input. T6 adds only a narrow hybrid assembly
path for a validated single-product comparison subset; it is not a generic or public
Odoo-to-canonical API. There is no automatic RFQ evaluation, pagination, retry
policy, write operation,
decision UI, API authentication/authorization, production persistence, historical
KPI logic, currency conversion, or validated purchase-line and inventory receipt
mapping. The local PoC uses a live-verified dedicated read-only integration identity.
T5 proved company-scoped read access to `purchase.order.line` and the standard
`purchase.order.purchase_group_id` comparison key without granting the integration
identity the alternatives feature group or direct access to grouping/agreement
models. A production Odoo-to-canonical adapter remains deferred because no validated
hard-MOQ source or authoritative supplier-offer lead time is available, and the
approved T6 solution therefore requires explicit, source-attributed supplemental
terms. The controlled three-RFQ T6 fixture and full read-only hybrid chain passed
their opt-in live contracts on 2026-09-19. This evidence validates only the bounded
local proof-of-concept subset and does not turn the internal assembler into an
automatic or production Odoo-to-decision pipeline. Do not assign broad Purchase or
Inventory roles as a shortcut.

T7 found a candidate purchase-line-to-receipt chain and defined
`delivery_schedule_adherence` against Odoo Expected Arrival with a separate
completed-line sample size. It is not implemented. The configured identity cannot
read `stock.move` or `stock.picking`, and standard Odoo 19 grants every internal user
create/write/unlink access to `stock.move.line`; therefore the inventory-history
boundary is not currently read-only. T7-S now provides the separately scoped
security design: a method-only, non-stored projection with mandatory company,
exact-line, date, and count bounds, called by a separate non-internal identity. Its
addon installation, group assignment, key creation, and focused live contract are
still pending manual setup. The controlled fixture must also pass before any
production historical-performance adapter is considered.
`product.supplierinfo.delay`, Odoo's computed `on_time_rate`, first
receipt `effective_date`, and heuristic joins remain rejected project KPI sources.
The old
administrator discovery key should be revoked. Image tags are explicit but are not
digest-pinned.
The frontend has no automated browser end-to-end test suite.
See [the implementation log](docs/IMPLEMENTATION_LOG.md) and
[the T5 comparison-case evidence](docs/spikes/odoo-comparison-case-enablement.md),
[the T6 design](docs/T6_DESIGN.md), and
[the T7 historical-performance evidence](docs/spikes/odoo-historical-supplier-performance.md),
plus [the T7-S security design](docs/T7S_DESIGN_SECURITY.md)
for verified facts, rejected mappings, and recovery steps.

The CI persistence check uses synthetic files to verify only that Docker named
volumes survive stack recreation. It does not establish persistence of an actual
Odoo business scenario. That evidence must come later from the implemented Odoo
integration flow.
