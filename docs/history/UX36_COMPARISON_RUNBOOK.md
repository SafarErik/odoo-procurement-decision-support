# Compare and explicitly select saved plans — #36

Current decision presentation, 2026-10-13: [#38](UX38_DECISION_RUNBOOK.md) replaces
the combined final selector/immediate finalization described below with separate
approval/No-award review and explicit confirmation. Comparison and selection remain
read-only; this note supersedes the final-control names in the historical procedure.

Use the existing [local service runbook](LOCAL_DEVELOPMENT_AND_SSH.md),
[library prerequisites](UX32_LIBRARY_RUNBOOK.md) and
[creation review](UX35_CREATION_RUNBOOK.md). This frontend increment needs no new
route, migration, dependency, Odoo setup or model. Saved browsing works without a
configured model; fresh creation still needs the matching owner-prepared model.

## Compare, select and review

1. Open a saved case from Cases, Practice or its `/planning?case_id=...&view=plans`
   bookmark. Nothing is selected for approval automatically. The Plans view leads
   with **Your allocation options** for the same saved product/demand.
2. On desktop/tablet, compare aligned plan columns and supplier rows. Each supplier
   stays on the same row, including zero allocations; promised dates and availability
   accompany its label. Costs, absolute premium and exact relative premium, demand
   coverage and exact exposure fractions remain readable. The small 0–100 scale is
   approximate; synthetic exposure is an uncalibrated proxy, not failure probability.
   **What shapes this allocation?** retains saved constraints and exact explanations.
3. Narrow screens/zoom use labelled plan sections with the same metrics and complete
   supplier rows. Wide desktop alternatives remain in a named, keyboard-focusable
   scroll region. **Cost–exposure chart and exact values** expands the subordinate
   saved-only plot and table, including exact cost/exposure fractions.
4. Press **Select for review** on a plan. Its column/section gains the selected
   surface and **Selected for review** text/pressed state. Selection performs no
   write or finalization. **Selection for review** mirrors its saved index, exact
   allocation/dates, demand/context, cost/premium and exposure. It remains available
   across Plans/What-if/Suppliers/Audit in normal page flow, without covering controls.
5. **Review decision** focuses the existing **Record the final decision** form.
   It does not submit. The existing Plan or No-award selector stays synchronized.
   Enter actor audit reference, required reason and demonstration acknowledgement,
   then deliberately **Finalize this base**. Alternative approval and No-award
   require reasons; attribution is audit text, not authenticated buyer identity.
6. Scenario selections remain analytical; return to the original base for a human
   decision. No proven plan means no invented costs/allocations or selected approval.
   Single/no-distinct-alternative and incomplete solver outcomes retain truthful
   messages and saved diagnostics. After finalization, controls are read-only and
   an approved summary derives from the immutable saved choice. No-award has no PDF.

Draft selection is session-local and is not saved metadata. Loading another case
or explicitly retrieving its stored data clears it; same-case view navigation
retains it. Approved retrieval reconstructs only its recorded approved choice.
Existing dirty navigation and exact pending-request recovery remain unchanged.

## Verify locally

Prerequisites: documented Python 3.11 frontend/dev/e2e environment, matching
Chromium, Node PATH and existing running Podman machine. Set the documented local
Compose provider; create a fresh pytest artifact parent:

```powershell
$comparisonRun = Join-Path '.artifacts' ('ux36-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$comparisonRun/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/test_plan_comparison.py tests/test_t16_acceptance.py `
  tests/test_t16_stored_planning.py tests/test_t17_frontend.py `
  tests/test_t16_cockpit.py tests/test_workspace_navigation.py -v `
  --basetemp "$comparisonRun/temp" -o "cache_dir=$comparisonRun/cache" `
  --junitxml "$comparisonRun/result.xml"

$comparisonBrowser = Join-Path '.artifacts' ('ux36-browser-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$comparisonBrowser/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/e2e/test_plan_comparison_browser.py tests/e2e/test_planning_smoke.py `
  tests/e2e/test_curated_practice_browser.py -m e2e -v -s `
  --basetemp "$comparisonBrowser/temp" -o "cache_dir=$comparisonBrowser/cache" `
  --junitxml "$comparisonBrowser/result.xml"
```

The first command checks exact mapping, bad allocation joins/totals, precision,
explicit selection and existing stored/finalization/navigation contracts. The
browser fixtures start only owned FastAPI/Reflex/Chromium and uniquely named
disposable helper PostgreSQL. They prepare trusted synthetic models offline and
execute actual CBC; Odoo is unconfigured. Expected: actual 3/5/10-supplier saves,
no-distinct alternative/infeasibility, long non-Latin identity, exact comparison,
read-only selection across views, keyboard/narrow/native zoom, separate No-award,
alternative approval/PDF and exact backend recovery pass. Retrieval is then tested
with the model unconfigured. These are correctness checks, not repeated timing workloads.

Native 200% Chromium zoom uses an owned temporary profile and test-only extension
calling `chrome.tabs.setZoom(..., 2)` and verifying `getZoom() == 2`, devicePixelRatio
and the reduced CSS viewport. It does not change the owner's browser or merely
scale screenshots/CSS/PDF. The profile closes in `finally`; each service fixture
stops its processes/tunnel and removes its own Compose project. Retain artifacts;
never reset application or Odoo databases. Run required AGENTS.md fast/static gates
before handoff. See [dated evidence and limits](UX36_COMPARISON_HANDOFF.md).
