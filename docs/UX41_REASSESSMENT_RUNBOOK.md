# Reproduce the buyer reassessment — #41

The [frozen human protocol](UX41_BUYER_PROTOCOL.md) owns prompts/scoring;
[assessment](UX41_ASSESSMENT.md) owns actual results and remaining gates. Use the
[local services guide](LOCAL_DEVELOPMENT_AND_SSH.md) for the project-local Python
3.11 frontend/dev/e2e environment, installed Git/Chromium/Node, existing running Podman
machine and Compose provider. Do not create another machine or reset owner/Odoo data.

## Automated consolidation

From the repository root, activate the existing environment and Node/provider PATH.
Create a new artifact parent, then run:

```powershell
$reassessmentRun = Join-Path '.artifacts' ('ux41-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$reassessmentRun/cache" -Force | Out-Null
python -m pytest tests/e2e/test_curated_practice_browser.py -m e2e -v -s `
  --basetemp "$reassessmentRun/browser" -o "cache_dir=$reassessmentRun/cache" `
  --junitxml "$reassessmentRun/browser.xml"
```

This reuses the owned disposable PostgreSQL/FastAPI/Reflex/Chromium harness with
actual offline ML/CBC. Expected: one original through Practice creation, exact
comparison, saved feasible disruption, return/alternative approval, product/status
library reopening without a UUID, real PDF access failure and exact download;
additional feasible/infeasible exercises, separate No-award and uncertain Practice
creation with guarded exact replay. Reduced-motion preference is enabled throughout.
Evidence includes current Git HEAD, copied frontend/test hashes, versions, case/
content/PDF identities, screenshots, trace, raw logs and cleanup. This is an informed
agent/browser check; no human observations or hosted browser pass are inferred.

Retain slice evidence listed in the assessment instead of rerunning unchanged
3/5/10-supplier, text-zoom, transactional or 1,000-base query workloads without cause.
Required fast/static/pip/Compose gates remain in the local guide. If relevant source,
fixtures or failures change an assumption, rerun that affected check and retain failures.

## Owner pilot and novice sessions

Use one fresh owned session per person. These commands reuse the existing test
harness for setup/control; they do not automate human task completion. Start an
interactive Python REPL from the repository root after activating the same runtime:

```powershell
python
```

In that REPL:

```python
import json
from uuid import uuid4
from tests.e2e.conftest import SmokeStack

stack = SmokeStack()
stack.setup()
base_url = "/api/v2/procurement/planning-cases"
for _ in range(2):
    response = stack.client.post(
        base_url,
        json=stack.payload | {"catalog_context": {"workspace": "practice"}},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 201
print("Participant starts at:", stack.frontend_url + "/cases")
print("Keep session evidence in:", stack.root)
stack.evidence["outcome"] = "HUMAN_SESSION_SETUP_ONLY"
```

Setup starts only its uniquely named disposable helper stack, prepares the trusted
synthetic fixture offline and creates the two stipulated older Practice drafts via
the real API. Record source/versions/hashes and those fixture identities privately
for the facilitator; do not give the participant a UUID or bookmark. Open the printed
Cases URL in a separate browser profile. Copy the observation CSV into that session's
artifact directory and follow the frozen task prompts. Record owner pilot separately
from novices; declare the cohort before observing novices. No missing observation is
a successful session. Practice's own shared-storage limit remains part of the task.

For B08, after the participant has reviewed a fresh request but before they save it,
the facilitator runs `stack.stop(stack.api)`. For B09, stop this same owned API before
the first document access. Restore with `stack.start_api()` when the interruption is
visible, log setup time, then observe recovery without hints. Never stop an owner/
shared service, alter pending payload/key, or demonstrate the answer silently.

Before teardown, restore the API if needed and keep human observations/screenshots
and downloaded PDFs.
Close the participant browser tab and restore its zoom while the frontend is live,
then export saved base/child records before the final `stack.close()` below:

```python
response = stack.client.get(base_url, params={"workspace": "practice", "limit": 50})
response.raise_for_status()
page = response.json()
assert not page["next_cursor"]  # This fixed session is small; never truncate evidence silently.
identities = [row["case_id"] for row in page["items"]]
for identity in list(identities):
    response = stack.client.get(f"{base_url}/{identity}/scenarios",
                                params={"workspace": "practice", "limit": 50})
    response.raise_for_status()
    children = response.json()
    assert not children["next_cursor"]
    identities.extend(row["case_id"] for row in children["items"])
records = {}
for identity in identities:
    response = stack.client.get(f"{base_url}/{identity}")
    response.raise_for_status()
    records[identity] = response.json()
(stack.root / "human-cases.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
stack.close()
exit()
```

The 50-row bound is a checked session-export limit, not an unrestricted discovery
API. If a cursor appears, stop and extend the export through documented continuation
before claiming complete evidence. Teardown removes only the owned helper project,
stops its API/Reflex/tunnel and redacts generated secrets from logs. It does not retain
that disposable database: export first. Keep the shared Podman machine running.
Close the session browser tab while its frontend is live, reset any zoom/viewport,
then close the stack. Do not exit the REPL before cleanup; if interrupted, inspect
the recorded owned project/process logs and follow the persistence guide's ownership
checks before cleanup. Never print `stack.env`, passwords, tokens or database URLs.

## Recording and acceptance

Keep raw first attempts and retakes in separate CSV rows. Record findings, fixes,
source/protocol version and affected retests. Apply `ceil(0.8 × n)` separately to each
essential task over the declared 3–5 unfamiliar people, with zero unintended
finalizations/unresolved critical misunderstandings. Owner/agent observations and
coached retakes do not count as independent novice successes. Follow the protocol's
versioning rule if pilot findings change a fixture or prompt. Update the assessment
only from actual records; no Drive/issue publication or final acceptance is automatic.
