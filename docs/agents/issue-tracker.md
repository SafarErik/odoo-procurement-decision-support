# Issue tracker: GitHub

Issues and specifications live in GitHub Issues for
SafarErik/odoo-procurement-decision-support.

Use gh from the repository root when available. Confirm the target repository
before writing. If gh is unavailable, use an authenticated GitHub connector that
supports the required operation; report unsupported operations instead of claiming
they succeeded. Do not install global tooling merely to hide an unavailable command.

## Conventions

- Read: gh issue view <number> --json number,title,body,labels,comments.
- List: gh issue list --repo SafarErik/odoo-procurement-decision-support --state open --json number,title,body,labels.
- Create: gh issue create --repo SafarErik/odoo-procurement-decision-support --title "..." --body-file <file>.
- Comment: gh issue comment <number> --body-file <file>.
- Label: gh issue edit <number> --add-label "<label>" or --remove-label "<label>".
- Close: gh issue close <number>.
- Read PR context with gh pr view <number> and gh pr diff <number>.
- Resolve ambiguous #numbers as a PR or issue before acting.
- For multiline bodies, write exact text to a temporary UTF-8 file and use --body-file.

When a skill says "publish to the issue tracker", create a GitHub issue within the
user-authorized task. When it says "fetch the relevant ticket", read that issue.
Sending comments/messages requires explicit user authorization or authorization
from an explicitly invoked skill. This configuration alone is not authorization.

## Ticket content

Before publishing a specification, consult project-baseline.md. Record the
buyer-visible capability, scope, relevant FR-V2/AC-V2 identifiers, acceptance
outcome, verification gates, limitations and evidence links. Preserve the existing
Drive roadmap rather than generating a competing backlog.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Parent tickets and dependencies

Prefer native GitHub sub-issues and issue dependencies when the available tool
supports them. Native dependency APIs require the issue database ID, not its
displayed #number. With unsupported operations, use "Part of #<parent>" in the
child and a task list in the parent; use "Blocked by: #<number>" for dependencies.
Keep fallback links consistent. Do not assume a gh version supports newer flags.

For wayfinder, the map is one issue labelled wayfinder:map; children use
wayfinder:research, wayfinder:prototype, wayfinder:grilling or wayfinder:task only
when that workflow is invoked. Select an open, unassigned child with no open
blockers; claim/resolve it only within the authorized workflow. These optional
labels are not part of initial setup.
