# R9 — Documentation consolidation

Date: 2026-11-10. Worktree branch `claude/r9-docs-911b2d` on `main` `a262a93`.
Uncommitted; the owner commits. Drive was not changed. Documentation only: no runtime
code, comment or docstring changed. Official task: no clause changes; FR-V2/NFR-V2/AC-V2
definitions unchanged.

## Problem

A newcomer could not find a clear way in. The root README mixed a dated status
narrative with the layout; install commands were repeated in README, RUNBOOK and
AGENTS.md; CI scope was described in three places; `AGENTS.md` pointed to a finished
"current plan"; most packages had no README and `odoo_adapter/README.md` described the
pre-R1 state; 22 handoffs still said "not committed"; one handoff section was Hungarian.

## Decision

- Root `README.md` is the entry point: one-paragraph pipeline, architecture sketch,
  quick start that links to the runbook, a package map and one link to the docs index.
- One home per fact: install/run commands in `docs/RUNBOOK.md`, test policy, markers and
  CI scope in `docs/TESTING.md`; the other documents link there. `AGENTS.md` keeps its
  own command block unchanged (it must stand alone for agents, and the brief said to
  change only its plan pointer).
- `docs/REVAMP_PLAN.md` is finished, so it moved to `docs/history/` (`git mv`).
- Each top-level package gets a short README: purpose, entry points, allowed imports
  (from `AGENTS.md` and `tests/test_architecture.py`), where its tests are.
- Handoff status lines name the merging PR (from `git log --first-parent main`);
  evidence lines that record a run on an uncommitted tree stay as they are, since they
  describe that run.

## Implemented behaviour

| File | Change |
| --- | --- |
| `README.md` | Rewritten as entry point; dated status and revamp narrative removed (they live in handoffs) |
| `docs/README.md` | Full index of `docs/`, one line each |
| `docs/history/REVAMP_PLAN.md` | Moved from `docs/`; content unchanged |
| `AGENTS.md` | Only the "current plan" pointer → documentation index |
| `docs/agents/project-baseline.md` | Reviewed against `a262a93`: current state after P0–P4, #50–#57 and R1–R8, one home per concept, what R1 removed, pre-P2 records unreadable (DB reset decision), PDF v3 / ADR-035/036; CI scope now linked to TESTING |
| `docs/TESTING.md` | CI paragraph states the integration workflow's steps and what no CI job runs |
| `docs/TRACEABILITY.md` | Demo evidence commit corrected (`e8b8d04`, the JSON's own `repository.commit`; MILP stays `12f383c`); row 8 UI pages (Home, Cases, wizard, "What if…?"); row 11 CI scope linked to TESTING |
| `docs/ARCHITECTURE.md` | Missing comma in the `tools/` row |
| `docs/LIMITATIONS_AND_FUTURE_WORK.md` | Two REVAMP_PLAN links → `history/`, with section anchor |
| `docs/handoffs/README.md` | New index: P0–P4, follow-ups and fixes, R1–R9 |
| `docs/handoffs/REVIEW_FIXES.md` | Hungarian "Drive teendők" section translated to English |
| 22 handoffs (P0–P4, P3/P4 follow-ups, L6, baseline refresh, review/UI/balanced/guided/final review, R1–R8) | One-line status: "Merged as PR #N"; five REVAMP_PLAN links → `../history/` |
| `decision_core/`, `optimization_adapter/`, `supplier_evaluation/`, `application/`, `persistence/`, `document_adapter/`, `backend/`, `frontend/`, `infra/`, `tools/`, `tests/` `README.md` | New, 10–45 lines each |
| `odoo_adapter/README.md` | Rewritten the same way; explains why `t7s_inventory_history_projection` keeps its historical name |

`migrations/` has no README; `persistence/README.md` and the root map cover it.
`infra/` got one README for both Compose files and both addons instead of one per addon.

## Evidence (commands actually run, Windows 11, Python 3.11 venv)

| Command | Result |
| --- | --- |
| `python <scratchpad>/linkcheck.py .` (relative links and `#anchors` in all tracked and untracked `*.md`, GitHub heading slugs; script not committed) | 148 files; **0 broken outside `docs/history/`**; 50 broken inside `docs/history/` (old locations, pre-existing, that folder is never edited) |
| `rg -n "REVAMP_PLAN" -g "*.md"` | Only intended links: `docs/history/REVAMP_PLAN.md` itself, its links from `docs/README.md`, `docs/handoffs/README.md`, the five P0–P4 handoffs, LIMITATIONS (L7 twice) and project-baseline |
| Hungarian scan of every `*.md` (outside `docs/history/`) and every comment/docstring in `*.py` (tokenize + ast) | No Hungarian prose left; remaining hits are quoted UI/PDF strings (RUNBOOK "Új beszerzés", handoffs, the `approved_pdf.py` docstring quoting the order-line title), UI selectors in `tools/ui_screenshots.py`, generated supplier place names in `tools/seed_odoo_history.py`, and test assertions |
| `python -m tools.dev check` | Passed: ruff format/lint, compileall, **487 passed**, 51 deselected, `uv pip check` compatible (run with the main checkout's `.venv` from the worktree root, final tree) |

Not run: integration and e2e tests (no runtime or test change).

## Limitations

- Package READMEs repeat the import rules of `tests/test_architecture.py` in prose; when
  a boundary changes, both must change. The frontend rule ("backend API only") is not
  enforced by any test.
- `AGENTS.md` still repeats the install commands (by design, see Decision).
- Links inside `docs/history/` stay broken by policy.

## Noticed, not changed

- Drive 06/07 still cite pre-R2 test file names (R2 note); Drive 00/06/07 status headers
  predate R1–R9. Needs an explicit owner request.
- No architecture test stops `frontend/` from importing `backend`/`application`.
- R5: the PDF viewer shows the English "Loading PDF…" on the Hungarian UI; `DESIGN.md`
  could list the supporting tokens from `frontend/theme.py`.
- R7: `docs/MODEL_ML.md` could name `contracts.leaf_score` / `SCORE_STEP`;
  `OPEN_QUOTATION_STATES` is a set, so the Odoo filter's order varies per process.
- R3/R5: English "settled purchase lines" wording is shared by frontend and backend labels
  (owner decision).

## Thesis chapter

Chapter 6 (implementation: repository structure and package boundaries) and chapter 7
(reproducibility: where each command and evidence file is documented).
