# Official task → implementation → evidence → thesis chapter

Official task 423.589/25/140 (2026-09-22). Requirement IDs (FR-V2/AC-V2) are
defined on Drive in 06_REQUIREMENTS_BASELINE. Status as of 2026-10-17 (P1); update this
table whenever a capability changes.

| # | Task sentence (abridged) | Implementation | Evidence | Status | Chapter |
| --- | --- | --- | --- | --- | --- |
| 1 | Open ERP systems; Odoo procurement, supplier evaluation, ERP data handling | — (literature) | Chapter 2 prose | Done | 2 |
| 2 | Odoo + Python side-by-side development; roles of FastAPI, PostgreSQL, Reflex | [ARCHITECTURE.md](ARCHITECTURE.md) | `test_architecture.py` | Done | 2, 4, 6 |
| 3 | Decision-support algorithms, especially decision trees and MILP | — (literature) | Chapter 2 prose | Done | 2 |
| 4 | System in Odoo using historical purchasing data under control; supplemental business data with provenance | history addon export, `odoo_adapter/product_history_reader.py`, `application/planning_history.py`, `tools/seed_odoo_history.py` | `test_odoo_purchase_history.py`, `tests/integration/test_live_purchase_history.py`, [P1 handoff](handoffs/P1_ODOO_HISTORY_ML.md) | Done: 2,546 generated Odoo purchase lines read only through Odoo; data is generated, not observed | 3, 4, 6 |
| 5 | Supplier evaluation in Python from performance characteristics with decision trees | `supplier_evaluation/purchase_history.py`, `history_model.py` | `test_odoo_purchase_history.py`, [P1_ML_REPORT.json](evidence/P1_ML_REPORT.json) | Done: 7 as-of features, next-60-day label, trained from Odoo history | 5, 6, 7 |
| 6 | Document the training dataset; interpret decision paths | [MODEL_ML.md](MODEL_ML.md) dataset card, readable path in UI and `path_text` | `test_odoo_purchase_history.py` | Done; Hungarian wording in P3 | 5, 7 |
| 7 | MILP: capacity, MOQ, supplier count, concentration, delivery limits; min cost and risk exposure; several suppliers | `decision_core/planning/`, `optimization_adapter/` — [MODEL_MILP.md](MODEL_MILP.md) | `test_t13_planning.py` | Done | 5, 6, 7 |
| 8 | Web UI in Python showing evaluations, allocations, justifications | `frontend/` (Reflex) | frontend + e2e tests | Works; **UX revamp** → P3 | 4, 6 |
| 9 | Store plans systematically; technical approvability; finalize fixed orders as PDF | `persistence/`, `application/planning_decisions.py`, `document_adapter/` | `test_t17_decisions.py`, `test_t21_documents.py`, Postgres tests | Works; **PDF content/language** → P2 | 4, 6, 7 |
| 10 | Stress test: supplier outage, capacity, demand, price change, same MILP | `application/planning_cases.py` scenarios | `test_t16_scenarios.py` | Works one-directional → both directions in P2 | 5, 6, 7 |
| 11 | Reproducible tests: models, integration, infeasible cases, full process, ML evaluation conventions | `tests/`, `tools/` | [TESTING.md](TESTING.md), [MODEL_ML.md](MODEL_ML.md) §5–7 | ML: supplier+time split, train-only depth CV, majority/expert/stump baselines, confusion matrix, F1, support, AUC; tree beats majority, not the expert rule | 7 |
| 12 | Propose further development | measured limitations | — | Open (P4) | 9 |
