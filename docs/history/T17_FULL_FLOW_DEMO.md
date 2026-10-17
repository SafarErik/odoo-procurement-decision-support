# Complete controlled procurement-to-approved-PDF demonstration

This is the #22 / AC-V2-13 reproduction procedure. It uses the existing read-only
Odoo comparison, offline synthetic Decision Tree, CBC, helper PostgreSQL and Reflex.
It is a controlled technical demonstration, not operational supplier validation.
See [the dated acceptance handoff](T17_FULL_FLOW_HANDOFF.md) for executed evidence.

## Prerequisites and isolation

- Activate the project-local Python 3.11 environment and install `.[frontend,dev]`
  using [the terminal runbook](LOCAL_DEVELOPMENT_AND_SSH.md).
- Reuse the existing Podman machine and Odoo stack. The three T6 quotations must
  already match [the manual fixture](T6_FIXTURE_SETUP.md), group 2. Its Odoo prices
  are A/B/C = USD 10/12/9, suppliers 51/52/53, product 54, company 1, unit 1 in the
  accepted local fixture. Independently verify actual IDs; do not recreate records.
  Missing/different records require the documented human setup and confirmation.
- Keep read-only Odoo credentials in ignored `.env`. No Odoo UI automation,
  writes or direct Odoo database access is used here.
- Use a deliberately separate helper database. Follow [persistence setup](PERSISTENCE_DEVELOPMENT.md)
  with an unused project/port, for example `procurement-decision-support-t17-demo`
  and `T11_POSTGRES_PORT=55434`. Do not reset any application/Odoo database.
  Run resetting service tests before the manual demonstration, not while keeping
  its cases. Preserve an existing demo database unless explicitly disposable.
- Export `DECISION_DATABASE_URL` for that helper database and run
  `python -m alembic upgrade head`; expect `20261010_01`. A missing migration is
  not fixed by frontend startup. See the Windows SSH workaround if host forwarding
  fails; keep the tunnel localhost-only and use its actual port in the helper URL.

## Prepare offline, then start only the needed services

Stop an earlier API using the default demo artifact before preparation:

```powershell
python -m tools.t15_odoo_demo prepare --group-id 2
$env:T15_TRUSTED_MODEL_DIRECTORY = (Resolve-Path .artifacts/t15-odoo-demo/model).Path
$env:T12_TRUSTED_CALLER_TOKEN = [guid]::NewGuid().ToString("N")
Set-Content .artifacts/t15-odoo-demo/caller-token.txt $env:T12_TRUSTED_CALLER_TOKEN -NoNewline
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Preparation reads the quotation expectations and trains/saves synthetic history
offline. It overwrites only the ignored default demo artifacts; back up any earlier
specimen you want to keep. The backend independently rereads supported Odoo facts
on each fresh `/from-odoo` creation. HTTP and Reflex never train a model.

In another activated terminal, load the same token and start Reflex:

```powershell
$env:T12_TRUSTED_CALLER_TOKEN = Get-Content .artifacts/t15-odoo-demo/caller-token.txt -Raw
$env:BACKEND_BASE_URL = "http://127.0.0.1:8000"
Push-Location frontend
../.venv/t13-check/Scripts/reflex.exe run --backend-host 127.0.0.1
Pop-Location
```

Open `http://localhost:3000/planning`. The API and Reflex token must agree; do not
paste it into the browser or a report. For isolated acceptance, consistently choose
unused API/frontend/Reflex ports and set `BACKEND_BASE_URL` to the selected API.

## Buyer walkthrough and expected outcomes

1. Choose **Odoo -> Load prepared Odoo comparison**. This loads a captured preview,
   not fresh Odoo data. Review demand 200, capacity 120/100/160, MOQ 50/100/150,
   current prepared required/promised dates, max suppliers 2, concentration 80%,
   epsilon 20%, and applicability 1–1000. Choose **Create and save Odoo plan**.
   The backend now independently reads Odoo and saves the assembled result.
2. **Plans:** minimum USD 1,850 with A/B/C = 50/0/150; alternative USD 2,200 with
   100/100/0. Its USD 350 premium reduces synthetic exposure from 75 to 48.305
   on the 0–100 display scale. Copy the original base ID. **Suppliers/Audit**
   distinguish actual quotation facts, explicit terms and generated ML history.
3. **What-if:** run each row below. Every child must refer to the original base,
   including when launched while viewing another child. They are independent
   experiments, not cumulative modifications or Odoo updates.

| Type | Input | Expected minimum |
| --- | --- | --- |
| Supplier outage | Supplier C unavailable | USD 2,200; 100/100/0 |
| Capacity reduction | Supplier C capacity 100 | USD 2,200; C's MOQ still prevents selection |
| Demand increase | Demand 250 | USD 2,340; 90/0/160 |
| Price increase | Supplier C price 13 | USD 2,200; simulated price, not a new Odoo fact |
| Combined | Demand 220; C capacity 150 and price 10 | USD 2,200; 70/0/150 |
| Infeasible demand | Demand 500 | No feasible plan; no fabricated cost/allocation |

Demand comparisons must retain the different-quantity warning. Open a child's
**Plans** view: it cannot be finalized or receive an approved procurement PDF.

