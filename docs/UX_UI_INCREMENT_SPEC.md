# Find, compare and decide — buyer workspace specification

Prepared 2026-10-12 from the [confirmed brief](UX_UI_INCREMENT_PLAN.md).
Status: **APPROVED AND PUBLISHED — [specification #42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42); implementation remains pending**.
The user confirmed curated Practice without resets, a bounded saved-case library,
the existing English/Reflex/read-only workflow and **Decision editorial**. The user
then confirmed the full brief and authorized specification work. T19 remains thesis
closure after this development and reassessment; no new T-number is assigned here.

The [approved ticket breakdown](UX_UI_TICKET_BREAKDOWN.md) refines the six delivery
areas into ten complete buyer tasks. On 2026-10-12 the user approved all ten tickets,
their dependencies, a new specification parent and the bounded validation gates.
These are prospective acceptance contracts, not measured results. Publication and
readback are complete for parent #42 and delivery tickets #32–#41; #32 is the first
unblocked capability. The ticket index records the authoritative delivery graph.

## Problem Statement

The controlled procurement chain works, but a buyer unfamiliar with the app needs
developer knowledge to start or reopen a case. Setup/evidence copy obscures results,
especially on phones. A label-only decision selector is distant from the comparison;
keyboard focus can be lost after saving, and an infeasible scenario hides original
facts. Recovery and document access are safe but technical. Many generated test
cases make an indiscriminate history browser unsuitable as the normal workspace.

[T18's buyer assessment](T18_29_BUYER_ASSESSMENT.md) records these observations as
UX29-03–10. [The controlled report](T18_CONTROLLED_ASSESSMENT.md) establishes
functional evidence with modern UX still open and unfamiliar-buyer usability
NOT ASSESSED. A new look alone would not resolve these problems.

## Solution

Deliver a coherent workspace where a buyer finds recognizable saved work, reviews
attributed inputs, compares exact supplier allocations/cost/exposure, tests a
disruption and deliberately records approval or No-award. Curated Practice provides
a clearly labelled way to learn the same real workflow. Use the selected editorial
comparison layout and responsive navigation throughout, with useful error/recovery
states and an approved document that is easy to reopen and download.

Keep the current Decision Tree/MILP, API-only Reflex, read-only Odoo, original-base
scenarios and immutable decision/PDF contracts. Extend only the bounded discovery
and case-classification seams needed for this workflow. Reassess tasks with the
owner and unfamiliar buyers; preserve pending or failed evidence explicitly.

## User Stories

1. As a first-time buyer, I want a clear starting action, so that I do not need a developer runbook.
2. As a returning buyer, I want recognizable product, demand, date and status labels, so that I can find saved work without retaining a UUID.
3. As a buyer, I want bounded filtering and paging, so that a long history remains usable.
4. As a buyer, I want original cases and their scenarios grouped, so that I know which decision a disruption belongs to.
5. As a buyer, I want an explicit Practice entry, so that I can learn with curated examples.
6. As a buyer, I want Practice and its persistence limits visible, so that I do not confuse an example with isolated or operational work.
7. As a buyer, I want older unclassified cases labelled honestly, so that missing metadata does not become an invented provenance claim.
8. As a buyer, I want the existing Open RFQs ledger available, so that the redesign preserves read-only quotation visibility.
9. As a buyer, I want captured quotations distinguished from explicit terms and synthetic assessments, so that I understand each input's authority.
10. As a buyer, I want labelled creation stages and field errors, so that I can review a comparison before calculating and saving.
11. As a buyer, I want the product, quantity, unit, currency, dates and lineage near the result, so that I do not interpret it in the wrong context.
12. As a buyer, I want aligned allocations, exact cost/premium and explained exposure, so that I can compare alternatives accurately.
13. As a buyer, I want a visible selected plan and review summary, so that I know what I am considering before approval.
14. As a buyer, I want honest single-plan/no-alternative and solver outcomes, so that missing options are not presented as a broken screen.
15. As a buyer, I want all five supported disruptions and a draft summary, so that I can test explicit assumptions.
16. As a buyer, I want original facts beside infeasible scenarios, so that a failed scenario does not erase the baseline.
17. As a buyer, I want demand-change and simulated-price caveats at comparison, so that I do not infer savings or fresh quotations incorrectly.
18. As a buyer, I want readable supplier explanations with exact audit detail available, so that I can question the assessment.
19. As a buyer, I want deliberate approval with exact chosen terms and a reason where required, so that selection alone never finalizes a case.
20. As a buyer, I want a separate reasoned No-award action, so that declining cannot be mistaken for approving a plan.
21. As a buyer, I want saved decision state to stay immutable, so that reopening does not change what I approved.
22. As a buyer, I want clear uncertain-save recovery, so that I resend the original intent rather than accidentally creating another decision.
23. As a buyer, I want draft/context changes guarded, so that navigation does not silently discard work or a pending request.
24. As a buyer, I want approval to survive document failures, so that retrying PDF access does not require approving again.
25. As a buyer, I want an approved summary, page navigation and exact artifact download, so that I can use the document confidently.
26. As a keyboard or narrow-screen user, I want logical navigation, focus, reflow and feedback, so that every essential task remains usable.
27. As a buyer using zoom or assistive technology, I want accessible labels and status/error semantics, so that state changes remain understandable.
28. As a project evaluator, I want real browser/API/database evidence, so that visual polish does not hide broken contracts.
29. As a project owner, I want small complete delivery slices, so that each capability is demonstrable and reviewable.
30. As a thesis author, I want human observations and technical results distinguished, so that usability and operational validity are not overstated.

## Implementation Decisions

### Selected design and navigation

- Preserve **Decision editorial**: deep-green navigation rail, soft mint ground,
  purple selection, opaque data surfaces, precise sans typography and tabular
  numbers. The full-width aligned plan comparison is the focal element; a
  persistent review strip summarizes the explicit selection. Keep familiar controls.
  Initial reference colours are rail `#153f40`, ground `#eff5f1`, ink `#173e3d`,
  selection `#413b76`, selected surface `#f1eff8`, muted `#536964`. Verify all actual
  text/state/focus contrast before use; state colours remain semantically distinct.
- The selected static sketch fixes desktop arrangement and direction, not a 1440px
  production width, fixed height, complete content or responsive behaviour. Exact
  data missing from the sketch must appear from saved backend results in the app.
- Global destinations are **Cases / Open RFQs / Practice**. Cases is the landing
  destination with New comparison, meaningful history and secondary open/copy UUID.
  Retain the RFQ ledger and existing `/` entry; `/planning` remains a compatible
  entry. Do not imply arbitrary RFQ-to-planning conversion.
- Keep the four case views **Plans / What-if / Suppliers / Audit**. Add useful
  bookmarkable stored-case navigation; a case ID and allowed view in the URL are
  navigation input only. Opening/reloading fetches saved state, never creates or
  recomputes a case. Invalid IDs/views fail safely without showing the previous case.
- On phones/tablets where a rail crowds the task, use a labelled Drawer. The case
  header and outcome precede help/setup. Reflow comparison into labelled plan sections
  retaining matching metrics; allow scoped exact-table scrolling, not whole-page
  horizontal overflow. The review strip must not hide content, fields or focus.

### Bounded saved-case discovery contract

- Add a trusted-caller-protected `GET /api/v2/procurement/planning-cases` collection
  endpoint. Require an owner-configured library company context on the backend;
  missing context fails unavailable rather than exposing every company's cases.
  Do not infer scope from a browser input or a loaded model. Stored browsing must
  work with Odoo/model/solver unavailable. Existing get-by-ID behaviour is preserved;
  library scope is not a new per-buyer authorization system.
- Queries accept `workspace=controlled|practice|unclassified`,
  `status=all|draft|approved|no_award`, optional trimmed product/case-ID text `q`
  (maximum 80 characters), `limit` (default 20, range 1–50) and a bounded continuation
  cursor. Reject unknown/invalid values. Parameterize database queries. Search
  recorded product identity and case ID; do not promise arbitrary supplier/full-text
  discovery or invent business names missing from snapshots.
- Return original-base summaries ordered by saved UTC time descending, then case
  ID descending. Use stable keyset continuation tied to the filters/company and
  reject mismatched/malformed cursors. Concurrent new cases appear on refresh rather
  than changing the continuation boundary. No total-count scan is required.
- Each summary supplies case ID, saved timestamp, company, product identity/display
  fallback, Q/unit/currency, required date, planning status, decision status, source
  kind and workspace classification. Monetary/fraction values retain existing exact
  serialization where included; do not send full snapshots, history or model blobs
  for every list row. Product/date/context labels lead; UUID is secondary.
- Add a bounded stored-child collection for an original base, with the same paging
  limits/order/company scope. Summaries include scenario kind, changed assumptions
  and outcome. Expand children on demand; never issue one request per list row.
  Reject a child used as an original-base container. Keep children grouped under the
  correct base; list filters describe base decisions, not invented child approvals.
- Collection reads use the existing application/repository/persistence boundaries.
  Summaries are validated against the supported stored contract; corruption produces
  explicit unavailable/invalid-data feedback, not fabricated or silently skipped
  results. Metadata is not authority for quantities, approval or document content.

### Practice classification and compatibility

- Store a small immutable case-catalog record separately from the hashed planning
  snapshot. It holds the original case ID, explicit workspace kind and optional
  curated example ID. It is a presentation/purpose fact, not business evidence or
  access control. Do not rewrite existing snapshot hashes, decisions or documents.
- Extend base creation with an optional catalog context. New Reflex Practice
  requests use `practice`; the prepared Odoo flow uses `controlled`. Validate
  the context server-side: Practice is accepted only for the fully synthetic base
  path, controlled only for the existing Odoo quotation path; example IDs must be
  in the prepared application catalogue. Neither a selected model nor a claimed
  browser source can change those rules. Keep preparation offline and trusted.
- Commit classification atomically with a new case. A classification-bearing intent
  includes its context in the creation fingerprint; changing it under the same key
  conflicts. Requests omitting context preserve their current fingerprint/replay
  contract. Exact replay never repairs/reclassifies an old case or adds metadata.
- Scenarios inherit the original base's classification; no child-controlled
  workspace override. Old cases with no catalogue record are **unclassified** even
  when their source kind is known. They remain reachable through an Earlier cases
  filter and compatible UUID retrieval, with explicit captured-Odoo/synthetic source
  labels. Do not auto-promote old evaluation cases into buyer work or curated Practice.
- The additive migration creates catalogue storage and necessary lookup indexes;
  no destructive reset or compulsory bulk relabelling/backfill. Query existing
  company/time fields from stored facts and use bounded reads. Measure query plans
  on a disposable representative history before adding further indexes; do not
  load the entire history into Python or Reflex state to filter it.
- Metadata-aware get/list responses expose classification outside the immutable
  snapshot. Keep legacy response fields and old readers compatible; missing metadata
  always means unclassified. V1 history/readability remains supported and is not
  silently merged with the V2 library.
- Practice entry offers three curated starting tasks: compare plans, test an outage,
  and make a case infeasible. Use the existing prepared synthetic base and supported
  scenario operations; do not add a new ML pipeline or fake solved outputs. Entering
  Practice/choosing a task performs no POST. Explicit calculate/save actions persist
  real examples; saving/finalizing remains deliberate. Never reuse a finalized shared
  example as a fresh editable exercise. Show stored-example versus new-run semantics.
- Practice remains visible on its case, approval review and document-access page.
  Existing immutable PDF bytes are not relabelled or watermarked by the frontend;
  their source/provenance remains intact. Do not promise a separate database, reset,
  automatic cleanup, production environment or operational validity. Saved examples
  persist in application storage; only owner-controlled disposable tests reset data.

### Creation, comparison and decision

- Reuse current prepared synthetic/Odoo requests. Guide creation through facts,
  explicit business terms and review/calculate; retain field validation, quantities,
  dates, MOQ absence, price/delivery applicability and policy. Captured Odoo preview
  time is distinct from the reread performed by FastAPI during new creation.
- Plans lead with exact allocations, total cost, absolute/relative premium and
  explained exposure. Display exclusions, binding constraints and delivery terms
  intelligibly. Keep the existing chart subordinate with an exact table equivalent.
  Exposure is an uncalibrated synthetic proxy, not failure probability.
- Plan selection is explicit (no automatic preselected approval). The selected
  summary mirrors the exact saved plan identity, allocations, context and costs.
  Review decision opens a deliberate confirmation with actor attribution and reason.
  Cancel is read-only. Alternative and No-award retain required reasons; No-award
  has a separate action and no approved-plan PDF. Use the existing finalization API.
- Disable duplicate submission while saving. Once finalized, show the immutable
  choice/time/reason and document eligibility; do not leave an editable approval
  control. Scenario children offer Return to original base, never child approval.
- What-if retains all five types and original-base targeting. Show original facts,
  draft changes and saved child results together. If infeasible, preserve the
  original cost/allocation and explain unavailable child metrics; no zero/default
  plan. Changed-demand totals are not like-for-like savings. Simulated prices are
  not fresh quotations. Never relax backend constraints to make an example work.
- Suppliers lead with readable saved classes/constraints and sample/reference-time
  interpretation. Audit retains exact inputs, tree paths, model/policy/solver
  versions, provenance and lineage. Developer testing instructions move to
  contextual Practice/help/runbooks; concise evidence limits stay visible.

### State, navigation, recovery and approved document

- Distinguish empty history, no filter matches, loading, validation rejection,
  infeasible/partial solver outcome, unavailable service, decision conflict,
  uncertain save and document failure. Loading does not create fake result numbers.
  Keep usable previous context only when its identity is clearly labelled; failed
  case opening must not present a previous case as the requested one.
- Explicit UI navigation checks dirty creation/scenario drafts and offers Stay or
  Discard draft. A pending write has no discard/context-switch escape: preserve the
  original URL, payload and key, show buyer-oriented recovery and explicit resend.
  Guard route-change handlers so they cannot clear pending intent before loading a
  different case. Keep technical request evidence available for recovery/support.
- No automatic POST retry, replacement key or optimistic “not saved” claim after
  uncertainty. The exact-request recovery contract is unchanged. No durable
  cross-session/outbox system is added: a closed/lost Reflex session or server
  restart cannot be advertised as retaining an unsaved intent. Provide recoverable
  support evidence before risky navigation; document this limit and verify actual
  behaviour rather than promising safe tab closure or global multi-tab coordination.
- After create/scenario/finalization removes its initiating control, move focus
  purposefully to the resulting heading/status or next action; avoid focus stealing
  during unrelated updates. Dialogs have labelled title/description, appropriate
  focus containment, Escape/cancel and safe focus return. Preserve alert/status roles.
- Documents show the saved approved allocation/date/cost summary, page indicator,
  labelled previous/next, zoom/fit and download. Reuse backend-rendered immutable
  content and the existing PDF viewer. No legal-order or Odoo-write claim. A PDF
  failure keeps approval visible and retries document access only. No-award,
  unapproved bases and children retain their current ineligibility.

### Architecture and implementation boundaries

Reuse frontend composition, shared theme and the existing state/input/scenario/
result/audit/decision/PDF modules and HTTP clients. Extend the application/repository
query interface and thin API schema/route for bounded discovery; add only the
classification storage and creation context necessary for Practice. Keep the
Decision Core, MILP, ML training/artifact trust, Odoo reader and PDF renderer
unchanged. The shared bearer token stays on the Reflex server. No frontend
database feature or arbitrary artifact/file selector is introduced.

Reflex 0.9.12 is the verified installed baseline. Reuse Drawer, Tabs, Radio Group,
Alert Dialog, layout primitives, Skeleton, Table and Callout as appropriate. Prove
their installed props and event/focus behaviour during implementation; component
export availability is not accessible behaviour. No framework upgrade is assumed.

## Testing Decisions

Use external behaviour at the existing HTTP and real-stack Chromium seams. Extend
current trust/idempotency/persistence tests only for the new catalog/query contracts;
do not mirror component structure in tests or rerun unrelated timed workloads.
Database-reset/browser tests use owned disposable helper PostgreSQL, never owner
or Odoo storage. The real Odoo check stays separate from synthetic browser tasks.

| Verification | Required outcome / evidence |
| --- | --- |
| Library API | Validate auth/company/query/cursor bounds; stable filtered base/child pages; corruption/unavailability errors; source/workspace distinction; no upstream read/inference/solve. Invalid input/cursors and cross-company summaries are never accepted |
| Catalog and real PostgreSQL | Atomic case+classification, replay without metadata writes, changed context/key conflict, inherited child context, legacy retrieval, migration compatibility, unchanged snapshot/decision/document hashes; retain contention/rollback coverage |
| Buyer browser flow | Curated Practice entry → create → compare exact quantities/premium → scenario → explicit alternative approval → library reopen → rendered PDF and byte-identical download. Include separate No-award and unavailable-backend/uncertain exact retry |
| Draft and route behaviour | Explicit navigation cancellation/discard; pending save cannot be replaced by route/view/Practice change; invalid/missing case safe; duplicate click guarded; focus and feedback after create/scenario/finalize/reopen |
| Content and visual review | Compare to chosen reference on desktop; inspect 1280/1440 desktop, 768 tablet, 390 and 320 widths; 3/5/10 suppliers, 1–3 epsilon requests with variable distinct alternatives, long/non-Latin/missing labels and exact monetary/fraction values |
| Accessibility | Keyboard flow, labels, error/status feedback, actual browser text zoom 200%, reflow at 320 CSS pixels, contrast, non-colour state, focus visibility/not obscured, dialog focus/return, target sizing and reduced motion. Record screen-reader speech and physical phone tests separately |
| New list performance | Disposable history with 1,000 bases plus children; 20-row filtered base and expanded-child pages: two warm-ups and 30 timings per selected query, observed local p95 ≤1s. Record failures, versions, rows and query plans; PoC target, not production SLA |
| Final gates | Focused checks per slice; required fast gates once before handoff, frontend compilation and affected real-stack checks. Quality remains required; no hosted browser job/dependency expansion by default |

The accessibility target is the relevant A/AA criteria of
[WCAG 2.2](https://www.w3.org/TR/WCAG22/): text/non-text contrast, resize/reflow,
keyboard access, meaningful focus order/visibility, focus not obscured, labels,
error identification, status messages and target size. Record criterion-specific
evidence and exceptions; no whole-app conformance claim follows from component
names or automated checks alone. PDF zoom is not browser text zoom.

### Buyer reassessment protocol and completion

Reuse the buyer task run sheet. Record owner walkthrough and 3–5 unfamiliar
participants separately from a source-informed agent. Before sessions, freeze
the fixtures/instructions and these tasks: enter Practice and explain persistence/
sources; find/reopen without UUID; explain allocations/premium/exposure; run feasible
and infeasible disruptions; knowingly approve an alternative or record No-award;
recover a simulated service failure; reopen the decision and download its document.
Use separate cases for irreversible approval and No-award.

For each participant/task record independent completion, assistance, mistakes,
human time, comprehension and comments. Approved scoped usability gate: at least
80% independent completion per essential task with n≥3 (round required successes
up), and zero unintended finalizations or unresolved critical source/decision
misunderstandings. This is a small qualitative PoC acceptance rule, not population
statistics or a time SLA. Document instructed fault setup separately from help
solving the task. Fix critical findings and repeat affected tasks; retain failures.

Technical delivery can be reviewed separately, but pending participants remain
**NOT ASSESSED**, pending owner/text-zoom/assistive checks retain their named gate,
and final buyer-experience acceptance stays open. Never substitute agent/screenshot
approval for human evidence or silently soften the criteria after observing results.

## Acceptance Criteria and Delivery Slices

The local UX-AC identifiers below organize verification; they do not replace or
renumber the canonical V2 requirements. All criteria describe future behaviour.

| Slice / dependency | Acceptance | Canonical traceability and finding |
| --- | --- | --- |
| 1. Stored discovery and classification / none | UX-AC-01: scoped bounded base/child listing and meaningful filters; UX-AC-02: atomic validated Practice/controlled metadata and unchanged old replay/hash; UX-AC-03: truthful unclassified legacy access without mass relabelling | FR/AC-V2-09/10; NFR-V2-05/06/07; UX29-03 |
| 2. Entry and navigation / 1 | UX-AC-04: recognizable Cases entry and same-context reopening without UUID; UX-AC-05: curated Practice enters without writing, persists only on explicit action and carries labels; UX-AC-06: chosen shell/case navigation and responsive hierarchy, compatible RFQ/old entries | FR/AC-V2-09/10; NFR-V2-07; UX29-03/04/10 |
| 3. Creation and comparison / 2 | UX-AC-07: attributed facts/terms/review and genuine API save; UX-AC-08: exact aligned comparison, no implicit selection/approval, selected review strip; UX-AC-09: honest single/no-distinct/solver states and chart/table equivalence | FR-V2-01/06/07/09; AC-V2-01/05/07/09; UX29-04/05/10 |
| 4. Scenarios and decision / 3 | UX-AC-10: all five draft/saved original-base scenarios with retained infeasible base facts and demand/price semantics; UX-AC-11: explicit base approval/reason or separate No-award, immutable/replay-safe outcomes and child ineligibility | FR/AC-V2-08/11; NFR-V2-06; UX29-05/06/07 |
| 5. Explanation, recovery and documents / 3/4 for integrated flow | UX-AC-12: readable Suppliers/Audit with exact evidence; UX-AC-13: distinct fault/conflict/pending states, guarded navigation and exact explicit recovery; UX-AC-14: approved summary/page/zoom/download with preserved approval and exact artifact | FR/AC-V2-07/09/10/12; NFR-V2-05/06/07; UX29-06/08/09/10 |
| 6. Reassessment / 1–5 | UX-AC-15: selected direction, keyboard/narrow/zoom/reduced-motion and new query gates evidenced; UX-AC-16: owner/novice outcomes, fixes and unassessed limits recorded against canonical acceptance | AC-V2-09/13; NFR-V2-04/08; UX29-03–10 |

Focus, feedback, validation, narrow layout and meaningful tests are part of each
slice. The final slice consolidates evidence; it does not defer correctness or
accessibility work. Tickets should be vertical, demonstrable and name genuine
blocking edges rather than splitting frontend/backend/testing into isolated layers.

## Out of Scope

Database reset/isolated Practice infrastructure; automatic history cleanup;
arbitrary Odoo quotation discovery or writes; observed-model promotion; new ML or
solver behaviour; simultaneous multi-product planning; arbitrary supplier score/
artifact selection; manual allocation editing; production IAM/RBAC/deployment;
durable cross-session pending outbox or multi-tab coordination; a new PDF renderer/
watermark/layout contract; unrelated dashboards, dark-theme configuration or
animation infrastructure; commit/push/merge or Hungarian Drive changes. Ticket
publication was separately approved; it does not start implementation.

## Further Notes and Sources

- The approved visual reference is [Decision editorial](design/decision-editorial.html),
  a byte-identical repository copy of the selected local static sketch. Its controls
  are illustrative; do not treat its fixed dimensions or omitted values as product
  behaviour. Preserve it as the implementation/review reference. Captured SHA-256:
  `bf25f3bdacaf45c9614d96a49a418a1f841f65e9019ffc91e3901f62193c7a4e`.
- [Product context](../PRODUCT.md), [baseline and official-task traceability](agents/project-baseline.md),
  [buyer findings](T18_29_BUYER_ASSESSMENT.md) and [T18 controlled evidence](T18_CONTROLLED_ASSESSMENT.md)
  ground this specification. The living Drive 00/06/02/03 sources were refreshed
  during this same planning session; their older technical status is explicitly
  reconciled in the brief. Accepted definitions/ADR boundaries remain unchanged.
- [Reflex dynamic routing](https://reflex.dev/docs/pages/dynamic-routing/),
  [Drawer](https://reflex.dev/docs/library/overlay/drawer/),
  [Alert Dialog](https://reflex.dev/docs/library/overlay/alert-dialog/) and
  [responsive styling](https://reflex.dev/docs/styling/responsive/) support the
  proposed framework mechanisms. Prove them against the installed runtime rather
  than adopting unrelated database examples or upgrading by assumption.
- Pagination limits, server-owned library scope, additive metadata handling and
  performance/usability acceptance rules were approved with the ticket breakdown
  on 2026-10-12. They define future verification, not existing capabilities or a
  new canonical ADR.
- Chapters 4/6 explain UI/integration decisions; chapter 7 records task/query/browser
  evidence and limitations. Update only affected runbooks/status/handoffs during
  implementation. Drive remains Hungarian and requires explicit update authorization.
