# Chapter 7 measurement refresh on the thesis tag

Date: 2026-11-13 (Europe/Budapest). Branch: `codex/chapter7-measurements-20261113`.
Measured commit: `e3e05d655099ccae68bf24d447e39564340bfc70`, tag `szakdolgozat-v1`.
No commit, push or PR was created by the agent.

## Problem and decision

Chapter 7 cited October measurements although the submitted code was tagged on
November 10. This Windows machine still had the older Odoo databases, old runtime
settings and an incomplete Python 3.14 environment; the other machine's seeded
`pdss_history_gen`, training export and saved model were absent.

The owner chose a new dedicated local environment and manually configured Odoo and
its two restricted users. The existing guarded seeder and standard training pipeline
were used. Application and tooling source stayed unchanged: 174 tracked Python/config
file hashes matched before and after. Both requested measurements ran on clean
`e3e05d6` and record `dirty: false`. After the demo, its new report was saved locally
and its original tracked bytes restored before starting MILP evaluation. Both new
summaries were copied into `docs/evidence` only after measurement completed. Their
Git metadata was never edited.

This is a new end-to-end experiment on the thesis code, with a new machine,
dependency resolution, Odoo record identities, rolling export window and model.
It cannot isolate the effect of the refactor or reproduce the old model's numbers.

## Implemented environment and retained evidence

- Python 3.11.16 in `.venv`; existing `.[frontend,dev]` requirements installed.
  The older incomplete environment and original `.env` were backed up locally.
- Existing Podman machine reused: 7 vCPUs, 2048 MiB, rootful WSL, user-mode networking.
  Host: 14 logical CPUs, Intel Family 6 Model 170, Windows build 26200. The old MILP
  report used Python 3.11.15, 16 logical CPUs and Intel Model 154.
- Odoo image `19.0-20260908`, PostgreSQL `16.15-bookworm`; new database
  `pdss_history_gen`, company 1, HUF. Runtime uses separate quotation and portal
  history keys; purchase writes and generic stock reads were verified denied.
- Generated history readback: 2,546 unique confirmed purchase orders, 2,823 completed
  receipts, 40 suppliers, 3 products; seed 20261017, simulated clock 2026-10-17.
  Groups 1/2/3 contain 4/5/10 suppliers respectively (19 draft RFQs altogether).
  Old Odoo databases and volumes were retained. Backend Odoo access remains read-only.
- Persistent `planning` database on localhost:55440; disposable `planning_test` on
  localhost:55441; both migrated to `20261021_01`. Measurement API uses localhost:8010.
- Windows Podman port forwarding failed although the services answered inside the VM.
  Two temporary localhost-only SSH tunnels expose 8069, 55440 and 55441. They and the
  containers are intentionally left available for continued local use. Measurement
  and verification APIs stop at the end of their context managers.
- [P4_DEMO_REPORT](../evidence/P4_DEMO_REPORT.json), generated 2026-11-13T10:11:56+00:00.
- [P4_MILP_EVALUATION](../evidence/P4_MILP_EVALUATION.json), generated 2026-11-13T10:52:12+00:00.
- [New ML context](../evidence/P4_ML_CONTEXT_20261113.json): complete training/evaluation
  report for this run, separate from historical `P1_ML_REPORT` and `P4_ML_REPORT_CHECK`.
- [Environment record](../evidence/P4_ENVIRONMENT_20261113.json): exact dependencies,
  model/export/artifact hashes, service settings without credentials, and verification.
- Local input copies: `.artifacts/p4-refresh-20261113/inputs/` (export, dataset, model,
  seed manifests); `raw-demo/` retains every demo response and all four PDFs. Their
  hashes are in the environment record. These are ignored local files, not Git assets.
  The same local parent also contains a secret configuration backup: never publish
  or archive that entire parent directory indiscriminately.

## Measured results

### Demo

Nine scenarios (including two infeasible), approval, a separate No-award, supplier
overview and HU/EN plan and audit PDFs passed. Thirteen exact operations replayed
with Odoo unreachable and the model directory empty. All four PDFs were byte-identical;
No-award denied both document kinds. HTTP flow: **28.032 s**; total demo
including isolated replay and API starts: **57.01 s**.

| Plan | Cost HUF | Exposure | Positive allocation quantities |
| --- | ---: | ---: | --- |
| Minimum cost | 288608 | 0.3958 | 80 + 120 |
| Lower-exposure alternative, approved index 1 | 299454 | 0.3333 | 120 + 80 |
| Balanced alternative, index 2 | 299860 | 0.3333 | 100 + 100 |

