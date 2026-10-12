# Responsive buyer workspace — #34

Use the existing [local service runbook](LOCAL_DEVELOPMENT_AND_SSH.md),
[library prerequisites](UX32_LIBRARY_RUNBOOK.md) and
[Practice preparation](UX33_PRACTICE_RUNBOOK.md). This increment adds no backend
route, migration, dependency or Odoo operation. Library company scope and the
Reflex server's service token remain owner configuration.

## Enter, navigate and protect work

1. Open `/cases` for the buyer workspace. Cases, Open RFQs and Practice are real
   destinations in the green navigation rail. `/` remains the compatible read-only
   RFQ ledger entry; `/planning` remains the existing comparison entry.
2. At narrow widths, use **Workspace menu**. Tab through its labelled destinations;
   Escape or Close menu returns focus to the menu button. No RFQ action converts
   arbitrary quotations into a planning case.
3. Filter and open a saved case. Product, exact demand/unit/currency, required date,
   source, cutoff/save dates, original-base identity and decision/solver status
   precede help. Plans, What-if, Suppliers and Audit update the bookmarkable URL;
   opening a bookmark only retrieves stored data. Invalid/missing IDs or invalid
   views clear the preceding case and show a safe error.
4. Loading a prepared creation input, editing a creation field, or changing a
   scenario marks an unsaved draft. App navigation, case/view/input changes,
   replacement preparation and Practice selection offer **Stay / Discard draft**.
   Stay retains values; Discard clears the creation/scenario draft before the
   requested navigation. Saved cases are not deleted.
5. An uncertain write has no Discard action. Use **Retry the same request** in its
   original recovery context. Direct route attempts return there without replacing
   the exact payload/key. Copy the recovery record before closing the session;
   durable closed-session recovery and multi-tab coordination are outside scope.
6. Audit tables retain exact values and named keyboard-focusable scroll regions.
   The shell reflows at tablet/phone widths and suppresses transitions under reduced
   motion. Help and compatible open/create controls remain below saved results.

## Verify locally

Prerequisites: Python 3.11 with existing frontend/dev/e2e extras, matching Chromium,
working Node, and the existing running Podman machine. Set the documented Compose
provider and local Node PATH only in this terminal, if needed. Then:

```powershell
$workspaceRun = Join-Path '.artifacts' ('ux34-browser-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$workspaceRun/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/e2e/test_workspace_browser.py tests/e2e/test_curated_practice_browser.py `
  tests/e2e/test_planning_smoke.py -m e2e -v -s `
  --basetemp "$workspaceRun/temp" -o "cache_dir=$workspaceRun/cache" `
  --junitxml "$workspaceRun/result.xml"
```

This starts only owned, uniquely named disposable helper PostgreSQL, FastAPI,
Reflex and Chromium instances. It prepares synthetic assets offline; Odoo is
unconfigured. Expected: navigation/draft/pending recovery, Practice and existing
approval/PDF workflows pass. Each stack removes its own processes, tunnel and
Compose project in fixture cleanup; preserve logs, traces, screenshots and failures.
Never point database-reset checks at application or Odoo storage.

The workspace check launches an additional owned Chromium profile with a tiny
test-only extension calling native `chrome.tabs.setZoom(..., 2)` and confirming
`getZoom() == 2`, doubled devicePixelRatio and the reduced CSS viewport. This is
actual browser enlargement, not CSS scaling or PDF zoom. The profile is closed in
`finally`; no extension is installed into the owner's browser. See
[Chrome's tab zoom API](https://developer.chrome.com/docs/extensions/reference/api/tabs)
and [Playwright's extension runtime](https://playwright.dev/python/docs/chrome-extensions).

Run focused navigation/client tests during changes and the required AGENTS.md fast
checks once before handoff. New list benchmarks and live Odoo are separate gates;
this frontend slice does not change those contracts. See the
[dated handoff](UX34_WORKSPACE_HANDOFF.md) for actual executed evidence and limits.
