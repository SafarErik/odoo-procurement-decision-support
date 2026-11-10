# Odoo Procurement Decision Support

BSc thesis project (BME VIK, task 423.589/25/140): a Python decision-support service
that runs beside **Odoo 19** and answers *how much should we order from which
supplier* for one approved product demand.

The buyer picks an open Odoo quotation group. The service reads the quotations and the
product's purchase history from Odoo (read-only), takes the buyer's terms with their
source, scores each supplier with a **Decision Tree**, computes order allocations with a
**MILP** (minimum cost plus lower-risk alternatives), reruns the same MILP on **stress
scenarios**, and records one **human decision**: approve a plan or No-award. An approved
plan becomes a Hungarian or English **purchase-order proposal PDF**. Odoo stays the ERP:
the service never writes business data and never creates purchase orders.

## Architecture at a glance

```text
Reflex UI ──HTTP──► FastAPI ──► application (use cases, through ports)
(frontend)          (backend)     ├── odoo_adapter            Odoo 19, read-only JSON-2
                                  ├── supplier_evaluation     Decision Tree scores
                                  ├── decision_core           planning model and rules
                                  │   └── optimization_adapter  MILP (PuLP + CBC)
                                  ├── persistence             PostgreSQL, immutable cases
                                  └── document_adapter        approved PDFs (ReportLab)
```

Details, boundaries and the HTTP API: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start

Python 3.11 and [uv](https://docs.astral.sh/uv/). Install, then run the fast gate
(`python -m tools.dev check`, no services needed): [docs/RUNBOOK.md §1–2](docs/RUNBOOK.md#1-one-time-setup).
Running the database, API, UI and Odoo, seeding test history and training the model:
the rest of the [runbook](docs/RUNBOOK.md).

## Where to go next

| Package | Purpose |
| --- | --- |
| [decision_core/](decision_core/README.md) | ERP-neutral planning model and rules |
| [optimization_adapter/](optimization_adapter/README.md) | MILP solver (PuLP + CBC) |
| [supplier_evaluation/](supplier_evaluation/README.md) | Decision Tree dataset, training, inference |
| [application/](application/README.md) | Use cases: cases, scenarios, decisions, documents |
| [odoo_adapter/](odoo_adapter/README.md) | Read-only Odoo JSON-2 readers |
| [persistence/](persistence/README.md) | PostgreSQL repositories; schema in `migrations/` |
| [document_adapter/](document_adapter/README.md) | Approved plan and audit PDFs |
| [backend/](backend/README.md) | FastAPI app |
| [frontend/](frontend/README.md) | Reflex web UI |
| [infra/](infra/README.md) | Compose files and the two Odoo addons |
| [tools/](tools/README.md) | `tools.dev`, seeder, training, demo, evaluation |
| [tests/](tests/README.md) | Fast, integration and browser tests |

Documentation: [docs/README.md](docs/README.md) indexes everything (architecture, ML and
MILP models, runbook, testing, traceability, limitations, ADRs, evidence, handoffs,
history). Product and UI design intent: [PRODUCT.md](PRODUCT.md), [DESIGN.md](DESIGN.md);
domain terms: [GLOSSARY.md](GLOSSARY.md); rules for coding agents: [AGENTS.md](AGENTS.md).

The Hungarian thesis and the accepted requirements (FR-V2/NFR-V2/AC-V2), roadmap and
ADR register live on Google Drive; see [docs/agents/project-baseline.md](docs/agents/project-baseline.md).
The supplier model is trained on generated purchase history in a dedicated Odoo test
database, so no real-world predictive accuracy is claimed
([limitations](docs/LIMITATIONS_AND_FUTURE_WORK.md)).
