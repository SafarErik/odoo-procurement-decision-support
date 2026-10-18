# P3 — Frontend revamp

Date: 2026-10-18. Branch: `feature/p3-frontend-revamp` (from `main` at `1f1d7eb`, after the
P2 merge #47). The owner committed a first working-tree state as `cda3f64`; the review and
CI fixes below are in the working tree, not committed. Plan:
[REVAMP_PLAN.md](../REVAMP_PLAN.md) §P3. Requirements touched: FR-V2-07/09 / AC-V2-09 (UI
shows evaluations, allocations and explanations), FR-V2-08 (scenarios in the UI),
FR-V2-10/11/12 (decision and PDF from the UI), NFR-V2 usability and accessibility.

## Problem

- The owner's main complaint: system data and metadata everywhere, hard to navigate and
  test, no supplier view, few charts, English only.
- `frontend/planning/state.py` had grown to ~1,330 lines; every UI string was English and
  hard-coded; hashes, fractions and "synthetic exposure" wording sat in buyer views.
- The browser e2e suite had not been collected since P2 (it started from the removed demo).
- The P2 handoff noted two `_set_focus` "No element found for ref" console errors.

## Decisions (owner, 2026-10-18)

1. Branch `feature/p3-frontend-revamp` from `main`; screen-by-screen plan accepted ("mehet").
2. Supplier KPIs are compared across the case's suppliers (no time series; that needs a
   backend read model and is left for later).
3. The e2e suite runs on fixture Odoo data, not on the live Odoo.
4. Earlier decisions applied: Hungarian default with an English switch, natural wording;
   the PDF language follows the UI language; no practice area, only a data-origin badge.

Own decisions, each explained below: English text keys with the visible strings in two
dictionaries; internal plan/decision keys stay English (`"Minimum cost"`, `"No-award"`) so
selection and approval never depend on the language; the old v1 RFQ ledger page is removed
(Open RFQs now lists quotation groups, which is what starts a case).

## Implemented behavior

### Information architecture

- Shell (`frontend/workspace.py`): dark-green sidebar with **Ügyek / Cases** and
  **Nyitott ajánlatkérések / Open RFQs**, language switch (HU/EN) at the bottom; on phones a
  sticky top bar with the switch and a drawer menu. Routes: `/` and `/cases`, `/rfqs`,
  `/planning?case_id=…&view=…` (old `view=whatif` bookmarks map to `scenarios`).
- **Cases** (`planning/library.py`): search, decision-status and data-source filters, a
  table (product with badge, demand, required date, minimum cost, decision badge, actions)
  and a right-hand context panel on wide screens; cards on phones; saved scenarios expand
  on demand; empty, filtered-empty, loading and error states.
- **Open RFQs** (`planning/rfqs.py`): one card per open Odoo quotation group from the P2
  API (product, quantity, currency, suppliers with prices, latest date); unusable groups
  show the reason in plain words. "Start comparison" reads the Odoo history preview, then
  the buyer sets demand, required date and each supplier's capacity, MOQ and promised date,
  reviews, and **Calculate and save** opens the new case on Overview.
- **Case page** (`planning/page.py`): breadcrumb, product name (Odoo display name), demand,
  currency, required date, decision/scenario/data-origin badges, an **Audit** button, and
  tabs **Áttekintés / Szállítók / Tervek / Forgatókönyvek / Döntés és PDF**.
  - Overview: KPI cards (minimum cost, plans to compare, decision), plan choice as a radio
    list with extra cost, supplier summary, and a numbered **Next step** panel.
  - Suppliers: KPI comparison charts (on time, fill rate, average lateness) and a card per
    supplier (class badge, offer price, planned quantity, capacity, promised date, the seven
    history indicators, readable decision path, leaf sentence) from
    `GET /{id}/suppliers?language=` (stored snapshot only).
  - Plans: aligned comparison table with selection, cost-versus-risk scatter chart,
    selected-allocation panel with bars, and "What shapes the allocation?" notes.
  - Scenarios: base-versus-scenario table and grouped bar chart for saved scenarios; the
    composer for outage, capacity, demand, price and combined changes in both directions.
  - Decision & PDF: one-time approval or No award with confirmation dialog; the approved
    PDF opens in the UI language (viewer labels localized too).
  - Audit: case and base IDs, snapshot and approved-content hashes, exact costs, exposure
    and premium fractions, solver notes, all allocations, tree paths and model IDs, field
    provenance, the recorded decision JSON, the last request, and the full snapshot JSON.

### Language and formatting

