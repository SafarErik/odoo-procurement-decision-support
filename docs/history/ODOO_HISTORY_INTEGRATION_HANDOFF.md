# Live Odoo history integration

## Offline reproducibility check — 2026-10-17

Problem: Git excludes `.artifacts`; a checkout alone cannot restore the qualified
model or detailed local evidence. Decision: preserve a narrow offline demonstration
kit and check it in isolation, without retraining, changing live configuration or
copying private backups. This supports NFR-V2-02/03/04/08 and AC-V2-03/04/08/10/12/13
evidence; it does not replace full-stack or human acceptance.

Actual scope: committed source `080ff320c083ad90395fab7d8b9abf98343a2ea6` extracted
separately; a second empty CPython 3.11.16 environment on the same Windows x64 host;
51 dependency/build-tool wheels installed with `--isolated --no-index --require-hashes`;
source installed without build isolation or dependency resolution. The verifier
asserts imports come from that source, blocks fitting and Python network access,
and uses only copied controlled evidence. No Odoo/helper reads or writes occur.

Results:

- Exact frozen compatibility report hash `576adafa322b8a007a143ebc390cf78ec1d77e3f70072d2ab6e7b53e75a7f744`;
  reconstructing the qualification wrapper gives all three original package files
  byte for byte, with unchanged fitted bytes and qualified model identity.
- Raw captured receipts recalculate through T8 to 100.00/66.67/33.33%, support 3
  each; B03 has two events and one eligible line. Inference gives classes 0/1/1,
  scores 0.0000/0.9661/1.0000 and saved tree explanations.
- Eight technical snapshot hashes validate. Separate CBC calculations from each
  recorded request reproduce every saved minimum/alternative plan, including
  infeasibility. They do not overwrite or replace stored decisions. The existing
  saved PDF matches SHA-256 `2f09067f37b09a41740d2a925b9f627956620d2a0442191b9f0f12b237b98d30`.
- Missing/corrupt artifacts, insufficient support and unqualified origin reject;
  corrupt fitted bytes are rejected before deserialization. `pip check` passes;
  focused receipt/MILP/architecture tests: **69 passed in 8.78 seconds**.
- A 73-file allowlisted ZIP passes extraction/member checksum verification.
  Seven current long configured credentials were checked for exact-value matches
  in the payload and decompressed source; zero matches. This is a bounded scan,
  not a universal secret-detection guarantee. No `.env` files, Odoo/helper backups,
  installed environments or service logs are included.

