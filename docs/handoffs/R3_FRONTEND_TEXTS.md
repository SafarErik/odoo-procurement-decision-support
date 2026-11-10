# R3 — Frontend texts in one place

Date: 2026-11-06. Worktree branch `claude/r3-frontend-texts-5b91f4` on `main` `09d8bd2`.
Merged as PR #61. Drive was not changed. Technical debt only; no FR-V2/AC-V2
change.

## Problem

UI texts lived in three modules chained by import-time mutation (`frontend/i18n.py` ←
`i18n_ui.py` ← `i18n_revamp.py`, merged with `dict.update`). More hu/en pairs sat in
`odoo_history_client.ISSUES`, `planning_client._HISTORY_STEPS` (+ hard-coded relation words)
and a JS object in `planning/pdf.py`. The same text existed under several keys, and supplier
KPI labels/tree-path sentences existed twice with drifted wording (frontend vs
`application/supplier_overview.py`, which also feeds the approved PDF).

## Decision

- One package `frontend/i18n/`: `format.py` (formatters, unchanged code), `texts.py` (one
  `TEXT` dict, 19 page/topic sections), `__init__.py` (re-exports + `tr`). No mutation chain.
- The backend supplier overview API is the single owner of supplier KPI labels and tree-path
  sentences. The Suppliers tab already showed them; the Audit tab now shows them too
  (`CaseMixin.supplier_paths`, built from the loaded supplier cards). `_HISTORY_STEPS`,
  `_metric`, `_history_step` and `readable_path` are gone.
- PDF viewer texts are `pdf_*` / `audit_pdf_*` keys; `planning/pdf.py` embeds them as JSON
  generated from `TEXT` (`_viewer_texts`).
- `supplier_overview.py` was not changed: its wording is kept as the official one.
  `format_number` is not a one-line fix (no grouping; `92,5%` vs frontend `92,5 %`) → R7.

## Implemented behaviour

Old → new: `frontend/i18n.py` → `frontend/i18n/format.py` + `__init__.py` (`tr`);
`i18n.TEXT` + `i18n_ui.UI_TEXT` + `i18n_revamp.REVAMP_TEXT` → `frontend/i18n/texts.py`;
`odoo_history_client.ISSUES` → `issue_<code>`; `pdf.py` JS objects → `pdf_*`, `audit_pdf_*`
(+ existing `next_page`). Imports `from frontend.i18n import …` are unchanged.
All 469 remaining texts are byte-identical to the old values (checked by script).

Merged keys (identical hu and en, same meaning):

| Surviving key | Removed keys |
| --- | --- |
| `nav_cases` | `cases_title` |
| `open` | `open_scenario` |
| `scenario` | `badge_scenario`, `chart_scenario` |
| `approved_plan` | `state_approved` |
| `outcome` | `metric_outcome`, `col_outcome` |
| `demand` | `metric_demand`, `col_demand`, `step_demand` |
| `audit` | `audit_title` |
| `new_procurement` | `new_comparison`, `nav_rfqs` |
| `min_cost` | `col_min_cost`, `kpi_min_cost` |
| `record_decision` | `step_decide` |
| `review_decision` | `review_no_award` |
| `total_cost` | `chart_cost` |
| `base_case` | `chart_base`, `audit_base_id` |
| `plan` | `decision_plan`, `audit_plan` |

Not merged (en or hu differs): `unavailable`/`not_available`, `open_case`,
`compare_plans`/`plan_comparison`, `col_required`/`required_label`,
`supplier_terms_title`/`step_terms`.

Deleted keys: unused (no literal reference in `frontend/` or `tests/`, no dynamic prefix):
`not_usable`, `review_selection`, `supplier_terms_note`, `terms_below`, `terms_title`.
Frontend supplier-label copies whose `_map_case` fields no view read (removed with the
fields `class_key`, `class_label`, `class_meaning`, `score_display`, `history_summary`):
`class_regular`, `class_problematic`, `class_meaning_history`, `history_summary`. The
“Problematic = next 60 days …” definition text was therefore never on screen; owner may want
it shown (R5). Dynamic families kept: `status_*`, `kind_*`, `why_*`, `source_*`,
`quotation_*`, `issue_*`, `range_*`.

