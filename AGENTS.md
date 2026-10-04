# Development guidance

## Current V2 scope and historical increments

T14 adds the controlled offline Decision Tree pipeline under `supplier_evaluation/`
and its narrow T13 risk-contract demonstration. See `docs/T14_ML_DESIGN.md` and
`docs/T14_HANDOFF.md`. ML dependencies and trusted artifact loading stay outside
the ERP-neutral planning core. Synthetic evidence is not a validated real-world
predictor. T14 adds no live Odoo discovery/write, HTTP route, database migration,
Reflex, approval/PDF or full T15 orchestration.

T13 authorizes the immutable one-product V2 planning model and application-ready
MILP core. Keep solver infrastructure behind `optimization_adapter/`; the
ERP-neutral `decision_core/planning/` uses a solver port. It does not authorize ML
training, new Odoo assembly, V2 HTTP routes, migrations, Reflex integration,
approval or PDF export. Preserve existing WSM/API behavior and T11/T12 version-1
snapshots and stored-only retrieval/retry semantics. See `docs/T13_V2_MILP_DESIGN.md`
and `docs/T13_HANDOFF.md` for supported input and numerical contracts.

The T0 and first read-only RFQ increment below are historical scope records;
they do not prohibit explicitly authorized later increments.

## Historical T0 scope

T0 establishes the local development foundation, a minimal FastAPI health API, a
minimal separate Reflex frontend, Odoo Compose configuration, automated checks,
and an evidence-based Odoo capability spike. It does not implement procurement
decision logic, rankings, constraints, KPIs, persistence schemas, or a final
domain model.

## Historical first read-only integration scope

The first post-T0 increment validates a narrow Odoo 19 JSON-2 path for listing open
`purchase.order` records. It may expose only the verified RFQ summary through the
ERP-neutral application contract. It does not authorize Odoo writes, scoring,
ranking, supplier recommendations, purchase-line or receipt mappings, or a broader
canonical procurement model.

## Architectural boundaries

- Keep the Decision Core independent of Odoo, FastAPI, Reflex, and database frameworks.
- Keep Odoo communication and mapping behind `odoo_adapter/`; never access the Odoo database directly.
- The frontend communicates only with the documented backend HTTP API. It must not access Odoo or a database.
- Keep FastAPI route handlers thin and keep business logic out of Reflex components and route handlers.
- The application layer orchestrates use cases; it must not own infrastructure-specific logic.
- Do not invent or rely on unvalidated Odoo models, fields, authentication details, or API capabilities.
- Never commit secrets. Keep local values in the ignored `.env` file.

## Manual Odoo UI operations

- Do not control the user's Odoo browser session or perform Odoo UI actions through
  computer-use, browser-automation, or similar GUI tools.
- When Odoo configuration or business-data entry is required, stop before the UI
  mutation and give the user clear numbered instructions. Include the exact Odoo
  application and menu path, field or setting labels, values to enter, buttons to
  press, expected effect, and any relevant rollback or safety note.
- Wait for the user to confirm that the instructions were completed before relying
  on the changed state or continuing with dependent validation.
- Do not claim that an Odoo UI change succeeded based only on the instructions.
  Confirm the postcondition with an authorized read-only probe or test when possible;
  otherwise record it explicitly as user-confirmed and not independently verified.
- This manual handoff rule applies even when a task plan or handoff document suggests
  that the agent perform the Odoo UI steps. Continue to prohibit application Odoo
  writes and direct database access unless the repository scope is explicitly changed.

## Language and documentation

Use English for all repository software-engineering artifacts, including source,
tests, logs, UI strings, documentation, branches, and commits. Preserve official
external names where appropriate. Update `README.md`, `docs/IMPLEMENTATION_LOG.md`,
and relevant spike documentation when implementation or verified facts change.
The repository is the primary source of truth for executable implementation
artifacts: source code, tests, workflows, Compose configuration, and technical
implementation logs. Google Drive is the primary source of truth for the Hungarian
thesis living documentation, project status, roadmap, requirements baseline, and
architectural decision records. Google Drive thesis documents must not be changed
unless the user explicitly asks.

## Commands

Use Python 3.11 as the local and CI compatibility baseline. `requires-python =
">=3.11"` permits later compatible versions, but do not change the baseline or add
a CI version matrix without documenting the compatibility reason.

After creating and activating a Python 3.11 virtual environment:

```powershell
python -m pip install -e ".[frontend,dev]"
ruff format --check .
ruff check .
python -m compileall application backend frontend decision_core odoo_adapter optimization_adapter supplier_evaluation persistence migrations
pytest -m "not integration and not e2e" -v
python -m pip check
podman compose --env-file .env -f infra/odoo/compose.yaml config
```

Run the backend with `uvicorn backend.app.main:app --reload` and the frontend
from `frontend/` with `reflex run`.

## Verification policy

- Unmarked tests are fast tests. Mark tests that require running services with
  `integration` and browser-level full-flow tests with `e2e`; unknown markers fail.
- Run the fast checks before handoff. Run `pytest -m "integration and not e2e" -v`
  only with the documented runtime services available.
- PuLP 3.3.0 and actual bundled CBC execution are required for T13 fast checks.
  Missing solver dependencies/executables must fail the runtime gate, never skip.
- T14 ML dependencies and actual training/artifact reload/inference are required
  for fast checks; missing dependencies must fail, never skip. Python 3.11 remains
  the compatibility baseline and the required CI runtime.
- GitHub Actions uses Docker Compose on Ubuntu; local Windows development continues
  to use Podman Compose.
- The `quality` job is the only check intended to be required for branch protection.
  The heavier container/API integration job remains path-filtered and optional.
- `reflex export --frontend-only --no-zip` verifies compilation only. Browser-level
  Reflex-to-FastAPI success and unavailable-backend behaviour remain local or
  milestone acceptance checks until a separate E2E suite exists.
- Synthetic volume markers prove technical named-volume persistence only. They do
  not prove persistence of an Odoo business scenario; verify that later through the
  implemented Odoo integration flow.
- Use synthetic CI credentials and never commit generated environment files. Do not
  claim a check passed unless it was actually executed.
- Permanent cloud deployment is outside the current increment.

## Code navigation

When a `.codegraph/` index exists, use a focused
`codegraph explore "<question or symbols>"` query before broad text searches or
reading multiple code files. Prefer the returned current source and dependency
paths to conserve context and tokens. Fall back to `rg` for exact text, non-code
files, or details CodeGraph does not return. Do not rebuild or replace the index
unless the user explicitly asks.
