# T11 Handoff — Decision-Case Persistence and Human Final Decision

## Decision

**GO — implementation, local persistence verification, hosted CI, and review pass;
PR #12 is merge-ready.**

Branch: `codex/t11-decision-case-persistence-human-decision`

Base `main`: `6f691ec31e64ad2763d477475b581c8c41bf2c3a`

Implementation commit: `5e058cd0bbff711c8441c2f62e804ca21415a0e8`

PR: [#12](https://github.com/SafarErik/odoo-procurement-decision-support/pull/12)

Hosted Quality, Container and API integration, and CodeRabbit checks pass. PR #12
is open, non-draft, mergeable, and has no unresolved review threads. The final
cleanup commit cannot self-reference its own SHA; that SHA is reported in the
delivery response.

## Preconditions and baseline

`git fetch --prune origin` completed before branching. Local `main` and
`origin/main` both resolved to `6f691ec`, the merge commit for PR #11. The merged
tree contains `docs/T10_HANDOFF.md`, the final T10 GO/merge-ready decision, the
opt-in historical scoring implementation, and hosted Quality, container/API, and
CodeRabbit pass evidence on T10 implementation head `bada66e`.

The pre-change fast baseline on `6f691ec` was:

```text
pytest -m "not integration and not e2e" -v
222 passed, 23 deselected
```

The interpreter was Python 3.14.7. Python 3.11 remains the repository and CI
compatibility baseline.

## Architecture and dependency direction

```text
Decision Core immutable evaluation models
                    ^
                    |
application DecisionCase + serializers + repository/UoW ports
                    ^
                    |
persistence PostgreSQL adapter --> SQLAlchemy/psycopg --> PostgreSQL
                    |
                    +--> explicit Alembic migration
```

Decision Core has no persistence, SQLAlchemy, psycopg, Alembic, FastAPI, Odoo,
configuration, or provenance dependency. Application code imports no concrete
persistence package. Domain/application dataclasses are not ORM entities. Provenance
remains an application-layer `ProvenanceManifest` and is serialized separately from
canonical/core snapshots.

T11 adds no public route/schema, Odoo call or permission, frontend behavior, scoring
policy, or automatic procurement action.

## Database schema and migration

Alembic revision: `20260922_01_create_decision_cases`

Table: `decision_cases`

Relational columns hold the stable case ID, snapshot version, UTC creation time,
lifecycle state, policy name, recommended/selected offer IDs, human outcome,
rationale, UTC decision time, caller-supplied actor reference, and unique idempotency
key. Four logically separate JSONB documents hold canonical input, selected policy,
evaluation result, and provenance.

Checks constrain snapshot version `1`, lifecycle states/outcomes, and required/null
fields for evaluated versus finalized cases. Trigger
`decision_cases_immutable_update` rejects mutation of any evaluation snapshot field
and rejects every change after finalization. Application startup never invokes
`create_all` or Alembic.

## Snapshot format version 1

- Decimal values are finite, plain decimal strings; binary floating point is never
  used.
- Snapshot timestamps serialize as explicit UTC ISO-8601 values ending in `Z`.
- Canonical input preserves requirement, offer/supplier identities, prices, lead
  times, MOQ, fallback profile, history values, sample/window/availability, and
  warnings.
- Selected policy is a separate snapshot so a historical fallback still records the
  historical profile that the caller selected.
- Evaluation supports the legacy `DecisionResult` and active/inactive
  `HistoricalScoringResult`, preserving rank/order, exact scores, criterion order,
  directions, raw/normalized/weight/contribution values, sample size, explanation,
  exclusions, and affected identities.
- Provenance preserves canonical path, field name, source type, source reference,
  and observed-at time. It proves origin only, not objective truth.
- Unknown snapshot versions and malformed serialized values fail clearly.
- Retrieval deserializes the stored documents and never calls a scorer.

## Transaction, immutability, and idempotency rules

A case is inserted atomically in `evaluated` state. Canonical input, selected policy,
evaluation result, provenance, version, creation time, recommendation identity, and
case identity cannot be updated. There is no edit or deletion use case.

Finalization locks the stored row, validates against its persisted eligible ranking,
and updates the state and all human-decision fields in one transaction. The adapter
uses a conditional `evaluated` update as additional double-finalization protection.
A finalized row cannot be changed by the adapter or by direct SQL because of the
trigger.

An exact retry must use the same case, idempotency key, and complete command payload;
it returns the recorded case without another commit. Reusing the key with different
payload or another case fails closed. A different key cannot overwrite a finalized
case.

## Human-decision validation matrix

| Outcome | Recommendation | Selected offer | Rationale | Result |
| --- | --- | --- | --- | --- |
| Accept recommendation | Required | Must equal recommendation | Optional | Accepted |
| Accept recommendation | Missing or different selection | Any | Any | Rejected |
| Override recommendation | Required | Required, eligible, and different | Non-empty | Accepted |
| Override recommendation | Missing, recommended, excluded, or unknown offer | Any | Any | Rejected |
| No award | Optional or missing | Must be absent | Non-empty | Accepted |
| No award | Any | Present | Any | Rejected |

This includes the all-offers-excluded case: no award is valid with a rationale, while
acceptance/override and selection of an excluded offer are rejected.

## Security and operational limitations

- `actor_reference` is caller-supplied attribution. T11 provides no authentication,
  authorization, identity verification, or non-repudiation.
- Provenance records where a value came from; it does not prove that the value is
  objectively true.
- T11 does not provide tamper-proof audit storage, encryption-key management,
  backup/restore, retention, regulatory compliance, or production deployment.
- Database URLs and passwords stay in ignored environment configuration. Tests use
  a separate localhost-only disposable PostgreSQL service.
- The test Compose file supplies `POSTGRES_PASSWORD` only through the env-only
  `${T11_POSTGRES_PASSWORD}` interpolation sourced from the externally required
  variable. It contains no password default or fixed test credential. CI supplies
  a fresh synthetic value per run.
- The persistence path does not use or log Odoo credentials, supplier snapshots,
  provenance documents, or rationales.

## Validation status

| Command | Result |
| --- | --- |
| pre-change fast baseline | PASS — 222 passed, 23 deselected |
| `ruff format --check .` | PASS |
| `ruff check .` | PASS |
| `python -m compileall application backend frontend decision_core odoo_adapter persistence migrations` | PASS |
| `python -m pip check` | PASS — no broken requirements |
| focused T11 unit + architecture tests | PASS — 35 passed |
| `pytest tests/integration/test_decision_case_postgres.py -v` | PASS — 9 passed |
| `pytest -m "not integration and not e2e" -v` | PASS — 246 passed, 32 deselected |
| T10 historical-scoring/core/API regressions | Included in full fast pass |
| `git diff --check` | PASS |
| Odoo and T11 Compose configuration | PASS |
| `pytest -m "integration and not e2e" -v` | PASS — 28 passed, 4 skipped, 246 deselected |
| hosted GitHub Actions | PASS — Quality and Container and API integration |
| hosted review/security checks | PASS — CodeRabbit; GitGuardian ambiguity removed |

Local PostgreSQL validation used the isolated T11 service. Podman's Windows forwarding
helper failed at machine startup, so the test connected through a temporary
localhost-only SSH tunnel; the container was independently healthy before the test.
The full integration run explicitly disabled the four controlled T6/T7-S/T8 live
fixture gates; those tests skipped for that reason. Existing read-only Odoo/API
integration regressions passed. Temporary services, tunnels, and the Podman machine
were stopped afterward without deleting the existing Odoo named volumes.

## Acceptance criteria

| # | Criterion | Status |
| ---: | --- | --- |
| 1 | Starts from merged T10 main | PASS |
| 2 | Existing fast baseline passes | PASS |
| 3 | Decision Core remains persistence-independent | PASS |
| 4 | Input, provenance, result, and human decision remain distinct | PASS |
| 5 | Legacy and historical results reconstruct | PASS |
| 6 | Decimal values round-trip exactly | PASS |
| 7 | Evaluation snapshots are immutable | PASS |
| 8 | Human finalization is transactional | PASS |
| 9 | Accept, override, and no-award rules are enforced | PASS |
| 10 | Excluded and unknown offers cannot be selected | PASS |
| 11 | Override/no-award rationales are enforced | PASS |
| 12 | Finalized decision cannot be overwritten | PASS |
| 13 | Identical retry creates no duplicate | PASS |
| 14 | Conflicting idempotency reuse fails closed | PASS |
| 15 | Schema is created through migration | PASS |
| 16 | Clean-database migration is tested | PASS |
| 17 | Persistence survives separate sessions | PASS |
| 18 | Database errors are translated | PASS |
| 19 | No public HTTP changes | PASS |
| 20 | No Odoo behavior or permission changes | PASS |
| 21 | No frontend changes | PASS |
| 22 | No automatic procurement action | PASS |
| 23 | Existing T0-T10 regressions remain green | PASS — fast suite |
| 24 | Hosted CI passes | PASS |
| 25 | Documentation reflects scope | PASS locally |

## Explicitly out of scope

Public orchestration/API schemas and routes, Odoo-to-evaluate-to-persist flow, Reflex
UI, authentication/authorization, Odoo writes or permissions, scoring/KPI changes,
editing or deleting cases, generic event sourcing, generic lineage, and automatic
supplier or purchase actions remain excluded.

## Recommended T12 scope

Add a thin authenticated-or-explicitly-trusted orchestration/API boundary that
assembles one accepted comparison case, evaluates it using an explicit policy,
stores it once, retrieves the snapshot, and records a buyer decision through the T11
use cases. T12 should define caller authorization and request ownership explicitly,
retain strict decimal/UTC/idempotency contracts, expose no Odoo write, and avoid
recalculation on reads. T13 should remain responsible for dashboard presentation.
