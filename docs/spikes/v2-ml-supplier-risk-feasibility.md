# V2 ML supplier-risk data and model feasibility spike

## Recommendation and scope

**GO WITH CONDITIONS for an isolated, interpretable ML research capability.**
The pipeline and ML-to-MILP boundary work. **NO-GO for claiming useful real-world
prediction or promoting this trained model to business use.** No suitable real
training export is established, and this fixed tree underperforms its non-ML
baseline even on the synthetic chronological holdout.

This spike implements exactly one ML algorithm, `DecisionTreeClassifier`, with one
fixed configuration. It does not approve mandatory ML in the official thesis
baseline. The proposed capability is evaluated as **SAFE_IF_GENERALIZED**: require
implementation and critical evaluation, explicitly allow an identified controlled
dataset, and do not require demonstrated predictive superiority before data exists.

Branch: `spike/v2-ml-supplier-risk-feasibility`, based on local commit
`706a882` preserving the previous input audit. The earlier optimization spike is
preserved in `0a316f8`. This ML follow-up remains uncommitted at handoff. Nothing
was pushed, merged, or promoted; Google Drive living documents are unchanged.

Implementation lives in `tools/v2_ml_risk/`. The only other source changes are a
small explicit score contract in the **experimental** `tools/v2_optimization/`
package and optional dependency metadata. Production application, Decision Core,
API, adapters, persistence and frontend are unchanged.

## 1. Exact observation and target

One observation represents **one completed, stock-backed purchase-order-line
receipt obligation**, with a stable supplier/product relationship and canonical
quantity/UoM. Receipt moves and partial/backorder transfers are events belonging
to that line, not separate training observations. Repeated orders from the same
supplier are distinct observations.

The proposed decision instant is when the procurement comparison inputs are
frozen, before allocation/human approval. It is not the receipt date, export date,
or automatically the order's current creation/confirmation timestamp. This instant
and the original quantity/Expected Arrival must be explicitly recorded.

Let `Q` be the immutable requested line quantity at that decision and `S` its
immutable operational **Expected Arrival**. Sort admissible inbound receipt events
by actual completion time. `C` is the first timestamp at which cumulative completed
quantity reaches or exceeds `Q`. The binary label is:

```text
schedule_miss = 1 if C > S
schedule_miss = 0 if C <= S
```

This is conditional on eventually completing an eligible obligation. A first
partial receipt cannot produce an on-time label if the rest arrives late. Exact
equality with Expected Arrival is on time. A completed line contributes once,
irrespective of order value, quantity or number of receipts.

The existing T7/T8 descriptive metric uses the observed schedule/quantity and
relationship-backed receipt facts. The proposed predictive label is a stricter
decision-snapshot variant; it is **not already supplied by the T8 API**.

## 2. Target semantic limitations

Expected Arrival is an operational planning reference, not a supplier-confirmed
promise. The target does not establish contractual lateness, supplier fault,
reliability in every product/company, service quality, expected financial loss, or
the chance of a supplier being late on an arbitrary future order. Warehouse
processing, internal schedule choices and recording delays can affect it.

T7's on-time/late/backorder/return cases validate receipt semantics; they do not
validate a historical feature snapshot at each procurement decision. Current
`date_planned` and `product_qty` can be edited. A retrospective read cannot prove
their earlier values or when a fact was knowable. The accepted projection lacks a
decision instant, schedule/quantity version history, and outcome-recording history.

The small canonical PoC assumes integer units, one product, one company and one
UoM. Its already-past-due schedule references are excluded as ambiguous for this
prospective subset. This is an additional limitation, not a reinterpretation of the
T7 fixture, whose deliberately past Expected Arrival was useful for testing lateness.

Cancelled, incomplete, return-affected and changed-quantity lines are excluded.
Consequently this is not a model of cancellation/non-delivery risk. Completion-only
sampling can produce survivorship and censoring bias. Real-data acceptance must
examine excluded obligations and the label horizon; silently treating unfinished
lines as on time would be wrong.

