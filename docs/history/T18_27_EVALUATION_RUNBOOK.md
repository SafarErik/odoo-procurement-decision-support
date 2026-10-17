# Supported workload and stress evaluation — #27

This procedure extends [#26's runtime setup](T18_26_EVALUATION_RUNBOOK.md) using
the same Python 3.11 environment, isolated disposable PostgreSQL, loopback API,
trusted offline model and existing Podman machine. Read that setup and cleanup
first. Never run resetting database tests against a database containing evidence
you intend to retain, or against an Odoo/application database.

## Prepare the six controlled workloads offline

Choose a **new** ignored root. Each preparation refuses to overwrite an existing
directory. No Odoo, database or API process is needed for preparation.

```powershell
$taskRoot = Join-Path '.artifacts' ('t18-27-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskRoot | Out-Null
foreach ($taskN in 3, 5, 10) {
    foreach ($taskE in 1, 3) {
        python -m tools.t18_evaluation prepare `
          --directory (Join-Path $taskRoot "synthetic-$taskN-$taskE") `
          --suppliers $taskN --epsilon-count $taskE
        if ($LASTEXITCODE -ne 0) { throw 'Offline preparation failed' }
    }
}
```

Expect six `create-request.json`, `preparation.json` and `model/` directories.
The existing seed-17 synthetic dataset/training pipeline is unchanged. All models
have the same declared company/product/unit, cutoff and manifest identity. The
three original suppliers keep their historical prices/capacities/history. Larger
fixtures add distinct existing held-out synthetic profiles, selected in stable
score/identity order, with prices EUR 11.5 upwards in 0.5 increments and capacity
10. Demand remains 10; max suppliers 2; concentration 80%; MOQ absent; all
price/delivery/score ranges 1–1000. This isolates supplier/epsilon dimensions;
it is not a representative random sample of real procurement problems.

One epsilon is `[0.1]`; three are `[0.05, 0.1, 0.2]`. Distinct returned
alternatives can be fewer than requested epsilons. The evaluator verifies each
saved run's reference and exact cap; duplicate allocation is an accepted outcome.
Preparation flags apply only to `prepare`; `run` reads the saved input.

## Verify services, then measure sequentially

Run the existing PostgreSQL integration contracts **before** serving cases, using
the new disposable database and a fresh pytest temp/cache directory as described
in [persistence development](PERSISTENCE_DEVELOPMENT.md). Apply `alembic upgrade
head` with that explicit `DECISION_DATABASE_URL` afterwards. Configure the API's
`T15_TRUSTED_MODEL_DIRECTORY` to the new `synthetic-3-1/model`; all six offline
fixtures have matching model metadata. Keep the bearer token on the server/in
the process environment. Start Uvicorn using #26's instructions and an unused
loopback port, e.g. 8002. Reflex is unnecessary for this evaluation.

```powershell
foreach ($taskN in 3, 5, 10) {
    foreach ($taskE in 1, 3) {
        python -m tools.t18_evaluation run `
          --directory (Join-Path $taskRoot "synthetic-$taskN-$taskE") `
          --base-url http://127.0.0.1:8002
        # Retain a nonzero result; inspect its report before any recovery.
        if ($LASTEXITCODE -ne 0) { Write-Warning "Workload $taskN/$taskE failed; retain evidence" }
    }
}
```

Each workload records two complete warm-ups and 30 measured attempts for each
of 12 operations: create; outage; capacity reduction; demand increase; price
increase; combined changes; infeasible demand; approval; GET; exact creation
replay; first PDF; cached PDF. The first original supplier is removed, reduced
from capacity 6 to 3, or repriced from 10 to 12. Feasible increased demand is 12;
the combination changes demand to 12 and that supplier's capacity to 3/price to
12. Infeasible demand is 1000, within declared model validity but above aggregate
capacity. All children target the original base and retain saved synthetic
assessments/facts. Approval selects the original minimum-cost plan explicitly.

Expect one `evaluation-<UUID>.json` and 32 fresh PDF artifacts per completed
workload. Every HTTP/transport/validation/partial solver outcome remains in that
report; dependents remain explicitly unattempted after failure. Ambiguous POST/
first-PDF outcomes stop that workload without automatic retry. Failed warm-ups
stop before measurement. Inspect the saved path/key/payload before manual
recovery; a new execution uses fresh keys and does not erase old evidence.

For each operation/workload, nearest-rank p95 includes all timed measured
attempts; warm-ups remain separate. PASS requires all 30 successful/timed
operations and the fixed target. Creation and each stress target 5 s; stored
GET/replay/approval/cached PDF 1 s; first PDF 3 s. Shared 30 s MILP budget and
45 s HTTP safety timeout remain unchanged. A quick error or missing sample
cannot pass. HTTP timings exclude offline training, startup, local validation,
checkpoint IO and browser display time. First PDF means a fresh artifact in a
warmed process. Do not run competing test/solver workloads during measurement.

## Separate fixed live Odoo reproduction

Keep this out of the synthetic latency summaries. Reuse the already configured
read-only quotation identity and group 2. Start the existing Odoo/db containers
without recreating fixtures or removing volumes. If Windows forwarding is
unavailable, use the documented temporary localhost SSH tunnel and set only the
process's `ODOO_BASE_URL`. Confirm the original fixture through read-only checks.

```powershell
$taskLive = Join-Path $taskRoot 'live-odoo'
if (Test-Path $taskLive) { throw 'Use a new live preparation directory' }
python -m tools.t15_odoo_demo prepare --directory $taskLive --group-id 2
```

This reads fixed quotations and prepares a matching **synthetic** model offline;
it does not import Odoo receipts. Stop only the harness-owned API, change its
trusted model directory to `$taskLive/model`, and restart it against the same
disposable evidence database. Preserve the existing token. Then run the existing
[full-flow demonstration](T17_FULL_FLOW_DEMO.md):

```powershell
python -m tools.t17_demo run --directory $taskLive `
  --base-url http://127.0.0.1:8002 `
  --actor 'T18 controlled evaluation buyer' `
  --reason 'Explicitly select the saved lower-exposure alternative for evaluation.' `
  --no-award-reason 'Separate controlled No-award case; no purchase commitment.'
```

Expect a new `t17-run-<UUID>.json`, six scenario children (five types plus
infeasible demand 500), alternative approval/PDF and separate reasoned No-award.
Retain that report. For stored-only reopening, stop the owned API, unset its
trusted-model directory, stop only the Odoo services started by this exercise,
restart the API, and run:

```powershell
python -m tools.t17_demo reopen --report <saved-report-path> `
  --base-url http://127.0.0.1:8002
```

Expect unchanged saved cases/decisions, stored exact replays, identical PDF and
No-award PDF denial while Odoo is stopped and no model is configured. This is
HTTP acceptance, not a new Reflex/browser or unfamiliar-buyer usability result.

## Existing history/security gates and cleanup

T7-S/T8 projection checks have historical controlled PASS evidence. Their two
opt-in gates were disabled in prior runs. To rerun, reuse the existing fixture
and dedicated non-internal projection identity; enable `RUN_T7_LIVE_CONTRACTS`
and `RUN_T7S_LIVE_CONTRACTS` only in the test process. Missing/rejected credentials
remain explicit blocked validation; do not grant broader permissions, create
fixtures or waive the controlled-history obligation. If the existing short-lived
key needs renewal, the user performs [the manual procedure](T7S_MANUAL_SETUP.md#5-generate-the-dedicated-api-key).
Never put keys in reports/chat. Reset process flags afterwards; leave owner `.env`
settings unchanged unless the user updates them.

Preserve reports/PDFs and database readback before cleanup. Stop owned API children
and SSH tunnel; remove only this disposable Compose project using #26's cleanup.
Restore Odoo/container/machine running state only where this exercise changed it.
Remove generated secret files. Keep owner artifacts, Odoo volumes and retained
failed/historical evidence. [#27's handoff](T18_27_HANDOFF.md) records actual results
and limitations; these instructions alone are not PASS evidence.
