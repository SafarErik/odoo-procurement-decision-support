# R5 — Readable Reflex views and state, one source of visual tokens

Date: 2026-11-09. Worktree branch `claude/r5-frontend-views-599e6b` on `main` `325b58d`.
Not committed; the owner commits. Drive was not changed. Technical debt only; no FR-V2/AC-V2
change. Behaviour-preserving; the visible differences are listed under Evidence.

## Problem

The Reflex views had grown long nested component trees: `audit_view` 178 lines,
`_decision_form` 149, `_scenario_form` 143, `rfqs._terms` 138, `_review` 124 — 27 frontend
functions over 60 lines in total. A reader had to count brackets to find where "the PDF
button" or "the supplier term fields" begin. Colours lived in four places: `theme.py`
(12 tokens), the shell's `_CSS` string (~20 hex literals, `#413b76` = `ACCENT` nine times),
`pdf.py`'s JavaScript and loose literals in `rfqs.py`, `results.py`, `overview.py`,
`library.py`, `scenarios.py`, `recovery.py`, `charts.py`. The purple primary button was
re-styled by hand 15 times. `CreationMixin` mixed form parsing, wording and request
handling in ~600 lines; `LibraryMixin` served Home and Cases and filled Home's lists with
`setattr(self, f"home_{name}_error", …)`. `CaseMixin.load_case` and
`LibraryMixin.open_library` were reachable only from tests. Three tests imported private
helpers (`_card`, `_viewer_texts`, `_filters`). Two Hungarian texts still said "lezárt
beszerzési sor" instead of the approved "lezárt rendelési sor".

## Decision

- **Split by what the buyer sees.** A view function is split where the part has a name a
  buyer would recognise ("approved allocation", "supplier toggle", "review actions",
  "pager"). Every extracted component has a one-line docstring saying what it shows. No
  component framework: plain functions returning `rx.Component`, as before.
- **One token file.** `frontend/theme.py` names every colour, radius and repeated size.
  Names follow the DESIGN.md frontmatter (`accent-hover` → `ACCENT_HOVER`); colours the
  views use but DESIGN.md does not name are a separate, commented "supporting" block. The
  shell CSS is a `string.Template` filled from `theme.TOKENS` (`$ACCENT`), so CSS keeps its
  braces and stays readable. The PDF viewer receives its colours as a JSON constant.
- **Spacing literals stay.** Per-element margins/gaps (`"1rem"` ×96, `"0.75rem"` ×50 …) are
  the DESIGN.md spacing scale already; replacing ~300 literals by constants would make every
  call longer without one-source value. Repeated *geometry* (card and page padding, page
  width, rail width, side column, touch target, font stack) is tokenised.
- **Pure rules out of the state.** The wizard's parsing and wording became plain functions
  in `frontend/planning/creation_rules.py`, returning text *keys* the mixin translates.
  The mixin keeps only Reflex vars, events and request flow.
- **Two explicit list states.** Home's lists moved to `HomeMixin` (`state_home.py`) with
  named assignments; `LibraryMixin` is the Cases page and the Scenarios tab's saved list.
- **Delete test-only entry points.** `load_case` and `open_library` were removed; tests use
  `navigate_global("cases")` and the shared case loader behind the `/planning` bookmark.
- **Two shared helpers in `ui.py`.** `primary_button` (DESIGN.md `button-primary`) and
  `field_label` / `NATIVE_FIELD` for the three native `<select>/<input>` forms; each form
  still sets its own padding, so geometry is unchanged.

## Implemented behaviour

### Component map per page

