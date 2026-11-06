# R6 — Backend shared kernel and clean module boundaries

Date 2026-11-06, branch `claude/r6-backend-kernel-f54796` on main `09d8bd2`, uncommitted.

## Problem

The same concept lived in several places: `(code, message)` error classes, identity/UTC
validators, the SHA-256 hex regex (×5), vocabulary literals (`"odoo_json2"` ×6,
`"generated"/"observed"`, languages, the 30 s solver limit ×3), request limits written
twice (pydantic and application), stored contract ids spread over four modules, and
JSON-2 client boilerplate copied across the Odoo readers. `application` and
`supplier_evaluation` imported each other, and `backend/app/dependencies.py` contained
use-case logic (buyer defaults, the one-line-group rule).

## Decision

Behaviour-preserving consolidation into the existing natural home; a new module only
where none existed (`application/stored_contracts.py`, `odoo_adapter/json2_client.py`).
Stored values unchanged (owner decision). Dependency direction: application → ML package,
never the reverse.

## Implemented behaviour — where each concept lives

| Concept | Module |
| --- | --- |
| `CodedError` base, `PlanningCaseError`, `RepositoryError`, `ProcurementData*` | `application/errors.py` (`InvalidPlanningInput` stays in `decision_core`, which may not import upward) |
| ValueError identity/UTC checks (`text_identity`, `utc`) | `supplier_evaluation/contracts.py` (now also used by `application/purchase_history.py`, `ExternalRiskContext`) |
| Coded planning checks (`identity`, `require`, `decimal`) | `decision_core/planning/models.py` (unchanged) |
| SHA-256 hex (`SHA256_HEX`, `is_sha256_hex`) | `application/planning_serialization.py`; the decision schema builds its pattern from it |
| Stored ids: snapshot/decision/content/PDF versions, `HISTORY_INPUT_KIND`, `t14-` risk prefixes, `controlled-proxy-v1`, `backend-owned-odoo-history` | `application/stored_contracts.py` |
| Advisory-lock prefixes `t15:`/`t17:`/`t21:pdf:`; snapshot check constraint built from `SNAPSHOT_VERSION` (same SQL, no migration) | `persistence/schema.py` |
| `HISTORY_SOURCE`, `HISTORY_GENERATED`/`HISTORY_OBSERVED`/`HISTORY_DATA_ORIGINS` | `supplier_evaluation/contracts.py` (Odoo history reader, config and PDF texts import them) |
| `ODOO_JSON2_SOURCE` | `application/odoo_planning_input.py` |
| `SOLVER_TIME_LIMIT_SECONDS` | `decision_core/planning/planner.py` |
| Limits `MAX_SUPPLIERS`, `MAX_EPSILONS`, `SCORE_QUANTITIES` | `application/planning_input.py` |
| `DECISION_OUTCOMES`, `MAX_ACTOR_LENGTH`, `MAX_RATIONALE_LENGTH` | `application/planning_decisions.py` |
| `SCENARIO_KINDS` (now an ordered tuple) | `application/planning_cases.py` |
| Route language/kind `Literal`s | read `supplier_overview.LANGUAGES`, `planning_documents.DOCUMENT_LANGUAGES/KINDS` |
| ML → MILP risk bridge `risk_inputs` | `application/procurement_planning.py` (was `supplier_evaluation/planning_bridge.py`, deleted) |
| Odoo capture + preview buyer defaults | `application/planning_history.py` (`capture_odoo_history`, `odoo_history_preview`); binding in `application/odoo_planning_input.bind_odoo_history_input`; `dependencies.py` only wires readers/settings and bridges async with `asyncio.run` |
| JSON-2 client, error mapping, datetime/id helpers | `odoo_adapter/json2_client.py` (`Json2Reader`, `odoo_errors`, …) |

Also: unused ports `PlanningDecisionRepository`/`PlanningDocumentRepository` deleted;
`PurchaseHistoryPort` kept (the capture use case is typed against it, architecture test
checks it). New architecture test: `supplier_evaluation` never imports `application`.

