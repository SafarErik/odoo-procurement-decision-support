# T8 historical supplier-performance vertical-slice handoff

## Outcome

**GO — CONTROLLED VERTICAL SLICE IMPLEMENTED AND LIVE-VERIFIED**

Branch `codex/t8-historical-kpi-vertical-slice` starts from current `main` commit
`af8297c09a4043e2fa7f0a80e9b6ea795cc7ab85`, the merge of PR #8. The pre-change
fast baseline was `141 passed, 23 deselected`. T8 satisfies AC-07 for the accepted
bounded subset: `delivery_schedule_adherence` and its separate historical sample
size are contextual fields in `CanonicalDecisionInput`.

T8 does not add a scoring criterion. Decision Core models and algorithms, WSM
normalization, strategic-profile weights, MOQ eligibility, contribution traces,
ranking, and explanation semantics are unchanged. A regression compares the full
`DecisionResult` with and without attached history.

## Architecture

```text
HistoricalPerformanceQuery
        |
        v
HistoricalPerformancePort (ERP-neutral Protocol)
        |
        +--> OdooHistoricalPerformanceReader
                 |
                 +--> procurement.inventory.history.projection
                        .read_bounded_history
        |
        v
InventoryHistorySnapshot (ERP-neutral observations)
        |
        v
calculate_delivery_schedule_adherence
        |
        v
SourcedSupplierHistoricalPerformance
        |
        v
attach_historical_performance / assemble_decision_input
        |
        +--> CanonicalDecisionInput.historical_performance
        +--> separate ProvenanceManifest
        |
        v
existing evaluate_procurement_decision --> unchanged Decision Core
```

The Odoo addon remains projection and access-control infrastructure. The adapter
owns JSON-2 transport and Odoo-field mapping. The application owns KPI semantics,
withholding, warnings, stable supplier joins, and provenance assembly. Decision Core
continues to own only the existing constraints, normalization, WSM score, ranking,
and explanations.

## Domain and port contracts

`application/historical_performance.py` introduces:

- `HistoricalPerformancePort.read_inventory_history(query)` — async neutral port;
- `HistoricalPerformanceQuery` — stable supplier/company identities, exact stable
  purchase-line identities, an exact 365-day half-open window, and a bounded result
  limit;
- `InventoryHistoryObservation` — relationship-backed purchase document/line,
  supplier, product, UoM, operational schedule, receipt event/transfer, completion,
  quantity, state, direction, backorder, and return facts without Odoo field names;
- `InventoryHistorySnapshot` — observations plus observation time and source
  attribution;
- `SupplierHistoricalPerformance` — metric identifier, nullable value, separate
  sample size, window bounds, observation time, stable supplier ID, availability,
  and ordered structured warnings; and
- `SourcedSupplierHistoricalPerformance` — the canonical value plus application
  source metadata used to build provenance.

The port is a Python `Protocol`; a test fake implements it without importing Odoo.
Application and Decision Core packages do not import the concrete Odoo reader.

`CanonicalDecisionInput` now has
`historical_performance: tuple[SupplierHistoricalPerformance, ...]`. Existing T6
callers that do not request historical attachment receive an empty tuple. Supplying
history requires exactly one mapping for every distinct supplier in the canonical
offer set. Missing, unknown, and duplicate supplier identities fail closed. Multiple
offers from one supplier share that supplier's one historical result.

## KPI contract

The only metric is `delivery_schedule_adherence`:

```text
adherent eligible completed line count
--------------------------------------- * 100
eligible completed line count
```

- Grain: one eligible completed purchase-order line.
- Weighting: line count, never raw quantity.
- Reference: line-level operational Expected Arrival; it is not a
  supplier-confirmed promise.
- Completion: the earliest completed eligible inbound event at which cumulative
  quantity reaches the current ordered quantity.
- Adherent: completion is at or before Expected Arrival.
- Window: exactly `[as_of - 365 days, as_of)` by completion timestamp.
- Representation: `Decimal` percentage, rounded half up to two decimal places.
- Sample size: eligible completed-line count, stored separately from the value.

Partial receipts remain ineligible until completed. Multiple receipts and explicit
backorders accumulate by timestamp and still count as one line. A completion after
Expected Arrival remains late. Return-affected lines are excluded with
`supplier_return_observed`. Cancelled obligations, incomplete receipts, and missing
Expected Arrival are excluded with explicit warnings. Over-receipt remains eligible,
uses the first threshold-reaching timestamp, and emits `over_receipt`. Warning order
is deterministic by code and stable line identity.

When sample size is `0`, `1`, or `2`, `value` is `None`. The actual sample size is
retained, availability is explicitly withheld, and `insufficient_history` explains
the minimum of `3`. Zero eligible lines additionally emit `no_eligible_lines`. The
system never substitutes zero, a neutral score, or a fabricated percentage, and an
offer is not excluded because its historical value is unavailable.

## Provenance

Historical provenance remains only in `ProvenanceManifest`. Four entries are emitted
per supplier for `value`, `sample_size`, `observation_window_start`, and
`observation_window_end`. Each carries `field_name`, `source_type`, bounded
`source_reference`, and `observed_at`.

The Odoo reference identifies
`procurement.inventory.history.projection.read_bounded_history`, company, half-open
window, and exact line identities. It excludes base URL, database, credentials, and
other sensitive configuration. It records where the evidence came from; it does not
claim that the observed value is objectively true.

## Odoo and security boundary

`OdooHistoricalPerformanceReader` uses only the accepted projection method. It
validates the complete fixed envelope and record schema, schema version, echoed
company/window, result count, requested line IDs, commercial-supplier identity,
event window, state, direction, quantities, and stable identifiers before mapping.
Incomplete or inconsistent responses fail closed.