## 3. Dataset construction and availability rules

`dataset.py` separates `Observation`, `Receipt`, `Outcome` and ordered `Example`
features. No ERP, ML or optimization library is required for these rules.

1. Require exact stable identities and timezone-aware timestamps. Map product,
   company/UoM and receipt direction upstream using validated relationships.
   The synthetic canonical receipt type represents only admitted inbound events;
   it is not an Odoo discovery or mapping mechanism.
2. Exclude cancelled/return-affected/changed-quantity lines, missing Expected Arrival,
   unproven decision snapshots, receipts predating the decision, an already-past-due
   reference, incomplete quantities and outcomes unavailable at export time.
3. Compute completion using cumulative quantities. Label only after full completion.
   `available_at = max(completed_at, outcome_recorded_at)` conservatively models
   when the completed outcome is usable. This field is supplied in synthetic data;
   no currently validated Odoo field is claimed to prove it.
4. Derive prior history from the same supplier/product, within the trailing 365 days
   by completion, with both completion and availability **strictly before** the
   row's decision. Exclude the current line. A record at exactly the decision time
   is not prior history. Require at least three eligible prior outcomes; otherwise
   exclude the training example or withhold its future assessment.
5. Sort by decision timestamp and stable line identity; reject duplicate IDs.
   No target, receipt status or actual completion enters the feature vector.
6. Apply the chronological split and label-availability purge described below.
   Test features use the frozen training history pool, never holdout outcomes.

Source attribution remains outside mathematics, following T6's distinction between
canonical facts and provenance. Attribution alone does not certify truth. A future
real export also needs an auditable as-of policy for late corrections, returns and
record versions; the synthetic flag/availability contract does not prove one exists.

## 4. Available data inventory

No real production history export is present for this spike. A fresh unauthenticated
read-only login reachability probe returned `ConnectError`; read-only Podman machine
inspection reported `Running=false`, `Starting=false`. No VM/service was started,
no JSON-2 history call or Odoo business-data mutation was performed, and no generic
stock reads, direct database access or privilege expansion was attempted.

| Evidence population | Lines/outcomes | Suppliers/products | Classes 0 / 1 | Interpretation |
| --- | ---: | --- | --- | --- |
| Documented T7/T8 controlled fixture | 4 lines, 3 eligible completed outcomes, 1 return exclusion | 1 / 1 | 1 / 2 | Historical acceptance evidence; not a fresh export |
| Established real rows with leakage-safe decision features | 0 established | 0 established | Not available | No qualifying export is established; actual database totals are unknown |
| Synthetic generated source | 726 lines, including 6 deliberate exclusions | 12 / 1 | 410 / 310 among 720 labelled outcomes | Pipeline demonstration only |
| Synthetic usable training | 464 | 12 / 1 | 266 / 198 | Earlier decisions, labels available before cutoff |
| Synthetic usable holdout | 180 | 12 / 1 | 108 / 72 | Later decisions, earlier history frozen |

The controlled fixture was accepted on 2026-09-20. Its setup specifies receipts on
one local administrator date `D` and Expected Arrival at `D-1` or `D+1`; no exact
per-line UTC export/time-span inventory is established here. Exact database totals,
other suppliers/products, class imbalance and null counts are **unknown**. The
accepted projection does not provide decision-time snapshots for the four documented
lines, even where current schedule/quantity values are present. One supplier and
three outcomes cannot support a defensible chronological tree evaluation with both
classes and supported leaves. This conclusion uses the structure of this dataset,
not an arbitrary universal minimum-record threshold.

Synthetic decisions span `2025-01-01T00:00Z` to `2026-02-18T11:00Z`; latest full
completion is `2026-03-15T05:00Z`, export as-of `2026-04-01T00:00Z`. Each of 12
suppliers has 60 completed lines. There is one product, company and integer UoM.
Of all labelled synthetic outcomes, 43.06% miss the schedule. Training positive
share is 42.67%; holdout positive share is 40.00%. Per-supplier counts, exclusions
and time bounds are recorded in the companion JSON.

