# Buyer reassessment protocol — #41

Version **UX41-v1**, frozen 2026-10-13 before any novice observations.
Owner pilot: **NOT ASSESSED**. Unfamiliar participants: **0 recorded**.
Source baseline: `6535b0ef4e829acd36ba2284d9e1e3658987b95d`.
This is a protocol, not completed human evidence. The approved gate and task goals
come from [#42's specification](UX_UI_INCREMENT_SPEC.md#buyer-reassessment-protocol-and-completion).
The [assessment](UX41_ASSESSMENT.md) separates technical delivery from human acceptance.

## Cohort and fixed conditions

Run an informed owner pilot first; it never counts toward novice completion.
Before the first novice, declare a cohort of 3–5 people who understand purchasing
and have not used this app. Record prior knowledge, consent to observation and
withdrawal, and the declared cohort size. Use coded IDs O01 and P01–P05; no personal
names, credentials or contact details belong in repository evidence. Keep consent
and identity information separately. Do not select cohort size or exclude failures
after seeing results.

Use one fresh owned helper stack per session, through the [runbook](UX41_REASSESSMENT_RUNBOOK.md).
Its offline three-supplier synthetic fixture has product `synthetic-product`, demand
10 piece, EUR, saved reference 2026-03-01 and required date 2026-03-08. Minimum cost
is 102 EUR and the distinct saved alternative 109 EUR. These are simulation values;
decision record time is current UTC. Start with two older Practice drafts prepared
through the API, then the participant creates fresh work. Retain setup UUIDs for the
facilitator only. Do not supply a UUID, direct case bookmark or procedural click
instructions for the find/open task. Do not reset any owner or Odoo database.

Freeze the source SHA, copied frontend hashes, versions, initial case IDs/save times,
browser/device, viewport/zoom and session start in the session record. Record any
deviation before tasks. A separate assessment environment is facilitator isolation;
Practice itself still shares its configured application's storage and has no reset.
Use the same fixed prompts and setup for each novice. Accessibility repeats follow
the first attempts, with their device/zoom/assistive mode explicitly recorded.

## Neutral introduction and essential tasks

Read: “This is a controlled procurement demonstration. Work through the tasks as
you normally would, and explain what you understand from the screen. Tell me when
you finish or cannot continue. You may ask for help; I will record it.” Do not teach
the controls or the correct comprehension answers before their task.

| ID | Participant prompt | Observable outcome and comprehension check |
| --- | --- | --- |
| B01 | Prepare and save an example comparison. Explain where the example's numbers come from and where saved work remains. | Curated Practice entry/review precedes an explicit save. Understand generated history/model evidence, explicit terms and shared persistence; no operational/current-validity or automatic Odoo-order claim. |
| B02 | Return to the case you just saved using its product, quantity/date and save time, without using a UUID or bookmark. | Find/open from Cases with the appropriate workspace/context; selected stored identity matches facilitator evidence. Reopening is a read, not a recalculation or new save. |
| B03 | Compare the alternatives and choose one for review. Explain supplier quantities, extra cost and exposure. | Exact saved allocations cover demand; distinguish 102 from 109 EUR and the 7 EUR premium. Exposure is a synthetic uncalibrated proxy, not failure probability. Selection alone is not approval. |
| B04 | Test what happens when one supplier becomes unavailable. Return to the original. | Feasible original-base supplier-outage child is saved and identified as analytical; explain changed supplier availability and unchanged original. |
| B05 | Test demand beyond the suppliers' combined capacity. Explain the result and what happened to the original facts. | Infeasible demand child (use 1000 if the participant requests a fixed setup value) preserves original quantities/cost; absent scenario allocation is unavailable, not zero. Changed demand totals are not like-for-like savings. |
| B06 | Deliberately approve the saved alternative on the original and explain what becomes permanent. | Correct original/plan/context, actor reference, reason and acknowledgement are reviewed before confirmation. Understand immutable finalization, caller-supplied actor text and no Odoo order. No unintended approval. |
| B07 | On a separate fresh example, decide to decline the offered plans. Explain the saved outcome. | Separate reasoned No-award is deliberate and immutable; no selected allocation or approved PDF. Use a fresh original, never overwrite B06. |
| B08 | Save another fresh example during the staged service interruption, then recover when access returns. | Pending outcome remains uncertain; navigation/context cannot replace intent. Explicit retry retains exactly the original payload/key. Explain session-loss limits and support evidence. |
| B09 | Find the approved case again, reopen its saved summary, navigate and download its document despite the staged document interruption. | Library reopening identifies B06; approved allocation/date/cost remain visible during failure. Retry accesses PDF only. Use page controls and fit/zoom; download the exact artifact. Explain eligibility/source limits. |

After B01/B03/B06/B09, ask the listed comprehension questions neutrally and record
the participant's words. For source authority, also show the fixed captured-Odoo
input example from [#35 evidence](UX35_CREATION_HANDOFF.md), labelled as a retained
controlled-reader fixture, and ask how its quotation prices differ from generated
ML history and explicit business terms. Do not describe it as a new live Odoo read.

## Timing, assistance and observations

Start human elapsed time when the prompt is read; stop at completion or declared
inability to proceed. There is no human time SLA. Record interrupted/waiting time,
including service restore, separately in comments; never use pytest/service latency
as human time. Stop promptly on an unintended finalization or critical source/decision
misunderstanding; record the failure before explaining the safe next step.

Use [the blank observation template](UX41_OBSERVATIONS_TEMPLATE.csv), copied to a
session artifact directory. Replace TEMPLATE with the coded participant/session and
owner/unfamiliar role; create one row per B01–B09 first attempt. Record completion,
independence, exact assistance, mistakes, human seconds, comprehension, unintended
finalizations, critical misunderstanding/resolution, evidence path and comments.
Blank means missing, never zero/false. Record “not attempted” explicitly where needed.
Retakes use separate rows with incremented attempt and version; preserve first rows.

The facilitator may restore owned services or supply the stipulated infeasibility
quantity as setup; log that setup distinctly. Hints locating controls, explaining
answers, choosing a plan, copying a UUID or instructing retry are task assistance.
Do not quietly demonstrate a failed task and then mark it independent. Screen-reader
speech and physical-phone behavior need their own actual sessions, not emulation.

## Fixed acceptance rule and revisions

A first-attempt success requires completed=yes, independent=yes, sufficient
comprehension and no task-solving assistance. Compute each B01–B09 separately over
the declared novice cohort; missing/unfinished tasks do not become successes.
Owner/agent observations and retakes are excluded from the independent novice
numerator. Record all raw rows and exact denominators.

| Novice cohort | Required independent successes for **every** essential task |
| --- | ---: |
| 3 | 3 |
| 4 | 4 |
| 5 | 4 |

This is `ceil(0.8 × n)`, with n≥3, plus **zero unintended finalizations and zero
unresolved critical source/decision misunderstandings**. It is a small qualitative
PoC gate, not population statistics. Fewer than three novices or absent owner
evidence remains NOT ASSESSED/pending; a technical PASS cannot close final acceptance.

Record findings with severity, affected task/source/version, raw observation,
decision/fix and retest evidence. Fix critical findings and repeat affected tasks;
retain original failures. A coached retake confirms a fix, not new novice independence.
If source/fixture/prompts change, preserve UX41-v1 and observations, issue a dated
version and freeze it before further observations. No threshold relaxation, silent
rewriting of failed rows or outcome-based participant exclusion is permitted.

Human sessions are the remaining input. Owner approval, novice validation and
assistive/device checks retain separate decisions. No tracker closure, T19, merge,
publication or Drive update follows automatically from this protocol.
