# Test disruptions against the original base — #37

Use the [local services runbook](LOCAL_DEVELOPMENT_AND_SSH.md) and
[library prerequisites](UX32_LIBRARY_RUNBOOK.md). Saved scenario work needs only
Reflex, FastAPI, helper PostgreSQL and the matching server-side service token.
No new route, migration, dependency, model or Odoo setup is introduced. Creating a
fresh base still requires its documented matching offline preparation.

## Draft, save and compare

1. Open a saved base or child and choose **What-if**. **Original base before
   disruption** or **Saved scenario comparison** shows the original UUID and exact
   feasibility, demand/unit, minimum cost, exposure fraction and supplier quantities.
   A child bookmark retrieves its original through the existing stored GET.
2. Choose **Scenario type**. Outage makes one original supplier unavailable;
   capacity reduction requires a smaller whole-number limit (zero is allowed);
   demand increase requires a larger demand; price increase requires a larger plain
   decimal price. Bounded combined changes require at least two of demand/capacity/
   price, with capacity/price applying to one supplier. Leave unused fields blank.
   Demand/capacity remain bounded to 1,000. Original terms stay the reference even
   when entering from another child; changes do not accumulate.
3. Read **Draft assumptions** and the original UUID. The base remains unchanged.
   **Create and save scenario** invokes the existing MILP scenario API with saved
   inputs/assessments; it acquires no new quotation or model evidence. Validation
   errors focus the alert. A successful save bookmarks the new child and focuses
   **Saved scenario comparison**. Saving resets the submitted draft fields.
4. Compare original/scenario/change columns in the named keyboard-scrollable
   region. The comparison uses the minimum-cost plans; Plans still offers the
   child's saved alternatives. An infeasible/incomplete child has **Unavailable**
   cost, exposure and quantities; the original remains visible. Zero is displayed
   only when it is a real saved allocation. Missing plans do not relax constraints.
5. Demand changes compare different totals, not like-for-like savings. Simulated
   prices are assumptions, not fresh quotations. Exposure remains an uncalibrated
   synthetic proxy. The header/source, class and parent lineage remain visible;
   scenarios inherit the original group/class and cannot be approved.
6. **Return to original base** opens its saved result for a human decision. Normal
   unsaved-draft navigation still offers Stay/Discard; pending writes cannot be
   discarded. Selection/review/finalization continue through the existing workflow.

If only the original GET fails, the child remains displayed. **Retry original-base
retrieval** retries that read without another scenario POST and preserves draft
fields. Original identity/company/product/unit/currency/dates/demand/class/Practice group
and supplier identities must match the child context before comparison.

If a scenario POST outcome is uncertain, retain the exact recovery JSON and key.
**Retry the same request** deliberately resubmits the unchanged original-base URL,
payload and key. Navigation stays guarded. Do not create a fresh request to guess
whether the first save succeeded. Recovery is session-local, not a durable outbox.

## Verify locally and clean up

Prerequisites: documented Python 3.11 frontend/dev/e2e environment, matching
Chromium, Node on PATH, and the existing running Podman machine with the documented
Compose provider. Create fresh artifact parents before pytest:

```powershell
$scenarioRun = Join-Path '.artifacts' ('ux37-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$scenarioRun/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/test_scenario_baseline.py tests/test_t16_scenarios.py `
  tests/test_t16_stored_planning.py tests/test_t16_odoo_planning.py -v `
  --basetemp "$scenarioRun/temp" -o "cache_dir=$scenarioRun/cache" `
  --junitxml "$scenarioRun/result.xml"

$scenarioBrowser = Join-Path '.artifacts' ('ux37-browser-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$scenarioBrowser/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/e2e/test_scenario_comparison_browser.py `
  tests/e2e/test_curated_practice_browser.py tests/e2e/test_planning_smoke.py `
  -m e2e -v -s --basetemp "$scenarioBrowser/temp" `
  -o "cache_dir=$scenarioBrowser/cache" --junitxml "$scenarioBrowser/result.xml"
```

The first command verifies original joins, exact deltas, preserved drafts and the
existing validation/replay boundaries using synthetic fixtures. The browser starts
only owned FastAPI/Reflex/Chromium and uniquely named disposable helper PostgreSQL,
prepares its model offline, and executes real saves/CBC/HTTP/storage. It removes
model configuration before scenario work. Expected: all five types from base/child,
bounded combined rejection, immutable original/assessments, genuine infeasibility,
class/group inheritance, keyboard/focus/narrow comparison and exact retry pass.
An owned test middleware injects 503 for only original GET; a separately stopped
API process establishes uncertain POST recovery. Neither is live Odoo evidence.

Fixtures close owned processes/tunnels and remove only their own Compose projects
in cleanup. Retain artifacts; never reset application or Odoo databases. Run required
AGENTS.md static/fast gates before handoff. Actual Reflex startup checks compilation;
no separate export is required for this exercised browser path. See the
[handoff](UX37_SCENARIO_HANDOFF.md) for executed scope and remaining gates.
