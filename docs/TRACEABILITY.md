# Official task → implementation → evidence → thesis chapter

Official task 423.589/25/140 (2026-09-22). Requirement IDs (FR-V2/AC-V2) are
defined on Drive in 06_REQUIREMENTS_BASELINE. Status as of 2026-10-18; update this
table whenever a capability changes.

| # | Task sentence (abridged) | Implementation | Evidence | Status | Chapter |
| --- | --- | --- | --- | --- | --- |
| 1 | Open ERP systems; Odoo procurement, supplier evaluation, ERP data handling | — (literature) | Chapter 2 prose | Done | 2 |
| 2 | Odoo + Python side-by-side development; roles of FastAPI, PostgreSQL, Reflex | [ARCHITECTURE.md](ARCHITECTURE.md) | `test_architecture.py` | Done | 2, 4, 6 |
| 3 | Decision-support algorithms, especially decision trees and MILP | — (literature) | Chapter 2 prose | Done | 2 |
| 4 | System in Odoo using historical purchasing data under control; supplemental business data with provenance | `odoo_adapter/`, `application/planning_input.py`, `odoo_planning_input.py`, history addon | Odoo adapter and history tests | Provenance done; **history weak** (9 admin lines) → P1 | 3, 4, 6 |
| 5 | Supplier evaluation in Python from performance characteristics with decision trees | `supplier_evaluation/` | `test_t14_*` | Works; **2 features, circular synthetic label** → P1 | 5, 6, 7 |
| 6 | Document the training dataset; interpret decision paths | dataset manifest, tree path in Audit | `test_t14_dataset.py` | Partial → dataset card + readable path in P1/P3 | 5, 7 |
| 7 | MILP: capacity, MOQ, supplier count, concentration, delivery limits; min cost and risk exposure; several suppliers | `decision_core/planning/`, `optimization_adapter/` — [MODEL_MILP.md](MODEL_MILP.md) | `test_t13_planning.py` | Done | 5, 6, 7 |
| 8 | Web UI in Python showing evaluations, allocations, justifications | `frontend/` (Reflex) | frontend + e2e tests | Works; **UX revamp** → P3 | 4, 6 |
| 9 | Store plans systematically; technical approvability; finalize fixed orders as PDF | `persistence/`, `application/planning_decisions.py`, `document_adapter/` | `test_t17_decisions.py`, `test_t21_documents.py`, Postgres tests | Works; **PDF content/language** → P2 | 4, 6, 7 |
| 10 | Stress test: supplier outage, capacity, demand, price change, same MILP | `application/planning_cases.py` scenarios | `test_t16_scenarios.py` | Works one-directional → both directions in P2 | 5, 6, 7 |
| 11 | Reproducible tests: models, integration, infeasible cases, full process, ML evaluation conventions | `tests/`, `tools/` | [TESTING.md](TESTING.md) | Works; baseline comparison for ML in P1 | 7 |
| 12 | Propose further development | measured limitations | — | Open (P4) | 9 |
