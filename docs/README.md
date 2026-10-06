# Documentation map

Start with [README](../README.md) for current capability/status, then select the
procedure or design you need. You do not need to read the project chronologically
to run it. T-numbered files retain evidence from their increment; dated branch,
CI, scope and "uncommitted" statements describe that time unless a newer status
explicitly supersedes them. They are not a second live dashboard.

## Current terminal procedures and working principles

- [Local development and SSH](LOCAL_DEVELOPMENT_AND_SSH.md): choose the task,
  activate Python, start only its services, interpret checks and clean up.
- [Persistence development](PERSISTENCE_DEVELOPMENT.md): isolated database,
  Windows forwarding workaround, destructive test boundary and Alembic.
- [Agent development guidance](../AGENTS.md): scope, architecture, testing and
  followable handoff principles inherited by repository work in future chats.
- [Implementation log](IMPLEMENTATION_LOG.md): dated technical decisions and
  verification evidence; preserved historical limitations.

## Active V2: understand the product flow

| Step | Design | Evidence and boundary |
| --- | --- | --- |
| Integer allocation and cost/exposure alternatives | [T13 MILP](T13_V2_MILP_DESIGN.md) | [T13 handoff](T13_HANDOFF.md) |
| Offline Decision Tree and saved supplier evaluation | [T14 ML](T14_ML_DESIGN.md) | [T14 handoff](T14_HANDOFF.md), [controlled metrics](T14_EVALUATION.json) |
| Controlled assembly -> inference -> MILP -> scenarios -> immutable storage | [Reviewed T15 plan](T15_IMPLEMENTATION_PLAN.md) | [T15 handoff](T15_HANDOFF.md) |

T15 currently uses explicitly synthetic inputs. The complete observed Odoo/model
integration and buyer-facing V2 frontend, approval/PDF and end-to-end acceptance
remain open. The accepted thesis/technology baseline is unchanged.

## Historical foundations: consult when their behavior matters

| Topic | Records |
| --- | --- |
| Environment, RFQ listing, canonical WSM and its API | [T0](T0_HANDOFF.md), [T1](T1_HANDOFF.md), [T2](T2_HANDOFF.md), [T3](T3_HANDOFF.md) |
| Odoo comparison mapping and attributed supplemental terms | [T4](T4_HANDOFF.md), [T5](T5_HANDOFF.md), [T6 design](T6_DESIGN.md), [T6 handoff](T6_HANDOFF.md), [manual fixture](T6_FIXTURE_SETUP.md) |
| Bounded company-scoped history and read-only projection | [T7 handoff](T7_HANDOFF.md), [T7 historical fixture](T7_FIXTURE_SETUP.md), [T7-S security design](T7S_DESIGN_SECURITY.md), [T7-S setup](T7S_MANUAL_SETUP.md), [T7-S handoff](T7S_HANDOFF.md), [T8](T8_HANDOFF.md) |
| History-aware V1 scoring and reference evaluation | [T9 design](T9_SCORING_DESIGN.md), [T9 handoff](T9_HANDOFF.md), [T10](T10_HANDOFF.md) |
| V1 immutable cases and controlled orchestration API | [T11](T11_HANDOFF.md), [T12 design](T12_DESIGN.md), [T12 handoff](T12_HANDOFF.md) |

V1 records/routes remain supported. Their WSM ranking and single-offer finalization
are historical/regression capabilities, not V2 allocation/approval acceptance.

## Closed discovery records: question -> evidence -> decision

- [Initial Odoo capability](spikes/odoo-capability-spike.md).
- [Odoo decision-input mapping](spikes/odoo-decision-input-mapping-spike.md).
- [Comparison-case enablement](spikes/odoo-comparison-case-enablement.md).
- [Historical supplier performance](spikes/odoo-historical-supplier-performance.md).

These explain why mappings, supplemental input and permission boundaries exist.
Reopen a specific question only when its assumptions change. They are not mandatory
reading for every implementation increment or blanket production-readiness claims.

## Thesis writing and Drive responsibilities

Drive is the Hungarian living thesis workspace. It owns the official task/title,
requirements, architecture decisions, roadmap and writing/research material.
Repository technical evidence is linked rather than copied as a development diary.

| Drive document | Update when |
| --- | --- |
| 00_THESIS_STATUS | Current capability or the next meaningful milestone changes |
| 02_ROADMAP | Next increment, dependencies or priority changes |
| 07_DEVELOPMENT_STATUS | A reviewed result supplies thesis-useful evidence/limitations |
| 06_REQUIREMENTS_BASELINE, 03_ARCHITECTURE_DECISIONS | A requirement or substantive architectural decision changes |
| 01/04/05/08 | Outline, research, writing guidance or theoretical explanation changes |
| 99_PROJECT_INSTRUCTIONS_REFERENCE | The user asks to synchronize enduring workflow instructions |

No routine ten-document synchronization is required. Drive writes still require
an explicit user request. Current Drive status is summarized in the repository
README with its last synchronization date; archives remain historical evidence.

For each completed increment, retain a compact thesis note:
**problem -> decision -> implemented behavior -> evidence -> limitation -> chapter
relevance**. A test count supports a described result; it is not the result itself.
Link the exact dated handoff/log and relevant hosted run when available.
