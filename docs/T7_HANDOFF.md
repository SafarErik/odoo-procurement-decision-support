# T7 historical supplier-performance capability spike handoff

## Outcome

**PENDING CONTROLLED LIVE ACCEPTANCE**

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

`GO` is blocked by three current facts:

1. the integration identity cannot read `stock.move`;
2. it cannot read `stock.picking`; and
3. as an internal user, it has inherited create/write/unlink rights on
   `stock.move.line`, so it is not read-only for that model.

The five existing confirmed purchase orders provide no substitute for controlled
history: their eight lines all have zero received quantity, every order has
`effective_date = false`, and the only receipts are pending. No heuristic join or
administrator fallback was used.

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

The chain is proven at schema/source level but not through readable live records.
That distinction is why the outcome is pending rather than `GO`.

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

The inventory-history models are not yet acceptable:

| Model | Current effective access | Required before fixture acceptance |
| --- | --- | --- |
| `stock.picking` | no read and no mutation | company-scoped read only |
| `stock.move` | no read and no mutation | company-scoped read only |
| `stock.move.line` | read plus create/write/unlink | company-scoped read only, all mutations denied |

T7 made no security change. `docs/T7_FIXTURE_SETUP.md` stops before business-data
creation and requires a separate approved security decision. Adding a broad
Inventory role is explicitly prohibited.

## Fixture and executable evidence

The opt-in setting `RUN_T7_LIVE_CONTRACTS` defaults to false. The dormant contracts:

- require the desired read-only rights and exact field semantics; and
- locate only four exact fixture markers before checking supplier identity,
  purchase-line/move/picking relationships, direction, company, quantity, completion
  timestamps, backorders, returns, candidate value, and sample size.

The administrator-only fixture procedure is in `docs/T7_FIXTURE_SETUP.md`. It was
not executed during T7, and no claim is made that its postconditions exist.

## Acceptance criteria

| # | Criterion | Status and evidence |
| ---: | --- | --- |
| 1 | Starts from T6-complete main | **Satisfied** — HEAD started at `01b9ff1` |
| 2 | Architecture/security boundaries intact | **Satisfied** — no runtime KPI/API/UI/core/persistence/write path added |
| 3 | Models, fields, relationships, permissions empirically inspected | **Satisfied** — bounded live metadata, rights, value, and denial probes documented |
| 4 | Supplier identity stable and T6-compatible | **Satisfied** — commercial-partner identity retained; names rejected |
| 5 | Purchase-line-to-receipt relationship proven or rejected | **Pending live behaviour** — schema path proven; move/picking reads denied |
| 6 | Reference timestamp meaning documented | **Satisfied** — Expected Arrival operational schedule, not supplier promise |
| 7 | Actual event/timestamp semantics documented | **Satisfied at metadata/source level; pending live behaviour** |
| 8 | Partial, backorder, cancellation, return, multi-receipt addressed | **Satisfied as explicit policy; controlled behaviour pending** |
| 9 | Exactly one KPI candidate or all rejected | **Satisfied** — only `delivery_schedule_adherence` retained |
| 10 | Sample, window, denominator, exclusions, insufficiency defined | **Satisfied** |
| 11 | No unsupported business meaning assigned | **Satisfied** |
| 12 | Read-only, mutation denial, company boundary validated | **Blocked** — stock move-line mutations are currently allowed |
| 13 | No Decision Core/API/frontend/persistence/Odoo-write scope | **Satisfied** |
| 14 | Fast/static checks | **See final verification section below** |
| 15 | Live evidence complete or pending with exact setup | **Satisfied as pending** — exact manual procedure provided |
| 16 | Final decision and T8 consequences | **Satisfied** — pending; T8 must not implement the KPI yet |

Because criteria 5, 7, 8, and 12 lack controlled live acceptance, a `GO` would be
false. The correct final state is **PENDING CONTROLLED LIVE ACCEPTANCE**.

## T8 recommendation

Do not begin a production historical-performance vertical slice yet. The exact next
increment should be a narrowly scoped security-and-fixture acceptance step:

1. make a separate, reviewed decision for a company-scoped read-only inventory
   history identity or projection that can read `stock.move` and `stock.picking` and
   cannot mutate `stock.move.line`;
2. re-run the T7 read/mutation/company contract;
3. have a human administrator create the exact four-record fixture;
4. run the focused and full live integration selections; and
5. only if both contracts pass, close T7 as `GO` and scope T8 to a small
   ERP-neutral historical-KPI port plus a read-only Odoo implementation.

If an effective read-only boundary cannot be achieved without broad Inventory
privileges or a speculative relationship, close T7 as `NO-GO` and omit historical
performance from T8.

## Google Drive synchronization facts

No Google Drive document was modified. The Hungarian living documentation should
later record:

- T7 outcome: `PENDING CONTROLLED LIVE ACCEPTANCE`;
- candidate: `delivery_schedule_adherence`, not supplier on-time delivery;
- Expected Arrival is an operational schedule, not a supplier promise;
- proposed grain is completed PO line, with separate sample size and trailing
  365-day window;
- commercial-partner identity remains aligned with T6;
- `stock.move` and `stock.picking` reads are currently denied;
- internal-user `stock.move.line` mutations are currently allowed and block the
  read-only requirement;
- controlled fixture and security approval are required before T8; and
- AC-07 remains unsatisfied.

## Verification record

Executed on Windows with project `.venv` Python 3.14.7; Python 3.11 remains the CI
baseline.

| Command/check | Result |
| --- | --- |
| `ruff format --check .` | Passed; 61 files already formatted |
| `ruff check .` | Passed |
| `python -m compileall application backend frontend decision_core odoo_adapter` | Passed |
| `pytest -m "not integration and not e2e" -v` | 121 passed, 23 deselected |
| `python -m pip check` | No broken requirements |
| `podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet` | Passed with project-local `podman-compose` provider |
| `pytest -m "integration and not e2e" -v` | 21 passed, 2 T7 tests skipped, 121 deselected |
| `git diff --check` | Passed; line-ending conversion warnings only |

The full live selection revalidated purchase-order and purchase-line mutation
denial, company scoping, installed modules, T6 fixture reads, and the full T6 hybrid
chain. The two T7 contracts skipped because `RUN_T7_LIVE_CONTRACTS` remains false.
They were not enabled: the documented security boundary and controlled business
fixture do not exist yet. Separate bounded read-only discovery calls established the
T7 metadata, access matrices, exact HTTP 403 denials, existing-data shape, and
outside-company empty result recorded in the spike.

The runs emitted existing dependency deprecation warnings and a local
`.pytest_cache` permission warning; neither affected results. GitHub Actions was not
run because no pull request was opened.
