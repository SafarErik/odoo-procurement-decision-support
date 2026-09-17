# Odoo capability spike — T0 baseline and first read-only integration

**Purpose:** reduce integration uncertainty, record the first validated read-only
adapter contract, and keep that evidence separate from future canonical mapping,
decision logic, and production data access.

**Assessment date:** 2026-09-16.

## Verified facts

### Odoo and PostgreSQL baseline

- Docker Hub publishes the official `odoo:19.0-20260908` image tag. This T0 Compose
  definition pins that dated 19.0 tag, rather than using `latest`. Docker Hub
  documents the image as requiring a running PostgreSQL server and recommends named
  volumes for `/var/lib/odoo` and PostgreSQL data. [Docker Hub Odoo official image](https://hub.docker.com/_/odoo)
- Odoo 19.0 documentation states that supported PostgreSQL versions are **13.0 or
  above**. `postgres:16.15-bookworm` was available in Docker Hub at assessment time,
  so PostgreSQL 16 was selected as a currently maintained supported version. [Odoo 19 source-install requirements](https://www.odoo.com/documentation/19.0/administration/on_premise/source.html)
  [PostgreSQL official-image tags](https://hub.docker.com/_/postgres/tags?name=16&page=1)
- The official 19.0 image entrypoint uses `HOST`, `PORT`, `USER`, and `PASSWORD`
  values to construct database connection arguments, waits for PostgreSQL, then runs
  Odoo. [Official Odoo 19.0 entrypoint](https://github.com/odoo/docker/blob/master/19.0/entrypoint.sh)

### Runtime-verified local facts

- Podman pulled and ran `postgres:16.15-bookworm` (image ID
  `5f71c21b69a7977b82247582e2e731ed76bdebaadb7dd7945ed76bcc9ed06632`)
  and `odoo:19.0-20260908` (image ID
  `400a621198ea355394df4a328b0f65043ffd1f4e79a5025ba16edf03cb26893d`).
- PostgreSQL reported version 16.15 in its logs, became healthy through
  `pg_isready`, and was not published to the Windows host.
- The pinned Odoo 19 image rejects the legacy `--admin-passwd` server option. Its
  default configuration still documents `admin_passwd`, so Compose now creates a
  mode-restricted runtime configuration in the named Odoo data volume and then
  invokes the official entrypoint. Odoo subsequently logged version 19.0-20260908,
  connected to `odoo@db:5432`, and started HTTP on port 8069.
- `GET /web/database/selector` returned HTTP 200 and HTML from the Windows host
  through a temporary localhost-only SSH tunnel into the Podman machine. The tunnel
  was necessary because this host's Podman Windows forwarding helper did not expose
  the Compose localhost binding even though Podman reported it correctly.
- Synthetic markers in PostgreSQL and `/var/lib/odoo` survived both a container
  restart and a normal Compose down/up cycle. No volume-removal command was used.

### Supported external interfaces and authentication

- Odoo documents JSON-2 as new in 19.0. Its model API endpoint is
  `POST /json/2/<model>/<method>` and requires an `Authorization: bearer <API key>`
  header and JSON content type. The available models, fields, and methods are
  database-specific and are intended to be consulted through that database's `/doc`
  page. [Odoo external JSON-2 API](https://www.odoo.com/documentation/master/developer/reference/external_api.html)
- Odoo documents XML-RPC and JSON-RPC endpoints as deprecated and scheduled for
  removal in a later release. They are not selected as the forward-looking adapter
  baseline, but their availability in the eventual environment still needs testing.
  [Odoo 19 external RPC API](https://www.odoo.com/documentation/19.0/developer/reference/external_rpc_api.html)
- Odoo documents API keys as credentials that substitute for a user's password and
  must be protected equivalently. This supports using a dedicated integration user
  with a separately managed API key rather than an administrator's interactive
  account. [Odoo API-key guidance](https://www.odoo.com/documentation/19.0/developer/reference/external_rpc_api.html)
- The external-API documentation states that hosted external API access is available
  only on Custom Odoo pricing plans, not One App Free or Standard. The local Docker
  Community environment's exact JSON-2 entitlement and behaviour still require
  runtime confirmation; do not extrapolate hosted-plan wording without testing.

### Locally validated JSON-2 RFQ contract

- A local Odoo 19 Community database named `procurement_poc` was created with the
  Purchase and Inventory applications installed and demo data enabled.
- An API key generated for the local administrator successfully authenticated a
  JSON-2 request. `res.users/context_get` returned the authenticated context for
  user ID 2. This proves the mechanism in this local database; it is not evidence
  of a least-privilege production identity.
- The database-specific `/doc` page exposed Purchase and Inventory model
  documentation. A read-only `purchase.order/search_read` request returned demo
  open RFQs.
- `purchase.order/fields_get` confirmed the exact fields used by the first adapter:
  `id`, `name`, `partner_id`, `date_order`, `state`, `amount_total`, and
  `currency_id`. The observed states were `draft`, `sent`, `to approve`,
  `purchase`, and `cancel`.
- The implemented query includes only `draft`, `sent`, and `to approve`, limits the
  result to at most 50 records, and orders by newest `date_order` and ID. It maps
  Odoo-specific values to an ERP-neutral RFQ summary before FastAPI or Reflex sees
  them.
- A live integration test and the FastAPI route both succeeded against this local
  database on 2026-09-16. The test deliberately performs reads only.
- A dedicated internal user, `Procurement Integration` (user ID 7), replaced the
  administrator as the durable application identity. It is limited to company ID 1
  and a custom `Procurement RFQ API Reader` group.
- Live access checks proved `purchase.order` read access and denied create, write,
  and unlink access. The identity is not a Settings administrator. These checks use
  Odoo's access introspection methods and perform no business-data write.

### Candidate business data concepts

These are **candidate source concepts only**, based on Odoo 19 functional
documentation. They are not accepted canonical model mappings or field contracts.

| Needed future input | Candidate Odoo business source | Evidence and validation required |
| --- | --- | --- |
| Products | Product records and their vendor-pricelist configuration | Odoo documents product purchase data, including vendor, price, and lead time. Validate exact model, identifiers, variants, units, companies, and access rights. |
| Suppliers | Vendor/contact records referenced by product vendor details and purchase documents | Validate the contact model, supplier designation, parent/child contacts, multi-company behaviour, and least-privilege reads. |
| RFQs and purchase orders | Purchase documents in the Purchase application | Odoo documents RFQs converting to POs. Validate document states, links, cancellation semantics, and available API methods. |
| Order lines and promised dates | Purchase-document line data and the documented expected-arrival concept | Odoo documents expected arrival and vendor lead time. Validate exact field(s), timezone, partial-delivery semantics, and whether a supplier promise exists independently of a calculated expected date. |
| Received quantities and receipt dates | Inventory receipt operations and generated inventory moves | Odoo documents receipt validation and inventory movement creation. Validate line linkage, returns, backorders, quantities, and authoritative actual-receipt timestamps. |
| Historical delivery performance | Raw purchase, order-line, and receipt history; Odoo's Purchase & Vendor analysis dashboard is corroborating evidence only | Odoo documents days-to-receive and on-time-delivery measures. Validate raw source data and calculation semantics before computing project KPIs. |

Functional supporting sources: [lead times](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/lead_times.html), [vendor pricelists](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/products/pricelist.html), [purchase analysis](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/advanced/analyze.html), and [Purchase & Vendor dashboard](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/advanced/purchase_dashboard.html).

## Observations limited to the local environment

- The closure audit used Podman client/server 6.0.2 with a WSL-based,
  Linux/amd64 `podman-machine-default`. The external Compose provider was
  `podman-compose` 1.6.0 from the project virtual environment.
- Podman was installed under the user's local application directory but was not on
  the initial shell `PATH`; the audit prepended that directory without relying on
  Podman Desktop operations.
- The machine's Windows forwarding helper failed to publish localhost ports. Direct
  in-container HTTP returned 200, and a localhost-only SSH tunnel provided host-side
  HTTP evidence without widening the Compose bind address.
- The Odoo database manager was used to create `procurement_poc`; Purchase and
  Inventory were installed and demo purchase records were available.
- JSON-2 authentication, `context_get`, `purchase.order/fields_get`, and a bounded
  `purchase.order/search_read` were executed successfully. XML-RPC and JSON-RPC were
  not exercised because JSON-2 is the selected Odoo 19 baseline.
- The administrator key was used only for discovery. The configured application key
  now authenticates as the dedicated user and the application no longer depends on
  administrator access. The old discovery key should be revoked.
- The only persistence probes remain synthetic PostgreSQL and Odoo-volume markers.
  Successful RFQ reads do not yet prove persistence of an Odoo business transaction.

## Assumptions

- The locally validated `purchase.order` field behaviour will remain stable for the
  pinned Odoo image and initialized database. It must still be rechecked after a
  material image, module, permission, or deployment change.
- Retry policy and production observability will be required beyond the current
  bounded request, timeout, validation, and explicit error translation.

## Unresolved questions

1. Which precise purchase-line, receipt, product, supplier, record-rule, and
   multi-company contracts are visible to that user?
2. What pagination pattern, maximum page size, transaction duration, timeout,
   throttling, and error responses apply to the target endpoint and deployment?
3. Which date is the contractual supplier commitment, which is Odoo's calculated
   expected arrival, and which receipt timestamp is authoritative for performance?
4. How should partial receipts, returns, backorders, cancelled lines, services, and
   unit conversions affect later canonical data and KPI definitions?
5. Is `/web/database/selector` an acceptable local-only readiness probe, or should a
   future initialized environment expose a narrower application-level endpoint?

## Implications for the planned adapter

- Keep all HTTP transport, authentication, pagination, retry/timeout handling, and
  Odoo-specific mapping inside `odoo_adapter/`.
- Extend the adapter only after inspecting the target database's `/doc` page and
  running focused read-only experiments. The RFQ summary is validated; candidate
  purchase-line, receipt, performance, and recommendation inputs are not.
- Preserve the validated dedicated low-privilege identity, keep its rotating API
  key outside the repository, and revalidate permissions after security changes.
- Expose only ERP-independent DTOs to the later application/Decision Core boundary.
- Treat reporting dashboards as validation aids, not the authority for the project's
  future performance calculations.

## T4 decision-input follow-up — 2026-09-17

The evidence-first decision-input spike attempted to revalidate the dedicated
identity and inspect narrowly selected fields on purchase orders, purchase lines,
products, supplier information, partners, currencies, and units. Odoo was reachable,
and the database-specific `/doc` route was present, but it required an interactive
web session. Every JSON-2 request made with the configured dedicated key returned
HTTP 401, including the previously successful `res.users/context_get` and bounded
`purchase.order/search_read` calls.

No administrator fallback, permission broadening, direct database access, or Odoo
write was used. The T1 facts above remain dated T1 evidence, not current T4
revalidation. Alternative grouping, shared requirement quantity, product and UoM
comparability, commercial supplier identity, unit price, currency consistency, lead
time, MOQ, state eligibility, and multi-line handling are unresolved. The T4 gate
therefore rejected an Odoo-to-canonical adapter. See
`docs/spikes/odoo-decision-input-mapping-spike.md` for the complete matrix and
smallest next validation step.
