# Find and reopen saved cases — #32

Use Python 3.11 and the existing FastAPI, Reflex and helper PostgreSQL setup in
[the local runbook](LOCAL_DEVELOPMENT_AND_SSH.md). Odoo, a model directory and CBC
execution are unnecessary for browsing/reopening saved results. This is a bounded
company library, not per-buyer authorization; compatible UUID retrieval keeps its
existing trusted-caller behavior.

## Configure and open

1. Back up the intended helper database using the owner's usual procedure. Export
   its `DECISION_DATABASE_URL` in this terminal, following
   [the migration guide](PERSISTENCE_DEVELOPMENT.md). Never select the Odoo database.
2. Run `python -m alembic upgrade head`. Expected revision: `20261012_01`. This adds
   an empty immutable catalog table and its workspace index. It does not rewrite,
   classify or delete old snapshots, decisions or PDF artifacts.
3. In the ignored `.env`, set `PLANNING_LIBRARY_COMPANY_ID` to the exact recorded
   `company_id` of the intended library. For the existing synthetic demo it is
   `synthetic-company`; use the saved Audit/API company identity for other cases.
   Keep `T12_TRUSTED_CALLER_TOKEN` configured on FastAPI and the Reflex server.
   The browser cannot choose company scope. Blank scope returns unavailable (503).
4. Start FastAPI with `uvicorn backend.app.main:app --reload`, and run `reflex run`
   from `frontend/`, in separate terminals. Restart the backend after scope changes.
   Open `/cases`, or choose Saved cases from `/` or `/planning`.
5. Select **Earlier cases** and Refresh to browse work saved without classification.
   Search recorded product identity or a case ID, optionally select decision status,
   and use Next cases. Show scenarios loads one bounded child page on demand; Next
   scenarios continues it. Open case/scenario retrieves its immutable saved result.
   The resulting `/planning?case_id=<UUID>&view=plans` URL can be bookmarked; allowed
   views are `plans`, `whatif`, `suppliers`, `audit`. Bad IDs/views clear stale results.

**2026-10-12 #33 extension:** new Reflex synthetic saves explicitly use Practice;
new prepared Odoo saves explicitly use controlled work. See the
[Practice runbook](UX33_PRACTICE_RUNBOOK.md). Existing records remain unclassified;
synthetic ML never automatically classifies an old case as Practice.
Product labels fall back to the recorded identity because snapshots contain no
authoritative business product name. Scenarios inherit their original's workspace;
their final-decision status belongs to the original, not to an invented child approval.
New comparison opens the existing cockpit and its prepared creation controls.

Empty/no-match views differ from service failures. Refresh recovers explicitly.
Collection reads never issue POSTs, refresh Odoo, load a model or rerun the solver.
Opening Cases/bookmarks while a write is pending preserves its exact payload/key and
returns to its original recovery route. This remains session-local recovery; closing
the session or restarting Reflex does not promise durable pending-intent recovery.

Stop the two owned terminal processes with Ctrl+C. No data cleanup is needed for
normal library use. Do not downgrade a populated catalog without reviewing metadata
loss; leaving the additive migration installed is the safe rollback for the UI.

## Collection HTTP contract

Both `GET /api/v2/procurement/planning-cases` and
`GET /api/v2/procurement/planning-cases/{original_id}/scenarios` require the service
bearer token. Parameters: `workspace=controlled|practice|unclassified` (default
controlled), `status=all|draft|approved|no_award` (default all), optional trimmed `q`
(80 characters maximum), `limit=1..50` (default 20), optional `cursor` (1024 characters
maximum). Unknown/repeated parameters and invalid/mismatched cursors return 422.
Missing/cross-company originals return 404; a child as a container returns 422.
Unavailable persistence/scope returns 503, and corrupt selected data returns explicit
`invalid_library_data` (503). Rows are ordered by UTC save time and case ID descending.

Pages return `items` and `next_cursor`; no total count or full snapshot/model/history
is sent. A continuation binds company, workspace, status, trimmed search, limit and
original container. New arrivals appear on refresh. Search is literal parameterized
product/ID text (including `%`/`_`), not supplier or arbitrary full-text discovery.
Status membership reflects current immutable decisions; finalizing a case can change
which filtered view contains it. A cursor is navigation data, not authorization.

## Disposable acceptance and query measurements

Follow [the browser prerequisites](T18_28_BROWSER_RUNBOOK.md): existing running
Podman machine, Compose provider, Python 3.11 frontend/dev/e2e extras, installed
Chromium and working Node. No owner API/frontend or Odoo service is required.

```powershell
$taskRun = Join-Path '.artifacts' ('ux32-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$taskRun/cache" -Force | Out-Null
python -m pytest tests/e2e/test_saved_library_browser.py -m e2e -v -s `
  --basetemp "$taskRun/temp" -o "cache_dir=$taskRun/cache" `
  --junitxml "$taskRun/result.xml"
```

This prepares the existing synthetic fixture offline, starts only uniquely owned
helper PostgreSQL/FastAPI/Reflex services, migrates the disposable database, inserts
1,000 original bases and 60 children, and adds one concurrent base after the first
page. Replication is a technical workload, not new ML/business evidence. Scope,
ordering/ties, status/product/ID filters, escaped searches, continuation failures,
stored-only reopening, 768/390/320 layouts and real backend failure/recovery are checked.
Six 20-row HTTP queries receive two warm-ups and 30 retained measurements each;
nearest-rank local p95 must be at most one second. `EXPLAIN (ANALYZE, BUFFERS)` plans
are retained. No extra snapshot indexes are added without evidence of need.

The run prints its unique `.artifacts/t18-browser-*` root. It retains service logs,
raw `library-timings.json`, screenshots, trace and `evidence.json`; failures and
cleanup outcomes remain visible. The corruption check disables the immutable-row
trigger only inside this owned disposable fixture, then checks fail-closed behavior.
Finally the owned processes/tunnel and Compose project are removed. Never redirect
this load/reset workflow at owner or Odoo storage. Existing integration tests also
reset storage: follow the disposable-only persistence guide before selecting them.

Run the existing approval/PDF/recovery regression separately with
`python -m pytest tests/e2e/test_planning_smoke.py -m e2e -v -s`, using another fresh
temp/cache/JUnit root. Required repository fast gates remain in AGENTS.md.
