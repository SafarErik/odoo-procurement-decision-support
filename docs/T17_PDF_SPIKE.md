# Approved PDF renderer/storage spike — 2026-10-10

Status: CLOSED. ReportLab and a separate immutable artifact in the existing
helper PostgreSQL database meet the bounded issue #21 rendering/storage seam.
No additional service or buyer-policy decision is needed.

## Question and accepted boundary

Can Python 3.11 render a viewable/downloadable procurement document solely from
the saved `t17-approved-planning-v1` content, paginate long/Unicode text, and
retain a stable artifact reference without changing approval or adding a service?

Sources: [issue #21](https://github.com/SafarErik/odoo-procurement-decision-support/issues/21),
[accepted specification](T17_APPROVAL_PDF_SPEC.md), and a read-only refresh of
[ADR-006/007](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit).
ADR-006 requires the helper database to retain the PDF-artifact reference;
ADR-007 preserves API-only frontend access and a server-only service token.
No accepted ADR or Drive document was changed.

## Evidence and decision

Use **ReportLab 4.4.10** as the runtime dependency and **pypdf 6.x** only in the
development checks. ReportLab's standard Platypus paragraphs/tables provide
pagination without HTML/browser rendering or another service. The existing
runtime had no PDF generator; a new PDF dependency is necessary for this capability.

The Python 3.11.16 specimen produced seven pages (28,139 bytes) with long unbroken
identifiers, repeated tables and Hungarian/Greek/Cyrillic text. pypdf extraction
preserved `Árvíztűrő tükörfúrógép`, `Őrség`, `Ω` and `Ж`; Poppler page inspection
showed wrapping and page splits. The renderer's stock Vera font lacked Hungarian
`ő`/`ű`, so use one unmodified bundled **DejaVu Sans** font instead. The project
wheel includes the font and complete upstream redistribution license.
See [ReportLab fonts](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/),
[Platypus](https://docs.reportlab.com/reportlab/userguide/ch5_platypus/),
and [DejaVu license](https://dejavu-fonts.github.io/License.html).

The implementation checks the bundled font's glyph coverage rather than silently
substituting missing glyphs. Latin, Greek and Cyrillic examples are verified;
arbitrary scripts/emoji are not promised. Unsupported glyphs fail rendering with
the same safe 503 recovery behavior. Long data is XML-escaped, wrapped and
paginated; no input can add PDF links/scripts/markup through a Paragraph.

## Artifact storage and delivery mechanics

- First successful authenticated document GET validates the original case and
  saved approval, locks the case's PDF namespace, renders solely from approved
  content and inserts one separate immutable `planning_documents` row.
- The reference is `t17-approved-pdf-v1:{case_id}:{approved_content_hash}`.
  Store approved-content version/hash, renderer/font/layout version, PDF SHA-256
  and bounded PDF bytes (at most 2 MiB). BYTEA in the existing helper database
  avoids files/volume configuration, public static storage and another service.
- Migration `20261010_01` links to the immutable final decision, rejects artifact
  insertion for different/unapproved content, and rejects UPDATE/DELETE. Original
  planning/final-decision rows remain unchanged. Failed rendering/storage rolls
  back only the new artifact; retry targets the same immutable content reference.
- Existing artifacts are served without rerendering. Binary equality is useful
  cache behavior, while the accepted requirement remains content equality.
  Renderer changes do not rewrite an already stored artifact.
- Backend GET supports `inline`/`attachment` delivery with a safe derived filename,
  content-identity/hash headers, `private, no-store` and `nosniff`. Reflex fetches
  it with the existing token on the server, checks bounded bytes and identities,
  and supplies session-local PDF bytes to a small **React-PDF 10.2.0** display
  component with a locally bundled PDF.js worker. Native iframe previews remained
  empty in the built-in browser. The component displays existing backend bytes
  with a selectable text layer, responsive pages and a native Blob download link;
  it generates no document and exposes no service token. Blob URLs are revoked
  when the component unmounts. No PDF data or worker request is sent to a CDN.
  See [React-PDF display and worker guidance](https://github.com/wojtekmaj/react-pdf/blob/v10.x/packages/react-pdf/README.md).

The initial data-URL iframe and scripted download did not pass browser acceptance;
the native Blob save link produced a real file, and React-PDF displayed all five
pages/text of the backend document. The viewer dependency is necessary for the
verified built-in-browser/mobile view behavior. It is distinct from PDF generation,
which remains entirely in the Python backend. Prepare/view once, then use the
explicit **Download approved PDF** link to save that exact document.

React-PDF is imported inside the client effect. A static import failed production
server prerendering; the client-only import passed production export and the final
built-in-browser view with all five pages. The worker remains bundled locally.

Final required-content, page-layout, browser and PostgreSQL acceptance is recorded
in [the PDF handoff](T17_PDF_HANDOFF.md). Spike specimens and packaging evidence
are ignored under `.artifacts/t21/`; no Odoo business data was acquired or written.

## Limits and reopening condition

This is a controlled procurement-plan record, not a legally complete external
Purchase Order. Saved inputs have supplier labels/identities, not established
legal names, addresses or tax details. Simulation dates, synthetic exposure and
caller-supplied actor attribution remain explicit.

Reopen the spike only if the accepted document content, required glyph coverage,
artifact size/storage requirements or current runtime assumptions change.
Full-flow AC-V2-13 and observed-model promotion remain separate increments.
