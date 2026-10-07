# V2 Odoo input/model compatibility: controlled fixture increment

## Current outcome — controlled hybrid implemented, 2026-10-07

The user delegated selection of the fastest sound path. The chosen increment uses
live Odoo quotation identities/prices/currency and explicit controlled business
terms, with separately generated synthetic ML history. It does not attach unrelated
T7 receipts or classify Odoo observations as synthetic. The renewed projection key
authenticates uid 8 and its security contract passes, but a bounded read found no
confirmed company-1 orders for suppliers 51/52/53.

`POST /api/v2/procurement/planning-cases/from-odoo` accepts an explicit group ID and
`controlled_input` using the existing strict planning schema. Context and price in
that input are expectations, not authoritative upstream facts: the server re-reads
and checks them. Business quantity is explicitly 200, not quotation quantity 100.
The same trusted bearer, request-size limit and immutable storage apply. A stable
normalized intent includes group ID and caller inputs; exact retry resolves the
stored case before Odoo/model/solver work. Different intent/key reuse is 409.

Preparation trains a new synthetic artifact offline in the selected company/
product/unit domain, with a new training/model ID and checksum. The saved dataset
records generation/split/label evidence. Model source checks and mapping remain
unchanged; inference receives genuinely generated synthetic history. Profiles A/B/C
are explicitly assigned lower/middle/higher simulated exposure, not measured
supplier performance. Live acquisition completion supplies the stored cutoff;
future caller cutoff and stale quotation expectations fail closed.

Verified reference: Q=200, capacities 120/100/160, hard MOQ 50/100/150,
max suppliers 2, concentration 80%, epsilon 20%; date and applicability are
attributed controlled assumptions. USD 1,850 minimum (50/0/150), USD 2,200
lower-exposure alternative (100/100/0); C outage USD 2,200 (100/100/0).
Field provenance distinguishes Odoo facts, controlled terms, synthetic receipts
and acquisition clock. Snapshot `input_kind=odoo_quotations_synthetic_history`
and comparison identity make the distinction explicit.

Local acceptance passes: 433 fast tests / 45 deselected, 22 PostgreSQL tests,
and actual live Odoo + saved inference/CBC + PostgreSQL/API. Stored GET/exact
base/child replay survive disabled Odoo/model access; fresh creation is 503.
The API was exercised with TestClient against real external services, not a new
separate Uvicorn/browser run. Current changes are uncommitted; new-SHA hosted CI
is pending. The controlled T15 boundary is locally ready for review/publication.
Observed receipt/model promotion, frontend, approval/PDF and full V2 remain open.
Drive is unchanged by this implementation task.

## Initial readiness, before key renewal — 2026-10-07

The user selected reuse of the existing controlled development fixture. The goal
is to assemble one source-attributed three-supplier V2 case from read-only Odoo
facts and explicit business terms, then establish whether a saved model can
legitimately evaluate its history before any MILP run or durable case is created.
This is a necessary dependency for the buyer-facing planning cockpit.

Read-only preflight verified comparison group 2: orders 16/17/18, suppliers
51/52/53, company 1, product 54, UoM 1, currency 1, draft RFQs with one untaxed,
undiscounted line each. Quotation quantity is 100 and prices are 10/12/9. These
are fixture observations, not an approved demand or general price applicability.
Four existing RFQ/identity/T6 live tests passed; 16 were outside the selection.

Two dependencies remain:

1. The dedicated history identity returns HTTP 401. Renew `ODOO_T7S_API_KEY`
   through [the existing manual procedure](T7S_MANUAL_SETUP.md#5-generate-the-dedicated-api-key).
   The RFQ key works and must stay unchanged. No ACL or business-data mutation was
   performed. User confirmation and read-only verification must precede dependent
   history acceptance.
2. Known T7 history is supplier 55/product 57, not the selected fixture. It cannot
   be attached to suppliers 51/52/53 or product 54. This is not a claim that no
   other compatible history exists. A bounded selection must identify matching
   receipt lines, source/cutoff availability and sufficient support. Missing data
   requires exact manual fixture instructions, not invented observations.

## Initial proposal after readiness — historical, superseded for the controlled slice

The proposal below considered Odoo-derived receipt history. The current outcome
above instead completes the controlled slice with live quotations and separate
synthetic history. Matching observed history/model promotion remains future work;
the history adapter is not called by the new planning route.

- Reuse `OdooComparisonCaseReader` and the bounded history port/adapter. Select
  one explicit group and exact company/product/unit/supplier/history identities;
  do not discover or heuristically group arbitrary RFQs.
- Keep a small V2 application assembler separate from the V1 WSM assembler. Join
  by stable identities; validate common context, one offer per supplier, supported
  lines and source timestamps. Retain Odoo provenance without relabelling it.
- Supply approved integer Q/reference, required date, supplier capacity/availability,
  hard MOQ or explicit absence, quantity-specific price/delivery bounds and promise,
  plus policy/epsilon through an attributed controlled fixture specification.
  Existing quotation quantity, Expected Arrival and master-data thresholds do not
  establish those meanings. Define one multi-supplier reference and one outage
  expectation before implementation acceptance.
- Prepare contextual features through the existing history/KPI conversion, then
  check model source/domain/schema/cutoff and complete quantity validity. A later
  read timestamp cannot prove historical as-of availability.
- Use the existing planner, scenario and immutable persistence/retrieval components
  only after compatibility passes. Keep trusted model selection in server-side
  configuration; no HTTP training, caller artifact paths or Odoo writes.

The API boundary is a selected Odoo case plus attributed supplemental terms and
policy. Odoo prices/identities/history are acquired behind adapters, never supplied
as caller-certified upstream facts. Preserve existing synthetic POST routes and
V1 snapshots. Exact retry must resolve durable intent before any upstream work;
GET and stored scenario/retry remain independent of Odoo/model availability.
Add a thin creation route only when the positive model contract is established;
an always-failing planning endpoint is not a useful deliverable.

## Observed-history model gate — still open

Current T14 metadata and inference explicitly accept `t14_synthetic` and its trained
domain only. The existing artifact is not compatible with Odoo-derived history.
Putting a controlled business fixture in Odoo does not bypass that gate. No source
rename, fabricated matching history, zero-risk fallback or copied model manifest.

Positive inference from Odoo-derived history needs an explicitly versioned
compatible dataset/model/mapping/validity contract, with documented cutoffs,
labels, support and leakage-safe
evaluation. A controlled demonstration can remain non-predictive; it must retain
its true data provenance and cannot imply observed-model promotion. Whether this
can reuse available fixture evidence is a readiness result, not an assumption.

Acceptance: exact live input/provenance; rejection of missing terms, incompatible
history/model and context mismatch before solve/store; a legitimate compatible
saved-model positive reference; unchanged MILP/outage result; atomic PostgreSQL
round-trip and stored-only retry/GET with Odoo/model unavailable; V1 regressions,
Python 3.11 fast checks and exact published-SHA CI. No frontend, approval/PDF or new
infrastructure. The original controlled T15 slice can close separately; full
Odoo-to-model acceptance cannot close from this preflight alone.