The minimum cost remains 288608 HUF. The old demo's exposure was 0.6000 and its
alternatives cost 293132 / 295800 HUF. Supplier IDs belong to different Odoo databases;
use the supplier names and report identity when comparing allocations. The refreshed
traceability description identifies the actually approved index 1 allocation.

### MILP/API

**PASS: 21/21 correctness entries**, including the minimum, every epsilon alternative
and balanced stage, repeated-result equality, input permutation stability and
infeasible variants. Six workloads used **2 warmups + 30 measured repetitions** each.
Every raw latency sample count and nearest-rank p95 was independently rechecked.

Times below are milliseconds, **median / p95**. The last column is historical context.

| Suppliers | Epsilons | Create | Scenario | Exact retry | GET | Old create p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 1 | 1794.4 / 2207.2 | 1255.5 / 1528.6 | 251.4 / 361.6 | 110.3 / 138.1 | 510.9 |
| 4 | 3 | 2613.0 / 3134.8 | 2110.7 / 2734.0 | 254.7 / 322.6 | 109.4 / 143.4 | 645.0 |
| 5 | 1 | 2102.8 / 2326.0 | 1600.8 / 1761.7 | 254.1 / 354.7 | 110.4 / 122.3 | 558.5 |
| 5 | 3 | 3478.0 / 4721.3 | 2876.8 / 3547.6 | 284.6 / 339.2 | 125.7 / 155.1 | 1104.5 |
| 10 | 1 | 3294.7 / 3677.1 | 3114.7 / 3503.3 | 319.5 / 408.4 | 147.4 / 170.4 | 1093.8 |
| 10 | 3 | 5680.1 / 6619.6 | 5126.0 / 5818.9 | 318.9 / 381.0 | 149.5 / 336.8 | 1578.2 |

These are single-machine observations with local SSH forwarding. They do not show
that the refactor caused a slowdown and are not an SLA. The complete tool, including
reference enumeration and repeated solves, took about 40 minutes on this machine.

### Model/data change that chapter 7 must identify

The standard pipeline reads a rolling **548-day** export. This run exported 2,481
purchase lines / 2,751 receipts, from 2025-05-14 10:00 UTC to 2026-11-13 10:00 UTC.
The full seeded database still contains 2,546 history orders; older lines fall outside
the export. Training boundary: 2026-05-16; 671 train rows; 147 primary test rows
(120 regular, 27 problematic); selected depth 4. Model:
`a31f0627c79a176da564a699aa908a09f60f7a32cfb2da73047f0d7ecc939bd4`.

| Primary metric | Historical P1 model | New model |
| --- | ---: | ---: |
| Held-out rows | 140 | 147 |
| Tree macro F1 | 0.588675 | 0.464865 |
| Tree accuracy | 0.685714 | 0.775510 |
| Majority macro F1 | 0.409283 | 0.449438 |
| Learned single split macro F1 | 0.594312 | 0.467873 |
| Expert rule macro F1 | 0.657738 | 0.497242 |

New tree confusion matrix (actual rows, predicted columns, regular/problematic):
`[[113, 7], [26, 1]]`. It detects **1 of 27** problematic test rows (recall 0.037037).
This is weak classification evidence and does not support operational supplier
screening. It remains below both the expert rule and learned single split in macro
F1. Generated data, small correlated samples and uncalibrated leaf frequencies remain
limitations. Requirements do not require superior predictive performance.

Reloading the new saved artifact and evaluating it again reproduced every metric and
hash in the **new** training report. That check does not mean it matches P1. Historical
`P1_ML_REPORT.json` and `P4_ML_REPORT_CHECK.json` were preserved unchanged.

## Commands actually run and verification boundaries

Python commands below used `.venv/Scripts/python.exe` at the repository root.
Command locations/prerequisites remain in [RUNBOOK](../RUNBOOK.md).

- `python -m tools.seed_odoo_history plan`, `apply`, then `groups`: PASS; official
  read-only API probes verified guard, modules, key roles and generated record counts.
- `python -m tools.train_history_model all`: PASS; read-only extraction and offline fit.
- `python -m tools.dev demo`: exit 0; full and isolated replay PASS.
- `python -m tools.milp_evaluation`: exit 0, `passed: true`; defaults retained.
- `python -m tools.dev check`: format, lint and compile PASS; host pytest attempt
  **137 failed / 350 passed** because the helper sets CBC TEMP/TMP inside the
  space-containing checkout path. The earlier sandbox import attempt was stopped;
  its own process tree was confirmed terminated. These attempts remain failed evidence.
- `python -m pytest tests/test_approved_documents.py -x -q --tb=short
  -p no:cacheprovider --basetemp .artifacts/p4-refresh-20261113/focused-pytest`:
  **28 PASS** without the helper's incorrect temp override.
