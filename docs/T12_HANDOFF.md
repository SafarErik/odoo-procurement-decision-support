# T12 handoff — controlled end-to-end orchestration API

## Result and baseline

T12 implements the bounded backend decision-case flow on
`codex/t12-controlled-e2e-orchestration-api`, based on merged `origin/main`
`0a1eee8a323f6cfe68a5cc30319d1f8c058d5c26` (PR #12 / T11). The mandatory
fetch found no newer main commits. Pre-change checks passed: 246 fast tests,
32 deselected; Ruff format/check, compileall, and pip check passed. The branch is
for PR review and must not be merged by the implementation agent.

## Architecture and API

The dedicated `application/decision_case_orchestration.py` use case owns the
sequence from explicit `purchase_group_id` through bounded read-only Odoo facts,
source-attributed supplemental terms, optional exact-line T7-S/T8 history,
`AssembledDecisionInput`, one fixed T10 policy evaluation, and atomic T11 case
persistence. FastAPI routes only map input/output and stable errors. The existing
`POST /api/v1/procurement/decisions/evaluate` is unchanged. Decision Core weights,
normalization, MOQ ordering, historical complete-case activation, and fallback are
unchanged. No Odoo write, automatic award, frontend, or new permission is added.

| HTTP endpoint | Contract |
| --- | --- |
| `POST /api/v1/procurement/decision-cases` | Canonical UUID `Idempotency-Key`; initial `201`, exact completed replay `200`, conflicting key `409`; body selects one explicit Odoo group, per-offer attributed MOQ and lead time, one of six fixed policies, optional exact-line history |
| `GET /api/v1/procurement/decision-cases/{decision_case_id}` | Stored T11 snapshots only; no Odoo/history access, assembly, KPI calculation, or rescoring |
| `POST /api/v1/procurement/decision-cases/{decision_case_id}/final-decision` | Separate canonical UUID `Idempotency-Key`; T11 accept/override/no-award rules and one-time idempotent finalization |

All three routes require `Authorization: Bearer <T12_TRUSTED_CALLER_TOKEN>`.
Missing/wrong token is `401`; an unset server token is `503`. The token is stored as
`SecretStr` and compared in constant time. This is a **shared PoC caller secret**,
not production identity management. `actor_reference` is caller-supplied audit
metadata, not authenticated buyer identity. It may differ from the shared secret.
OpenAPI states this explicitly. The API returns typed stored snapshot sections and
decimal strings, UTC times, provenance, warnings, contributions, exclusions,
historical activation/fallback context, and optional human decision.

## Persistence and idempotency

Alembic revision `20260922_02` adds `decision_case_creations` after T11's
`20260922_01`. A canonical UUID key maps to a SHA-256 fingerprint of normalized
caller intent and one unique case foreign key. The fingerprint excludes the bearer
secret, server-generated IDs/timestamps, and live Odoo values; it sorts unordered
offer/supplier/line selections and normalizes Decimal and UTC timestamps. A
transaction advisory lock serializes same-key requests. Exact replay returns the
persisted case before upstream reads or scoring. A conflicting request fails before
upstream calls. Case and key mapping commit atomically, and failed attempts leave no
completed mapping. This is separate from T11 finalization idempotency. T11's
database-enforced immutable snapshot trigger remains active. Startup never creates
or migrates the schema automatically.

## Verification

All counts below are local, not hosted CI claims. The project `.venv` uses Python
3.14.7 locally; Python 3.11 remains the compatibility baseline.

| Check | Observed result |
| --- | --- |
| Pre-change `pytest -m "not integration and not e2e" -q` | 246 passed, 32 deselected |
| Focused T12 unit/API/architecture selection | 38 passed; includes explicit zero-scorer replay/read/finalization and safe repository-error response |
| T11/T12 PostgreSQL selection | 14 passed, including migration, durable replay, concurrency, atomic rollback, and actual HTTP lifecycle |
| Full `pytest -m "integration and not e2e" -q` with controlled live gates disabled | 33 passed, 4 skipped, 271 deselected; existing live RFQ/security/service regressions passed |
| Final fast `pytest -m "not integration and not e2e" -q` | 271 passed, 37 deselected |
| `ruff format --check .`, `ruff check .`, compileall, pip check | Passed after the final source formatting pass |
| Odoo and isolated persistence Podman Compose `config --quiet` | Both passed |
| `git diff --check` | Passed; Windows line-ending conversion notices only |
| `reflex export --frontend-only --no-zip` | PASS on final retry with installed Node 24.20.0; production build completed 4/4. The first attempt had no active Node version and the next attempt timed out during prerender; the final retry succeeded. No T12 frontend code was added. |

The first full integration attempt failed 17 existing Odoo/service tests because the
Odoo stack was stopped and localhost forwarding was unavailable. After starting
the existing Odoo stack and establishing a localhost-only SSH tunnel, the full
selection passed. The four controlled T6/T7-S/T8 live fixture gates stayed
explicitly disabled and are **SKIPPED**, not passed. The T12 actual HTTP integration
uses deterministic upstream fakes with real PostgreSQL; it does not claim a new
live three-supplier historical-scoring fixture. No browser E2E suite was run.

## Limits and follow-up

The supported Odoo subset remains a single product/UoM/currency, one line per RFQ,
zero tax/discount, bounded explicit group. Supplemental MOQ and promised lead time
are supplied and source-attributed, not independently verified. Historical line IDs
must be explicitly supplied; arbitrary supplier history discovery is unavailable.
The T7-S identity and normal read-only integration identity remain separate.
Historical scoring is an uncalibrated bounded PoC policy. The shared bearer secret
does not identify individual buyers or provide production IAM. The transaction
remains open across bounded upstream reads to guarantee same-key serialization;
production throughput and deployment security require separate review. Existing
Odoo named volumes were preserved.

After acceptance/merge, synchronize Google Drive living documents
`00_THESIS_STATUS`, `02_ROADMAP`, `03_ARCHITECTURE_DECISIONS`,
`06_REQUIREMENTS_BASELINE`, and `07_DEVELOPMENT_STATUS`. Add a new ADR for the
trusted-caller and creation-idempotency boundary; do not silently rewrite ADR-022.
No Google Drive document was changed here.

## Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| 01 | PASS | Fetched and branched from exact merged T11 main; baseline recorded |
| 02–03 | PASS | Dedicated application coordinator; thin routes |
| 04–07 | PASS | Explicit group via read-only adapter, exact attributed terms, no forbidden fallback or writes |
| 08–09 | PASS | Only T7-S/T8 exact-line history; no invented values |
| 10–12 | PASS | Six fixed IDs, unchanged T10 active/fallback and all-excluded behavior |
| 13–17 | PASS | Separate durable create key; replay/conflict/concurrency/atomicity PostgreSQL tests |
| 18–20 | PASS | One immutable case; GET uses stored snapshots only |
| 21–24 | PASS | Existing T11 finalization use case, outcomes, idempotency, immutable machine snapshots |
| 25–28 | PASS | Caller-supplied actor reference; shared secret gate; no committed secret |
| 29–32 | PASS | T3 unchanged; core independent; explicit migration; immutable trigger preserved |
| 33–35 | PASS | Fast, architecture/API, PostgreSQL, and full integration selections green after services started |
| 36 | PASS | README, implementation log, design, handoff, env example, persistence guide updated |
| 37–38 | PASS | No frontend implementation, automatic award, or purchasing action |

Proposed PR title: **T12: controlled decision-case orchestration API**

Proposed PR description: Add a trusted PoC HTTP boundary and application coordinator
for explicit Odoo comparison cases, attributed supplemental terms, optional bounded
history, fixed policy evaluation, and immutable PostgreSQL case creation. Add
atomic creation idempotency in Alembic `20260922_02`, stored-only retrieval, and
T11 human finalization endpoints. Include fast, architecture, API, concurrency,
rollback, and actual HTTP-to-PostgreSQL tests. No Odoo write, frontend, or automatic
supplier decision is introduced. Note the controlled live gates that were not run.
