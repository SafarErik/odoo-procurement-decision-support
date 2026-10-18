# Odoo Procurement Decision Support

BSc thesis project (BME VIK, task 423.589/25/140): a Python decision-support service
that runs beside **Odoo 19** and answers *how much should we order from which
supplier* for one approved product demand.

```text
Odoo quotations + supplier history (read-only)   +   buyer terms with source
        -> supplier evaluation (Decision Tree)
        -> order allocation (MILP: minimum cost and lower-risk alternatives)
        -> what-if stress scenarios (same MILP, changed inputs)
        -> human approval or No-award
        -> approved purchase-order proposal PDF
```

Odoo stays the ERP: the service reads it through the official API, never writes
business data and never creates purchase orders.

## Quick start

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -e ".[frontend,dev]"
.venv\Scripts\Activate.ps1
python -m tools.dev check        # lint + fast tests, no services needed
```

Running the UI, database and Odoo: [docs/RUNBOOK.md](docs/RUNBOOK.md).

## Repository layout

| Path | Content |
| --- | --- |
| `decision_core/planning/` | ERP-neutral planning model, bounds, verification, explanations |
| `optimization_adapter/` | PuLP + CBC MILP solver adapter |
| `supplier_evaluation/` | Dataset, Decision Tree training/evaluation, inference, ML → MILP bridge |
| `application/` | Use cases: input assembly, cases, scenarios, decisions, library, documents |
| `odoo_adapter/` | Read-only Odoo JSON-2 readers |
| `persistence/`, `migrations/` | PostgreSQL repositories and Alembic schema |
| `document_adapter/` | Approved PDF renderer |
| `backend/` | FastAPI app |
| `frontend/` | Reflex web UI |
| `infra/` | Compose files (Odoo, planning DB, test DB) and the Odoo history addon |
| `tools/` | `tools.dev` entry point, Odoo test-data seeder, offline training, one-command demo, MILP/API evaluation |
| `tests/` | Fast, integration and browser tests |

## Documentation

| Document | Use |
| --- | --- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, flow, boundaries, API, persistence |
| [MODEL_ML.md](docs/MODEL_ML.md) | Supplier model: Odoo-history dataset card, features, label, evaluation |
| [MODEL_MILP.md](docs/MODEL_MILP.md) | Allocation model and its limitations |
| [RUNBOOK.md](docs/RUNBOOK.md) | Setup and running services |
| [TESTING.md](docs/TESTING.md) | Test levels and coverage map |
| [TRACEABILITY.md](docs/TRACEABILITY.md) | Official task → implementation → evidence → chapter |
| [LIMITATIONS_AND_FUTURE_WORK.md](docs/LIMITATIONS_AND_FUTURE_WORK.md) | Measured limitations with evidence and further-development proposals |
| [REVAMP_PLAN.md](docs/REVAMP_PLAN.md) | Current improvement plan |
| [handoffs/](docs/handoffs/) | What each increment changed and how it was verified |
| [history/](docs/history/) | Earlier designs, handoffs and evidence (T0–T18, UX32–UX41) |

The Hungarian thesis documents and accepted requirements live on Google Drive
(see [docs/agents/project-baseline.md](docs/agents/project-baseline.md)).

## Status (2026-10-18)

All five required capabilities work end to end in a controlled local setup:
Decision Tree supplier evaluation, MILP allocation with alternatives, Reflex UI,
stress scenarios, and human approval with PDF. The revamp (see the plan) cleaned the
repository (P0), retrained the model from Odoo-sourced history (P1), extended
scenarios/PDF/API (P2: open quotation-group selection, two-way stress changes, supplier
overview, Hungarian/English purchase order proposal PDF), rebuilt the UI (P3: Hungarian
default with an English switch, case tabs, charts) and closed validation (P4, implemented):
`python -m tools.dev demo` reproduces the whole flow on live Odoo and replays it without
Odoo and model; the MILP/API evaluation (4/5/10 suppliers) matches an exhaustive reference
optimum in every check; measured limitations and proposals are in
[docs/LIMITATIONS_AND_FUTURE_WORK.md](docs/LIMITATIONS_AND_FUTURE_WORK.md) and evidence in
[docs/evidence/](docs/evidence/). The supplier model is trained from purchase history read
from Odoo; in the test database that history is generated, so no real-world predictive
accuracy is claimed.
