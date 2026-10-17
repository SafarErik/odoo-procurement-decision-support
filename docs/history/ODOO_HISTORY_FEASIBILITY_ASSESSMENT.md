# Bounded Odoo history and V2 Decision Tree: feasibility assessment

Assessment date: 2026-10-14. Source inspection and bounded read-only live probes. This assessment does not
authorize implementation, Odoo data preparation, model training, source promotion,
schema changes, or requirement changes. The official assignment and all five CORE
functions remain unchanged. Repository baseline: `feature/odoo-data-integration`,
HEAD `86c389c0d07dd1893d5ace32bb035fbd05adf2b2`; initially clean working tree.

## Conclusion

**GO WITH CONDITIONS for a bounded data-readiness increment; NO-GO for connecting
the current synthetic model directly to Odoo-derived feature snapshots.** The
reusable components are substantial, but source compatibility is intentionally
closed at multiple boundaries. Equal feature names and matching identifiers do
not establish model validity. Odoo-hosted synthetic test records would demonstrate
transport and integration, not observed supplier predictive validity.

The smallest safe next implementation is a read-only export/readiness report for
one selected company/product/unit and explicit supplier/line identities. It should
prove context membership, exact KPI/support, temporal availability limitations and
provenance before any model promotion. Connecting new history to planning is a
subsequent conditional increment, requiring an explicitly compatible, independently
evaluated offline artifact and all downstream consumers to recognize its evidence.

Traceability: controlled history FR-V2-01/02 and AC-V2-01/02; Decision Tree
FR-V2-02/03/07 and AC-V2-02/03; reproducibility and leakage NFR-V2-02/03/04/06/08;
stored results/approval/PDF FR-V2-10/11/12 and AC-V2-10/11/12; integrated acceptance
AC-V2-13. These are existing identifiers, not new requirements.

## Canonical and published state checked in this assessment

The five canonical living documents were fetched in full, including their latest
2026-10-14 addenda; archives were not substituted:

| Document | Drive modified time (UTC) | Relevant current direction |
| --- | --- | --- |
| [00_THESIS_STATUS](https://docs.google.com/document/d/1X2WGVVYn0j1ymX0cv5kQQGIaJiEc7pcLSZYDIrXA3VU/edit) | 19:40:35 | Five CORE functions fixed; history feasibility and current Odoo-to-PDF reproduction are priorities |
| [02_ROADMAP](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4/edit) | 19:42:51 | Readiness first, conditional history/model integration afterward; rolling-wave schedule |
| [03_ARCHITECTURE_DECISIONS](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit) | 19:42:42 | ADR-024–027 boundaries retained; no automatic synthetic-to-observed promotion |
| [06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit) | 19:42:52 | Controlled/synthetic datasets remain accepted; test history in Odoo retains synthetic origin |
| [07_DEVELOPMENT_STATUS](https://docs.google.com/document/d/1Xgphr_FEurdFlK651s2DTJWlubwt9vii1c5st9iO6E8/edit) | 19:43:00 | T7S/T8 and T14 are separate paths; identity, temporal and artifact audit precedes integration |

Latest addenda also replace the extra mandatory novice-cohort gate with documented
owner trials plus technical evidence. This assessment records that existing
canonical decision; it changes neither requirements nor past failed UX evidence.

Live GitHub REST reads reconcile publication discrepancies in Drive and the dated
`docs/agents/project-baseline.md` routing guide:

- [PR #24](https://github.com/SafarErik/odoo-procurement-decision-support/pull/24)
  merged on 2026-10-11 at 15:13:03 UTC, merge `ed4be413b11dc469307fc1bb1ed4bd6c16c17b88`.
- [PR #31](https://github.com/SafarErik/odoo-procurement-decision-support/pull/31)
  merged on 2026-10-14 at 19:57:08 UTC (21:57:08 Europe/Budapest), merge `86c389c`.
  Published PR head was `ecbb41d26cfd223f9136771c8149b5e538e6a299`.
- [Published main](https://github.com/SafarErik/odoo-procurement-decision-support/tree/86c389c0d07dd1893d5ace32bb035fbd05adf2b2)
  matches local HEAD. Exact merge-SHA [Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38627957510)
  and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38627957452)
  are completed SUCCESS, both push-triggered. These are hosted checks, not this
  assessment's live history or browser acceptance.

Drive's statements that #24/#31 are open and its older local SHA are superseded by
those live publication facts. Canonical functional/source rules remain authoritative.
No Drive document or GitHub issue was edited. `gh` was absent, so the connected
GitHub GET tools were used; a PR-only workflow wrapper returned an empty list,
then the general workflow REST read established the actual post-merge runs.

## Current versus proposed data flow

```text
CURRENT OFFLINE MODEL
generated t14_synthetic prior receipts + separately future synthetic outcomes
  -> two historical features + target -> purged temporal/supplier split
  -> offline DecisionTreeClassifier -> trusted versioned artifact

CURRENT V2 /from-odoo
read-only Odoo quotations/currency + explicit business terms
  + separately generated t14_synthetic receipt history
  -> synthetic features -> saved synthetic artifact inference
  -> validated exposure coefficients -> unchanged MILP -> immutable base
  -> stored original-base scenarios -> human decision -> approved snapshot PDF

SEPARATE EXISTING HISTORY PATH
exact company/purchase-line selection -> T7S guarded Odoo projection
  -> neutral raw history snapshot -> T8 adherence/support/warnings
  -> V1 contextual history; no V2 model connection

PROPOSED FIRST INCREMENT
one fixed quotation group + trusted exact history manifest
  -> bounded read-only T7S capture -> validate raw company/supplier/product/unit
  -> existing T8 KPI -> immutable offline readiness export/report
  -> explicit usable/withheld/blocked result, without a model score

LATER, ONLY AFTER DATA/MODEL GO
audited capture/as-of history + distinct eligible future label evidence
  -> compatible versioned offline dataset/split/training/evaluation/artifact
  -> runtime quotation and bounded history reads after creation lock/replay lookup
  -> source-compatible features/inference -> same ML-to-MILP bridge and solver
  -> versioned immutable evidence -> existing scenarios/approval/PDF consumers
```

The proposed runtime branch is conditional, not current capability. Transport
`odoo_projection` and evidence origin (controlled synthetic versus operational
observed) must both remain visible. Exact feature parity cannot validate a model's
transfer to a new source population.

## Live data compatibility: 2026-10-14

Bounded JSON-2 reads at **20:11:38 UTC / 22:11:38 Europe/Budapest** used the existing
`procurement_poc` database. The quotation identity returned HTTP 200. The existing
production history adapter returned **HTTP 401** with the dedicated history key.
No administrator key, direct inventory read or alternative history identity was used.

| Check | Controlled planning fixture | Existing T7 fixture | Assessment |
| --- | --- | --- | --- |
| Company | `odoo:res.company:1` | `odoo:res.company:1` | Matches live |
| Supplier commercial IDs | 51 / 52 / 53; each equals its commercial partner | 55; commercial partner 55 | Does not match live |
| Product | `odoo:product.product:54` | `odoo:product.product:57` | Does not match live |
| Unit | `odoo:uom.uom:1` (Units) | `odoo:uom.uom:1` | Matches live; no conversion |
| PO/line IDs | group 2; draft orders 16/17/18; lines 28/29/30 | confirmed orders 19/20/21/22; lines 31/32/33/34 | Exact disjoint identities live |
| Prices/currency | 10 / 12 / 9; USD currency ID 1 | Not ML features | Quotation quantities are 100, not approved demand |
| Matching confirmed orders | none returned for exact company 1/vendor IDs 51/52/53, limit 11 | Four exact T7 origin markers found | No eligible matching fixture history established |
| Eligible line support | No matching completed obligations established | Historical accepted KPI: n=3, value 33.33%, one return exclusion | T7 KPI/support not refreshed because 401 |
| Schedule timestamps | all three RFQ lines `2026-09-19 09:49:28` | line 31 `2026-09-21 21:00:22`; 32 `2026-09-18 22:00:58`; 33 `2026-09-18 22:00:45`; 34 `2026-09-21 21:00:33` | Current schedule fields live; not immutable prior schedule versions |
| Receipt completion/backorder/return timestamps | none established | not returned in this run | Blocked by dedicated-key authentication |
| Capture/as-of availability | current read timestamp | current read would follow history window end | Old event dates cannot prove prior knowledge |

The confirmed-order query was scoped to the three exact direct vendor IDs. It was
not a global history scan and does not establish absence of child-vendor records,
other company/product history or externally available data. Names and origin
markers located the controlled fixtures; stable IDs/commercial identities determine
whether records can be joined. Never attach supplier 55/product 57 to 51/52/53/product 54.

Historical n=3/33.33% comes from [T7 handoff](T7_HANDOFF.md), [T8 handoff](T8_HANDOFF.md)
and the preserved security/KPI rerun in [T7S handoff](T7S_HANDOFF.md), not today's
projection read. The 2026-10-07 absence finding in
[T15 compatibility plan](T15_ODOO_COMPATIBILITY_PLAN.md) is now corroborated for the
same exact vendor IDs by today's bounded query.

Local probe evidence: `.artifacts/odoo-history-assessment/live-probe-via-tunnel.jsonl`,
SHA-256 `c076aa881655de0489c6863f921c582191990504faa40099df908b0929c2cc66`.
It is ignored local evidence, not a published artifact or a new business fixture.
Initial host reads failed. The existing machine was running, its Odoo/db containers
were stopped; these two existing containers were temporarily started. VM HTTP
returned 303 while Windows forwarding failed. A temporary localhost-only SSH tunnel
enabled the successful reads. The tunnel was closed and those two containers stopped
afterward; the pre-existing helper test database/machine/volumes were retained.
No procurement-data write method was invoked; normal Odoo startup is not a forensic
guarantee that its own background processes performed no internal housekeeping.

An existing local hybrid manifest was inspected as JSON, without deserializing or
training the model: `.artifacts/t15-odoo-demo/model/manifest.json`. It explicitly
records `source_type=t14_synthetic`, domain company 1/product 54/unit 1,
model ID `6a982edc068f77784ed3045812fafe72e52c81eb8d10c1fed9734b2f2e6c43d7`,
160 training rows and class support 43/117. Its feature, label and mapping versions
remain the T14 synthetic ones; `trained_through=2026-01-31T00:00:00+00:00`,
Python 3.11/scikit-learn 1.8.0. This does not verify which artifact a running
server is configured to load, its current bytes/runtime, or Odoo-source validity.
The prepared request and [T18 live record](T18_27_LIVE_VALIDATION.json) explicitly
use generated `H:*` histories assigned to quotation suppliers; they are not stock receipts.

## Decision and Odoo test-data prerequisites

| Decision scope | Outcome | Required condition |
| --- | --- | --- |
| Reuse guarded projection and neutral KPI for a bounded readiness export | GO WITH CONDITIONS | Renew dedicated key; prove exact context and complete bounded evidence |
| Attach current T7 records to current planning suppliers | NO-GO | Supplier and product differ |
| Feed Odoo-derived features into the current synthetic artifact | NO-GO | No audited source/model compatibility; existing guards intentionally reject it |
| Later controlled Odoo-history-to-V2 demonstration | GO WITH CONDITIONS | Matching explicitly labeled data, valid cutoffs, independently evaluated compatible artifact, all saved consumers/regressions pass |
| Claim observed commercial predictive validity | NO-GO on present evidence | Requires operational data, credible as-of/outcomes and adequate held-out evaluation |

**Matching Odoo test-history preparation is necessary for a controlled demonstration
using the currently verified fixtures, unless a subsequent authorized bounded read
finds suitable existing history.** It is not necessary merely to produce the
readiness report, which may correctly report insufficient/mismatched evidence.
Nine completed eligible lines (at least three per runtime supplier) would satisfy
only the minimum feature-support gate; they do not form a sufficient training or
holdout dataset and do not guarantee a meaningful plan alternative.

The following are proposed prerequisites for a separate, expressly authorized
human preparation phase, not actions to execute during this assessment:

1. **Separate test environment and recovery:** a human administrator selects a
   dedicated Odoo 19 test database (or explicitly approved existing test database),
   verifies its name/company, takes a fresh database/filestore backup and records
   the restoration procedure. Reuse the existing Podman machine; do not reset
   current Odoo or helper databases or delete volumes. A dedicated database has its
   own IDs: re-resolve and approve its exact quotation/history mapping rather than
   copying IDs 51/52/53/54 blindly.
2. **Restore the current read gate first:** follow
   [T7S manual setup, section 5](T7S_MANUAL_SETUP.md#5-generate-the-dedicated-api-key).
   Admin: **Settings > General Settings > Permissions > API Keys**, temporarily
   enable **Customers can generate API Keys**, **Save**. Dedicated portal user:
   `/my/security?debug=1` > **Developer API Keys > New API Key**, description
   `T7-S local projection validation`, **1 Day**, confirm, copy locally. Admin
   disables the temporary setting and saves. Set only `ODOO_T7S_API_KEY` in ignored
   `.env`; leave the RFQ key/groups unchanged. Human confirmation and passing
   bounded-read/direct-stock-denial security contracts precede receipt preparation.
3. **Freeze the fixture manifest:** record test-origin label/reference, exact
   company/product/Units/commercial suppliers, quotation group, future purchase
   line IDs, administrator preparation timestamp, window/cutoff and required
   scenarios. Keep existing T7 regression markers/records untouched. Use distinct
   proposed markers such as `V2-HIST-A-001` through `V2-HIST-C-003`; check duplicates
   through **Purchase > Orders > Purchase Orders > Source Document** before creation.
4. **Prepare matching obligations manually:** **Purchase > Orders > Requests for
   Quotation > New**. Select the manifest's exact **Vendor**, **Company**, **Product**,
   **Quantity 100**, **Unit Units**, explicit test price, **Discount 0**, no taxes,
   distinct **Source Document** and line **Expected Arrival**. Save/reopen/verify,
   then **Confirm Order > Receive**. For a same-day synthetic receipt date D in
   Europe/Budapest, the existing validated procedure uses `D+1 day 23:00` for on
   schedule and `D-1 day 00:00` for late. These are controlled test schedules,
   not claims of supplier promises. Exact proposed scenario counts/times must be
   frozen before the later preparation starts.
5. **Include edge cases without replacing support:** process quantity **100** and
   **Validate** for complete lines. For the late-backorder case process **40**,
   **Validate > Create Backorder**, then process **60** and **Validate** on its
   explicit backorder. Include separately marked return/incomplete cases using
   [the validated T7 procedure](T7_FIXTURE_SETUP.md); exclude return lines from the
   eligible count and retain warnings. Do not silently alter existing done transfers
   or backdate database fields. Refund/return/replacement semantics outside the
   supported projection subset stay rejected.
6. **Confirm postconditions through runtime reads:** human completion is followed
   by dedicated bounded projection checks, exact raw context joins, completion
   sums/times, sample counts/exclusions and source-origin capture. No admin runtime
   key, broad Inventory/Purchase role, fixture automation or direct DB reads.
   Rollback is restoration of the dedicated backup, not deletion of done transfers.
7. **Separate model evidence:** freeze an independently adequate offline training
   and evaluation dataset. Three planning suppliers and same-day test receipts
   cannot satisfy current supplier-disjoint temporal evaluation by themselves.
   Newly created synthetic Odoo history stays synthetic even when transport works.

If step 2 cannot be completed, data acquisition stays blocked; do not widen rights
or reinterpret the 401 as empty history. The exact receipt timestamps/KPI remain
unverified until a later successful read.

## Current executable flow

1. Offline `supplier_evaluation/dataset.py` constructs synthetic receipts, separates
   prior history from future labels, and fits one fixed Decision Tree. Exported
   manifest and joblib remain owner-configured local artifacts.
2. V2 `POST /planning-cases` receives controlled synthetic history. Its
   `PlanningCreateRequest.source_type` is literally `t14_synthetic`
   (`backend/app/planning_case_schemas.py:122`).
3. `POST /planning-cases/from-odoo` independently rereads quotations and currency,
   checks caller expectations and retains the separately supplied synthetic history.
   `backend/app/dependencies.py:131-152` reads comparison/currency only; it never calls
   the existing history reader. `application/odoo_planning_input.py:222-289` retains
   receipts and their synthetic attribution while replacing quotation facts and the
   application cutoff.
4. `assemble_planning_input` prepares synthetic features; `infer_planning_features`
   loads the trusted artifact and performs inference without fitting.
   `risk_inputs` passes scalar exposure coefficients and applicability references
   to unchanged ERP-neutral MILP code. Immutable snapshots store facts, model
   manifest, assessments, provenance, requests and results.
5. Exact replay occurs before source/model/solver acquisition. Scenarios consume
   stored original-base assessments. Retrieval, finalization and PDF use stored
   evidence. Sources: `application/planning_cases.py:308-409`,
   `backend/app/dependencies.py:76-100`,
   `supplier_evaluation/planning_bridge.py:12-73`.

Separately, T8 already reads Odoo through `get_historical_performance_reader`
(`backend/app/dependencies.py:35-41`), the bounded neutral port and calculator. That
route has not been composed into the V2 model flow. The current V2 input kind and
idempotent operation are explicitly `odoo_quotations_synthetic_history`
(`application/planning_cases.py:344,383`).

## Exact reusable components and compatibility gaps

| Component | Available behavior | Remaining gap |
| --- | --- | --- |
| `OdooHistoricalPerformanceReader` | Exact company and purchase-line IDs; bounded JSON-2 projection; response/schema/window/supplier checks; stable prefixed IDs; UTC timestamps; `odoo_projection` attribution | No per-record historical availability or prior revision timestamp; no arbitrary line discovery; product/unit must be checked before aggregation |
| `HistoricalPerformanceQuery` | Exact 365-day half-open window; at most 50 explicit line IDs and 200 results | Query itself has no selected product/unit fields; IDs must be established explicitly |
| Neutral raw snapshot | Company/supplier/product/unit, line/event/transfer IDs, ordered/completed quantities, expected/completed times and returns/backorders | Acquisition timestamp means current read time, not knowledge at an older cutoff |
| T8 KPI calculator | Full cumulative completion per line; on-time against Expected Arrival; line-count weighting; two-decimal percentage; minimum three eligible lines; warnings/withheld states | Aggregate drops company/product/unit/raw membership and does not constitute a training dataset or labels |
| `from_sourced_history` | Preserves typed KPI value/support/source into `FeatureSnapshot`; requires usable matching supplier | Caller must prove company/product/unit and historical as-of evidence; the helper does not perform that proof or authorize model use |
| T14 feature contract | Exact ordered two features, finite percent and integer support; canonical float32 inference; explicit context/cutoff | Existing inference is synthetic-only; feature equality is necessary but insufficient |
| T14 split/training/artifact | Purged temporal split, supplier groups disjoint, unique receipt IDs, fixed tree, hashes, trusted load, exact runtime compatibility | Synthetic source/dataset/label/mapping versions are hardcoded; new-source training and promotion need an explicit versioned contract |
| ML-to-MILP bridge | Exact complete supplier join; common company/product/unit; same model/training; time/range validity; no zero-risk fallback | Its mapping/validity references explicitly describe a controlled quantity-independent proxy; observed applicability must be justified |
| Immutable storage and HTTP orchestration | Acquisition after replay lock; stored-only replay/GET/scenario; current routes and own PostgreSQL | Source/input-kind/finalization/UI validators assume synthetic history; widening only inference would leave saved cases unreadable or unapprovable |

Source anchors:
`odoo_adapter/historical_performance_reader.py:71-177,180-217`;
`application/historical_performance.py:66-148,259-399`;
`supplier_evaluation/history.py:19-106`;
`supplier_evaluation/contracts.py:45-123`.

### Deliberate synthetic-only and downstream guards

These are scope/trust gates, not bugs to remove:

- Synthetic unit receipt construction: `supplier_evaluation/history.py:55-56`.
- Synthetic planning assembly: `application/planning_input.py:63-64`.
- Synthetic training split: `supplier_evaluation/dataset.py:100`.
- Synthetic artifact envelope and training output:
  `supplier_evaluation/model.py:68,249`; observed inference rejected at `169-173`.
- Saved approval evidence checks source and versions:
  `application/planning_decisions.py:113-132,173-200`.
- Library and catalog source validation:
  `application/planning_library.py:90-98`, `application/planning_catalog.py:35-39`.
- Frontend response parsing rejects non-synthetic assessments and expects the
  current Odoo input kind:
  `frontend/planning_client.py:129,298-301,598-615`; library labels likewise assume
  the two existing kinds (`frontend/planning_library_client.py:72-74`).
- Current generated PDF describes synthetic exposure and assessments:
  `document_adapter/approved_pdf.py:111-112,153`. Component copy and acknowledgments
  also assume synthetic evidence throughout `frontend/planning/`.

An implementation must review callers, schemas, snapshot reconstruction,
finalization, catalog/library, HTTP clients, audit/approval/PDF copy, demo/evaluation
tools and affected fixtures/tests together. It should keep old snapshots and
synthetic practice behavior valid. Merely replacing the source string with
`t14_synthetic` would falsify provenance.

## Temporal, feature and target requirements

The two features are exactly `delivery_schedule_adherence` and
`historical_completed_count` in that order. T14 accepts adherence [0,100] and an
integer eligible completed-line count [3,50], not raw event count. Missing or
withheld evidence fails closed. Product/unit/company/supplier membership must be
checked on raw observations before T8 aggregation because the KPI aggregate only
identifies supplier. No new feature, imputation, scaling, or quantity feature is
needed merely to integrate the existing history source.

`FeatureSnapshot` requires an exact 365-day window, explicit UTC timestamps,
`history_end <= evidence_available_at <= cutoff`, and history end at most seven
days before cutoff (`supplier_evaluation/contracts.py:103-123`). T14 synthetic
history requires every completion strictly before cutoff and availability no later
than cutoff (`supplier_evaluation/history.py:65-72`). An old completion timestamp
in a newly read record cannot prove the record or its current Expected Arrival was
known then. T7S's strict returned schema has no `available_at` or versioned prior
Expected Arrival; its `observed_at` is the post-request UTC clock
(`odoo_adapter/historical_performance_reader.py:30-49,121-133`).

For current-time inference, a read followed by an application cutoff can satisfy
read-time availability: choose the half-open window end before the read and cutoff
after it, without extending the window or claiming prior knowledge. This still
requires context and model validity and can involve several sequential reads; it
does not create an atomic historical snapshot across calls. For backtesting,
preserve a capture at each actual cutoff and subsequently collect outcomes, or
use trustworthy external versioned as-of evidence. Do not invent availability from
completion time or backdate newly entered test records. A frozen controlled fixture
can explicitly define a simulated clock, but its result remains synthetic.

Current target v1 is at least two late lines among exactly five future completed
lines in the following 30 days. Expected Arrival and completion must both lie
strictly after cutoff and at/before cutoff+30 days. All outcomes must be available
by extraction; the full label window must have elapsed. Sources:
`supplier_evaluation/dataset.py:119-135` and `docs/T14_ML_DESIGN.md`.

This target is feasible only for observations satisfying that exact eligibility.
It is not a general target for arbitrary Odoo history. A completed-event projection
alone cannot establish all outstanding obligations or a missing future receipt.
Selecting only five completed outcomes after looking at the results risks selection
bias; sampling/eligibility must be defined before outcomes are inspected. Open,
cancelled, partial, returned and late-beyond-window obligations require explicit
exclusions and coverage reporting under the current target. A different target
would require a separate version and accepted decision, not an implicit conversion.
Mutable Expected Arrival further requires its value at the relevant historical
time to avoid retrospective schedule leakage.

## Training, evaluation and model-validity gates

The existing dataset requires one company/product/unit domain, supplier groups
disjoint across train and holdout, unique observation/context-cutoff identities,
and globally unique history/outcome line IDs. Training labels must be available
strictly before the split boundary; held-out cutoffs must be on/after it
(`supplier_evaluation/dataset.py:65-109,138-166`). Repeated supplier cutoffs that reuse
the same receipt history are therefore incompatible with the current dataset
contract. Do not quietly permit reuse to manufacture enough rows.

The fixed tree requires at least 20 training examples of each class and leaf
support at least ten; max depth three, min split support twenty, seed seventeen,
and no held-out tuning (`supplier_evaluation/model.py:34-43,120-160,223-260`). Three
runtime suppliers with three eligible lines each meet neither training support nor
held-out design. The shipped 160/80 split and 240 suppliers are a generator design,
not a universal minimum; the explicit class/group/time gates are the actual
compatibility constraints. Reducing them to fit a small fixture needs scientific
justification and is outside this assessment.

A promoted artifact must record the new dataset/export identity, exact feature
semantics/order, label/sampling policy, training provenance, extraction/cutoffs,
split and class support, company/product/unit domain, source compatibility and
time/quantity applicability. Source transport and evidence origin must remain
separate: `odoo_projection` identifies retrieval, while a dedicated Odoo test
dataset is still controlled synthetic evidence. Do not treat either label as a
proof of real-world quality.

Keep fit offline; fit/preprocessing/tuning never use held-out data. Report confusion
matrix, per-class precision/recall/F1/support, macro metrics, undefined metrics,
coverage/exclusion counts, reproducible hashes and a simple baseline. Small or
single-class held-out sets must retain their limitations. The existing evaluator
matches the training digest and explicitly disclaims real-world validity
(`supplier_evaluation/evaluation.py:75-101`). For a new source, equal metrics on
synthetic data do not establish transfer validity.

Retain trusted-local artifact loading, pre-deserialization manifest/runtime and
SHA checks, verified-byte loading and post-load semantic/leaf validation
(`supplier_evaluation/artifacts.py:26-46`). Runtime inference must match an
explicitly supported source/domain and occur no earlier than all training labels
were available. A checksum proves consistency, not authenticity or predictive
validity. The exact scikit-learn/Python/numerical runtime remains part of the model
contract.

The leaf class-1 fraction is an uncalibrated schedule-watch exposure proxy, not
failure probability. Its explicit quantity independence and 30-day validity are
definitions in the controlled demonstration, not empirically validated Odoo
delivery guarantees. Retain that distinction, exact supplier joins/range coverage,
and no zero-risk fallback. The MILP continues to consume validated coefficients;
no ML library or Odoo logic should enter Decision Core or the solver.

Primary external references checked on 2026-10-14:
[Odoo 19 JSON-2 documentation](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
describes standard Odoo security and a separate transaction for each API call;
therefore separate quotation/history reads must not be claimed as one atomic ERP snapshot.
[scikit-learn 1.8 leakage and preprocessing guidance](https://scikit-learn.org/1.8/common_pitfalls.html)
supports keeping fitting/model choices inside training data and applying the same
feature transformation to inference;
[scikit-learn 1.8 persistence documentation](https://scikit-learn.org/1.8/model_persistence.html)
supports the trusted-artifact and matched-environment constraints. Applicability to
this project's data and promotion gates is an assessment judgment.

## Proposed one small increment

**Capability:** for one existing controlled quotation group, show whether exact
bounded Odoo history can supply the current two features for every selected
supplier, with explicit exclusions and evidence gaps.

Reuse the existing adapter/neutral snapshot/calculator. Accept an owner-approved
static company/product/unit/supplier/line manifest; do not add arbitrary discovery.
Produce an offline immutable export and readiness report with UTC capture/window,
raw membership, KPI/support/warnings, stable source identifiers and hashes. Keep
the existing runtime model/source gates and planning APIs unchanged. No training,
new database schema, generic history API, ML framework, scheduler, dashboard
redesign, or Odoo writes are needed for this increment.

Acceptance example: a buyer's three controlled suppliers are joined to their exact
company/product/unit history; each feature is either an independently verified
usable value with evidence or a precise withheld/blocking reason. A report must
say whether each record is test-generated, operational, or unverified, and whether
training labels/as-of evidence exist. It must never return an invented score.

If data-readiness passes, a subsequent runtime connection can reuse `/from-odoo`
and current storage/ML-to-MILP ports, while adding a bounded history selection and
versioned compatible model/evidence path. It must change source validators and
consumers coherently, preserve old synthetic snapshots/practice, acquire new
history only after idempotency lookup/locking, and save exact facts/features/model
references once. A database migration is not inherently necessary for JSON
snapshots; their software contract still needs explicit version compatibility.

## Required acceptance tests for future authorized implementation

| Area | Evidence required |
| --- | --- |
| Context/read bounds | Wrong company/supplier/product/unit or unrequested lines rejected before aggregation; stable commercial-partner mapping; 50-line/200-event limits; overflow/error response fails closed |
| KPI parity | Same T8 completion/partial/backorder/overreceipt/return/missing-schedule semantics; exact expected-arrival equality; eligible-line support rather than event count; minimum support withheld |
| Cutoff/leakage | UTC only; exact 365-day half-open boundaries; future/late-available records rejected; altered retrospective schedule cannot rewrite captured evidence; delayed acquisition cutoff checked |
| Label coverage | Five contextual outcomes and full 30-day observability; late/outstanding/returned/cancelled exclusions explicit; no outcome-conditioned sampling; history/target separation |
| Split/training | No reused evidence/context-cutoff or cross-partition suppliers; purged label windows; held-out changes never alter fitted model; support gates remain meaningful; no runtime fit |
| Artifact/source | Synthetic model rejects Odoo source; test Odoo data cannot masquerade as operational history; compatible model/source/domain required; trust/hash/runtime/version/config/leaf corruption rejected before use |
| MILP regression | Exact complete supplier join; same model/training and time/quantity validity; no implicit zero score; unchanged cost/constraint solver behavior; class and exposure semantics separate |
| Storage/API regression | Existing V1/V2 synthetic cases read/finalize/PDF unchanged; exact replay and GET/scenarios work after Odoo/model removal; concurrent creation acquires once; stored content/hash cannot change |
| Browser/E2E | Source/origin/model limitations visible in plans, supplier explanations, audit, library, approval and PDF; backend unavailable and insufficient history fail clearly; full new creation through scenarios, finalization and stored PDF with sources subsequently disabled |

Existing test anchors worth extending, not replacing:
`tests/test_t14_dataset.py:54-159,176-239`;
`tests/test_t14_model.py:27-79,122-176`;
`tests/test_t15_odoo_planning.py:85-105`;
T15 persistence/replay, T17 decision and document, library/catalog and browser suites.
No training tests or new tests were run during this assessment.

## Architecture, schedule and thesis consequences

The proposal deepens the existing controlled-history dependency without changing
the official assignment, five CORE functions, offline-training boundary,
read-only runtime, ERP-neutral core, API-only frontend, immutable snapshots or
human approval. It is a source integration and evidence-validity extension, not a
system redesign.

Schedule it as readiness -> any manually authorized dedicated-test-data preparation
-> capture/label observation and offline evaluation -> explicitly compatible
runtime connection -> regression/E2E acceptance. Data permissions, historical
availability and the 30-day future label window can dominate elapsed time. Past
timestamps on newly entered data do not remove that scientific dependency.
Controlled simulated chronology can shorten an integration demonstration but
cannot establish real historical availability or operational predictive validity.

Use rolling-wave checkpoints, not a promised completion date: credential renewal
and manifest/data readiness first; manually approved test-data preparation if
needed; offline dataset/model compatibility next; one fixed-group runtime slice
and its downstream regressions last. Genuine newly captured future labels require
at least the complete 30-day outcome window, plus extraction/evaluation time.
The current synthetic baseline's accepted results remain valid in their original
scope. Do not let an unbounded observed-model project replace the already required
current-source Odoo-to-PDF reproduction or parallel thesis writing. This assessment
adds no new thesis acceptance requirement or deadline.

Thesis evidence should distinguish projection correctness, KPI parity, controlled
integration and empirical predictive validity. Relevant chapters are ERP/data
handling (3), architecture (4), algorithms/ML-to-MILP mapping (5), implementation
(6), evaluation/limitations (7) and further development (8/9). Record problem ->
decision -> implemented behavior -> evidence -> limitation with exact source and
model identities. This research note establishes compatibility gaps; it does not
claim an observed model, validated business benefit, or completed new acceptance.

## Renewed-key readiness update — 2026-10-14

After the owner renewed the dedicated key and saved it locally, the guarded
projection returned HTTP 200 with six events. The two existing focused live
contracts passed: **2 passed in 2.11 s**, Python 3.11.16. They prove bounded
same-company projection access, denied generic CRUD/direct stock reads,
cross-company/invalid-bound rejection, and the production T8 adapter/calculator
flow. A pytest cache-write permission warning did not affect either assertion;
passing checks were not rerun merely to remove that warning.

Current production capture at `2026-10-14T21:02:42.197053+00:00` independently
confirms company 1/supplier 55/product 57/UoM 1, lines 31–34, six stock-move
events, **delivery_schedule_adherence 33.33%, eligible sample size 3**, and
`supplier_return_observed` excluding line 34. Receipt completion times are
2026-09-20 11:20:16 through 11:37:41 UTC. Line 33 completes across 40+60 receipts;
line 34 has its explicit 20-unit supplier return. Thus the earlier authentication
blocker is resolved; the original 401 evidence above remains historical.

A bounded partner query (`commercial_partner_id in [51,52,53]`, limit 31)
returned only IDs 51/52/53, so no child contacts were present in that scoped
result. A fresh company-1 confirmed-order query for those exact vendors returned
no records (limit 11). Matching planning history is still absent in the checked
fixture, and the supplier/product mismatch remains. Access is ready for the
assessment; data/model readiness for a direct V2 connection remains **NO-GO**.
Conditional matching test-data preparation and compatible offline artifact
validation remain separate next phases, not enabled by a successful key check.

Raw local capture: `.artifacts/odoo-history-key-refresh/live-readiness.jsonl`,
SHA-256 `188eb63b22bef1344a96acb52a0c3374cc78e2bdfae8b5f5e505ad2c6579745a`.
Live test flags were process-only; `.env` was not edited by the agent. The Odoo
containers and existing forwarding were already running at this update's start
and were left running. No fixture, model, runtime code, schema, requirements,
Drive/tracker or Git publication changes were made; no training/E2E was run.
