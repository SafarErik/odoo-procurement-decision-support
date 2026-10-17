# Revamp plan — completeness audit and delivery plan

Date: 2026-10-17. Status: P0 and P1 merged; P2 implemented (see docs/handoffs/P2_BACKEND_CAPABILITIES.md); P3–P5 open.
Baseline read: official task sheet (423.589/25/140), Drive 00/01/02/03/06/07/08,
README, AGENTS.md, source tree at `main` `0c9f228`.

## 1. Audit summary

### 1.1 Verified technical state

- Fast gate on a fresh Python 3.11.15 venv (uv): `ruff format --check`, `ruff check`
  clean; `pytest -m "not integration and not e2e"` **707 passed**, 76 deselected.
- Not run in this audit: integration/e2e suites, live Odoo, browser UI. This machine
  has no Podman and no system Python 3.11 (Docker Desktop and uv are present).
- Size: ~20k lines of application Python, ~15.6k lines of tests, 107 tracked docs.

### 1.2 Official task sentence → implementation

| Task sentence (abridged) | State | Gap |
| --- | --- | --- |
| Open ERP / Odoo procurement, supplier evaluation, ERP data | Chapter 2 prose done | — |
| Odoo + Python side-by-side; FastAPI, PostgreSQL, Reflex roles | Chapter 2 done; architecture implemented | Repo lacks one architecture doc to write chapter 4 from |
| Decision trees and MILP background | Chapter 2 done | — |
| System **in Odoo** using **historical purchasing data** under control, supplemental data with provenance | Provenance: done. History: 9 admin-created lines, fixed test-copy profile, opt-in path | **Weak.** Model never trains on Odoo history; no in-Odoo entry point |
| Supplier evaluation in Python from **supplier performance characteristics** with decision trees | One `DecisionTreeClassifier` | **Weak.** 2 features, effectively 1; label is a near-deterministic function of the generator's 80 % threshold (circular) |
| Document the training dataset; interpret decision paths | T14 docs, tree path in Audit | No dataset card; path shown as raw evidence, not readable |
| MILP: capacity, MOQ, supplier count, concentration, delivery limits; min cost and risk exposure; multi-supplier | Done (T13), tested vs. reference optimum | Linear exposure Σrᵢxᵢ/Q does not reward diversification → state as limitation (ch. 5) |
| Web UI in Python showing evaluations, allocations, justifications | Reflex cockpit exists | **UX poor**: system metadata everywhere, English only, one chart, no supplier overview, practice/real data blur |
| Store plans, technical approvability, finalize fixed purchase orders as PDF | Immutable storage, idempotent approval, backend PDF | PDF is English, contains raw JSON, reads as an audit log, not as orders |
| Stress test: outage, **capacity, demand and price change**, same MILP | 5 kinds, same MILP | Only one direction (capacity down, demand/price up) — task says "change" |
| Reproducible tests: models, integration, infeasible, full process, ML evaluation conventions | 707 fast + integration/e2e suites | No baseline comparison for the tree; full-flow test depends on a fixed fixture |
| Propose further development | Chapter 9 planned | Feed from measured limitations |

### 1.3 Structural findings

1. **Documentation is an execution diary.** README is 333 lines of dated status;
   107 docs are T-/UX-numbered handoffs. Nothing maps cleanly to thesis chapters 4–7.
2. **Historical V1 code is still live**: WSM decision core, V1 decision-case routes,
   persistence and tools (T2–T12). Not required by the task; owner approved archiving.
3. **Frontend**: `frontend/planning/state.py` is 1,561 lines; UI strings hard-coded in
   English; no i18n layer; audit/hash/snapshot vocabulary leaks into buyer views.
4. **Practice vs. controlled workspace** adds a classification dimension to API,
   DB and UI that the owner does not need in the final product.
5. **Odoo path is hard-wired** to one prepared comparison and one test-copy history
   profile; the reader itself already works per `purchase_group_id`.
6. **An Odoo addon already exists** (`infra/odoo/addons/t7s_inventory_history_projection`,
   ADR-020), so a small RFQ-form button addon is not a new architectural category.
7. **Environment drift**: runbooks assume Podman and a `.venv/t13-check`; neither
   exists here.

### 1.4 Can good thesis chapters be written from this?

Chapters 3 and 5 (requirements, MILP model): yes, the material is solid.
Chapter 4 (design) and 6 (implementation): only after a component-level architecture
doc replaces the diary. Chapter 7 (evaluation): the ML part is currently the weakest
argument — a tree that rediscovers a generator threshold is hard to defend. Training
on Odoo-sourced history with richer features and a baseline fixes this.

## 2. Decisions recorded (owner, 2026-10-17)

- Odoo RFQ-button addon: decide at the end.
- Practice vs. real: no separate DB; filter is enough, possibly not needed at all.
- PDF: per-supplier "Megrendelési javaslat" (purchase order proposal) sheets, audit
  appendix at the end, no raw JSON; PDF language follows UI language.
