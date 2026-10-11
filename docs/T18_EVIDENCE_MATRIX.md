# Initial controlled-system evidence inventory — T18

Prepared 2026-10-11 for [#26](https://github.com/SafarErik/odoo-procurement-decision-support/issues/26).
This is an initial routing inventory, not final acceptance. Canonical meanings
remain in [06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit)
and [04_RESEARCH_NOTES](https://docs.google.com/document/d/1wpglDSL8rMUCFADUhslrgtIRRcWVAdujoEncrDY9WmY/edit).
The requirement link above is the canonical document linked by
[project alignment](agents/project-baseline.md); no identifier is redefined here.

Historical T13–T17 handoffs record their actual dates and revisions. T17 merged
through PR #24 at `ed4be413b11dc469307fc1bb1ed4bd6c16c17b88`; its controlled PASS
does not imply T18 completion. #26 starts from `7536a54`, the published planning
commit; [its handoff](T18_26_HANDOFF.md) and [measurement evidence](T18_26_EVALUATION.json)
record new local checks and hashes of the uncommitted evaluator. Hosted checks
for a later user-published implementation SHA remain pending.

## 2026-10-11 continuation — #27

[#27's handoff](T18_27_HANDOFF.md), [six-workload export](T18_27_EVALUATION.json)
and [separate live record](T18_27_LIVE_VALIDATION.json) supersede the initial
inventory's future-#27 wording below. All six 3/5/10 × 1/3 workloads, five stress
types and bounded infeasibility passed: 2,160 measured/144 warm-up operations,
72 unchanged target gates. Exact returned constraints/metrics, all epsilon-run
references, original-base lineage, deltas/provenance/comparisons and actual
PostgreSQL readback are verified; the independent T13 oracle remains in the
591-pass fast suite. Requested epsilons and deduplicated plans stay separate.

The fixed three-supplier read-only Odoo/synthetic-model/approval/PDF/No-award
chain and unavailable-Odoo/unconfigured-model stored reopening passed. Relevant
PostgreSQL contracts passed 36 checks, primary live Odoo 18. The initial run's
**two T7-S/T8 HTTP 401 failures are retained**. After the user renewed the dedicated
key, a separate focused rerun passed both checks (2 passed, no failures/skips).
Current history/security validation is PASS; this is 54 initial passes plus
2 later passes, not one 56-pass execution. Earlier history/projection proof
remains dated evidence; neither it nor this rerun promotes an observed model.

FR/AC-V2-01–08/10–13 and NFR/RQ routes below now have the linked #27 contribution;
NFR-V2-05 has fresh bounded projection/direct-access-denial evidence; short-lived credentials remain an operational prerequisite. #28/#29 browser/buyer assessment
and #30 consolidated acceptance remain separate. Unfamiliar-buyer usability
is NOT ASSESSED. Local warmed sequential targets are not production SLAs or
arbitrary-instance scaling evidence. This continuation adds no Drive change.

## Functional and acceptance routes

| Canonical identifiers | Existing evidence and scope | #26 contribution / later gate |
| --- | --- | --- |
| FR-V2-01 / AC-V2-01 | [T15 handoff](T15_HANDOFF.md), [Odoo boundary](T15_ODOO_COMPATIBILITY_PLAN.md): fixed read-only quotations plus explicit terms and separate synthetic ML | #26 is fully synthetic HTTP, not a fresh live Odoo check; #27 validates the fixed hybrid separately |
| FR-V2-02 / AC-V2-02 | [T14](T14_HANDOFF.md), [dataset tests](../tests/test_t14_dataset.py): controlled dataset, cutoff/split/leakage boundaries and offline preparation | Reuse actual offline prepared model/dataset, hashes and validity; observed promotion stays separate |
| FR-V2-03 / AC-V2-03 | [ML metrics](T14_EVALUATION.json), [model tests](../tests/test_t14_model.py): controlled metrics, saved artifact and tree paths | Actual saved inference is exercised; no new predictive/calibration claim or new training method |
| FR-V2-04/05 / AC-V2-04 | [T13](T13_HANDOFF.md), [independent reference tests](../tests/test_t13_planning.py): integer demand and capacity/MOQ/count/concentration/delivery constraints | Recheck returned allocations/exact metrics using the existing validator; retain independent small reference proof |
| FR-V2-06 / AC-V2-05 | T13 reference tests and [T15 API tests](../tests/test_t15_planning_api.py): minimum/epsilon trade-offs, distinct/no-distinct alternatives | Record one requested epsilon and actual returned plans; broader supported matrix is #27 |
| FR-V2-07 / AC-V2-06 | T13/T14/T15 tests: deterministic ties, input-order stability, exact metrics and reproducibility | Repeated cases retain request/model/policy/solver evidence; no new deterministic-policy definition |
| FR-V2-07 / AC-V2-07 | T13 reference/fault tests: exclusion/infeasibility and incomplete-solver distinctions | Record all actual statuses/partial results; a nonoptimal controlled flow fails rather than becoming false success |
| FR-V2-08 / AC-V2-08 | T15 tests and [T17 full flow](T17_FULL_FLOW_HANDOFF.md): five stress types plus infeasible, immutable original base | #26 repeatedly evaluates supplier outage only; all five and broader comparisons belong to #27 |
| FR-V2-09 / AC-V2-09 | [T16](T16_HANDOFF.md), T17 manual local browser/mobile/error acceptance | No fresh browser result from #26; local automated smoke is #28, task/accessibility assessment #29; novice usability NOT ASSESSED |
| FR-V2-10 / AC-V2-10 | [T15 storage](T15_HANDOFF.md), [actual PostgreSQL tests](../tests/integration/test_t15_planning_postgres.py): immutable GET/replay/scenarios/concurrency | Repeated real HTTP/PostgreSQL stored GET and exact replay preserve snapshot/decision/time; no new concurrency benchmark |
| FR-V2-11 / AC-V2-11 | [T17 approval](T17_HANDOFF.md), [contending PostgreSQL tests](../tests/integration/test_t17_decisions_postgres.py): one original-base approval/No-award, rollback/immutability | Repeated explicit minimum-plan approval and stored identity; No-award and concurrency retain prior coverage and later assessment |
| FR-V2-12 / AC-V2-12 | [T17 PDF](T17_PDF_HANDOFF.md), [content/fault tests](../tests/test_t21_documents.py), [PDF PostgreSQL tests](../tests/integration/test_t21_documents_postgres.py) | Fresh/cached PDF timings, approved-content binding, stable reference/hash and exact cached bytes; existing content/rendering/security coverage reused |
| AC-V2-13 (cross-cutting) | T17 local real hybrid flow and [reproduction](T17_FULL_FLOW_DEMO.md): separate No-award and stored-only reopening | #26 repeatedly measures a narrower synthetic HTTP flow; #27/#28/#29 feed the final controlled assessment in #30 |

## Nonfunctional routes

| Identifier | Evidence route | Assessment boundary |
| --- | --- | --- |
| NFR-V2-01 modularity | [Project alignment](agents/project-baseline.md), accepted ADRs, existing adapters/ports | #26 adds a CLI tool, not core/framework coupling, schema or new endpoint |
| NFR-V2-02 reproducibility | T13/T14/T15 tests; #26 raw intent/timing/model/input/policy/solver/source identity | Repeated 3/1 local evidence; exact stored equality is checked, larger matrix is #27 |
| NFR-V2-03 data integrity | T14 cutoff/split/leakage/observed rejection; T15 provenance tests | Synthetic remains synthetic; no observed-model validation is inferred |
| NFR-V2-04 testability | Independent T13 oracle, T14 runtime tests, API/real-DB contracts; [new accounting tests](../tests/test_t18_evaluation.py) | Real served HTTP/PG measurements complement memory-backed fast tests; browser smoke is separate |
| NFR-V2-05 least privilege | T6/T7-S access contracts and T15 auth/input/error tests | #26 reads no Odoo; two skipped T7-S live gates retain their limits and relevance review in #27; token is not production identity |
| NFR-V2-06 snapshot/approval integrity | T15/T17 stored-only/rollback/concurrency/immutability and T21 content/PDF checks | Repeated stored comparison and PDF identity supplement prior transactional evidence; no concurrency-SLA claim |
| NFR-V2-07 replaceable frontend | Reflex HTTP-only baseline; T16/T17 frontend contracts | No frontend change or new browser evidence; #28/#29 assess their own boundaries |
| NFR-V2-08 local reproduction/runtime | [#26 runbook](T18_26_EVALUATION_RUNBOOK.md), raw observations and operation-specific target results | Two warm-ups/30 attempts, one workload and seven operations only; larger matrix, cold start and production distribution are not established |

## Research-question routes — provisional until #30

| Identifier / question area | Evidence and interpretation | Remaining boundary |
| --- | --- | --- |
| RQ-V2-01 ERP/hybrid separation | Odoo mapping/ports, provenance/access tests and controlled T15 hybrid | #26 is synthetic; new fixed live reproduction in #27; no arbitrary discovery |
| RQ-V2-02 controlled ML reproducibility/interpretation | T14 metrics/split/artifact/path and actual saved inference | Controlled synthetic evidence, not observed predictive superiority or calibrated probability |
| RQ-V2-03 allocation constraints/reference optimum | T13 independent oracle plus #26 returned-plan revalidation | Larger runtime cases cannot replace an independent optimum proof |
| RQ-V2-04 cost/exposure alternatives | T13/T15 exact minimum/epsilon comparisons; #26 recorded plans | Interpret descriptive trade-offs across supported workloads in #27; never assert real savings from synthetic risk |
| RQ-V2-05 disruption outcomes | T15/T17 five scenarios/infeasible; #26 original-base outage | New systematic all-stress evaluation in #27; changed demand remains a different total |
| RQ-V2-06 decision/PDF traceability | T17/T21 integrity tests; #26 selected-plan/content/hash/time/replay/document identity | Technical attribution, not authenticated/legal approval; browser tasks in #28/#29 |
| RQ-V2-07 local runtime/reproducibility | #26 seven-operation repeated HTTP evidence and exact runtime context | Only 3 suppliers/1 epsilon here; fuller matrix in #27; no production SLA/cold-start/novice-task claim |

No threshold or unresolved gate becomes PASS merely because evidence is linked.
The final #30 assessment records exact dates/revisions, scope, failures, limits
and needed user decisions. Substantial UX/UI improvement and reassessment remain
later development before final acceptance and T19 thesis closure. Chapter 7 owns
measurements/assessment; chapters 3/4/6 and conclusions use only justified findings.
