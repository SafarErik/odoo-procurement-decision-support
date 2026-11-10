# R8 — Tools and CI that explain themselves

Date: 2026-11-06. Worktree branch `claude/r8-tools-ci-1cc27e` on `main` `09d8bd2`.
Merged as PR #60 (the rename was staged with `git mv` so Git keeps the
history). Drive was not changed. Official task: no clause changes (technical debt only);
FR-V2/NFR-V2/AC-V2 definitions unchanged. Behaviour-preserving for every tool and CI gate.

## Problem

- `tools/t17_demo.py` was named after an increment but is the shared HTTP acceptance flow:
  `tools.demo`, `tools.milp_evaluation` and `tests/test_full_http_flow.py` import it, and
  the integration workflow's path filter listed only that one tool file.
- `tools/ui_screenshots.py` ran code at import time and was only runnable as
  `python tools/ui_screenshots.py OUT CASE`.
- The Quality workflow repeated what `python -m tools.dev check` does (format, lint,
  compile, fast tests, pip check) and had drifted: its `compileall` list missed `tools`.
- Stale increment names in CI (`t11-quality.env`, `t11-persistence-compose.log`,
  "T11 test PostgreSQL") and in tool help/report labels ("P4 …", "T17 demonstration").
- `pyproject.toml` described an "ERP-independent development foundation"; ruff's
  `known-first-party` missed `document_adapter`, `tools` and `tests`.
- Reflex sometimes writes `.states/` at the repository root; it was not ignored.

## Decision

- Rename by purpose: `tools/t17_demo.py` → `tools/http_flow.py`; default output
  `.artifacts/t17-demo` → `.artifacts/http-flow`; run reports `t17-run-*.json` →
  `http-flow-run-*.json`. CLI (`run`, `reopen`) and behaviour unchanged.
- CI calls the local gate: Quality runs `python -m tools.dev check` and keeps only what
  `check` does not do (install, `git diff --check`, Compose `config` validation). CI
  installs with pip, so `check` takes its existing `pip check` branch; no uv in CI.
- `ui_screenshots` becomes `python -m tools.ui_screenshots CASE_ID [--out DIR]` (default
  output unchanged: `docs/evidence/p3`). No `tools.dev` subcommand: `tools.dev` takes
  exactly one argument and this tool needs a case id, so a pass-through would have added
  argument plumbing for one command. Instead `tools.dev --help` lists every standalone tool.
- Not renamed (persisted or owner-decided): `PDSS-GEN-P1` tag and the Odoo note text the
  seeder writes, evidence file names `docs/evidence/P1_*.json` / `P4_*.json` and their
  JSON field names, `t17-*` document/decision version identifiers, env vars
  (`ODOO_T7S_API_KEY`, `RUN_T6_LIVE_CONTRACTS`, `RUN_T7S_LIVE_CONTRACTS`), the addon
  directory. Evidence files were not regenerated, so the committed reports keep their
  old `"report"` label values ("P4 …"); the next regeneration writes the new labels.

## Implemented behaviour — tool map

| Tool | Purpose | Command | Reads | Writes | Odoo |
| --- | --- | --- | --- | --- | --- |
| `tools/dev.py` | Developer entry point; `--help` lists commands and tools | `python -m tools.dev check\|db-up\|db-down\|api\|ui\|odoo-up\|odoo-down\|demo` | `.env` | `.artifacts/` temp dirs (check) | `odoo-up/down` start/stop the container; `demo` reads only |
| `tools/http_flow.py` | Full HTTP acceptance flow and stored-result check (shared by demo and evaluation) | `python -m tools.http_flow run --odoo-history N --actor … --reason … --no-award-reason …`; `… reopen --report FILE` | running API, `API_SERVICE_TOKEN` | `.artifacts/http-flow/http-flow-run-*.json` + 4 PDFs; cases in the API's planning DB | read only, via the API |
| `tools/demo.py` | One-command demonstration with isolated replay | `python -m tools.dev demo` or `python -m tools.demo [--group N]` | `.env`, seeded Odoo, trained model | `docs/evidence/P4_DEMO_REPORT.json`, `.artifacts/demo/`; dev planning DB | read only |
| `tools/milp_evaluation.py` | MILP/API latency and correctness vs. exhaustive reference | `python -m tools.milp_evaluation [--repetitions 30] [--warmups 2]` | `.env`, `TEST_DATABASE_URL`, `.artifacts/seed/evaluation_groups.json` | `docs/evidence/P4_MILP_EVALUATION.json`, `.artifacts/evaluation/`; test planning DB | read only |
| `tools/seed_odoo_history.py` | Generated purchase history and evaluation groups | `python -m tools.seed_odoo_history plan\|apply [N]\|groups` | `.env` (`ODOO_SEED_*`) | `.artifacts/seed/manifest.json`, `evaluation_groups.json` | **writes** `pdss_history_gen` only (guarded); `plan` writes nothing |
| `tools/train_history_model.py` | Offline supplier-model extraction, training, re-evaluation | `python -m tools.train_history_model extract\|train\|all\|report` | `.env`, Odoo history (restricted user) | `.artifacts/ml/`; `report` → `docs/evidence/P4_ML_REPORT_CHECK.json` | read only (`extract`) |
| `tools/ui_screenshots.py` | UI evidence screenshots, desktop and 375 px | `python -m tools.ui_screenshots CASE_ID [--out docs/evidence/p3]` | running `tools.dev api` + `ui` | PNGs + `report.json` in `--out` | none directly |

