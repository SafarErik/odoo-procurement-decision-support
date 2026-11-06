# Odoo adapter

This directory owns the Odoo-specific integration boundary. Every reader is a bounded,
read-only Odoo JSON-2 client that validates the response and maps it into ERP-neutral
application DTOs:

- `comparison_case_reader.py` lists the open quotation groups of one company and reads
  one quotation group (orders, lines, partners, currency) as comparison-case facts
  (`application/odoo_quotations.py`).
- `product_history_reader.py` reads one product's bounded purchase history through the
  `procurement.product.history.export.read_product_history` method of the
  `t7s_inventory_history_projection` addon (`application/purchase_history.py`).

The adapters must remain read-only until a write use case is explicitly designed and
approved. They must never access Odoo's PostgreSQL database directly. Credentials are
loaded from the ignored root `.env` through backend configuration and must not be
logged, returned in errors, or committed.

The field contract is evidence for the local Odoo 19 Community database, not a
universal Odoo schema guarantee. Revalidate `/doc`, permissions, record rules, and
field behaviour for every materially different target environment.

R1 (2026-11-05) removed the open-RFQ summary reader (`GET /api/v1/procurement/rfqs`)
and the T8 historical-performance reader; their design notes stay in `docs/history/`.
The addon's older `read_bounded_history` projection method is still deployed and
covered by `tests/test_odoo_inventory_projection_policy.py`, but no runtime code calls it.
