# L6 — Provenance of suggested buyer terms, and the P4 evidence rerun

Date: 2026-10-19. Branch: `feature/cleanup` (on top of `bb9badf`,
which is `main` `e3cbf84` plus the project-baseline refresh). Not committed; the owner commits.
Requirements touched: FR-V2-01 (field-level provenance), FR-V2-04 / the 06 hybrid-input rule
on defaults, NFR-V2-03 (sources distinguishable). Limitation: L6.

## Problem

- The Odoo-history preview proposes buyer terms that Odoo does not hold: capacity ⌈0.6·Q⌉,
  "no MOQ", availability, price and delivery validity ranges 1–1000, a promised date, the
  required date, demand and the policy. They are tagged `buyer_default_terms`.
- When the buyer saved in the UI, `_odoo_request` overwrote every supplier source and the
  requirement source with `controlled_business_terms` / `t16-ui-odoo-terms-v1`. A stored case
  therefore claimed that every value was entered by the buyer, including the never-visible
  validity ranges and an unchanged "no MOQ". This contradicts the 06 rule that a missing MOQ
  or capacity must not be filled by a default without trace.
- The P4 review fixes had left `seed_odoo_history groups`, `tools.dev demo` and
  `tools.milp_evaluation` unrun; the P4 evidence JSON came from the earlier code.

## Decision (owner, 2026-10-19)

Clarify the rule on Drive 06 (a visible, source-tagged suggestion that the buyer reviews and
saves is buyer input, but the stored provenance must show which values stayed at the
suggestion; hidden defaults remain forbidden) and fix the provenance in code, keeping L6 as a
limitation (the values are not supplier-confirmed). No API or schema change: the per-supplier
and requirement source already reach every field-level provenance entry.

## Implemented behavior

- `frontend/planning/state_creation.py`: `_reviewed_source` compares each saved supplier with
  its preview suggestion over `capacity, available, minimum_order_quantity, price_quantities,
  delivery_quantities, promised_date`, and the requirement over `approved_quantity,
  required_date`. The source becomes `buyer_reviewed_terms` with reference
  `ui-odoo-terms-v2;kept-suggested=<fields>` (or `none`). The policy source stays the preview's
  `buyer_default_terms`, because the UI does not edit the policy.
- A value the buyer retyped identically counts as kept; the record says "equal to the
  suggestion", not "untouched".
- Cases created by `tools.t17_demo` / `tools.dev demo` send the preview terms unchanged and keep
  `buyer_default_terms`, as before. Stored cases are immutable and keep their original sources.
- Scenario deltas still use `controlled_business_terms` (they are always buyer-entered).
- Test: `tests/test_creation_review.py::test_saved_terms_record_which_values_were_kept_from_the_suggestion`.
- `docs/LIMITATIONS_AND_FUTURE_WORK.md` L6 updated.

## P4 evidence rerun (on `bb9badf`, clean code, live Odoo `pdss_history_gen`)

| Command | Result |
| --- | --- |
| `python -m tools.seed_odoo_history groups` | groups 2 and 3 "already present", no Odoo writes; `.artifacts/seed/evaluation_groups.json` written (`{"4": 1, "5": 2, "10": 3}`) |
| `python -m tools.dev demo` | complete in 15.4 s (HTTP flow 3.3 s); every business value identical to the previous report (minimum cost 288,608 HUF, exposure 0.60; alternative 293,132 HUF, 0.333; nine scenarios with the same deltas, two infeasible; approval, No-award, HU and EN PDF, replay without Odoo and model). Only case ids, content hashes, PDF sizes (±5 bytes from the new ids) and timings changed. `repository.dirty` is now `false` |
| `python -m tools.milp_evaluation` | PASSED; all 21 correctness checks match the exhaustive reference (only `solve_time` differs); one distinct minimum-cost allocation per workload; every demand ×5 scenario infeasible |

Median / p95 / max latency in ms (30 measured runs; previous run in brackets):

| Suppliers | ε | Create | Scenario | Exact retry | GET |
| --- | --- | --- | --- | --- | --- |
| 4 | 1 | 379/448/455 (480/562/599) | 186/222/225 (217/306/320) | 41/46/91 (46/79/112) | 22/23/24 (24/39/45) |
| 4 | 3 | 534/577/579 (748/864/940) | 331/370/383 (454/524/530) | 42/46/86 (72/85/129) | 22/24/26 (39/57/65) |
| 5 | 1 | 413/457/462 (422/456/460) | 263/291/295 (258/282/285) | 44/48/88 (44/55/91) | 23/26/26 (24/27/28) |
| 5 | 3 | 634/748/750 (626/674/717) | 433/464/476 (430/462/468) | 44/50/88 (44/51/89) | 23/26/26 (23/26/27) |
| 10 | 1 | 614/668/670 (602/653/668) | 415/454/480 (409/448/458) | 55/66/99 (56/69/96) | 29/32/72 (29/31/73) |
| 10 | 3 | 943/1022/1027 (944/1006/1065) | 743/800/817 (734/768/812) | 56/101/108 (57/98/100) | 30/32/33 (30/38/47) |

The 4-supplier workloads run first; the previous run showed the warm-up spread noted in the
P4 handoff, the 5- and 10-supplier numbers are within a few percent. The evaluation report
records `dirty: true` only because the regenerated demo report was not yet committed.

## Evidence (commands actually run, 2026-10-19, Windows, Python 3.11.15)

| Check | Result |
| --- | --- |
| `pytest tests/test_creation_review.py` | 14 passed |
| `python -m tools.dev check` | PASS — format, lint, compileall, **497 passed**, 51 deselected, `uv pip check` compatible |
| `pytest -m e2e tests/e2e --browser chromium` | **2 passed** (109 s) |

Not run: `pytest -m "integration and not e2e"` (no persistence change), hosted CI (nothing
pushed), a browser walk-through of the provenance table in the Audit drawer and the PDF audit
appendix with the new reference text.

## Limitation

- The suggested values are still defaults, not supplier facts (L6 stays).
- One source per supplier covers six fields; the reference lists the kept fields instead of a
  separate field-level source per value.
- Cases saved before this change keep `controlled_business_terms` for unchanged suggestions.

## Thesis chapter

Ch. 3 (data needs: suggested vs. confirmed terms), ch. 4/6 (provenance in the hybrid input),
ch. 7 (rerun evidence: unchanged correctness, latency table), ch. 9 (capacity and MOQ from Odoo).
