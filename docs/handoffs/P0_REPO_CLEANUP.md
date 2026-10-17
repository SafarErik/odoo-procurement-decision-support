# P0 — Repository cleanup and structure

Date: 2026-10-18. Branch: `feature/p0-repo-cleanup`. Status: implemented in the
working tree, not committed (owner commits). Plan: [REVAMP_PLAN.md](../REVAMP_PLAN.md).

## Problem

The repository mixed the obsolete V1 product (Weighted Sum ranking, V1 decision
cases) with the current V2 planning system, recorded its state as a ~100-file
increment diary, carried a "Practice/controlled" workspace dimension through API,
database and UI, and used increment numbers in configuration names. A reader (or
the thesis author) could not tell what the product is or how to run it.

## Decisions

1. **Remove V1 completely.** The official task needs supplier evaluation with a
   decision tree and MILP allocation; the WSM ranking is not part of it (ADR-024
   already superseded it). Owner confirmed V1 compatibility is not required.
2. **Derive data origin instead of storing a classification.** Whether a case is
   demo data or comes from Odoo already follows from the stored snapshot
   (`facts.input_kind`). The separate `planning_case_catalog` table and the Practice
   area were removed; the library filters by `origin = all | demo | odoo`.
3. **One baseline migration.** With V1 and the catalog gone, the six development
   migrations were folded into `20261018_01_create_planning_schema`. Existing local
   databases must be recreated (owner accepted resets).
4. **Archive, do not rewrite, history.** All earlier docs moved unchanged to
   `docs/history/`; new current docs are short and organized by component.
5. **Descriptive settings.** `T12_TRUSTED_CALLER_TOKEN` → `API_SERVICE_TOKEN`,
   `T15_TRUSTED_MODEL_DIRECTORY` → `SUPPLIER_MODEL_DIRECTORY`,
   `T11_TEST_DATABASE_URL` → `TEST_DATABASE_URL`, `T11_POSTGRES_*` → `TEST_POSTGRES_*`.

## Implemented behavior

- Deleted V1 code: `application/decision_*`, `application/decisions.py`,
  `decision_core/{models,decision,constraints,normalization,errors}.py`,
  `backend/app/routes/{decisions,decision_cases}.py`, `backend/app/decision_case_schemas.py`,
  `persistence/postgres.py`, `tools/t9_scoring_evaluation.py`, V1 request schemas
  and their tests. Routes `/api/v1/procurement/decisions*` and `/decision-cases*` are gone.
- Shared pieces V2 still needed were extracted into V1-free modules:
  `application/errors.py` (`RepositoryError`), `application/provenance.py`,
  `application/odoo_quotations.py` (Odoo quotation facts and reader port),
  `persistence/session.py`, `backend/app/api_common.py` (strict model base, UTC
  validator, service-token gate). `SqlAlchemyPlanningUnitOfWork` is now standalone.
- Practice removed: `/practice` page and nav entry, catalog context in requests and
  responses. Case responses and library rows carry `origin`; UI shows "Data origin:
  Demo data / Odoo" and a Data origin filter.
- New: `tools/dev.py` (`check`, `db-up`, `db-down`, `api`, `ui`, `odoo-up`,
  `odoo-down`), `infra/app/compose.yaml` (persistent planning DB with named volume),
  rewritten `.env.example`, README, AGENTS.md, PRODUCT.md, and docs
  `ARCHITECTURE.md`, `MODEL_MILP.md`, `RUNBOOK.md`, `TESTING.md`, `TRACEABILITY.md`.
- Fix: `tools/t18_evaluation.py` decoded `git diff` with the Windows code page and
  crashed on non-ASCII diffs; it now decodes UTF-8 with replacement.

Size: 220 files changed, about 149k lines removed (mostly archived JSON evidence
moved, plus V1 code/tests). Python in `application`, `backend`, `decision_core`, `persistence` and `tools` went from 10,593 to 6,224 lines.

## Evidence (run 2026-10-18 on Windows, Python 3.11.15 uv venv)

| Check | Result |
| --- | --- |
| `python -m tools.dev check` (format, lint, compileall, fast tests, dependency check) | PASS — 511 passed, 55 deselected; `uv pip check` compatible |
| Integration/e2e collection (`pytest -m "integration or e2e" --collect-only`) | collects without import errors |
| `reflex export --frontend-only --no-zip` | compiles 19 pages/components |
| Built-in browser, `/cases` without backend | Data origin filter shown, backend-unavailable message shown, navigation lists only Cases and Open RFQs |
| `pytest -m "integration and not e2e"` on the disposable PostgreSQL 16 (Podman 6.1.4) | 23 passed: squashed migration, immutability triggers, idempotency/concurrency, decisions, PDFs, origin filter; 19 live-Odoo tests skipped (no Odoo credentials) |
| `python -m tools.dev db-up` with temporary credentials | container healthy, `alembic upgrade head` creates `planning_cases`, `planning_final_decisions`, `planning_documents`; volume removed afterwards |
| `tests/integration/test_runtime_services.py` against a running FastAPI | health and planning-token (401) checks pass; Odoo HTTP check fails because Odoo was not started |

Fast-test count fell from 707 to 511: the removed tests covered deleted V1 code
(WSM core, V1 decision API/cases/orchestration, T9 scoring) and the Practice catalog.

## Not verified / remaining

- Live Odoo contract tests and the Odoo HTTP runtime test were not run: Odoo is not
  set up on the recreated Podman machine (its earlier volumes did not carry over).
- Podman setup note: on this host the machine only started after `wsl --update`
  and recreating it (`podman machine rm -f`, `podman machine init`).
- e2e browser tests were updated mechanically but not run; the Practice navigation
  e2e test was deleted (P3 adds navigation e2e for the new UI).
- Hosted CI not run (no push).
- `test_runtime_services.py`: the V1 decision-endpoint check was replaced by a
  planning-route token check.
- Test files still carry increment numbers (`test_t13_planning.py`, …).

## Owner action

1. Fill `.env` from the new `.env.example` (new setting names).
2. Review and commit the branch.

## Thesis relevance

Chapter 4 (architecture): component table and boundaries in `ARCHITECTURE.md`.
Chapter 5: `MODEL_MILP.md` formulation and the stated linear-exposure limitation.
Chapter 6/7: `RUNBOOK.md`, `TESTING.md`; `TRACEABILITY.md` is the task → chapter table.
The V1/WSM history can be mentioned briefly as the earlier ranking approach that
was replaced because a ranking does not answer "how much from whom".
