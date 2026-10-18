# P4 — Validation and thesis support

Date: 2026-10-18. Branch: `feature/p4-validation` (from `main` at `62caf80`, after the P3
merge #48). Nothing committed; the owner commits. Plan: [REVAMP_PLAN.md](../REVAMP_PLAN.md)
§P4. Requirements touched: NFR-V2-02/03/04/06/08 and AC-V2-01…13 evidence (reproducible
tests, infeasible cases, full process, ML evaluation conventions), official task sentences
11 (reproducible tests) and 12 (further development). Drive was not changed.

## Problem

- The thesis evaluation chapter (7) needs reproducible, citable evidence on the final
  Odoo-history path; until now the full flow existed only as a P1/P2 manual run.
- The MILP/API latency evaluation (T18) was removed in P2 together with the synthetic demo
  path, so no measurement of the current system existed.
- `TRACEABILITY.md` rows 11–12 were open and the limitations for chapter 9 were scattered
  over the P1–P3 handoffs.

## Decisions

Owner (2026-10-18): P3 is merged; branch `feature/p4-validation` from `main`; the plan
was accepted ("mehet"); the guarded seeder may write 15 RFQs and 2 quotation groups into
`pdss_history_gen`; the `.env` secrets of this test environment were filled jointly (the
owner entered the Odoo API keys and the Odoo database passwords; this session generated
`API_SERVICE_TOKEN`, a new test-database password and a new planning-database password).

Own decisions:

1. **Extend, don't duplicate.** `tools/t17_demo.py` keeps the HTTP flow (now HU and EN PDF;
   supplier changes target the main supplier of the minimum-cost plan so outage, capacity
   and price scenarios actually change the plan). `tools/demo.py` only orchestrates it.
2. **Replay without Odoo and model is proved by a second API process**, not by mocks: same
   planning database, `ODOO_BASE_URL` set to a closed local port and no model directory.
   The demo refuses to report success if the Odoo preview still answers 200.
3. **Measured cases go to the disposable test database**, not to the development library,
   so 200+ evaluation cases do not flood the buyer's case list.
4. **Evaluation groups reuse the existing history.** 27 generated suppliers already have
   PRD-01 history, so only open RFQs and groups were written (no new purchase history).
   Selection is deterministic: the original four RFQ suppliers, then the suppliers with
   the most settled lines in the recent feature window.
5. **Reference optimum is independent of the core.** `tools/milp_evaluation.py` enumerates
   every integer allocation directly from the raw input (eligibility, ranges, K,
   concentration) and applies the documented lexicographic objective and tie-break; it
   imports neither the core bounds nor the solver.
6. **ML: no retraining.** A new offline `report` command re-evaluates the saved model on the
   stored export and compares it with the P1 report field by field.

## Implemented behavior

- `python -m tools.dev demo`: starts Odoo and the planning database, then `tools.demo`:
  own API on 127.0.0.1:8010 → open quotation group (default: the four-supplier group) →
  preview → case (minimum-cost plan + lower-exposure alternative) → nine scenarios (outage;
  capacity −1/6 and ×2; demand +25 % and −25 %; price +30 % and −20 %; combined; demand ×5)
  → approval of the alternative → separate No-award case → HU and EN PDF → supplier overview
  HU/EN → restart without Odoo and model → GET of every case, exact retry of every POST,
  byte-identical PDFs, identical overview, No-award PDF denied. Summary:
  [P4_DEMO_REPORT.json](../evidence/P4_DEMO_REPORT.json); full responses, PDFs and API log in
  `.artifacts/demo/`.
- `python -m tools.seed_odoo_history groups`: guarded like `apply` (exact database name,
  `pdss.seed_target`, administrator key, target verified before any write); writes one
  tax-free RFQ per supplier (origins `PDSS-GEN-P1:RFQ5:*`, `PDSS-GEN-P1:RFQ10:*`) and one
  quotation group per size; a rerun reuses them. `plan` also prints the selection.
- `python -m tools.milp_evaluation`: workloads 4/5/10 suppliers × ε sets {0.2} and
  {0.05, 0.1, 0.2}, 2 warm-ups + 30 measured runs each; create, scenario (price −10 %),
  exact retry, GET; an infeasible demand ×5 scenario per workload; then in-process solver
  checks on each stored request and on controlled variants (K = 3, equal prices for the
  tie-break, K = 1 infeasible, MOQ combination infeasible, demand ×5 infeasible).
