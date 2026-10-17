# Live Odoo history integration

## Frozen compatibility protocol — 2026-10-16

User authorized the existing local Odoo case, saved-tree evaluation first, no
automatic retraining. This protocol is recorded before evaluating the candidate.
The fixture remains controlled synthetic; this is not operational predictive validation.

- Candidate: `.artifacts/t15-odoo-demo/model`, original fitted bytes and manifest
  preserved; require trusted artifact integrity, Python 3.11 runtime and exact
  company/product/unit domain 1/54/1.
- Reconstruct the original seed-17 dataset in memory and reproduce its held-out
  results with the existing evaluator, requiring its training identity to match.
  Do not call training, change a feature/label definition or use Odoo fixture lines.
- Independent evaluation: seed **18**, two cohorts of **240** unique supplier
  contexts each. First cohort has exactly three historical lines per context;
  second cycles history counts 3 through 30. Use the existing generator's declared
  past-miss distribution and conditional future-miss mechanism, five outcome
  completions and existing next-30-day label rule. Cutoff 2026-05-01 UTC, extraction
  2026-06-01 UTC. Context and receipt identifiers are disjoint from original data.
- Before prediction, verify no reused evidence/context, exact feature schema,
  history/outcome separation, label availability and cutoff after training.
- For each cohort require both classes with at least **20** true examples,
  accuracy >= majority-class accuracy and macro-F1 > majority-class macro-F1.
  Report confusion matrix, precision/recall/F1/support and prediction hashes.
- GO requires all checks, including the independent n=3 cohort. Qualified support
  is 3–30 completed lines; company/product/unit and controlled-synthetic origin
  stay restricted. Score remains an uncalibrated quantity-independent proxy.
- Freeze protocol/report hashes. On failure: preserve report, no artifact promotion,
  no automatic retraining, no relabelling live input and no weakened acceptance gate.

Implementation traceability: FR-V2-01/02/03/07/08/09/10/11/12;
AC-V2-01/02/03/08/09/10/11/12/13;
NFR-V2-02/03/04/08. All five CORE functions and read-only runtime remain unchanged.

## Implemented behavior

Problem: the existing V2 quotation path used separately generated receipt vectors,
although the owner had completed matching controlled receipts in a neutralized copy.
Decision: add one opt-in fixed profile and qualify the existing saved tree offline;
preserve the original synthetic workflow and its artifact bytes.

```text
restricted Odoo quotations + guarded exact receipt projection
 -> raw identity/backorder validation -> unchanged T8 KPI -> T14 features
 -> qualified saved tree -> existing risk contract -> unchanged MILP
 -> immutable case -> stored scenarios / human approval / saved PDF
```

- `config/odoo_history_local_v1.json` pins database, company/product/unit/currency,
  group, three quotation order/line/supplier identities and all nine historical
  order/line/event identities. It retains A01's accepted +46-second schedule
  deviation and B03's 40 + 60 backorder chain. Old T7 supplier/product history is
  excluded. Profile content is hashed; stale caller revisions reject new creation.
- `odoo_adapter/planning_history_reader.py` reuses the quotation reader and guarded
  historical projection with separate restricted keys. Exact context, quantities,
  schedules, origin markers, events and return/backorder relationships are checked
  before aggregation; no generic stock access, discovery or Odoo writes.
- `application/planning_history.py` reuses T8 and feature conversion with one
  365-day UTC window, individual acquisition times and a server-generated cutoff
  after acquisition. The capture retains raw evidence, profile, origin, KPIs,
  features and integrity hashes. Field provenance uses actual history acquisition
  times rather than earlier business-term entry times.
- `supplier_evaluation/odoo_compatibility.py` evaluates without fitting.
  `qualified_odoo.py` retains original synthetic training provenance and verifies
  candidate/report/package integrity, runtime, feature schema, domain, source,
  origin, support and quantity applicability. Legacy inference still rejects this
  new source; only the explicit qualified path accepts it.
- The existing backend composition root owns the reader/model configuration.
  The preview and `/from-odoo-history` routes use existing authentication, request
  limits and idempotency locking. Caller input contains business terms and
  quotation expectations, never history vectors, artifact paths or credentials.
