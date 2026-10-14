# Three-supplier HTTP evaluation — #26 handoff

Date: 2026-10-11. Branch: `feature/T18-implementation`.
Scope: [issue #26](https://github.com/SafarErik/odoo-procurement-decision-support/issues/26),
first delivery slice of [specification #25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25).
Status: **COMPLETE WITHIN #26'S LOCAL SCOPE — implementation, real HTTP measurement, required fast/documentation gates and cleanup verified.**
Changes are uncommitted; this is not hosted CI or completion of T18.

## Problem → decision → behavior

Prior full-flow timings were descriptive single runs. The evaluator needs repeated
operation-specific observations, with exact source identity and visible failures,
before supported-size conclusions can be defended. Reuse the T15 offline synthetic
fixture and existing production HTTP/core/PDF/storage contracts; add only one
bounded CLI and meaningful reporting/failure tests. No API, schema, production
business rule, frontend or dependency changes are needed.

[Evaluator](../tools/t18_evaluation.py) prepares a fresh isolated directory offline,
then makes two warm-up and 30 measured flows through fresh creation, supplier
outage, explicit minimum-plan approval, stored GET, exact creation replay and
first/cached PDF. The workload has three suppliers, demand 10 and one 10% epsilon.
The synthetic model's quantity range is 1–1000 and reference time is 2026-03-01.
Returned minimum/alternative allocations and exact cost/exposure are rechecked
using the existing core validator, without running a solver during verification.
The base minimum is EUR 102; its alternative EUR 109; outage minimum EUR 106.

Request/key/path are atomically recorded before POSTs. Raw outcomes distinguish
HTTP rejection, transport error, validation failure, pending and not attempted.
Ambiguous writes/artifact requests stop without automatic retry; failed warm-ups
stop before measurement. Timed failures remain in percentiles and cannot pass a
successful-operation gate. The first cached retrieval must match PDF bytes,
hash, content binding and reference; stored operations preserve snapshot,
decision/content identity and record time.

Checkpoint evidence retains request intent, hashes, raw latencies, solver outcomes
and decision identities; full saved snapshots are not repeatedly duplicated.
The initial implementation's larger report is retained as development history.
No general benchmarking framework, runtime training, browser model selection
or new configuration API was introduced.

## Executed real HTTP evidence

The authoritative final run is
`.artifacts/t18-26-evaluation-b7580128/evaluation-0ab57503-ba24-4dc5-bfbb-c703fa07f651.json`.
[Repository evidence](T18_26_EVALUATION.json) retains every warm-up/measured timing
and outcome, identity, exact plan metrics, prepared input and reproducibility
context; its raw-report SHA-256 binds the local full-intent/solver report.
Repeated payloads and verbose explanations are omitted from the repository copy,
not from the actual correctness comparisons. The report also captures the
evaluator source hash alongside the planning HEAD and dirty working-tree state;
the unpublished implementation is not mislabelled as that HEAD's committed code.

Served FastAPI at loopback port 8002 used actual saved scikit-learn inference,
PuLP 3.3.0/CBC 2.10.3 and PostgreSQL 16.15 under the existing Podman WSL machine.
Only a new disposable project `procurement-t18-26-b7580128` was started. Its
database exposed VM port 55435; Windows forwarding failed, so a task-owned
localhost SSH tunnel on 55436 was used. The measured latency includes that
network path. Python was 3.11.16 on Windows build 26200, AMD64, 14 logical host
CPUs. The Podman VM was configured for 7 CPUs and 2 GiB memory. Host physical
memory was independently read as 33,765,654,528 bytes. Exact dependency/model/
dataset/input/policy/solver configuration and hashes are in the evidence JSON.

Two warm-up flows succeeded; all **210 measured operations** succeeded, with no
timeout, partial solver outcome, validation error or missing timing. Every row
has 30 measured samples. Nearest-rank p95 is the 29th sorted latency; warm-ups
are excluded. The unrounded observations remain in the JSON.

| Operation | Median (s) | Observed p95 (s) | Maximum (s) | Target (s) | Outcome |
| --- | --- | --- | --- | --- | --- |
| Fresh creation | 0.507567 | 0.571495 | 0.764070 | 5 | PASS |
| Supplier outage | 0.504778 | 0.602628 | 0.652373 | 5 | PASS |
| Explicit approval | 0.200707 | 0.258946 | 0.262753 | 1 | PASS |
| Stored GET | 0.111403 | 0.142419 | 0.161610 | 1 | PASS |
| Exact creation replay | 0.220253 | 0.281872 | 0.303343 | 1 | PASS |
| First PDF | 0.219626 | 0.244752 | 0.250140 | 3 | PASS |
| Cached PDF | 0.140395 | 0.172571 | 0.207589 | 1 | PASS |

The complete earlier development run also succeeded, but predates final compact
reporting/source-hash capture and is not substituted for the authoritative run.
Database readback across both 32-flow executions found 128 planning cases
(base + outage), 64 final decisions and 64 PDF artifacts, consistent with
fresh cases and stored replay/download rather than duplicated creation.
Only helper database tables were read; no Odoo database was accessed.

## Verification and operational notes

[New tests](../tests/test_t18_evaluation.py) cover nearest-rank accounting with
timed failures, missing/pending/unattempted observations and warm-up exclusion;
preservation of existing owner artifacts; actual inference/CBC/API/PDF through
memory persistence; lost-response exact-intent retention without retry; definitive
and ambiguous HTTP failures; and missing document reference/changed cached bytes.
Existing independent allocation oracle, model-integrity, stored-only sentinels,
database concurrency and PDF-content checks are reused rather than copied.

An initial focused command omitted the temporary directory's parent and failed
three fixture setups. Creating the fresh parent corrected that execution error.
A sandboxed TestClient run then stalled before app startup in Windows asyncio's
local socket pair; a timed stack dump established this environmental boundary.
The permitted run outside that socket sandbox passed five tests. These failures
are retained as setup evidence, not counted as procurement failures. The final
test selection includes the two added HTTP-status cases; final gates follow.

The earlier required suite passed 584 tests before the final report/failure
changes; it is historical. The final required suite ran after those changes:
**586 passed, 59 deselected**, including all seven new cases and required actual
ML/CBC runtime. Ruff 0.17.0 whole-repository formatting (206 files) and lint pass;
compileall includes production packages, tools and tests; pip check found no
broken requirements. Both Compose configurations validate without printing
credentials. Patch whitespace and document links pass; the evidence summary
reproduces from all 224 raw observations and matches evaluator/raw-report hashes.
No framework/dependency upgrade was introduced for the existing Starlette
TestClient deprecation warning.

Task-owned API and SSH processes were stopped; the isolated Compose service was
removed, discarding only its disposable data. Generated secret files were deleted.
With no other running containers, the Podman machine was restored to its initially
stopped state. Model/report/PDF evidence remains in ignored task directories;
owner default artifacts, Odoo/application data and named volumes were preserved.
No additional live-Odoo/browser or resetting integration suite was run: #26's
served HTTP measurement exercised actual PostgreSQL, while unchanged transactional
tests retain their historical evidence. New hosted CI awaits user publication.

Reproduction, prerequisites, expected outcomes, uncertainty recovery and cleanup
are in [the runbook](T18_26_EVALUATION_RUNBOOK.md). The
[initial FR/AC/NFR/RQ inventory](T18_EVIDENCE_MATRIX.md) separates reused component
evidence from new #26 observations and later gates.

## Limits and next capability

This is sequential local 3-supplier/1-epsilon **synthetic HTTP** evidence, including
PostgreSQL via the documented tunnel. Thirty samples are descriptive and do not
establish a production distribution, confidence guarantee, concurrent-load SLA
or cold-start behavior. Validation/report IO, offline training, startup and
browser display/task time are outside the HTTP timer and recorded separately.

No new live Odoo, browser, mobile or unfamiliar-participant usability acceptance
is claimed. Larger supplier/epsilon combinations, all five stresses/infeasibility
and separate live quotation reproduction belong to #27; committed browser smoke
to #28; walkthroughs and bounded UI blockers to #29; consolidated conclusions to
#30. Existing skipped T7-S gates retain their relevance review in #27. Synthetic
exposure is not calibrated real-world probability; supplied actor text is not
authenticated identity; approved PDF is not an Odoo PO or legal external order.

No Drive write, stage, commit, push, PR, merge or GitHub issue change is made in
this implementation stage. User review/publication and exact-new-SHA hosted
checks remain next user-controlled gates. After review, #27 can reuse the proven
evaluator to assess all six agreed workloads. Substantial UX/UI improvement and
reassessment remain later development before final acceptance/thesis closure.

Thesis relevance: chapter 7 gains a bounded repeatable method, actual timings,
failure-accounting and limitations for RQ-V2-03–07 and NFR-V2-02/04/06/08; chapter
6 explains the tool, and the complete initial inventory routes all canonical IDs.
No new requirement or ADR is inferred from a passing local measurement.
