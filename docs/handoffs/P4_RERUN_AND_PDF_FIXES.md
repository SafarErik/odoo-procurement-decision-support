# P4 evidence rerun, ADR-035 doc alignment and Hungarian PDF fixes

Date: 2026-10-21. Working-tree increment on `feature/littleChanges` on top of `12f383c`
(merged PR #52, balanced alternative). The regenerated evidence is committed alone as
`36a7a7d` (not pushed); everything else stays in the working tree for the owner.

## Problem

1. `docs/evidence/P4_DEMO_REPORT.json` and `P4_MILP_EVALUATION.json` predate the balanced
   (`kind: "diversified"`) MILP stage, so chapter 7 cannot cite them for the current model.
2. Drive registered ADR-035 as **accepted** (2026-10-20); the repository still called it a
   proposal, and TRACEABILITY rows 7 and 9 described the pre-ADR-035 behaviour.
3. One Hungarian error message still said „Nincs odaítélés”; the rest of the UI says
   „Nem rendelünk”.
4. The Hungarian PDF audit appendix printed two fixed English sentences from the stored
   decision record, plus the raw solver status (`optimal`).
5. PDFs of real Odoo cases printed the raw Odoo unit name ("200 Units"; the synthetic
   fixture "10 piece"), while the UI shows "db" / "pcs".

## Decision

- **P4 rerun:** first blocked by an expired Odoo history key; after the owner renewed it,
  both tools ran from a clean detached worktree at `12f383c`, so the evidence reflects the
  merged code and not this working tree (both reports record `dirty: false`).
- **Fixed English sentences:** the renderer shows the Hungarian translation first and then
  the stored original verbatim in parentheses: `<magyar fordítás> (eredeti, rögzített
  szöveg: „<stored English>”)`. Translation first because the Hungarian reader needs the
  meaning; the verbatim quote keeps the audit exact (the PDF can still be compared
  character-for-character with the stored record and its hash). Records are not changed.
- **Solver status:** Hungarian label with the stored code in parentheses, e.g.
  „optimális (optimal)”, for the same reason.
- **Units:** mapped at render time only, from the stored Odoo unit label. The renderer
  keeps its own copy of the map because `document_adapter` may not import `frontend`
  (and vice versa); the copy is marked as mirroring `frontend/i18n.py` `_UNITS`.
- `LAYOUT_VERSION` is raised to `layout-v4`. PDFs already stored keep their bytes and
  their recorded renderer version (`layout-v3`); only newly rendered languages use v4.

### Every fixed English string reaching the PDF from a stored record

Origin: `application/planning_decisions.py` `_audit()`, written into every decision record.

| Field | Stored text | HU rendering |
| --- | --- | --- |
| `actor_attribution` | caller-supplied audit reference; not authenticated buyer identity | A hívó által megadott naplóhivatkozás; nem hitelesített beszerzői személyazonosság (eredeti, rögzített szöveg: „…”) |
| `demonstration` | Controlled demonstration; synthetic ML evidence; no current operational validity asserted | Ellenőrzött bemutató; szintetikus ML-bizonyíték; aktuális üzemi érvényességet nem állít (eredeti, rögzített szöveg: „…”) |
| `solver_outcome` | `optimal`, `infeasible`, `no_proven_optimum`, `solver_error`, `invalid_input` | optimális (optimal), … |

Not translated on purpose: technical identifiers (Odoo references, provenance field paths
and source types, hashes, solver adapter name). The actor reference and rationale are
free text the buyer typed; the demo tool (`tools/demo.py`) types them in English
("Demonstration buyer", "Approve the lower-exposure alternative…").

### Proposal for new cases (not implemented; kept as L9 future work)

The `demonstration` sentence says "synthetic ML evidence" even for Odoo-history cases,
whose model is trained on generated Odoo purchase history (L9). A durable fix needs a new
decision-record version, e.g. `t17-final-decision-v2`, that stores language-neutral codes
instead of sentences:

- `actor_attribution: "caller_supplied_reference"` (later `"authenticated_user"` with OIDC);
- `evidence_scope` derived from the snapshot (`generated_odoo_history` |
  `observed_odoo_history` | `synthetic_demo`) plus `operational_validity: "not_asserted"`.

The renderer and UI translate the codes; v1 records keep today's verbatim + translation
rendering; approval re-verification accepts both versions; v1 hashes are untouched.
Owner decision (2026-10-21): keep it as documented L9 future work; no record-contract
change now.

## Implemented behavior

| Area | Change |
| --- | --- |
| `docs/adr/ADR-035-balanced-alternative.md` | Status accepted; Drive named as canonical register |
| `docs/MODEL_MILP.md`, `docs/LIMITATIONS_AND_FUTURE_WORK.md` | "ADR-035 proposal" → accepted; L9 notes the HU PDF translation |
| `docs/TRACEABILITY.md` | Status date 2026-10-21; note on the balanced increment; row 7: three ε defaults 0.05/0.1/0.2 + balanced stage ε_d = 0.2; row 9: order-line page title; rows 7, 9, 11 cite the 2026-10-21 evidence |
| `frontend/i18n.py` | `err_reason`: „Nem rendelünk”; no „odaítélés” remains in code, tests or current docs (only historical handoffs quote it) |
| `document_adapter/approved_pdf.py` | `RECORDED_TEXT_HU`, `SOLVER_OUTCOME_HU`, `UNITS`; `recorded()`, `outcome()`, `unit`; layout-v4 |
| Tests | `test_t21_documents.py`: fixture unit `piece` → „db” / "pcs"; `test_odoo_purchase_history.py`: HU translation + verbatim quote of both stored sentences, „optimális (optimal)”, Odoo „Units” → „db”, English PDF unchanged |

## Evidence (commands actually run)

- First P4 attempt: `python -m tools.dev demo` (twice, on clean `12f383c`) → "Demonstration
  incomplete: ValueError: Expected HTTP 200, received 503" at
  `GET …/odoo-history/preview?purchase_group_id=1` (`odoo_history_unavailable`). Root
  cause traced in Python: the history export call
  `/json/2/procurement.product.history.export/read_product_history` answers **401**.
  Read-only probe of both keys against `res.users/search_read`: `ODOO_API_KEY` 200,
  `ODOO_T7S_API_KEY` 401, so the history user's key is expired or revoked. No case was
  stored by these runs. `tools.milp_evaluation` uses the same preview and was not run.
  Side finding: `tools.dev demo` exits 0 even when it prints "Demonstration incomplete".
- After the owner renewed `ODOO_T7S_API_KEY`: read-only probe → 200 for both keys.
  `git worktree add --detach <scratch>/p4wt 12f383c`, with the ignored `.env`,
  `.artifacts/ml/model` and `.artifacts/seed/evaluation_groups.json` copied in (imports
  verified to resolve to the worktree). The services were already up, so instead of
  `tools.dev demo` (whose `odoo-up` would re-run compose with the worktree's relative
  addon mount) the same remaining steps ran with `.env` loaded:
  `python -m alembic upgrade head` and `python -m tools.demo` → "Demonstration complete in
  20.574 s"; then `python -m tools.milp_evaluation` → "PASSED".
- `P4_DEMO_REPORT.json` (2026-10-21T16:41:30Z, `12f383c`, `dirty: false`): policy ε =
  0.05/0.1/0.2, ε_d = 0.2; plans: minimum cost 80 + 120 at 288,608 HUF (exposure 0.6),
  alternative 120 + 80 at 293,132 (0.3333), balanced 100 + 100 at 295,800 (0.3333);
  approval of plan 1, separate No-award (PDF 422), HU/EN PDF, stored replay without Odoo
  and model passed (13 operations). The full local response carries 11 `diversified` runs.
- `P4_MILP_EVALUATION.json` (2026-10-21T16:59:54Z, `12f383c`, `dirty: false`): `passed:
  true`; 21 correctness entries (4/5/10 suppliers, stored request, K = 3, equal-price
  tie-break, three infeasible variants), every one `reference_match: true` and
  `failures: []`; the exhaustive reference includes the balanced (min–max) optimum.
  Median / p95 create latency: 4 suppliers 456 / 511 ms (1 ε) and 618 / 645 ms (3 ε);
  5 suppliers 515 / 559 and 968 / 1,105 ms; 10 suppliers 953 / 1,094 and 1,355 / 1,578 ms.
  In-process solve (3 ε + balanced): 349, 532, 973 ms median for 4/5/10 suppliers.
- A first evaluation run in the same worktree recorded `dirty: true` only because the demo
  had just rewritten its report there (also passed, 0 failures); the demo report was set
  aside and the evaluation rerun so both committed files are clean.
- Real Odoo PDF check: stored case `18d1eef1-2a85-4a47-b086-eee56b707ca5` read through
  the API (GET case and its already stored HU PDF): unit label `odoo:uom.uom:1 = Units`,
  stored PDF text "200 Units" and both English sentences. The same approved content
  rendered locally with the new renderer (nothing stored): „200 db”, „120 db”,
  „1–1 000 db”, translated audit sentences with verbatim quotes, „optimális (optimal)”;
  pages 2 and 6 rendered to PNG and checked visually.
- `pytest tests/test_t21_documents.py tests/test_odoo_purchase_history.py -k pdf` → 14 passed.
- `python -m tools.dev check` → 526 passed, 52 deselected; format, lint, compile and
  `uv pip check` passed.
- `pytest tests/e2e -m e2e --browser chromium` → 3 passed (192 s).

## Limitations and unrun gates

- `P4_ML_REPORT_CHECK.json` was not rerun (the model did not change).
- The P4 demo stored new cases in the development planning database (as requested); the
  evaluation used the disposable test database only.
- The demo summary JSON lists plans by label only; the `diversified` kind is visible in the
  full local response under `.artifacts/demo/`, not in the committed summary.
- Latencies are local single-machine measurements, not an SLA (L10).
- Postgres integration tests not run (no persistence change).
- Already stored PDFs (e.g. case `18d1eef1…`, HU and EN) keep "Units" and the English
  sentences; that is the immutability rule, not a defect.
- Unknown Odoo unit names are shown as Odoo names them; the renderer and UI unit maps
  must be kept in step by hand.

## Thesis chapter

Chapter 6 (implementation: PDF rendering of immutable records, Hungarian presentation of
fixed audit text) and chapter 7 (validation: fresh P4 demo and MILP numbers including the balanced stage);
L9 in chapter 9.
