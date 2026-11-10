# odoo_adapter

The only code that talks to Odoo. Each reader is a bounded, read-only Odoo 19 JSON-2
client that validates the response and maps it into the ERP-neutral facts of
`application/`. It never writes to Odoo and never touches Odoo's database.

## Entry points

- [comparison_case_reader.py](comparison_case_reader.py) — lists the company's open
  quotation groups and reads one group (orders, lines, partners, currency) as the facts
  in `application/odoo_quotations.py`.
- [product_history_reader.py](product_history_reader.py) — reads one product's bounded
  purchase history through `procurement.product.history.export.read_product_history`
  into `application/purchase_history.py`.
- [json2_client.py](json2_client.py) — shared JSON-2 client, error mapping and value parsing.

The history export lives in the Odoo addon
[`t7s_inventory_history_projection`](../infra/odoo/addons/t7s_inventory_history_projection/).
Its name is historical (increment T7-S, inventory-history projection); it is not renamed
because Odoo identifies an installed module by its technical name, so a rename would mean
uninstalling and reinstalling it, with its access groups, in every Odoo database.
Its older `read_bounded_history` method is still deployed but unused by the runtime.
Addon setup: [docs/RUNBOOK.md §5.1](../docs/RUNBOOK.md#51-dedicated-test-database-manual-administrator).

Credentials come from the ignored `.env` through `backend/app/config.py` and are never
logged, returned in errors or committed. The field contract was verified on the local
Odoo 19 Community database; revalidate it for any other Odoo environment.

## Imports

- May import: `application` (errors and fact types), `supplier_evaluation.contracts`, httpx.
- Must not import: `decision_core`, `tools`; must call only Odoo read methods.
  Enforced by [tests/test_architecture.py](../tests/test_architecture.py).

## Tests

`tests/test_quotation_groups.py`, `tests/test_odoo_comparison_case_adapter.py`,
`tests/test_odoo_purchase_history.py` (mocked transport); opt-in live checks in
`tests/integration/test_live_odoo_contract.py` and `test_live_purchase_history.py`.
See [docs/TESTING.md](../docs/TESTING.md).
