# Odoo capability spike — T0

**Purpose:** reduce integration uncertainty without implementing an adapter,
canonical mapping, decision logic, or production data access.

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
- The Odoo database manager page was reachable, but no Odoo database was created and
  no Purchase or Inventory application was installed. The only persistence probes
  were a synthetic PostgreSQL table marker and a synthetic Odoo-volume file marker.
- No JSON-2, XML-RPC, or JSON-RPC call was executed. No API key, user permission,
  model, field, method, record rule, or edition-specific licensing behaviour was
  inspected locally. Candidate concepts below remain unverified mapping inputs.

## Assumptions

- A fresh local database will be created through the Odoo database manager using the
  master password supplied in the ignored `.env` file.
- A dedicated non-administrator integration user can be restricted to read-only
  access to the validated source data. This is a design target, not verified Odoo
  permission evidence.
- JSON-2 with a dedicated API key will be preferred if it works in the selected PoC
  environment and gives the required least-privilege access.
- HTTP timeouts, bounded requests, retry policy for transient failures, and explicit
  error translation will be required in the future adapter.

## Unresolved questions

1. Which Odoo edition, apps/modules, pricing plan, and configuration form the
   selected PoC environment, and is JSON-2 usable there? The container startup and
   database-manager smoke test do not answer this.
2. Can a low-privilege local user create and use an API key for JSON-2 without
   broader administration access?
3. Which precise models, fields, methods, relationships, record rules, and
   multi-company constraints are visible from `/doc` and the external interface?
4. What pagination pattern, maximum page size, transaction duration, timeout,
   throttling, and error responses apply to the target endpoint and deployment?
5. Which date is the contractual supplier commitment, which is Odoo's calculated
   expected arrival, and which receipt timestamp is authoritative for performance?
6. How should partial receipts, returns, backorders, cancelled lines, services, and
   unit conversions affect later canonical data and KPI definitions?
7. Is `/web/database/selector` an acceptable local-only readiness probe, or should a
   future initialized environment expose a narrower application-level endpoint?

## Implications for the planned adapter

- Keep all HTTP transport, authentication, pagination, retry/timeout handling, and
  Odoo-specific mapping inside `odoo_adapter/`.
- Design the adapter after inspecting the target database's `/doc` page and running
  read-only API experiments with synthetic data. Do not map directly from this
  document's candidate concepts.
- Prefer a dedicated low-privilege API identity, keep its API key outside the
  repository, and document the exact permissions after validation.
- Expose only ERP-independent DTOs to the later application/Decision Core boundary.
- Treat reporting dashboards as validation aids, not the authority for the project's
  future performance calculations.