- Reflex adds **Use history from Odoo** in the existing form, with actual KPI values,
  sample support and model readiness. Saving reacquires both sources; saved supplier
  assessments, audit, scenarios, library, approval and PDF use recorded evidence.
  Specific profile/source/model errors have no fabricated fallback scores.

### Stored compatibility

Keep the existing `t15-controlled-planning-v1` SQL container and legacy serializers:
the current database constraint pins that container. Version the new nested capture
as `bounded-odoo-history-capture-v1`, discriminate by
`facts.input_kind=odoo_quotations_odoo_history`, and use separate qualified artifact
and exposure-mapping versions. All consumers validate that combination together.
Old snapshots/JSON hashes remain unchanged; there is no SQL migration or owner
database rewrite. Reopening validates stored contracts without KPI recomputation,
model deserialization, Odoo access, inference or reoptimization. Scenarios solve
only from saved original-base facts/assessments, using the existing MILP.

## Offline compatibility decision: GO for the declared controlled domain

| Evaluation | Examples | True class support 0 / 1 | Accuracy | Majority accuracy | Macro-F1 | Majority macro-F1 |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Original held-out reproduction | 80 | 24 / 56 | 0.9875 | — | 0.98494 | — |
| Independent n=3 | 240 | 90 / 150 | 0.9500 | 0.6250 | 0.94690 | 0.38462 |
| Independent support 3–30 | 240 | 64 / 176 | 0.94583 | 0.73333 | 0.92654 | 0.42308 |

Both independent cohorts pass the predeclared criteria with disjoint supplier and
receipt identities and unchanged feature/label definitions. No tuning, fitting,
retraining or use of the nine fixture lines as training/evaluation examples.
The 480 generated evaluation contexts reproduce the declared synthetic mechanism;
this is restricted compatibility evidence, not external operational validation.
The sample count is not empirical evidence of quantity-dependent delivery risk.

Local immutable evidence (ignored, not published):

- Candidate `.artifacts/t15-odoo-demo/model`: tree SHA-256
  `d94a1c50576c45d0b852ed4fdcfefa590ed85cbd6201e491c830d21938cb818a`;
  original model ID `6a982edc068f77784ed3045812fafe72e52c81eb8d10c1fed9734b2f2e6c43d7`.
- `.artifacts/v2-odoo-history-integration/compatibility-evaluation.json`: report hash
  `576adafa322b8a007a143ebc390cf78ec1d77e3f70072d2ab6e7b53e75a7f744`;
  per-class metrics, confusion matrices, dataset/prediction hashes and runtime.
- `.artifacts/v2-odoo-history-integration/qualified-model`: separate qualified model
  `e09600ab347899f37341347994ec20fca5ee67981783a0a938f6f1f281495280`;
  company/product/unit 1/54/1, test-copy/local-v1, controlled synthetic origin,
  support 3–30, quantity validity 1–1000. Candidate files are copied unchanged.

Reproduce evaluation only as an explicitly new run, to a new output path:

```powershell
python -m supplier_evaluation.odoo_compatibility --candidate .artifacts/t15-odoo-demo/model --output .artifacts/new-compatibility-run/report.json
```

This command does not train or overwrite evidence. A fresh checkout requires the
trusted candidate/package to be supplied by the owner; runtime never trains one.

## Verification and remaining boundaries

Focused tests cover source/context/quantity/backorder failures, temporal/support
and provenance integrity, package corruption before deserialization, qualification
NO-GO, rejected browser vectors, rollback, actual tree/CBC, explicit error handling
and stored lifecycle/replay. Existing architecture tests remain unchanged; their
initial failure was resolved by keeping composition in `backend/app/dependencies.py`.
The original full-suite failure and corrected runs are retained under the ignored
integration artifacts. Windows sandbox pytest stalled; only owned test processes
were stopped before the successful unsandboxed rerun. No credential failure or
renewal occurred. An initial browser setup lacked the Compose provider; subsequent
runs used the existing environment's `podman-compose.exe` and cleaned up successfully.