- UI: natural Hungarian by default, English toggle.
- Stress test: support changes in both directions.
- ML: train from Odoo history so the pipeline works as it would on real data.
- Cleanup: V1 compatibility not required; archive freely while the task stays covered.
- Multi-product: stay single-product, keep the model extensible.
- Workflow: one branch + PR per increment, English handoff each, owner merges.

## 3. Delivery plan

Each phase is one or more PRs with an English handoff (problem → decision →
behavior → evidence → limitation → thesis chapter).

### P0 — Repository cleanup and structure (week 1)

- Move T*/UX* handoffs, runbooks and evidence JSON to `docs/history/` unchanged.
- New docs: `docs/ARCHITECTURE.md` (components, data flow, boundaries),
  `docs/MODEL_ML.md`, `docs/MODEL_MILP.md`, `docs/RUNBOOK.md`, `docs/TESTING.md`,
  `docs/TRACEABILITY.md` (task sentence → feature → test → chapter).
- Short README: what it is, quick start, structure, status table.
- Remove V1: WSM core, V1 decision routes/application/persistence code, T9–T12 tools
  and their tests. New migration drops V1 tables (DB reset accepted).
- Remove the Practice/controlled workspace classification; replace with a
  `data_origin` badge (Odoo / demo) and a list filter.
- One dev entry point (`tools/dev.py` or `justfile`): start stack, seed, test.
  Compose works with Docker or Podman.
- Rewrite AGENTS.md to current, concise rules.

### P1 — Odoo-sourced history and ML retraining (weeks 2–3)

- Seeding tool writes a generated, multi-supplier purchase history (orders,
  partial/late receipts over ~18 months, several products) into a **dedicated Odoo
  test database**, as admin, clearly tagged as generated. *Needs owner approval —
  current rules forbid scripted Odoo writes.*
- Extend the bounded read-only history projection to export per supplier/product
  windows; dataset is built from Odoo reads only.
- Features (as-of cutoff): on-time rate, mean and spread of lateness days, fill rate,
  partial-delivery share, order count, recency. Label: problematic next window.
- Time-based and supplier-grouped split; depth chosen by time-series CV on train
  only; majority-class and single-rule baselines; confusion matrix, F1, support.
- Dataset card, tree rendering, readable path text for UI and PDF.
- Honest framing: the pipeline is Odoo-native; the history in it is generated.

### P2 — Backend capabilities (weeks 2–3, parallel with P1)

- Open-RFQ selection: list purchase groups with quotations; create a case from any
  group (bounded, company-scoped, read-only).
- Stress test in both directions: `capacity_change`, `demand_change`,
  `price_change`, `supplier_outage`, `combined`.
- Supplier overview API: per-supplier history KPIs and latest assessment.
- PDF v2: HU/EN, summary page, one "Megrendelési javaslat" page per supplier,
  readable audit appendix; rendered from the immutable approved snapshot.

### P3 — Frontend revamp (weeks 3–5)

- Layout from the reference mockups: sidebar (Cases, Open RFQs), case header and
  tabs Overview / Suppliers / Plans / Scenarios / Decision & PDF, Audit as drawer.
- i18n module (HU default, EN toggle) with locale-aware money/date formatting.
- Charts: cost vs. exposure, allocation bars, scenario vs. base, supplier KPI trends.
- Buyer views show business language; exact values and hashes only in Audit.
- Split `state.py` per feature. Verify desktop, mobile and error states in browser.

### P4 — Validation and thesis support (week 6)

- One-command reproducible demo (seed → case → plans → scenarios → approve → PDF).
- Full-flow e2e test on the new UI; regenerate ML and MILP evaluation reports.
- Rebuild the MILP/API latency evaluation (T18, removed in P2 with the synthetic demo
  path) on the Odoo-history path; seed quotation groups with 5 and 10 suppliers.
- Fill `TRACEABILITY.md`; list measured limitations for chapter 9.

### P5 — Deferred decisions (week 7, buffer)

- Odoo addon: button on the RFQ form that opens the matching case/creation page.
- Multi-product, only if the supervisor asks (see §4).

## 4. Multi-product extensibility

The core is single-product by explicit validation (`decision_core/planning/models.py`
requires one product/unit/currency). A joint multi-product model needs product-indexed
`x[i,p]`, shared `y[i]`, per-product demand, per supplier-product capacity/MOQ/price and
shared supplier-count/concentration limits. Estimated 1–1.5 weeks including API, UI and
tests. To keep that cheap: new code (supplier overview, PDF, UI) keys data by product
and supplier, and the solver adapter stays behind the planner port. No speculative
multi-product code now.

## 5. Open questions for the owner

1. Approve a scripted admin seeding tool for a dedicated Odoo test database (P1)?
2. Drop the Practice workspace entirely, keeping only a demo-data badge and filter?
3. Use Docker on this machine, or install Podman to match the documented setup?
