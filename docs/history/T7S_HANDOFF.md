# T7-S company-scoped read-only inventory-history projection handoff

## Outcome

**T7-S COMPLETE — T7 LIVE VALIDATION MAY RESUME**

T7-S is implemented as a separate prerequisite on branch
`codex/t7s-company-scoped-read-only-inventory-history-projection`, stacked on the
completed T7 spike commit. A human administrator installed the addon and configured
the dedicated portal caller and projection group. The focused live security
contract passed on 2026-09-20; the T7-S live gate was returned to `false` afterward.

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
| 3 | No broad Inventory/Purchase/internal role granted | **Satisfied** — dedicated portal caller; live rights matrix remained false |
| 4 | No generic stock-model ACL granted | **Satisfied** — live generic rights and direct reads were denied |
| 5 | On-demand non-writable projection | **Satisfied** — `AbstractModel`, no table or ACL |
| 6 | Odoo ORM/JSON-2 only; no direct PostgreSQL/raw SQL | **Satisfied** |
| 7 | Active authorized company enforced | **Satisfied** — live cross-company request returned 403 |
| 8 | Mandatory bounded range, line IDs, and result limit | **Satisfied** — invalid and unbounded calls returned 422 |
| 9 | Projection create/write/unlink denied | **Satisfied** — live rights matrix returned false |
| 10 | Direct stock reads remain denied | **Satisfied** — all three generic stock-model reads returned 403 |
| 11 | Elevated reads justified and constrained | **Satisfied** — five fixed bounded readers only |
| 12 | Only validated semantics exposed | **Satisfied** — Expected Arrival is not a promise |
| 13 | Unsupported states/relationships fail closed | **Satisfied** — fast policy tests plus observed live rejection of an unsupported line |
| 14 | No secrets or unrestricted payloads exposed | **Satisfied** — exact live envelope/schema and denied direct reads |
| 15 | T6 security and architecture preserved | **Satisfied** — implementation boundary and regression checks |
| 16 | Manual install/group/key instructions supplied | **Satisfied** |
| 17 | T7 semantic and controlled-live acceptance | **Satisfied** — four-scenario controlled contract passed |

## Verification record

| Check | Result |
| --- | --- |
| `ruff format --check .` | Passed; 70 files formatted |
| `ruff check .` | Passed |
| Python compilation including the addon | Passed |
| Fast selection | 141 passed, 23 deselected |
| Disposable pinned-image addon import | Passed against `odoo:19.0-20260908`; no database used |
| Podman Compose configuration | Passed with the read-only addon mount |
| Existing live integration selection | 21 passed, 2 gated tests skipped, 139 deselected |
| `python -m pip check` | No broken requirements |
| Focused T7-S live security contract (2026-09-20) | **1 passed**, 19 deselected |
| Focused T7-S plus T7 live selection (2026-09-20) | **2 passed**, 18 deselected |
| Full live integration selection (2026-09-20) | **23 passed**, 141 deselected |

The focused live run used the human-configured dedicated portal identity and proved
same-company bounded success, the false CRUD rights matrix, direct stock-model
denial, cross-company rejection, and rejection of arbitrary or unbounded input. The
first diagnostic call also confirmed that a non-stock-move-backed line fails closed
with HTTP 422. No receipt fixture mutation was performed. The live gate is disabled.
The remaining warning was the existing local pytest-cache permission warning.

## Completed resume sequence

The human-created fixture and both live selections passed. Both gates are now
`false`. T7 is `GO` for the controlled subset, but neither T7-S nor T7 implements a
production historical adapter or satisfies AC-07.

## Subsequent T8 reuse

T8 later implemented the bounded application vertical slice over this exact method
without changing the addon, group, ACLs, caller, request bounds, response schema, or
generic stock-model denials. The historical statement above remains the T7-S
handoff state; current implementation and AC-07 evidence are in `docs/T8_HANDOFF.md`.
