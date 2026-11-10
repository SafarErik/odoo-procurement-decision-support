# R4 — One HTTP-client layer for the frontend

Date: 2026-11-07. Worktree branch `claude/r4-frontend-api-95e7cf` on `main` `a29da04`.
Merged as PR #63. Drive was not changed. Technical debt only; no FR-V2/AC-V2
change. Behaviour-preserving except the two error texts listed under Limitations.

## Problem

Five client modules (`frontend/planning_client.py` 762 lines, `planning_library_client.py`,
`planning_pdf_client.py`, `supplier_overview_client.py`, `odoo_history_client.py`) each opened
their own `httpx.AsyncClient`, built the Bearer header themselves and mapped errors to text
keys in their own way. Timeouts were 45 / 7 / 15 / 10 / 30 s with no stated reason;
`trust_env=False` in three of five. The state mixins read
`settings.api_service_token.get_secret_value()` 13 times and assembled URLs
(`…/{id}/scenarios`, `+ "/from-odoo-history"`, `…/final-decision`, the preview query string).
The canonical-UUID check `str(UUID(x)) != x` was repeated ~9 times. `_map_case` was one
446-line function mixing validation and all display formatting. Private names crossed module
boundaries (`_map_case`, `_supplier_label`, `_bounded_form_integer`), and the supplier and
product label rules existed twice.

## Decision

- One package `frontend/api/`. `http.py` is the only module that knows httpx, the base URL
  rules, the token and timeouts. Every other module calls `http.send`, `http.get_json` or
  `http.get_bytes`.
- One module per backend resource with small public functions; the state passes ids,
  params and the language, never URLs or tokens. Saves still go through
  `cases.submit_planning_request(url, payload, key)` because the pending request (and the
  recovery JSON the buyer can copy) keeps the full URL; the URL comes from
  `cases.from_odoo_history_url()`, `scenarios_url(base_id)` or `final_decision_url(case_id)`.
- `case_view.py` holds the stored-case presentation: `validate_case` owns every cross-field
  invariant, one function per section formats.
- Transport errors are one exception (`http.Unreachable`), so no module outside `http.py`
  catches httpx types. Tests swap the transport through one seam (`http.transport`).
- `submit_planning_request` keeps its no-retry, uncertain-outcome and conflict logic
  line for line; only the transport call changed.

## Implemented behaviour

### Module map (old → new)

| Old | New |
| --- | --- |
| `frontend/planning_client.py` (submit, fetch) | `frontend/api/cases.py` (`submit_planning_request`, `fetch_planning_case`, `FINAL_DECISION_CONFLICT`, URL helpers) |
| `frontend/planning_client.py` (`PlanningDisplay`, `_map_case` and helpers) | `frontend/api/case_view.py` (git rename keeps history) |
| `frontend/planning_library_client.py` | `frontend/api/library.py` (`fetch_library`, new `fetch_scenarios`, `library_row`) |
| `frontend/planning_pdf_client.py` | `frontend/api/documents.py` (`fetch_planning_pdf`, `PlanningPDF`, `FILENAMES`) |
| `frontend/supplier_overview_client.py` | `frontend/api/suppliers.py` (`fetch_supplier_overview`, `map_overview`, `CHART_KPIS`) |
| `frontend/odoo_history_client.py` | `frontend/api/odoo_history.py` (`fetch_quotation_groups`, `fetch_odoo_history(group_id)`, `group_row`, `quotation_rows`) |
| `frontend/parsing.py` | `frontend/api/parsing.py` (+ `is_uuid`, the one canonical-UUID guard) |
| `planning_client._supplier_label`, `_product_label`, `planning_library_client._product`, `supplier_overview_client._name` | `frontend/api/labels.py` (`supplier_label`, `product_label`) |
| `state_creation._bounded_form_integer` | `state_creation.bounded_form_integer` (public; also used by `state_scenarios`) |
| — | `frontend/api/http.py` (`send`, `get_json`, `get_bytes`, `TIMEOUT`, `LONG_TIMEOUT`, `DATA_ERRORS`, `TokenMissing`, `Unreachable`, `transport`) |

### Request policy (`http.py`)

Every request: `Authorization: Bearer <token>` from `settings` (read only in `_headers`),
`trust_env=False` (proxy variables ignored), `follow_redirects=False`, no automatic retry.
An empty, non-ASCII or whitespace-containing token sends nothing (`TokenMissing`).

| Call | Tier | Before | After | Why |
| --- | --- | --- | --- | --- |
| `GET planning-cases/{id}` | `TIMEOUT` | 7 s | 15 s | Stored read from PostgreSQL |
| `GET planning-cases` (library), `…/{id}/scenarios` | `TIMEOUT` | 15 s | 15 s | Stored read |
| `GET …/{id}/suppliers` | `TIMEOUT` | 10 s | 15 s | Stored snapshot read |
| `GET quotation-groups` | `LONG_TIMEOUT` | 30 s | 45 s | Backend reads Odoo live |
| `GET …/odoo-history/preview` | `LONG_TIMEOUT` | 30 s | 45 s | Backend reads Odoo history and scores |
| `GET …/approved-pdf/{hash}` | `LONG_TIMEOUT` | 45 s | 45 s | PDF rendered per request |
| `POST from-odoo-history`, `…/scenarios`, `…/final-decision` | `LONG_TIMEOUT` | 45 s | 45 s | Reads Odoo / solves the MILP / stores |

