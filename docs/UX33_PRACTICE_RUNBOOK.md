# Curated Practice and case classification — #33

Use the existing Python 3.11, helper PostgreSQL, FastAPI and Reflex setup. This
builds on [the library runbook](UX32_LIBRARY_RUNBOOK.md); revision `20261012_01`
already supplies catalog storage. #33 adds no migration or dependency. Never use
an Odoo database as helper storage. Configure the backend library company and
server-held service token before browsing.

## Prepare, enter and deliberately save

1. From the repository root, run `python -m tools.t15_demo prepare`. This prepares
   the existing matched synthetic input/model offline in `.artifacts/t15-demo`.
   It performs no API POST or database reset. Keep its simulation dates unchanged.
2. Set `T15_TRUSTED_MODEL_DIRECTORY` in the ignored `.env` to that prepared `model`
   directory, and retain `DECISION_DATABASE_URL`, `T12_TRUSTED_CALLER_TOKEN` and
   `PLANNING_LIBRARY_COMPANY_ID=synthetic-company` for the existing synthetic demo.
   A different controlled Odoo company needs its own owner-selected library scope;
   workspace filtering never expands company access.
3. Start `uvicorn backend.app.main:app --reload` at the root and `reflex run` from
   `frontend/`, in separate terminals. These start the HTTP API and frontend;
   creation requires the prepared trusted model and actual CBC, unlike stored GET.
4. Open `/practice`, or choose Practice from Saved cases or the cockpit. Choose
   Compare plans, Test a supplier outage, or Make a case infeasible. Entry/selection
   reads only the fixed prepared input and fills a fresh draft; it saves nothing.
   Choosing again after finalization never treats the finalized case as editable.
5. Press **Calculate and save fresh Practice case**. This explicitly creates a new
   real synthetic base with demand 10 pieces and immutable Practice classification.
   Open saved Practice case to compare exact allocations, costs and exposure.
6. For outage/infeasibility, press **Prepare exercise scenario**. This fills the
   existing What-if form without saving: one original supplier unavailable, or
   demand 25 for the prepared 24-unit-capacity example. Review the fields, then press
   **Create and save scenario** deliberately. The backend validates original-base
   assumptions and solves; no constraints are relaxed and no fake results supplied.
7. In Saved cases, select **Practice** and Refresh. Reopen your original and expand
   its saved scenarios. All source labels remain separate from workspace purpose.
   Practice stays visible in the case, decision review and document-access context.
   Approval/No-award remain deliberate and immutable; PDF downloads are the backend's
   exact saved bytes, with no frontend watermark or content rewrite.

Practice uses the same application storage and service authorization. There is no
isolated database, reset, automatic cleanup or operational-validity claim. New Demo
saves in the compatible cockpit also use Practice, without a curated example unless
explicitly chosen. New prepared Odoo UI saves use controlled work while their ML
history stays synthetic. Legacy callers omitting context remain unclassified.

If the backend response is uncertain, keep the original request/key. Retry the same
request explicitly after service recovery; exercise/case/navigation controls cannot
replace it. Recovery remains session-local, not a durable closed-session outbox.
Stop owned terminal processes with Ctrl+C. Ordinary use requires no data cleanup.

## API context and compatibility

Base creation accepts optional `catalog_context` separately from business facts:

```json
{"workspace": "practice", "example_id": "compare-plans"}
```

Synthetic `POST /api/v2/procurement/planning-cases` accepts only Practice; optional
example IDs are `compare-plans`, `supplier-outage`, `infeasible-demand`. The existing
`/from-odoo` route accepts only `{"workspace":"controlled"}` on the outer request;
no curated example or nested context is accepted there. Scenarios accept no override.
The server selects the creation path; claimed source/model/browser fields do not
grant another classification.

The case and catalog record commit atomically. Supplied context participates in the
creation fingerprint: changed/removed context under the same key conflicts. Omitted
or null context keeps the old fingerprint, and replay never adds/repairs metadata.
Get/create/scenario/final-decision responses add `workspace` and `example_id` outside
the immutable snapshot. Children read the original's metadata; missing metadata
means unclassified. Existing response fields and hashes remain unchanged. Catalog
purpose is not authority for demand, allocations, approval or PDF content.

## Disposable verification

Follow [the Chromium prerequisites](T18_28_BROWSER_RUNBOOK.md): Python 3.11
frontend/dev/e2e extras, Chromium, working Node and the existing running Podman
machine/Compose provider. No owner services, Odoo credentials or Odoo UI mutation
are needed for the synthetic acceptance task.

```powershell
$taskRun = Join-Path '.artifacts' ('ux33-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$taskRun/cache" -Force | Out-Null
python -m pytest tests/e2e/test_curated_practice_browser.py -m e2e -v -s `
  --basetemp "$taskRun/temp" -o "cache_dir=$taskRun/cache" `
  --junitxml "$taskRun/result.xml"
```

Expected: a passing real Reflex → FastAPI → owned disposable PostgreSQL test. It
checks no writes on entry/selection; three fresh bases; genuine outage/infeasibility;
Practice library reopening with model configuration removed; explicit alternative
approval and byte-identical PDF download; and exact uncertain-create retry with
blocked context changes. Keyboard entry, labels/focus and 1280/1440/768/390/320 reflow
are checked. The printed unique `.artifacts/t18-browser-*` root retains screenshots,
trace, service logs, PDF and evidence. Owned services/tunnel/project are removed.
Never redirect this workflow at owner/Odoo storage or clean their volumes.

The meaningful HTTP and real PostgreSQL classification tests are
`tests/test_practice_classification.py` and
`tests/integration/test_practice_catalog_postgres.py`. Integration/reset tests require
an explicitly disposable database using [the persistence guide](PERSISTENCE_DEVELOPMENT.md).
They cover rollback after insertion/before commit, post-commit ambiguity, exact
replay, concurrent calls, context conflict and original-child inheritance. Required
fast gates remain in AGENTS.md; hosted browser CI stays deferred.
