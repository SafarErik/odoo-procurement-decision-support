# T15 — controlled planning API, scenarios and immutable storage

Current capability/publication status is in [README](../README.md); the dated
proposal/implementation record below is historical. The 2026-10-06 update in
[T15 handoff](T15_HANDOFF.md) records the subsequently user-created local commit.

Status: **CONTROLLED SLICE IMPLEMENTED LOCALLY, 2026-10-05; REVIEW PENDING.**
The user authorized implementation after reviewing this proposal. No commit/push/
merge was made by this implementation task. See [current handoff](T15_HANDOFF.md).
The reviewed design below retains the controlled boundaries and acceptance goals;
its proposed API/storage now have local implementations. Hosted T15 CI is unverified.
Verified base: main `247914ac05663d7358d53036c08750d9390d1baa`, with T13/T14
merged and post-merge Quality/Container/API successful. See [T14 handoff](T14_HANDOFF.md).

## Smallest useful increment

Compose one controlled, explicitly synthetic, three-supplier case end to end:

```text
controlled facts + attributed business terms + explicit policy
  -> application assembly + separate provenance
  -> trusted saved T14 model reload/inference
  -> risk_inputs -> PlanningCommand -> unchanged T13 MILP
  -> atomic immutable planning-case snapshot
  -> explicit scenario delta on the stored base -> same MILP -> new child snapshot
  -> stored-only GET and exact retry
```

This closes a technical composition gap. It does not close AC-V2-01's observed Odoo
input requirement or AC-V2-13's complete system acceptance. The T14 synthetic model
rejects observed features; relabelling Odoo data as synthetic is prohibited.
Offline training remains T14. No API operation trains or silently regenerates a model.

## Reuse and necessary additions

| Existing component | T15 use / necessary addition |
| --- | --- |
| T6 assembly/provenance and T8 history contracts | Reuse field-attribution and bounded context semantics. Add a small typed V2 assembler; the V1 canonical input lacks capacity, availability and commercial validity, so do not coerce it into V2. Controlled receipts use the existing T14 history preparation/T8 KPI calculation. |
| `supplier_evaluation/contracts.py`, `history.py`, `artifacts.py`, `model.py` | Reuse `FeatureSnapshot`, `QuantityValidity`, trusted-local `load_model` and `TreeModel.infer`; no new ML framework or training service. Backend composition supplies one trusted local artifact directory; HTTP cannot supply paths, uploads or trust flags. |
| `supplier_evaluation/planning_bridge.py` | Reuse `risk_inputs` for exact supplier joins, company/product/unit, as-of/date, model/mapping and full quantity-range validation. Missing or stale assessments fail closed; no zero-risk/default fallback. |
| `application/procurement_planning.py`, `decision_core/planning/`, `optimization_adapter/pulp_cbc.py` | Reuse `PlanningCommand`, `ExternalRiskContext`, `create_procurement_plans` and the actual CBC adapter unchanged. Preserve objectives, epsilon semantics, proof statuses, exact arithmetic and deterministic tie-breaks. |
| T11/T12 PostgreSQL transaction, immutability and idempotency patterns | Reuse engine/configuration and proven locking/atomic-write approach. Add one V2 planning-case record with a JSONB snapshot, unique creation key/fingerprint and nullable parent ID; one explicit Alembic migration. V1 has `snapshot_version = 1` and WSM-specific serializers: leave its tables, records, routes and decoding intact. |
| FastAPI DTOs, composition and T12 trusted-caller guard | Add thin V2 routes/strict DTOs and reuse the existing configured PoC bearer guard. No new identity provider, queue, registry, cache, deployment or generic workflow engine. |

Keep concrete ML loading and solver construction at backend/infrastructure composition;
the application receives those dependencies. The Decision Core receives only T13
canonical planning data, never source metadata, ML libraries, HTTP or ORM objects.

## Controlled input and inference boundary