- `python -m pytest -m "not integration and not e2e" -q
  --basetemp .artifacts/p4-refresh-20261113/pytest-safe -p no:cacheprovider`:
  **487 PASS, 51 deselected**, 309.62 s, with TEMP/TMP set to the verified Windows
  short path stored locally in `cbc-temp-path.txt`. Real CBC and scikit-learn ran.
  `uv pip check --python .venv/Scripts/python.exe`: PASS, 80 packages compatible.
  This equivalent successful check sequence is not a passing `tools.dev check` command.
- Initial `python -m pytest -m "integration and not e2e" -q -rs
  --basetemp .artifacts/p4-refresh-20261113/pytest-integration -p no:cacheprovider`:
  **27 PASS / 17 FAIL / 4 SKIP**. The passes comprise **26 PostgreSQL tests plus Odoo
  HTTP availability**, not 27 PostgreSQL tests. Old keys caused 15 HTTP-401 failures;
  two external API tests reached another service on port 8000. Preserve this attempt.
- Targeted retry: `python -m pytest tests/integration/test_live_odoo_contract.py
  tests/integration/test_live_purchase_history.py tests/integration/test_runtime_services.py
  -m "integration and not e2e" -q -rs
  --basetemp .artifacts/p4-refresh-20261113/pytest-live -p no:cacheprovider`: **20 PASS / 2 SKIP**, 6.54 s.
  A dedicated API ran on 8010, `BACKEND_BASE_URL` pointed there,
  `RUN_ODOO_HISTORY_LIVE=true`; old `RUN_T6_LIVE_CONTRACTS` and
  `RUN_T7S_LIVE_CONTRACTS` were false. The 26 already-passing PostgreSQL tests were
  not rerun. The scopes together cover 46 passing integration cases and two older
  manual-fixture skips; no fresh full-suite PASS is claimed.
- Final artifact checks: `git diff --check`, JSON parsing, report/input/PDF SHA-256
  checks, unchanged code hashes and historical ML reports, documentation links and
  a scan for local secret values in every changed/new file: PASS.
- No new browser/e2e, UI visual acceptance, PDF visual review, human buyer acceptance
  or hosted CI was run. One upstream Starlette deprecation warning remains.

Local logs are under `.artifacts/p4-refresh-20261113/`: `check*.log`,
`pytest-safe.log`, `integration.log`, `live-integration.log`, `seed-*.log`,
`train.log`, `demo-command.log`, `milp-command.log`; API logs are retained as well.

## Remaining limits, cleanup and owner actions

- The `tools.dev check` Windows path bug remains in the measured tag; no application
  or tooling source was changed to fix it. Use a space-free CBC temp path for the
  measurement commands; see RUNBOOK troubleshooting. Later training and inference
  are date-dependent, so preserve the exact local input/model copies before reruns.
- Native Windows Podman forwarding remains broken; SSH is a session-local workaround.
  The two current tunnel PIDs are recorded in `odoo-tunnel.pid` and
  `postgres-tunnel.pid` under the local run folder. Restore forwarding after it stops
  or the machine restarts. Port 8000 belongs to another local service; normal API/UI
  startup was not part of this run. Measurements and the retry used 8010.
- The seeder admin key is no longer needed: revoke it in Odoo and remove its value
  from `.env`. It was never used by the runtime backend. Keep the two restricted keys.
- Services/tunnels remain running for local use. Before cleanup, verify the saved PIDs
  still belong to these SSH commands, stop only those processes, and wait for exit.
  Stop the new test stack without deleting unrelated containers or volumes. The app
  volume and both old Odoo databases must be retained.
- Review and commit/push/merge are owner actions. No Drive document was edited.

## Thesis chapter and acceptance mapping

Official task **423.589/25/140**: historical data and Python supplier evaluation,
MILP multi-supplier allocation, stress scenarios, stored human decision/PDF, and
reproducible evaluation. Relevant **FR-V2-01–08, FR-V2-10–12**;
**AC-V2-01–08, AC-V2-10–13**; **NFR-V2-02–06 and NFR-V2-08**.
The HTTP demo adds no new browser evidence for FR-V2-09 / AC-V2-09.

For chapter 7, cite the exact measured commit/tag and November 13 report timestamps;
use this run's model/data identities, plans, class metrics and timing table together.
Keep earlier numbers explicitly dated as historical experiments. The new model's
0.464865 macro F1 and low problematic recall require an updated discussion, not only
a changed date in section 7.2. The source-code version is aligned; thesis prose and
figures in Drive still need the owner's explicit update/review.