| Page / tab | Module | Top-level component → named parts |
| --- | --- | --- |
| Shell (every page) | `workspace.py` | `workspace_shell` → `_rail`, `_mobile_bar` → `_menu_drawer`; `_navigation`, `_brand`, `language_switch`, `_discard_dialog`; `page_frame` |
| Home | `home.py` | `home_page` → `_section` (one list card) → `_case` (one row) |
| Cases | `library.py` | `library_page` → `_filters`, `_list` → `_empty`, `_desktop_table` → `_table_row`, `_mobile_card`, `_pager`, `_context_panel`; per case `_actions`, `_children` → `_child` |
| New procurement | `rfqs.py` | `rfqs_page` → `_page_header`, `creation_steps`, `_groups` (step 1: `_group_card`, `_group_details` → `_quotation`), `_terms` → `_selected_group_bar`, `_demand_step` (step 2), `_terms_step` (step 3: `_supplier_terms` → `_supplier_toggle`, `_supplier_basics`, `_quantity_ranges`; `_history_table`), `_review` (step 4: `_review_facts`, `_review_table`, `_review_supplier_card`, `_suggested_terms`, `_review_actions`); fields `_field`, `_field_error` |
| Case page | `page.py` | `planning_page` → `_messages`, `_workspace` → `_header` → `_breadcrumb`, `_case_facts` |
| Overview | `overview.py` | `overview_view` → `kpi` tiles, `_suppliers_tile`, `_options` → `_plan_option`, `_next_step` → `_step` |
| Suppliers | `suppliers.py` | `suppliers_view` → `_kpi_comparison` (charts), `_supplier_card` → `_fact`, `_class_badge` |
| Plans | `results.py` | `plans_view` → `_plan_summary`, `_allocation_card` → `_comparison_table` → `_plan_header_cell`, `_metric_row`, `_supplier_row`; `_tradeoff_card`, `_constraint_notes`, `_selected_panel` → `_allocation_bar` |
| What if…? | `scenarios.py` | `scenarios_view` → `_saved_scenarios` → `_saved_scenario`, `_saved_scenarios_status`; `_comparison` → `_comparison_header`, `_comparison_table`; `_scenario_form` → `_kind_select`, `_supplier_select`, `_new_values` → `_number_field`, `_draft` |
| Decision & PDF | `decision.py` | `decision_view` → `saved_decision` → `_approved_allocation` (→ `pdf_panel`); `_decision_form` → `_choice_field`, `_actor_and_reason`, `_acknowledgement`, `_decision_error`, `_confirmation` → `_confirmation_summary` |
| Audit | `audit.py` | `audit_view` → `_header`, `_identity`, `_audit_pdf` (→ `pdf_panel`), `_inputs`, `_plans` → `_plan_record`, `audit_tree` → `_assessment`, provenance table, `_stored_texts` |
| PDF | `pdf.py` | `pdf_panel` (button + note + error + viewer, shared by Decision and Audit), `ApprovedPDFViewer`; the JS is the module constant `VIEWER_SCRIPT` |
| Charts | `charts.py` | `cost_exposure_chart` → `_plan_points`; `scenario_chart`; `kpi_chart` |

`pdf_panel` replaced two near-identical 40-line blocks (approved PDF and audit PDF).
`_get_custom_code` now returns `VIEWER_SCRIPT`: Reflex inlines custom component code into
the page module, so the JavaScript stays a Python string, but at module level with a
comment, with texts (`PDF_TEXT`, `AUDIT_TEXT`) and colours (`PDF_COLOR`) generated above it.

### Token table (`frontend/theme.py`)