Missing-field/source counts in the synthetic source: one missing Expected Arrival,
one unproven reference snapshot, zero missing supplier/product/decision/quantity
fields. One each is cancelled, return-affected, changed-quantity and incomplete.
Of the 720 labelled outcomes, 56 rows lack three prior known outcomes and 20 earlier
decisions have outcomes unavailable before the split. Thus `720 - 56 - 20 = 644`
usable examples. The six unsupported source lines are additional exclusions.

## 5. Synthetic generation and permitted claims

Generation uses only `random.Random(17)` and fixed timestamps. For each of 60 weekly
rounds and 12 suppliers, quantity is sampled from `{50,100,200,350}`. A hidden
supplier propensity is `0.08 + supplier_index*0.035`, with `0.24` added for quantity
at least 200 and `0.07` for November/December. An independent uniform draw produces
the latent late/on-time outcome; receipt timestamps are then constructed on the
appropriate side of the decision-time schedule. Expected Arrival is decision plus
12 days; half arrives on day 5 and the remainder at full completion. Outcome
recording is one day after completion. Six explicit boundary exclusions are added.

Hidden propensity, the random draw, actual dates and the generated class are never
features. Stochastic overlap prevents a deterministic target encoding in the
selected feature matrix. The generator nevertheless assumes quantity/season/supplier
relationships by construction. Finding splits on those relationships would not
discover real business causality. The poor holdout result is retained without
regenerating data, changing seeds or tuning against the test set.

Permitted claims: the controlled feature/label pipeline, leakage gates, fitting,
metrics, explanation, deterministic outputs and score-to-MILP interface execute.
Forbidden claims: representative Odoo training coverage, real supplier-risk accuracy,
predictive improvement, calibrated probability or demonstrated business benefit.

## 6. Candidate feature inventory

Classes below describe **availability at the decision**, not merely a technically
readable field. “Conditional” means an immutable as-of snapshot must be established
for real data. No broad field mapping is approved by this table.

