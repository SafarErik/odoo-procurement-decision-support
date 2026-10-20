# Balanced alternative (min–max supplier share) and PDF order-line title

Date: 2026-10-20. Working-tree increment on `feature/frontend-revamp`, on top of the
uncommitted [UI copy increment](UI_COPY_AND_ALTERNATIVES.md). The owner commits and
pushes; this work performs neither.

## Problem

1. Linear exposure Σrᵢxᵢ/Q never rewards splitting an order (L5), so most cases showed
   one alternative and none that limits dependence on a single supplier.
2. Each per-supplier PDF page was titled "Megrendelési javaslat" while the same page says
   it is not an Odoo purchase order; a printed copy reads as a contradiction.

## Decision

Owner chose option B (2026-10-20): a separate balanced alternative that minimises the
largest single-supplier quantity. Drafted as
[ADR-035 (proposal)](../adr/ADR-035-balanced-alternative.md); Drive registration is the
owner's step. K stays 2. PDF pages are retitled "Rendelési tétel – jóváhagyott terv" /
"Order line – approved plan"; the "not an Odoo purchase order" note stays.

## Implemented behavior

| Area | Change |
| --- | --- |
| MILP (`optimization_adapter/pulp_cbc.py`) | `diversified_alternative`: integer `m ≥ xᵢ`; cost ≤ (1+ε_d)·C*; exposure ≤ the minimum-cost plan's; min `m` → min exposure → min cost → existing tie-break. Exact integer encoding as before. |
| Core (`decision_core/planning`) | `PlanningPolicy.diversification_epsilon` (optional), `AlternativeRun.kind` (`risk`/`diversified`). The balanced stage runs after the ε stages, is deduplicated like them, and is rejected if it raises exposure or the largest share. |
| Records (`application/`) | Default-valued new fields are not written, so pre-existing snapshots keep exact JSON and hashes. Approval re-verification checks the (ε, kind) stage sequence and the balanced invariants. |
| API / preview | `PolicyRequest.diversification_epsilon` optional; Odoo preview default 0.2. |
| UI | A plan proved only by the balanced stage is "Kiegyensúlyozott terv" / "Balanced plan" (badge "kiegyensúlyozott" when it coincides with a risk alternative). Every plan card and the comparison table show "Legnagyobb függés egy szállítótól". The chart draws the balanced plan as its own series (square, label to the left); the policy line names the balanced allowance; an expandable note explains the measure. Table columns narrowed so four plans fit at 1440 px. |
| PDF | Order-line title, "Tétel adatai" section heading, balanced plan name, layout version `layout-v3`. Download filename `jovahagyott-beszerzesi-terv` / `approved-procurement-plan`. Already stored PDF artifacts are immutable and keep their old title. |
| Evaluation tool | `tools/milp_evaluation.py` exhaustive reference also computes the balanced optimum and reports ε_d. |

## Evidence (commands actually run)

In-memory replanning of saved cases (no writes), ε ∈ {0.05, 0.1, 0.2}, ε_d = 0.2:

| Case | Plans with K = 2 | Balanced plan |
| --- | --- | --- |
| 5f9b7b21 (5 suppliers) | 4 (min + 2 risk + balanced) | 100/100, largest share 60 % → 50 %, +7.9 %, exposure 33.3 |
| 52170388 (4 suppliers) | 3 (min + 1 risk + balanced) | 100/100, 60 % → 50 %, +2.5 %, exposure 33.3 |

With K = 3 (not adopted) the balanced plans reach 67/67/66 (largest share 34 %).

| Check | Result |
| --- | --- |
| `tests/test_balanced_alternative.py` | 8 passed: L5-shaped hand case, stage order, ε_d = 0 duplicate proof, 25 random instances against the exhaustive reference, exact old JSON, round trip, unknown kind rejected, supplier-order invariance |
| PDF / client / HTTP flow tests | balanced PDF name HU/EN and new title; client naming; full HTTP flow stores, verifies and approves a case whose last run is `diversified` |
| `python -m tools.dev check` | 526 passed; format, lint, compileall, dependency check passed |
| `pytest tests/e2e -m e2e --browser chromium` | 3 passed (disposable PostgreSQL/FastAPI/Reflex, fixture Odoo); the flow test now asserts the largest-share row and the balanced heading when present, and saves `plans-1440.png` |
| Visual check | e2e screenshot at 1440 px (disposable stack): four plan cards, four-column table without horizontal scroll, non-overlapping chart labels |

## Limitations

- Existing cases are immutable and keep their recorded alternatives and PDFs.
- `m` measures one supplier's worst single outage; correlation between suppliers and
  partial delivery are not modelled. Exposure is still linear (L5 partly addressed).
- K = 2 caps the balanced split at 50/50.
- The P4 latency/evaluation report (`tools/milp_evaluation.py` against seeded Odoo
  groups) was not rerun; its stored evidence predates this stage.
- Integration tests (PostgreSQL/Odoo) not run; no schema or Odoo access change.
- Drive (ADR register, FR-V2 text, thesis) not changed.

## Thesis chapter

Chapter 5: third lexicographic objective, its formal constraints, why min–max share
rather than HHI or PWL penalties, K = 2 consequence. Chapter 7: exhaustive-reference test
and the in-memory table above; evaluation rerun pending. Chapter 6: order-line PDF wording.
