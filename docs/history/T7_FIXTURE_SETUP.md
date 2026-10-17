# T7 controlled historical-receipt fixture setup

## Purpose and mandatory stop gate

This procedure creates the smallest local-only history needed to test the proposed
`delivery_schedule_adherence` KPI. Perform it only in the development
`procurement_poc` database, after a fresh database backup, as a human administrator.
Never use the `Procurement Integration` identity to create, confirm, receive, return,
edit, cancel, or delete business records.

The 2026-09-19 T7 discovery found:

- `stock.move` read denied;
- `stock.picking` read denied; and
- `stock.move.line` create, write, and unlink allowed through the standard internal
  `Role / User` ACL.

Odoo ACLs are additive, so T7-S does not change that user or stack broader ACLs on
it. The separately implemented T7-S prerequisite uses a dedicated non-internal
identity and a guarded, method-only projection. Do not grant **Inventory / User**,
**Inventory / Administrator**, **Purchase / User**, **Purchase / Administrator**, or
**Role / User** as a shortcut.

**Do not start the business-data steps until T7-S live acceptance passes.** Complete
`docs/T7S_MANUAL_SETUP.md`, set `RUN_T7S_LIVE_CONTRACTS=true` only long enough to
run:

```powershell
pytest tests/integration/test_live_odoo_contract.py -m integration -k t7s -v
```

Continue only if it passes, proving bounded same-company projection reads while
generic projection CRUD and all direct `stock.move`, `stock.picking`, and
`stock.move.line` reads remain denied. Set the gate back to `false` after the run.
If it fails, stop and preserve the evidence.

## Preflight duplicate check

1. Open **Purchase > Orders > Purchase Orders**. Remove the default filter if
   necessary.
2. Search **Source Document** separately for each exact marker:

   - `T7-HIST-001-ONTIME`
   - `T7-HIST-002-LATE`
   - `T7-HIST-003-BACKORDER`
   - `T7-HIST-004-RETURN`

3. If none exists, continue. If all four exist, do not recreate them; inspect every
   value and receipt relationship below. If only some exist, more than one record
   has a marker, or any record differs, stop. Do not silently repair, delete, or
   reuse an ambiguous fixture.

Record the administrator's local calendar date in the `Europe/Budapest` timezone as
`D`. Complete all receipt validation steps on `D`:

- **future Expected Arrival:** `D + 1 day`, at `23:00`;
- **past Expected Arrival:** `D - 1 day`, at `00:00`.

The future time leaves a margin for same-day completion. If the UI displays dates in
another timezone or does not allow the time component, stop and record the exact
display instead of approximating it.

## Create the shared supplier and product

1. Open **Contacts** and search the exact name `T7 Historical Supplier`.
2. If absent, select **New**, create it as a **Company**, enter that exact name, and
   save. Do not create or select a child contact. If more than one matching
   commercial entity exists, stop.
3. Open **Purchase > Products > Products** and search the exact product name
   `T7 Historical Product`.
4. If absent, select **New** and set:

   - **Product Name:** `T7 Historical Product`
   - **Can be Purchased:** enabled
   - **Product Type:** **Goods**
   - **Track Inventory:** enabled
   - **Unit of Measure:** **Units**
   - **Purchase Unit:** **Units**

   Save the product. If a matching product exists with different type, inventory
   tracking, or UoM, stop.

## Common purchase-order values

For every scenario below, create a new record through
**Purchase > Orders > Requests for Quotation > New** with:

- **Vendor:** `T7 Historical Supplier`
- **Company:** the integration identity's validated company (company ID 1)
- one product line only;
- **Product:** `T7 Historical Product`
- **Quantity:** `100`
- **Unit:** **Units**
- **Unit Price:** `10`
- **Discount:** `0`
- no taxes; remove any automatically inserted purchase tax;
- the exact **Source Document** marker for the scenario; and
- the exact line-level **Expected Arrival** described below.

Save, re-open, and verify those values before selecting **Confirm Order**. Do not
change the ordered quantity or Expected Arrival after confirmation.

## Scenario 1 — complete on schedule

1. Create the common order with Source Document `T7-HIST-001-ONTIME` and future
   Expected Arrival `D + 1 day 23:00`.
2. Select **Confirm Order**.
3. Select **Receive**. In this Odoo 19 form, **Receive** opens the generated receipt
   transfer; installations that expose the same action as a smart button may label
   it **Receipt**. Confirm the transfer is for the exact PO, product, supplier,
   company, and demand `100`.
