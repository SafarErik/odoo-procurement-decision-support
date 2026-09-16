# T1 handoff — read-only Odoo RFQ vertical slice

## Delivered flow

```text
Odoo purchase.order
  -> read-only JSON-2 adapter
  -> ERP-neutral application RFQ contract
  -> GET /api/v1/procurement/rfqs
  -> responsive Reflex procurement ledger
```

The flow lists recent open RFQs only. It does not score vendors, recommend a
supplier, update Odoo, or establish a final procurement domain model.

## Local configuration

The ignored root `.env` must contain these integration settings in addition to the
Compose passwords:

```dotenv
ODOO_BASE_URL=http://127.0.0.1:8069
ODOO_DATABASE=procurement_poc
ODOO_API_KEY=
ODOO_REQUEST_TIMEOUT_SECONDS=5
```

Never copy the real key into `.env.example`, documentation, test data, logs, or an
issue. The tracked example intentionally uses `ODOO_API_KEY=` with no value.

## Verification matrix

| Check | Result on 2026-09-16 | Meaning |
| --- | --- | --- |
| Ruff lint and Python compilation | Passed | Python source is syntactically valid and meets the configured lint rules. |
| Dedicated identity | Passed | User ID 7, `Procurement Integration`, is non-admin, single-company, and can read but not create, write, or delete `purchase.order`. |
| Fast test selection | 18 passed, 4 deselected | Unit/contract coverage passed without selecting integration or E2E tests. |
| Integration selection | 4 passed, 18 deselected | Least-privilege access, live RFQ read, running FastAPI health, and Odoo HTTP checks passed. |
| Live FastAPI route | HTTP 200, 7 items | The application and API boundaries work with the dedicated Odoo identity. |
| Compose configuration | Passed | The current `.env` and Compose model are valid. |
| Reflex Python/component compilation | Passed | The page and responsive component props compile. |
| Reflex production export | Passed | Production frontend build completed locally with Node.js 24.20.0. |
| Browser RFQ success state | Passed manually | Seven RFQs displayed reference, vendor, date, status, total, currency, and connected state; refresh worked. |
| Browser backend failure and recovery | Passed manually | The UI cleared stale rows, displayed the unavailable state, and recovered after FastAPI restarted. |
| Browser upstream failure | Passed manually | An invalid temporary key produced the stable 502 contract and unavailable UI without exposing upstream details. |

## Manual milestone acceptance

1. Start PostgreSQL and Odoo, FastAPI, and Reflex using
   `docs/LOCAL_DEVELOPMENT_AND_SSH.md`.
2. Open the Reflex URL and confirm the ledger contains Odoo demo RFQs with reference,
   vendor, date, status, and total.
3. Stop FastAPI, press **Refresh data**, and confirm the UI shows the unavailable
   state rather than stale or fabricated data.
4. Restart FastAPI and confirm **Refresh data** restores the ledger.

## Dedicated identity outcome

The durable local credential now belongs to the internal `Procurement Integration`
user rather than the administrator. The user is limited to company ID 1 and a custom
`Procurement RFQ API Reader` group. Live JSON-2 checks proved that it can read
`purchase.order` but cannot create, write, or unlink those records, and it is not a
Settings administrator. The application no longer requires the administrator key.

The earlier administrator discovery key should now be revoked. Continue rotating
the dedicated key before expiry; validate a replacement before revoking the previous
working key.

## Remaining boundaries

- This increment still does not implement WSM, normalization, ranking, hard
  constraints, supplier recommendations, historical KPI logic, production
  persistence, Odoo writes, or a final canonical procurement domain model.
- Purchase-line, product, receipt, and supplier-performance semantics are not yet
  validated.
- Named-volume markers do not prove persistence of an Odoo RFQ or purchase order.
- `quality` remains the only check intended for required branch protection; the
  container/API integration workflow remains optional.
- Google Drive thesis documents were not changed by this increment.
