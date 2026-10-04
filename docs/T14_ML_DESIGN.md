# T14 — controlled Decision Tree pipeline design

## Authority and entry evidence (2026-10-04, before implementation)

The user explicitly authorizes T14, superseding the historical T13-only ML exclusion
for this increment. Read AGENTS.md, the implementation log, T13 design/handoff and
the existing planning and T8 history contracts. Read the current original Drive
00/02/03/06/07 under SZAKDOLGOZAT / 00_Project_Control through the connector. Their
October 2 pre-merge statements are dated records: fetch and ls-remote now agree on
main `ff8cc5bfebaef5f8d73751991101008830307012` (T13 PR #15 squash merge), and T13
ancestry is verified. A clean working tree and Python 3.11.16 baseline of 328 passed /
37 deselected permit entry. Ruff format/lint and pip check passed. Created
`feature/t14-decision-tree-pipeline` from that verified origin/main.

Reviewed the isolated ML spike `ffa2939` as research only. Reuse its temporal
discipline, explicit leaf support and float32 path explanation idea; do not copy its
quantity/month features, quantity-100 bridge, optional runtime skips, cumulative
optimization or UI code. No spike merge, new HTTP/migration/UI, live discovery,
Odoo writes or Drive edits. The human retains the final decision.

## Observation, labels and provenance

One observation is a supplier/company/product/integer-unit context at a UTC
prediction cutoff, with exact identified prior completed purchase-line evidence.
All rows in the shipped generator are SYNTHETIC, never Odoo records. Synthetic
receipts use complete unit quantities, no returns/cancellations, an explicit
Expected Arrival, completion and availability timestamp. The existing T8 neutral
calculator supplies `delivery_schedule_adherence` on an exact 365-day half-open
history window; returns and incomplete lines retain the existing T8 semantics.
Preparation checks product/unit/company/supplier membership before this calculator.
The extra availability timestamp establishes what was known at cutoff; T8's current
read time alone cannot reconstruct historical as-of truth from a later Odoo export.
Observed training/promotion is outside this controlled contract.

Target v1: class 1 `schedule_watch` means at least two of five completed synthetic
lines in the following 30 days miss their Expected Arrival; class 0
`schedule_regular` means fewer than two. Outcomes must occur after cutoff and be
available by the declared dataset extraction time, after the full outcome window.
They never enter feature preparation. Labels are computed from those outcomes,
not directly from feature columns. A seed-17 generator deliberately creates a
relationship: history adherence below 80 percent generates future per-line misses
with probability 0.65; otherwise 0.10. This is an intentionally constructed
labelling mechanism with noise, not evidence of natural supplier behaviour.
History probabilities span 0.05 to 0.70; prior support spans 8 to 30 completed lines.

## Feature and missing-data contract

Feature version `t14-history-features-v1`, exact ordered numeric inputs:

| Feature | Meaning/unit | Bounds/support |
| --- | --- | --- |
| delivery_schedule_adherence | T8 two-decimal percent against Expected Arrival | finite [0,100], at least three eligible lines |
| historical_completed_count | supporting eligible completed-line count | integer [3,50], never confidence or capacity |

Supplier IDs, company/product/unit, quantity, prices, future outcomes and labels
are metadata, not features. UTC-aware timestamps are mandatory. Every history line
must be completed strictly before cutoff and recorded no later than cutoff. No
missing-value imputation, scaling, data-learned preprocessing or feature selection
is needed: identity conversion to canonical ordered float32 vectors is fixed.
Only the training partition is passed to `fit`; future learned preprocessing must
be fitted there exclusively. Missing, NaN/infinite, extra/reordered features,
withheld history, insufficient class/leaf support and stale input fail closed.

## Split and versions

Dataset/generator v1: 240 disjoint suppliers, 160 training cutoffs on 2026-01-01,
80 test cutoffs on 2026-03-01. Training outcome availability precedes the split
boundary 2026-02-15; test features use only their own independent history, never
training/test target events. Purge overlapping label windows. Supplier groups are
disjoint globally, and exact receipt IDs cannot be reused anywhere across rows or
between history/outcomes. Multiple rows for a supplier are permitted only within
one partition; duplicate observation identities/context cutoffs fail. Equal numeric
vectors for independent suppliers are legitimate repeated patterns, not duplicates.
Test labels remain outside configuration selection, tree tuning and fitting.

Version dataset, feature order, target/class names, mapping and artifact format.
Canonical sorted JSON SHA-256 identifies datasets, training inputs, semantic tree
state and assessments. Record Python major/minor plus exact sklearn/NumPy/SciPy/
joblib versions. Pin sklearn 1.8.0 and numerical dependencies for the recorded
Python 3.11 environment; no new global dependencies or version matrix.

## Model, export, reload and explanation

Exactly one `DecisionTreeClassifier`: gini, best splitter, seed 17, max_depth 3,
min_samples_leaf 10, min_samples_split 20, no class weights or pruning/tuning.
Require at least 20 training rows of each class. Leaf training counts and class
support accompany each inference. Class ties use sklearn's class-0 ordering.
Export locally generated joblib plus a JSON manifest, ignored under `.artifacts/t14/`.
Explicit trusted-local loading is required; compare format/schema/class/mapping/
runtime versions and file SHA-256 before deserializing, then validate fitted tree
shape/configuration/semantic identity and support. Checksums detect inconsistency,
not authenticity. Never load downloaded/user-supplied pickle/joblib artifacts.

Use the actual sklearn `decision_path` and `apply`, with canonical float32 values
and full thresholds, to report each traversed condition, leaf ID, class counts,
raw class-1 fraction and canonical score. No rounded display rule drives inference.
Inference never calls fit and rejects cutoffs earlier than the training-label cutoff.

## Risk mapping and quantity validity

<a id="t14-leaf-exposure-v1"></a>

Mapping `t14-leaf-exposure-v1`: class-1 training count / leaf support, rounded
half-up to four Decimal places. Higher [0,1] means less favourable **controlled
supplier schedule-watch exposure**. It is not calibrated disruption probability,
expected late units or joint plan failure. Leaf score, class and support remain
separate; zero is valid only for an actually scored leaf with zero class-1 support.
An absent or invalid assessment never becomes zero.

The features and target concern a supplier context, not a particular order
quantity. For this controlled proxy only, define the coefficient as constant on an
explicit caller-declared quantity range, valid for the assessment cutoff through
30 days later. Quantity independence is a definition of the planning exposure
proxy, not empirical evidence that delivery is quantity independent. A synthetic
model accepts only synthetic contexts; observed data cannot silently be promoted.
Changing capacity/Q within a declared range does not change the score. Real
promotion requires a new audited dataset/mapping/validity version.

The narrow in-process bridge checks supplier joins, common company/product/unit,
as-of cutoff, model/mapping compatibility, controlled provenance and range coverage
against unchanged T13 business bounds. It returns `RiskCoefficient` tuples and
`ExternalRiskContext` with definition/assessment/validity references. It never
narrows commercial feasibility to fit a score, extrapolates beyond a declared
range, or changes the MILP. All supplied suppliers must have assessments; explicit
cost-only planning remains the original separate T13 path.

## Evaluation and boundaries

Report fixed labels [0,1] confusion matrix, accuracy, per-class precision/recall/F1
and support, macro metrics, dataset/split hashes, seed, config, runtime and global
tree text. Undefined metrics use JSON null with reasons, not hidden zeroes. A
held-out absent class is reported; insufficient training classes are rejected.
Document the actual reload/inference/three-supplier CBC demonstration. Scientific
claims stop at controlled pipeline behaviour. FR-V2-02/03, AC-V2-02/03 and the
tree-path portion of FR-V2-07 target LOCAL PASS; full V2 remains open.

T15 owns live as-of evidence/assembler, API/scenario orchestration, V2 snapshots and
stored-only retry/retrieval. No V1 behaviour changes. Proposed Drive synchronization
belongs in T14 handoff; do not write those documents here.

Library references: [tree API](https://scikit-learn.org/1.8/modules/generated/sklearn.tree.DecisionTreeClassifier.html),
[leakage guidance](https://scikit-learn.org/1.8/common_pitfalls.html),
[persistence limitations](https://scikit-learn.org/1.8/model_persistence.html).