- `python -m tools.train_history_model report`: offline re-evaluation →
  [P4_ML_REPORT_CHECK.json](../evidence/P4_ML_REPORT_CHECK.json).
- Docs: RUNBOOK §5.4, TESTING (validation runs), [TRACEABILITY.md](../TRACEABILITY.md)
  rows 4, 5, 7, 9–12, new [LIMITATIONS_AND_FUTURE_WORK.md](../LIMITATIONS_AND_FUTURE_WORK.md),
  README status.
- Tests: `tests/test_p4_validation.py` (7 fast tests: group selection and guarded writes
  with a mocked Odoo, reference optimum on controlled variants, a wrong plan is detected,
  nearest-rank p95, latency workload on the fixture Odoo, demo incl. refusal when Odoo is
  still reachable); `test_t17_demo.py` updated for two stored PDFs.

## Evidence (commands actually run, 2026-10-18, Windows 11, Python 3.11.15 uv venv)

Machine: Intel64 Family 6 Model 154 (16 logical CPUs); Podman 6.1.4 with Odoo 19 and
PostgreSQL 16 on the same machine; one uvicorn worker; CBC 2.10.3 via PuLP 3.3.0
(1 thread, seed 17).

### Seeding

| Command | Result |
| --- | --- |
| `python -m tools.seed_odoo_history groups` | group 2 (5 suppliers: SUP-01, 06, 11, 04, 23) and group 3 (10 suppliers: + SUP-24, 28, 40, 13, 16) created |
| same command again | both groups "already present", no writes |

### Demonstration

`python -m tools.dev demo` — complete in 16.5 s (HTTP flow 4.2 s), group 1 (200 Units
`[GEN] Steel bracket M8`, HUF, 4 suppliers), model `9b45987c…` (generated data):

| Step | Result |
| --- | --- |
| Base case | optimal; minimum cost 288,608 HUF (Fenyves 80, Kalocsa 120), exposure 0.60; alternative ε = 0.2: 293,132 HUF (Kalocsa 120, Alpha 80), exposure 0.333 |
| Scenarios (target Kalocsa) | outage +10,846; capacity 100: +1,537; capacity 240: −3,074; demand 250: **infeasible** (K = 2 × 120 cap); demand 150: −74,457.5; price +30 %: +10,846 (Kalocsa dropped); price −20 %: −33,900; combined: +31,420; demand 1000: **infeasible** |
| Decisions | alternative 1 approved; separate No-award recorded |
| PDF | HU 41,210 B and EN 39,472 B, same approved content hash |
| Replay without Odoo/model | Odoo preview 503; 13 exact retries = stored replays; all GETs, both PDFs and the HU/EN supplier overview identical; No-award PDF 422 |

### MILP/API evaluation

`python -m tools.milp_evaluation` — **PASSED**
([P4_MILP_EVALUATION.json](../evidence/P4_MILP_EVALUATION.json)). Latency in ms,
median / nearest-rank p95 / max of 30 measured runs:

| Suppliers | ε | Create | Scenario | Exact retry | GET | CBC runs | Solve (in-process) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 1 | 480 / 562 / 599 | 217 / 306 / 320 | 46 / 79 / 112 | 24 / 39 / 45 | 9 | 141 / 180 / 185 |
| 4 | 3 | 749 / 864 / 940 | 454 / 524 / 530 | 72 / 85 / 129 | 39 / 57 / 65 | 19 | 373 / 454 / 472 |
| 5 | 1 | 422 / 456 / 460 | 259 / 282 / 285 | 44 / 55 / 91 | 24 / 27 / 28 | 11 | 156 / 176 / 177 |
| 5 | 3 | 626 / 674 / 717 | 430 / 462 / 468 | 44 / 51 / 89 | 23 / 26 / 27 | 23 | 336 / 352 / 352 |
| 10 | 1 | 602 / 653 / 668 | 409 / 448 / 458 | 56 / 69 / 97 | 29 / 31 / 73 | 21 | 294 / 316 / 316 |
| 10 | 3 | 944 / 1006 / 1065 | 734 / 768 / 812 | 57 / 98 / 100 | 30 / 38 / 47 | 43 | 651 / 776 / 879 |

Correctness (21 checks): every stored request and variant matches the exhaustive
reference optimum (minimum-cost plan and every ε alternative), Σx = Q, ranges, K and
recomputed cost hold; 30 repeated solves and a supplier-permuted solve are identical;
the equal-price variant follows the documented tie-break; K = 1 and demand ×5 are
reported infeasible by the capacity diagnostics without a solver call, the MOQ
combination is proved infeasible by CBC (`interacting_constraints_infeasible`); each
workload's demand ×5 scenario is stored as `infeasible`. Every measured create in a
workload produced the same minimum-cost allocation.

