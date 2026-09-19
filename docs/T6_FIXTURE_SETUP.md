# T6 controlled Odoo fixture setup

## Purpose and safety boundary

This is the approved manual fallback for creating the development-only T6 comparison
case. Perform it only in the local `procurement_poc` database, after a fresh backup,
as the human administrator who has **Manage Purchase Alternatives**. Do not use the
`Procurement Integration` user: that identity must remain read-only.

Before changing data, open **Purchase > Orders > Requests for Quotation**, remove the
default open-RFQ filter if necessary, and search the **Source Document** field for
each exact marker:

- `T6-COMP-001-A`
- `T6-COMP-001-B`
- `T6-COMP-001-C`

If none exists, continue. If all three exist, inspect them against every value below
and reuse them only when they are exactly compatible. If only some exist, more than
one record has a marker, or any value differs, stop. Do not repair, overwrite,
delete, or regroup the records silently.

## Create the controlled records

1. In **Purchase > Products > Products**, search for exact product name
   `T6 Comparison Product`. If absent, select **New**, set the name to that value,
   enable **Can be Purchased**, select product type **Goods**, use the company's
   standard **Units** UoM, and save. If it exists with different product type or UoM,
   stop.
2. In **Contacts**, search for `T6 Supplier A`, `T6 Supplier B`, and
   `T6 Supplier C`. Create any missing entry as a company contact with the exact
   name. Do not create child contacts for this fixture. If an exact name resolves to
   multiple commercial partners, stop.
3. Open **Purchase > Orders > Requests for Quotation** and select **New**. Choose
   `T6 Supplier A`, keep the validated company and common currency, and set
   **Source Document** to `T6-COMP-001-A`.
4. Add exactly one order line for `T6 Comparison Product`: quantity `100`, UoM
   **Units**, unit price `10`, discount `0`, and no taxes. If Odoo inserts a default
   purchase tax, remove it explicitly. Save the RFQ without confirming it.
5. On that saved RFQ, open the **Alternatives** tab and select **Create Alternative**.
   Choose `T6 Supplier B`, copy the product line, and create the alternative. On the
   new RFQ set **Source Document** to `T6-COMP-001-B`, retain exactly one line and
   change only the unit price to `12`. Confirm quantity `100`, Units, discount `0`,
   no taxes, the same company, and the same currency; save without confirming.
6. From either member of the alternatives group, select **Create Alternative** again.
   Choose `T6 Supplier C`, copy the line, set **Source Document** to
   `T6-COMP-001-C`, and change only the unit price to `9`. Confirm the same remaining
   values and save without confirming.
7. Return to each RFQ's **Alternatives** tab. Confirm all three RFQs are visible in
   the same alternatives set and each remains in **RFQ** or **RFQ Sent** state. Do
   not add another line, tax, discount, or alternative.

The supplemental reference case is deliberately outside Odoo:

| Source marker | Explicit hard MOQ | Supplier-promised lead time (days) |
| --- | ---: | ---: |
| `T6-COMP-001-A` | 50 | 10 |
| `T6-COMP-001-B` | 100 | 5 |
| `T6-COMP-001-C` | 150 | 8 |

These values model source-attributed statements for the controlled test. Creating
the table does not establish that they are objectively true supplier commitments.

## Read-only verification

After saving all three RFQs, set `RUN_T6_LIVE_CONTRACTS=true` in the ignored local
`.env` and run:

```powershell
pytest tests/integration/test_live_odoo_contract.py -m integration -v
```

The live tests locate only the three exact Source Document markers, require one
shared persisted `purchase_group_id`, then read the complete case with the dedicated
integration API key. They verify the supported-subset facts and the full hybrid
assembly/evaluation chain. They do not write to Odoo.

If the test reports missing or incompatible records, set the opt-in back to `false`
and correct the fixture through the administrator UI only after reviewing the exact
failure. Never broaden the integration user's permissions.

## Cleanup

Cleanup is optional. With `RUN_T6_LIVE_CONTRACTS=false`, use the administrator UI to
cancel the three RFQs and delete them only if the local evidence is no longer needed.
Deletion is destructive; confirm the exact three Source Document markers first.
Archive the three fixture contacts and product only if they are unused elsewhere.
Do not uninstall Purchase Agreements, remove the read-only line ACL, or delete
Compose volumes as routine fixture cleanup.