| Candidate | Exact source / type | Availability class | Missing handling and leakage risk | Initial use |
| --- | --- | --- | --- | --- |
| Prior adherence | Eligible prior full-line outcomes under T7 receipt semantics; fraction `[0,1]` | DERIVED_ONLY_FROM_PRIOR_HISTORY | Withhold below 3; final export aggregate would leak later outcomes; current T8 aggregate alone cannot reconstruct all past features | Yes, synthetic as-of derivation |
| Prior completed count | Same prior supplier/product/window population; integer | DERIVED_ONLY_FROM_PRIOR_HISTORY | Withhold below 3; never include own/future/unrecorded outcome | Yes, support/context |
| Requested quantity | T6 quotation `purchase.order.line.product_qty`, frozen at decision; canonical integer here | AVAILABLE_AT_DECISION_TIME, conditional | Required; current/final edited quantity is unsafe; quote quantity is not authoritative approved V2 demand | Yes, snapshot only |
| Decision month | Explicit recorded procurement decision instant; integer 1–12, UTC here | AVAILABLE_AT_DECISION_TIME, conditional | Required decision timestamp; receipt month/export month leaks or misrepresents timing | Yes; zero fitted importance here |
| Expected Arrival | `purchase.order.line.date_planned`, immutable decision reference; aware datetime | AVAILABLE_AT_DECISION_TIME, conditional | Required for target; current mutable value is insufficient | Target reference only, not feature |
| Planned interval | Frozen Expected Arrival minus decision timestamp; duration | SEMANTICALLY_UNVALIDATED for real prediction | Could reflect internal planning; does not prove supplier promise; not established as decision-time history | No |
| Commercial supplier ID | `purchase.order.partner_id -> res.partner.commercial_partner_id`; stable string | AVAILABLE_AT_DECISION_TIME | Required join key; including ID encourages memorization and unseen-ID failure | Join only |
| Product/UoM/company | Validated purchase-line/product/company relations; stable IDs | NOT_USEFUL in this one-product/company/UoM dataset | Required cohort gates; cross-cohort conversions cannot be guessed | Cohort/validation only |
| PO/line ID, origin/name | Stable IDs or display text; string | NOT_USEFUL | Line ID joins and orders rows only; textual similarity is never a relationship | No |
| Configured vendor delay | `product.supplierinfo.delay`; integer planning days | SEMANTICALLY_UNVALIDATED | Not promised delivery nor historical actual lead time; historical version unknown | No |
| Prior average actual delay | Prior completion minus frozen prior schedule; duration | DERIVED_ONLY_FROM_PRIOR_HISTORY, conditional | Must use prior outcome availability and original schedule; no accepted current metric/decision snapshots | No; unnecessary new KPI |
| Prior late count | Same time-safe prior outcome population; integer | DERIVED_ONLY_FROM_PRIOR_HISTORY | Redundant with adherence/count; unsafe if computed from full export | No |
| Current actual completion/delay | Relationship-backed done inbound `stock.move.date`, computed full completion; datetime/duration | POST_OUTCOME_LEAKAGE | Directly defines the target | Explicitly rejected |
| Final received quantity/status | Final `qty_received`, `receipt_status`, done states; quantity/enum | POST_OUTCOME_LEAKAGE | Reveals eventual fulfillment/outcome; cannot stand in for decision quantity | Explicitly rejected |
| Own schedule-miss/adherence | Current line label or KPI including the line; integer/fraction | POST_OUTCOME_LEAKAGE | Target encoding or self inclusion | Explicitly rejected |
| Final return/cancellation/backorder facts | Relationship-backed final events/status; bool/IDs | POST_OUTCOME_LEAKAGE | Outcome eligibility/diagnostics only; using eventual facts as predictors leaks | Explicitly rejected |
| Current quotation price, capacity, hard MOQ | T6 quote price / V2 attributed supplemental terms; Decimal/integer | AVAILABLE_AT_DECISION_TIME only within validated context | No historical snapshots for training; price-quantity applicability and capacity not automatically Odoo facts | No; MILP terms remain separate |

## 7. Selected schema and supplier identity choice

The exact, versioned feature order is:

```text
historical_adherence_before_decision
historical_completed_count
requested_quantity_at_decision
decision_month
```

An exact whitelist rejects additional/missing fields and nonfinite/out-of-range
values. No generic dataframe-column selection can accidentally add outcome fields.
Supplier IDs are grouping keys and output identities, not numerical/categorical
features. The model receives no company, product or supplier identifiers.

Conceptually, an identity-aware tree could learn supplier-specific behavior but
would easily memorize a tiny supplier panel and fail for new IDs. The chosen model
uses supplier-specific **prior statistics without supplier identity as a feature**,
plus decision quantity/calendar context. It can score a new supplier only after
enough compatible prior history exists; otherwise it withholds. No second model
was trained to compare these alternatives. Shared suppliers across this holdout
test later orders for known suppliers, not unseen-supplier generalization.

## 8. Configuration and methodology

Pinned algorithm: `scikit-learn==1.8.0`, `DecisionTreeClassifier`.

```python
criterion = "gini"
splitter = "best"
max_depth = 3
min_samples_leaf = 12
min_samples_split = 24
random_state = 17
class_weight = None
```

The configuration bounds interpretation complexity and prevents singleton leaves.
Both classes have substantial synthetic training support; no class weights are
applied. This does not imply the resulting recall is satisfactory. No random split,
hyperparameter sweep, alternative ML algorithm, feature selection search or
calibration model was used. The same configuration is fitted three times solely to
test reproducibility.

Chronological cutoff is **2025-11-12 00:00 UTC**. Training decisions and training
outcome availability must both precede it; 20 pending earlier outcomes are purged.
The remaining warmup rows can supply prior outcomes even if they lack enough
features to become training examples themselves. Every training row sees only
strictly earlier available history. Holdout decisions are at/after the cutoff,
their labels available by export as-of. Holdout feature history is frozen to the
eligible earlier pool, including no holdout outcomes. It can age out of the 365-day
window but is not updated with test labels. This is a deliberately conservative
fixed-model backtest, not a live incremental history/retraining policy.