Live browser acceptance uses real restricted local Odoo reads, actual saved tree,
CBC, disposable helper PostgreSQL and Reflex. It verifies 100.00/66.67/33.33%, n=3
each, one B03 line despite two receipt events; creation, supplier evaluation,
scenario, deliberate approval and PDF. The actual tree produces A/B/C classes
0/1/1, scores 0/0.9661/1; minimum USD 1,850 allocates 50/0/150. A's zero is the
recorded fitted-leaf result, not an unavailable-history fallback. New-case
source/model failures save nothing.

The harness then restarts only its own API with Odoo URL unreachable, all Odoo
keys and model-directory configuration empty. Stored reopening, exact POST replay
(same identity/hash), library listing and byte-identical PDF retrieval succeed.
The owner Odoo service is never stopped. PDFs retain database/origin/cutoff/hash,
actual feature values/support and synthetic training provenance; all six rendered
pages were visually inspected. Detailed run identifiers and final check counts
are recorded below after execution.

Use the [startup/run instructions](LOCAL_DEVELOPMENT_AND_SSH.md#controlled-odoo-history-path).
The ignored `.env.v2-history-runtime` is prepared; original configuration is
preserved. No owner helper database was changed by acceptance, and temporary
acceptance services are removed after each run. No commit, push, merge or Drive edit.

Limitations: this is one fixed controlled case, a multi-request API capture rather
than an atomic ERP-wide snapshot, and a synthetic-trained uncalibrated proxy.
Genuine operational history, arbitrary selection, model retraining/promotion for a
new domain and unfamiliar-buyer acceptance remain separate. No new infrastructure,
schema, CORE function or ML-to-MILP architecture is introduced. Thesis relevance:
chapters 4/6 explain acquisition/provenance and integration; chapters 5/7 report the
frozen compatibility protocol, leakage controls and controlled evidence; chapter 8
retains operational validity and broader sampling as limitations.

### Executed check record

- Full required fast suite: **702 passed, 76 deselected**, 191.51 seconds; actual
  CBC and ML runtime gates included. One existing Starlette/httpx deprecation
  warning. `.artifacts/v2-odoo-history-integration/fast-checks-final.log`.
- Final **26 focused checks passed**, 9.32 seconds, including the added
  raw-before-KPI ordering test and exact Decimal quantity comparisons after the
  full run. `.artifacts/v2-odoo-history-integration/focused-final.log`.
- Ruff format/lint, compilation, `pip check`, redacted Compose configuration and
  `git diff --check`: PASS. No dependency or schema changes.
- Real-stack browser: **1 passed in 107.52 seconds**;
  `.artifacts/t18-browser-dcffa826b0b6/evidence.json`. Technical case
  `fa0afd0f-0b22-4b10-9d73-e32a10b4459f`, snapshot hash
  `3a0c2f1d5d97d237d947f007b21978aaa32823398268b5b92280f68a16799c4a`,
  PDF SHA-256 `d4d1805deced02f7f6feedd9640915e97f4f129c95c690e3c025f7a0784b27f9`.
  Disposable test cases/database were removed; these UUIDs are evidence, not
  bookmarks in the owner's application database.
- Final read-only preview after the raw-validation refinement: `ready`, exact
  expected KPI/support, profile revision
  `84bcbe82e2c3f28416ef0c138bfed51893af91e35fe35847a8432a8935bc9571`;
  `.artifacts/v2-odoo-history-integration/live-preview-final.json`.
- Final retained raw capture `.artifacts/v2-odoo-history-integration/live-capture-final.json`
  has nine lines, ten events, original-candidate hash unchanged and actual qualified
  classes 0/1/1; capture hash
  `4f8b6ad90ee500e53320c0aca30f160aa58668b811d119c11e4e3a05cb527f7a`.
- Cleanup confirms only the two pre-existing owner Odoo/PostgreSQL containers
  remain running. Original model hash matches the frozen candidate. Branch
  `feature/odoo-data-integration`, baseline HEAD `71927ca`; changes remain local.

Not rerun: the entire optional integration/browser/UX matrix, hosted CI or new
mobile/assistive/novice assessment. The bounded live PostgreSQL/Chromium flow is
the executed integration scope. Owner-facing runtime services were not left
running; use the prepared runtime profile and existing helper database to start them.
