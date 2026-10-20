# Supplier evaluation model (Decision Tree on Odoo purchase history)

Status 2026-10-17 (P1); wording and data-origin handling revised 2026-10-19
([REVIEW_FIXES](handoffs/REVIEW_FIXES.md)). Code: `supplier_evaluation/purchase_history.py` (features,
label, split), `supplier_evaluation/history_model.py` (training, evaluation, artifact,
inference), `tools/train_history_model.py` (offline pipeline). Evidence:
[evidence/P1_ML_REPORT.json](evidence/P1_ML_REPORT.json).

> **Honest framing.** The pipeline is Odoo-native: every training row is derived from
> purchase lines and receipts read through Odoo's API. The history in the test
> database `pdss_history_gen` is **generated** by `tools/seed_odoo_history.py` with a
> simulated clock. The metrics below therefore show that the method works and is
> evaluated correctly; they do not measure real supplier behaviour.

## 1. Purpose and role

The tree turns a supplier's recent delivery history into a **risk score in [0, 1]**:
the share of problematic training cases in the leaf the supplier falls into. The
MILP uses that score as the supplier's risk coefficient for the lower-risk
alternatives. The tree never decides quantities; hard constraints always win.

## 2. Data source and dataset card

| Item | Value |
| --- | --- |
| Source | `procurement.product.history.export.read_product_history` (Odoo addon, JSON-2, read-only, restricted portal user) |
| Database / origin | `pdss_history_gen`; generated history (seed 20261017, simulated clock ending 2026-10-17). The origin is declared on extraction (`--data-origin generated\|observed`, default `generated`) and travels export → dataset card → model metadata `data_origin` |
| Export | 2,546 confirmed purchase lines, 2,823 receipts, 40 suppliers, 3 products, Expected Arrival 2025-04-17 … 2026-10-17 |
| Unit of observation | supplier × product × cutoff (1st and 16th of each month); one row aggregates many purchase lines, and windows of neighbouring cutoffs overlap |
| Rows | 2,546 purchase lines → 1,804 supplier–product–cutoff rows (all contexts and cutoffs where both features and label are supported); 682 train rows, 140 primary test rows from 10 held-out suppliers |
| Class balance | 1,389 regular / 415 problematic (23%) |
| Extraction | 2026-10-17 18:25 UTC; export hash and row ids in the report |

The export returns, per confirmed line (`purchase`/`done` order) of one company and
product with Expected Arrival in a ≤366-day window (≤500 lines): ordered quantity,
Expected Arrival, order confirmation time, every completed receipt (time, quantity,
backorder link) and returned quantity. It computes nothing; features are derived
outside Odoo.

Generator behaviours (ground truth, never a training input): reliable, steady late,
deteriorating, improving, partial shipper, volatile, temporary shock; each with a
slowly drifting latent on-time probability, lateness size, partial-shipment and
short-close probability ([seed tool](../tools/seed_odoo_history.py)).

## 3. Features (as of cutoff `c`)

Lines with Expected Arrival in `[c−134d, c−14d)` that were confirmed before `c`;
only receipts processed before `c` are used. At least 3 such lines are required,
otherwise the supplier gets **no score** (fail closed, no fallback).

| Feature | Definition |
| --- | --- |
| `on_time_rate` | share of lines whose first receipt arrived by Expected Arrival + 1 day |
| `mean_lateness_days` | mean of (first receipt − Expected Arrival) in days; no receipt yet ⇒ `c − Expected Arrival` |
| `lateness_spread_days` | population standard deviation of the same delays |
| `fill_rate` | received quantity / ordered quantity (receipt quantity capped per line) |
| `partial_share` | share of lines received in several receipts or not in full |
| `order_count` | number of settled lines in the window |
| `days_since_last_receipt` | days since the last receipt of lines due in the last 180 days (cap 180) |

