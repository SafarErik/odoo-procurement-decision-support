# Repeatable three-supplier HTTP evaluation — #26

**2026-10-11 continuation:** #27 extends the current evaluator to six workloads
and all stress types. The default preparation still produces 3 suppliers/1
epsilon, but current `run` executes 12 operations. The seven-operation results
below and in [#26's handoff](T18_26_HANDOFF.md) remain historical evidence from
the #26 implementation. Use [#27's runbook](T18_27_EVALUATION_RUNBOOK.md) for the
current measurement contract and supported matrix.

This procedure measures fresh synthetic creation, supplier outage, explicit
minimum-plan approval, stored GET, exact creation replay, first PDF and cached
PDF through actual FastAPI/CBC/helper PostgreSQL. It is the first T18 evaluation
slice, not the six-workload assessment, live Odoo acceptance or browser usability.
See [specification](T18_EVALUATION_SPEC.md), [initial evidence inventory](T18_EVIDENCE_MATRIX.md)
and [executed handoff](T18_26_HANDOFF.md).

## Contract and measurement meaning

- Fixed workload: 3 suppliers, one requested 10% epsilon, demand 10; separately
  synthetic T14 history/model. Reuse the prepared T15 fixture and its validity
  ranges 1–1000. The saved date is a simulation reference, not today's forecast.
- Two complete warm-up flows followed by 30 measured attempts per operation.
  Use fresh creation/scenario/approval keys and the original creation key/payload
  for exact replay. Warm-ups are retained separately and excluded from summaries.
- Local observed p95 targets: create/outage ≤5 s; approval/stored GET/exact replay/
  cached PDF ≤1 s; first PDF ≤3 s. These are descriptive PoC targets, not SLAs.
- Measure client request/response wall time including API/DB/solver and full body
  transfer, excluding response validation and evidence-file IO. Offline training,
  service startup, process cold start and browser task/display time are not HTTP
  measurements. A first PDF is a fresh artifact in an already warmed process.
- Report median, nearest-rank p95 and maximum. For 30 timed attempts p95 is the
  29th sorted latency. Include timed failures; separately count outcomes, pending
  requests, missing timings and unattempted operations. A fast error cannot pass
  the gate. Incomplete samples/any unsuccessful operation/missed target fail it.
- Unknown POST/first-PDF outcomes stop the exercise without automatic retry.
  Failed warm-ups also stop it before measurement. Definite measured-run failures
  leave dependent operations unattempted and remain in the report; later distinct
  attempts are not retries of that failed request. Do not hide them in averages.

## Prerequisites and isolation

Activate the existing Python 3.11 environment as described in
[the terminal runbook](LOCAL_DEVELOPMENT_AND_SSH.md). Existing `.[frontend,dev]`
dependencies include everything needed; no new package or frontend process is
required. Odoo need not run. The backend must use the exact prepared model below.

Use the existing Podman machine. Follow [the persistence guide](PERSISTENCE_DEVELOPMENT.md)
for Compose/provider setup and isolation principles. Choose a new project name
and unused localhost ports. This example uses 55435 for PostgreSQL, 55436 for
the optional SSH forwarding workaround, and 8002 for FastAPI. Verify they are
unused; do not replace an existing application/test/demo service or its data.
The Compose service has no named volume. Never reset or migrate an Odoo database.

## Terminal 1: prepare offline and start the task's database/API

Run from the repository root in an activated environment. Preparation refuses
an existing directory; earlier owner artifacts and default frontend previews
are preserved. The random suffix identifies this disposable exercise.

```powershell
$taskSuffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
$taskDirectory = Join-Path ".artifacts" ("t18-26-" + $taskSuffix)
$taskProject = "procurement-t18-26-" + $taskSuffix
python -m tools.t18_evaluation prepare --directory $taskDirectory

$env:T11_POSTGRES_DB = "decision_cases_test"
$env:T11_POSTGRES_USER = "t11_test"
$env:T11_POSTGRES_PASSWORD = [guid]::NewGuid().ToString("N")
$env:T11_POSTGRES_PORT = "55435"
$env:T12_TRUSTED_CALLER_TOKEN = [guid]::NewGuid().ToString("N")
@{
    token = $env:T12_TRUSTED_CALLER_TOKEN
    project = $taskProject
} | ConvertTo-Json | Set-Content (Join-Path $taskDirectory "local-session.json")
podman compose -p $taskProject -f infra/persistence/compose.test.yaml up -d
podman compose -p $taskProject -f infra/persistence/compose.test.yaml ps
```

Expect offline model/dataset and matching request files, then a healthy
task-owned `decision-db`. The token file is ignored local configuration, not
an evaluation artifact to publish. Keep the existing Podman machine's prior
state for cleanup. No training occurs during the later HTTP flow.

If Windows forwarding works, use port 55435 below. If it fails while the
container is healthy, open a separate terminal for this localhost-only tunnel:

```powershell
$taskMachine = (podman machine inspect podman-machine-default | ConvertFrom-Json)[0]
ssh.exe -i $taskMachine.SSHConfig.IdentityPath -p $taskMachine.SSHConfig.Port -N `
  -L 127.0.0.1:55436:127.0.0.1:55435 `
  "$($taskMachine.SSHConfig.RemoteUsername)@127.0.0.1"
```

Keep that terminal open and use host port 55436 instead. In terminal 1:

```powershell
$taskDbHostPort = "55435" # Use 55436 only when the tunnel above is running.
$env:DECISION_DATABASE_URL = "postgresql+psycopg://t11_test:$env:T11_POSTGRES_PASSWORD@127.0.0.1:$taskDbHostPort/decision_cases_test"
$env:T15_TRUSTED_MODEL_DIRECTORY = (Resolve-Path (Join-Path $taskDirectory "model")).Path
python -m alembic upgrade head
python -m alembic current
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

These migrations target only the newly identified disposable helper database;
expect revision `20261010_01`. Uvicorn remains in the foreground. Do not run
schema-resetting integration fixtures while this API uses the database.

## Terminal 2: check readiness and measure

Activate the same Python environment. Substitute the exact directory printed
by preparation; existing terminals do not share environment variables.

```powershell
$taskDirectory = ".artifacts/t18-26-REPLACE_WITH_SUFFIX"
$taskSession = Get-Content (Join-Path $taskDirectory "local-session.json") -Raw | ConvertFrom-Json
$env:T12_TRUSTED_CALLER_TOKEN = $taskSession.token
Invoke-RestMethod http://127.0.0.1:8002/api/v1/health
python -m tools.t18_evaluation run --directory $taskDirectory --base-url http://127.0.0.1:8002
```

Health should say `ok`; it proves API readiness, not model/database acceptance.
The real workflow proves those next. Expect 32 lines of seven successful
operations and a unique `evaluation-<uuid>.json`, with one local PDF per completed
flow. The default fixture's minimum is EUR 102, alternative EUR 109 and outage
minimum EUR 106. Approval selects the saved minimum explicitly for this technical
exercise, not a live order. The cached PDF must have identical bytes/reference.

The command exits zero only when both warm-ups succeed and all measured
operation gates pass. Otherwise inspect `summary`, `attempts` and `stopped`.
Each POST's exact path/payload/key is atomically checkpointed before sending.
Response evidence retains IDs/hashes, solver/result outcomes and approval audit
without duplicating full saved snapshots; complete response equality is checked
in memory. Raw timings, failures, model/dataset/policy/input hashes, evaluator
hash, git SHA/working-tree state, client/solver versions and hardware are retained.
The bearer token and database URL are excluded.

An interrupted report can contain `pending` with no reliable elapsed time. It
is incomplete evidence, not a successful sample. Recover the saved exact intent
against this same database/API using the documented
[explicit retry procedure](LOCAL_DEVELOPMENT_AND_SSH.md#controlled-planning-workspace-create-and-test).
Do not rerun `run` to recover an unknown write: it creates fresh distinct cases.
There is no automatic resume/retry feature or hidden target relaxation.

## Verification and cleanup

Focused check: `python -m pytest tests/test_t18_evaluation.py -v`, using a fresh
workspace temp/cache directory as in the terminal runbook. Tests cover reporting,
transport/HTTP failures, owner-artifact preservation and actual inference/CBC/
PDF through the API with memory persistence. They do not prove PostgreSQL or
network latency; the served HTTP exercise does. Required fast gates remain in
AGENTS.md. Browser/live-Odoo evaluation belongs to later T18 tickets.

Preserve desired report/PDF evidence, then stop this foreground API with Ctrl+C.
Stop its SSH tunnel if used. In terminal 1, remove only this exercise's service:

```powershell
podman compose -p $taskProject -f infra/persistence/compose.test.yaml down
Remove-Item -LiteralPath (Join-Path $taskDirectory "local-session.json")
Remove-Item Env:T12_TRUSTED_CALLER_TOKEN, Env:T15_TRUSTED_MODEL_DIRECTORY, Env:DECISION_DATABASE_URL, Env:T11_POSTGRES_PASSWORD, Env:T11_POSTGRES_USER, Env:T11_POSTGRES_DB, Env:T11_POSTGRES_PORT -ErrorAction SilentlyContinue
```

`down` discards this disposable database after the API stops; it does not affect
Odoo/application volumes. Stop the Podman machine only if this exercise started
it from a stopped state and no other work now uses it. Keep desired model/report
evidence; do not delete the `.artifacts` root or default prepared owner data.

Results establish only the measured 3-supplier/1-epsilon controlled synthetic
HTTP scope on the recorded local runtime. Other workloads, all stress types,
live Odoo, concurrent-load performance, browser smoke and unfamiliar-participant
usability retain their own gates. Approval attribution is not buyer authentication,
synthetic exposure is not calibrated risk and the PDF does not create an Odoo PO.
