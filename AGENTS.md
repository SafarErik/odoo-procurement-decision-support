# Development guidance

## Project in one paragraph

Python side-by-side decision support for Odoo 19 (BSc thesis, task 423.589/25/140):
read-only Odoo facts + sourced buyer terms → Decision Tree supplier evaluation →
MILP allocation with cost/risk alternatives → stress scenarios on the same MILP →
human approval or No-award → approved PDF. One product, one approved demand, N
suppliers. Start with [README.md](README.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
and the current plan [docs/REVAMP_PLAN.md](docs/REVAMP_PLAN.md).

## Workflow

- One branch and one PR per increment. The owner commits, pushes and merges:
  leave changes in the working tree unless explicitly asked to commit.
- Describe each increment as a buyer-visible capability or a needed dependency,
  with an acceptance outcome. Historical T-/UX-numbers are references only.
- End every increment with an English handoff in `docs/handoffs/`: problem →
  decision → implemented behavior → evidence (commands actually run) → limitation →
  thesis chapter. Name unrun gates explicitly. Update README/TRACEABILITY only when
  their meaning changed. Never rewrite files in `docs/history/`.
- Prefer small demonstrable increments and reuse over speculative abstraction.
- Google Drive holds the Hungarian thesis, requirements (FR-V2/NFR-V2/AC-V2), ADRs
  and roadmap. Change Drive only on explicit request.

## Architectural boundaries

- `decision_core/` stays independent of Odoo, FastAPI, Reflex, databases and provenance.
- Odoo access only through `odoo_adapter/` and the official API; never Odoo's database.
- The frontend talks only to the backend HTTP API; no Odoo, database, ML training or
  solver logic in Reflex. Route handlers stay thin; use cases live in `application/`.
- Solver code stays in `optimization_adapter/`; ML dependencies stay in `supplier_evaluation/`.
- Training is offline. HTTP requests never train, and callers never choose model files.
- Stored cases are immutable; GET and exact retries never re-read Odoo, re-score or re-solve.
- Keep generated (synthetic) and observed data distinguishable in provenance.
- Never commit secrets; local values live in the ignored `.env`.

## Odoo writes

- The runtime backend is read-only toward Odoo.
- A scripted **seeding tool** may write generated purchase history into a
  **dedicated Odoo test database** with an administrator key the owner provides
  (approved 2026-10-17 for P1). It must refuse any other database, tag what it
  creates as generated, and never run from the backend.
- Do not drive the owner's Odoo browser session. For manual Odoo configuration give
  numbered steps (app, menu path, fields, values, buttons, expected effect, rollback),
  wait for confirmation and verify the postcondition with a read-only probe.

## Language

English for all repository artifacts (code, tests, UI string keys, docs, commits).
The UI ships Hungarian (default) and English texts. Thesis text is Hungarian and
written by the owner.

## Commands

Python 3.11 is the compatibility baseline (local and CI).

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -e ".[frontend,dev]"
python -m tools.dev check      # required before handoff
python -m tools.dev db-up | api | ui | odoo-up
```

Details: [docs/RUNBOOK.md](docs/RUNBOOK.md), [docs/TESTING.md](docs/TESTING.md).

## Verification policy

- Unmarked tests are fast; `integration` needs services; `e2e` needs a browser stack.
- Actual CBC and scikit-learn execution is part of the fast gate; missing runtimes fail.
- Run focused tests while working and `tools.dev check` once before handoff.
  Run integration/e2e when the change touches persistence, Odoo or UI flows and the
  services are available; otherwise record them as unrun.
- Verify visual UI changes in the built-in browser, including narrow width and errors.
- Never claim a check passed that was not run. Local success is not hosted CI.
- Database-resetting tests use only the disposable test database.

## Code navigation

When a `.codegraph/` index exists, use `codegraph explore "<question>"` before broad
searches. Do not rebuild it unless asked.

## Agent skills

Before planning, specification, research, implementation or review, read
[docs/agents/project-baseline.md](docs/agents/project-baseline.md) and the
task-relevant Drive sources. Map work to the official task and FR-V2/AC-V2 IDs.

- Issue tracker: GitHub Issues in SafarErik/odoo-procurement-decision-support
  ([docs/agents/issue-tracker.md](docs/agents/issue-tracker.md)).
- Triage labels: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix
  ([docs/agents/triage-labels.md](docs/agents/triage-labels.md)).
- Domain docs: root GLOSSARY.md and docs/adr/ when needed; Drive remains the
  canonical ADR register ([docs/agents/domain.md](docs/agents/domain.md)).
