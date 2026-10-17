# T6 provenance-aware hybrid decision-input assembly handoff

## Outcome

**T6 COMPLETE — CONTROLLED LIVE ACCEPTANCE PASSED**

T6 is complete for its explicitly bounded proof-of-concept scope. A human
administrator created the controlled three-RFQ fixture through the Odoo UI, and the
configured dedicated integration identity independently verified it through
read-only JSON-2 calls. Both focused T6 live contracts and the complete integration
selection passed on 2026-09-19.

This result does not establish a production Odoo-to-decision pipeline. The public
read-only RFQ ledger and public caller-supplied decision API remain deliberately
disconnected. T6 exposes only an internal, explicitly invoked hybrid assembly path
for the validated subset; there is no automatic RFQ evaluation or public
Odoo-to-canonical endpoint.

The branch starts from `main` commit `c2c4b18`; required T5 commit
`392e2482ce11aef9446722251b868d926f814a0a` is in its history.

## Implemented architecture

`application/decision_input_assembly.py` defines immutable application-layer
contracts for Odoo facts, supplemental values, source attribution, canonical input,
and provenance. `assemble_decision_input()` validates the supported subset, joins
only by stable offer identity, constructs the existing Decision Core models, and
returns:

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

## Controlled fixture and read-only evidence

The administrator followed `docs/T6_FIXTURE_SETUP.md` and manually created the
three RFQs with exact `Source Document` markers:

- `T6-COMP-001-A`
- `T6-COMP-001-B`
- `T6-COMP-001-C`

The live contracts, running as the dedicated integration identity, established that
exactly those three marked RFQs exist, share one persisted `purchase_group_id`, and
can be read with their lines and commercial-partner identities. They also validated
the single-product, one-line-per-RFQ, quantity, UoM, currency, company, state,
discount, tax, and price invariants. Existing live security contracts confirmed
that create, write, and unlink remain denied on decision-input models, the
alternatives feature group is not granted, and line reads remain company-scoped.

The fixture was created only through the human-admin UI procedure. No fixture
writer or teardown utility was introduced, and runtime packages do not import
fixture tooling. Live T6 tests require `RUN_T6_LIVE_CONTRACTS=true` and exact source
markers, preventing silent execution against arbitrary RFQs.

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

## Verification evidence

Executed on Windows with project `.venv` Python 3.14.7; Python 3.11 remains the CI
baseline.

| Command/check | Result |
| --- | --- |
| `pytest tests/integration/test_live_odoo_contract.py -m integration -k t6 -v` | 2 passed, 16 deselected |
| `ruff format --check .` | 58 files already formatted |
| `ruff check .` | Passed |
| `python -m compileall application backend frontend decision_core odoo_adapter` | Passed |
| `pytest -m "not integration and not e2e" -v` | 120 passed, 21 deselected |
| `python -m pip check` | No broken requirements |
| `podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet` | Passed |
| `pytest -m "integration and not e2e" -v` | 21 passed, 120 deselected |
| `git diff --check` | Passed; line-ending conversion warning only |

The focused full-chain test proves the canonical values, deterministic eligible
ranking A then B, exclusion of C with an explanation, and exact provenance-path
coverage for the requirement identifier, requested quantity, all three strategic
profile fields, and all five canonical fields for every actual live offer identity.
Repeated requested-quantity provenance is also checked once per live offer.

The test run emitted only existing dependency deprecation warnings and a local
`.pytest_cache` permission warning. They did not affect test results. Browser E2E
was not run because no browser E2E suite exists. GitHub Actions evidence is added to
the pull request after the branch is pushed.

## Acceptance criteria

| # | Criterion | Status and evidence |
| ---: | --- | --- |
| 1 | Controlled Odoo case with three grouped RFQs | **Satisfied** — exact A/B/C markers exist and one live group ID contains all three |
| 2 | Dedicated user reads controlled case without writes | **Satisfied** — orders, lines, and partner identities were read through the integration credential; no admin credential was used by tests |
| 3 | Supported invariants validated | **Satisfied** — both controlled-case and full-chain live contracts passed |
| 4 | Every offer requires attributed MOQ and lead time | **Satisfied** — assembler requires both values and source attribution per stable offer identity |
| 5 | Missing or ambiguous supplemental input fails closed | **Satisfied** — fast negative contracts passed |
| 6 | Forbidden Odoo fallback fields never used | **Satisfied** — reader/assembler contracts prohibit supplier-info MOQ/delay and planned-date fallback |
| 7 | Exact predefined canonical case | **Satisfied** — live quantities, prices, supplemented terms, and profile matched the reference case |
| 8 | Canonical input passes unchanged to existing use case | **Satisfied** — application contract and architecture tests passed |
| 9 | Deterministic ranking and explanations | **Satisfied** — live result ranked A then B and excluded C with an explanation |
| 10 | Every canonical field traceable | **Satisfied** — exact live provenance-path set is asserted using actual offer IDs |
| 11 | Provenance excluded from Decision Core | **Satisfied** — architecture and assembly tests passed |
| 12 | Line create/write/unlink denied | **Satisfied** — live read-only mutation contracts passed |
| 13 | Company boundary enforced | **Satisfied** — live company-scoped order/line contract passed for the same identity |
| 14 | Existing T2/T3 tests unchanged and green | **Satisfied** — complete 120-test fast selection passed |
| 15 | Runtime does not import fixture tooling | **Satisfied** — architecture isolation test passed; no fixture writer exists |

All 15 T6 acceptance criteria are satisfied for the controlled local proof-of-concept
scope.

## Production limitations

Supplemental provenance records who supplied a value, the named source, its
reference, and observation time; it does **not** prove the value is objectively true
or historically accurate. Historical supplier-performance KPIs, actual-delivery,
quality, and reliability evidence remain later work.

The reader intentionally supports only a 20-offer and 40-line safety bound and the
single-product, single-UoM, single-currency, no-tax, no-discount subset. The system
still has no automatic Odoo-to-evaluation orchestration, production Odoo-to-canonical
API, write workflow, decision persistence, decision UI, currency/UoM conversion, or
authoritative Odoo source for hard MOQ and supplier-promised lead time. Broad
Purchase or Inventory roles must not be assigned as a shortcut.
