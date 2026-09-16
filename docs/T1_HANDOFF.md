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
| Fast test selection | 18 passed, 3 deselected | Unit/contract coverage passed without selecting integration or E2E tests. |
| Integration selection | 3 passed, 18 deselected | Live Odoo read, running FastAPI health, and Odoo HTTP checks passed. |
| Live FastAPI route | HTTP 200, 5 items | The application and API boundaries work with the local Odoo database. |
| Compose configuration | Passed | The current `.env` and Compose model are valid. |
| Reflex Python/component compilation | Passed | The page and responsive component props compile. |
| Reflex production export | Not completed locally | Windows NVM had no active Node version; CI provisions Node.js 22.22. |
| Browser RFQ and unavailable-state acceptance | Pending | Must be checked manually until an E2E suite exists. |

## Manual milestone acceptance

1. Start PostgreSQL and Odoo, FastAPI, and Reflex using
   `docs/LOCAL_DEVELOPMENT_AND_SSH.md`.
2. Open the Reflex URL and confirm the ledger contains Odoo demo RFQs with reference,
   vendor, date, status, and total.
3. Stop FastAPI, press **Refresh data**, and confirm the UI shows the unavailable
   state rather than stale or fabricated data.
4. Restart FastAPI and confirm **Refresh data** restores the ledger.

## Required follow-up outside the code

The current discovery key belongs to the local administrator. Create a dedicated
Odoo integration user with only the read access needed for the validated RFQ query,
generate a new key for that user, replace `ODOO_API_KEY` locally, and rerun the live
integration test. Revoke the administrator key after that migration succeeds.

Do not broaden access merely to make the adapter pass. If the dedicated user fails,
capture the exact Odoo access error and adjust the smallest relevant permission or
record rule.

## Remaining boundaries

- Purchase-line, product, receipt, and supplier-performance semantics are not yet
  validated.
- Named-volume markers do not prove persistence of an Odoo RFQ or purchase order.
- `quality` remains the only check intended for required branch protection; the
  container/API integration workflow remains optional.
- Google Drive thesis documents were not changed by this increment.
