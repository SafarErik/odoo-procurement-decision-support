# T17 specification and ticket handoff — 2026-10-09

Status: PLANNING COMPLETE; SPECIFICATION AND TICKETS PUBLISHED; IMPLEMENTATION NOT STARTED.

## Result and scope

The user confirmed the plan and testing seams, then approved publication of three
vertical implementation slices. This branch supplies Matt Pocock skill routing,
the shared [glossary](../GLOSSARY.md), the [confirmed plan](T17_APPROVAL_PDF_PLAN.md),
the [specification](T17_APPROVAL_PDF_SPEC.md) and the
[published ticket breakdown](T17_TICKET_BREAKDOWN.md).

The specification preserves the official task (423.589/25/140), existing
FR-V2/NFR-V2/AC-V2 identifiers and accepted ADRs. User decisions: only original
bases can be finalized; retained proven plans remain eligible with incomplete-
comparison warnings; historical demo approval is explicit and labelled, with
saved simulation dates distinct from a current server-recorded decision time.

Approval/no-award, approved-snapshot PDF and full-flow acceptance remain open.
No application code, schema, dependency, Odoo data, model or runtime configuration
changed. Observed Odoo-history training/model promotion remains a separate
capability, not part of these tickets. No new accepted ADR or Drive edit was made.

## Published work and dependencies

| Issue | Result | Blocked by |
| --- | --- | --- |
| [#19: parent specification](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19) | Accepted V2 approval/PDF scope and testing seams | Definition only; use the children for implementation |
| [#20: saved human approval/no-award](https://github.com/SafarErik/odoo-procurement-decision-support/issues/20) | Reflex/API/PostgreSQL final decision, integrity, audit, approved content and recovery | None |
| [#21: approved PDF](https://github.com/SafarErik/odoo-procurement-decision-support/issues/21) | Backend render, view/download and safe rendering retry; bounded PDF spike included | #20 |
| [#22: complete local demonstration](https://github.com/SafarErik/odoo-procurement-decision-support/issues/22) | Reproducible controlled hybrid workflow, runtime and acceptance evidence | #21 |

All four issues are open and labelled ready-for-agent. The three child issue bodies,
labels and explicit parent/blocker references were fetched and verified after
creation. The parent body, state and labels were unchanged by child publication.

The connector exposes no native sub-issue/dependency operations. Relationships
are text links, not native GitHub relationship objects. Parent modification was
prohibited by the invoked to-tickets skill, so no parent task list or closure was
added. Work the unblocked frontier: #20 first. A ready label does not authorize
implementation or permit bypassing an unfinished blocker.

## Branch and commit boundary

The current branch is feature/T16-1-matt-skills-setup. Its existing commit
780cf0437a327f0f0d89aeb15c1f9d6d001ed204 adds the approved skills setup on top
of T16 merge 979b9b89e8517c65daefcf7e533c8b3f9c2c0ccd. Live GitHub main was
verified at that T16 merge during this planning session. The setup commit is
already on this local branch; do not recreate it.

The remaining handoff changes to include in the next documentation commit are:

- README.md: dated publication/status reconciliation and next ticket.
- docs/README.md: routes to the approved planning artifacts.
- docs/IMPLEMENTATION_LOG.md: dated planning/publication evidence.
- GLOSSARY.md: resolved domain vocabulary.
- docs/T17_APPROVAL_PDF_PLAN.md: confirmed policy and investigation.
- docs/T17_APPROVAL_PDF_SPEC.md: published parent specification content.
- docs/T17_TICKET_BREAKDOWN.md: approved child bodies and actual dependencies.
- docs/T17_PLANNING_HANDOFF.md: this commit and next-chat handoff.

Review those files, then run the following yourself from the repository root:

```powershell
git add -- README.md docs/README.md docs/IMPLEMENTATION_LOG.md GLOSSARY.md docs/T17_APPROVAL_PDF_PLAN.md docs/T17_APPROVAL_PDF_SPEC.md docs/T17_TICKET_BREAKDOWN.md docs/T17_PLANNING_HANDOFF.md
git diff --cached --stat
git diff --cached --check
git commit -m "Document approved V2 finalization plan and implementation tickets"
```

The first command stages only the eight handoff artifacts; it starts no service.
The next two commands show the staged scope and check whitespace. The final
command records the documentation locally. No application data or history is
reset. If the staged scope contains unrelated work, review it before committing.

Suggested PR title: **Align engineering skills and specify V2 approval/PDF work**.
After your commit/push, open the PR from this branch to main, review the complete
diff (including the existing setup commit), and check CI for its exact new SHA
before merging. This PR prepares the implementation; it does not close #19–#22.
The agent has not staged, committed, pushed, created a PR or merged.

## Verification and limits

- Issue readback: parent and three children verified against the approved content;
  ready-for-agent labels, open state and text dependencies verified.
- Documentation PASS: eight handoff files, 91 local links, 32 user stories, three
  complete ticket templates, source identifiers, dependency order and whitespace.
  Local specification/ticket bodies match the verified published content;
  git diff --check passed and the Git index remains unstaged.
- Application tests were not repeated for these documentation-only edits. Earlier
  skill-setup evidence records Python 3.11.16, 521 passed / 45 deselected / one
  existing warning, plus Ruff format/lint, compileall and pip check. These are
  historical setup results, not new planning runtime evidence.
- The earlier Podman Compose configuration gate remains blocked by unavailable
  local socket connectivity. No service, database, live Odoo or browser application
  check was started here. A documentation handoff does not resolve that runtime gate.
- Hosted CI for the final documentation commit remains pending user publication.
  Approval/PDF behavior, AC-V2-11/12/13 and observed-model claims are not established
  by published issues.

## Next chat after merge

Start a fresh implementation branch from updated main and authorize #20 only.
Use this prompt:

> Implement https://github.com/SafarErik/odoo-procurement-decision-support/issues/20
> only. Read AGENTS.md, glossary, parent specification #19 and this planning
> handoff. Start from updated main on a new codex/ branch. Preserve the official
> task, existing FR/AC identifiers and accepted ADRs. Follow the ticket's
> acceptance criteria and verification gates; update affected documentation and
> report evidence, limitations and unrun gates. Do not implement #21/#22 yet.
> No Odoo writes or Drive edits. Leave changes uncommitted for my review; keep
> commit, push and merge under my control.

The next buyer-visible result is a saved human decision that survives reload and
exact retry. PDF follows after that ticket passes its gates. T18 integrated
evaluation and T19 thesis closure remain separate. Hungarian Drive synchronization
requires its own explicit request.

## Thesis-useful record

Problem: V2 machine plans currently stop before human finalization.
Decision: preserve immutable planning evidence, add a separate human outcome and
derive backend PDF from approved content; use three bounded vertical slices.
Implemented behavior: engineering guidance/glossary and published work definitions;
no new procurement behavior.
Evidence: source investigation, refreshed canonical requirements/ADRs, confirmed
user decisions and verified issue publication.
Limitation: controlled synthetic/historical context, PoC actor attribution,
unimplemented approval/PDF, open runtime and final evaluation gates.
Chapter relevance: 3 requirements/traceability; 4 lifecycle/architecture; 5
invariants; later 6 implementation and 7 acceptance/content identity/runtime;
8/9 conclusions and further work.