Verified and left as is:
- Route-level Odoo → 503/502 mapping exists only in `routes/quotation_groups.py`; planning
  routes receive `PlanningCaseError` codes from the use case, so no shared helper was added.
- `routes/planning_cases._library` keeps hand parsing: FastAPI `Query` cannot reject unknown
  or repeated parameters and would change the 422 body format (comment added).
- `planning_cases.validate_snapshot` keeps its lazy `history_model` import: the metadata
  contract depends on the model's training configuration; moving it is not a small change
  (comment added).

## Evidence (commands actually run)

- Baseline before edits: fast tests 458 passed.
- `python -m tools.dev check` (final tree): format, lint, compile, **461 passed** (458 +
  the boundary test + two Odoo error-mapping cases), 51 deselected, `uv pip check` OK.
- `pytest -m "integration and not e2e"` with `RUN_ODOO_HISTORY_LIVE=true` on a fresh
  disposable test DB (`podman run postgres:16.15-bookworm` on 127.0.0.1:55432, `.env`
  credentials; `podman compose` hits Docker's provider here, as in R2): **46 passed,
  2 skipped** (opt-in `RUN_T6_LIVE_CONTRACTS`/`RUN_T7S_LIVE_CONTRACTS`). The two
  `test_runtime_services` checks query whatever API listens at `BACKEND_BASE_URL`
  (port 8000, not started from this tree).
- `python -m tools.demo` against the running Odoo (`pdss_history_gen`) and development
  planning DB (services already up, so the `tools.dev demo` compose step was skipped):
  case, nine scenarios, approval, No-award, HU/EN plan and audit PDFs, and the replay
  with Odoo unreachable and no model all passed. The same demo from `HEAD` code
  (`git archive` copy, same day) gave **identical** plans, allocations, costs, risk
  exposures, scenario statuses and supplier assessments; only case ids, timings and
  id-dependent hashes differ. Scores differ from the committed October report because
  the history window follows the current date. `docs/evidence/P4_DEMO_REPORT.json` was
  restored to its committed version (the run was on a dirty tree).
- `ponytail-review` over the diff: two findings, both fixed (evidence file restored; test
  for unreachable Odoo → unavailable and HTTP 500 → bad response in
  `tests/test_odoo_comparison_case_adapter.py`).
- OpenAPI schema and `Settings` JSON schema dumped from `HEAD` (via `git archive`) and from
  this tree: **byte-identical**.
- `rg -n '\[0-9a-f\]\{64\}'`: one backend definition (`planning_serialization.py`); two
  remaining hits in `frontend/` (R3 scope).
- `rg -n '"odoo_json2"|"generated"|"observed"|timeout_seconds=30|time_limit=30'`: backend
  only constant definitions; remaining hits in `frontend/` (R3), `tools/train_history_model.py`
  (R8) and tests (fixtures asserting stored wire values, intentionally literal).

## Not run (name explicitly)

- Browser e2e (`pytest -m e2e`); hosted CI. Rerun `tools.demo` after the commit if a
  commit-exact `P4_DEMO_REPORT.json` is wanted.

## Limitations

- `ExternalRiskContext` references now also reject leading/trailing whitespace (shared
  `text_identity`); generated references never contain any.
- `application/purchase_history.py` validation messages lose their field label (messages
  never reach HTTP responses).
- The currency read now sends the same `User-Agent` header as the other Odoo reads.
- `supplier_overview.LANGUAGES` and `planning_documents.DOCUMENT_LANGUAGES` are still two
  definitions; R3 owns `supplier_overview.py` this round — follow-up after R3 merges.
- Odoo adapter now imports `supplier_evaluation.contracts` (dependency-free) for
  `HISTORY_SOURCE`; `ARCHITECTURE.md` updated accordingly.

## Thesis relevance

Architecture chapter: layer directions (core ← ML contracts ← application ← adapters/backend),
one home per concept, and stored contract identifiers as an explicit compatibility surface.