No transformations are fitted to test data. Feature order is fixed, input rows are
sorted, and the model uses float32 input consistently with scikit-learn's tree
execution. Classification uses the tree's ordinary class prediction; at an exactly
tied leaf, ordered class 0 wins. The baseline predicts miss when `1-prior_adherence
>= 0.5`, including ties. This small tie-policy difference is explicit.

## 9. Evaluation and non-ML baseline

Confusion matrices use rows=actual, columns=predicted, labels `[0,1]`:

| Predictor | TN | FP | FN | TP | Positive precision | Positive recall | Positive F1 | Balanced accuracy | Accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Bounded Decision Tree | 104 | 4 | 68 | 4 | 0.5000 | 0.0556 | 0.1000 | 0.5093 | 0.6000 |
| Prior historical-risk threshold | 79 | 29 | 41 | 31 | 0.5167 | 0.4306 | 0.4697 | 0.5810 | 0.6111 |

Both use the same 180 held-out lines: 108 on time, 72 schedule misses. The tree
misses 68 of 72 positive cases. It is worse on positive F1, recall, balanced accuracy
and accuracy. **No useful predictive improvement beyond the historical KPI is
demonstrated.** Its quantity split is additional model structure, not evidence that
the additional information helps. False-positive/negative business costs are not
specified, so no alternate business-optimal threshold is claimed.

These are exact executed synthetic metrics, not fabricated real-data estimates.
No real predictive metrics can be reported. Confidence intervals, unseen-supplier
tests, external validation and repeated temporal folds are not established. A
single-class holdout is rejected for meaningful two-class evaluation.

## 10. Global and local interpretation

Actual tree: **depth 3, six leaves**. Training leaf supports are `20,178,20,195,29,22`;
all exceed the configured minimum 12. Class counts `[on-time,miss]` are respectively
`[8,12]`, `[126,52]`, `[20,0]`, `[77,118]`, `[18,11]`, `[17,5]`.

Impurity importances: quantity `0.498817`, prior adherence `0.413089`, prior count
`0.088094`, calendar month `0`. These describe fitted splits, not causal attribution
or proven predictive value. Complete display-rounded rules and exact local
thresholds are in the JSON. The root splits quantity at 150; subsequent splits use
prior adherence and, on one branch, historical count at 35.5.

Example held-out line `S00-W45`, decision `2025-11-12T00:00Z`:

```text
quantity=200 > 150
prior adherence=0.863636... <= 0.8765243887901306
prior completed count=44 > 35.5
-> leaf 9, training support 29, counts [18,11]
-> predicted class 0
-> raw positive-class score 11/29 = 0.3793103448275862
-> canonical score 0.3793
```

The actual holdout class 0 is shown only for evaluation. It is not used to generate
the feature vector or explanation. Local rules are reconstructed from the model's
actual decision path using float32 feature values and unrounded thresholds; the
rounded global text is display-only. No SHAP or separate explanation framework is
needed. A minimum leaf count does not establish adequate statistical confidence.

## 11. Score semantics and neutral output contract

`SupplierRiskAssessment` contains supplier ID, Decimal `ml_risk_score`, predicted
class, model hash/version, evaluation context, feature observation timestamp and
local explanation. The model validates that assessment time is not before its
training-data cutoff; historical holdout assessment is explicitly a backtest, not
a claim that a model existed at those historical dates. Actual fitting time is
recorded separately.

The raw positive-class score is the positive class proportion in the reached
training leaf. Class counts are independently reconstructed from training labels
assigned to that leaf, avoiding confusion between normalized `tree_.value` and
integer sample counts. With no class/sample weights, the ratio agrees with
`predict_proba`. Canonical scores use Decimal `positive_count/leaf_count`, rounded
half up to four decimals. Raw score, count distribution, rounded score, thresholds,
model/config/schema/dataset hashes are retained outside the optimizer.

