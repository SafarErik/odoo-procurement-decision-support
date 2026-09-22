# T12 controlled orchestration API design

## Boundary and sequence

`application/decision_case_orchestration.py` coordinates one explicit create command.
The FastAPI route maps strict HTTP input and stable errors, while adapters retain all
Odoo transport and SQLAlchemy mapping. Decision Core remains ERP, provenance, HTTP,
and persistence independent.

1. Validate a canonical UUID create key and hash normalized caller intent with
   SHA-256. The hash sorts supplemental offer and history supplier identities,
   normalizes Decimal text and UTC timestamps, and excludes the bearer secret, live
   Odoo facts, and generated IDs/timestamps.
2. Open one T11 UnitOfWork and acquire a PostgreSQL transaction advisory lock for
   the create key. Read the durable `decision_case_creations` mapping. An exact match
   returns the stored case immediately; a different fingerprint fails with `409`.
3. Read exactly the selected `purchase_group_id` through the existing bounded,
   read-only `OdooComparisonCaseReader` structural port. Validate its returned group
   identity. The T6 assembler checks supported RFQ semantics and exact supplemental
   offer identity joins. There are no supplierinfo MOQ/delay or planned-date fallbacks.
4. If selected, require exactly one bounded history selection for each comparison
   supplier. Each selection supplies exact `odoo:purchase.order.line:<positive id>`
   identities. Derive `[window_end - 365 days, window_end)` and use the shared company
   identity. Reuse T8 `acquire_historical_performance` and `attach_historical_performance`;
   T7-S remains the only history transport. No arbitrary history discovery exists.
5. Resolve one of six fixed policies. Legacy IDs use the accepted two-criterion
   evaluator. Historical IDs use the T10 history evaluator and its exact fallback
   profile. No HTTP weight vector, imputation, or scoring change is allowed.
6. Evaluate once, validate T11 snapshot consistency, insert the immutable case and
   create-key mapping, then commit both in one transaction. A failed transaction
   leaves neither. The advisory lock serializes concurrent same-key requests; the
   loser sees the committed winner's mapping and case.

The application ports are `ComparisonCaseReader`, the existing
`HistoricalPerformancePort`, T11 case repository/UnitOfWork, and the narrow creation
mapping repository. The latter has `lock/get/add` operations. The SQL lock is
transaction scoped; hash collisions only serialize unrelated keys, while the table's
full UUID primary key and full fingerprint determine correctness.

## HTTP contract

All `/api/v1/procurement/decision-cases` routes require
`Authorization: Bearer <T12_TRUSTED_CALLER_TOKEN>`. The configured value is a
`SecretStr`, compared in constant time. A missing or wrong token returns `401`; an
unconfigured gate returns `503`. This is shared PoC service-secret possession, not
individual authentication. `actor_reference` is unverified caller-supplied audit
metadata. Secrets are excluded from fingerprints and responses.

`POST /api/v1/procurement/decision-cases` requires a canonical UUID
`Idempotency-Key` header. Its body contains `purchase_group_id`,
`supplemental_terms[]` (stable `offer_id`; each hard MOQ and promised lead time has
decimal-string `value`, `source_type`, `source_reference`, and explicit UTC
`observed_at`), `scoring_policy_id`, and optional `history_selection` with UTC
`window_end` and supplier/exact-line-ID lists. Initial success is `201`; exact
completed replay is `200` with the same stored case; conflicting key reuse is `409`.
The bearer token is not a semantic part of the create request.

`GET /api/v1/procurement/decision-cases/{id}` reads T11 snapshots only. It never
calls Odoo, T7-S, assembly, KPI calculation, or scoring. The typed response includes
canonical input, selected policy, evaluation with history activation/fallback fields,
provenance, recommendation, lifecycle state, and optional human decision. Decimal
values are strings and timestamps are UTC. The snapshot serializer is shared with
T11 persistence, so the HTTP representation cannot silently choose different
numeric semantics.

`POST /api/v1/procurement/decision-cases/{id}/final-decision` takes a separate
canonical UUID `Idempotency-Key`, outcome, selected offer, rationale, explicit UTC
decision time, and caller-supplied actor reference. It invokes T11's
`record_human_decision`; accept, override, no-award, eligible-selection checks,
one-time finalization, and exact retry semantics remain T11 behavior. It cannot
modify machine snapshots or write to Odoo.

## Errors, persistence, and exclusions

Stable code-bearing errors map to `401` trusted-caller failure, `404` missing case,
`409` creation/finalization conflict, `422` malformed input or domain rule, `502`
invalid Odoo response, and `503` unavailable Odoo/database or unconfigured gate.
Upstream and database exception text is replaced with safe messages. Normal FastAPI
schema validation also returns `422`.

Alembic revision `20260922_02` adds `decision_case_creations` after T11's
`20260922_01`. It has a primary-key create UUID, SHA-256 fingerprint, and unique
foreign key to the immutable decision case. The existing T11 database trigger still
rejects snapshot mutation and all changes after finalization. Startup never runs
`create_all` or migrations.

Rejected approaches: key state in memory, reuse of the T11 finalization key,
heuristic Odoo case/history discovery, direct SQL in application code, HTTP supplied
scoring weights, Odoo writeback, automatic purchasing, and a generic workflow engine.
The open transaction spans the bounded upstream reads to serialize same-key creates;
this is acceptable for the controlled PoC, but throughput and production identity
management remain outside scope.