The 14-day gap `[c−14d, c)` lets recent lines settle and is excluded from the six
window features. `days_since_last_receipt` is the exception: its 180-day window
`[c−180d, c)` includes the gap, so a receipt processed in the last 14 days before `c`
shortens it. This is not leakage — only lines confirmed before `c` and receipts
processed before `c` are used, and the label window starts at `c` — but the gap is not
unused.

## 4. Label (next window)

Lines due in `[c, c+60d)` (at least 2). A line's delay is first receipt − Expected
Arrival in days, early = 0, nothing within 14 days = 14. **Problematic** if the mean
delay exceeds **3 days** or the fill rate (quantity received within 14 days of
Expected Arrival) is below **85%**. The label is observable from `c + 74d`.

Label history: the first version (late share ≥ 1/3, fill < 90%) was dominated by
single lines — with 3–4 due lines one late delivery flipped it, so 18% of the
generator's *reliable* supplier windows were "problematic" and the label was
mostly noise. It was replaced after the first run, before the larger dataset
existed; both runs are kept as evidence (§7).

## 5. Split, model selection and training

- **Held-out suppliers**: 25% of suppliers (10 of 40) chosen by a seeded hash of the
  supplier id, independent of outcomes.
- **Time boundary** `B` = the last cutoff ≥ 92 days before the last labelled cutoff
  (here 2026-05-01). Train: other suppliers, label observable by `B` (682 rows).
  Primary test: held-out suppliers, cutoff ≥ `B` (140 rows). Supplementary test: all
  suppliers, cutoff ≥ `B` (574 rows) — known suppliers, later time.
- **Depth** chosen from 1–5 by mean macro F1 over 4 expanding-window time-series
  folds **on the training rows only** (each fold fits only rows whose labels were
  observable before the validation block). Scores: d1 0.485, d2 0.542, d3 0.533,
  d4 0.546, d5 0.546 → depth 4 (smallest best). A class-weighting variant was checked
  on the same train-only folds and not better, so it was not adopted.
- Fixed: Gini, `min_samples_leaf=10`, `min_samples_split=20`, `random_state=17`,
  no class weights. Trained through 2026-05-01; 13 leaves.

## 6. Results (held-out)

Primary test — 10 unseen suppliers, later period (97 regular / 43 problematic):

| Model | Macro F1 | Accuracy | Problematic recall | Score ROC AUC |
| --- | --- | --- | --- | --- |
| **Decision tree (depth 4)** | **0.589** | 0.686 | 0.33 | 0.699 |
| Majority class (always regular) | 0.409 | 0.693 | 0.00 | — |
| Learned single split | 0.594 | 0.693 | 0.33 | — |
| Expert rule: on-time rate < 80% | 0.658 | 0.671 | 0.77 | 0.749 (1 − on-time rate) |

Tree confusion matrix (rows = true 0/1, columns = predicted 0/1): `[[82, 15], [29, 14]]`;
class 0 precision 0.74 / recall 0.85 / F1 0.79, class 1 precision 0.48 / recall 0.33 /
F1 0.39.

Supplementary test — all suppliers, later period (426 / 148): tree macro F1 0.554,
single split 0.587, expert rule 0.564, majority 0.426; score AUC tree 0.659 vs
1 − on-time rate 0.652.

**Measured.** On the primary test (140 rows, 10 unseen suppliers; rows are correlated
because cutoff windows overlap):

- Macro F1 (the selection metric): tree 0.589 > majority 0.409, but < expert rule 0.658
  and ≈ learned single split 0.594.
- Accuracy does not separate the models: 0.671–0.693 for all four, the majority class is
  highest (0.693) because 69% of rows are regular.
- Problematic recall: tree 0.33, single split 0.33, expert rule 0.77.
- Score ROC AUC: tree 0.699, 1 − on-time rate 0.749.
- Supplementary test (known suppliers, later period): tree macro F1 0.554 vs expert rule
  0.564; score AUC tree 0.659 vs 0.652.
- Problematic share: 18% in the training period, 31% in the test period.