Call this an **ML-derived schedule-miss risk score**, not “the supplier has a 37.93%
probability of being late.” No calibration/statistical validation supports that
claim. A pure training leaf produces 0 or 1; neither is a guarantee. The demo's
`S00` score zero arises from only 20 on-time training examples in its leaf.

The mathematical core consumes only `SupplierRiskScore(supplier_id,value)` with
finite Decimal `[0,1]` on the four-decimal grid, exactly one score for every input
supplier. Missing/duplicate/unknown identities, floats and excessive precision
fail closed. Supplied scores explicitly override the historical coefficient path
within the experiment; the old historical path and sample-size withholding remain
the default. Plans state `risk_basis="supplied_score"`. No ML score is disguised
as `historical_adherence=1-score`, and no historical sample count is invented.

## 12. ML-to-MILP proof and limits

Three **fixed** synthetic suppliers `S11`, `S06`, `S00` are evaluated at the same
cutoff, product and comparison quantity 100 using frozen earlier history. They are
chosen by fixed demo IDs, not by labels, training success or model supplier choice.
Scores are `0.2921`, `0.2921`, `0.0000`. Illustrative costs/capacities are respectively
`10/60`, `10.5/80`, `11/100`. Required quantity is 100, maximum two suppliers,
concentration at most 0.8 and epsilon cost premium 0.05.

| Plan | S11 quantity | S06 quantity | S00 quantity | Total cost | Weighted score exposure | Premium |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Proven minimum cost | 60 | 40 | 0 | 1020 | 0.292100 | — |
| Proven minimum score within 5% cost cap | 29 | 0 | 71 | 1071 | 0.084709 | 0.05 |

Exposure is `sum(x_i * canonical_score_i) / Q`. CBC proves the objective phases and
the existing exact primal/lock/tie-break validation still runs. The bridge passes
only IDs/scores. The optimizer imports neither scikit-learn nor Odoo/feature code;
the dataset/model modules import no optimizer. Boundary tests run without optional
dependencies. ML evaluates scores; MILP chooses suppliers/quantities; a human
remains responsible for any final business decision. This spike executes no action.

**Material limitation:** quantity is an ML feature, while the MILP uses fixed
scores evaluated at comparison quantity 100 even when allocations become 29/71.
The proof establishes interface mechanics, not consistent prediction at the final
allocated quantities. Also a line-level event score weighted by units is a planning
proxy, not calibrated expected late units, joint plan failure probability or loss.
Before promotion, explicitly decide whether to use a quantity-independent supplier
context or a separately validated bounded quantity/score representation. This spike
does not implement that extension or conceal the mismatch.

## 13. Determinism and reproducibility

Executed environment: Windows, Python **3.14.7**, scikit-learn **1.8.0**, NumPy
**2.5.3**, SciPy **1.18.1**, joblib **1.6.0**, threadpoolctl **3.7.0**, cloudpickle
**3.1.2**, PuLP **3.3.0**.
All installations stayed in the ignored project `.venv`. Python 3.11 remains the
repository compatibility baseline; a 3.11 interpreter was not established in the
preceding audit, and this ML spike has **not** verified execution on it. The pinned
scikit-learn release declares Python >=3.11; that metadata is not a local run.

Reproduce from the repository root, in the project environment:

```powershell
python -m pip install -e ".[dev,optimization-spike,ml-spike]"
python -m tools.v2_ml_risk.experiments
pytest tests/test_v2_ml_dataset.py tests/test_v2_ml_model.py tests/test_v2_ml_integration.py tests/test_v2_ml_architecture.py -v
```

The optional extras leave runtime dependencies unchanged. `tools` remains
repository-local tooling, outside installed runtime packages. Default hosted CI
does not install these extras: optional model/solver tests skip when absent;
dependency-free leakage/architecture tests still run. No hosted CI was run here.