4. Choose **View base case**, then explicitly select **Alternative 1**, enter an
   actor audit reference and a reason, acknowledge the controlled demonstration,
   and choose **Finalize this base**. This is immutable, technical approval;
   the actor is supplied audit text, not authenticated buyer identity.
5. Copy the approval time, reopen that base with **Load stored case**, then choose
   **View approved PDF -> Download approved PDF**. Inspect the saved allocation,
   exact USD 2,200 total, approved-content hash, provenance and human audit. Match
   downloaded bytes/hash to the stored artifact where doing acceptance inspection.
6. Create a separate original base with the same prepared terms. Explicitly select
   **No-award**, supply its own reason and acknowledgment, and finalize it. Reopen:
   the outcome/time remain saved and there is no approved-PDF action.

## Repeatable HTTP evidence and exact stored reopening

The CLI is a separate technical exercise; it creates its own two bases and six
children. Explicit actor and separate outcome reasons are required. It does not
replace the buyer's browser walkthrough or automatically finalize browser cases.

```powershell
$env:T12_TRUSTED_CALLER_TOKEN = Get-Content .artifacts/t15-odoo-demo/caller-token.txt -Raw
python -m tools.t17_demo run --actor "Controlled demonstration buyer" --reason "Prefer lower saved synthetic exposure." --no-award-reason "No purchase authorized in this separate demonstration."
```

Expect HTTP 201 creation/finalization, stored GET, exact HTTP 200 replays, a
matching downloaded PDF and HTTP 422 No-award PDF denial. The tool prints a
`.artifacts/t15-odoo-demo/t17-run-<uuid>.json` report path, with its matching PDF.
It records request/key **before** every POST and actual per-operation/flow seconds;
the token is never recorded. There is no automatic retry. If interrupted, inspect
that report and explicitly replay the pending operation's saved path/payload/key
against the same loopback API using [the recovery procedure](LOCAL_DEVELOPMENT_AND_SSH.md#controlled-planning-workspace-create-and-test).
Do not rerun `run` as a substitute for recovering an uncertain operation: it makes
new cases. `reopen` requires a completed report.

Stop FastAPI, keep helper PostgreSQL/Reflex running, then restart without a model:

```powershell
$env:T15_TRUSTED_MODEL_DIRECTORY = ""
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Stop only the Odoo service started for this exercise if no other user depends on
it; retain its data/volumes. In another terminal, substitute the printed report:

```powershell
python -m tools.t17_demo reopen --report .artifacts/t15-odoo-demo/t17-run-<uuid>.json
```

Expect identical snapshots, final decisions/times and PDF bytes, with Odoo stopped
and the model unconfigured. Browser reopening/PDF must also work. Missing upstream
sources affect fresh creation, not saved evidence. The fast test in
`tests/test_t17_demo.py` additionally forbids acquisition, inference, optimization
and rendering during these exact stored operations.

## Controlled renderer and backend failure acceptance

For deliberate renderer failure, use this local acceptance-only composition root.
Save it as ignored `.artifacts/t17-demo/acceptance_app.py`, stop normal FastAPI and
start it with `uvicorn acceptance_app:app --app-dir .artifacts/t17-demo` on the
same API port. It changes no production source or persistence rules:

```python
from pathlib import Path
from backend.app.main import app
from backend.app.routes import planning_cases as routes

root = Path(__file__).parent
original = routes.render_approved_document


def controlled_render(content):
    if (root / "render-failure").exists():
        raise RuntimeError("Controlled acceptance renderer failure")
    return original(content)


routes.render_approved_document = controlled_render
```

Create `render-failure` before the **first** PDF request for an approved case;
already stored artifacts intentionally bypass the renderer. Expect safe HTTP 503,
retained approval/time and no download link. Remove only that marker and explicitly
choose **View approved PDF** again; content identity/time must stay unchanged.
Now stop the acceptance API, request the PDF again, and confirm retained approval
with a safe unavailable message. Restart at the same port and explicitly retry:
the stored document must display. Use only development cases and restore the
normal composition root afterward. #22's handoff also records live forbidden-call
sentinels across the model-unavailable restart; these are evidence instrumentation,
not production settings.

## Verification and cleanup

Run required fast checks from AGENTS.md. Run
`pytest -m "integration and not e2e" -v` only with its documented services and
explicitly disposable `T11_TEST_DATABASE_URL`; this resets the test database.
Opt into T6 fixture contracts only after verifying that fixture. Record separate
browser, service, skipped and hosted results. Do not reset a database while using
it for the walkthrough or retaining cases for review.

Stop task-created API/Reflex/tunnel processes. Bring down only the named disposable
helper project; this discards its cases, so save evidence first. Stop Odoo containers
only if started for the exercise and restore the machine's initial state when no
other work depends on it. Never remove Odoo volumes. Remove the ignored caller-token
file and clear process overrides. Keep model/report/PDF evidence as desired;
restore any default preview/artifact backup you temporarily replaced.

The milestone is a reproducible controlled AC-V2-13 demonstration. It does not
establish observed-model promotion, calibrated supplier risk, business savings,
production buyer authentication, legally complete Purchase Orders, final T18
evaluation or complete thesis acceptance. Drive synchronization follows user review
and a separate green light; this procedure edits no Drive document.
