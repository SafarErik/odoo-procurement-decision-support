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
| How does the controlled planning API work? | [T15 handoff](docs/T15_HANDOFF.md) |
| Where are the designs, spikes and historical evidence? | [Documentation index](docs/README.md) |
| Which principles should agents follow across chats? | [Development guidance](AGENTS.md) |

## Current capability — verified 2026-10-06

| Capability | Current implementation and remaining work |
| --- | --- |
| Odoo facts and supplier history | Bounded read-only RFQ/comparison/history components exist. Complete V2 Odoo input assembly remains open; business terms require explicit source attribution. |
| Decision Tree evaluation | T14 offline training, saved artifact reload, inference and tree-path explanation exist. Evidence/model are controlled synthetic; observed input is rejected. |
| MILP allocation and alternatives | T13 computes one-product integer allocations with hard constraints, minimum cost and epsilon cost/exposure alternatives. |
| Planning API, scenarios, storage | T15 composes controlled synthetic facts, saved inference and MILP; five stress scenarios create immutable child records; GET/exact replay use stored data only. |
| Buyer-facing planning workflow | The existing Reflex UI lists RFQs. The V2 planning cockpit, plan approval and snapshot PDF remain open. |

**Publication:** T13/T14 are merged. GitHub main is
`247914ac05663d7358d53036c08750d9390d1baa`; its post-merge
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37358433437)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37358433349)
checks passed. Local T15 commit is `921673493d63b3e5fadd9189f50ee5b644308871` on
`feature/T15-implementation`. At this check GitHub could not resolve that commit and
returned no workflow runs for it. T15 hosted CI is unverified; main's results do
not cover T15 or this consolidation working tree.

**Evidence limits:** this is a controlled technical slice, not full V2 acceptance.
The synthetic score is an uncalibrated exposure proxy, not a supplier-failure
probability. The complete Odoo-to-V2/model integration, frontend, approval/PDF and
full local demonstration remain open. Historical checks, Podman forwarding failures
and skipped live/browser gates remain in the [implementation log](docs/IMPLEMENTATION_LOG.md)
and handoffs. Current T15 service evidence predates the subsequent audit fixes;
its handoff distinguishes those runs. No new service/live acceptance is inferred.

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
| `frontend/` | Separate Reflex API client; currently the RFQ ledger |
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
python -m pytest tests/test_t15_planning_api.py -v
```

Those checks use actual saved inference and CBC through an in-process API with a
memory repository. Real PostgreSQL acceptance has a separate command and disposable
database in the [persistence guide](docs/PERSISTENCE_DEVELOPMENT.md).
Before handoff, run the required fast checks from the runbook once.

Quality CI executes the full fast suite, including mandatory actual ML/CBC runtime
checks. The path-filtered Container/API workflow tests services and frontend
compilation; it is not browser E2E or observed-model acceptance. `quality` is the
only check intended to be required for branch protection; no settings change is
claimed. Browser milestone procedures are in the runbook.

## Next product steps

1. Review the consolidation and validate/publish the existing controlled T15 slice;
   verify CI for the published SHA, preserving the user's commit/merge control.
2. Resolve the V2 Odoo input and model-compatibility demonstration boundary. The
   accepted ML baseline permits documented controlled/synthetic data; it does not
   permit relabelling observations or claiming predictive validity without evidence.
3. Deliver the T16 Reflex planning cockpit, then T17 V2 approval/PDF and a complete
   local demonstration. Keep unresolved integration dependencies visible.
4. Complete T18 system evaluation and T19 thesis closure against the accepted
   requirements. Plan the next small capability in detail; later work stays indicative.

## Documentation responsibilities

The repository owns executable behavior, terminal procedures and dated technical
evidence. Drive owns the Hungarian thesis requirements, architecture decisions,
roadmap and writing material. Its living status documents were last synchronized
on 2026-10-05 and still describe T15 as proposed; they do not reflect the local T15
commit or these workflow principles. Drive edits require an explicit user request.

Update current status here; link detailed evidence instead of repeating execution
logs. Historical handoffs/spikes retain their dated boundaries. Use the
[documentation index](docs/README.md) to find evidence for thesis writing.
