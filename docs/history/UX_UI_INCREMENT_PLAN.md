# Buyer workspace redesign — discovery and delivery proposal

Date: 2026-10-12. Status: **CONFIRMED BRIEF — [specification #42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42) and [ten delivery tickets](UX_UI_TICKET_BREAKDOWN.md) approved, published and verified; implementation pending**.
This plans a substantial UX/UI increment after T18. Ticket publication was
separately approved; no production routes, migrations or UI are implemented by
this planning work. T19 remains thesis closure after development and reassessment.

## Outcome and evidence

A first-time procurement buyer should be able to start or find a recognizable
case, understand supplier quantities and the cost/exposure trade-off, test a
disruption, deliberately finalize a choice and reopen its approved document.
The interface should make these tasks understandable without a terminal runbook.

The current functional chain already works. The redesign addresses
[UX29-03–10](T18_29_BUYER_ASSESSMENT.md#observed-findings-and-prioritized-uxui-follow-up),
not a hypothetical replacement of the decision engine. Most urgent are entry and
retrieval, mobile hierarchy and contextual approval. Focus continuity, preserved
infeasible baseline facts, recovery and document navigation also need improvement.
UX29-01/02 feedback roles are already fixed and must remain covered.

At reviewed HEAD `eec2ba11ec4fcf0727a66218596ee01a63aac6d0`, exact-SHA
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38216056407)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38216056497)
workflow conclusions are SUCCESS. This is CI evidence, not a new browser or
human-usability assessment. [T18's report](T18_CONTROLLED_ASSESSMENT.md) remains
the evidence baseline; unfamiliar-buyer usability is NOT ASSESSED.

The living Drive 00/06/02/03 documents were read on 2026-10-12. Their accepted
requirements and architecture still apply, but their 2026-10-11 status paragraphs
predate the T17 merge and completed T18 work. Current repository evidence governs
technical status; this proposal neither edits Drive nor changes its requirements.

## Confirmed product decisions

1. **Practice boundary — CONFIRMED:** curated synthetic examples with honest
   persistence labels and no database reset. A UI toggle does not guarantee storage
   isolation; separate storage/reset is outside this increment.
2. **Return journey — CONFIRMED:** include a bounded saved-case library rather than
   requiring buyers to retain UUIDs, as an explicit backend/API slice.
3. **Product foundation — CONFIRMED:** English, desktop-first procurement workspace
   with usable mobile layouts and the existing read-only decision workflow.

The user answered all three on 2026-10-12. [PRODUCT.md](../PRODUCT.md) records that
confirmed context and links the accepted baseline. The user then selected
Decision editorial in the local review page and confirmed that choice in chat.
The user also confirmed the final brief and authorized specification work on
2026-10-12. No production implementation is approved here. Local decision sketches
are planning material, not functioning app screens.

## Visual-direction review

The product's distinctive mechanism is exact multi-supplier allocation with
explainable alternatives, explicit simulated disruption and an immutable human
choice. The first screen must demonstrate that comparison and choice, with familiar
procurement navigation. Cultural references below are design hypotheses, not
research about participant preferences. They contribute type, palette, density and
one signature treatment; they do not dictate unusual controls or task metaphors.

Seven grounded candidates were considered: Swiss financial-report graphics
(comparison alignment); civic service design (clear next action); contemporary
industrial catalogues (readable allocation/specification rhythm); gallery
wayfinding (quiet sectional hierarchy); architectural publication grids
(side-by-side explanation); transport signage (legible task emphasis); and ISO
technical-document typography (exact evidence hierarchy). Generic KPI dashboards
and decorative futuristic cockpits were excluded from the direction search.

The local review page presents these static desktop sketches:

| Direction | Visual and structural proposal | Trade-off |
| --- | --- | --- |
| Precision procurement | Navy rail, warm ground, terracotta selection; parallel quantity rows with an adjacent selected-plan summary | Strong specification clarity; compact rows need deliberate mobile reflow |
| Decision editorial — USER SELECTED | Deep-green rail, soft mint ground, purple selection; full-width aligned comparison and persistent review strip | Calm and readable; more familiar, so distinction depends on comparison quality |
| Clear next step | Dark rail, yellow navigation band, green selected alternative; explicit next-task emphasis above side-by-side exact data | Strong wayfinding; yellow must never become indistinguishable from amber warnings |
| Familiar business workspace | Conventional white sidebar, neutral cards and blue selection; parallel plans and review panel | Familiar structure with less distinctive visual character |

Impeccable's structured direction exploration assigned the industrial-catalogue
candidate and supplied six challenger systems. Airport wayfinding remained a
competitive alternative on task clarity. Orienteering, vertical media, mixtape,
tabbed manual and photographic exposure notation were declined on buyer relevance
and comparison clarity; their useful disciplines remain explicit: source/change
distinction, one primary task, reconciled demand totals, stable wayfinding and
aligned exact comparisons. Their costumes, gestures and specialist controls do
not enter the procurement workflow. These judgments are design reasoning, not
measured human preference.

Four HTML sketches and their desktop captures live under ignored
`.impeccable/mocks/decision/`; the local selection page/answer record lives under
ignored `.impeccable/questions/`. They use T18's actual demo demand, allocations,
EUR 102/109 costs, EUR 7 premium and alternative exposure `9661/50000`. Minimum-cost
exposure is not fabricated where the sketch omits it. Labels identify static
Practice/synthetic examples. The sketches were viewed in the built-in browser;
they are fixed desktop compositions, not responsive or functional acceptance.
The recorded answer is `optionId=model-pick`, `buildPath=code`, with no steer or
build-path change. Its selected sketch is
`.impeccable/mocks/decision/model-pick.html`; the reviewed capture is
`.impeccable/mocks/decision/review/decision-editorial.jpg`. The declared PNG comp
slot is unused and no generated image exists there. The local page's “Build this”
control selected the planning direction; this request remains planning-only.

## Final design brief — confirmed

**Job and audience:** an English, desktop-first workspace for a procurement buyer
unfamiliar with the app. The buyer can find work, compare exact allocations and
costs, test assumptions and deliberately finalize a saved original-base decision.

**Selected direction:** Decision editorial. Preserve the chosen sketch's deep-green
navigation rail, soft mint ground, purple selected alternative, precise typography,
aligned full-width comparison and persistent selected-plan review strip. The
comparison is the visual focal point; its aligned supplier quantities and exact
premium make the decision understandable. Extend this grammar to entry, creation,
scenarios, explanation, recovery and documents. The sketch's static desktop frame
does not settle responsive behaviour, every state or the final token values.

**Workflow and scope:** Cases / Open RFQs / Practice globally; Plans / What-if /
Suppliers / Audit within a case. Include the bounded stored-case library, curated
Practice without resets, attributed-input review, comparison, all five existing
scenario types, deliberate approval/No-award and approved-document access. Keep
technical audit available behind readable buyer explanations. Reuse Reflex and
the current engine, API clients, immutable decision/PDF and original-base semantics.

**Interaction and layout:** initial and empty states provide a useful next action;
loading and backend failure remain distinct. Selection is visibly separate from
approval. Exact pending intent survives uncertainty and contextual navigation.
On narrow screens, replace global navigation with a labelled drawer, reflow the
comparison and keep selected-plan context near review without obscuring content.
Preserve original facts beside infeasible or changed-demand scenarios, keyboard
focus continuity, alert/status semantics and actual PDF integrity.

**Proof and limits:** implement the six bounded slices below with meaningful
API/persistence/browser checks and task-based owner/novice reassessment. Test
3/5/10-supplier content, variable alternatives, narrow layouts, actual browser text
zoom and relevant assistive behaviour. Curated examples remain synthetic and saved
Practice is not isolated storage. Odoo quotations still use a synthetic model;
no probability/operational validity or authenticated-actor claim. Unfamiliar-buyer
usability remains NOT ASSESSED until participant evidence exists.

**Builder decisions still to specify:** bounded list pagination/filter contract,
server-owned case purpose and ambiguous legacy handling, draft/context navigation,
session-loss recovery limits, responsive compositions and observable usability
acceptance criteria. These are specification work, not missing approval of the
selected visual direction. Do not create a competing brand or re-run direction
selection unless the user requests a change.

## Proposed information architecture

Use a compact desktop sidebar for **Cases / Open RFQs / Practice**, with contextual
help. Cases is the normal landing page and contains a clear New comparison action.
Open RFQs retains the existing read-only ledger; a link from a row must not imply
that arbitrary RFQs can already become valid V2 cases. Practice is an explicit
entry point, not a production/development switch disguised as an ordinary setting.

Inside an opened case, retain **Plans / What-if / Suppliers / Audit**. Keep product,
quantity/unit, currency, recorded date, base/scenario identity and decision status
in a concise case header. Review decision and Approved document are contextual
actions with a clear return path. Global navigation chooses work; case navigation
explains the selected work. Avoid duplicated sidebars and unrelated dashboard KPIs.

On phones, replace the global sidebar with a labelled menu/drawer. Keep case
identity, current outcome and next action before setup/help paragraphs. Reflow
comparison and forms deliberately; horizontally scrolling exact tables may remain
in labelled keyboard-accessible regions. Do not shrink the desktop screen intact.

Proposed buyer journey:

```text
Cases → New comparison → Review facts and terms → Saved Plans
      → Open saved case                         → Plans / What-if / Suppliers / Audit
Practice → Choose an example → Same labelled workflow
Saved Plans → Review selected decision → Approved / No-award
Approved → View or download approved document → Return to saved case
```

### Entry, case library and Practice

- Case rows show recognizable product/context, demand, saved time, source and
  decision status. Start with bounded pagination and a small set of useful filters;
  decide search scope in the API contract. Original cases lead, with scenarios
  grouped beneath their base. Keep UUID copy/open as a secondary support function.
- Empty, loading, unavailable and genuinely empty-filter states have different
  explanations and useful next actions. A missing backend never looks like no work.
- Practice offers a few curated tasks: compare alternatives, test a disruption and
  understand infeasibility. Reuse offline prepared inputs and the actual HTTP chain;
  do not replace real calculations with invented UI results. Distinguish opening a
  saved example from calculating and saving a new practice case.
- Show Practice continuously on its cases, decisions and document context. Explain
  whether results are saved and where. Existing test/benchmark cases must not flood
  the buyer's library. Do not bulk-delete, relabel or alter historical snapshots.
- Both current pathways use a synthetic Decision Tree. Therefore synthetic ML is
  **not** a reliable marker of Practice: the Odoo pathway also has synthetic ML.
  Server-owned case-purpose/catalog metadata needs a bounded design. Ambiguous old
  cases stay explicitly unclassified; a browser filter is not access control.
- Switching context must preserve a pending exact request. Block switching while
  its outcome is uncertain; protect unsaved form edits separately. Session loss and
  multi-tab recovery remain explicit design questions, not promises of durability.

### Create and compare

Present creation as three understandable stages: confirm the prepared facts,
complete business terms, review and calculate/save. This is guidance, not a forced
tour that prevents an experienced buyer moving directly to a task. Label capacity,
MOQ and promised dates as supplied terms; distinguish captured preview time from
the new Odoo read performed by FastAPI. Keep policy and validity bounds reviewable.

Plans lead with exact total cost, supplier allocations, delivery terms and
meaningful alternative premiums. Use selectable plan summaries with a visible
selected state instead of a label-only approval dropdown. Keep the cost/exposure
chart as supporting explanation and an exact tabular equivalent. Exposure is a
synthetic, uncalibrated proxy; never label it failure probability or real savings.
Keep single-plan/no-distinct-alternative outcomes understandable.

### Scenarios and deliberate approval

What-if shows the original base, draft changes and saved scenario together. All
five existing stress types remain available. Original cost and allocations stay
visible when a scenario is infeasible; absent scenario values are not zero. A demand
change is not a like-for-like saving, and a simulated price is not a refreshed quote.
Scenario children cannot be approved; returning to the original base is explicit.

Review decision shows the selected exact allocation/cost/exposure, relevant dates,
reason and actor attribution before a deliberate final confirmation. Alternative
selection and No-award retain required reasons; No-award has its own action and
explanation. Cancelling review performs no write. Submitting remains exactly one
immutable backend intent with the existing key/recovery semantics. Explain that
actor text is attribution, not authenticated identity, and no Odoo order is created.

### Explanation, recovery and documents

Supplier views lead with readable class/constraint explanations; tree paths,
versions and exact provenance stay available in Audit. Move developer test scripts
and execution instructions into Practice/help/runbooks, while concise source and
authority limits remain visible in every relevant workflow.

For uncertain saves, lead with “We cannot confirm whether this was saved” and a
clear action that resends the exact original request. Do not create a new intent,
automatically retry or claim failure means no save. Keep technical key/payload
details available as support evidence. Distinguish validation, infeasibility,
service failure, finalized conflict and unavailable PDF. A PDF failure preserves
the approved state; recovery must not suggest approving again.

Documents show a concise **saved approved** summary, page navigation, zoom and exact
artifact download. Reuse the backend renderer and current PDF viewer first. Any
later PDF layout revision is a separate version/content compatibility decision;
the existing document audit and immutable artifacts must remain intact.

## Reflex implementation shortlist and seams

Official [Drawer](https://reflex.dev/docs/library/overlay/drawer/) supports a sidebar
menu pattern; compose the persistent sidebar with existing layout primitives.
[Tabs](https://reflex.dev/docs/library/disclosure/tabs/) suit the four case views,
[Radio Group](https://reflex.dev/docs/library/forms/radio-group/) suits explicit plan
selection, and [Alert Dialog](https://reflex.dev/docs/library/overlay/alert-dialog/)
provides deliberate confirmation. Use Theme, Table/Data List, Accordion, Skeleton
and persistent Callout feedback where they serve a task. Use
[responsive styling](https://reflex.dev/docs/styling/responsive/) for topology changes.
Do not add components merely to demonstrate the library.

Installed Reflex 0.9.12 exposes these component names (verified by import on
2026-10-12). This confirms availability, not correct props, rendering or accessible
behaviour. Prove small compositions against the installed version before broad UI
work; an upgrade or new dependency requires a concrete compatibility reason.

Reuse `frontend/app.py`, `frontend/theme.py` and the existing planning state/input/
scenario/result/audit/decision/PDF modules and HTTP clients. Keep business rules in
the backend. Current planning routes provide create, from-Odoo, scenario, get-by-ID,
final-decision and PDF, **not list/search**. A case library therefore reaches the
application/repository port, persistence adapter, thin route/schema, client and
UI, with pagination/filter/trust-boundary and real-database checks. Metadata must
preserve existing snapshot hashes, V1 readability and stored-only retrieval.
The current trusted service token does not establish per-buyer authorization.

## Proposed delivery slices

These are sizing proposals, not published issues or a finalized specification.
Accessibility, loading, error, focus and narrow-layout behaviour belong in each
slice; they are not deferred to the final polish pass.

| Slice | Buyer-visible acceptance example | Dependencies / traceability |
| --- | --- | --- |
| 1. Find saved cases and identify Practice | Find the intended original by recognizable labels; its scenarios and source/purpose remain clear without recalculation. Agree the bounded list/catalog contract and legacy handling first | Confirmed library/Practice scope; contract to specify; FR/AC-V2-09/10, NFR-V2-05/06/07; UX29-03 |
| 2. Workspace entry and responsive navigation | Enter normal work or a curated practice task, open a case, and reach Plans without developer instructions or a supplied UUID | 1 for full return journey; FR/AC-V2-09, NFR-V2-07; UX29-03/04/10 |
| 3. Understand creation and compare plans | Review attributed terms, create a case, explain exact quantities/cost/premium and select an alternative from its summary | 2; FR-V2-01/06/07/09, AC-V2-01/05/07/09; UX29-04/05/10 |
| 4. Test disruptions and finalize deliberately | Understand feasible/infeasible outcomes and original facts; approve a valid base once or record reasoned No-award, with purposeful keyboard focus | 3; FR/AC-V2-08/11, NFR-V2-06; UX29-05/06/07 |
| 5. Explain, recover and retrieve documents | Inspect supplier explanation/audit, recover the same uncertain intent, reopen approval and navigate/download its exact PDF | 3/4 for the integrated flow; FR/AC-V2-07/09/10/12, NFR-V2-05/06/07; UX29-08/09/10 |
| 6. Reassess and record acceptance | Owner and unfamiliar buyers perform the tasks; affected browser/integrity checks pass; open findings and evidence limits are recorded | 1–5; AC-V2-09/13, NFR-V2-04/08; all UX29 follow-ups |

## Quality and completion brief

- Coherent typography, spacing, numeric alignment, semantic status treatment and
  task hierarchy across entry, forms, comparisons and documents. Choose the visual
  direction with the user before implementation; do not equate modernity with extra
  cards, decorative charts, glass effects or animation.
- Persistent labels, visible focus, logical keyboard order and purposeful focus
  after completed actions; dialogs return focus safely. Alerts/status announcements
  survive the redesign. Essential information is never hover-only or color-only.
  Proposed target: WCAG 2.2 AA criteria relevant to these flows, with actual manual
  and automated evidence; component choice alone does not establish conformance.
- Inspect desktop, tablet, 390px and 320px layouts, actual browser text zoom at
  200%, reduced motion, long/missing names and exact numeric values, 3/5/10-supplier
  data and variable alternative counts. Keep physical-phone and screen-reader
  results separate from emulation/DOM evidence. Do not animate financial values or
  keyboard navigation; motion must explain state without delaying a task.
- Reuse and adapt the local real-stack Chromium smoke; cover the new return/Practice
  journey and deliberate choice, plus genuine backend/PDF downtime and exact retry.
  Retain meaningful snapshot, provenance, decision and download-integrity tests.
  Measure new list/filter behaviour separately; historical API p95 evidence does
  not establish new browser or query performance.
- Before participant sessions, define observable tasks: find/open without UUID;
  explain both source boundaries; compare exact allocations/premium; run feasible
  and infeasible scenarios; knowingly approve or decline; recover safely; reopen
  and download. Record completion, assistance, critical mistakes, human time and
  comprehension with 3–5 unfamiliar participants where available. Do not invent
  numerical success thresholds after observing outcomes.
- Separate technical completion, user visual approval and novice usability evidence.
  Participant absence remains NOT ASSESSED and cannot become validated experience
  or final acceptance. The technical/user review and participant evidence gates
  were approved with the ticket breakdown on 2026-10-12; missing participant
  evidence remains NOT ASSESSED and cannot establish final buyer acceptance.

## Next implementation step and discovery limits

The user confirmed the full brief and authorized specification work. The
[local specification](UX_UI_INCREMENT_SPEC.md) now resolves the bounded library,
Practice classification, compatibility, recovery and reassessment contracts.
The user approved ten tickets, their dependencies, a new parent and the prospective
query/usability gates. Publication/readback is complete for parent #42 and #32–#41.
Begin with [#32 — find and reopen saved procurement cases](https://github.com/SafarErik/odoo-procurement-decision-support/issues/32).
The [ticket index](UX_UI_TICKET_BREAKDOWN.md) records actual blocking links and
verification. Keep the substantial increment ahead of T19 without renumbering it.

No production frontend implementation, application runtime stack start, new buyer
walkthrough, benchmark rerun, test-suite run, GitHub mutation or Drive write was
performed for this discovery. A localhost-only design selection helper and static
planning sketches were prepared and browser-inspected. Current code, retained
reports, live primary sources, component exports and exact-SHA CI were checked.
This proposal preserves API-only
Reflex, offline synthetic ML, exact saved values, original-base scenarios and
immutable decisions/PDF. Arbitrary Odoo discovery, observed-model promotion,
production IAM, ERP writes, multi-product planning and global infrastructure remain
outside it. Thesis relevance: chapters 4/6 explain the UI/integration decisions;
chapter 7 owns reassessment evidence and its limits.
