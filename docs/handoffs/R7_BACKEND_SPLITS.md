# R7 — Readable backend units and models explained in the code

Date 2026-11-07, branch `claude/r7-backend-splits-b77cb4` on main `a29da04`, uncommitted.

## Problem

The backend's central steps were hard to read and learn from. The PDF renderer was one
827-line module whose `_render` (457 lines) held two closures of 142 and 131 lines and a
270-line text table. Eight use-case and core functions ran 80–170 lines mixing several
jobs (e.g. stored-case revalidation: metadata, provenance, risk replay and plan proofs
in one block). The MILP formulation was only in `docs/MODEL_MILP.md`; the adapter copied
its error handling three times and its cost cap twice. The Decision Tree's feature
ranges were unexplained numbers, the leaf-score rounding was written twice, and the
stored-fraction decoder three times. One CI run failed the solver determinism test.

## Decision

Behaviour-preserving split into named steps, each with a plain-English docstring, only
where a reader gains a self-explaining step (no new layers or interfaces). Persisted
identifiers, number formatting, the HTTP contract, stored JSON and the rendered PDFs are
unchanged and were compared byte for byte against `HEAD` (see Evidence). The flaky test
was diagnosed as environmental (wall-clock budget on an overloaded runner), so the solver
is unchanged and the test was made independent of the budget.

## Implemented behaviour — where things are now

### PDF (`document_adapter/`)

| Module | Contents |
| --- | --- |
| `approved_pdf.py` | Entry points `render_plan_pdf`, `render_audit_pdf`; `_render` (31 lines): font, `Formatter`, story, page template, footer |
| `plan_document.py` | `plan_story` → `_summary_page` (`_allocation_table`, `_assessment_table`), `_order_line_page` per supplier, `_verification_block`; `plan_name` |
| `audit_document.py` | `audit_story` → `_data_source_and_model`, `_assessments`, `_optimization`, `_decision_log`, identity block, `_provenance` |
| `texts.py` | `TEXT` (HU/EN), `RECORDED_TEXT_HU`, `SOLVER_OUTCOME_HU` |
| `formatting.py` | `UNITS` (the one backend copy; the frontend keeps its own in `frontend/i18n/format.py`) and `Formatter`: Hungarian decimal comma and space grouping, dates, money, quantities, recorded sentences, solver outcomes |
| `layout.py` | `FONT`, `LAYOUT_VERSION` (`layout-v7`, see the review fixes below), styles, `register_font`, `check_glyphs`, `paragraph`, `fields`, `grid` |

### Long functions → named steps

| Before (lines) | After |
| --- | --- |
| `approved_pdf._render` 457 (closures 142 + 131) | 31; pages as listed above, longest `_order_line_page` 67 (one flat list of flowables) |
| `odoo_planning_input.assemble_odoo_planning_input` 168 | 69: `_check_group_and_sources`, `_checked_offer_line`, `_supplier_provenance`, `_requirement_provenance` (+ `_entry`, `_odoo`) |
| `rules.checked_plan` 134 | 55: `_check_allocations`, `_supplier_explanations`, `_plan_explanations` |
| `planning_decisions._saved_evidence` 125 | 22: `_check_model_and_solver`, `_check_provenance`, `_check_contracts`, `_check_risk_replay`, `_check_plan_proofs` |
| `planning_cases.create_planning_case` 125 | 73 (17 of them docstring): `_base_inputs`, `_scenario_inputs` (both return `_CaseInputs`), `_planned_snapshot` |
| `planner.plan_procurement` 120 | 67: `_minimum_cost_stage`, `_alternative_stage` |
| `comparison_case_reader.list_quotation_groups` 95 / `read_comparison_case` 79 | 35 / 39: shared `_read_orders`, `_read_lines`, `_read_partners`, and `_read_groups` |
| `planning_cases.validate_snapshot` 89 | 44: `_check_model_evidence`, `_check_recorded_plans`, `_check_case_row` |
| `planning_library.case_summary` 84 | 48: `_scenario_changes` |
| `supplier_overview.supplier_overview` 82 | 59: `_history`, `_assessment` |

Longest functions now in the listed packages (AST measure, `def` to last line, docstring
included): `risk_inputs` 77 (12-line docstring), `odoo_history_preview` 74,
`create_planning_case` 73, `bind_controlled_odoo_input` 73, `read_result` 71 — none above
80. Before, 13 functions were 80 lines or longer.

### Models explained and single homes

