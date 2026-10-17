# Architecture

A Python service that runs **beside Odoo 19** (side-by-side), reads procurement
facts through Odoo's external API, and helps a buyer decide **how much to order
from which supplier** for one approved product demand. Odoo stays the ERP; this
service never writes to it and never touches its database directly.

## 1. End-to-end flow

```text
Odoo 19 (read-only JSON-2)            buyer-supplied terms (with source)
  quotations, suppliers, prices          demand Q, capacity, MOQ, dates, policy
  receipt history (bounded addon)               |
            \                                   /
             v                                 v
        input assembly + field-level provenance   (application/)
                         |
                         v
        supplier evaluation: saved Decision Tree  (supplier_evaluation/)
          class, exposure score in [0,1], tree path
                         |
                         v
        MILP planning: minimum cost + epsilon alternatives (decision_core/planning,
                         |                                  optimization_adapter/)
                         v
        immutable snapshot in PostgreSQL           (persistence/)
                         |
            +------------+-------------+
            v                          v
   stress scenarios (same MILP,    human decision: approve one plan
   explicit input changes,         or No-award, recorded once
   stored as child cases)                     |
                                              v
                                   approved PDF from the stored snapshot
                                              (document_adapter/)
```

The Reflex web UI drives every step through the HTTP API only.

## 2. Components

| Package | Responsibility | Depends on |
| --- | --- | --- |
| `decision_core/planning/` | ERP-neutral planning model: immutable request/plan types, bound rules, plan verification, explanations, the `plan_procurement` use of a solver port | standard library only |
| `optimization_adapter/` | PuLP + CBC implementation of the solver port (integer encoding, exact rational scaling, tie-break) | `decision_core`, PuLP |
| `supplier_evaluation/` | Offline dataset building, Decision Tree training/evaluation, trusted artifact loading, inference with tree path, ML → MILP risk bridge | scikit-learn, `decision_core` |
| `application/` | Use cases: assemble inputs and provenance, create cases and scenarios, finalize decisions, list saved cases, prepare approved document content | ports only (no Odoo/DB/HTTP) |
| `odoo_adapter/` | JSON-2 readers for RFQs, comparison groups and bounded receipt history | `application` contracts, httpx |
| `persistence/` | SQLAlchemy repositories and unit of work for cases, decisions and PDFs | `application` contracts |
| `document_adapter/` | ReportLab rendering of the approved PDF | approved content only |
| `backend/app/` | FastAPI composition root, strict request schemas, thin routes, service-token gate | all of the above |
| `frontend/` | Reflex UI; talks to the backend over HTTP; holds the service token server-side | backend API only |
| `infra/odoo/addons/t7s_inventory_history_projection/` | Minimal Odoo addon exposing one bounded, company-scoped, read-only receipt-history method | Odoo |
| `migrations/` | Alembic schema for the planning database | `persistence.schema` |
| `tools/` | Developer entry point (`tools.dev`), reproducible demos and the evaluation harness | everything |

Boundaries enforced by `tests/test_architecture.py`: the planning core imports no
application/adapter code and carries no provenance; the application layer imports
no Odoo, SQL or HTTP code; adapters point inward.

## 3. Key design decisions

- **Hybrid input with provenance.** Odoo proves identities, prices and history; it
  does not prove approved demand, capacity, hard MOQ or promised dates. Those come
  from explicit buyer input, each with `source_type`, `source_reference`,
  `observed_at`. Missing critical data fails closed.
- **ML evaluates, MILP allocates.** The tree turns supplier history into a risk
  coefficient; it never decides quantities. Hard constraints always win over a
  good score or price.
- **Immutable snapshots.** Every base case and every scenario is one immutable
  row (database triggers reject UPDATE/DELETE). Re-reading a case never re-reads
  Odoo, re-scores or re-solves.
- **Idempotent writes.** Every POST carries an `Idempotency-Key`; an exact retry
  returns the stored result, a different payload under the same key is a conflict.
- **One human decision per base case.** Approve a stored plan or record No-award;
  scenarios cannot be approved. The PDF is rendered from the approved snapshot only.
- **Offline training.** Models are trained by a CLI and loaded from a trusted local
  directory; HTTP callers can never select or upload a model.

## 4. HTTP API

Prefix `/api/v2/procurement/planning-cases`, bearer service token required.

| Method and path | Purpose |
| --- | --- |
| `POST /` | Create a base case from explicit (demo) input |
| `POST /from-odoo` | Create a base case from an Odoo quotation group plus explicit terms |
| `GET /odoo-history/local-v1`, `POST /from-odoo-history` | Fixed Odoo test-copy path using Odoo receipt history |
| `POST /{id}/scenarios` | Re-run the same MILP on explicitly changed inputs (child case) |
| `GET /`, `GET /{id}/scenarios` | Saved-case library, filters `origin`, `status`, `q`, cursor paging |
| `GET /{id}` | Stored case, its decision and data origin |
| `POST /{id}/final-decision` | Approve a plan or record No-award (once) |
| `GET /{id}/approved-pdf/{hash}` | Approved PDF bytes |

`GET /api/v1/procurement/rfqs` lists open Odoo RFQs; `GET /api/v1/health` is a
liveness probe.

## 5. Persistence

One PostgreSQL database owned by this service (`migrations/versions/20261018_01`):

| Table | Content |
| --- | --- |
| `planning_cases` | Snapshot JSONB (facts, request, assessments, model manifest, solver evidence, result, scenario delta, provenance), parent link, idempotency key and fingerprint |
| `planning_final_decisions` | One immutable decision per original base case |
| `planning_documents` | Approved PDF bytes, content hash and renderer version |

The data origin shown in the UI (`demo` or `odoo`) is derived from the stored
snapshot, not stored separately.

## 6. Runtime

Local only (no cloud deployment): Odoo and its database in one Compose project,
the planning database in another, a disposable test database in a third. FastAPI
and Reflex run as Python processes. See [RUNBOOK.md](RUNBOOK.md).
