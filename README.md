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
| How can I view a saved plan in Reflex? | [Stored planning walkthrough](docs/LOCAL_DEVELOPMENT_AND_SSH.md#stored-planning-view-two-terminals), [T16 handoff](docs/T16_HANDOFF.md) |
| Where are the designs, spikes and historical evidence? | [Documentation index](docs/README.md) |
| Which principles should agents follow across chats? | [Development guidance](AGENTS.md) |

## Current capability — verified 2026-10-07

| Capability | Current implementation and remaining work |
| --- | --- |
| Odoo facts and supplier history | V2 independently reads selected quotations/currency, verifies expectations and assembles attributed business terms. The controlled demonstration uses synthetic ML history; matching Odoo receipt history/model promotion remains open. |
| Decision Tree evaluation | T14 offline training, saved artifact reload, inference and tree-path explanation exist. Evidence/model are controlled synthetic; observed input is rejected. |
| MILP allocation and alternatives | T13 computes one-product integer allocations with hard constraints, minimum cost and epsilon cost/exposure alternatives. |
| Planning API, scenarios, storage | T15 supports the original synthetic case and live Odoo quotations with separate synthetic ML evidence. Five stress scenarios create immutable children; GET/exact replay use stored data only. |
| Buyer-facing planning workflow | T16's first local slice displays saved base/scenario plans at `/planning`, including allocations, cost/exposure, explanations and provenance. Creation/scenario controls, charts, plan approval and snapshot PDF remain open. |

**Publication:** T13/T14/T15 are merged. T15
[PR #17](https://github.com/SafarErik/odoo-procurement-decision-support/pull/17)
merged into main `3c19890bd17cd89ffd6d4fbdfca3152d07898f55`;
its post-merge [Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141549)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37653141222)
checks passed. T16 changes are local and uncommitted on
`feature/T16-reflex-frontend-implementation`; those hosted results do not cover them.

**Evidence limits:** this is a controlled technical slice, not full V2 acceptance.
The synthetic score is an uncalibrated exposure proxy, not a supplier-failure
probability. Odoo-derived ML history/model promotion, the remaining frontend, approval/PDF and
full local demonstration remain open. Historical checks, Podman forwarding failures
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
exists locally, but its case is absent from the currently connected demo database.

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
| `frontend/` | Separate Reflex API clients; RFQ ledger and stored planning display |
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

1. Review the first T16 slice using the linked stored-planning walkthrough, then
   publish it under the user's control and verify CI for that exact SHA.
2. Add the next T16 capability: controlled case creation and an explicit outage
   rerun through existing API routes. Add charts once that interaction works.
   [The compatibility boundary](docs/T15_ODOO_COMPATIBILITY_PLAN.md) remains live
   Odoo quotations plus synthetic ML history with independent provenance; matching
   observed receipts/model promotion stays separately open.
3. Complete T16 acceptance, then T17 V2 approval/PDF and a complete
   local demonstration. Keep unresolved integration dependencies visible.
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