No T7-S addon, ACL, group, or projection-policy code changed. The separate
non-internal caller, explicit projection group, active-company check, maximum 50
line IDs, maximum 200 results, fixed schema, and method-only read path remain intact.
There is no direct `stock.move`, `stock.move.line`, or `stock.picking` read in the
application adapter; no create, write, unlink, fixture-creation, administrator, raw
SQL, or direct-database path was added. The normal T6 integration identity remains
read-only and separate from `ODOO_T7S_API_KEY`.

## Files added and changed

Added:

- `application/historical_performance.py`;
- `odoo_adapter/historical_performance_reader.py`;
- `tests/test_historical_performance.py`;
- `tests/test_odoo_historical_performance_adapter.py`; and
- `docs/T8_HANDOFF.md`.

Changed:

- `application/decision_input_assembly.py`;
- `tests/test_decision_input_assembly.py`;
- `tests/test_architecture.py`;
- `tests/integration/test_live_odoo_contract.py`;
- `README.md`;
- `odoo_adapter/README.md`;
- `docs/T7_HANDOFF.md`;
- `docs/T7S_HANDOFF.md`;
- `docs/T7S_DESIGN_SECURITY.md`; and
- `docs/IMPLEMENTATION_LOG.md`.

## Verification record

Executed on Windows with the project `.venv` using Python 3.14.7; Python 3.11
remains the compatibility and CI baseline.

| Command/check | Result |
| --- | --- |
| Pre-change `pytest -m "not integration and not e2e" -v` | 141 passed, 23 deselected |
| Focused T8 unit/adapter/assembler/architecture tests | 72 passed |
| Final `ruff format --check .` | Passed |
| Final `ruff check .` | Passed |
| `python -m compileall application backend frontend decision_core odoo_adapter infra/odoo/addons/t7s_inventory_history_projection` | Passed |
| Final `pytest -m "not integration and not e2e" -v` | 180 passed, 23 deselected |
| `python -m pip check` | No broken requirements |
| Focused live T7-S/T8 selection | 2 passed, 18 deselected |
| Full `pytest -m "integration and not e2e" -v` with controlled gates | 23 passed, 180 deselected |
| `podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet` | Passed |
| `reflex export --frontend-only --no-zip` | Passed |
| `git diff --check` | Passed; only Git line-ending conversion warnings |

The focused and full controlled runs temporarily set the T7-S and T7 gates in the
process environment; tracked defaults and the ignored `.env` were not changed.
Dependency deprecation warnings were unchanged from the baseline.

## Controlled live result

The production T8 adapter read the four exact fixture lines through the bounded
projection. The live test proved:

- one shared company, commercial supplier, product, and UoM;
- one line completed at or before Expected Arrival;
- one line completed late;
- one two-picking backorder completed late;
- one explicit return-affected line excluded with
  `supplier_return_observed`;
- `delivery_schedule_adherence = 33.33` and `sample_size = 3`;
- the result and sample size attached to canonical contextual history;
- four separate bounded-projection provenance entries;
- cross-company calls were rejected;
- projection and generic stock-model CRUD rights remained false;
- generic stock-model reads returned HTTP 403; and
- the complete decision result was unchanged after history attachment.

## Acceptance criteria

| # | Criterion | Status | Evidence |
| ---: | --- | --- | --- |
| 1 | Expected T7/T7-S main base | PASS | Branch merge-base is `af8297c...` |
| 2 | ERP-neutral port and typed representation | PASS | `HistoricalPerformancePort` and typed neutral models |
| 3 | Exact accepted KPI semantics | PASS | Policy unit matrix plus controlled live fixture |
| 4 | Value and sample size separate | PASS | Distinct typed fields and assertions |
| 5 | Samples below 3 withheld | PASS | Samples 0/1/2 return `None` plus warning |
| 6 | History in canonical decision input | PASS | `CanonicalDecisionInput.historical_performance` |
| 7 | Provenance separate | PASS | `ProvenanceManifest`; no provenance in Decision Core/history model |
| 8 | Stable supplier joins fail closed | PASS | Missing/unknown/duplicate tests |
| 9 | Accepted Odoo projection only | PASS | URL assertion and architecture scan |
| 10 | Company/request/schema controls | PASS | Adapter negatives, policy tests, and live rejection |
| 11 | Generic stock access and mutations denied | PASS | Static checks and live rights/HTTP denials |
| 12 | Controlled `33.33`, sample `3` | PASS | Production adapter/calculator live test |
| 13 | Ranking/constraints/contributions unchanged | PASS | Full `DecisionResult` regression and live equality |
| 14 | Unit, architecture, integration, live tests pass | PASS | Verification table |
| 15 | Documentation reflects T7 merge and T8 | PASS | README, logs, handoffs, adapter boundary |
| 16 | No skipped/mocked live claim | PASS | Two selected live tests and full 23-test live run passed |

## Known limitations and next increment

The slice is internal and explicitly invoked. It does not expose a public API or UI,
discover arbitrary supplier history, persist KPI values, schedule refreshes, or make
an automatic purchase decision. Exact historical purchase-line IDs remain an input
to the bounded query. The controlled fixture does not validate unrestricted
production data, every quantity-change/replacement history, currency conversion, or
cross-UoM aggregation.

Adding historical performance to WSM is deliberately deferred. A future increment
must define normalization, strategic-profile weights, missing/insufficient-history
behaviour, sensitivity analysis, regression evidence, and an ADR or approved
amendment to the existing decision-model ADR before any score or ranking changes.
