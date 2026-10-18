# Measured limitations and further development

Input for thesis chapter 9 (further development) and the limitation paragraphs of
chapters 5 and 7. Status 2026-10-18 (P4). Each item states what was **measured or
observed**, links the evidence, and proposes a concrete next step. Proposals are not
part of the accepted scope and are not implemented.

| # | Limitation | Evidence | Chapter |
| --- | --- | --- | --- |
| L1 | Generated purchase history | [P1 handoff](handoffs/P1_ODOO_HISTORY_ML.md), [MODEL_ML.md](MODEL_ML.md) §2 | 3, 7, 9 |
| L2 | Tree below a hand-written rule on unseen suppliers | [P1_ML_REPORT.json](evidence/P1_ML_REPORT.json), [P4_ML_REPORT_CHECK.json](evidence/P4_ML_REPORT_CHECK.json) | 5, 7, 9 |
| L3 | Drift between training and test period | [MODEL_ML.md](MODEL_ML.md) §6 | 5, 7, 9 |
| L4 | Uncalibrated scores | [P4_DEMO_REPORT.json](evidence/P4_DEMO_REPORT.json) `supplier_assessment` | 5, 9 |
| L5 | Linear exposure does not reward diversification | [P4_DEMO_REPORT.json](evidence/P4_DEMO_REPORT.json) `base_case`, [MODEL_MILP.md](MODEL_MILP.md) §7 | 5, 9 |
| L6 | Buyer terms are defaults, not Odoo facts | `preview_odoo_history` in `backend/app/dependencies.py`, [P4_MILP_EVALUATION.json](evidence/P4_MILP_EVALUATION.json) `protocol` | 3, 5, 9 |
| L7 | One product, one period | [MODEL_MILP.md](MODEL_MILP.md) §7, [REVAMP_PLAN.md](REVAMP_PLAN.md) §4 | 5, 9 |
| L8 | Scenarios keep the saved scores | [MODEL_MILP.md](MODEL_MILP.md) §6 | 5, 9 |
| L9 | Proof-of-concept identity and trust | [P4_DEMO_REPORT.json](evidence/P4_DEMO_REPORT.json) `decisions`, [ARCHITECTURE.md](ARCHITECTURE.md) | 4, 9 |
| L10 | Local, single-machine performance only | [P4_MILP_EVALUATION.json](evidence/P4_MILP_EVALUATION.json) | 7, 9 |
| L11 | PDF is a proposal, not an Odoo purchase order | [P2 handoff](handoffs/P2_BACKEND_CAPABILITIES.md) | 6, 9 |
| L12 | Usability not assessed with real buyers | [P3 handoff](handoffs/P3_FRONTEND_REVAMP.md) | 7, 9 |
| L13 | Smaller data and contract gaps | handoffs P1–P3 | 7, 9 |

## L1 Generated purchase history

**Observed.** All 2,546 purchase lines (40 suppliers, 18 months) in `pdss_history_gen`
were written by `tools/seed_odoo_history.py` from seven latent behaviour profiles. The
pipeline is Odoo-native (official API, restricted history export, no database access),
but the values are not observations. Odoo's technical create/write dates show the
seeding day; only business dates are back-dated.

**Consequence.** Metrics validate the method, not real supplier performance.

**Proposal.** Run the unchanged extraction and training (`python -m tools.train_history_model
all`) on an anonymised copy of a real company's Odoo purchase history (≥ 12 months,
≥ 30 suppliers), report the same held-out metrics, and add a data-quality report
(missing Expected Arrival, manual receipt corrections, returns).

## L2 Tree below a hand-written rule on unseen suppliers

**Measured.** Primary test (10 unseen suppliers, later period, 140 rows): tree macro F1
**0.589**, majority 0.409, learned single split 0.594, expert rule "on-time rate < 80 %"
**0.658**; problematic recall tree 0.33 vs. rule 0.77. P4 re-evaluated the saved model on
the stored export without retraining: artifact hash, export hash, train split and every
metric are identical to the P1 report (`unchanged: true`).

**Why.** The generator's latent variable is an on-time probability, so the on-time rate
is nearly sufficient and the 80 % threshold matches the generator.

**Proposal.** (a) Keep the expert rule as a mandatory baseline and show it next to the
tree in the UI; (b) add class weights or threshold tuning for problematic recall, chosen
by train-only time-series CV; (c) compare a gradient-boosted tree or logistic regression
under the same split — only adopt one if it beats the rule on unseen suppliers.

## L3 Drift between training and test period

**Measured.** Problematic windows: 18 % in the training period vs. 31 % in the test period
(deteriorating suppliers degrade later). The tree, fitted on the earlier period,
under-predicts the problematic class.

**Proposal.** Rolling retraining with a monitored label rate per month, a drift alarm when
the recent problematic share leaves the training range, and a model validity date that is
already stored per assessment (`valid_until`) enforced in the UI.

## L4 Uncalibrated scores