### Error mapping (`http.get_json`, used by every read)

Token missing → `err_token`. Unreachable (connection, timeout, protocol) or non-200 →
the resource's `unavailable` key, or `statuses[code]` when given. A response the parser
rejects (`ValueError`, `TypeError`, `KeyError`, `AttributeError`, `ArithmeticError`) →
the resource's `invalid` key.

| Resource | unavailable | invalid | statuses |
| --- | --- | --- | --- |
| case | `err_case_unavailable` | `err_case_invalid` | 404 `err_case_missing`, 401/403 `err_rejected` |
| library, scenarios | `err_library` | `err_library_data` | — |
| suppliers | `err_suppliers` | `err_suppliers` | — |
| quotation groups | `err_groups` | `err_groups_data` | — |
| history preview | `err_preview` | `err_preview_data` | — |

The PDF and the save keep their own mapping (all PDF failures → `err_pdf`, including a
missing token as before; saves: unchanged status table, `err_token`, and `err_uncertain`
with `uncertain=True` for transport failures and unexpected answers).

### `_map_case` → functions (`case_view.py`)

| Function | Produces |
| --- | --- |
| `map_case(payload, expected_id, lang)` | Validates, then assembles `PlanningDisplay` from the sections |
| `validate_case(payload, expected_id)` | Identity, snapshot version, status, input kind, demand, parent, supplier joins, comparison joins/totals, plan allocations/costs/exposure, assessment source/class/score, final decision and approved-content hash |
| `summary(case)` | Overview facts: identity, demand, dates, status, policy, buyer diagnostics |
| `suppliers(case)` | Base vs saved supplier terms (what-if form rows) |
| `alternatives(case)` | Plan count, minimum cost, trade-off sentence or why no alternative |
| `plan_rows(case)` | Plan rows and allocation rows |
| `scenario_comparison(case)` | Changed assumptions, deltas, per-supplier change rows |
| `audit(case)` | Assessments, provenance, raw explanations, snapshot JSON |
| `decision(payload, plans, lang)` | Recorded human decision fields |

Each has a one-line docstring. Section functions still parse single values strictly
(`_decimal`, `_integer`, `required_string`) and raise on malformed values.

### Tests

- Imports and patch targets moved to `frontend.api.*`; `patch_client` patches one place
  per name (the mixins call `<module>.<name>`), new `fetch_scenarios` entry.
- New seam: `tests.helpers.frontend_patching.use_transport` and the `frontend_api` fixture
  (`tests/conftest.py`, token + transport) replace per-call `url, token, transport=` args.
- New focused tests in `tests/test_frontend_config.py`: the shared error mapping (6 cases),
  no request without a usable token (3), Bearer header and timeout tier per call kind (all
  8 call kinds), non-canonical identities never reach a URL.

## Evidence (commands actually run, Windows, Python 3.11.15, worktree `.venv`)

- `python -m tools.dev check` on the final tree — ruff format/check, compileall,
  477 passed, 51 deselected, `uv pip check` OK.
- `pytest -m e2e --browser chromium` — 3 passed, 525 deselected (3 min 9 s; disposable
  Compose PostgreSQL, Reflex + FastAPI, fixture Odoo).
- `ponytail-review` over the diff: one finding fixed (the timeout test keyed GET and POST
  `…/scenarios` to the same entry, so the GET tier was not asserted; now keyed by method).
- Done-criteria greps: `rg -n "httpx\." frontend` → only `frontend/api/http.py`;
  `rg -n "get_secret_value" frontend` → only `frontend/api/http.py:33`;
  `rg -n "from frontend\.[a-z_.]+ import _" frontend tests` → 3 remaining hits, all
  pre-existing tests of view/state helpers, not API-client code (R5 scope):
  `tests/test_frontend_presentation.py` imports `state_case._card`, `planning.pdf._viewer_texts`,
  `planning.library._filters`.
- Old vs new presentation on real data (scratch script, dev planning DB, API running):
  `main`'s `_map_case`, `library_row` and `map_overview` against the new functions on
  106 stored cases (20 bases + 86 scenarios, incl. infeasible, approved, No-award and the
  new cases below) in hu and en — every `PlanningDisplay` field, supplier overview and
  library row identical.
- Validation split: 9,600 random mutations (delete / null / wrong type / negative / huge /
  duplicate list item) of 12 stored payloads — old and new accept and reject exactly the
  same payloads, with identical output when accepted.
