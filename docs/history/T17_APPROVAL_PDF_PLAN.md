# T17 planning investigation: human finalization and approved PDF

Status: CONFIRMED FOR SPECIFICATION - user requested to-spec on 2026-10-09.
This planning record does not itself authorize implementation or create a new accepted ADR.

## Intended buyer-visible outcome

A buyer selects a valid saved procurement plan or records no-award. The decision
is recorded once, survives retrieval/retry, and an approved plan has a viewable
and downloadable PDF from the same immutable content.

Requirement references remain FR-V2-10/11/12, AC-V2-10/11/12/13, and the affected
FR-V2-09 frontend completion. Preserve relevant NFR-V2-02/04/05/06/07/08.
Existing V1 behavior and accepted ADR identifiers remain unchanged.

## Primary-source authority

- [Official task](https://drive.google.com/file/d/1T4Fo_RsSFgs-zjV5NUPfF6_h7xOraog8/view).
- [06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit): FR-V2-10/11/12 and AC-V2-11/12/13.
- [03_ARCHITECTURE_DECISIONS](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit): ADR-006/007/013/022/023/026/027.
- [02_ROADMAP](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4/edit): approval/PDF and first full local demonstration.
- [Repository alignment](agents/project-baseline.md) and [domain rules](agents/domain.md).

Relevant live Drive records were refreshed during this investigation. Their
pre-merge publication wording remains historical: local HEAD is
780cf0437a327f0f0d89aeb15c1f9d6d001ed204, containing the committed skill setup;
live GitHub main is 979b9b89e8517c65daefcf7e533c8b3f9c2c0ccd. No Git mutation
was performed during this investigation.

## Already settled by requirements and ADRs

- Human finalization is one-time, transactional, concurrency-safe and idempotent.
- Only a concrete valid saved plan can be approved; no-award is separate.
- Alternative selection carries a recorded reason. Keep the existing no-award
  reason requirement. Caller actor attribution is not authenticated buyer identity.
- The approved content and original planning evidence remain immutable.
- A no-award or unapproved state has no approved procurement PDF.
- PDF generation belongs in the backend and consumes stored approved content.
  Download/retry performs no Odoo read, model load/inference, training or solve.
- Rendering failure does not undo approval; rendering the same content version
  can be retried. Content equality is required; byte equality is not a baseline gate.
- Required PDF content includes plan identity, product/demand/unit, supplier
  allocations, prices/cost/currency, relevant terms/scenario, model/policy/source
  references and approval metadata.
- Odoo remains read-only; no automatic ERP Purchase Order, electronic signature,
  new personal identity system or observed-model promotion is authorized.
- Manual allocation editing is not needed for this bounded increment. If added
  later, it requires a new validated plan and approval, never snapshot mutation.
- Drive remains Hungarian and is edited only on explicit request. Engineering
  records here remain English.

## Current implementation facts

| Area | Evidence | Planning implication |
| --- | --- | --- |
| V1 finalization | application/decision_cases.py:237, :333; backend/app/routes/decision_cases.py:236 | Reuse lock/replay/conflict patterns, not offer-based outcome semantics |
| V1 identity/time | backend/app/decision_case_schemas.py:92; application/decision_cases.py:110 | Actor is audit text; V1's caller time participates in exact retry; V2 record-time semantics must be explicit |
| V2 snapshot | application/planning_cases.py:40, :108, :180 | Inputs, assessments, model/policy/solver evidence and results are already saved and read without new computation |
| V2 row immutability | migrations/versions/20261005_01_create_planning_cases.py:36 | Every UPDATE and DELETE is rejected; approval should be a separate linked record |
| Saved plan identity | decision_core/planning/planner.py:95, :117; frontend/planning_client.py:411 | Existing stable indices: 0 = minimum cost; 1..N = distinct alternatives; no independent plan UUID exists |
| Partial calculation | decision_core/planning/planner.py:95; tests/test_t15_planning_api.py:288 | A proven minimum/earlier alternatives may survive a later failure despite a non-optimal overall case status |
| Scenario inputs | application/planning_cases.py:377; frontend/planning/state.py:468 | Each child has its effective changed input; it targets the original base, and changes remain simulations |
| Existing API/UI | backend/app/routes/planning_cases.py:89; frontend/planning/page.py:241 | Creation/scenario/GET exist; V2 human decision and PDF do not |
| Exact saved values | application/planning_serialization.py:41, :140 | PDF can use recorded Decimal strings and rational values; avoid browser calculations |
| PDF dependencies | pyproject.toml dependency declarations and Python 3.11 environment metadata | No generator is currently installed/declared; library remains an engineering choice requiring a focused compatibility/render check |

PDF data must use the selected case's effective request, not original base facts
when the two differ. Supplier labels/identifiers are available; legal business
names, addresses and tax fields are not established document inputs. Do not invent them.

## User-resolved decisions

### Q1 - which cases can be finalized? RESOLVED BY USER

The user accepted approval/no-award only for original base cases. Stress scenarios
remain analytical and cannot be finalized or receive an approved procurement PDF.
If simulated changes become actual business terms, create a new base from confirmed
inputs through the existing creation flow before finalizing it. T17 adds no automatic
scenario promotion or cross-case demand-family locking.

### Q2 - retained proven plans after an incomplete comparison? RESOLVED BY USER

The user accepted approval of a proven valid saved plan when a later alternative
calculation fails or times out. UI and PDF must explicitly show that comparison
is incomplete and preserve the recorded solver outcome. Eligibility is checked
per saved plan, not by requiring an optimal overall case status. A case with no
proven valid plan cannot be approved; it can still receive a reasoned no-award.

### Q3 - historical controlled demonstration? RESOLVED BY USER

The user accepted explicitly labelled historical demo approval, with the saved
simulation/planning reference time and a separate current server-recorded decision
timestamp. The document must distinguish technical demonstration from current
operational input/forecast validity. Synthetic ML provenance remains visible.
This does not waive a future real operational validity gate or promote the model.

## Confirmed implementation plan

Preserve the immutable planning table/snapshot and V1 schema. Add one immutable
linked V2 final-decision record, selecting an existing plan by case/hash/index,
with audit actor, outcome, reason, separate finalization key and recorded UTC time.
Use existing repository/UoW, thin routes, trusted-caller guard and server-only
Reflex token boundaries. Do not add standalone plan IDs or rebuild the solver model.

The decision transaction validates stored contracts and the selected saved plan,
serializes finalization per original base case, and atomically inserts the
decision. Exact replay returns the original decision and timestamp. Conflicting
key reuse or another finalization is rejected. The selected case/hash/index must
match the immutable saved result. Do not infer approval from a default UI selection:
the buyer explicitly chooses the plan and submits the human decision. Index 0 is
the minimum-cost reference; choosing an alternative requires a nonblank reason.
No-award requires a nonblank reason and no selected plan.

The server records the UTC decision time once. It is not a caller-selected or
backdated simulation timestamp, and exact retry cannot change it. Stored plan
validation checks its proof and business constraints against recorded inputs;
it does not search for another plan, rerun inference or solve. Missing, malformed,
unsupported or inconsistent stored evidence fails closed without a decision row.

A versioned document representation is derived solely from immutable decision
and planning data. Keep a stable document/content reference; choose renderer/
artifact storage details through a focused Python 3.11 spike. No fresh lookup of
supplier names or Odoo facts is allowed. Rendering can happen after approval and
fail independently. The result must support viewing and downloading from Reflex.

The approved snapshot combines the original case ID/hash, selected plan/index,
effective planning terms and recorded human decision. Persist the content version
and stable PDF-artifact reference without altering either original planning data
or final-decision content. The renderer must preserve exact quantities, money and
rational metrics from saved data. A PDF is an approved procurement-plan document;
supplier labels alone cannot establish a legally complete external Purchase Order.

Historical-demo documents show a prominent demonstration label, saved simulation
dates, separately recorded current decision time, and synthetic ML provenance.
Approval demonstrates a human decision about that saved simulation; it does not
assert that its old quotations or predictions are currently valid. T17 does not
introduce a general operational freshness policy. The historical-demo path must
remain explicit, rather than silently classifying arbitrary old cases as demos.

Preserve exact pending finalization payload/key on an uncertain HTTP outcome and
require explicit retry, as current planning creation does. Reload exposes the saved
human outcome and selected plan. A download error leaves the approved state visible.

## Bounded delivery slices

| Slice | Buyer-visible capability and concrete acceptance outcome | Existing references |
| --- | --- | --- |
| 1. Saved human decision | A buyer approves saved base plan 0, selects a valid alternative with a reason, or records no-award. Reload and exact retry show the same immutable decision; scenario finalization and a competing second decision are rejected. | FR-V2-10/11, FR-V2-09; AC-V2-10/11 |
| 2. Approved document | The buyer views/downloads a backend PDF containing exactly the selected approved allocation and its audit context. Renderer failure leaves approval intact; retry uses the same content version. Unapproved, no-award and scenario cases cannot receive this document. | FR-V2-12, FR-V2-09; AC-V2-12 |
| 3. Controlled full demonstration | A labelled historical hybrid Odoo/synthetic case passes through saved tree evidence, MILP, stress analysis, explicit base approval, reload and PDF. A separate case demonstrates no-award. Evidence states runtime, provenance and limitations. | AC-V2-13; relevant FR-V2-09/10/11/12 |

Reuse the existing application/repository/API/frontend seams. Expected changes
reach the V2 application decision/document use cases and ports; linked persistence
record/migration; V2 request/response contracts and routes; Reflex client/state,
plans/audit views; relevant fixtures and fast/integration tests. Keep V1 contracts,
solver and model artifacts unchanged. Add only the chosen PDF dependency after
the bounded spike. Update README, execution instructions and dated implementation
evidence when actual behavior or verified facts change.

The PDF spike closes with: Python 3.11 compatibility, required content and long/
Unicode supplier-name rendering, view/download behavior, dependency choice,
artifact-reference/storage decision and any blocker. It is an engineering task,
not an additional buyer-policy question or infrastructure expansion.

## Necessary verification

- Application/HTTP: valid selection; invalid index/hash; no-plan rejection;
  alternative/no-award reasons; one-time outcomes; exact retry versus conflict;
  retained proven plan approval with incomplete-comparison warning; unproven-plan
  rejection; base-only finalization; no-award with and without available plans.
- Stored-only sentinels: approval/retrieval/retry/PDF cannot call Odoo, ML or solver.
- PostgreSQL: unchanged planning snapshots; decision UPDATE/DELETE rejection;
  atomic rollback; simultaneous identical/conflicting finalizations and key reuse.
  V1's sequential double-finalization tests do not establish a racing V2 gate.
- PDF: required content equals approved snapshot; correct effective terms,
  exact money/quantities, source/time/demo labels; Unicode and long content render
  without clipping; unapproved/no-award denial; renderer failure/retry preserves approval.
- Browser/API/PostgreSQL: approve, no-award, reload, lost-response recovery,
  PDF view/download/error, mobile and inaccessible-backend states.
- AC-V2-13: controlled hybrid input -> saved tree -> MILP -> stress analysis ->
  human decision -> retrieval/PDF, with recorded scope, runtime and limitations.
  Final integrated performance/evaluation remains distinct from this first demo.

These are planned gates, not PASS claims. During implementation run focused checks;
before handoff run the required Python 3.11 fast checks once. Run disposable
PostgreSQL integration tests separately from application/Odoo databases. Record
Reflex compilation separately from actual browser acceptance, and hosted CI against
the exact published SHA only after user-controlled publication.

## Thesis-useful record

Problem: machine-generated saved plans currently stop before human finalization.
Decision: extend the existing immutable architecture using the accepted approval/
PDF boundary: base-only human finalization, approval of retained proven plans with
an incomplete-comparison warning, and explicitly labelled historical-demo approval.
Implemented behavior: none yet; this document records investigation and discussion.
Evidence: current source tracing plus refreshed requirements/ADRs; no new runtime tests.
Limitation: controlled/synthetic model, historical simulation dates, PoC actor
attribution, no general operational freshness policy and no V2 approval/PDF implementation.
Chapter relevance: 3 requirements; 4 lifecycle/architecture; 5 invariants;
6 actual future implementation; 7 tests/content identity/limits; 8/9 conclusions.

The buyer-policy frontier is empty. The user confirmed the shared understanding
by requesting progression to to-spec. The [specification](T17_APPROVAL_PDF_SPEC.md)
captures the agreed behavior using the skill's issue template. The user confirmed
the testing seams before requesting to-tickets; [GitHub specification #19](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19)
is published and verified as ready-for-agent. The [ticket breakdown](T17_TICKET_BREAKDOWN.md)
was approved and published as linked issues #20 -> #21 -> #22, each ready-for-agent.
Bodies, labels and text dependencies were verified; parent #19 was unchanged.
No implementation has started. See the [branch handoff](T17_PLANNING_HANDOFF.md).
The official task, FR/AC
identifiers and accepted ADRs are preserved. No new accepted ADR or Drive write
is inferred from this discussion.
