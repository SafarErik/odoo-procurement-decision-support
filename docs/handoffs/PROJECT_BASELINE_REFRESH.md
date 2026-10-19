# Project baseline refresh after the revamp

Date: 2026-10-19. Prepared in worktree branch `claude/pensive-blackwell-ca7a26` (from `main` at `e3cbf84`), copied into the owner's checkout.
Not committed; the owner commits. Documentation only; no requirement or code change.
Drive was read, not changed.

## Problem

[docs/agents/project-baseline.md](../agents/project-baseline.md), which agents read before
every task, still described 2026-10-09: PR #18, open AC-V2-11/12/13, T13–T17 evidence
routes, an open PDF library choice and V1 compatibility. Agents would plan against closed
gates and removed code.

## Decision

Keep the guide's structure and Drive link list; replace only stale facts. Route detail to
[TRACEABILITY.md](../TRACEABILITY.md) and Drive 06 instead of duplicating the status table.

## Implemented behavior

- Header: reviewed 2026-10-19 against `e3cbf84` and the 2026-10-18/19 Drive sync.
- Drive 03 described as ADR-001–034; Drive 06 as the AC-V2 status table holder.
- Accepted-baseline table: ReportLab as the PROVISIONAL PDF renderer; V1/WSM described as
  removed (ADR-028) with evidence in `docs/history/`.
- Official-task traceability table: evidence routes point to ARCHITECTURE, MODEL_ML,
  MODEL_MILP, TESTING, TRACEABILITY, LIMITATIONS_AND_FUTURE_WORK, the P0–P4 handoffs and
  `docs/evidence/`, plus the relevant ADR-024–034.
- "Dated reconciliation and open acceptance" replaced by "Current state (main e3cbf84)":
  all AC-V2 LOCAL PASS in the controlled scope, training on generated Odoo-read history in
  `pdss_history_gen`, single case-creation path, bidirectional scenarios, PDF v2, bilingual
  UI, removed V1; remaining items are limitations (L1–L13), not gates.

## Evidence

- Facts taken from Drive 03 and 06 (read 2026-10-19), `docs/TRACEABILITY.md` and the P4
  handoff.
- All relative links in the updated guide resolved to existing files (local script).
- `python -m tools.dev check` (shared main-checkout `.venv`, Python 3.11.15): 496 passed,
  51 deselected; `uv pip check` clean. Integration and e2e not run (docs-only change).

## Limitation

The guide is a snapshot; it names `e3cbf84` and must be refreshed after the next merge
that changes status. Hosted CI was not re-run for this docs-only change.

## Thesis chapter

None directly; supports agent routing for chapters 2–9.
