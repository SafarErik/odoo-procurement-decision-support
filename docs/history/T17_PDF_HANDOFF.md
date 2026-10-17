# Approved PDF viewing and download — 2026-10-10

## Result and scope

Issue [#21](https://github.com/SafarErik/odoo-procurement-decision-support/issues/21)
is implemented on `feature/T17-implementation`, starting from committed #20
at `294b312`. The user reports prior CI looks fine; this session does not treat
that as CI for the new PDF changes. New work remains uncommitted/unpublished,
with GitHub issues open and commit/publication/merge under user control.

The buyer views the backend-generated PDF for an approved original base and
downloads the exact saved artifact. Rendering/retrieval failure leaves approval
visible; explicit retry targets the same immutable approved content. No-award,
unapproved bases and stress children are denied approved procurement PDFs.
This supplies local FR-V2-09/10/12 and AC-V2-12 evidence, with AC-V2-10/11 and
V1/V2 regressions. #22/AC-V2-13 complete controlled demonstration remains open.

The official task and accepted ADRs are preserved. A read-only refresh of
ADR-006/007 confirmed helper-database artifact references, API-only frontend
access and a server-only token. Drive was not edited. The
[closed renderer/storage spike](T17_PDF_SPIKE.md) explains the engineering choice.

## Implemented behavior

- `application/planning_documents.py` validates saved case/approval/content
  identity and atomically stores/returns one immutable artifact. Acquisition,
  ML training/loading/inference and solver execution remain outside document operations.
- `document_adapter/approved_pdf.py` uses ReportLab 4.4.10 and packaged DejaVu Sans
  to paginate escaped saved text, exact allocations/prices/cost/currency, terms,
  source/model/policy references and human audit. Rational exposure stays exact;
  synthetic proxy, saved simulation dates, current UTC approval time and incomplete
  comparison are explicit. No supplier legal/address/tax fields are invented.
- Migration `20261010_01` adds `planning_documents`, linked to the final decision.
  Store stable `t17-approved-pdf-v1:{case_id}:{approved_content_hash}`, content
  version/hash, renderer/font/layout version, binary SHA-256 and PDF bytes.
  Exact-approval insertion, unique case/reference, 2 MiB bound and UPDATE/DELETE
  protection leave original planning/final-decision records unchanged.
- The existing trusted API serves inline/attachment PDF responses with safe
  filenames, identity/hash headers and private/no-store/nosniff. Failed rendering
  or post-flush storage rollback leaves no partial artifact. Retry can generate
  the same content version; stored retrieval does not execute the renderer.
- Reflex checks authenticated bounded bytes on its server, then uses React-PDF
  10.2.0 with a locally bundled PDF.js worker to display them. Pages have a
  selectable text layer, responsive fit-width/zoom and keyboard scrolling. A native
  Blob link downloads the exact bytes; Blob URLs are revoked on unmount. No token,
  public document file, CDN document/worker request or frontend generation is used.

The new runtime Python dependency is ReportLab; pypdf is development-only.
The React viewer is necessary because native iframe previews stayed empty in the
built-in browser. Frontend locks retain its resolved dependencies and the current
Reflex-generated package requirements. No backend/core technology choice changed.

## Verification and artifacts

Final fast/quality/export counts are in the dated
[implementation log](IMPLEMENTATION_LOG.md). Focused PDF/hybrid tests compare
extracted required content against the exact saved approval, reject invalid
identities/content/eligibility, exercise size/MIME/hash/reference bounds, and
preserve approval across renderer/storage/retrieval failure. The hybrid fixture
uses a mocked read-only Odoo adapter only at creation, then forbidden acquisition,
model/training/solver dependencies for approval/PDF. It produces the saved USD
2,200 alternative and both Odoo/synthetic provenance, without a fresh live-Odoo claim.

Real PostgreSQL: **5 PDF tests passed** (20.83 s), plus **31 V1/planning/approval
regressions passed** (53.75 s). Two document requests genuinely wait on a held
advisory lock before release: one render and one stored row, with identical
responses. Direct UPDATE/DELETE, wrong approved-content insertion and post-flush
rollback are tested. User/Odoo/application databases were not reset.

Built-in browser -> real Reflex/FastAPI/PostgreSQL acceptance:

| Check | Observed outcome |
| --- | --- |
| Minimum/alternative view | Five rendered pages show the saved EUR 102 / EUR 109 selected allocation, exact content identity and human audit |
| Actual browser downloads | Desktop alternative and mobile recovered document saved real files; both equal stored bytes/hash |
| Renderer failure | Test-only wrapper returns 503 before rendering; saved approval/time remain visible and no download link appears |
| Explicit retry | Same case/content produces a stored PDF after failure is removed; approval is unchanged |
| Backend unavailable/restart | Approval stays visible through failed PDF request; after restart, stored PDF displays even with renderer forbidden |
| No-award and stress child | Zero actionable approved-PDF controls; API denial also tested |
| Mobile / keyboard | 390x844, outer scroll width equals client width (375); zoom scrolls inside the PDF region; keyboard Page Down works |
| Page layout | All five standard and ten long/Unicode pages rendered with Poppler and inspected; wrapping, tables, footer and pagination have no clipping/overlap |

Alternative case `7db24179-c795-4b10-90cf-55ae658e48a8` retained approved content
hash `cb46610ef038b46f49ea150348736e6110bc60fda467117e51f804d2b893fd29`;
its 30,131-byte PDF SHA-256 is
`caadff4e7e0da9fdc6ae46f2eddd84181e0c56dc4487af635e7afdac031bd4fc`.
Recovery case `3eaacb69-3b61-47e4-a834-ed7cfabd110c` retained approval time
`2026-10-10T20:11:13.741893Z` and approved content hash
`554655ee255be96db6e8b7ccdafc90660f9dfaad56d48497327489bf648aedc3`.
All original case hashes and final-decision JSON equal the pre-document records.

Ignored `.artifacts/t21/` contains `approved.pdf`, `long-unicode.pdf`, rendered
pages/contact sheets, `browser-evidence.json`, `pdf-workspace.jpg`, `mobile-pdf.jpg`
and `pdf-failure.jpg`. Test-only fixture preparation/wrapper files are not production
code. Layout stress specimens deliberately enlarge text/provenance; they are
renderer tests, not independently finalized operational records.

Initial native data-URL/Blob iframe previews and scripted downloads did not pass
browser acceptance. They were replaced by the verified local display component
and native download link. An initial database run stalled before tunnel recovery
and was interrupted; fresh connected runs supplied the passing results above.
These initial attempts are not PASS evidence.

A static React-PDF import also failed production server prerendering. Loading it
inside the client effect fixed the failure; production export and a fresh browser
view of all five pages passed afterward, with the renderer forbidden for stored
retrieval. The final focused PDF/frontend selection passed **21 tests** (18.43 s).

## Setup, limitations and next capability

Install the declared dependencies and apply `alembic upgrade head` to the
intentionally selected helper database; expect `20261010_01`. No user application
migration was performed here. Follow [view/download instructions](LOCAL_DEVELOPMENT_AND_SSH.md#approved-pdf-view-and-download).
Downgrading only this revision removes PDF artifacts and preserves human decisions
and approved content; retain backups before any deliberate application rollback.

Acceptance reused the existing Podman machine and a separate disposable
`procurement-decision-support-t21-acceptance` database. Existing Odoo and helper/demo
containers stayed stopped/untouched. Windows forwarding failed; a task-created
localhost-only SSH tunnel used host 55435 -> VM 55434. Acceptance servers,
container and tunnel are cleaned up; the initially stopped machine is returned
to stopped state. Artifact evidence and browser-downloaded synthetic PDFs remain.

Unsupported scripts/emoji outside the bundled font fail rendering rather than
silently substituting missing glyphs. The two-MiB artifact bound is intentional.
Historical/synthetic evidence is a controlled demonstration, not current
operational validity, calibrated supplier prediction, production authentication
or a legally complete external Purchase Order. Browser acceptance is manual/local;
new hosted CI, user review and #22/full AC-V2-13 remain open.

Next: the reproducible controlled hybrid acquisition -> ML -> MILP -> stress ->
base human decision -> stored PDF demonstration (#22). This ticket adds no Odoo
UI/write, direct Odoo database access, observed-model promotion, arbitrary
quotation discovery, Drive write or permanent deployment.

Thesis note: missing approved document -> immutable linked artifact from approved
content -> backend render plus API-only view/download and safe retry -> exact
PDF/HTTP/PostgreSQL/browser/layout evidence -> synthetic/local/authentication
limits -> chapters 3/4/5/6/7; integrated evaluation and conclusions remain later work.