So "better" depends on the metric: by macro F1 and problematic recall the expert rule is
better on unseen suppliers; by accuracy no model is meaningfully better than predicting
"regular"; by ranking (AUC) tree and rule are close on known suppliers.

**Possible explanations (not tested separately).** (1) The generator's latent variable is
an on-time probability, so the on-time rate may be close to a sufficient statistic, and
the 80% threshold is close to the generator's parameters. (2) The class-share shift
between periods (deteriorating suppliers degrade later) is a drift the tree, fitted on
the earlier period, may under-predict. No ablation separates the two. The thesis should
present the measurement as a result and these as hypotheses.

Global importances: lateness spread 0.63, partial share 0.21, mean lateness 0.14,
recency 0.02; on-time rate, fill rate and order count unused.

## 7. Run log

| Run | Data | Label | Test rows | Tree macro F1 | Expert rule | Majority |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 16 suppliers, 1,019 lines | late share ≥ 1/3 or fill < 90% | 56 | 0.468 | 0.854 | 0.333 |
| 2 | 16 suppliers, 1,019 lines | mean delay > 3 d or fill < 85% | 56 | 0.525 | 0.738 | 0.411 |
| 3 (current) | 40 suppliers, 2,546 lines | same as run 2 | 140 | 0.589 | 0.658 | 0.409 |

Run 3 added 24 suppliers because the train-only folds of 16 suppliers had 25–125
rows; the first 16 suppliers' records were unchanged. Runs 1–2 used an earlier
recency definition (all prior receipts, cap 400 days). Reports:
[run 1](evidence/P1_ML_REPORT_run1_share_label.json),
[run 2](evidence/P1_ML_REPORT_run2_16_suppliers.json),
[run 3](evidence/P1_ML_REPORT.json).

## 8. Inference and explanation

At case creation the backend reads the quotation group, then the product's last 180
days of history through the restricted export, freezes the raw lines in the case
snapshot and derives each quoted supplier's features at the read time. The trusted
local model (`SUPPLIER_HISTORY_MODEL_DIRECTORY`) is used only if it was trained on
the same Odoo database and company, before the cutoff, and on history of the same
declared origin: model `data_origin` must equal `ODOO_HISTORY_DATA_ORIGIN`, which is
also frozen in the capture. A stored case is rejected if its model origin differs from
its capture's origin; captures saved before the origin was recorded read as
`generated`. The stored case keeps the
raw lines, features, assessments and model manifest; reopening re-derives and
checks the features from the stored lines but never reads Odoo or re-scores.

Each assessment carries its tree path. The UI and `history_model.path_text` render it
as sentences, e.g. *"Lateness spread (5.0 days) is above 4.5 days. Share of partial
deliveries (14.3%) is above 6.2%. … Result: Problematic."*

## 9. Reproduce

```powershell
python -m tools.seed_odoo_history plan            # inspect the generated plan, no writes
python -m tools.seed_odoo_history apply           # dedicated test DB only (see RUNBOOK)
python -m tools.train_history_model all           # extract (read-only) + train + report
```

Output: `.artifacts/ml/{history_export,dataset,report}.json` and `.artifacts/ml/model/`.

## 10. Limitations

- Generated data; no claim about real suppliers or real predictive accuracy.
- Back-dated timestamps: Odoo's own `create_date`/`write_date` show the seeding day,
  only the business dates are simulated.
- Expected Arrival is read as currently stored, not as originally promised; a later
  change of the date in Odoo would rewrite history.
- Supplier returns are exported but not yet used in features.
- Small held-out set (10 suppliers); semi-monthly cutoffs overlap, so rows are
  correlated and the metrics have wide uncertainty.
- Scores are leaf frequencies, not calibrated probabilities.
- P2 removed the demo creation path (`POST /`, `POST /from-odoo`) and with it the
  runtime use of the earlier synthetic two-feature tree
  ([history/T14_ML_DESIGN.md](history/T14_ML_DESIGN.md)); cases it created stay
  readable, and its offline code remains only to rebuild such cases in tests.