| Token | Value | DESIGN.md | Used for |
| --- | --- | --- | --- |
| `PAPER` | `#eff5f1` | paper | canvas, active nav item |
| `SURFACE` | `#FFFFFF` | surface | cards, text on purple/green (was also the keyword `white`) |
| `INK` | `#173e3d` | ink | headings, PDF viewer text, selected chart ring |
| `MUTED` | `#536964` | muted | secondary text, table headers |
| `ACCENT` | `#413b76` | accent | primary buttons, focus outlines, Radix accent override |
| `ACCENT_HOVER` | `#373164` | accent-hover | Radix `--accent-10` |
| `RAIL` | `#153f40` | rail | sidebar, phone bar, drawer |
| `HAIRLINE` | `#d1ded6` | hairline | borders, chart tooltip, PDF viewer borders |
| `ERROR` | `#A43E47` | error | error-state rule |
| `SERIES_1`, `SERIES_2`, `GRID` | `#5b4fc4`, `#1a9a7f`, `#e3ebe6` | series-1/2, grid | charts, allocation bars |
| `SELECTED` | `#f1eff8` | selected | selected plan / group / case row |
| `NAV_HOVER` | `#24504f` | nav-hover | rail item hover |
| `SUBTLE` | `#f6f9f7` | — | row hover, nested scenario list, draft panel |
| `POLICY_PANEL` | `#e7eeea` | — | wizard policy box |
| `BAR_TRACK` | `#e6ece8` | — | empty part of an allocation bar |
| `RADIO_RING` | `#9fb3ab` | — | unchosen plan radio |
| `FIELD_ERROR` | `#92313b` | — | wizard inline field error |
| `ACCENT_A8`, `TEXT_SELECTION` | `#71699c`, `#d8d2f0` | — | Radix accent step 8, `::selection` |
| `BRAND_BORDER`, `BRAND_ICON` | `#668b85`, `#e4eee9` | — | brand mark on the rail |
| `RECOVERY_BORDER`, `RECOVERY_BACKGROUND` | `#956018`, `#FFF8EB` | — | recovery panel |
| `DRAWER_OVERLAY`, `LANGUAGE_SWITCH` | `rgba(21,63,64,.35)`, `rgba(255,255,255,.92)` | — | drawer overlay, HU/EN switch on green |
| `RADIUS_BAR`, `RADIUS_NAV`, `RADIUS_TERMS`, `RADIUS_CARD`, `RADIUS_STEP` | 4px, 8px, 12px, 14px, 50% | rounded | bars, nav/fields/tooltips, supplier terms/plan cards/brand mark, cards, step numbers |
| `CARD_PADDING`, `PAGE_PADDING`, `PAGE_MAX_WIDTH` | `1rem/1.25rem`, `1/1.5/2rem`, `92rem` | spacing, layout | `card()`, `page_frame()` |
| `RAIL_WIDTH`, `SIDE_COLUMN`, `TOUCH_TARGET` | `14rem`, `20rem`, `2.75rem` | layout | rail, sticky side columns and drawer width, min hit height |
| `FONT_BODY` | Aptos stack | typography.body | shell font |

Left as literals on purpose (one-off, not a token): recovery panel radius `10px`, error-rule
pill `999px`, PDF viewer control radius `6px`, Recharts bar radius `[4, 4, 0, 0]` (numbers,
not CSS), wizard label size `14px`, chart tooltip `13px`. A `grep` for `#` colours in
`frontend/` outside `theme.py` and `i18n/` now finds none.

### State split

| Before | After |
| --- | --- |
| `CreationMixin`: `bounded_form_integer`, `_form_date`, `_kept_suggested`, `_reviewed_source`, preview/history/policy wording in `_apply_preview` (66 lines), field parsing in `_odoo_request` (72), review wording in `_set_review` (83) | `creation_rules.py` plain functions: `bounded_form_integer`, `form_date`, `kept_suggested`, `reviewed_source`, `preview_offers`, `suggested_values`, `history_rows`, `policy_text`, `read_demand`, `reviewed_terms` (returns `(request, {field id: text key})`), `review_summary`, `review_rows`. The mixin's `_apply_preview` 15 lines, `_odoo_request` 12, `_set_review` 26 |
| `LibraryMixin` with Home lists via `setattr(f"home_{name}_…")` | `HomeMixin` (`state_home.py`): `home_pending/_recent`, errors, `home_on_load` with named assignments, `_relabel_home`; `LibraryMixin` keeps Cases + saved scenarios |
| `state_scenarios.run_scenario` 110 lines | `_scenario_payload` (+ `_demand_change`, `_capacity_change`, `_price_change`), `run_scenario` 23 lines |
| `state_creation.bounded_form_integer` imported by `state_scenarios` | `creation_rules.bounded_form_integer` (public, shared) |
| `CaseMixin.load_case`, `LibraryMixin.open_library` (tests only) | deleted; tests use `navigate_global("cases")` and `tests/helpers/frontend_patching.open_case` (the `_load_case` loader behind `load_bookmark`) |
| `state_case._card` (private, imported by a test) | `SupplierCard.from_row` |
| `api/cases.submit_planning_request` 92 lines | `_rejection` (which refusal text) + `_check_saved` (does the saved case answer this request) + 34-line flow; logic unchanged |
| `api/case_view.plan_rows` 90, `scenario_comparison` 76, `summary` 63 | `_plan_budgets`, `_plan_row`, `_allocation_rows`; `_assumptions`; `_policy_sentence` |

### Private-name imports