Reading: solve time grows with the number of CBC runs (minimum cost + one per ε + the
tie-break, which fixes quantities supplier by supplier), so ε count and N dominate; the
scenario latency is mostly solve time; create adds the Odoo quotation + history read and
inference (~250–300 ms); a stored replay is 44–72 ms median. The 4-supplier/1-ε workload
ran first and shows higher spread than the 5-supplier one (warm caches after it).

### ML check

`python -m tools.train_history_model report` → `unchanged: true` (artifact hash, export
hash, train split id and the whole evaluation equal the P1 report). Tree macro F1 0.589,
expert rule 0.658, majority 0.409 — unchanged.

### Gates

| Check | Result |
| --- | --- |
| `python -m tools.dev check` | PASS — format, lint, compileall, **491 passed**, 51 deselected, `uv pip check` compatible |
| `pytest -m "integration and not e2e"` (disposable PostgreSQL 16, live Odoo, API on :8000, `RUN_ODOO_HISTORY_LIVE=true`) | **46 passed**, 3 skipped (T6 and 2× T7S fixture contracts); includes the 2 live Odoo-history tests and the runtime-service checks |
| `pytest -m e2e tests/e2e --browser chromium` (before the fix) | 1 passed, 1 failed: `test_cases_scenario_and_states_at_375_px` — search after returning to Cases left the list unfiltered; reproduced alone |
| same, after applying the library-search fix | 375 px test **passed**; the Odoo-flow test errored in setup (Reflex backend port already in use), rerun alone **passed** — both tests pass |
| `python -m tools.dev check` after the fix | PASS — **493 passed**, 51 deselected |

## Not verified / remaining

- **e2e failure found by P4, fixed in this branch.** Returning to Cases disabled the search
  form during the on_load reload, so an Enter submit was dropped. Fix (separate session,
  [P3_LIBRARY_SEARCH_RELOAD_FIX.md](P3_LIBRARY_SEARCH_RELOAD_FIX.md)): filters stay usable
  during a reload and a submit made mid-load is re-applied; one fast state test added.
- Review fixes after the runs above (CodeRabbit comments, applied and checked by
  `tools.dev check`, 496 passed): the PDF byte counts now match `P4_DEMO_REPORT.json`;
  live `demo` and `milp_evaluation` refuse cutoffs after 2027-02-28 (`REPRODUCTION_LAST_CUTOFF`,
  the end of the 134-day feature window of the seeded history) and point to the stored
  evidence; the evaluation reads its group ids from `.artifacts/seed/evaluation_groups.json`
  written by `seed_odoo_history groups` (the quotation listing shows only the newest 20 groups
  and has no seed tag); an unequal or identical TEST/DECISION database stops the run before
  migration; a non-optimal price-change scenario fails the run; `groups` completes an interrupted
  RFQ set. **Unrun after these fixes:** `groups` (rerun to write the id file), `demo` and
  `milp_evaluation`; the JSON evidence was produced by the earlier code.
- Hosted CI: not run (nothing pushed).
- Live T6/T7/T7S fixture contracts: skipped (fixtures not recreated in `pdss_history_gen`,
  as in P1–P3).
- The demo PDFs were checked by hash, size, content type, language header and identity on
  replay; their pages were not re-reviewed as images in P4.
- Unfamiliar-user usability and a screen-reader pass: not assessed (L12).
- The development planning database password was reset by this session (new value only in
  the ignored `.env`); the previous dev cases remain.

## Limitations

See [LIMITATIONS_AND_FUTURE_WORK.md](../LIMITATIONS_AND_FUTURE_WORK.md) (L1–L13). For P4
itself: timings are one machine with all services local, sequential requests, N ≤ 10
(API limit), the buyer default terms of the preview (K = 2, concentration 0.8, capacity
⌈0.6·Q⌉); they are descriptive, not an SLA. The reference enumeration is exhaustive only
for the evaluated sizes (Q = 200, K ≤ 3).

## Thesis chapter

Chapter 7 (evaluation: demonstration, MILP correctness and latency, ML re-check, gate
results), chapter 5 (MILP behaviour: CBC run count, infeasibility diagnostics, L5),
chapter 9 (further development from L1–L13), chapter 6 (one-command reproduction).