Other changes:

- `quality.yml`: one "Fast quality gate" step; env file `persistence-quality.env`.
- `integration.yml`: path filter `tools/**`, plus `optimization_adapter/**` and
  `alembic.ini`, which the integration tests depend on but the filter missed; log
  `decision-db-compose.log`; message "Decision test PostgreSQL …".
- `tests/test_architecture.py`: the two CI self-checks now assert that Quality runs
  `python -m tools.dev check` on Python 3.11, that `check` selects the unmarked suite,
  and that `tools.dev.PACKAGES` covers `supplier_evaluation`, `optimization_adapter`, `tools`.
- `pyproject.toml`: accurate description; `known-first-party` += `document_adapter`,
  `tests`, `tools`. `.gitignore`: `/.states/`.
- Docs: RUNBOOK §5.3 command, ARCHITECTURE `tools/` row, TESTING CI sentence.

## Evidence (commands actually run, Windows, Python 3.11.15, main checkout's `.venv`)

- `python -m tools.dev check` — first run: 2 failed / 456 passed (the old CI assertions
  in `test_architecture.py`, fixed afterwards); final run: exit 0 — ruff format/check
  clean, compileall incl. `tools`, 458 passed / 51 deselected, `uv pip check` clean (the
  uv-created local venv has no pip; CI takes the `pip check` branch).
- `pytest tests/test_architecture.py tests/test_full_http_flow.py tests/test_validation_tools.py` — 37 passed.
- `--help` exit 0 for `tools.dev`, `http_flow`, `demo`, `milp_evaluation`,
  `train_history_model`, `ui_screenshots`, `seed_odoo_history`; `tools.dev bogus` exits 2.
- `python -m tools.seed_odoo_history plan` — summary printed, no writes. `apply`/`groups` not run.
- Live demonstration through the renamed flow: `tools.demo.main(["--directory", <scratch>,
  "--report", <scratch>/demo-report.json])` with the main checkout's `.env` loaded and
  `SUPPLIER_HISTORY_MODEL_DIRECTORY` set to the absolute model path (the worktree has no
  `.env`/model) against the running Odoo and planning DB — exit 0, group 1, 9 scenarios,
  13 operations replayed with Odoo unreachable and no model, `passed: true`, 36.8 s.
  Report written outside the repository; committed evidence not touched. It stored new
  demonstration cases in the development planning database, as the tool documents.
- Both workflows parse as YAML (PyYAML) with the expected steps and path filters;
  `git diff --check` clean;
  `rg -n "t17_demo|t11-|T11|T13/T14" -g '!docs/history/**' -g '!docs/handoffs/**'` —
  only a false positive inside a hash in `frontend/reflex.lock/bun.lock`.

Not run: hosted CI (runs after the cockpit pushes), `actionlint` (not installed),
`docker compose config` on the CI env files (Compose files unchanged; only the temp env
file name changed), integration and e2e suites (no persistence/UI code changed),
`tools.milp_evaluation` (~15 min, writes the test DB), `tools.ui_screenshots` capture,
`http_flow` CLI `run`/`reopen` against port 8000 (its functions ran inside the demo).

## Limitations

- `tools.dev check` runs pytest with `-q`, so the CI log no longer lists every test name.
- `--help` of `tools.demo` and `tools.milp_evaluation` fails with `UnicodeEncodeError`
  when stdout is a cp1250 pipe on Windows (pre-existing; `→`/`Σ` in the docstrings). It
  works in a console or with `PYTHONUTF8=1`.
- The committed `P4_*.json` evidence keeps the old `"report"` label text until regenerated.

## Thesis chapter relevance

Testing and operations chapter: one quality gate shared by local work and CI (no drift
between the two), and a tool map that states for each tool what it reads, writes and
whether it touches Odoo (read-only vs. the guarded seeding of the dedicated test database).