The initial create payload supplies one explicit company/product/unit/currency,
approved positive integer Q and approval-source reference, required date, explicit
UTC simulation `as_of`, and stable supplier/offer identities. For each supplier it
supplies price, integer capacity, availability, hard MOQ or explicit absence,
price/delivery quantity ranges and promised date, with source attribution. Policy
supplies max supplier count, concentration and epsilon values explicitly.

Supply bounded synthetic receipt evidence and its version/source references, then
derive the ordered T14 features in the application. Do not accept HTTP predictions,
arbitrary feature vectors, risk coefficients or future training labels. Validate
context, duplicate identities, evidence availability at cutoff, history window,
support, feature schema and artifact compatibility before solving. The controlled
simulation clock must satisfy the existing trained-through and 30-day validity
contracts; it is not a claim of current operational model freshness.

JSON prices, concentration and epsilon use finite decimal strings; quantities/counts
use strict integers, rejecting booleans/fractions. No implicit currency/unit conversion,
RFQ-quantity approval, supplierinfo-to-MOQ mapping or Expected Arrival-to-promise mapping.
Proposed HTTP envelope: 1–10 suppliers, 3–50 prior receipts per supplier (the existing
T14 bound), 1–3 epsilon values and at most 256 KiB of request JSON. These are limits
of this controlled API slice, not new T13 business constraints. Require assessments for the exact
supplier set and coverage of all allowed allocations, never narrow business bounds
to fit the score. Do not add a cost-only bypass to this ML composition slice.

## API boundary (proposed)

All operations use the existing fail-closed trusted-caller guard. The shared token
proves possession, not buyer identity; supplied approval/source references are
attribution, not authentication or T17 final plan approval.

| Operation | Contract |
| --- | --- |
| `POST /api/v2/procurement/planning-cases` | Strict controlled input above; canonical UUID `Idempotency-Key`. Assemble, load/infer, solve and atomically store one case. First durable result `201`; exact replay `200`. |
| `POST /api/v2/procurement/planning-cases/{case_id}/scenarios` | Canonical UUID key; explicit attributed delta over a stored base. Store a new child with parent ID, delta and complete derived snapshot; never mutate the base. Restrict this first slice to scenarios from a base case. |
| `GET /api/v2/procurement/planning-cases/{case_id}` | Read/validate the stored snapshot only, returning the same stored inputs, explanations, assessments and plans. No upstream read, artifact load, training, inference or solve. |

Normalize caller intent and check durable idempotency before any source/model/solver
work. Scenario fingerprints include parent ID and normalized delta; creation keys
are unique across both POST operations. Same key/different intent is `409`, even
across operations. Serialize concurrent same-key creation and atomically commit
the case plus its mapping; failures roll back both. An exact replay must succeed
even when the model or solver is subsequently unavailable or replaced.

Unknown/extra fields and invalid assembly/model validity are `422`; missing case
is `404`; missing/invalid bearer token follows the current guard; unavailable
persistence or configured artifact is a safe `503`, without raw infrastructure
details. Preserve T13 `invalid_input`, `optimal`, `infeasible`, `no_proven_optimum`
and `solver_error` meanings. Invalid input is rejected without a durable run;
valid completed runs may store the other statuses, including failure diagnostics.
Only proved stages contain plans: a retained proved minimum does not make failed
alternative work optimal. Stored failure retries return that same result; a new
computation requires a new key. HTTP success means durable storage, not approval
or solver optimality. No final-decision, PDF, frontend or Odoo-write endpoint.

## Scenarios and immutable evidence

Support exactly the five existing requirement cases: supplier outage, capacity
reduction, Q increase, price increase and combined disturbance. Modify explicit
values, revalidate with the same T13 rules, then call the same planner. Preserve
company/product/unit/currency, feature/model identity and simulation time. Reuse
stored assessments because these scenario fields are not T14 features; recheck
their time and complete quantity coverage. Beyond-range demand/capacity fails
closed. New history, model, context or cutoff requires a fresh base case.

