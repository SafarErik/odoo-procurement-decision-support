# Understand supplier assessments and exact Audit evidence — #39

Use the [local services guide](LOCAL_DEVELOPMENT_AND_SSH.md) and
[saved-case prerequisites](UX32_LIBRARY_RUNBOOK.md). An existing saved case needs
only FastAPI, its helper database and Reflex with the matching server-side token.
Inspection needs no Odoo connection, configured model, training or solver execution.
It cannot refresh quotations, promote observed evidence or approve a plan.

## Buyer explanation → exact record

1. Open an existing original or child and choose **Suppliers**. Read the saved
   Schedule regular/watch class, generated receipt sample, history window,
   assessment reference time and saved quantity/time applicability. These classes
   describe synthetic training labels, including when quotations came from Odoo.
   The displayed exposure is approximate and uncalibrated, not failure probability.
2. Expand **How did the tree classify this supplier?** to trace the saved branches
   in readable wording. Rounded rates/thresholds do not replace exact evidence or
   explain the cause of a particular late delivery. Human business names that were
   never captured are not invented; canonical identities supply readable fallbacks.
3. Read **Saved allocation constraints** for each saved plan. Not selected is
   different from a hard exclusion. Notes translate recorded exclusion/binding
   codes; the frontend does not re-evaluate price, MOQ, delivery or supplier limits.
   An infeasible case retains its assessments, recorded diagnostics and original
   lineage; it offers no invented allocation. Scenarios do not reclassify suppliers.
4. **Inspect exact evidence in Audit** opens the bookmarkable Audit view and focuses
   its heading. Critical source/authority limits remain visible above disclosures.
5. Expand **Saved inputs, policy and allocations** for the exact saved input table,
   policy, identities/cutoff/hash, per-plan solver notes, all supplier allocations
   and field-level provenance. Finalized cases retain their exact final decision
   and immutable approved content. Classification is presentation metadata, and
   actor attribution is not authenticated identity.
6. Expand **Supplier tree paths and model evidence**, then a supplier's exact tree
   record, for saved class/score, branch values, model and history references.
   **Complete saved snapshot JSON** retains all recorded facts, inputs/policy,
   node/leaf IDs and support, paths, model/feature/dataset/mapping/runtime versions,
   solver records, provenance and scenario comparison. It reformats JSON for reading;
   it preserves recorded values and does not replace canonical hash serialization.
7. Use Tab/Enter/Space for native disclosure. Exact tables and the JSON pane have
   labelled, focusable scroll regions. Arrow keys scroll wide tables locally;
   PageDown scrolls long JSON. Narrow screens and native browser zoom retain labels
   without horizontal page overflow. Normal case work keeps the development workflow
   checklist in Practice/contextual help rather than showing it for every saved case.

Switching views can reuse the loaded immutable case in Reflex. Opening a different
case performs a stored GET. An unavailable/invalid response clears previous case
content and preserves existing alert/retry behavior; it does not train or refresh
upstream data. General recovery/document refinement remains #40.

## Verification and cleanup

Use the existing Python 3.11 environment. Fast checks below need no services and
prepare trusted synthetic assets offline, with actual ML/CBC required. Create an
owned artifact parent before pytest uses its basetemp:

```powershell
$evidenceRun = Join-Path '.artifacts' ('ux39-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$evidenceRun/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/test_supplier_evidence.py tests/test_t16_stored_planning.py `
  tests/test_plan_comparison.py tests/test_t17_frontend.py -v `
  --basetemp "$evidenceRun/temp" -o "cache_dir=$evidenceRun/cache" `
  --junitxml "$evidenceRun/result.xml"
```

Expected: exact snapshot/reference projection, no mutation, invalid/observed evidence
rejection, actual exclusion versus zero-allocation distinction and existing
selection/approval/recovery checks pass. Run the required AGENTS.md fast/static
gates before handoff; do not repeat passing checks without a relevant change.

The browser selection requires the existing running Podman machine, documented
project-local Compose provider/Node setup, installed Chromium and permitted local
process/loopback access. Follow [browser prerequisites](UX38_DECISION_RUNBOOK.md)
and [isolated persistence boundaries](PERSISTENCE_DEVELOPMENT.md), then run:

```powershell
$evidenceBrowser = Join-Path '.artifacts' ('ux39-browser-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$evidenceBrowser/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest `
  tests/e2e/test_supplier_evidence_browser.py `
  tests/e2e/test_decision_confirmation_browser.py -m e2e -v -s `
  --basetemp "$evidenceBrowser/temp" -o "cache_dir=$evidenceBrowser/cache" `
  --junitxml "$evidenceBrowser/result.xml"
```

Expected: real saved base/feasible/infeasible child inspection with model configuration
removed; long/non-Latin identities and missing business-name fallbacks; exact inputs
and full JSON equality; keyboard disclosure/focus/table/JSON scrolling; five viewport
widths and native 200% zoom; real stopped-API GET outage and stored reopening; no
inspection POST. The companion flow retains deliberate approval/No-award recovery.
The fixtures own fresh helper PostgreSQL projects, API, Reflex, browser profiles and
localhost tunnels, and stop/remove only those resources. Never reset application
or Odoo databases. Retain screenshots/logs/XML, close owned preview tabs and reset
temporary viewport overrides. No standalone transaction rerun is needed when
persistence/finalization contracts are unaffected. See the [handoff](UX39_EVIDENCE_HANDOFF.md)
for actual results, failures and remaining human gates.