**Observed.** The risk coefficient is the leaf's problematic frequency: in the demonstration
"[GEN] Fenyves Trade" sits in a leaf with 13 of 13 problematic cases, score **1**; two
other suppliers share the same leaf frequency 5/15 = **0.3333**. Leaf sizes are small and
the score is coarse (few distinct values).

**Proposal.** Calibrate on held-out data (Platt or isotonic), report Brier score and a
reliability curve, and smooth small leaves (e.g. Laplace/Bayesian prior on the leaf
frequency) before the score enters the MILP.

## L5 Linear exposure does not reward diversification

**Measured (demonstration, 200 units, K = 2, concentration 0.8).** Minimum-cost plan:
80 units from a supplier with score 1 and 120 from one with 0.3333 → exposure
(80·1 + 120·0.3333)/200 = **0.60**, cost 288,608 HUF. Lower-exposure alternative at
ε = 0.2: 120 + 80 units from two suppliers both scored 0.3333 → exposure **0.3333**,
cost 293,132 HUF (+1.6 %). Splitting between two equally scored suppliers gives exactly
the exposure of buying everything from one of them: Σrᵢxᵢ/Q is a weighted average.
Diversification comes only from the concentration limit and K.

**Proposal.** Add a concave or scenario-based risk term while staying a MILP: e.g.
expected shortfall over joint-failure scenarios with binary indicators, or a piecewise
linear penalty on each supplier's share; compare plans on simulated delivery outcomes.

## L6 Buyer terms are defaults, not Odoo facts

**Observed.** Odoo quotations carry price, quantity and dates but no supplier capacity or
MOQ. The preview proposes source-attributed defaults (`buyer_default_terms`): capacity
⌈0.6·Q⌉ per supplier, no MOQ, K = 2, concentration 0.8, ε = 0.2. The demonstration and
the evaluation use these defaults; the buyer can change them before saving.

**Proposal.** Read capacity and MOQ from Odoo where they exist (vendor pricelist
`product.supplierinfo` minimum quantity; a custom capacity field in the history addon)
and keep the defaults only as an explicit fallback with their own source type.

## L7 One product, one period

**Observed.** The core validates one product, unit and currency per request
(`decision_core/planning/models.py`); no transport cost, inventory or multi-period
dimension.

**Proposal.** Product-indexed variables `x[i,p]` with shared `y[i]`, per-product demand and
shared supplier limits (estimated 1–1.5 weeks, [REVAMP_PLAN.md](REVAMP_PLAN.md) §4); later
a multi-period lot-sizing extension with lead times.

## L8 Scenarios keep the saved scores

**Observed.** A stress scenario reruns the same MILP with changed capacity, demand, price or
availability but the base case's saved supplier scores; it cannot express "this supplier
became riskier".

**Proposal.** Add a `risk_change` scenario kind (explicit new score with its own source)
and a sensitivity view: the score threshold at which the recommended plan changes.

## L9 Proof-of-concept identity and trust

**Observed.** The approver is a caller-supplied reference recorded as "not authenticated
buyer identity"; the frontend and API share one service token; the stored decision record
of Odoo-history cases still carries the immutable demonstration text "synthetic ML
evidence" (`t17-final-decision-v1`).

**Proposal.** Odoo or OIDC login with per-user roles (buyer, approver), approver identity
from the token in the decision record, a new decision-record version with data-origin
neutral wording, and audit export.

## L10 Local, single-machine performance only

**Measured.** See [P4_MILP_EVALUATION.json](evidence/P4_MILP_EVALUATION.json) and the
summary table in the [P4 handoff](handoffs/P4_VALIDATION.md#milpapi-evaluation): one
laptop, Odoo, PostgreSQL and the API on the same machine, one uvicorn worker, 30 measured
runs per workload. These are descriptive local numbers, not a service-level agreement;
no concurrency, network latency or larger N (> 10 suppliers, the API limit) was measured.

**Proposal.** A load test with concurrent buyers against a containerised deployment, a
solver-time study for 20–100 suppliers and K up to 5 (outside the current API limit), and
an asynchronous job for long solves.

## L11 PDF is a proposal, not an Odoo purchase order

**Observed.** The approved PDF lists one purchase-order proposal per supplier; it has no
legal supplier data and nothing is written back to Odoo (accepted scope: read-only).

**Proposal.** An Odoo addon button that creates draft purchase orders from an approved
plan after explicit confirmation (P5 option), with the approved content hash on the order.

## L12 Usability not assessed with real buyers

**Observed.** UI checks were agent walkthroughs, automated browser tests and screenshots
at 1440 px and 375 px; no session with unfamiliar procurement users and no screen-reader
pass with a real assistive technology.

**Proposal.** 3–5 task-based sessions (SUS questionnaire, task time, errors), and an
accessibility audit with NVDA.

## L13 Smaller data and contract gaps

- Expected Arrival is read as stored at extraction time; returns are not yet features.
- 10 held-out suppliers; overlapping semi-monthly windows make rows correlated (report
  supplier-level bootstrap intervals).
- The quotation-group listing scans the 200 newest open orders (paging would remove it).
- KPI trends over time are not shown (one value per KPI in the snapshot).
- Supplier names exist only in snapshots created since P2.