- `optimization_adapter/pulp_cbc.py`: module docstring with the formulation (below);
  docstrings for `minimum_cost`, `risk_alternative`, `diversified_alternative`, `_run`,
  `_tie_break`, `_integer_values`, `_scale`, `_model`, `EncodedModel`. The three copied
  `try/except` blocks are one decorator `_failures_as_outcomes`; the cost cap is
  `_cost_cap`; "minimize, then fix the objective at its optimum" is `_minimize_and_fix`
  (same CBC runs, same constraint names).
- `supplier_evaluation/contracts.py`: `feature_vector` docstring explains every range and
  what happens outside it; `SCORE_STEP` and `leaf_score(counts)` are the one leaf-score
  rule, used by `HistoryTreeModel.infer` and the `Assessment` check. `planning_decisions`
  uses `SCORE_STEP` to restore the four-place form before the risk replay (comment says
  why). `HistoryTreeModel.infer` and `procurement_planning.risk_inputs` have docstrings.
- `application/planning_serialization.read_fraction`: the one decoder of stored
  `{"numerator", "denominator"}` values (validating), used by `read_result`, the scenario
  comparison and the PDF.
- `docs/ARCHITECTURE.md` (optimization and document adapter rows) and the source line of
  `docs/MODEL_MILP.md` name the new places.

## MILP formulation as written in the `pulp_cbc.py` docstring

Data for one product and suppliers i = 1..N, sorted by supplier id: demand Q, unit price
p_i, risk score r_i (0..1), positive-use range [L_i, U_i] from `rules.bounds` (a used
supplier gets at least L_i — MOQ, price and delivery ranges — and at most U_i — capacity,
concentration limit ⌊c·Q⌋, price and delivery ranges; U_i = 0 when excluded), maximum
supplier count K.

Variables: x_i integer, 0 ≤ x_i ≤ U_i (quantity); y_i binary (supplier used).

Constraints of every model: Σ x_i = Q (`approved_demand`); Σ y_i ≤ min(K, N)
(`max_supplier_count`); x_i ≤ U_i·y_i (`activation_upper_i`); x_i ≥ L_i·y_i
(`positive_use_lower_i`; an excluded supplier uses 1 instead of L_i, so it cannot be
activated). Cost C(x) = Σ p_i x_i, risk R(x) = Σ r_i x_i, exposure R(x)/Q.

Lexicographic phases, each solved to proven optimality and then fixed with an equality:
1. `minimum_cost`: min C(x) → C*.
2. `risk_alternative(ε)` (ε-constraint method): C(x) ≤ (1+ε)·C*, min R(x), then min C(x).
3. `diversified_alternative(ε_d)`: integer m with x_i ≤ m, C(x) ≤ (1+ε_d)·C*,
   R(x) ≤ R(x_min); min m, then min R(x), then min C(x).
4. Deterministic tie-break: in supplier-id order maximize x_i and fix it (the last follows
   from demand), so equal-cost optima give the same plan for any input order.

Prices and scores are scaled to the smallest integers with the same ratios; caps are
rounded down in those units; every answer is rechecked in exact integers; CBC runs
single-threaded with a fixed seed and the remaining planning budget as time limit;
running out of time gives `NO_PROVEN_OPTIMUM`, never an unproven plan.

## Flaky test diagnosis

`tests/test_validation_tools.py::test_solver_matches_exhaustive_reference_on_controlled_variants`
failed once (Quality run 42255197688, attempt 1) with `assert (False)` on
`repeated_identical and permutation_identical` for `equal_prices_tie_break`;
`reference_match` had passed, so the first solve was the correct, proven plan.

Reading the solver path, the hypotheses from the task were ruled out:
- Tie-break scaling: there is none; each tie-break step is its own exact solve of
  "maximize x_i", then an equality lock.
- Supplier order: `_model` sorts suppliers by id before encoding, so a permuted request
  produces the identical model.
- Threads/seed: CBC runs with `threads=1`, fixed `randomSeed`/`randomCbcSeed`, `gapRel=0`,
  `gapAbs=0`.
- Float vs Decimal: all coefficients are exact integers; answers are rechecked exactly.
- The only code paths that let two solves of the same request differ are the shared
  wall-clock budget (`_run` returns `NO_PROVEN_OPTIMUM` when CBC stops on its time limit
  or the deadline has passed) and a CBC/file failure (`SOLVER_ERROR`). Both make the
  repeat non-optimal, i.e. different from the first result, while the first result still
  matches the reference — exactly the observed failure.

Experiments (scratch scripts, not committed):
- Normal budget: the variant needs 19 CBC runs and 0.26–0.28 s per plan here.
- Tiny budgets 0.02–0.2 s: repeats end with `no_proven_optimum` after 0–3 completed stages
  and differ from each other — the observed symptom.
- 30 repeats with 48 CPU-burning processes on 16 CPUs: all optimal and identical (Windows
  kept the solve at 0.27–0.38 s, so the overload of the CI VM was not reproduced).
