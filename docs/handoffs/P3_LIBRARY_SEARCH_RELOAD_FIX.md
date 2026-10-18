# P3 follow-up — Case search submitted during a reload is not lost

Date: 2026-10-18. Branch: `claude/busy-tereshkova-19e673` (from `main` at `62caf80`, after the
P3 merge #48). Not committed; the owner commits. Requirement touched: NFR-V2 usability
(Cases list filters, FR-V2-07 case library); found by the P4 validation e2e run.

## Problem

`tests/e2e/test_cases_scenarios_mobile_browser.py::test_cases_scenario_and_states_at_375_px`
failed 2 of 2 runs under machine load (251 s; it passed in P3 in 165 s). After opening a
case, running a price scenario and returning to Cases through the drawer, typing
`nincs-ilyen-termek` into the search and pressing Enter left the list unfiltered, so
"Nincs találat" never appeared.

## Cause

- `library_loaded` stays `true` from the first visit, so on return the Cases page renders
  with the filters **enabled**; Playwright's `fill()` succeeds at once.
- `library_on_load` then starts the reload and sets `library_loading`, which disabled the
  search box, both selects and the Refresh (submit) button (`disabled = ~library_loaded |
  library_loading` in `frontend/planning/library.py`).
- Enter on a disabled input does nothing, and a form whose submit button is disabled
  cannot be submitted implicitly either. The search was dropped without any message.
  The slower the machine, the wider the window between `fill()` and the reload delta.
- Second, smaller hole: had a submit reached `refresh_library` while a load ran, its
  `library_loading` guard returned early and the query was lost there too.

## Decision

Keep the filter form usable while an already-loaded list reloads (it is still disabled
before the very first load), and let the state remember the latest filters: a submit or
filter change during a load is stored and the running load re-reads with it when it ends.

## Implemented behavior

- `frontend/planning/library.py`: filters are disabled only by `~library_loaded`.
- `frontend/planning/state_library.py::refresh_library`: during a load it stores
  origin/status/search and marks the list stale; the running call loops once more with the
  newest filters. The `has_pending`/`is_loading` guard (an uncertain write) is unchanged.
- Tests (`tests/test_p3_frontend.py`):
  `test_a_search_submitted_during_a_library_reload_is_applied` (a submit landing in the
  middle of `library_on_load` produces a second GET with `q=nincs-ilyen-termek`) and
  `test_library_filters_stay_usable_while_a_loaded_list_reloads` (rendered search input is
  disabled only by `library_loaded`). Both failed on the unfixed code and pass with the fix.

## Evidence (commands actually run)

- `pytest tests/test_p3_frontend.py -k reload` on the unfixed code: 2 failed; with the fix:
  `pytest tests/test_p3_frontend.py`: 20 passed.
- `python -m tools.dev check`: exit 0, 486 passed, 51 deselected.
- `pytest -m e2e tests/e2e --browser chromium` (Podman, other stacks running in parallel):
  2 passed in 230.51 s.
- Built-in browser, 375 px, local `api` + `ui` on the dev database: open a case → drawer →
  Cases → search `nincs-ilyen-termek` + Enter shows "Nincs találat"; no horizontal scroll,
  no console errors. The exact reload window was not reproduced by hand (too short
  without load); the state test and the e2e cover it.

## Limitation

- During a reload the list still shows the loading state; a search typed then shows its
  result only after the extra GET (one more read-only request, never a re-score or re-solve).
- Hosted CI has not run this change.

## Thesis chapter

Implementation / frontend (Reflex state and event handling): an example of a UI race
between page `on_load` and user input, and why disabling inputs mid-reload loses intent.