Kit: `.artifacts/thesis-repro-20261017-c217b8ae/thesis-offline-demo-windows-py311.zip`,
114,149,566 bytes, SHA-256
`9b06bb647b34ea7713b44a7dd443a5d42d9856e9f73c61a2c2c8b136598769e9`.
It includes its README, pinned/hashes dependency lock, original wheels, committed
source archive, trusted model/capture/evaluation, technical matrix/PDF and final
check results. Detailed working diagnostics remain separately in that run directory.
See [repeat instructions](LOCAL_DEVELOPMENT_AND_SSH.md#offline-model-and-evidence-reproduction).
The archive and this external hash require an owner-controlled backup; Git alone
does not preserve ignored files. A checksum inside an untrusted package is not
authenticity; joblib requires trusted origin before execution.

Limits: no fresh OS/second machine/Linux, training rebuild, full fresh-stack suite,
Reflex/Node/browser deployment, live Odoo restoration/acquisition, HTTP/database
replay or fresh PDF rendering was checked. Python must be supplied separately;
the archived wheels are Windows x64/Python 3.11 specific. The broader application
dependencies have ranges in `pyproject.toml`; this kit pins the resolved versions
for this demonstration without changing application requirements. Use the source
checkout: a wheel-only installation does not include the profile/config and demo
tools. Historical cutoffs stay recorded, future live 365-day windows may expire,
and the model remains synthetic-trained with controlled-domain validity only.
Application code, runtime configuration, services, original artifact bytes and
pre-existing worktree changes are preserved. No Git publication or Drive edits.
Thesis relevance: chapters 5/7 can distinguish repeatable compatibility/inference
and optimization results from live acquisition and operational predictive validity;
chapters 6/8 record packaging and portability limits.

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

## Functional operation follow-up — 2026-10-17

Initial status before key renewal: **implemented functional extensions; live
completion blocked by restricted-reader credentials**. This blocker is resolved
in the completion record below. UX acceptance/redesign is deferred by the owner.
Traceability remains AC-V2-08/10/11/12/13, preserving all five CORE functions.

Problem: the prior acceptance database was disposable, while the normal owner
helper remained at `20261005_01` and lacked approval/PDF/catalog tables. Existing
Podman/Odoo/helper containers were stopped. Decision: restore those existing
services in place, preserve owner rows, apply only the already accepted additive
migrations, and reuse the existing HTTP-only demonstration for the new source.

Implemented and verified:

- Started `podman-machine-default` and the three existing containers; no machine,
  container, Odoo record or volume replacement. Existing helper storage is its
  original anonymous volume; preserve its container and volume. Windows reported
  the known proxy failure; owned localhost SSH tunnels restored 8069 and 55433.
- Captured helper-only `helper-before.dump` before any schema operation. Both the
  archive listing and a complete `pg_restore --file=/dev/null` read pass. No restore
  was performed against any database. Applied the existing three additive
  revisions through `20261012_01`; no new migration/schema design was added.
- Fingerprinted every pre-existing row: 36 planning cases, one V1 decision and
  one creation record. All remain unchanged after upgrade and actual helper/API
  restart. All 36 cases return HTTP 200 with identical snapshot hashes when API
  source/model configuration is disabled. No existing case was finalized.
- `tools.t17_demo run --odoo-history` acquires the fixed ready preview and reuses
  existing scenario/finalization/PDF/replay logic. It creates two new technical
  bases, five scenario types plus infeasible demand, alternative approval and a
  separate No-award; `reopen --report ...` verifies exact saved evidence. Intent is
  recorded before each POST; uncertain responses do not trigger automatic retry.
- New fast tests check reference scenario costs, unchanged saved assessments,
  alternative index, No-award PDF denial, IO-free exact replay, unready-source
  rejection and retained uncertain intents. The expanded Chromium test adds the
  same matrix and actual disposable helper/database restart before stored replay.
- Test-copy keys are database-specific after renewal. New server setting
  `ODOO_HISTORY_QUOTATION_API_KEY` isolates that reader from original
  `ODOO_API_KEY`; empty configuration fails closed without fallback. The projection
  still uses only its separate `ODOO_HISTORY_API_KEY`. No model/artifact changes.

Evidence directory: `.artifacts/odoo-history-functional-43457854b415/`.
`helper-upgrade.json`, `existing-row-hashes.json`, `existing-case-restart.json`,
`archive-check.json` and backup archive retain actual state/results. The normal
owner database has no new history cases: acquisition rejected before any POST.

Verification:

- Full fast suite: **706 passed, 76 deselected**, 253.90 seconds. One existing
  Starlette/httpx deprecation warning; `fast-checks.log` preserves the output.
- After adding credential separation: **34 focused checks passed**, including
  all history gates, full matrix, legacy demo and unchanged architecture checks.
- Ruff format/lint, compilation, `pip check`, redacted Compose configuration and
  whitespace checks pass. No dependency, fixture or fitted-artifact change.
- Live attempt: restricted quotation identity read **401** and independent exact
  three-line guarded projection **401**. The backend preview returns **503**;
  the browser displays unavailable history and creates no case. Expanded live
  browser result is **FAILED due to the authentication blocker**, not PASS or a
  skipped acceptance. `.artifacts/t18-browser-c927dbfbfd1c/evidence.json` records
  cleanup of its owned disposable services. Original 2026-10-16 PASS remains.

Initial manual prerequisite (subsequently met): in `procurement_v2_history_test_v1`, renew keys for the
existing restricted quotation reader uid 7 and method-only projection uid 8,
without changing permissions. Save both in ignored `.env.v2-history-test` as
`ODOO_API_KEY` and `ODOO_T7S_API_KEY`. Preserve original `.env`. After explicit owner
confirmation, map those values to the two dedicated runtime fields and restart
the API, then rerun only the blocked live gates. Never use an administrator key,
generic inventory read, fixture rewrite or model fallback to bypass this failure.

Remaining work at the first handoff (completed below): authenticated live matrix against the normal persistent helper;
expanded browser/database-restart acceptance; final runtime startup and preserved
technical-case bookmarks. No UX assessment, Git publication or Drive edit. The
completed upgrade/restart evidence is useful for thesis chapters 6/7; the live
authentication limitation must remain distinct from model compatibility and
operational predictive validity.

First handoff runtime state: the owned diagnostic API was stopped and port 8000 released,
with process-tree termination verified. The existing Odoo/helper containers and
owned localhost tunnels remain available for manual key renewal. No frontend is
left running. Original services/volumes and the verified helper backup are retained.

### Completed after owner key renewal — 2026-10-17

Owner confirmed both renewed test-copy keys. Non-mutating identity/ACL checks
verify quotation uid 7, history uid 8, neither a Settings administrator. Quotation
purchase-order permissions remain read=true, create/write/unlink=false. Full
bounded capture reproduces 100.00/66.67/33.33% with three eligible lines each.
Updated only the dedicated ignored runtime key fields; original `.env` is preserved.
No permission expansion, Odoo business write or fitted-model change occurred.

**Normal persistent setup: PASS.** The actual HTTP matrix completed in 8.427 s:

| Scenario | Minimum USD | Result |
| --- | ---: | --- |
| Supplier C outage | 2,200 | feasible |
| C capacity 100 | 2,200 | feasible; MOQ prevents C allocation |
| Demand 250 | 2,340 | feasible |
| C price 13 | 2,200 | feasible |
| Demand 220, C capacity 150/price 10 | 2,200 | feasible |
| Demand 500 | — | infeasible; no fabricated plan |

All children retain the original captured assessments. The new original base has
USD 1,850 minimum and its saved lower-exposure alternative is deliberately
technically approved. A separate base records No-award and rejects approved-PDF
retrieval. These records are labelled functional verification, not real purchasing
authority or UX acceptance.

Persistent cases retained in the existing helper:

- Approved alternative: `725988fb-79fe-483d-b556-d9cecc8911e8`.
- No-award: `ebb0ef54-b48a-4dab-a09f-59d583c740b0`.
- Six scenario children. Total helper cases: **44 = 36 unchanged originals + 8 new**;
  two new final decisions and one saved PDF.
- Saved report `t17-run-1e90b7d0-3be8-49c5-b15b-02b00b04f92f.json` under the evidence
  directory above; PDF SHA-256
  `2f09067f37b09a41740d2a925b9f627956620d2a0442191b9f0f12b237b98d30`.

Actual owner helper/API restart with all Odoo keys and model directories disabled
passes stored case/scenario/decision checks, every exact idempotent replay,
byte-identical PDF retrieval and No-award PDF denial. All prior row fingerprints
remain present unchanged. Normal API configuration was then restored.
`persistent-restart-pass.json` and `functional-final-summary.json` retain the result.

**Expanded live Chromium stack: PASS**, one test in 104.65 s. It completes UI
creation/supplier evidence/scenario/minimum-cost approval/PDF, then the entire
functional matrix, owned database/API restart and stored replay without upstream.
Evidence: `.artifacts/t18-browser-cf6c39026580/evidence.json`. Its disposable
containers/processes were removed; owner Odoo was never stopped. Preserve the
earlier authentication failure separately.

**Normal owner frontend: PASS.** At localhost:3000, a read-only browser check
reopens the persistent approved case, retrieves its saved PDF and displays the
Odoo-history supplier evidence without creating/finalizing anything new.
`owner-browser-reopen.json` records this check. API 8000, Reflex 8001/frontend
3000 and existing containers/localhost tunnels are intentionally left running
for owner use. Existing local startup/recovery instructions apply after reboot.

The 706-test full fast run and 34 post-isolation focused checks above remain the
code verification; only the credential-blocked live gates were rerun. No further
code change required retraining or altered the solver/contracts. This closes the
declared functional increment locally. Hosted CI for these new uncommitted changes,
UX assessment and genuine operational model validation remain outside this result.

Owner Reflex startup regenerated its tracked lock files. Those startup-generated
edits were preserved under ignored evidence and restored to their original tracked
contents; no dependency update is part of this increment. To stop the current
background app after use, verify the command lines for the root PIDs recorded in
`api.pid` / `frontend.pid`, then stop those process trees only. At this handoff the
roots are API 39940 and Reflex 30048; do not reuse these numbers after a restart.
The existing helper's original volume and all saved records must remain intact.