- CI evidence of the overload: the same fast suite took 42–43 s on normal runs but 149 s
  (the failing run), 200 s and 251 s on the same afternoon's runs.
- Determinism across processes: the 420-request golden set below was solved by two
  different processes (HEAD and this tree) with identical results.

Conclusion: environmental, not a solver defect. The determinism test now gives all its
solves one shared 120 s budget (about 25 times its 4.5 s local run, well inside the
10-minute quality job; it patches `tools.milp_evaluation.plan_procurement` with a
wrapper). It still requires identical repeated and permuted results, but one slow
solve no longer breaks it, and its total time stays bounded. The assertion message lists every
solve's status and CBC run count, so a real nondeterminism would show `optimal` statuses
with different results. A separate test,
`test_controlled_variants_are_proven_within_the_production_budget`, solves each variant
once with the production 30 s budget and checks its status, so a solver that becomes too
slow for production is still caught. `tools/` is unchanged (out of scope). A hard kill
of a hung CBC process would need `pytest-timeout`, which is not a dependency; CBC itself
stops at its time limit.

## Evidence (commands actually run)

Baselines were taken from `HEAD` (`git archive HEAD` into a scratch folder, run with this
tree's venv and `PYTHONPATH` set to that copy), then compared with this tree after every
split. Scratch scripts are not committed.

- **PDF, byte-identical.** Four approved contents were dumped from the test fixtures
  (minimum-cost plan, alternative 1, the same alternative named as balanced, and a variant
  with an incomplete comparison, a missing quotation, a flipped concentration limit and MOQ,
  a long rationale with markup and Hungarian accents, and tripled provenance). Each was
  rendered as plan and audit in HU and EN (16 PDFs) with ReportLab's `rl_config.invariant = 1`
  (no timestamps or random document ids), before and after the split. Result:
  **identical bytes and identical `pypdf` text for all 16**. Rendering twice before the split
  was also identical, so the method is deterministic. After the row-splitting fix below,
  the same 16 PDFs are still byte-identical; only the renderer version string changed.
- **Plans and explanations.** 420 seeded requests (60 random cases with 2–7 suppliers,
  random prices, capacities, MOQs, availability, concentration, scores, 1–3 epsilons, half
  with a balanced stage, plus the six evaluation variants each and a cost-only variant):
  142 optimal, 218 infeasible, 60 invalid input. `json_value(plan_procurement(...))` with
  real CBC: **identical** to `HEAD`.
- **HTTP and stored JSON.** A temporary in-process test (fake Odoo, trained model, real
  CBC): base case, seven scenarios (outage, all suppliers out, capacity, demand, price,
  combined, one rejected with 422), HU/EN supplier overview, approval of plan 1, GET case,
  `case_summary` of every case, preview, quotation groups, every stored snapshot and
  decision record, and every Odoo JSON-2 request body. After masking case UUIDs, times and
  the approved-content hash (it covers the case id): **identical** to `HEAD`. Snapshot
  hashes were compared unmasked. One note: the order of the states in the open-quotation
  filter comes from a Python set and varies between processes; the comparison sorts it.
- **Flaky test.** `pytest tests/test_validation_tools.py` 25 times in a row:
  **25 × 15 passed** (15.2–20.5 s each) with the first fix, and **25 × 16 passed** (30.9–35.7 s each) with the
  final version (shared budget plus the production-budget test).
- `python -m tools.dev check` (final tree): format, lint, compile, **471 passed** (466 + the
  five tests added by the review fixes), 51 deselected, `uv pip check` OK. Plans, HTTP and
  stored JSON, Odoo request bodies and the 16 PDFs were compared with `HEAD` again after
  the review fixes: identical (PDF bytes and page text; only the renderer version string
  is now `layout-v7`).
- `pytest -m "integration and not e2e"` with `RUN_ODOO_HISTORY_LIVE=true` against the
  disposable test DB (`podman compose -f infra/persistence/compose.test.yaml up -d`, with the
  `.venv` `podman-compose.exe` as provider and the `.env` password) and this tree's API on
  port 8000 for the two running-service checks: **46 passed, 2 skipped** (opt-in
  `RUN_T6_LIVE_CONTRACTS` / `RUN_T7S_LIVE_CONTRACTS`). An earlier run without the API and
  without live history gave 42 passed, 4 skipped and 2 failed (connection refused on port
  8000). After the review fixes (2026-11-09; Odoo started with `tools.dev odoo-up`, this
  tree's API on port 8000): **44 passed, 4 skipped** without live history. With
  `RUN_ODOO_HISTORY_LIVE=true`, 44 passed and the two live-history tests failed with
  HTTP 401: the renewed key expired at 2026-11-08 00:00. Those two tests are unrun for
  the final tree.
- `python -m tools.dev demo` (renewed Odoo key): complete, 23.6 s. The same demo from the
  `HEAD` copy: plans, allocations, costs, exposures, scenario statuses, supplier
  assessments and stored replay are **identical**. Only case ids, hashes, timings and the
  PDF byte counts differ, by a few bytes, because the compressed content carries different
  case ids. `docs/evidence/P4_DEMO_REPORT.json` was restored to its committed version.
- AST length scan (script over the eight backend packages): before, 13 functions were
  80 lines or longer; after, none (table above).
- `ponytail-review` over the diff: two findings, both fixed. (1) A new comment in
  `_base_inputs` described the provenance override wrongly. (2) The planner loop
  told plans and failures apart by `SolveOutcome`, so a duck-typed solver answer could
  crash outside the `try`; it now checks `ProcurementPlan`, the type the planner builds itself.

### Review fixes (after the first handoff)

Five inline review comments and one nitpick were checked against the code. All were still valid and are fixed:

- `assemble_odoo_planning_input` docstring: business violations raise
  `InvalidPlanningInput` with a code; a non-UTC timestamp or a missing, misnamed or
  future source attribution raises a plain `ValueError` without a code.
- Planner: the non-optimal alternative outcome (`status`, `code`) is now read inside the
  `try`. A malformed solver answer becomes a `SOLVER_ERROR` run
  (`alternative_verification_failed`), and the verified minimum-cost plan is kept. New test
  `test_malformed_alternative_outcome_is_a_solver_error_that_keeps_the_minimum`; it fails
  on the previous loop.
- PDF label/value tables (`layout.fields`) may now split a row across pages
  (`splitInRow=1`, as `grid` already did). Before, a valid rationale of about 400 short lines
  (1,998 characters, under the 2,000 limit) raised ReportLab `LayoutError` in both
  documents. Every retry failed the same way, so the approved case never got a PDF. This
  bug predates R7. `LAYOUT_VERSION` is raised to `layout-v7` because a row that used to
  move whole to the next page may now split. Stored PDFs keep their bytes; the 16
  reference PDFs are byte-identical. New test
  `test_rationale_taller_than_a_page_continues_on_the_next_page` (HU/EN, plan and audit);
  it fails with `LayoutError` without the fix.
- Odoo reader: `_read_lines` now also rejects a line whose `order_id` names another order
  than the one listing it, or a line listed by two orders. The complete-set check
  stays. Before, such a line was silently attached to another quotation or dropped. The request bodies
  sent to Odoo are unchanged. New parametrized test
  `test_reader_rejects_a_line_that_does_not_belong_to_the_order_listing_it`; both cases
  fail without the check.
- Validation test runtime and production budget: see the flaky-test conclusion above.
  The nitpick asked to keep 600 s per solve. That conflicts with the requested bound
  under the 10-minute CI job, so the solves share one 120 s test budget instead.

## Not run (name explicitly)

- Browser e2e (`pytest -m e2e`): no UI change in this increment.
- Hosted CI. Local success is not hosted CI; the flaky-test fix is proven locally only.
- Live Odoo history tests and `tools.dev demo` on the final tree (after the review fixes):
  the Odoo history key expired; they passed on the tree before the review fixes.

## Limitations

- Error precedence inside one malformed input can differ only where two checks now sit
  in different functions and both fail at once; codes are unchanged. In the Odoo
  assembly the original check order was kept on purpose.
- The diversified adapter checks the cost cap and the risk cap against the integer
  budget separately (same `unsupported_numeric_contract` code; the message never leaves
  the adapter).
- `_CaseInputs` is a small private record introduced so the base and scenario branches
  return the same named values instead of a six-tuple.
- `docs/MODEL_ML.md` does not yet mention `leaf_score`/`SCORE_STEP`; R9 consolidates docs.

## Thesis relevance

- MILP chapter (5): the `pulp_cbc.py` docstring is a compact, code-adjacent statement of
  variables, constraints, lexicographic phases, ε-constraint alternatives, the balanced
  plan and the deterministic tie-break; the flaky-test analysis is a concrete argument for
  why the solver is deterministic and where a time budget makes results incomplete
  (`no_proven_optimum`) rather than different.
- ML chapter: `feature_vector` documents the plausibility ranges and the no-fallback rule;
  `leaf_score` states the score definition (leaf share of problematic training rows,
  four places, half up); `risk_inputs` documents the ML → MILP bridge.
- Architecture/implementation chapter: the PDF and use-case modules now read as named
  steps (plan document, audit appendix, stored-case revalidation, case creation).
