# T7 historical supplier-performance capability spike handoff

## Outcome

**GO — CONTROLLED LIVE SUBSET ACCEPTED**

The separately scoped T7-S prerequisite established a guarded projection and a
dedicated non-internal caller without adding KPI runtime code. Its security contract
and the four-scenario controlled T7 contract passed on 2026-09-20; see
`docs/T7S_HANDOFF.md`.

T7 identified exactly one semantically defensible candidate:
`delivery_schedule_adherence`, a line-count-weighted measure of whether a completed
purchase-order-line receipt obligation reached the internal warehouse by Odoo's
line-level **Expected Arrival**. Its value and sample size remain separate. The name
deliberately avoids claiming a supplier-confirmed promise.

The branch starts exactly at required T6 merge
`01b9ff16d77934c2164d75ae6f4d938d98eedee3`. No production historical-performance
adapter or calculator was implemented. The Decision Core, `SupplierOffer`,
`StrategicProfile`, public API, frontend, persistence, T6 input contract, and T6
provenance separation are unchanged. AC-07 is not claimed.

The original T7 discovery was blocked by three facts:

1. the integration identity cannot read `stock.move`;
2. it cannot read `stock.picking`; and
3. as an internal user, it has inherited create/write/unlink rights on
   `stock.move.line`, so it is not read-only for that model.

T7-S resolved this without changing the original internal integration identity:
the portal caller retains no generic stock-model rights and can invoke only the
bounded projection. The controlled fixture now provides four exact one-line orders,
including on-time, late, backorder, and supplier-return histories. No heuristic join
or administrator data-read fallback was used.

## Verified schema and candidate chain

Live Odoo 19 Community metadata and matching official source establish this
candidate relationship:

```text
purchase.order.partner_id
    -> res.partner.commercial_partner_id        supplier grouping

purchase.order
    -> purchase.order.line.order_id
    -> purchase.order.line.move_ids
    <-> stock.move.purchase_line_id
    -> stock.move.picking_id
    -> stock.picking
```

The source line supplies `date_planned` (**Expected Arrival**). A candidate actual
event requires a `stock.move` with `state = done`, positive actual `quantity`,
supplier-to-internal locations, the exact purchase-line relationship, matching
product/UoM/company, no return relationship, and a done picking. For completed
moves, runtime metadata defines `stock.move.date` as the actual move-processing
date. `stock.picking.date_done` is corroboration only because it can also be set for
a cancellation.

The chain is now proven through controlled live records as well as schema and source.

## Candidate KPI

| Property | T7 recommendation |
| --- | --- |
| Name | `delivery_schedule_adherence` |
| Meaning | Share of eligible completed PO-line receipt obligations fully received by Odoo Expected Arrival |
| Grain | One completed stock-move-backed purchase-order line |
| Supplier | T6-compatible commercial-partner ID |
| Numerator | Eligible lines completed at or before `date_planned` |
| Denominator | Eligible completed lines in the historical window |
| Window | Half-open trailing 365 days by completion timestamp |
| Value | Percentage, Decimal, rounded half up to two decimals only for display |
| Sample size | Eligible completed-line count, separate from the percentage |
| Insufficient data | Withhold value below sample size 3 and return `insufficient_history` |

The controlled fixture's expected result is `33.33%` with sample size `3`: one
on-time line, one late line, one late line completed across a backorder, and one
separate return-affected line excluded with a warning.

## Rejected interpretations

- `product.supplierinfo.delay` is configured planning data, not historical
  performance.
- `purchase.order.line.date_planned` is Expected Arrival, not a supplier-confirmed
  promise or T6 quotation lead time.
- `purchase.order.effective_date` records the first completed receipt and is wrong
  for full completion across partial receipts.
- `qty_received` and `receipt_status` lack the required actual-event timestamp and
  direction evidence.
- Odoo's computed `on_time_rate` is unavailable to this identity, has no separately
  exposed sample size, aggregates quantities under direct partner identity, and does
  not satisfy T7's fail-closed edge-case policy.
- `stock.move.line.date` changes for multiple operational events and is not selected
  as the authoritative actual timestamp.
- Names, origin text, product coincidence, and timestamp proximity are never joins.

## Security result

Existing purchase-order and purchase-order-line create/write/unlink denial remains
valid, and the identity remains limited to company ID 1 without broad Purchase,
Inventory, alternatives, or Settings roles. An outside-company
`stock.move.line` query returned no rows.

The original internal integration identity remains intentionally unsuitable for
inventory history:

| Model | Current effective access | Required before fixture acceptance |
| --- | --- | --- |
| `stock.picking` | no read and no mutation | company-scoped read only |
| `stock.move` | no read and no mutation | company-scoped read only |
| `stock.move.line` | read plus create/write/unlink | company-scoped read only, all mutations denied |

T7-S selected a separate non-internal caller and method-only projection, so the
direct-model target in the table remains historical design evidence rather than the
implemented setup. Live checks prove the T7-S caller remains denied direct access to
all three stock models and has false generic create/write/unlink rights.

## Fixture and executable evidence

