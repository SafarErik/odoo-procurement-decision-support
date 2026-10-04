# T14 — controlled Decision Tree supplier-evaluation handoff

## Result and starting point

**IMPLEMENTED / LOCAL AND HOSTED IMPLEMENTATION CHECKS VERIFIED; PR #16 OPEN / NOT MERGED.** T14 provides
an offline supplier-evaluation pipeline, versioned trusted model reload, actual tree
paths and a narrow T13 risk-input/CBC demonstration. It does not complete the V2
workflow or validate a real supplier predictor.

Repository and hosted evidence reverified on 2026-10-04:

- Branch: `feature/t14-decision-tree-pipeline`.
- Entry base: [`ff8cc5bfebaef5f8d73751991101008830307012`](https://github.com/SafarErik/odoo-procurement-decision-support/commit/ff8cc5bfebaef5f8d73751991101008830307012),
  the merged T13 PR #15 commit. Remote main still matches this base at this check;
  fetch, ls-remote and T13 ancestry were verified. It is not the T14 implementation HEAD.
- Implementation commit: [`32e117242b1dbdf58f2e38897942e13c6507e12a`](https://github.com/SafarErik/odoo-procurement-decision-support/commit/32e117242b1dbdf58f2e38897942e13c6507e12a),
  `Add Controlled T14 Supplier Evaluation Pipeline`, committed and published by
  the user. Local HEAD, origin branch, ls-remote and PR HEAD matched this commit
  before this documentation correction; the working tree was clean.
- PR [#16](https://github.com/SafarErik/odoo-procurement-decision-support/pull/16),
  `Add Controlled T14 Supplier Evaluation Pipeline`, is open, non-draft and unmerged,
  targeting `main`. The verified implementation CI evidence below belongs to `32e1172`.
- Documentation revision: this 2026-10-04 follow-up changes only `docs/T14_HANDOFF.md`
  and is committed after the implementation commit on the same branch/PR. After
  publication, branch/PR HEAD identifies this correction rather than the entry base
  or implementation commit. Its exact commit and new HEAD's CI status are reported
  after push; successful implementation runs do not establish CI for this revision.

The October 2 Drive and October 3 T13 handoff pre-merge statements are dated status
records, not evidence that T13 is absent from main. At the original local T14
handoff, changes were unstaged/uncommitted and hosted CI was unverified. Those
pre-publication observations are historical and superseded by the publication and
implementation checks above; the local results and limitations below are preserved.

The entry working tree was clean. Python 3.11.16 baseline: 328 passed / 37 deselected;
Ruff format/lint and pip check passed. Reused ignored `.venv/t13-check`, leaving the
existing root Python 3.14.7 environment intact. Installed dependencies only in the
project-local Python 3.11 environment. No unrelated work or stash was changed.

Before implementation on 2026-10-04, read the then-current original
00_THESIS_STATUS, 02_ROADMAP, 03_ARCHITECTURE_DECISIONS,
06_REQUIREMENTS_BASELINE and 07_DEVELOPMENT_STATUS under the actual
SZAKDOLGOZAT / 00_Project_Control through Google Drive. They confirm ADR-025,
FR-V2-02/03 and controlled data acceptance; the issued/approved task sheet is dated
2026-09-22, reference 423.589/25/140. Drive was read, not edited. Inspecting the
isolated ML spike `ffa29398f42e2ccb7f11f09696a42295bd394035` informed temporal,
support and explanation choices; no cumulative spike code was merged or imported.
The [design](T14_ML_DESIGN.md) was saved before source implementation.

## Files and implemented boundaries

| Files | Responsibility |
| --- | --- |
| `supplier_evaluation/contracts.py` | Immutable context/evidence/features/assessment, versions, class mapping and score validity |
| `supplier_evaluation/history.py` | Existing T8 neutral KPI reuse; sourced aggregate conversion, no live read |
| `supplier_evaluation/dataset.py` | Seeded controlled receipts/outcomes, strict cutoff/group/duplicate validation, dataset JSON |
| `supplier_evaluation/model.py` | Fixed sklearn tree, training-only fit, semantic identity, supported inference and exact float32 tree path |
| `supplier_evaluation/artifacts.py` | Trusted local joblib + manifest, pre-load compatibility/checksum and post-load fitted-state checks |
| `supplier_evaluation/evaluation.py` | Explicit binary/undefined metrics and genuine three-supplier CBC example |
| `supplier_evaluation/planning_bridge.py` | Complete T13 supplier join, context/time/quantity coverage and provenance references |
| `supplier_evaluation/cli.py` | Generate/train/evaluate/reload/infer/demo/reproduce commands |
| `tests/test_t14_*.py`, `tests/t14_helpers.py` | Data, model, boundary, architecture and mandatory runtime verification |
| `pyproject.toml`, `.github/workflows/quality.yml` | Required pinned ML runtime and installed-package discovery; explicit Python 3.11 runtime gate |
| `.gitignore`, `AGENTS.md`, `README.md`, implementation log and T14 records | Ignored generated artifacts, current scope, commands and evidence |

Decision Core/planning and solver source are unchanged. Existing V1 WSM/API/history,
T11/T12 snapshots and stored-only GET/exact retry retain their regressions. No new
HTTP route, migration, Reflex code, Odoo call/write, direct DB access, approval/PDF,
autonomous transaction or full T15 coordinator was added.

## Data, split, target and risk decisions

One observation: supplier/company/product/unit at a prediction cutoff. The prior
365-day half-open history contains only complete synthetic receipts known at that
cutoff. The two ordered features are T8 `delivery_schedule_adherence` percent
against **Expected Arrival**, and its completed-line sample size. Supplier identity,
quantity and future outcomes are excluded from features. No imputation, scaling or
learned preprocessing occurs; only train vectors/labels enter fit. Minimum history
3, maximum 50, minimum training class support 20 and minimum leaf support 10 are
technical PoC gates, not statistical confidence guarantees.

Class 1 `schedule_watch`: at least two of five synthetic receipts in the next
30 days miss Expected Arrival. Class 0 `schedule_regular`: fewer than two.
Future labels come from separate receipts, available after the complete window.
The generator deliberately assigns a future per-line miss probability of 0.65
when prior adherence is below 80%, otherwise 0.10. The tree therefore learns an
intentionally constructed noisy mechanism; high accuracy does not establish real
predictive value. All data are synthetic; no observed Odoo training export exists.

Seed 17; 160 train suppliers at 2026-01-01, outcome availability 2026-01-31; split
boundary 2026-02-15; 80 disjoint test suppliers at 2026-03-01; extraction 2026-04-01.
Exact observation/context cutoffs and receipt IDs cannot be duplicated or cross
history/target or train/test. Repeated numeric patterns from independent suppliers
are legitimate. Test outcomes cannot change train/test features or the fitted tree.
No test-based model/threshold selection. Fixed gini/best tree, depth <=3,
min_samples_leaf=10, min_samples_split=20, seed=17, no weights/pruning/tuning.
The fitted tree has depth 3 and five leaves.

Dataset `t14-controlled-supplier-contexts-v1`; feature `t14-history-features-v1`;
target `t14-next-window-schedule-watch-v1`; artifact `t14-trusted-tree-v1`;
risk mapping `t14-leaf-exposure-v1`. Model/training/assessment identities are
canonical content hashes; exact runtime versions are checked on reload.

Risk score = training class-1 count / leaf support, four-place Decimal half-up.
Higher means less favourable controlled schedule-watch exposure. It is not a
calibrated real disruption probability or expected late units. An actual supported
zero-count leaf may score zero; absent/malformed assessments never default to zero.
The class, score, training support, path and provenance remain separately visible.

No quantity feature: the controlled exposure proxy is **defined** as constant over
an explicit caller-declared integer range. This avoids quantity-100 extrapolation
without claiming empirical quantity independence. Inference rejects observed
contexts with this synthetic model. The bridge checks every supplier, common
company/product/unit, model identity, as-of time and required date inside the
30-day horizon, and coverage of every positive business allocation range. It does
not restrict business feasibility to accommodate a score. Real promotion requires
new audited dataset/mapping/quantity-validity evidence. Cost-only remains separate.

## Measured evaluation and actual solver example

The full machine-readable [evaluation](T14_EVALUATION.json) contains dataset/split
details, exact hashes, model/runtime versions, configuration, metrics, leaf support,
tree text and solver outputs. Two independent CLI reproduction directories produced
identical complete reports under the documented environment.

Confusion matrix, rows=true and columns=predicted, labels [0,1]:

```text
[[23, 1],
 [ 0,56]]
```

| Class | Test support | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| 0 schedule_regular | 24 | 1.000000 | 0.958333 | 0.978723 |
| 1 schedule_watch | 56 | 0.982456 | 1.000000 | 0.991150 |

Accuracy: **0.987500**; macro precision 0.991228, recall 0.979167, F1 0.984937.
Train support [43,117]; test support [24,56]. No undefined metric in this run.
Absent/no-predicted classes are separately tested: undefined values are JSON null
with explicit reasons, and macro metrics remain undefined if a component is undefined.
This evaluation measures synthetic pipeline behaviour, not prediction superiority.

Actual inferred coefficients: S226=1.0000, S184=0.9661, S161=0.0000, each valid on
the explicitly declared [1,1000] controlled proxy range. Q=10 pieces, prices
10/10.5/11 EUR respectively, capacities 6/8/10, no hard MOQ, maximum two suppliers,
concentration 0.8 and epsilon 0.1. Existing PuLP/CBC proves:

| Plan | S226 | S184 | S161 | Cost EUR | Weighted exposure | Premium |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Minimum cost | 6 | 4 | 0 | 102 | 24661/25000 (0.98644) | 0 |
| Lower exposure within 10% cap | 0 | 2 | 8 | 109 | 9661/50000 (0.19322) | 7/102 |

These are actual ML predictions used in `RiskCoefficient`/`ExternalRiskContext`,
not hard-coded coefficients or a mocked solve. The quantities, cost objective,
epsilon semantics and deterministic tie-break remain T13's unchanged model.

## Historical local reproduction and verification (2026-10-04)

Recorded local runtime: Windows; Python 3.11.16, sklearn 1.8.0, NumPy 2.3.5, SciPy 1.16.3,
joblib 1.5.2, threadpoolctl 3.6.0, PuLP 3.3.0, actual CBC 2.10.3. Dependencies are
required, installed locally and pinned in project metadata. No optional skip.

```powershell
.\.venv\t13-check\Scripts\python.exe --version
.\.venv\t13-check\Scripts\python.exe -m pip install -e ".[frontend,dev]"
.\.venv\t13-check\Scripts\python.exe -m supplier_evaluation.cli generate
.\.venv\t13-check\Scripts\python.exe -m supplier_evaluation.cli train
.\.venv\t13-check\Scripts\python.exe -m supplier_evaluation.cli evaluate
.\.venv\t13-check\Scripts\python.exe -m supplier_evaluation.cli infer
.\.venv\t13-check\Scripts\python.exe -m supplier_evaluation.cli demo
.\.venv\t13-check\Scripts\python.exe -m supplier_evaluation.cli reproduce
.\.venv\t13-check\Scripts\python.exe -m supplier_evaluation.cli reproduce --directory .artifacts/t14/recheck
.\.venv\t13-check\Scripts\python.exe -m ruff format --check .
.\.venv\t13-check\Scripts\python.exe -m ruff check .
.\.venv\t13-check\Scripts\python.exe -m compileall -q application backend frontend decision_core odoo_adapter optimization_adapter supplier_evaluation persistence migrations infra/odoo/addons/t7s_inventory_history_projection
.\.venv\t13-check\Scripts\python.exe -m pytest -m "not integration and not e2e" -v -o cache_dir=.venv/t13-check/pytest-cache
.\.venv\t13-check\Scripts\python.exe -m pip check
git diff --check
$env:PODMAN_COMPOSE_PROVIDER = Join-Path (Get-Location) '.venv\t13-check\Scripts\podman-compose.exe'
& "$env:LOCALAPPDATA\Programs\Podman\podman.exe" compose --env-file .env -f infra/odoo/compose.yaml config --quiet
```

Generated raw receipt datasets, joblib/manifest and JSON outputs are ignored in
`.artifacts/t14/`. Only the small evaluation evidence report is tracked for review.
`train` saves/reloads; evaluate/infer/demo reload and never train. All CLI operations
were exercised by the mandatory runtime suite; reproduce and infer were also run as
independent Python processes. Load only locally generated trusted artifacts:
joblib can execute code; the explicit trust flag and checksums are compatibility/
integrity gates, not authentication or safe loading of foreign files.

| Status | Gate and evidence |
| --- | --- |
| PASS | Final full suite: 394 passed, 37 deselected, one upstream Starlette warning, 48.22s; includes all 66 T14 and existing legacy/T13 tests |
| PASS | Latest focused T14 after final boundary hardening: 66 passed, 24.69s |
| PASS | Actual Python 3.11 training/export/reload/inference, CLI stages and genuine CBC contract demonstration; no dependency/runtime skips |
| PASS | Final formatting (131 Python files), lint, compilation, pip check and whitespace |
| FAILED | Local Podman Compose configuration: 127.0.0.1:64087 socket connection refused; retry outside sandbox confirmed infrastructure failure |
| SKIPPED | Local service integration, controlled live Odoo and browser E2E: unavailable runtime; no service start or Odoo mutation |
| UNVERIFIED | Real-world prediction, observed dataset sufficiency, full V2 API/UI/scenario/approval/PDF and cross-platform artifact portability |

These are the original local execution results, not tests rerun for this
documentation correction. The local Podman failure and service/live/browser skips
remain unchanged by the subsequent hosted Linux/Docker success.

## Hosted implementation evidence, reverified on 2026-10-04

GitHub PR metadata, workflow conclusions, job steps and decoded logs were read for
implementation commit `32e117242b1dbdf58f2e38897942e13c6507e12a`. Both workflows
executed on 2026-10-04. This evidence read does not rerun local tests or services.

| Gate | Actual hosted implementation evidence |
| --- | --- |
| [Quality run 37189074967](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37189074967), [job 111397267966](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37189074967/job/111397267966) | SUCCESS on Linux / Python 3.11.16: 394 passed, 37 deselected, one warning in 13.80s |
| Required T13 solver gate in the same Quality run | PASS: 5 passed in 0.07s, including actual PuLP/CBC runtime execution |
| Required T14 training/reload/inference/MILP gate in the same Quality run | PASS: 2 passed in 5.65s, including genuine training/export/reload/inference/CBC and all documented CLI stages; no dependency/runtime skips |
| Formatting / lint / compilation / dependencies / whitespace / Compose configuration in Quality | PASS: 131 Python files formatted, lint passed, compilation and whitespace steps succeeded, no broken requirements; hosted Docker Compose configuration validated with synthetic credentials |
| [Container/API run 37189075012](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37189075012), [job 111397268296](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37189075012/job/111397268296) | SUCCESS on Linux / Python 3.11.16: 17 passed, 20 skipped, 394 deselected, one warning in 3.24s |
| Reflex frontend compilation and technical named-volume persistence in Container/API | PASS as job steps; compilation and technical persistence do not prove browser E2E or an Odoo business-scenario persistence flow |
| Controlled live Odoo contracts in Container/API | SKIPPED: all 20 cases in `tests/integration/test_live_odoo_contract.py`, including RFQ/access/schema/T5 and controlled T6/T7-S/T8 contracts |

CodeRabbit's commit status was SUCCESS for `32e1172` at this read. This status and
the successful workflows do not turn skipped live tests into passes or establish
real-world model validity, cross-platform artifact interchange, or full V2 readiness.
The original synthetic-model limitations and quantity-independent proxy meaning
remain unchanged. Hosted configuration/service checks used Linux/Docker and do not
resolve the historical local Windows/Podman socket failure.

The new documentation HEAD requires its own check. After push, inspect runs/statuses
for that exact SHA and report their actual state. Pending, absent or path-filtered
checks must not inherit SUCCESS from the implementation commit.

## Traceability and T15 boundary

| Requirement / acceptance | T14 status | Evidence/limit |
| --- | --- | --- |
| FR-V2-02 / AC-V2-02 | IMPLEMENTED / LOCAL PASS on controlled data | Existing KPI semantics, support/as-of provenance, versioned synthetic receipts, separate labels and leak-safe split |
| FR-V2-03 / AC-V2-03 | IMPLEMENTED / LOCAL PASS on controlled data | Single tree, deterministic training/reload/inference, measured metrics/class support and actual path |
| FR-V2-07 tree explanation | IMPLEMENTED / LOCAL PASS | Float32 conditions, exact thresholds, actual leaf/class counts; no probability/causal claim |
| NFR-V2-01–04 relevant ML portion | LOCAL PASS | External library/artifact boundary, versions/seed, leakage gates, architecture and negative/runtime tests |
| Complete FR-V2-07 and V2 acceptance chain | OPEN at workflow level | T13 explanation plus T14 path exist in process; their live API/UI presentation and full lifecycle remain later work |

T15 should assemble bounded source-derived as-of history with explicit
company/product/unit selection and supplemented business terms; it must not infer
historical availability from a later current Odoo read. Decide whether to retain a
controlled demo or authorize a new observed-model/label/validity version. Add typed
V2 API/scenario orchestration and immutable model/feature/dataset/policy/solver/
input/output/provenance snapshots. Exact retry/GET must remain stored-only: no
Odoo reread, fit, inference or solve. Approval/PDF and frontend remain T16/T17.

There is no blocking question for the authorized controlled T14 increment.
Observed-data promotion and full T15 interface design remain separate decisions.

## Proposed Drive synchronization only — no writes performed

- **00_THESIS_STATUS:** T13 is merged at ff8cc5b; T14 implementation is committed
  and published at 32e1172 in open/unmerged PR #16, with local and hosted checks
  verified on that implementation commit and explicitly synthetic evidence.
  Preserve full V2 OPEN, issued task-sheet attribution, the historical local
  Podman failure and live/browser skips. Record this subsequent documentation
  revision and its CI separately; do not retain uncommitted/unpublished as current state.
- **02_ROADMAP:** T14 data/cutoff/split/risk-validity/Python 3.11 gates addressed in
  controlled scope; next T15 is bounded assembly/API/scenario/snapshot composition,
  with observed promotion still requiring audited evidence.
- **03_ARCHITECTURE_DECISIONS:** supplement ADR-025 with versioned two-feature
  synthetic tree and quantity-independent exposure proxy rationale. Preserve
  ADR-024/026/027 and do not mark probability calibration or real validity established.
- **06_REQUIREMENTS_BASELINE:** FR-V2-02/03, AC-V2-02/03 and tree portion of FR-V2-07
  LOCAL PASS on controlled data; keep workflow-level and live gates separate.
- **07_DEVELOPMENT_STATUS:** record actual branch/base, runtime, measured metrics,
  implementation commit/PR and linked hosted runs, tree/CBC example, executed
  checks and FAILED/SKIPPED/UNVERIFIED categories. Hosted implementation CI is
  verified; the documentation HEAD's CI is separate. Keep skipped live tests,
  synthetic limitations and full V2 OPEN, with links to these T14 records.

This documentation-only correction uses `git diff --check` and is committed/pushed
to the existing `feature/t14-decision-tree-pipeline` branch and PR #16. It changes
only this handoff. No local runtime/service tests are rerun, and no code, Drive,
Odoo, new PR or merge operation is part of this correction. The implementation
checks above remain attributed to `32e1172`; the correction's exact commit and
latest CI state are reported separately after publication.
