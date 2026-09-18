# T6 provenance-aware hybrid decision-input assembly handoff

## Outcome

**T6 IMPLEMENTATION COMPLETE — LIVE ACCEPTANCE INCOMPLETE**

The code, fast contracts, architecture checks, read-only adapter, opt-in live tests,
and repository documentation are implemented. The controlled Odoo comparison
fixture was not created because the repository requires manual Odoo UI changes and
the available evidence does not support a safe automated administrator writer. As a
result, the two fixture-dependent live contracts were skipped and the full T6
acceptance claim remains blocked on the documented human setup and subsequent
read-only validation.

The branch starts from `main` commit `c2c4b18`; required T5 commit
`392e2482ce11aef9446722251b868d926f814a0a` is in its history.

## Implemented architecture

`application/decision_input_assembly.py` defines immutable application-layer
contracts for Odoo facts, supplemental values, source attribution, canonical input,
and provenance. `assemble_decision_input()` validates the full supported subset,
joins only by stable offer identity, constructs the existing Decision Core models,
and returns:

```text
AssembledDecisionInput
├── canonical
│   ├── PurchaseRequirement
│   ├── SupplierOffer[]
│   └── StrategicProfile
└── provenance
    └── FieldProvenance[]
```

Only `canonical` is passed unchanged to the existing
`evaluate_procurement_decision()` use case. The Decision Core, WSM, hard constraint,
and public `POST /api/v1/procurement/decisions/evaluate` contract were not changed.

`odoo_adapter/comparison_case_reader.py` performs a bounded read of one explicit
`purchase_group_id`, its complete purchase orders, order lines, and commercial
partners. It uses only the existing JSON-2 credential and does not filter away
unsupported records before application validation.

## Fixture mechanism and isolation

`docs/T6_FIXTURE_SETUP.md` is the specification-approved manual UI fallback. A
development-only administrator writer was rejected as disproportionate because this
repository has no validated JSON-2 write contract for the alternative wizard,
product/tax defaults, idempotent relationship creation, or safe teardown. Inventing
those calls would risk ambiguous or destructive fixture data.

The procedure requires the human administrator only to create the controlled
records. The integration identity remains read-only, does not receive **Manage
Purchase Alternatives**, and performs all automated validation. Runtime packages do
not import fixture tooling; no fixture code or production route exists. Live T6
tests require `RUN_T6_LIVE_CONTRACTS=true` and exact `Source Document` markers, so
they cannot silently run against arbitrary RFQs.

## Supported subset

- at least three RFQs in one explicit persisted `purchase_group_id`;
- one line per RFQ;
- one exact product variant, UoM, currency, company, and comparison quantity;
- actual line `price_unit` values;
- RFQ states `draft`, `sent`, or `to approve`;
- zero discount and no line taxes;
- stable order and commercial-partner identities;
- explicitly supplied hard MOQ and supplier-promised lead time with field name,
  source type, source reference, and timezone-aware observation time;
- an explicitly attributed strategic profile.

No UoM, currency, tax, discount, multi-line, or date conversion is performed.

## Fail-closed behavior

Stable assembly errors cover missing or unstable comparison identity, fewer than
three offers, duplicate Odoo identities, zero or multiple lines, unsupported state,
missing identities or non-finite Odoo numerics, missing/duplicate/unknown
supplemental joins, missing MOQ or lead time, unusable attribution, different
product/UoM/currency/company/quantity, order-line currency/company mismatch,
non-zero discount, taxes, and invalid values rejected by the existing domain model.
No malformed offer is dropped and no partial case is evaluated.

`product.supplierinfo.min_qty`, `product.supplierinfo.delay`, and
`purchase.order.line.date_planned` remain prohibited. The comparison reader does not
request them and the assembler has no fallback path for them.

## Changed files

- `.env.example` — explicit live-T6 opt-in.
- `application/decision_input_assembly.py` — typed contracts, assembler, errors,
  and provenance.
- `backend/app/config.py` — opt-in setting only; no route change.
- `odoo_adapter/comparison_case_reader.py` — bounded read-only JSON-2 fact reader.
- `tests/test_decision_input_assembly.py` — reference, provenance, join, and negative
  contracts.
