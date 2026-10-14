# Review attributed creation inputs — #35

Use the existing [local service runbook](LOCAL_DEVELOPMENT_AND_SSH.md),
[library prerequisites](UX32_LIBRARY_RUNBOOK.md) and
[Practice preparation](UX33_PRACTICE_RUNBOOK.md). No new backend route, migration,
dependency or Odoo configuration is required.

## Prepare, review and deliberately save

1. Open **New comparison** from Cases, or the open/create section at `/planning`.
   Choose Demo or Odoo and load its owner-prepared input. Practice exercises at
   `/practice` use the same review before their explicit calculation/save action.
   Loading or reviewing a draft creates no case and performs no model/solver run.
2. Read prepared facts, then supply terms. Demo/Practice allow demand 1–1,000 and
   retain their synthetic prepared dates and supplier terms. Odoo additionally
   allows required/promised dates, capacities 0–1,000 and MOQ 1–1,000; blank MOQ
   means no MOQ. Required date must be today or later. Availability, price/delivery
   applicability ranges, policy and matching synthetic history stay prepared.
3. Select **Review demo terms**, **Review Practice terms** or **Review Odoo terms**.
   Invalid terms receive labelled inline feedback and focus on the first invalid
   field. Correct the terms and review again. Successful review focuses its heading
   and shows exact demand/unit/currency/dates, company/purpose, captured cutoff,
   supplier/offer identity, price, capacity, MOQ, availability, ranges and policy.
   Tab to the named supplier-table scroll region to inspect all exact columns on
   a narrow screen. Review is not a feasibility result or approval.
4. Odoo review is a local captured preview. It does not refresh ERP quotations;
   FastAPI independently rereads the selected quotations/currency and checks
   expectations only when saving. Prices/identities are quotation facts; demand,
   capacity, MOQ and dates are supplied business terms. The Decision Tree still
   uses separately synthetic history, not an observed supplier predictor.
5. **Edit terms** retains field values and invalidates the frozen review. Review
   again before saving. The final create/save button submits that reviewed request
   through the existing HTTP route. Repeated submission is guarded. A newly expired
   required date requires edit/review; uncertain recovery retains its exact date.
6. Successful comparison creation opens its bookmarked saved Plans result and
   focuses the saved heading. Practice focuses **Practice case saved**, retaining
   its deliberate **Open saved Practice case** action. Synthetic creation is
   classified Practice; prepared Odoo creation is controlled work. Saved results
   retain their real immutable snapshot, assessments and allocations.
7. For an uncertain POST, keep the server/tab session and select **Retry the same
   request**. Editing, replacement and navigation cannot discard/replace its exact
   payload/key. The existing token-free recovery record remains available.
   Definitive validation/access failure leaves the review available; edit if needed.

## Reproduce focused and browser checks

Prerequisites: the documented Python 3.11 frontend/dev/e2e environment, matching
Chromium, Node PATH and running existing Podman machine. Set the documented local
Compose provider. Create a fresh artifact parent before pytest:

```powershell
$creationRun = Join-Path '.artifacts' ('ux35-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$creationRun/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/test_creation_review.py tests/test_t16_odoo_planning.py `
  tests/test_practice_classification.py tests/test_workspace_navigation.py -v `
  --basetemp "$creationRun/temp" -o "cache_dir=$creationRun/cache" `
  --junitxml "$creationRun/result.xml"

$creationBrowser = Join-Path '.artifacts' ('ux35-browser-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$creationBrowser/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/e2e/test_creation_review_browser.py tests/e2e/test_curated_practice_browser.py `
  tests/e2e/test_planning_smoke.py tests/e2e/test_workspace_browser.py -m e2e -v -s `
  --basetemp "$creationBrowser/temp" -o "cache_dir=$creationBrowser/cache" `
  --junitxml "$creationBrowser/result.xml"
```

The first command checks frozen intent, exact replay, validation, provenance and
existing classification/navigation without running services. Browser fixtures start
only owned FastAPI, Reflex, Chromium and uniquely named disposable helper PostgreSQL;
they prepare matching models offline and execute actual CBC. The new creation test
uses the existing read-only Odoo adapter with **mocked quotation transport**, while
HTTP, model, solver and storage remain real. It is not live Odoo evidence. Expected:
review produces no rows, field focus/edit preservation pass, genuine classified
saves and existing Practice/approval/PDF/recovery flows pass. Fixtures stop their own
processes/tunnel and remove their own Compose project; retain logs/screenshots/traces.
Never use application or Odoo databases for these reset checks.

Run required AGENTS.md fast/static gates before handoff. A live Odoo rerun needs the
existing owner-configured read-only fixture/credentials and matching prepared model;
it is a separate gate. See [dated evidence and limits](UX35_CREATION_HANDOFF.md).