`rg -n "from frontend\.[a-z_.]+ import _|import frontend.*\._" tests frontend` is empty.
Tests now use `SupplierCard.from_row`, `pdf.VIEWER_SCRIPT` and `str(library_page())`.

### Wording (HU only)

| Key | Before | After |
| --- | --- | --- |
| `history_note` | A lezárt beszerzési sorokból számolva. | A lezárt rendelési sorokból számolva. |
| `err_history_insufficient` | … háromnál kevesebb lezárt beszerzési sora van az Odoo-ban … | … háromnál kevesebb lezárt rendelési sora van az Odoo-ban … |

EN check: the English side says "settled purchase lines" (`history_note`,
`err_history_insufficient`), "Settled lines" (`kpi_lines`, `kpi_help_sample`), the same as
the backend's own EN label (`application/supplier_overview.py`: "Settled purchase lines").
It does **not** say "closed order lines". I left EN unchanged so the wizard and the
Suppliers tab keep one English term; switching both to "closed order lines" needs the
backend label too (out of scope here) — owner decision.

### Module docstrings

Every `frontend/` module now opens with one or two sentences naming the part of the
buyer's screen it builds or the state it holds; every view component has a one-line
docstring saying what the buyer sees.

## Evidence

### Longest frontend functions (AST: `end_lineno - lineno + 1`, all of `frontend/`)

| Function (before) | Before | After |
| --- | ---: | ---: |
| `audit.audit_view` | 178 | 21 |
| `decision._decision_form` | 149 | 35 |
| `scenarios._scenario_form` | 143 | 39 |
| `rfqs._terms` | 138 | 31 |
| `rfqs._review` | 124 | 28 |
| `state_scenarios.run_scenario` | 110 | 23 |
| `scenarios._comparison` | 109 | 41 |
| `rfqs._supplier_terms` | 101 | 18 |
| `results._comparison_table` | 94 | 30 |
| `api/cases.submit_planning_request` | 92 | 34 |
| `api/case_view.plan_rows` | 90 | 19 |
| `decision.saved_decision` | 87 | 25 |
| `pdf._get_custom_code` | 85 | 2 |
| `state_creation._set_review` | 83 | 26 |
| `decision._confirmation` | 81 | 42 |
| `suppliers.suppliers_view` | 80 | 49 |
| `page._header` | 80 | 33 |
| `api/case_view.scenario_comparison` | 76 | 49 |
| `rfqs.rfqs_page` | 75 | 38 |
| `state_creation._odoo_request` | 72 | 12 |
| `charts.cost_exposure_chart` | 71 | 38 |
| `workspace._mobile_bar` | 68 | 23 |
| `state_creation._apply_preview` | 66 | 15 |
| `library._list` | 64 | 29 |
| `results.plans_view` | 63 | 41 |
| `api/case_view.summary` | 63 | 43 |
| `recovery.recovery` | 62 | 47 |
| **Functions > 60 lines / longest / count** | **27 / 178 / 269** | **0 / 60 / 339** |

