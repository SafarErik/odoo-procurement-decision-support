# Safe recovery and approved document access — #40

Use the [local service guide](LOCAL_DEVELOPMENT_AND_SSH.md) and
[saved-case prerequisites](UX32_LIBRARY_RUNBOOK.md). Reopening, finalization and PDF
access need Reflex, FastAPI and the migrated helper database containing the case,
with a matching server-side service token. They require no Odoo access or configured
model. Creating comparisons additionally needs the existing offline-prepared inputs
and matched model; scenarios reuse saved evidence and the existing solver.

## Recover a save

- **Inputs rejected** identifies a definitive validation response. Review the
  indicated terms. **Save conflict (HTTP 409)** identifies a reused key with different
  intent; copy **Last request for support**, including the response message, for the
  owner. Do not change inputs under that key. No raw server response or token appears.
- **Confirm the pending save before continuing** means the response is uncertain:
  the case/scenario/decision may already exist. Navigation and edits remain guarded.
  **Retry the same request** is an explicit resend of the original URL/payload/key,
  not a new intent or automatic retry. A failed recovery retains that exact record.
- **Copy recovery record before leaving** exposes the original intent without the
  service token. Recovery is session-local. A closed/lost Reflex session or server
  restart can lose it; copying JSON is support evidence, not an automatic restore.
  There is no durable outbox, import workflow or global multi-tab coordination.
- A finalization **Decision conflict (HTTP 409)** pauses decision actions and offers
  **Reopen saved decision**. This sends a GET only. Failed access or a response without
  a recorded decision keeps the current context and recovery proof; contact the owner
  about the conflicting key. A recorded outcome replaces the stale decision form.
  It may belong to another actor; review its terms rather than assuming your approval
  succeeded. An uncertain intent is released only after the stored decision is read.
- **Planning data is unavailable** on opening offers explicit **Load stored case**
  recovery. The failed opening clears stale case content; retry reads stored work.

## Use an approved document

1. Reopen an approved original. **Saved approved terms** shows its recorded product,
   demand, required date, exact cost and all supplier quantities/promised dates.
   Practice and synthetic/actor/operational limitations remain visible in access
   context. The label does not rewrite or watermark the immutable document.
2. **View approved PDF** retrieves the existing approved hash/reference. The viewer
   renders one page at a time. **Previous PDF page** / **Next PDF page** announce the
   page and disable at the ends. These controls work with keyboard focus and Enter.
3. **PDF zoom** offers Fit width, 150%, 200% and 300%. Large pages scroll within the
   labelled keyboard-focusable document region. This changes viewing scale only;
   browser text zoom is a separate accessibility check.
4. **Download approved PDF** saves the exact backend artifact, including every page.
   A backend/PDF failure leaves selection, approval, saved terms and Audit accessible.
   **Retry approved PDF** retries document GET only. **Document identity for support**
   supplies the original case and approved content hash. Do not approve again.

No-award, undecided bases and analytical children retain their existing PDF
ineligibility. No Odoo order is created. The backend renderer/content/hash/bytes and
decision persistence contracts are unchanged.

## Verify and clean up

Activate the documented project-local Python 3.11 frontend/dev/e2e environment.
Chromium and Node must already be installed. For browsers, use the existing running
Podman machine and documented Compose provider. Create a fresh artifact parent:

```powershell
$recoveryRun = Join-Path '.artifacts' ('ux40-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$recoveryRun/cache" -Force | Out-Null
python -m pytest tests/test_decision_confirmation.py tests/test_t17_frontend.py `
  tests/test_t21_documents.py tests/test_workspace_navigation.py `
  tests/test_t16_stored_planning.py -v --basetemp "$recoveryRun/focus" `
  -o "cache_dir=$recoveryRun/cache" --junitxml "$recoveryRun/focus.xml"
python -m pytest tests/e2e/test_planning_smoke.py `
  tests/e2e/test_recovery_documents_browser.py -m e2e -v -s `
  --basetemp "$recoveryRun/browser" -o "cache_dir=$recoveryRun/cache" `
  --junitxml "$recoveryRun/browser.xml"
```

The first command checks exact lost-response replay, definitive/recovering conflicts,
unavailable/no-record GET guards, frozen review, token privacy, unchanged saved
approval and PDF integrity/eligibility. The browser commands own fresh helper
PostgreSQL, offline synthetic preparation, actual CBC, FastAPI, Reflex and Chromium.
They stop the owned API for genuine GET/create/scenario/finalization/PDF faults;
explicitly replay the original intents; verify one child/decision and unchanged
stored content; render/navigate/download the PDF; verify narrow layout, non-Latin
long supplier labels, keyboard focus and native 200% browser zoom. A fresh isolated
browser context checks that pending recovery does not transfer to a new session.
No owner or Odoo database is reset. The native zoom extension belongs to the test's
temporary Chromium profile, not the user's browser.

Expected: both commands pass without skipped runtime gates. Fixtures close their
owned browser contexts/processes/tunnels and remove only their disposable Compose
project; inspect each retained `evidence.json` for cleanup. Close a built-in preview
tab and reset its viewport while its frontend is still running, then stop that owned
preview. Keep the shared Podman machine running. Retain logs/traces/JUnit/screenshots
for review. Required full fast/static/pip/Compose checks remain in the local guide;
hosted CI and human reassessment are separate gates.

The [dated handoff](UX40_RECOVERY_HANDOFF.md) records executed scope, failures and limits.
