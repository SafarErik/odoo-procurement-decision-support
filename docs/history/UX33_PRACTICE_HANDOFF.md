# Curated Practice and classification — #33 handoff

Local implementation/evidence, 2026-10-12, on top of #32 commit
`5f09e91aa20d3f62cf6f2ba7c6ec4c97391463a1`. This implements
[#33](https://github.com/SafarErik/odoo-procurement-decision-support/issues/33) under
parent [#42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42),
using the [approved specification](UX_UI_INCREMENT_SPEC.md) and
[ticket breakdown](UX_UI_TICKET_BREAKDOWN.md). Changes are uncommitted;
publication/new-SHA hosted CI and merge remain user-controlled.

## Problem → decision → implemented behavior

Synthetic evidence alone did not establish a case's purpose, and an unfamiliar
buyer lacked deliberate curated exercises. Use #32's existing catalog storage,
add explicit creation context outside planning facts, and expose three real tasks
through `/practice`. No new migration/dependency, core algorithm, model pipeline,
Odoo writer, PDF format or infrastructure is introduced.

- Entry/selection prepares only a fresh draft from the trusted offline synthetic
  input. Compare, supplier outage and infeasible-demand tasks create no POST until
  explicit calculation/save. Scenario preparation fills the existing What-if draft;
  a separate explicit scenario save uses the same validated original-base MILP.
- Every new Practice save creates its own genuine base. Choosing a task after a
  finalized run starts a fresh draft; stored runs remain explicitly stored. New
  compatible Demo saves are Practice without a curated ID unless chosen. Prepared
  Odoo UI creation explicitly uses controlled work; its ML history remains synthetic.
- Optional `catalog_context` is validated against the server-selected creation path.
  Practice is synthetic-only; controlled is Odoo-path-only, with no curated example.
  Unknown example IDs, nested Odoo context and scenario overrides are rejected.
  Neither claimed source labels nor model selection grants a different classification.
- Case and catalog insertion share one transaction. Context-bearing fingerprints
  include purpose; omitted/null context keeps the old intent hash. Changing/removing
  context under the same key conflicts. Replay reads, never repairs/reclassifies.
  Children inherit original metadata rather than persisting an override.
- Create/get/scenario/decision responses expose `workspace` and `example_id` outside
  the immutable snapshot. The frontend validates classification against submitted
  intent and shows workspace separately from source on case/history/decision/PDF
  access. Catalog corruption fails validation; missing metadata remains unclassified.
  Old snapshots, V1 records, decision content and rendered PDF bytes stay unchanged.
- Entry explains persistence/synthetic limits, uses labelled native actions and
  purposeful focus, and reflows at narrow widths. Pending intent/key remains exact;
  exercise/case changes cannot replace it. Recovery remains session-local.

Scope maps to UX-AC-02/03/05, FR/AC-V2-09/10, NFR-V2-05/06/07 and UX29-03/10.
The official task's Python UI/stored decision workflow and existing source authority
remain fixed. Presentation metadata is not business evidence or access control.

## Verification and retained evidence

| Gate | Result and evidence |
| --- | --- |
| Required fast suite | **617 passed**, 67 service/browser tests deselected; actual ML/artifact/CBC execution. `.artifacts/ux33-final-fast/result.xml` |
| Affected focused recovery/frontend/API checks | **59 passed**, `.artifacts/ux33-final-focus/result.xml`; new Practice path/context and prepared Odoo request validation included |
| Real PostgreSQL integration | **36 passed**, `.artifacts/t18-browser-ebee77830db1/result.xml` and `evidence.json`; owned project cleanup verified |
| New real Practice browser flow | **1 passed**, `.artifacts/ux33-browser-confirm/result.xml`; root `.artifacts/t18-browser-7c60fd3daec5/` retains logs, screenshots, trace, PDF and verified cleanup |
| Existing approval/PDF/navigation recovery browser regression | **1 passed**, second test in `.artifacts/ux33-final-browser/result.xml`; root `.artifacts/t18-browser-78a656d3f58d/` retains PASS and verified cleanup |
| Format/lint/compileall/dependency/Compose gates | Passed locally; Compose validation started no Odoo service |

PostgreSQL evidence covers rollback after catalog insertion/before commit,
post-commit ambiguity followed by exact replay, four concurrent callers creating
one case/catalog row, changed/omitted-context conflicts, inherited child retrieval,
empty/immutable base-only catalog, legacy snapshot-hash equality and V1 migration/
readability. The Odoo path/source restrictions use the existing controlled adapter
fixture over mocked Odoo HTTP, not a fresh live Odoo acceptance claim.

The real browser test checks database counts after all three entry choices (zero
writes), three distinct fresh classified bases, actual saved outage/infeasible
children, explicit alternative approval, stored-only Practice library reopening
after model configuration removal, rendered PDF and byte-identical download. It
then starts another fresh exercise after finalization, forces a genuine backend
outage, verifies classified pending JSON and blocked navigation, and explicitly
retries the original key/payload with an idempotent replay.

Entry layout assertions/screenshots cover 1280/1440/768/390/320, keyboard choice,
visible labels and no whole-page horizontal overflow. Built-in browser inspection
confirmed desktop entry/draft focus and 320-width DOM reflow, plus actual white-on-
purple navigation/action styles and 44px action heights. The first visual pass
found low-contrast default navigation styling; the confirmation used explicit
styles. The mechanical detector returned no findings. This is bounded agent/UI
evidence, not unfamiliar-buyer assessment or whole-app WCAG conformance.

### Corrections and failures retained

The first focused draft test lacked its prepared JSON file; corrected fixture
preparation passed. The first full suite passed 616 tests and failed one old exact-
recovery assertion that omitted the newly explicit catalog context; the corrected
assertion verifies that context remains in the retained payload. Final 617 passed.
A final browser attempt passed the existing regression but observed labels during
the new case's loading phase; the Practice test now waits for the requested saved
case identity/label, then passed. Failed roots/JUnit files remain alongside PASS:
`.artifacts/ux33-focus`, `.artifacts/ux33-fast`, `.artifacts/ux33-final-browser` and
their printed owned-service roots. The combined final-browser JUnit is therefore
one failed/one passed; the separate confirmation establishes Practice PASS.

Windows pytest cache-directory ACL warnings are retained; they did not skip tests
or fail business checks. Starlette's httpx deprecation warning remains unchanged.
An initial Reflex-only visual helper ended on stdin EOF; a bounded owned preview
replaced it. Preview timeout/disconnected error pages are not UI PASS evidence.
Owned preview services were cleaned up after actual inspection. A temporary expired
preview's error tab could not be explicitly closed because its browser error URL
was blocked by the browser tool; temporary tabs use automatic end-of-turn cleanup.

## Limits, owner action and next capability

Use [the runbook](UX33_PRACTICE_RUNBOOK.md). The existing #32 migration/company/token
setup is still required; #33 has no additional migration. Prepare the matching
synthetic model/input offline, restart FastAPI/Reflex with this source, and open
`/practice`. Stored reopen requires neither Odoo nor model configuration. Library
company remains owner-selected: the existing synthetic example's company is
`synthetic-company`, distinct from an Odoo company's context unless prepared otherwise.

No owner/application/Odoo database was reset or migrated; Odoo and Drive were not
mutated. Live Odoo, hosted/new-SHA CI, owner/novice usability, real browser 200% text
zoom, screen-reader speech and physical phones were not verified here. No new list
latency benchmark was run: #32's unchanged bounded query design retains its dated
evidence; metadata-path correctness was checked through HTTP/PostgreSQL/browser.
Practice is persistent application data, with no isolation/reset/automatic cleanup,
observed-model promotion or current operational-validity claim. Actor attribution
remains audit text. PDF bytes/source claims are not changed by workspace labels.

Next capability is **#34: responsive Decision editorial workspace navigation**,
including wider dirty-draft guards and coherent global/case navigation. The later
creation/comparison/scenario/decision/explanation/document redesign and buyer
reassessment remain open. Chapters 4/6 can explain the catalog transaction and
deliberate UI; chapter 7 can use the scoped compatibility/fault/browser evidence.