- Built-in browser (`tools.dev api` + `ui` from this worktree, dev DB and Odoo in Podman):
  - Home: recent cases listed; "awaiting decision" shows `err_library` because the backend
    answers 503 `invalid_library_data` for `status=draft` (pre-P2 rows; unchanged).
  - Cases: 20 rows, search by id prefix (1 row), expanding a base case's 9 scenarios,
    next page → 503 from the same old rows → "Saved cases are unavailable. Retry."
  - Case `a6d1d58a…`: Overview, Suppliers (cards and charts), Plans, What-if (base scenario
    list), Decision & PDF (approved PDF in the viewer; download link
    `jovahagyott-beszerzesi-terv-a6d1d58a-…-866dd2a00969-hu.pdf`, blob checked: 29,366 bytes,
    `%PDF-1.4` … `%%EOF`), Audit (audit appendix `audit-melleklet-…-hu.pdf`).
  - What-if: capacity change for Kalocsa Profiles to 90 → saved child `84062c46…`, comparison
    +2,305.50 HUF / +0.5 points shown.
  - HU → EN switch relabels without requests; checked at 375 px and desktop.
  - Wizard (EN, 375 px): quotation groups listed from Odoo, group 1 history preview, demand,
    supplier terms, review, "Calculate and save plans" → draft `900eaa90…`; recorded the
    decision (Alternative 1, "R4 verification buyer") → "Decision recorded."
  - Errors: unknown UUID → "This case was not found."; `case_id=NOT-A-UUID` → "Invalid case
    identifier."; API stopped → case "cannot be loaded right now", Cases "Saved cases are
    unavailable", New procurement Refresh → "Open RFQs are unavailable. Check the Odoo
    connection." (375 px).

## PR review follow-up (2026-11-08)

All seven review findings were checked against the code and were valid; each fix has a
regression test that fails without it.

- `case_view.validate_case` compares plan exposure as exact integers
  (`0 <= numerator <= denominator`). Before, a 28-digit Decimal quotient rounded e.g.
  `(10**30 + 1) / 10**30` to 1 and accepted it (inherited from `main`). Test: `exposure`
  fault in `test_malformed_snapshots_fail_closed`.
- `cases.submit_planning_request`: a 409/422 (or 503) on `from-odoo-history` with a non-JSON
  or non-object body no longer counts as an uncertain save; the status decides (409
  `err_key_conflict`, 422 `err_odoo_changed`, 503 stays uncertain). Before, the JSON
  parse error offered a same-key retry for a definite rejection (inherited from `main`).
- `http.get_bytes` takes `check_headers`, run before any body byte is read;
  `documents.fetch_planning_pdf` passes its header check there, so a wrong document is
  rejected without downloading up to 2 MB.
- `http._headers` also rejects tokens with NUL or other control characters (before, the
  request failed in the transport and a save was reported as uncertain).
- Tests: the uppercase-identity case uses a fixed UUID with letters (a random `uuid4` could
  be all digits after the version nibble); timeout assertions use the documented 15 / 45 s
  instead of the constants they test.
- One-line docstrings on every function and class in `frontend/api/` and
  `tests/helpers/frontend_patching.py` (the PR's docstring-coverage check). Test functions
  were not given docstrings; whether the PR check counts them was not verified.
- Evidence: `python -m tools.dev check` — 482 passed, 51 deselected; ruff, compileall and
  `uv pip check` OK. Not re-run: e2e and the browser walkthrough (no UI-visible change
  except the rejection texts above).

## Limitations

- Two error texts change on a transport failure (backend down or timeout) because there is
  now one mapping: quotation groups `err_groups_data` → `err_groups`, history preview
  `err_preview_data` → `err_preview`. The new texts say "unavailable"; the old ones said the
  data "could not be verified", which was wrong for a connection error. Non-200 and invalid
  data keep their old texts.
- A missing or unsafe service token now shows `err_token` on library, supplier, group and
  preview reads (before: the request went out and the 401 showed the resource's
  "unavailable" text). Only a misconfiguration reaches this.
- Timeouts changed for three reads (see the table); no displayed value depends on them.
- `fetch_scenarios` refuses a non-canonical case id before sending (`err_library`); before,
  the string went into the URL.
- Browser run setup in this worktree (all ignored paths): its own `.venv` (the main
  `.venv`'s editable install points `frontend` at the main checkout), a copy of `.env`, and a
  copy of `.artifacts/ml/model` (without it the backend reports "compatible model not
  available" and the wizard stops at supplier terms).
- Dev DB now holds the new draft-then-approved case `900eaa90…` and scenario `84062c46…`
  created by this check.

## Thesis relevance

Ch. 6 (implementation, frontend architecture): the Reflex UI reaches the backend through
one small client layer with a stated timeout and error policy; the stored-case
presentation separates validation (fail closed on any inconsistent record) from
formatting, which makes the "API-only replaceable frontend" principle concrete.