The longest after the change are `overview._plan_option` (60, one radio row),
`case_view._plan_row` and `validate_case` (56, one record's fields / invariants) and
`library._filters` (55, one form): each is one component or one record, so not split.

### Commands actually run

- `python -m tools.dev check` → ruff format/lint clean, compileall, **487 passed, 51
  deselected**, `uv pip check` compatible.
- Focused while working: `pytest tests/test_creation_review.py tests/test_frontend_*.py
  tests/test_guided_workspace.py tests/test_planning_library.py
  tests/test_workspace_navigation.py tests/test_scenario_baseline.py
  tests/test_saved_result_presentation.py tests/test_architecture.py` → 199 passed.
- `pytest -m e2e --browser chromium` → **3 passed, 535 deselected** (5 min 25 s; disposable
  Compose PostgreSQL, fake Odoo).
- Not run: `pytest -m "integration and not e2e"` (no persistence or Odoo-adapter code
  changed). Hosted CI not observed (nothing pushed).
- `rg -n "from frontend\.[a-z_.]+ import _|import frontend.*\._" tests frontend` → no hits.

### Screenshot comparison

Method: one Playwright script (kept outside the repo) captured the same 44 full-page
screenshots twice against the dev stack (`tools.dev db-up`, `api`, `ui`, live Odoo):
first on the unchanged tree (= `main` `325b58d`), then on this tree after restarting
`reflex run`. Set: Home, Cases, wizard step 1, approved case Overview / Suppliers / Plans /
What if…? / Decision / Audit, an undecided case's Decision form, and the case error page;
each in HU and EN, at 1440×900 and 375×812. Comparison: Pillow `ImageChops.difference`
per pair (identical / changed pixel count / bounding box), changed regions cropped and
inspected.

Result: **40 of 44 pixel-identical**; no console errors and no horizontal overflow in
either run. The four others:

| Screenshot | Difference | Reason |
| --- | --- | --- |
| `wizard-{desktop,mobile}-{hu,en}` | ~82 px in one line | "Ajánlatok lekérve: … 19:02 → 19:28 UTC": the Odoo read time, data not UI |
| `case-approved-overview-desktop-hu` | 11 px, max channel delta 1/255 | antialiasing of a card corner; same colours and radius |
| `case-approved-plans-mobile-en` | 1 px, delta 1/255 | antialiasing |

Intended visual difference outside the set: the PDF viewer's borders were `#c9d8d1` and
are now `HAIRLINE` `#d1ded6` (computed `rgb(209, 222, 214)` verified in the browser);
`white` became `#FFFFFF` (same colour).

### Interaction checks (headless Chromium via Playwright against the dev stack)

The built-in browser pane was hidden in this session (0×0 viewport, screenshots timed
out), so the interactions ran in headless Chromium on the same stack. All passed with no
console errors:

- Cases: search with no match → "Nincs találat", clear; row click selects (context panel);
  Scenarios expand/hide; status filter and Next page → the known 503 error card (pre-P2
  rows in the dev DB).
- 375 px: menu drawer opens, closes and navigates; HU → EN → HU switch on Home.
- Wizard with live Odoo: group → demand (quantity 0 → inline error) → terms (capacity
  5000 → inline error, supplier block expanded) → review (not saved); leaving the review →
  discard dialog: Stay keeps it, Discard draft goes Home.
- Decision form on an undecided case: blank actor → "Adja meg a nevét (1–255 karakter)";
  valid input opens the confirmation dialog, Cancel closes it (nothing recorded); No-award
  toggle and back.
- Approved PDF viewer pages (2. oldal / 3); audit appendix PDF viewer opens.
- What if…?: More scenarios; capacity 1001 → validation error; capacity 40 → saved a
  child scenario (`da6511f2…`) and opened its comparison.
- Backend down (API stopped): Home shows "A mentett ügyek nem érhetők el" with Újra; the
  case page shows "Az ügy nem nyitható meg" with Vissza az ügyekhez — desktop and 375 px.

Data written by these checks (dev planning DB only, never Odoo): one undecided base case
created through the wizard for the Decision baseline (`9e6f8294…`) and the what-if child
above.

## Limitations

- Spacing literals are not tokenised (see Decision); changing `CARD_PADDING` or
  `PAGE_PADDING` works, changing "the standard gap" still means a search.
- `pdf.py`'s viewer is JavaScript in a Python string: Reflex inlines custom component code,
  and a static asset would need its own bundling path. It is now a commented module constant.
- Odoo history access: the key worked today (2026-11-09); it expires 2026-11-10 00:00.

### UI ideas noticed (not built)

- The recovery panel uses its own `10px` radius and amber colours outside the Radix palette;
  a Radix amber callout would match the other notices.
- The wizard's inline field error uses `#92313b`, not the `ERROR` token; one red would do.
- PDF viewer controls are hand-styled buttons (6px radius, 44px) beside Radix buttons; the
  viewer could reuse the workspace button look.
- While a PDF loads, react-pdf shows its own English "Loading PDF…" inside the viewer
  region, also on the Hungarian UI; passing `loading=` with `pdf_loading_pages` fixes it.
- `kpi_lines` "Lezárt sorok" could read "Lezárt rendelési sorok" in the history table header
  if width allows (phones).

## Thesis relevance

UI chapter (frontend architecture): the view layer is now a tree of small, named Reflex
components per screen region; visual identity is one token module mirroring DESIGN.md;
state mixins hold Reflex vars and request flow while pure functions hold parsing and
wording (testable without Reflex). The component map and token table above can be cited.