Dataset hash:
`bd038d336ca2f4334c083dc1567dfc8cbe346377890672e5c110df57dad808ce`.
Feature schema hash:
`781a15c6077a90c4b50cdcffb3f0abd3d94a98fb27df410bde14b7ec295d986c`.
Model hash:
`2fb01bd8d63ce53ac33ee8a665b215a58351a1342ce7b46bf44c2b76da87b892`.
The JSON also records the target/config hashes, every effective tree parameter,
actual UTC training timestamp and output-score hashes. Three identical fits produce
identical model hashes, class predictions and scores. Input-row reordering also
preserves the canonical dataset/examples. Timestamp metadata varies between runs
and is intentionally excluded from model identity. Reproducibility is demonstrated
on this recorded platform/dependency set, not universally across future versions.

## 14. Leakage, boundary and regression validation

Explicit tests cover partial completion, exact schedule equality, return/cancellation,
changed quantity, missing/unproven reference, timestamp ambiguity and unavailable
outcomes. Feature tests reject target, completion, delay, final received quantity,
recording timestamp, receipt status and supplier ID columns. They prove strict
prior completion/availability, self/other-product/supplier exclusion, future-record
invariance, stable feature order and minimum-history withholding.

Chronological tests assert label-availability purging and that no holdout identity
enters any history feature. Replacing all test outcomes changes labels but leaves
both training and test feature vectors unchanged. Model tests verify deterministic
fits, local branch rules, leaf counts, score quantization, single-class rejection
and refusal to predict before the training-data cutoff. Integration tests verify
explicit external score validation, unchanged historical withholding/defaults,
cost cap and score reduction, and actual tree output flowing through the bridge.

Executed local checks:

| Check | Result |
| --- | --- |
| Focused ML plus optimization suite | PASS: 78 passed (initial pytest cache-write warning only) |
| Ruff format/check | PASS |
| Compileall runtime and experimental packages | PASS |
| Project dependency consistency (`pip check`) | PASS |
| Full fast tests | PASS: 349 passed, 37 deselected, 18.10 seconds on Python 3.14.7 |
| JSON parsing, Git whitespace and artifact consistency | PASS: recorded/generated hashes, metrics and plans agree |
| Live Odoo / controlled live contracts | SKIPPED: local environment unavailable |
| Python 3.11 execution | UNVERIFIED |
| Hosted CI, browser/E2E, production ML integration | NOT RUN / outside this spike |

The full fast run disables only pytest's cache provider after the focused run's
cache-path warning. Tests and strict markers remain enabled. Existing FastAPI/
Starlette deprecation warnings are not ML failures.

## 15. Thesis-task readiness and promotion conditions

The proposed wording is **SAFE_IF_GENERALIZED**:

> Apply a machine-learning method to historical procurement data in order to
> support data-driven supplier evaluation.

As written it can imply that suitable real historical data is already available.
That is not established. Safer implementation-independent wording is:

> Implement and critically evaluate a machine-learning method for supplier
> evaluation using available historical procurement data or an explicitly
> identified controlled dataset.

“Machine learning” can name the proposed capability once the thesis direction is
approved. “Classification” can name the intended research approach if the target
is approved, but need not constrain the official task. Decision Tree, specific
features/metrics and scikit-learn belong in the implementation/evaluation plan,
not the official task unless explicitly fixed by the supervisor/topic. Require
transparent evaluation and limitations, not a predetermined accuracy or superiority.

Before V2 baseline promotion:

1. Obtain explicit thesis scope approval, including controlled-data acceptability
   and the distinction between research implementation and useful real prediction.
2. Establish bounded read-only historical export coverage and auditable decision-time
   schedule/quantity/reference snapshots plus outcome availability/correction policy.
   Keep exact joins, company/UoM scope and accepted security restrictions.
3. Inventory real suppliers/products/time coverage, both classes, exclusions and
   supported train/test leaves; decide the completion horizon and censoring policy.
4. Evaluate the same bounded algorithm on independent later data, with predeclared
   metrics and business error costs. Do not assert improvement when the baseline wins.
