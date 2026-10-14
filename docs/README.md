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
- [Saved-case library #32](UX32_LIBRARY_RUNBOOK.md): company configuration, additive
  catalog migration, browsing/bookmarks and owned disposable performance/browser checks.
  [Handoff](UX32_LIBRARY_HANDOFF.md) records dated evidence and limits.
- [Curated Practice #33](UX33_PRACTICE_RUNBOOK.md): offline preparation, deliberate
  exercises, creation classification/replay and disposable verification.
  [Handoff](UX33_PRACTICE_HANDOFF.md) records scope and dated evidence.
- [Responsive workspace #34](UX34_WORKSPACE_RUNBOOK.md): shared navigation, protected
  drafts, case bookmarks and real browser zoom/recovery checks.
  [Handoff](UX34_WORKSPACE_HANDOFF.md) retains dated evidence and limits.
- [Attributed creation review #35](UX35_CREATION_RUNBOOK.md): facts/terms/review,
  preserved editing, deliberate real saves and exact pending recovery.
  [Handoff](UX35_CREATION_HANDOFF.md) distinguishes real runtime from mocked Odoo transport.
- [Saved allocation comparison #36](UX36_COMPARISON_RUNBOOK.md): aligned exact values,
  explicit selection and persistent in-flow review with working finalization.
  [Handoff](UX36_COMPARISON_HANDOFF.md) records real saved 3/5/10-supplier and zoom evidence.
- [Original-base disruption comparison #37](UX37_SCENARIO_RUNBOOK.md): bounded drafts,
  exact saved comparisons, retained original on infeasibility and explicit recovery.
  [Handoff](UX37_SCENARIO_HANDOFF.md) distinguishes genuine saves from controlled read faults.
- [Deliberate decision review #38](UX38_DECISION_RUNBOOK.md): read-only review/cancel,
  exact confirmation, separate No-award and immutable reopening with existing PDF.
  [Handoff](UX38_DECISION_HANDOFF.md) records browser and real transaction evidence.
- [Supplier explanations and exact Audit #39](UX39_EVIDENCE_RUNBOOK.md): saved classes,
  timing/constraints, progressive exact evidence and keyboard/scoped scrolling.
  [Handoff](UX39_EVIDENCE_HANDOFF.md) records stored-only browser/reflow/native-zoom checks.
- [Safe recovery and documents #40](UX40_RECOVERY_RUNBOOK.md): distinct rejection/conflict/
  uncertainty, exact explicit replay, session limits and approved summary/page/zoom/download.
  [Handoff](UX40_RECOVERY_HANDOFF.md) records genuine API faults and exact artifact recovery.
- [Complete buyer reassessment #41](UX41_ASSESSMENT.md): current consolidated flow,
  UX-AC-01–16/canonical mapping, retained accessibility/query evidence and CI limitations.
  [Runbook](UX41_REASSESSMENT_RUNBOOK.md), [frozen human protocol](UX41_BUYER_PROTOCOL.md),
  [blank observations](UX41_OBSERVATIONS_TEMPLATE.csv) and [evidence JSON](UX41_EVIDENCE.json)
  retain owner/novice sessions as NOT ASSESSED until actual observations exist.
- [T15 terminal demonstration](T15_DEMO.md): generate matched synthetic inputs,
  create a base/outage, inspect saved evidence and retrieve after backend restart.
- [T17 complete controlled demonstration](T17_FULL_FLOW_DEMO.md): reproduce read-only
  Odoo acquisition, all stress types, approval/PDF, No-award and stored reopening.
- [T18 #26 repeated HTTP evaluation](T18_26_EVALUATION_RUNBOOK.md): offline matched
  preparation, isolated database/API, two warm-ups, 30 observations and safe cleanup.
- [T18 #27 workload/stress and separate live evaluation](T18_27_EVALUATION_RUNBOOK.md):
  six supported workloads, all stress types/infeasibility and fixed live/stored-only checks.
- [Agent development guidance](../AGENTS.md): scope, architecture, testing and
  followable handoff principles inherited by repository work in future chats.
- [Implementation log](IMPLEMENTATION_LOG.md): dated technical decisions and
  verification evidence; preserved historical limitations.

## Active V2: understand the product flow

[Buyer workspace redesign proposal](UX_UI_INCREMENT_PLAN.md) captures the next
substantial UX/UI discovery after T18. Curated Practice without resets and a bounded
case library, Decision editorial direction and the final brief are confirmed.
The [implementation specification](UX_UI_INCREMENT_SPEC.md), published as
[parent #42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42),
defines bounded discovery/classification, buyer flows and approved reassessment
gates. The [published ten-ticket index](UX_UI_TICKET_BREAKDOWN.md) records #32–#41
and their verified blocking links. #32–#40 now supply local discovery, Practice,
responsive guarded navigation, attributed input review and aligned explicit
comparison, original-base disruptions, deliberate final review and exact supplier
evidence, safe recovery and approved-document navigation; their dated handoffs
distinguish technical evidence from pending participants.
#41 technical consolidation and a frozen protocol are ready; its owner/participant
sessions remain next, and final buyer acceptance stays open.

| Step | Design | Evidence and boundary |
| --- | --- | --- |
| Integer allocation and cost/exposure alternatives | [T13 MILP](T13_V2_MILP_DESIGN.md) | [T13 handoff](T13_HANDOFF.md) |
| Offline Decision Tree and saved supplier evaluation | [T14 ML](T14_ML_DESIGN.md) | [T14 handoff](T14_HANDOFF.md), [controlled metrics](T14_EVALUATION.json) |
| Controlled assembly -> inference -> MILP -> scenarios -> immutable storage | [Reviewed T15 plan](T15_IMPLEMENTATION_PLAN.md) | [T15 handoff](T15_HANDOFF.md) |
| Create a synthetic or prepared-Odoo plan, run all supported stress scenario types and compare stored results | [Synthetic workspace](LOCAL_DEVELOPMENT_AND_SSH.md#controlled-planning-workspace-create-and-test), [Odoo workspace](LOCAL_DEVELOPMENT_AND_SSH.md#controlled-odoo-planning-workspace), [Scenario controls](LOCAL_DEVELOPMENT_AND_SSH.md#what-if-scenarios-and-stored-comparisons) | [T16 handoff](T16_HANDOFF.md) |
| Saved human approval/no-award -> approved snapshot PDF -> full controlled demonstration | [Confirmed plan](T17_APPROVAL_PDF_PLAN.md), [specification](T17_APPROVAL_PDF_SPEC.md), [published tickets](T17_TICKET_BREAKDOWN.md) | [Approval handoff](T17_HANDOFF.md) preserves #20 evidence; [PDF handoff](T17_PDF_HANDOFF.md) records #21. [Planning handoff](T17_PLANNING_HANDOFF.md) preserves the earlier scope. |
| View/download the approved document without reacquiring facts or changing approval | [Closed PDF spike](T17_PDF_SPIKE.md), [PDF walkthrough](LOCAL_DEVELOPMENT_AND_SSH.md#approved-pdf-view-and-download) | [PDF handoff](T17_PDF_HANDOFF.md) preserves #21/local AC-V2-12 evidence; the full-flow row below records the newer #22 status |
| Complete controlled procurement-to-approved-PDF flow, with separate No-award | [Reproduction guide](T17_FULL_FLOW_DEMO.md) | [Full-flow handoff](T17_FULL_FLOW_HANDOFF.md): dated #22 / controlled AC-V2-13 evidence; T17 is now merged with post-merge CI and closed issues, as recorded in README |
| Integrated evaluation and buyer usability | [Confirmed T18 plan](T18_EVALUATION_PLAN.md), [specification](T18_EVALUATION_SPEC.md), [published delivery tickets](T18_TICKET_BREAKDOWN.md) | [#27 handoff](T18_27_HANDOFF.md), [six-workload timings](T18_27_EVALUATION.json), [separate live evidence](T18_27_LIVE_VALIDATION.json), [FR/AC/NFR/RQ inventory](T18_EVIDENCE_MATRIX.md); local targets/live flow passed, including the separate history/security rerun after key renewal. [#28 browser handoff](T18_28_HANDOFF.md), [runbook](T18_28_BROWSER_RUNBOOK.md) and [small evidence record](T18_28_BROWSER_EVIDENCE.json) add local functional Chromium/recovery proof. [#29 assessment/fixes, UX priorities and pending owner run sheet](T18_29_BUYER_ASSESSMENT.md), [small evidence](T18_29_BUYER_EVIDENCE.json) add informed-agent desktop/keyboard/narrow tasks. #30, pending human/text-zoom gates and substantial UX/UI improvement remain. [#26](T18_26_HANDOFF.md) retains the earlier smaller measurement. |
| Consolidated controlled acceptance and next UX/UI increment | [#30 acceptance/RQ assessment and prioritized follow-up](T18_CONTROLLED_ASSESSMENT.md) | [#30 reconciliation/gates](T18_30_CONSOLIDATION_EVIDENCE.json) verifies all six original reports, 2,304 observations, 72 p95 targets and current revision relevance. This supersedes the earlier row's future-#30 status. Controlled functional outcomes pass; human/text-zoom/assistive gates, substantial UX/UI reassessment and final acceptance remain open. |

T15 supports synthetic inputs and a controlled hybrid: live Odoo quotations with
separately synthetic ML history. See [compatibility boundary](T15_ODOO_COMPATIBILITY_PLAN.md)
and the Odoo section of [the terminal demo](T15_DEMO.md). The complete observed Odoo/model
integration, arbitrary quotation selection, broader combined scenarios and full acceptance
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