Wording changes (Audit tab tree path only; now the API/PDF wording):

| Item | Old (frontend) | New (backend) |
| --- | --- | --- |
| `order_count` HU | Lezárt beszerzési sorok | Lezárt rendelési sorok száma |
| `days_since_last_receipt` HU | Napok az utolsó átvétel óta | Utolsó beérkezés óta eltelt napok |
| relation HU | `Név: X – több mint Y.` | `Név: X – Y felett.` |
| relation EN | `Name (X) is at most/above Y.` | `Name: X, at most/above Y.` |
| percent HU | `92,5 %` (frontend `percent`) | `92,5%` (backend `format_number`) |
| feature names `delivery_schedule_adherence`, `historical_completed_count` | had frontend labels | dropped (not produced by the current model) |

Owner to confirm. Also noticed, not changed: “lezárt beszerzési sor” (`history_note`,
`err_history_insufficient`) vs “lezárt rendelési sor” (`kpi_help_sample`, backend).

## Evidence

- `python -m tools.dev check` on the final tree: 463 passed, 51 deselected (ruff format/check, pip check OK).
- New checks in `tests/test_frontend_presentation.py`: one key definition in `texts.py`;
  PDF viewer script generated from `TEXT`; Audit `supplier_paths` numbering + root fallback;
  quotation-group issue text (known code HU/EN, unknown code shown raw, no issue → empty).
- `pytest -m e2e --browser chromium`: 3 passed (full quotation → approval → HU/EN PDF flow,
  375 px scenario/error states, guided workspace).
- `ponytail-review` of the diff: one finding (issue lookup untested) → fixed with the test
  above; one note (Audit readable path depends on the supplier overview) → limitation below.
- `rg "i18n_ui|i18n_revamp|UI_TEXT|REVAMP_TEXT" -g '!docs/history/**'`: only past handoffs
  (`GUIDED_WORKSPACE.md`, `PDF_PLAN_AND_AUDIT_SPLIT.md`, `P3_FRONTEND_REVAMP.md`) and
  `docs/evidence/GUIDED_WORKSPACE.json` file hashes, left as historical records (R9).
- No Hungarian accented letters in `frontend/` outside `frontend/i18n/` (grep).
- Built-in browser (API + UI from this worktree, dev DB, Podman Odoo): Home HU/EN incl. the
  pending-list error state; case Overview, Suppliers, Plans, What if…?, Decision & PDF (PDF
  viewer “Page 1 of 3”, audit appendix viewer labels), Audit (API-worded tree paths) in HU
  and EN; a saved scenario in HU; wizard step 1 (groups, quotations) and step 2 with the
  “no compatible model” error. A script found no raw `TEXT` key in page text, aria-labels,
  placeholders or titles. Screenshots: Audit tree paths (HU, 737 px pane); at 375 px Suppliers
  (HU), Plans (EN), Home error state (EN), wizard step 1 (EN) and the menu drawer (EN);
  `scrollWidth` stayed 375 (no horizontal scroll).

## Limitations / unrun

- Not run: wizard steps 3–4 in the dev stack (both tried Odoo groups report no compatible
  model; e2e covers the full flow with fakes); integration tests (no persistence/Odoo
  change). Desktop width was the app pane (737 px), not 1280+.
- Audit tab readable tree sentences now come from the supplier overview API; if that call
  fails they are blank (the exact raw path stays, the Suppliers tab shows the error).
- Cases list shows 503 `invalid_library_data` for `limit=20` (Home `limit=5` works) and
  Home's pending list fails the same way: pre-P2 rows in the dev DB (R1 asked the owner to
  reset it). Not caused by this change; backend untouched.
- A library error message stays in the language it was fetched in until Retry (existing).
- `document_adapter/approved_pdf.py` comment still names `frontend/i18n.py ``_UNITS``` →
  now `frontend/i18n/format.py` (R7 owns the file).
- `supplier_overview.format_number`: no thousands grouping, `%` without space, float
  rounding (`0.0625` → `6,2%`) → R7.

## Thesis relevance

Ch. 6 (implementation): one text catalogue for the bilingual UI and one owner (backend) for
supplier-assessment wording shared by the UI and the approved PDF.
