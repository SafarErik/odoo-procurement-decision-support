# Odoo adapter

This directory owns the Odoo-specific integration boundary. The first implemented
adapter is a bounded, read-only JSON-2 query for recent open requests for quotation.
It calls `purchase.order/search_read`, validates the response, and maps these
locally verified Odoo fields into ERP-neutral application DTOs:

- `id` to `source_id`;
- `name` to `reference`;
- `partner_id` display value to `vendor_name`;
- `date_order` to a timezone-aware `order_date`;
- `state` to the neutral draft/sent/awaiting-approval status set;
- `amount_total` and `currency_id` display value to currency-aware `total`.

The adapter must remain read-only until a write use case is explicitly designed and
approved. It must never access Odoo's PostgreSQL database directly. Credentials are
loaded from the ignored root `.env` through backend configuration and must not be
logged, returned in errors, or committed.

The current field contract is evidence for the local Odoo 19 Community PoC database,
not a universal Odoo schema guarantee. Revalidate `/doc`, permissions, record rules,
and field behaviour for every materially different target environment.

## T4 decision-input gate

T4 did not extend this adapter. On 2026-09-17, the renewed key authenticated as the
existing dedicated non-admin user. Live probes verified read-only access to orders,
products, product templates, supplier information, partners, currencies, and UoMs.
However, `purchase.order.line` read is denied, candidate alternative-grouping fields
were absent, and `purchase_requisition` was not installed. Product, quantity, UoM,
quoted price, multi-line, lead-time, and MOQ transformations therefore remain
unresolved.

Do not map the RFQ summary to `SupplierOffer`, treat unrelated RFQs as one case, use
order total as unit price, use line quantity as MOQ, or default missing decision
data. The exact evidence, rejected mappings, and recovery sequence are in
`docs/spikes/odoo-decision-input-mapping-spike.md`.
