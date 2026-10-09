# Domain documentation

This repository uses one domain context.

Before exploring domain behavior, read docs/agents/project-baseline.md, the root
GLOSSARY.md if present, and decisions relevant to the task. Use CodeGraph first
when the existing .codegraph index is present, as required by AGENTS.md.

## Glossary

GLOSSARY.md at the repository root is the shared vocabulary. Use its domain terms
in tickets, designs and tests. Keep implementation details and specifications in
their existing documents. If the glossary does not exist, proceed; create it
lazily when terminology is actually resolved.

## Architecture decisions

Drive 03_ARCHITECTURE_DECISIONS is the canonical accepted ADR register, currently
ADR-001 through ADR-027. Read the relevant records before proposing an architectural
change. docs/adr/ is the location for repository-local technical decision records
when needed; each must link its relevant Drive ADR and state whether it is a
proposal, implementation detail or accepted decision. It is not a replacement
register.

If local ADRs or a glossary are absent, proceed without scaffolding empty files.
Surface conflicts with an accepted ADR rather than silently overriding it.
Preserve accepted records and their identifiers; a superseding decision identifies
its predecessor. Drive updates require an explicit user request.

Use project-baseline.md for source links, requirement traceability and thesis
chapter mapping. Skill examples and generic engineering advice cannot change
the project's existing domain or technology baseline.
