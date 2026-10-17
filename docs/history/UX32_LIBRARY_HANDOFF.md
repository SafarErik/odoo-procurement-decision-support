# Saved-case library — #32 handoff

Local implementation and evidence, 2026-10-12. Scope:
[#32](https://github.com/SafarErik/odoo-procurement-decision-support/issues/32),
parent [#42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42),
[approved specification](UX_UI_INCREMENT_SPEC.md) and
[delivery contract](UX_UI_TICKET_BREAKDOWN.md). Changes are uncommitted;
commit/push/merge, new-SHA hosted CI and owner migration remain user-controlled.

## Problem → decision → behavior

A returning buyer needed a UUID/runbook to find saved work, while evaluation
history could be mistaken for normal controlled work. Add bounded stored discovery
through the existing application/repository boundaries, and a functioning history
entry at `/cases`; retain the existing RFQ/cockpit entries and source authority.

- Trusted collection routes use only backend `PLANNING_LIBRARY_COMPANY_ID`; missing
  scope fails unavailable. Workspace/status/product/ID filters, literal search,
  20-row default/50-row maximum and filter/company-bound keyset continuation keep
  database reads and Reflex state bounded. No total-count scan or per-row child call.
- Rows lead with recorded product identity, demand/unit/currency/date, company,
  save time, planning outcome and human-decision status. No invented business names.
  Show scenarios lazily retrieves grouped children, with saved assumptions/outcome.
  Open case/scenario retrieves the selected result via a compatible bookmark URL.
  Bad IDs/views remove previous results; loading, empty/no-match and unavailable
  responses remain distinct. Keyboard/native controls and narrow reflow are retained.
- An additive empty immutable catalog stores classification separately from hashed
  evidence. Old cases remain **unclassified**, explicitly available through Earlier
  cases. Catalog insertion requires an original base; children inherit its workspace.
  Creation fingerprints, snapshots, V1 history, final decisions and PDF bytes are
  unchanged. Classification-aware creation/curated Practice is #33, not this slice.
- Selected page rows reuse stored snapshot/decision validation. Unsupported/corrupt
  data fails explicitly instead of fabricating/skipping summaries. Supported older
  synthetic snapshots omit `input_kind`; their existing synthetic source tag identifies
  source evidence without assigning Practice. No source acquisition, training,
  inference or optimization occurs during collection/reopening.
- Pending navigation retains exact request/key and returns to the original recovery
  route. That route does not repeatedly redirect to itself. The recovery contract is
  still session-local; #34 owns broader dirty-draft/shell navigation work.

This implements UX-AC-01/03 and supports FR/AC-V2-09/10 and
NFR-V2-04/05/06/07/08, addressing UX29-03. The official task's Python web UI and
systematic stored workflow remain the same; no ADR/framework/core change is claimed.

## Verification and retained evidence

- Required fast suite: **605 passed**, 61 integration/E2E tests deselected.
  `.artifacts/ux32-fast2/result.xml`. Actual ML training/artifact reload and bundled
  CBC execution ran; no runtime-dependency skip. Final route-guard/recovery focused
  check: **20 passed**, `.artifacts/ux32-final-focus/result.xml`.
- Format/lint, compileall, pip dependency consistency and Odoo Compose configuration
  passed. Compose configuration verification started no Odoo service. The mechanical
  UI detector returned no findings; it does not prove human usability.
- Real PostgreSQL integration: **32 passed**, including migration downgrade/upgrade,
  V1 readability, V2 immutable storage/decisions, empty catalog, base-only insertion,
  UPDATE/DELETE rejection, inherited child classification and unchanged snapshot hash.
  `.artifacts/t18-browser-877c9a6416ec/result.xml` and its `evidence.json` retain PASS
  and verified owned-service cleanup.
- New real Reflex → FastAPI → PostgreSQL library acceptance: **1 passed**,
  `.artifacts/ux32-browser6/result.xml`, run
  `.artifacts/t18-browser-f25fcfec32d1/`. It covers ordering including timestamp ties,
  concurrent insertion/continuation stability, filters, escaped SQL text, scope,
  cursor/container failures, real corrupt-row rejection, stored-only find → expand →
  keyboard reopen/reload, invalid opening and real backend outage/explicit recovery.
  Odoo configuration and model directory were cleared for stored reads. Library
  viewport assertions passed at 768/390/320; screenshot/trace artifacts are retained.
- Existing approval/PDF/uncertain-create browser regression: **1 passed**,
  `.artifacts/ux32-regression/result.xml`, run `.artifacts/t18-browser-54502588a6b0/`.
  It retains exact approved PDF download, saved approval and identical idempotent retry.
  The final pending-navigation extension also passed at
  `.artifacts/ux32-nav/result.xml`, run `.artifacts/t18-browser-e03b38630237/`:
  attempted Cases/another-bookmark navigation returned to the original recovery
  route, retained the exact payload/key, then succeeded through explicit replay.
  Both owned stacks report verified cleanup.
- Built-in browser inspection exercised Earlier cases and reviewed desktop and
  390/320 history layouts against the selected palette. Automated screenshot evidence
  remains in the successful library root. This is agent inspection, not buyer feedback.

### Approved disposable library performance gate

[Raw measurements and PostgreSQL plans](UX32_LIBRARY_MEASUREMENTS.json) retain all
192 HTTP observations: six selected 20-row queries × two warm-ups + 30 measurements.
The owned workload has 1,000 company-scoped original bases, 60 children and a separate
cross-company original; one new company base is inserted after the first page to
check concurrent arrivals. Rows replicate valid saved snapshots, not new business
or ML observations. p95 is nearest-rank observation 29 of the 30 measured values.

| Query | Local p95 seconds |
| --- | ---: |
| First original page | 0.171 |
| Continued original page | 0.170 |
| Product-filtered original page | 0.244 |
| Awaiting-decision original page | 0.201 |
| First child page | 0.190 |
| Continued child page | 0.184 |

All six passed the approved **p95 ≤1 second** gate. The retained plans measure the
existing snapshot/company/time/parent fields with no additional snapshot indexes;
the catalog's workspace lookup index is the only new index. Bounded page validation
reads full snapshots internally, at most limit+1, to preserve integrity; list HTTP
responses contain compact summaries. The small controlled history meets the target;
larger/heterogeneous history requires new measurement before proposing indexes.
This is a local PoC observation, not a production SLA.

### Failed attempts remain recorded

The first browser attempt stopped before stack setup because Podman was off.
Initial focused invocations hit Windows temp ACL/missing-parent errors; subsequent
runs use fresh workspace-local directories. Real acceptance found and fixed missing
legacy `input_kind`, a filter remount problem and a controlled-field update race.
An intermediate compile exposed unavailable autogenerated setters in installed
Reflex; explicit form handling resolved it. Full-suite collection also found duplicate
test basenames; the E2E module now has a distinct name. These failed runs remain at
`.artifacts/ux32-first`, `ux32-focus*`, `ux32-browser2`–`ux32-browser5`, `ux32-fast` and
their printed `t18-browser-*` roots. They are not PASS; intermediate raw timings and
logs remain alongside final measurements. Disposable projects/processes were removed.

## Limits, user action and next capability

Use [the runbook](UX32_LIBRARY_RUNBOOK.md): migrate the intended helper to
`20261012_01`, configure its exact library company and restart FastAPI/Reflex. The
owner database was not migrated/reset and Odoo/Drive were not mutated. The shared
service-token/company context is not production per-buyer IAM; get-by-ID retains
its earlier authorization contract. Classification is presentation metadata, not
quantity/approval/document authority. Concurrent finalization can alter membership
in decision-status filters; continuation order remains save-time/ID based.

Unfamiliar-buyer/owner assessment, real browser 200% text zoom, screen-reader speech,
physical phones, broader shell accessibility and hosted/new-SHA CI remain unverified.
They are not inferred from DOM/screenshot/functional PASS. Live Odoo checks were not
needed for stored-only discovery. New Practice/controlled creation classification,
curated examples and the complete workspace redesign are still pending (#33–#41).
Next product capability is **#33: enter curated Practice and preserve classification**.

Chapters 4/6 can explain the bounded API/storage/UI decision and immutable boundaries;
chapter 7 can use the measured gate and functional evidence with their stated limits.
Final thesis/buyer-experience acceptance remains separate.
