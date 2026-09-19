# T7-S company-scoped read-only inventory-history projection handoff

## Outcome

**PENDING MANUAL ODOO SETUP**

T7-S is implemented as a separate prerequisite on branch
`codex/t7s-company-scoped-read-only-inventory-history-projection`, stacked on the
completed T7 spike commit. The code and fast security policy tests are complete,
but the addon has not been installed and no dedicated projection caller or API key
has been created. Live security claims are therefore not yet accepted.

## Delivered boundary

- method-only Odoo addon with no table, menu, view, generic ACL, or stored copy;
- fixed JSON-2 method `read_bounded_history`;
- separate non-internal projection identity and API-key configuration;
- active-company, exact-line, time-window, and result-count bounds;
- fixed sanitized receipt-evidence schema;
- fail-closed state, direction, product/UoM, picking, backorder, and return checks;
- opt-in live security contract; and
- original T7 controlled test migrated away from direct stock-model reads.

No Decision Core, `SupplierOffer`, `StrategicProfile`, scoring, public API, Reflex,
application persistence, or historical KPI implementation was added. The existing
T6 identity and its contracts remain unchanged.

## Acceptance criteria

| # | Criterion | Status |
| ---: | --- | --- |
| 1 | Separate T7-S scope and branch | **Satisfied** |
| 2 | Odoo-native alternatives compared | **Satisfied** — design records six mechanisms |
| 3 | No broad Inventory/Purchase/internal role granted | **Satisfied in code; pending manual confirmation** |
| 4 | No generic stock-model ACL granted | **Satisfied in addon; pending live denial proof** |
| 5 | On-demand non-writable projection | **Satisfied** — `AbstractModel`, no table or ACL |
| 6 | Odoo ORM/JSON-2 only; no direct PostgreSQL/raw SQL | **Satisfied** |
| 7 | Active authorized company enforced | **Satisfied in code/tests; pending live proof** |
| 8 | Mandatory bounded range, line IDs, and result limit | **Satisfied in code/tests; pending live proof** |
| 9 | Projection create/write/unlink denied | **Satisfied structurally; pending live rights matrix** |
| 10 | Direct stock reads remain denied | **Pending live proof with dedicated identity** |
| 11 | Elevated reads justified and constrained | **Satisfied** — five fixed bounded readers only |
| 12 | Only validated semantics exposed | **Satisfied** — Expected Arrival is not a promise |
| 13 | Unsupported states/relationships fail closed | **Satisfied by fast policy tests; pending fixture evidence** |
| 14 | No secrets or unrestricted payloads exposed | **Satisfied by exact schema tests; pending live proof** |
| 15 | T6 security and architecture preserved | **Satisfied by code boundary; full regression pending** |
| 16 | Manual install/group/key instructions supplied | **Satisfied** |
| 17 | T7 semantic and controlled-live acceptance | **Not started** — requires T7-S live pass and fixture |

## Verification record

| Check | Result |
| --- | --- |
| `ruff format --check .` | Passed; 70 files formatted |
| `ruff check .` | Passed |
| Python compilation including the addon | Passed |
| Fast selection | 139 passed, 23 deselected |
| Disposable pinned-image addon import | Passed against `odoo:19.0-20260908`; no database used |
| Podman Compose configuration | Passed with the read-only addon mount |
| Existing live integration selection | 21 passed, 2 gated tests skipped, 139 deselected |
| `python -m pip check` | No broken requirements |

The T7-S and T7 gates skipped by design. No addon installation, group assignment,
portal-user creation, API-key creation, or receipt fixture mutation was performed.
Existing warnings were dependency deprecations, the local pytest-cache permission
warning, and Git line-ending conversion notices; none changed a result.

## Resume sequence

1. Complete `docs/T7S_MANUAL_SETUP.md` as a human administrator.
2. Run the focused T7-S live contract and return `RUN_T7S_LIVE_CONTRACTS` to false.
3. Review the live evidence; if any direct stock right is true, close T7-S as
   `NO-GO` rather than broadening access.
4. If T7-S passes, create the four T7 fixtures manually.
5. Enable both live gates, run the focused T7 test and full integration selection,
   and then decide whether T7 can become `GO`.

Passing T7-S only permits original T7 live validation to resume. It does not approve
a production historical adapter or satisfy AC-07.
