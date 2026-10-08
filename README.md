# Odoo Procurement Decision Support

A Python side-by-side procurement helper for a BSc thesis. For one approved
product demand and several known suppliers, the intended workflow is:

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
| How do I run real database tests safely? | [Persistence guide](docs/PERSISTENCE_DEVELOPMENT.md) |
| How can I see a plan, a disruption and stored retrieval? | [T15 terminal demonstration](docs/T15_DEMO.md) |
| How does the controlled planning API work? | [T15 handoff](docs/T15_HANDOFF.md) |
| How can I create, compare and reopen a plan in Reflex? | [Planning workspace walkthrough](docs/LOCAL_DEVELOPMENT_AND_SSH.md#controlled-planning-workspace-create-and-test), [T16 handoff](docs/T16_HANDOFF.md) |
| Where are the designs, spikes and historical evidence? | [Documentation index](docs/README.md) |
| Which principles should agents follow across chats? | [Development guidance](AGENTS.md) |

## Current capability — verified 2026-10-08

| Capability | Current implementation and remaining work |
| --- | --- |
| Odoo facts and supplier history | V2 independently reads selected quotations/currency, verifies expectations and assembles attributed business terms. The controlled demonstration uses synthetic ML history; matching Odoo receipt history/model promotion remains open. |
| Decision Tree evaluation | T14 offline training, saved artifact reload, inference and tree-path explanation exist. Evidence/model are controlled synthetic; observed input is rejected. |
| MILP allocation and alternatives | T13 computes one-product integer allocations with hard constraints, minimum cost and epsilon cost/exposure alternatives. |
| Planning API, scenarios, storage | T15 supports the original synthetic case and live Odoo quotations with separate synthetic ML evidence. Five stress scenarios create immutable children; GET/exact replay use stored data only. |
| Buyer-facing planning workflow | T16 controlled implementation is complete locally: synthetic/prepared-Odoo creation, all five bounded stress types, saved plan cost/exposure chart, allocation comparisons, tree explanations, saved input/provenance audit and stored retrieval. Local functional acceptance passes; user testing and publication of the final diff remain pending. Arbitrary quotation discovery and observed-model promotion are separate open capabilities; approval/PDF belongs to T17. |

**Publication:** T13/T14/T15 are merged. T15
[PR #17](https://github.com/SafarErik/odoo-procurement-decision-support/pull/17)
merged into main `3c19890bd17cd89ffd6d4fbdfca3152d07898f55`;
its post-merge [Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141549)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141222)
checks passed. T16 [PR #18](https://github.com/SafarErik/odoo-procurement-decision-support/pull/18)
is open at `0a2cafbacef4adf45f97902df56d7aace21d8786`; its
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37806351589)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37806351546)
checks passed, covering the published scenario/comparison workflow. The final
chart/input-audit/acceptance diff remains local and uncommitted on the same branch;
those hosted checks do not cover it. The [T16 acceptance record](docs/T16_HANDOFF.md)
records 516 passing fast tests and fresh browser/API/PostgreSQL evidence.

**Evidence limits:** this is a controlled technical slice, not full V2 acceptance.
The synthetic score is an uncalibrated exposure proxy, not a supplier-failure
probability. Odoo-derived ML history/model promotion, approval/PDF and
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
This closes local functional acceptance for the controlled cockpit, not the
approval/PDF portions of FR-V2-09 or full V2 acceptance. Drive remains unchanged.

## Architecture and code map

| Area | Responsibility |
| --- | --- |
| `odoo_adapter/` | Validated read-only Odoo API transport and mapping |
| `application/` | Input/provenance assembly and use-case orchestration |
| `supplier_evaluation/` | Offline Decision Tree pipeline and trusted saved inference |
| `decision_core/planning/` | ERP-neutral planning contracts, rules and solver port |
| `optimization_adapter/` | PuLP/CBC implementation behind that port |
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

1. Repeat the short T16 validation sequence, then commit and publish the final diff
   under the user's control; verify CI for the resulting exact SHA before merge.
2. Synchronize the Hungarian Drive status on explicit request after user validation,
   then plan T17 human approval/no-award and approved-snapshot PDF.
   Arbitrary Odoo quotation discovery is not implemented by the prepared flow;
   do not silently treat it or observed-model promotion as accepted.
   [The compatibility boundary](docs/T15_ODOO_COMPATIBILITY_PLAN.md) remains live
   Odoo quotations plus synthetic ML history with independent provenance; matching
   observed receipts/model promotion stays separately open.
3. Implement T17 and complete the local demonstration. Keep unresolved observed
   history/model integration dependencies visible; the full UI revamp comes later.
4. Complete T18 system evaluation and T19 thesis closure against the accepted
   requirements. Plan the next small capability in detail; later work stays indicative.

## Documentation responsibilities

The repository owns executable behavior, terminal procedures and dated technical
evidence. Drive owns the Hungarian thesis requirements, architecture decisions,
roadmap and writing material. On the user's explicit request, nine affected
Hungarian living documents were synchronized on 2026-10-07: T15 merged with
post-merge CI, controlled hybrid acceptance, remaining observed-model/full V2 gates,
and the next T16/T17 capabilities. Native structure and historical evidence were
preserved; the writing guide was checked and retained. This new T16 implementation
has not been synchronized to Drive. Further Drive edits require an explicit request.

Update current status here; link detailed evidence instead of repeating execution
logs. Historical handoffs/spikes retain their dated boundaries. Use the
[documentation index](docs/README.md) to find evidence for thesis writing.
