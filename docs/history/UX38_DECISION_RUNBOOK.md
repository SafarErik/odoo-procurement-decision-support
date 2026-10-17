# Deliberately approve or record No-award — #38

Use the [local services guide](LOCAL_DEVELOPMENT_AND_SSH.md) and
[saved-case prerequisites](UX32_LIBRARY_RUNBOOK.md). An existing saved original
needs only FastAPI, its helper database and Reflex with the matching server token.
No Odoo access, configured model, training, migration or new dependency is required
for review, finalization, retrieval or document access.

## Review, cancel or confirm

1. Open an undecided original. **Select for review** identifies a saved plan but
   writes nothing. **Review decision** focuses the final-decision form. Its
   **Saved plan for approval** selector remains synchronized with the comparison.
2. Enter **Actor audit reference** and **Reason**, then acknowledge the controlled
   demonstration/synthetic evidence. A reason is required for an alternative;
   minimum-cost approval permits no reason. Actor attribution is caller-supplied
   audit text, not authenticated buyer identity. The existing backend also validates
   these rules independently.
3. **Review approval** opens **Confirm approval** without saving or allocating a
   request key. Read the original UUID, product/demand/unit/currency, required and
   captured dates, source, exact selected index/cost/allocations/promised dates,
   exposure, actor and reason. Exposure is an uncalibrated synthetic proxy. Practice
   shares application storage; this is not an isolated exercise database.
4. **Cancel** or Escape returns to the form with entered values and selection
   retained. Neither action creates a final decision. The dialog starts with safe
   Cancel focus, contains keyboard focus, and returns it to the review button.
   On narrow screens, the exact review scrolls inside the dialog while actions stay
   visible. The final confirmation sends the frozen reviewed payload once.
5. **Confirm approval** records an immutable original-base decision through the
   existing API. The saved outcome receives focus; its selected plan, actor, reason
   and UTC record time replace editable controls. No Odoo order is created.
   **View approved PDF** and the existing viewer/download continue to use the
   backend's exact approved document. Document failure does not undo approval.
6. To decline, use the separate **Record No-award** action. No allocation is selected
   for approval. Enter actor and a required reason, acknowledge the demonstration,
   then **Review No-award** and **Confirm No-award**. Cancel remains read-only.
   **Choose a plan instead** returns to explicit plan selection before review.
   A saved No-award is immutable and has no approved-plan PDF.

Scenario children remain analytical: their UI offers no approval/No-award controls,
and the backend independently rejects finalization. Return to the original or
create a newly confirmed base when operational terms change. Reopening retrieves
the recorded decision without rereading quotations, rescoring or optimizing.

If the response is uncertain, **Confirm the pending save before continuing**
receives focus. Keep the original URL/payload/key from **Copy recovery record before
leaving**. Navigation and editing remain guarded; **Retry the same request** explicitly
replays that exact intent. Do not create a replacement request to guess whether
approval succeeded. Recovery is session-local, not a durable outbox. A definitive
conflict requires reopening the stored outcome; there is no overwrite action.

## Verification and cleanup

Prerequisites: documented Python 3.11 frontend/dev/e2e environment, Chromium,
Node PATH, existing running Podman machine and the local Compose provider. Create
a fresh workspace artifact parent before pytest:

```powershell
$decisionRun = Join-Path '.artifacts' ('ux38-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$decisionRun/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/test_decision_confirmation.py tests/test_t17_frontend.py `
  tests/test_plan_comparison.py tests/test_workspace_navigation.py `
  tests/test_t16_stored_planning.py -v --basetemp "$decisionRun/temp" `
  -o "cache_dir=$decisionRun/cache" --junitxml "$decisionRun/result.xml"

$decisionBrowser = Join-Path '.artifacts' ('ux38-browser-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$decisionBrowser/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/e2e/test_decision_confirmation_browser.py tests/e2e/test_planning_smoke.py `
  tests/e2e/test_curated_practice_browser.py `
  tests/e2e/test_plan_comparison_browser.py -m e2e -v -s `
  --basetemp "$decisionBrowser/temp" -o "cache_dir=$decisionBrowser/cache" `
  --junitxml "$decisionBrowser/result.xml"
```

The first command checks read-only review/cancel, frozen payload, stale-context and
child guards, required reasons, exact lost-response replay and existing selection/
retrieval/navigation. The browser owns disposable helper PostgreSQL, FastAPI,
Reflex/Chromium and any localhost tunnel. It prepares trusted synthetic inputs
offline and uses real CBC/HTTP/storage. Expected: alternative confirmation/cancel,
long/narrow review, safe focus, one-save double-click, immutable reopening, separate
reasoned No-award, actual API-outage exact recovery, child UI/API rejection and
existing Practice/approval/PDF flows pass. Stored work then runs model-unconfigured.

For real transaction/content integrity, use the [isolated persistence procedure](PERSISTENCE_DEVELOPMENT.md)
with a new uniquely named Compose project, unused port and separate synthetic
credentials. Verify ownership before setting `T11_TEST_DATABASE_URL`; these fixtures
reset schema/data and must never target application or Odoo storage. Run:

```powershell
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/integration/test_t17_decisions_postgres.py `
  tests/integration/test_t21_documents_postgres.py -v `
  --basetemp "$decisionRun/postgres-temp" -o "cache_dir=$decisionRun/cache" `
  --junitxml "$decisionRun/postgres-result.xml"
```

Expected: actual contending decisions, conflict/idempotency, immutable content,
rollback, exact PDF binding and render-once protection pass without skips. No API
server or Reflex is needed for this TestClient selection. Browser fixtures stop
their owned processes/tunnels and remove only their Compose projects. For manually
started persistence, use the guide's matching project cleanup and clear the test
URL afterward. Retain artifacts and existing owner services/data. Run the required
AGENTS.md fast/static gates before handoff; actual Reflex startup checks compilation.
See the [dated handoff](UX38_DECISION_HANDOFF.md) for executed evidence and limits.