- `tests/test_odoo_comparison_case_adapter.py` — adapter request/mapping contracts.
- `tests/test_architecture.py` — dependency and fixture-isolation checks.
- `tests/integration/test_live_odoo_contract.py` — two opt-in T6 live contracts.
- `README.md`, `docs/IMPLEMENTATION_LOG.md`,
  `docs/spikes/odoo-decision-input-mapping-spike.md`, `docs/T6_DESIGN.md`, and
  `docs/T6_FIXTURE_SETUP.md` — status, mapping, design, setup, and evidence.

## Verification evidence

Executed on Windows with project `.venv` Python 3.14.7; Python 3.11 remains the CI
baseline.

| Command/check | Result |
| --- | --- |
| Unchanged pre-branch fast baseline | 80 passed, 19 deselected |
| `ruff format .` and `ruff check .` | Passed |
| Focused T6 fast tests | 40 passed |
| `pytest -m "not integration and not e2e" -v` | 120 passed, 21 deselected |
| `python -m compileall application backend frontend decision_core odoo_adapter` | Passed |
| `python -m pip check` | Passed; no broken requirements |
| `podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet` | Passed |
| `pytest -m "integration and not e2e" -v` with local stack and tunnel | 19 passed, 2 skipped, 118 deselected |
| `git diff --check` | Passed; line-ending conversion warnings only |
| `.env` ignore check | Passed |
| Tracked credential-pattern review | No committed credential value found; workflow variable assignments were the only pattern matches |

The first integration attempt was unavailable because Podman, Odoo, and FastAPI
were stopped. After starting the existing Podman machine and Compose services,
establishing the documented localhost-only tunnel, and starting FastAPI, all 19
non-fixture live/served tests passed. The two T6 tests skipped because
`RUN_T6_LIVE_CONTRACTS` remained false and no controlled fixture was claimed.

GitHub Actions and browser E2E were not run. No browser E2E suite exists, and no
pull request has been created at this handoff.

## Acceptance criteria

| # | Criterion | Status |
| ---: | --- | --- |
| 1 | Controlled Odoo case with three grouped RFQs | **Not satisfied** — manual fixture pending |
| 2 | Dedicated user reads controlled case without writes | **Partial** — general order/line read-only contract passed; controlled case pending |
| 3 | Supported invariants validated | Satisfied in code and fast tests; live fixture pending |
| 4 | Every offer requires attributed MOQ and lead time | Satisfied |
| 5 | Missing or ambiguous supplemental input fails closed | Satisfied |
| 6 | Forbidden Odoo fallback fields never used | Satisfied |
| 7 | Exact predefined canonical case | Satisfied in fast tests; live fixture pending |
| 8 | Canonical input passes unchanged to existing use case | Satisfied |
| 9 | Deterministic ranking and explanations | Satisfied in fast tests; live fixture pending |
| 10 | Every canonical field traceable | Satisfied in fast tests; live fixture pending |
| 11 | Provenance excluded from Decision Core | Satisfied |
| 12 | Line create/write/unlink denied | Satisfied by live T5 contract |
| 13 | Company boundary enforced | Satisfied by live T5 contract; fixture pending |
| 14 | Existing T2/T3 tests unchanged and green | Satisfied |
| 15 | Runtime does not import fixture tooling | Satisfied |

Because criteria 1 and 2 are not fully satisfied and the live portions of 3, 7, 9,
10, and 13 remain unexecuted, T6 must be reported as incomplete rather than
production-ready.

## Remaining risks and next action

The UI labels and defaults in `docs/T6_FIXTURE_SETUP.md` must be followed against the
validated local Odoo 19 build. Default purchase taxes are the most likely fixture
pitfall and must be cleared. Supplemental terms prove source attribution, not
objective truth. The reader intentionally supports only a 20-offer and 40-line
safety bound and the single-product, no-tax, no-discount subset.

Next, the user should complete the administrator procedure, confirm it, set the
local opt-in, and rerun the focused live contract. Only a passing read-only result
can close T6 acceptance. Historical supplier-performance KPIs, actual delivery,
quality, and reliability evidence remain a later increment.
