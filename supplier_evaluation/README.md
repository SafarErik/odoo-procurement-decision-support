# supplier_evaluation

Decision Tree supplier evaluation on purchase history read from Odoo. Training is
offline (a CLI in `tools/`); the backend only loads a trusted model directory and
scores suppliers. Callers never choose or upload a model.

## Entry points

- [purchase_history.py](purchase_history.py) — as-of supplier features, next-window
  labels and the leakage-safe dataset (supplier and time split).
- [history_model.py](history_model.py) — depth selection, baselines, artifact writing and
  trusted loading, inference with the readable tree path.
- [contracts.py](contracts.py) — dependency-free assessment contracts, the history
  vocabulary (`HISTORY_GENERATED` / `HISTORY_OBSERVED`) and shared validators.

Dataset card, features, label and evaluation: [docs/MODEL_ML.md](../docs/MODEL_ML.md).
Training command: [docs/RUNBOOK.md](../docs/RUNBOOK.md#53-train-the-odoo-history-model).
The ML → MILP risk bridge lives in `application/procurement_planning.py`.

## Imports

- May import: scikit-learn, NumPy, SciPy, joblib.
- Must not import: `application` (no cycle), `decision_core`, `optimization_adapter`,
  `backend`, `odoo_adapter`, `persistence`, `tools`, PuLP, httpx, Reflex.
  Enforced by [tests/test_architecture.py](../tests/test_architecture.py).

## Tests

`tests/test_odoo_purchase_history.py`, `tests/test_risk_bridge.py`,
`tests/test_supplier_overview.py`; see [docs/TESTING.md](../docs/TESTING.md).
