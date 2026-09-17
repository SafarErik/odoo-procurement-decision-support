# T4 handoff — Odoo decision-input mapping spike

## Status

**SPIKE COMPLETE — CRITICAL MAPPING NOT AVAILABLE — ADAPTER DEFERRED**

T4 performed no Odoo business-data write and added no Odoo-to-Decision-Core adapter.
The configured dedicated integration key returned HTTP 401 for every JSON-2 request,
including the previously proven identity and RFQ calls. New schema, relationship,
permission, and business-value evidence could therefore not be obtained safely.

## Prerequisites and baseline

- Fetched `origin`; the T4 branch, local `main`, and `origin/main` all resolved to
  T3 merge commit `f123446dac7994d9ea4727225c5fe4a9d0a39cd5`.
- `docs/T3_HANDOFF.md` and
  `POST /api/v1/procurement/decisions/evaluate` were present.
- The focused Decision Core, application, and decision-API baseline passed:
  62 tests.
- The branch remained `codex/t4-odoo-decision-input-spike`; it was not merged.

## Live evidence

- Podman client/server 6.0.2 started the existing PostgreSQL and Odoo containers.
- PostgreSQL reported healthy and Odoo's web route returned HTTP 200 through the
  documented localhost-only SSH tunnel.
- `/doc?db=procurement_poc` existed but required an interactive authenticated web
  session; a JSON-2 bearer key did not establish that session.
- The ignored `.env` contained a non-empty key; the key itself was not displayed.
- `res.users/context_get`, `purchase.order/search_read`, all attempted
  `fields_get` and `check_access_rights` calls, and both existing live Odoo contract
  tests returned HTTP 401.
- No administrator fallback, permission change, database query, or write occurred.

The rejection cause is unresolved: expiry, revocation, and credential mismatch are
possible explanations, but none was proven.

## Mapping decisions

Accepted:

- T1's dated evidence that `purchase.order.id` can identify a source RFQ record.
- The existing seven-field T1 RFQ summary mapping remains valid for its separate
  ledger contract; it was not reused as `SupplierOffer`.

Rejected:

- grouping unrelated RFQs by names, origin, dates, product coincidence, or inferred
  supplier relationships;
- vendor display names as stable supplier identity;
- order totals as unit prices;
- line quantities as MOQ;
- silent UoM or currency conversion and silent MOQ defaults;
- conflating expected, promised, configured, ordered, and actual dates;
- aggregating multi-line RFQs into artificial offers.

Unresolved:

- explicit alternative-RFQ grouping;
- shared requirement identity and quantity;
- line, product/variant, UoM, and multi-line semantics;
- stable commercial-supplier identity;
- unit price, discount, tax, and currency consistency;
- lead-time definition and calculation;
- applicable MOQ source and deterministic selection;
- comparable RFQ states;
- access and record-rule/company behavior for every new candidate model.

## Data and adapter gate

The seven demo RFQs observed during T1 are not evidence of a complete comparison
case. T4 could not inspect current records and therefore could not establish three
explicit alternatives for one requirement with the same product, UoM, quantity
context, currency, usable lead time, and usable MOQ.

The conditional adapter gate failed. No production adapter, application wrapper,
fixture-only mapping, public API endpoint, frontend change, or Decision Core change
was added. Adding any of those would falsely convert unvalidated hypotheses into a
contract.

## Verification classification

| Check | Result |
| --- | --- |
| Fetch and T3 ancestry | Passed; `HEAD == origin/main == f123446`. |
| Focused T2/T3 tests | Passed; 62 tests. |
| Ruff formatting and lint | Passed; 48 Python files already formatted and lint clean. |
| Python compilation | Passed for `application`, `backend`, `frontend`, `decision_core`, and `odoo_adapter`. |
| Full fast test selection | Passed; 80 tests, 5 integration tests deselected. |
| Dependency consistency | Passed. |
| Whitespace check | Passed. |
| Compose configuration | Passed with the ignored local `.env`. |
| Odoo/PostgreSQL runtime | Started; PostgreSQL healthy, Odoo HTTP 200 through localhost tunnel. |
| Database-specific `/doc` route | Present; blocked by interactive login. |
| Dedicated-user JSON-2 authentication | Failed; HTTP 401. |
| Existing live Odoo tests | Executed; 2 failed at HTTP 401. |
| New mapping evidence | Not available because authentication failed. |
| Fixture-only mapping evidence | None; schema and semantics were not validated. |
| Odoo writes | None. |
| Google Drive changes | None. |

GitHub Actions had not run at the time of this local handoff; CI must be reported
separately after the branch is pushed and the pull request is opened.

## Security observations

The credential remained in the ignored `.env` and was not exposed. T4 did not use
administrator credentials, query PostgreSQL, install a module, broaden ACLs or
record rules, change company access, or create/modify/confirm/cancel/delete any Odoo
record. The temporary network workaround stayed on localhost.

## Exact next step

Issue a new API key for the unchanged `Procurement Integration` user, replace only
the local ignored `ODOO_API_KEY`, and rerun identity plus the existing bounded RFQ
query. If those succeed, inspect `/doc` in an authenticated browser session and run
the exact read-only T4 probes listed in
`docs/spikes/odoo-decision-input-mapping-spike.md`. Do not broaden permissions until
a specific model denial is observed and reviewed. Do not begin T5.