- `frontend/i18n.py` + `frontend/i18n_ui.py`: 414 English keys, each with Hungarian and
  English text written as procurement language (e.g. "Nincs odaítélés", "Kockázati
  kitettség", "Forgatókönyv"). Formatting: `1 545,70 Ft` / `1,545.70 Ft`, `€102.00`,
  `2026. márc. 8.` / `8 Mar 2026`, `80 %` / `80%`; stored digits are never rounded away.
- The choice lives in browser local storage (`pdss_language`, Hungarian default). Switching
  re-labels what is loaded from the stored payloads; only the supplier overview (a GET of
  the stored snapshot) is re-read. Odoo is not read and nothing is re-solved.
- "Synthetic exposure" wording is gone from buyer views; generated or demo data shows as a
  small **Generált adat / Bemutató adat** badge plus one note on the Suppliers tab.

### State split and boundaries

- `PlanningState` (`frontend/planning/state.py`) is composed from Reflex state mixins:
  `state_base` (language, navigation guard, the one pending request and recovery),
  `state_library`, `state_creation`, `state_case`, `state_scenarios`, `state_decision`.
- Unchanged semantics: HTTP-only boundary, idempotent retry of an uncertain save with the
  same key and payload, decision conflict → reopen the recorded decision, one-time approval,
  scenarios never approvable, No award has no PDF.
- `_set_focus` errors: every `rx.set_focus` was replaced by `focus()` (a
  `document.getElementById(id)?.focus()` script), so a target that is not mounted yet is
  skipped instead of logging "No element found for ref".

### Backend (read-only, small)

- `application/planning_library.py` library rows now carry the stored Odoo product name,
  unit name, minimum cost and the model's data origin (badge in the list).

### Review and CI follow-up (2026-10-18)

- CI `reflex export` failed: `set_language` was annotated `str`, the segmented control
  sends `str | list[str]`. It now accepts both and ignores empty or multi-value lists.
- The quality job failed on the frontend tests (monkeypatch targets, English assertions
  against the Hungarian default, changed money format). Tests now patch the feature module
  that resolves each client (`tests/frontend_patching.py`) and set English explicitly where
  they read English text; `tests/test_p3_frontend.py` covers the Hungarian path.
- Review findings applied: library accepts `invalid_input`; starting an already loaded
  group keeps the draft and focuses its terms; the saved rationale is stripped like the
  confirmation shows it.
- Found on the way: `money()` raised `InvalidOperation` on very long exact values
  (quantize); tree thresholds on counts (e.g. 2.5 receipts) were rounded to whole numbers;
  the "did not finish" alternative notice had lost "this does not establish that no
  alternative exists"; Hungarian validation texts attached a suffix to a unit.
- e2e harness: uses the venv `podman-compose` provider like `tools.dev` (the Docker pipe
  was missing) and trusts the recreated local Podman VM's SSH host key, kept in the run
  folder rather than the user's known_hosts.
- Browser check found and fixed: the phone top bar was 8 px wider than 375 px (menu button
  is now icon-only with its accessible name); the scatter chart now has grouped axis
  ticks with the currency, direct point labels and no entry animation; programmatic
  heading focus no longer draws a focus ring; the language switch text is centred; English
  amounts in forint read `293,132.00 HUF`.
- `frontend/reflex.lock/` now pins `recharts` (and `mergician`), which the charts need;
  Reflex resolved `react-router` 8.4.0 at the same time.
- `tools/ui_screenshots.py` reproduces the evidence screenshots.

## Evidence (commands actually run, 2026-10-18, Windows, Python 3.11.15 uv venv)

| Check | Result |
| --- | --- |
| `python -m tools.dev check` | PASS — format, lint, compileall, **480 passed**, 51 deselected, `uv pip check` compatible |
| `reflex export --frontend-only --no-zip` (the failing CI step), in `frontend/` | PASS — compiled and production build created (exit 0) |
| `pytest -m e2e tests/e2e --browser chromium` (Podman 6.1.4, disposable PostgreSQL 16, real FastAPI + Reflex, fixture Odoo) | **2 passed** in 165 s: `test_rfq_to_approved_pdf_in_hungarian_then_english`, `test_cases_scenario_and_states_at_375_px`; no `_set_focus` / "No element found" console errors |
| `pytest -m "integration and not e2e"` on the disposable test database (`infra/persistence/compose.test.yaml`) | **44 passed**, 5 skipped (opt-in live Odoo/T6/T7S fixtures, same as P2) |
| Live dev stack (`tools.dev odoo-up`, `db-up`, `api`, `ui`; `pdss_history_gen`) + `tools/ui_screenshots.py` at 1440×900 and 375×812 | 20 screenshots in [docs/evidence/p3/](../evidence/p3/): Cases, Open RFQs, Overview, Suppliers, Plans, Scenarios, Decision & PDF (HU), Plans (EN), unknown-case error, empty search; `report.json`: **0 console errors**, horizontal overflow 0 px on every screen |
| Built-in browser on the live stack | Cases list with Odoo names and HU formatting; Suppliers tab 4 cards + 3 KPI charts; Plans tab table, allocation bars and scatter; console without errors |

## Not verified / remaining

- Hosted CI: not run from here (nothing pushed); the failing quality job and `reflex
  export` step were reproduced and pass locally.
- The approved PDF opened in the e2e flow (Hungarian, viewer shows "1. oldal / N"); the PDF
  pages themselves were not re-reviewed as images in P3 (P2 reviewed the layout).
- A base case's Scenarios tab now lists its saved scenarios (see the addendum below).
- KPI time series (owner decision 2): not built.
- Screen reader pass with a real assistive technology: not done; checked roles, labels,
  focus targets and keyboard-reachable controls only.
- Legacy P1 cases without stored Odoo names show "1. termék" in the list (data, not code).

## Limitations

- KPI trends over time are not shown: the stored snapshot has one value per KPI; a
  per-period read model would be a backend increment.
- Recovery data is still session-local (copy before leaving), as before.
- The PDF viewer loads the PDF as a data URL; very large PDFs are capped at 2 MB (unchanged).
- Supplier names come from Odoo display names stored since P2; older cases show
  "Supplier N" / "Demo supplier N".
- Odoo history in the test database is generated; badges say so, values are not real
  supplier performance.

## Owner action

1. Review and commit (new files are untracked; six removed demo-based e2e files and the
   v1 ledger page are deleted in the working tree, not staged).
2. Optional local e2e: `pip install -e ".[frontend,dev,e2e]"`, `python -m playwright
   install chromium`, Podman machine running, then `pytest -m e2e --browser chromium`.

## Thesis relevance

- Ch. 4 (design): information architecture (Cases, Open RFQs, case tabs, Audit as a
  secondary view), language as client-side preference, stored-only re-labelling.
- Ch. 6 (implementation): Reflex state mixins, i18n and locale formatting, recharts charts,
  focus handling without refs, fixture-Odoo browser harness.
- Ch. 7 (evaluation): browser evidence at desktop and 375 px, the two e2e flows, the
  screenshots in `docs/evidence/p3/` (usable as thesis figures).
- Ch. 9: KPI time series, durable recovery, user identity instead of typed actor names.

## Addendum: saved scenarios on the base case's Scenarios tab

- Problem: on a base case the Scenarios tab showed only the composer; the base's saved
  scenarios were reachable only from Cases → "Forgatókönyvek".
- Decision: reuse the existing read-only library GET
  (`{planning_cases_url}/{case_id}/scenarios` via `fetch_library` / `library_row`); no new
  backend route, nothing re-read from Odoo or re-solved.
- Behavior: a "Mentett forgatókönyvek" card above the composer lists each scenario's kind,
  demand and outcome with an Open button (`open_saved_case(id, "scenarios")`); two columns
  from the `lg` breakpoint, one below. It loads when the tab mounts on a base case
  (`LibraryMixin.load_base_scenarios`), shows loading, empty ("Ehhez az ügyhöz még nincs
  forgatókönyv."), error with Retry, and "További forgatókönyvek" when a next page exists.
  Showing any case (including the child just saved) clears the list, so returning to the
  base reloads it; a page that arrives for a case no longer open is dropped; a language
  switch re-labels the stored rows without HTTP.
- Evidence: `pytest tests/test_p3_frontend.py` (3 new tests, 17 passed);
  `python -m tools.dev check` passed (483 passed, 51 deselected). Built-in browser against
  the local Postgres stack: 1440×900 English list of 9 scenarios in two columns, 375×812
  Hungarian list and empty state, Open navigates to the child, API stopped → error +
  Retry, API restarted → Retry loads; horizontal overflow 0 px at 375 px (−15 px at 1440,
  i.e. none).
- Integration into this branch (2026-10-18): the change was made in a separate worktree
  on top of `cda3f64` and applied here as a patch on top of `b3ddfba` (six files, no
  `reflex.lock` changes). After applying, `python -m tools.dev check` on this branch:
  PASS, 484 passed, 51 deselected.
- Not run: integration/e2e suites (no persistence or flow change beyond this read);
  hosted CI.
- Limitation: the list is read when the tab mounts; a scenario saved in another browser
  tab appears after re-opening the tab.
- Thesis: Ch. 4 (case navigation), Ch. 7 (browser evidence).