4. Set the processed **Quantity** to `100` and select **Validate**.
5. Confirm the receipt state is **Done** and its completion occurs before the future
   Expected Arrival.

Expected postcondition: one done supplier-to-internal receipt move for quantity 100.

## Scenario 2 — complete after schedule

1. Create the common order with Source Document `T7-HIST-002-LATE` and past
   Expected Arrival `D - 1 day 00:00`.
2. Select **Confirm Order**, select **Receive** to open the receipt transfer, process
   quantity `100`, and select **Validate** on the transfer.
3. Confirm the receipt state is **Done**.

Expected postcondition: one done supplier-to-internal receipt move for quantity 100,
completed after Expected Arrival.

## Scenario 3 — partial receipt with a backorder

1. Create the common order with Source Document `T7-HIST-003-BACKORDER` and past
   Expected Arrival `D - 1 day 00:00`.
2. Select **Confirm Order** and select **Receive** to open the receipt transfer.
3. Set processed **Quantity** to `40` and select **Validate**.
4. In the partial-transfer dialog, select **Create Backorder**. Do not choose the
   option that cancels the remaining quantity.
5. Open the created backorder for the remaining `60`, set processed **Quantity** to
   `60`, and select **Validate**.
6. Confirm both receipts are **Done**, the second identifies the first through
   **Back Order of**, and total received quantity is `100`.

Expected postcondition: two done supplier-to-internal receipt moves in one explicit
backorder chain, quantities 40 and 60, both completed after Expected Arrival.

## Scenario 4 — supplier return exclusion

1. Create the common order with Source Document `T7-HIST-004-RETURN` and future
   Expected Arrival `D + 1 day 23:00`.
2. Select **Confirm Order**, select **Receive** to open the receipt transfer, process
   quantity `100`, and select **Validate** on the transfer.
3. From the done receipt select **Return**.
4. In the return dialog, set quantity `20`, keep the exact product and source
   receipt, and select the button that creates the return transfer.
5. Open the generated return transfer, process quantity `20`, and select
   **Validate**.
6. Confirm the return is **Done**, links back to the original receipt, and moves from
   the internal location to the supplier location.

Expected postcondition: one done inbound move plus one explicit done supplier-return
move. This purchase line must be excluded from the T7 candidate sample with
`supplier_return_observed`; it must not be silently treated as an ordinary receipt.

Do not create a replacement receipt. Replacement semantics remain intentionally
unsupported and fail-closed in T7.

## Read-only acceptance

1. Sign out of the administrator account. Do not generate or copy an administrator
   API key.
2. In the repository's ignored local `.env`, set:

   ```text
   RUN_T7S_LIVE_CONTRACTS=true
   RUN_T7_LIVE_CONTRACTS=true
   ```

3. Run with the existing integration key:

   ```powershell
   pytest tests/integration/test_live_odoo_contract.py -m integration -k t7 -v
   pytest -m "integration and not e2e" -v
   ```

4. The controlled contract must find exactly the four Source Document markers,
   resolve all four direct vendors to one commercial partner, prove one common
   product/UoM/company, read the exact purchase-line-to-move-to-picking chain, and
   validate on-time, late, backorder, and return behaviour.
5. The controlled expected KPI evidence is:

   - eligible completed lines: the first three scenarios;
   - adherent lines: `T7-HIST-001-ONTIME` only;
   - excluded with warning: `T7-HIST-004-RETURN`;
   - `delivery_schedule_adherence = 33.33%`;
   - `sample_size = 3`.

6. Immediately set both live gates back to `false` after the run. If either test
   fails, do not reinterpret or manually patch the records to force a pass. Preserve
   the exact failure for review.

Passing this fixture still validates only the controlled local subset. It does not
authorize a production adapter or satisfy AC-07.

## Rollback and cleanup

Completed stock transfers are historical accounting/inventory evidence and should
not be deleted casually. The preferred full rollback is to restore the fresh local
database backup made immediately before the fixture.

If the fixture is retained:

1. keep both `RUN_T7S_LIVE_CONTRACTS=false` and `RUN_T7_LIVE_CONTRACTS=false`
   during ordinary development;
2. do not delete or edit the four completed purchase orders or transfers;
3. archive `T7 Historical Supplier` and `T7 Historical Product` only after verifying
   that no non-fixture record uses them; and
4. reverse T7-S only through `docs/T7S_MANUAL_SETUP.md` rollback after confirming
   that no validation path depends on it.

Never use `podman compose down -v` or delete the named volumes as routine fixture
cleanup.