5. Resolve quantity-context/fixed-coefficient semantics and risk-objective meaning;
   define withholding/fallback and human presentation of low-support scores.
6. Verify Python 3.11 and optional-dependency checks on the intended environment;
   approve any later production boundaries separately. No automated retraining,
   Odoo writes, frontend changes or runtime feature adapter is approved here.

## Evidence and primary references

Repository evidence reviewed: the preceding
[optimization report](v2-procurement-optimization-feasibility.md),
[input audit](v2-odoo-input-capability.md), [T6 design](../T6_DESIGN.md),
[T7 handoff](../T7_HANDOFF.md), [T7 fixture](../T7_FIXTURE_SETUP.md),
[T8 handoff](../T8_HANDOFF.md), current historical calculator/adapter architecture,
`tests/test_historical_performance.py`, controlled T7/T8 live-contract tests and
experimental optimizer source/tests. Recorded results are in
[the companion JSON](v2-ml-supplier-risk-results.json).

Primary library references: [pinned release and Python compatibility metadata](https://pypi.org/project/scikit-learn/1.8.0/),
[Decision Tree API and leaf-score semantics](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html),
[data leakage guidance](https://scikit-learn.org/1.8/common_pitfalls.html),
[temporal evaluation guidance](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
The stable API documentation currently describes a newer release; this experiment
uses installed 1.8.0, records its effective parameters, and tests the relevant
behaviors directly. The custom holdout does not invoke `TimeSeriesSplit`.

## Final questions answered

1. **Observation:** one completed purchase-line receipt obligation, with decision-time
   context; partial/backorder moves belong to that same line.
2. **Defensible target:** full quantity completion later than immutable decision-time
   operational Expected Arrival, conditional on the eligible completed subset.
3. **Unjustified semantics:** supplier-confirmed promise, contractual failure, supplier
   fault, universal supplier reliability, cancellation/non-delivery prediction and
   calibrated lateness probability.
4. **Decision-time features:** snapshot quantity/calendar context and strictly prior
   available adherence/count. Their real historical snapshots remain unproven.
5. **Leaky candidates:** own/future-inclusive KPIs, actual completion/delay, final
   received quantity/status, eventual returns/cancellations and mutable final fields
   substituted for originals.
6. **Time-safe history:** technically yes with prior completion AND recording time,
   exact joins and immutable references; not established for real historical exports.
7. **Real usable counts:** zero established leakage-safe training rows, actual totals
   unknown. Documented controlled evidence is four lines, three outcomes, one supplier,
   one product; it is not a representative real dataset.
8. **Real sufficiency:** not established; the documented fixture cannot support
   meaningful time-aware classifier evaluation.
9. **Justified PoC:** the deterministic 726-line synthetic source, 720 labels and
   644 usable feature rows validate mechanics. Its accuracy cannot establish real
   prediction, business value or representativeness.
10. **Bounded tree suitability:** technically yes for an interpretable binary
    experiment; this configuration is not empirically good enough for prediction.
11. **Added value:** not demonstrated. Tree F1 0.10 and balanced accuracy 0.5093
    trail the historical baseline's 0.4697 and 0.5810.
12. **MILP-compatible risk score:** yes as an explicitly uncalibrated leaf-derived
    four-decimal score, with support/explanation retained; no probability claim.
13. **Independence:** yes; dataset/model has no Odoo or optimizer dependency, and
    production runtime does not import experimental ML tooling.
14. **Clean integration:** technically yes via explicit generic scores; fixed-score
    allocation and quantity-dependent features still require semantic resolution.
15. **Mandatory thesis capability:** SAFE_IF_GENERALIZED as implementation and
    critical evaluation with explicitly approved controlled-data scope. Useful real
    predictive improvement should not be mandatory yet; baseline approval is separate.
16. **Remaining conditions:** approved research scope, sufficient audited temporal
    data, target/censoring decisions, honest independent baseline comparison, resolved
    quantity/score semantics, withholding and Python 3.11 verification.

**Final recommendation: GO WITH CONDITIONS. Stop at this feasibility spike.**