The child records the delta and compares allocation, total cost, exposure and
status against the stored base; missing plans/metrics yield explicit unavailable
comparisons. A Q change's total-cost delta is not a like-for-like saving claim.

Store the complete canonical input and policy, receipt/source evidence and feature
snapshots, ordered feature values, actual paths/classes/leaf support/scores,
model/training/dataset/feature/label/mapping/artifact identities and manifest/hash,
quantity/time validity and risk context, solver/runtime/configuration, result
statuses/plans/explanations, parent/delta, creation time and request fingerprint.
Keep the locally generated trusted artifact in its existing ignored location;
the database stores identity/manifest, not executable joblib bytes. GET does not
depend on that artifact. Protect snapshot columns against UPDATE/DELETE using
the existing database immutability pattern. No speculative approval fields.

## Meaningful acceptance checks

1. **Real composition:** train/save outside the request, then create from three
   controlled suppliers using actual reload, inference, bridge and CBC. Reproduce
   the T14 EUR 102 / EUR 109 reference, exact allocations and genuine tree paths;
   trap `fit` to prove create never trains. Verify the stored versions/provenance.
2. **Trust boundaries:** reject missing hard terms, duplicate/supplier/context
   mismatches, stale/future/insufficient history, observed input, incompatible or
   tampered artifact, absent assessments and uncovered quantities. Assert no
   solve or durable case after those failures and no artifact path accepted by HTTP.
3. **Scenarios:** run all five deltas through actual unchanged CBC; include a
   proved infeasible case and a beyond-score-range rejection. Check independent
   small-instance results, comparison meanings and unchanged parent bytes/hash.
   Assert no inference/artifact reload during a commercial-only scenario.
4. **Storage/retry:** PostgreSQL integration verifies round-trip exact decimals,
   fractions, paths and statuses, trigger protection, atomic rollback, same-key
   concurrent creation/replay and conflicting reuse. Trap source reads, artifact
   load, fit, inference and solve during GET/exact retry; retrieve after removing
   runtime artifact availability. Read historical V1 fixtures unchanged.
5. **HTTP/failure contracts:** bearer guard and strict schemas, `201/200/404/409/422/503`,
   sanitized infrastructure errors, no false infeasible/optimal status and no
   unproven incumbent. New-key recomputation is explicit; no silent POST retry.
6. **Regression and evidence:** Python 3.11 fast checks with required actual ML/CBC,
   existing V1/API/snapshot tests, Ruff/compile/pip/whitespace and Compose checks.
   PostgreSQL tests require documented services. Record exact SHA/CI and distinguish
   local, hosted, skipped live and unrun browser checks; no blanket full-V2 PASS.

These target controlled parts of FR-V2-01/07/08/10 and AC-V2-08/10. AC-V2-01
remains OPEN until its three-supplier Odoo boundary is verified; AC-V2-09/11/12/13
remain for later increments. Requirement meanings and IDs do not change.

## Separate observed Odoo/model promotion gate

Future promotion requires audited, bounded company/product/unit Odoo evidence
that was actually available at each cutoff, valid source-derived future labels,
sufficient support and leakage-safe splits, a new observed-compatible model/schema/
mapping/validity version, reproducible Python 3.11 training/reload/inference, and
controlled live read-only acceptance including commercial and full quantity bounds.
A later Odoo read timestamp cannot establish historical as-of availability.
Synthetic metrics, past T7/T8 KPI acceptance and hosted service smoke do not meet
this gate. No bypass, automatic promotion or unvalidated Odoo field is planned.

The reviewed sequence was assembler/inference/planner composition, immutable
storage/scenarios, then thin API and service acceptance. The subsequent user request
authorized this controlled slice. Frontend, approval/PDF, Odoo writes, observed
promotion and full V2 remain separate.
