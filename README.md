# Odoo Procurement Decision Support

A Python side-by-side procurement helper for a BSc thesis. For one approved
product demand and several known suppliers, the supported controlled workflow is:

```text
validated read-only Odoo facts + source-attributed supplemental business inputs
  -> input assembly -> saved Decision Tree supplier evaluation -> MILP plans
  -> disruption scenarios -> stored results -> human approval -> downloadable PDF
```

The buyer compares allocations, cost and exposure before making the final decision.
Odoo remains the ERP; the helper reads its documented API and does not create
Purchase Orders. The accepted baseline retains Python, an ERP-independent core,
Odoo 19, FastAPI, PostgreSQL, Reflex and local Podman + Compose.

## Start here

| Your question | Read |
| --- | --- |
| What works and what comes next? | Current capability and next steps below |
| What should I start or run in the terminal? | [Local development runbook](docs/LOCAL_DEVELOPMENT_AND_SSH.md) |
| Why does a saved plan say planning data is unavailable? | [Local stack recovery checklist](docs/LOCAL_DEVELOPMENT_AND_SSH.md#planning-data-unavailable-recover-the-local-stack) |
| How do I run real database tests safely? | [Persistence guide](docs/PERSISTENCE_DEVELOPMENT.md) |
| How can I see a plan, a disruption and stored retrieval? | [T15 terminal demonstration](docs/T15_DEMO.md) |
| How does the controlled planning API work? | [T15 handoff](docs/T15_HANDOFF.md) |
| How can I create, compare and reopen a plan in Reflex? | [Planning workspace walkthrough](docs/LOCAL_DEVELOPMENT_AND_SSH.md#controlled-planning-workspace-create-and-test), [T16 handoff](docs/T16_HANDOFF.md) |
| How can I approve a saved plan or record No-award? | [Decision walkthrough](docs/LOCAL_DEVELOPMENT_AND_SSH.md#saved-human-decision), [T17 approval handoff](docs/T17_HANDOFF.md) |
| Where are the designs, spikes and historical evidence? | [Documentation index](docs/README.md) |
| Which principles should agents follow across chats? | [Development guidance](AGENTS.md) |
| How should engineering skills align with the official thesis task and Drive? | [Project and thesis alignment](docs/agents/project-baseline.md) |
| What is ready for V2 approval/PDF implementation? | [T17 planning handoff](docs/T17_PLANNING_HANDOFF.md), [published tickets](docs/T17_TICKET_BREAKDOWN.md) |

## Current capability — updated 2026-10-11

| Capability | Current implementation and remaining work |
| --- | --- |
| Odoo facts and supplier history | V2 independently reads selected quotations/currency, verifies expectations and assembles attributed business terms. The controlled demonstration uses synthetic ML history; matching Odoo receipt history/model promotion remains open. |
| Decision Tree evaluation | T14 offline training, saved artifact reload, inference and tree-path explanation exist. Evidence/model are controlled synthetic; observed input is rejected. |
| MILP allocation and alternatives | T13 computes one-product integer allocations with hard constraints, minimum cost and epsilon cost/exposure alternatives. |
| Planning API, scenarios, storage | T15 supports the original synthetic case and live Odoo quotations with separate synthetic ML evidence. Five stress scenarios create immutable children; GET/exact replay use stored data only. |
| Buyer-facing planning workflow | The merged T16 cockpit has separate Plans, What-if, Suppliers and Audit views, a cost/exposure chart, scenario drafts and stored retrieval. Synthetic/prepared-Odoo creation and five stress types retain the existing API. Observed-model promotion and arbitrary quotation discovery remain separate. |
| Human decision | Issue #20 is committed: explicit original-base approval or reasoned No-award, immutable audit/approved content, stored reopening and exact uncertain-response recovery. The approval handoff preserves its local evidence. Complete controlled demonstration remains separate. |
| Approved PDF | Issue #21 adds a backend-rendered document from immutable approved content, stored separately with a stable reference/hash. Reflex displays its pages and downloads the exact artifact. Rendering/retrieval failure preserves approval; No-award, unapproved bases and stress children are ineligible. See the PDF handoff for local evidence and limits. |
| Complete controlled demonstration | Issue #22 reproduces the actual read-only Odoo/synthetic-ML/MILP/stress/approval/PDF chain, separate No-award and stored-only reopening. Local AC-V2-13 evidence is recorded; final integrated T18 evaluation remains separate. |

**2026-10-11 update:** #20/#21 are committed at `294b312` / `cf20ada` on
`feature/T17-implementation`. #22 now supplies a repeatable complete controlled
demonstration, with actual read-only Odoo -> saved ML -> CBC -> PostgreSQL ->
Reflex approval/PDF and No-award evidence. The defined controlled AC-V2-13 gate
is met locally; user review, publication/new-SHA CI and merge remain pending.
See [reproduction instructions](docs/T17_FULL_FLOW_DEMO.md) and
[acceptance evidence](docs/T17_FULL_FLOW_HANDOFF.md). No application database was
migrated/reset. Drive remains untouched pending the user's review and green light.
T18 evaluation and observed-model validity remain separate.

**Earlier 2026-10-10 update, superseded above:** #20 is committed at `294b312` on
`feature/T17-implementation`; the user reports its CI looks fine. #21 is now
implemented on the same branch, with new local changes awaiting publication/CI.
Migrate the intended helper database to `20261010_01`, then follow
[PDF viewing/download instructions](docs/LOCAL_DEVELOPMENT_AND_SSH.md#approved-pdf-view-and-download).
See [PDF evidence and handoff](docs/T17_PDF_HANDOFF.md) and the
[closed renderer/storage spike](docs/T17_PDF_SPIKE.md). GitHub issues remain open.
Complete controlled demonstration (#22 / AC-V2-13) remains next; this does not
establish observed-model promotion or full V2 acceptance.

**Earlier 2026-10-09 implementation record, superseded above:** the supplied `feature/T17-implementation`
branch starts at planning merge `f0c5552`. Issue #20 now supplies the saved human
decision capability and local AC-V2-11 evidence. The application database must
be migrated to `20261009_01` before running this branch. See the
[T17 handoff](docs/T17_HANDOFF.md). Changes remain uncommitted; GitHub issues are
still open. PDF (AC-V2-12) and full controlled demonstration (AC-V2-13) remain open.

**Earlier 2026-10-09 planning record, superseded above:** T16 is merged through
[PR #18](https://github.com/SafarErik/odoo-procurement-decision-support/pull/18)
at `979b9b89e8517c65daefcf7e533c8b3f9c2c0ccd`. The approval/PDF
[specification #19](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19)
and linked implementation issues
[#20](https://github.com/SafarErik/odoo-procurement-decision-support/issues/20) ->
[#21](https://github.com/SafarErik/odoo-procurement-decision-support/issues/21) ->
[#22](https://github.com/SafarErik/odoo-procurement-decision-support/issues/22)
are published as ready-for-agent. They define work; approval/PDF and AC-V2-11/12/13
remain unimplemented/open. The current skills/planning branch is not published
or merged by this handoff. See [verification and next-chat instructions](docs/T17_PLANNING_HANDOFF.md).

**Historical publication record, superseded by the update above:** T13/T14/T15 are merged. T15
[PR #17](https://github.com/SafarErik/odoo-procurement-decision-support/pull/17)
merged into main `3c19890bd17cd89ffd6d4fbdfca3152d07898f55`;
its post-merge [Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141549)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141222)
checks passed. T16 [PR #18](https://github.com/SafarErik/odoo-procurement-decision-support/pull/18)
was previously verified open at `0a2cafbacef4adf45f97902df56d7aace21d8786`; its
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37806351589)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37806351546)
checks passed, covering the published scenario/comparison workflow. The final
chart/input-audit/acceptance increment was subsequently committed by the user;
local HEAD is now `02c359ca1920a55ac20e510a1a992785257fc680`. Hosted checks for
that SHA were not refreshed during the cockpit revision, whose changes remain local.
Those earlier hosted checks do not cover this revision. The [T16 acceptance record](docs/T16_HANDOFF.md)
records 516 passing fast tests and fresh browser/API/PostgreSQL evidence.

**Evidence limits:** this is a controlled technical slice, not full V2 acceptance.
The synthetic score is an uncalibrated exposure proxy, not a supplier-failure
probability. Odoo-derived ML history/model promotion and
full V2 demonstration/evaluation remain open. Historical checks, Podman forwarding failures
and skipped live/browser gates remain in the [implementation log](docs/IMPLEMENTATION_LOG.md)
and handoffs. Fresh PostgreSQL and loopback HTTP demo verification now covers the
audit fixes and shared fixture preparation; [T15 handoff](docs/T15_HANDOFF.md)
distinguishes it from earlier runs. The controlled live Odoo quotation/PostgreSQL/API
flow passes: USD 1,850 minimum, USD 2,200 lower-exposure alternative and
USD 2,200 after Supplier C's outage. This is read-only quotation acceptance with
synthetic ML evidence. Initial T16 browser verification used an isolated memory
repository with upstream calls disabled. After local configuration recovery, the
user confirmed the synthetic stored case displays through Reflex; independent live
API GET against actual PostgreSQL returned 200. This is stored retrieval acceptance,
not a fresh Odoo acquisition or complete V2 browser flow. The prior hybrid report
existed locally, but its case was absent from the database at that earlier recovery.
That historical limitation is separate from the fresh persisted T16 cases below.

The next T16 slice now also passes a real Reflex -> FastAPI -> PostgreSQL
controlled creation/outage flow: EUR 102/109 base plans and EUR 106 after the
outage. The model was prepared offline in Python 3.11; no live Odoo acquisition
was performed. See the dated [T16 handoff](docs/T16_HANDOFF.md) for scope,
request-recovery checks and the compatible-model setup requirement.

The 2026-10-08 extension verifies the real Reflex -> FastAPI -> read-only Odoo ->
saved synthetic model -> MILP -> PostgreSQL flow: USD 1,850/2,200 base plans,
USD 2,200 after Supplier C's outage and stored base reopening. The form uses a
fixed prepared comparison, with captured prices checked again during creation;
it is not arbitrary live quotation discovery. See the
[Odoo UI walkthrough](docs/LOCAL_DEVELOPMENT_AND_SSH.md#controlled-odoo-planning-workspace).

The published scenario increment exposes all five supported scenario types and stored
base/scenario comparisons. Browser/PostgreSQL checks reuse the saved hybrid base
with Odoo acquisition and inference disabled. What-if prices remain assumptions;
demand comparisons explicitly distinguish different total quantities. See the
[scenario walkthrough](docs/LOCAL_DEVELOPMENT_AND_SSH.md#what-if-scenarios-and-stored-comparisons).

The final local T16 increment adds the saved cost/exposure chart, explicit
no-distinct-alternative handling and saved input/policy audit. Fresh controlled
Odoo creation, all five scenarios, infeasibility, synthetic creation, stored GET,
service failure and mobile chart checks pass. See the
[short user validation sequence](docs/LOCAL_DEVELOPMENT_AND_SSH.md#t16-final-user-validation).
This was the earlier local functional acceptance. User feedback reopened T16 for
usability and maintainability; the current cockpit revision is recorded separately
in the handoff. Approval/PDF and full V2 acceptance remain open. Drive remains unchanged.

## Architecture and code map

| Area | Responsibility |
| --- | --- |
| `odoo_adapter/` | Validated read-only Odoo API transport and mapping |
| `application/` | Input/provenance assembly and use-case orchestration |
| `supplier_evaluation/` | Offline Decision Tree pipeline and trusted saved inference |
| `decision_core/planning/` | ERP-neutral planning contracts, rules and solver port |
| `optimization_adapter/` | PuLP/CBC implementation behind that port |
| `document_adapter/` | Backend PDF renderer with bundled Unicode font; consumes immutable approved content |
| `persistence/`, `migrations/` | Own PostgreSQL snapshots and explicit Alembic migrations |
| `backend/` | FastAPI contracts, errors and dependency composition |
| `frontend/` | Separate Reflex API clients; RFQ ledger and controlled creation/scenario/comparison/retrieval workspace |
| `tests/`, `.github/workflows/` | Fast, database/service and controlled-live verification |
| `infra/` | Odoo stack/addon and separate disposable persistence-test service |
| `docs/`, `tools/` | Designs/evidence and isolated non-runtime evaluation tooling |

The core does not depend on Odoo, FastAPI, Reflex or ORM frameworks. The frontend
calls only the backend API. Application use cases orchestrate the model, planner
and persistence; infrastructure details stay in adapters/composition.

V1 WSM offer-ranking routes and stored records remain supported historical and
regression components. V2 allocates quantities across suppliers; V1 finalizing one
offer does not implement V2 plan approval. [V1 API](docs/T3_HANDOFF.md),
[V1 stored-case API](docs/T12_HANDOFF.md), [V2 MILP design](docs/T13_V2_MILP_DESIGN.md).

## Run and verify

Use the [terminal runbook](docs/LOCAL_DEVELOPMENT_AND_SSH.md) to activate the
project-local Python 3.11 environment and select only the required services.
For focused controlled planning checks, no running Podman/backend/frontend is needed:

```powershell
$taskRun = Join-Path ".artifacts" ("pytest-run-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $taskRun | Out-Null
python -m pytest tests/test_t15_planning_api.py -v --basetemp "$taskRun/temp" -o "cache_dir=$taskRun/cache"
```

Those checks use actual saved inference and CBC through an in-process API with a
memory repository. Real PostgreSQL acceptance has a separate command and disposable
database in the [persistence guide](docs/PERSISTENCE_DEVELOPMENT.md).
The [terminal demo](docs/T15_DEMO.md) generates matched synthetic artifacts from a
fresh checkout and shows base/scenario creation, stored retrieval and exact replay.
Before handoff, run the required fast checks from the runbook once.

Quality CI executes the full fast suite, including mandatory actual ML/CBC runtime
checks. The path-filtered Container/API workflow tests services and frontend
compilation; it is not browser E2E or observed-model acceptance. `quality` is the
only check intended to be required for branch protection; no settings change is
claimed. Browser milestone procedures are in the runbook.

## Next product steps

1. Review the [#22 full-flow implementation and local acceptance](docs/T17_FULL_FLOW_HANDOFF.md)
   and [repeatable demonstration](docs/T17_FULL_FLOW_DEMO.md). Install dependencies,
   migrate the intended helper database and follow the buyer walkthrough as needed.
2. After the user's green light, consolidate thesis-relevant T17 results into
   affected Hungarian Drive records. Commit/publication/merge and issue closure
   remain under user control; verify CI for the exact final T17 SHA.
3. Complete the separate T18 integrated evaluation and T19 thesis closure against
   the accepted requirements. Observed-history/model promotion, arbitrary quotation
   selection and broader combined scenarios remain separate capabilities;
   [the controlled compatibility boundary](docs/T15_ODOO_COMPATIBILITY_PLAN.md)
   is Odoo quotations plus separately synthetic ML history.

## Documentation responsibilities

The repository owns executable behavior, terminal procedures and dated technical
evidence. Drive owns the Hungarian thesis requirements, architecture decisions,
roadmap and writing material. The earlier 2026-10-07 synchronization covered T15
and its controlled hybrid evidence. The 2026-10-08 Drive records reviewed during
this planning session include T16 local evidence, but retain pre-merge publication
wording. No Drive correction or T17 planning synchronization was performed here.
Further Drive edits require an explicit request.

Update current status here; link detailed evidence instead of repeating execution
logs. Historical handoffs/spikes retain their dated boundaries. Use the
[documentation index](docs/README.md) to find evidence for thesis writing.
