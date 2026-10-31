# Runbook

Windows PowerShell at the repository root. Start only what the task needs.

| Task | Needs |
| --- | --- |
| Change code and run fast checks | Python 3.11 |
| Use the web UI with saved cases | + planning database, FastAPI, Reflex, trained model |
| Read live quotations | + Odoo (Podman) |
| Database integration tests | + disposable test database (Podman) |

## 1. One-time setup

Python 3.11 is the project baseline. With [uv](https://docs.astral.sh/uv/):

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -e ".[frontend,dev]"
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env   # only if .env does not exist; then fill the blanks
```

Podman: `podman machine start` once per boot. If `podman compose` needs a provider,
`tools.dev` uses the `podman-compose` installed in the venv automatically.

## 2. Fast quality gate (no services)

```powershell
python -m tools.dev check
```

Runs `ruff format --check`, `ruff check`, `compileall`, the fast test suite
(`not integration and not e2e`, with real CBC and scikit-learn) and a dependency
check. Run it before every handoff.

## 3. Supplier model

Since P2 every new case is created from an Odoo quotation group with the
Odoo-history model (§5.3); the synthetic demo model and its `prepare` command were
removed. Cases saved earlier with that model remain readable without it.

## 4. Planning database, API and UI

```powershell
python -m tools.dev db-up   # starts infra/app/compose.yaml and runs migrations
python -m tools.dev api     # terminal 2: FastAPI on http://127.0.0.1:8000 (docs at /docs)
python -m tools.dev ui      # terminal 3: Reflex on http://localhost:3000
```

`tools.dev ui` starts the development server. For a compiled local demonstration,
run `..\.venv\Scripts\reflex.exe run --env prod` from `frontend/`. Reflex
0.9.12 serves the production build on the configured backend port, normally
`http://localhost:8001/`; use the URL printed in its log. Production does not
hot-reload: restart it after frontend edits. Do not run two Reflex instances on
the same port.

Before `db-up`, set `APP_POSTGRES_PASSWORD` and the matching `DECISION_DATABASE_URL`,
plus `API_SERVICE_TOKEN` and `PLANNING_LIBRARY_COMPANY_ID` (the Odoo company, e.g.
`odoo:res.company:1`; it scopes the case library and the quotation-group list) in `.env`.
`db-up` also applies new migrations (P2 adds `20261019_01`: one PDF per language;
`20261021_01` adds the plan/audit document kind, ADR-036). The database
keeps its data in a named volume; `python -m tools.dev db-down` stops it.

After a schema change that squashes migrations (as on 2026-10-18), recreate the
volume: `podman compose -f infra/app/compose.yaml down -v`, then `db-up`.

## 5. Odoo

```powershell
python -m tools.dev odoo-up    # Odoo on http://127.0.0.1:8069 with its own database
python -m tools.dev odoo-down
```

`odoo-up` needs `POSTGRES_PASSWORD` and `ODOO_MASTER_PASSWORD` in `.env`.

### 5.1 Dedicated test database (manual, administrator)

1. `http://localhost:8069/web/database/manager` > **Create Database**: master password
   from `.env`, name `pdss_history_gen`, language English, country Hungary, no demo data.
2. **Apps**: activate **Inventory** and **Purchase**. **Purchase > Configuration >
   Settings**: enable **Purchase Agreements** (alternative RFQ groups).
3. **Settings > Activate the developer mode**; **Settings > Technical > System
   Parameters > New**: key `pdss.seed_target`, value `pdss_history_gen`.
4. **Apps > Update Apps List**, then activate `T7-S Inventory-History Projection`
   (19.0.2.0.0, history export) and `PDSS Quotation Reader`.
5. Quotation user (internal, no Purchase/Inventory role, only company 1): add it to the
   `PDSS Quotation Reader` group; API key from its **Preferences > Account Security** →
   `ODOO_API_KEY`.
6. History user (portal, only company 1): **Contacts > New > Action > Grant portal
   access**, add it to `T7-S Inventory-History Projection Reader`; temporarily enable
   **Settings > Permissions > Customers can generate API Keys**, create the key at
   `/my/security?debug=1`, disable the setting again → `ODOO_T7S_API_KEY`.
7. `ODOO_DATABASE=pdss_history_gen` and `ODOO_HISTORY_DATA_ORIGIN=generated` (the
   declared origin of its purchase history; the default).

Rollback: delete the database in the database manager. Earlier setups (T6/T7 fixtures)
are in [history/](history/).

### 5.2 Seed generated purchase history (dedicated test database only)

Create a short-lived administrator API key and set `ODOO_SEED_DATABASE=pdss_history_gen`
and `ODOO_SEED_ADMIN_API_KEY` in `.env`. The tool refuses any other database name and
any database without `pdss.seed_target`; the backend never reads these settings.

```powershell
python -m tools.seed_odoo_history plan     # summary only, no writes
python -m tools.seed_odoo_history apply    # ~2,550 orders, ~40 min; resumable
```

It creates 3 products, 40 suppliers (`[GEN]` names), 18 months of confirmed orders
with back-dated, partly late and partial receipts (origin `PDSS-GEN-P1:*`) and one
open quotation group (four tax-free RFQs, origin `PDSS-GEN-P1:RFQ:*`). The manifest
is written to `.artifacts/seed/manifest.json` (`purchase_group_id` is needed below).

### 5.3 Train the Odoo-history model

```powershell
python -m tools.train_history_model all   # read-only extraction, training, report
```

`--data-origin generated|observed` (default `generated`) declares what the database
holds; it is stored in the export, the dataset card and the model metadata. The
backend only uses a model whose origin equals `ODOO_HISTORY_DATA_ORIGIN`, and the
origin is frozen in every case's history capture.

Set `SUPPLIER_HISTORY_MODEL_DIRECTORY` to the absolute path of `.artifacts/ml/model`.
In the UI, **New procurement** (Hungarian: **Új beszerzés**) lists the company's open
groups (`GET /api/v2/procurement/quotation-groups`); choose one, then Demand → Supplier
terms → Review previews and saves a case from live Odoo history. Full HTTP flow:
`python -m tools.t17_demo run --odoo-history <group> --actor … --reason … --no-award-reason …`
(base case, nine scenarios in both directions, approval, No-award, HU PDF, stored replay).
Opt-in live check: `RUN_ODOO_HISTORY_LIVE=true pytest tests/integration/test_live_purchase_history.py -m integration`.

### 5.4 Reproducible demonstration and evaluation (P4)

Prerequisites: §5.1–5.3 done, `.env` complete (including `API_SERVICE_TOKEN` and, for
the evaluation, `TEST_DATABASE_URL` with the test database of §6 running). Port 8010
must be free: both tools start their own API there.

```powershell
python -m tools.dev demo                      # one command: Odoo + planning DB + demonstration
python -m tools.seed_odoo_history groups      # once: open groups with 5 and 10 suppliers
python -m tools.milp_evaluation               # ~15 min: latency + correctness report
python -m tools.train_history_model report    # re-evaluate the saved model, no training
```

- `demo` picks the four-supplier group (or `python -m tools.demo --group N`), runs case →
  plans → nine scenarios (both directions, two infeasible) → approval of the
  lower-exposure alternative and a separate No-award → HU and EN plan and audit PDF, then
  restarts the
  API with `ODOO_BASE_URL` pointing to a closed port and no model directory and replays
  every case, retry, PDF and supplier overview from storage. Summary:
  `docs/evidence/P4_DEMO_REPORT.json`; full responses, PDFs and the API log:
  `.artifacts/demo/`. Cases are stored in the development planning database.
- `groups` writes 15 open tax-free RFQs and two quotation groups (origins
  `PDSS-GEN-P1:RFQ5:*`, `PDSS-GEN-P1:RFQ10:*`) into `pdss_history_gen` only, with the
  same guards as `apply`; a rerun reuses them. Rollback: cancel and delete those RFQs in
  **Purchase > Orders > Requests for Quotation** (filter by Source Document).
- `milp_evaluation` writes its measured cases into the disposable test database, never
  the development library. Report: `docs/evidence/P4_MILP_EVALUATION.json`.
- `report` writes `docs/evidence/P4_ML_REPORT_CHECK.json` (offline; needs
  `.artifacts/ml/history_export.json` and `.artifacts/ml/model`).

## 6. Database integration tests

```powershell
$env:TEST_POSTGRES_PASSWORD = python -c "import secrets; print(secrets.token_urlsafe(32))"
podman compose -f infra/persistence/compose.test.yaml up -d --wait
$env:TEST_DATABASE_URL = "postgresql+psycopg://planning_test:$env:TEST_POSTGRES_PASSWORD@127.0.0.1:55432/planning_test"
python -m pytest -m "integration and not e2e" -v
podman compose -f infra/persistence/compose.test.yaml down
```

These tests drop and recreate the schema of the disposable test database only.
If the container is healthy but Windows refuses port 55432, see the SSH tunnel
workaround in [history/PERSISTENCE_DEVELOPMENT.md](history/PERSISTENCE_DEVELOPMENT.md).

## 7. Troubleshooting

- **CBC fails with a temp path error**: CBC cannot use a temp directory with spaces;
  `tools.dev check` sets a safe one. For manual runs set `$env:TEMP`/`$env:TMP`.
- **Saved case shows "planning data unavailable"**: check `/api/v1/health`, that the
  planning database container runs, and that FastAPI was restarted after `.env` edits.
- **Unicode errors in tooling**: set `$env:PYTHONUTF8 = "1"`.