The opt-in setting `RUN_T7_LIVE_CONTRACTS` defaults to false. The contracts:

- require the desired read-only rights and exact field semantics; and
- locate only four exact fixture markers before checking supplier identity,
  purchase-line/move/picking relationships, direction, company, quantity, completion
  timestamps, backorders, returns, candidate value, and sample size.

The human administrator completed the fixture in `docs/T7_FIXTURE_SETUP.md`. Live
validation found exactly the four markers, one shared commercial partner,
product/UoM/company consistency, one on-time completion, one late completion, one
late two-picking backorder, and an explicit supplier return. The observed candidate
result is `33.33%` with sample size `3`; the return-affected line is excluded.

## Acceptance criteria

| # | Criterion | Status and evidence |
| ---: | --- | --- |
| 1 | Starts from T6-complete main | **Satisfied** — HEAD started at `01b9ff1` |
| 2 | Architecture/security boundaries intact | **Satisfied** — no runtime KPI/API/UI/core/persistence/write path added |
| 3 | Models, fields, relationships, permissions empirically inspected | **Satisfied** — bounded live metadata, rights, value, and denial probes documented |
| 4 | Supplier identity stable and T6-compatible | **Satisfied** — commercial-partner identity retained; names rejected |
| 5 | Purchase-line-to-receipt relationship proven or rejected | **Satisfied** — controlled live PO-line/move/picking paths passed |
| 6 | Reference timestamp meaning documented | **Satisfied** — Expected Arrival operational schedule, not supplier promise |
| 7 | Actual event/timestamp semantics documented | **Satisfied** — done move timestamp matched done picking and controlled comparisons |
| 8 | Partial, backorder, cancellation, return, multi-receipt addressed | **Satisfied for controlled subset** — backorder and supplier return passed; unsupported cases remain fail-closed |
| 9 | Exactly one KPI candidate or all rejected | **Satisfied** — only `delivery_schedule_adherence` retained |
| 10 | Sample, window, denominator, exclusions, insufficiency defined | **Satisfied** |
| 11 | No unsupported business meaning assigned | **Satisfied** |
| 12 | Read-only, mutation denial, company boundary validated | **Satisfied** — separate T7-S caller passed rights, direct-read, and cross-company checks |
| 13 | No Decision Core/API/frontend/persistence/Odoo-write scope | **Satisfied** |
| 14 | Fast/static checks | **See final verification section below** |
| 15 | Live evidence complete or pending with exact setup | **Satisfied** — focused and full live selections passed |
| 16 | Final decision and T8 consequences | **Satisfied** — controlled-subset `GO`; T8 may implement only the accepted boundary |

All mandatory controlled-live criteria now pass. The final T7 state is
**GO — CONTROLLED LIVE SUBSET ACCEPTED**. This is not approval for unrestricted
production history or a claim that AC-07 is already implemented.

## T8 recommendation

T8 may now be scoped to a small ERP-neutral historical-KPI port plus a read-only Odoo
implementation over the accepted T7-S projection. It must preserve the exact
reference event, actual event, completed-line grain, commercial-partner identity,
sample size, exclusions, insufficient-history result, company boundary, and
fail-closed edge policies documented here. It must not add a Decision Core criterion
or reinterpret Expected Arrival as a supplier promise.

## Google Drive synchronization facts

No Google Drive document was modified. The Hungarian living documentation should
later record:

- T7 outcome: `GO — CONTROLLED LIVE SUBSET ACCEPTED`;
- candidate: `delivery_schedule_adherence`, not supplier on-time delivery;
- Expected Arrival is an operational schedule, not a supplier promise;
- proposed grain is completed PO line, with separate sample size and trailing
  365-day window;
- commercial-partner identity remains aligned with T6;
- the separate T7-S identity remains denied generic stock-model reads and mutations;
- the four-scenario controlled fixture produced `33.33%` with sample size `3`;
- T8 may implement only the accepted bounded projection and edge-case policy; and
- AC-07 remains unsatisfied.

## Verification record

Executed on Windows with project `.venv` Python 3.14.7; Python 3.11 remains the CI
baseline.

| Command/check | Result |
| --- | --- |
| `ruff format --check .` | Passed; 70 files already formatted |
| `ruff check .` | Passed |
| `python -m compileall application backend frontend decision_core odoo_adapter` | Passed |
| `pytest -m "not integration and not e2e" -v` | 141 passed, 23 deselected |
| `python -m pip check` | No broken requirements |
| `podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet` | Passed with project-local `podman-compose` provider |
| Focused T7/T7-S live selection | 2 passed, 18 deselected |
| `pytest -m "integration and not e2e" -v` | 23 passed, 141 deselected |
| `git diff --check` | Passed; line-ending conversion warnings only |

The full live selection revalidated purchase-order and purchase-line mutation
denial, company scoping, installed modules, T6 fixture reads, the full T6 hybrid
chain, T7-S security, and the controlled T7 semantics. Both live gates were returned
to `false` immediately afterward.

The runs emitted existing dependency deprecation warnings and a local
`.pytest_cache` permission warning; neither affected results. GitHub Actions was not
run because no pull request was opened.
