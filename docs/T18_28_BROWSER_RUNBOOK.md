# Local Chromium buyer-flow smoke — #28

This tests the buyer-facing Reflex → FastAPI → PostgreSQL workflow, including
real backend downtime. It is a functional smoke, separate from visual/accessibility
assessment, unfamiliar-buyer usability and the #27 HTTP latency measurements.
See [issue #28](https://github.com/SafarErik/odoo-procurement-decision-support/issues/28)
and [the agreed specification](T18_EVALUATION_SPEC.md).

## Prerequisites

Use the existing **Python 3.11** environment and Node.js installation. Start the
existing Podman machine using the [local runbook](LOCAL_DEVELOPMENT_AND_SSH.md).
No running FastAPI, Reflex, Odoo, Odoo credential or application database is
needed. Existing services may remain running; smoke uses independently selected
loopback ports and a unique disposable Compose project.

Install the optional browser tools into the chosen environment:

```powershell
.\.venv\t13-check\Scripts\python.exe -m pip install -e ".[frontend,dev,e2e]"
.\.venv\t13-check\Scripts\python.exe -m playwright install chromium
```

The first command installs the project's frontend/development/browser extras.
The second installs Playwright's matching Chromium binaries; it does not use your
personal browser profile. Neither operation changes `.env` or Odoo. Default fast
tests need no browser package/binary. Explicitly selected E2E fails when the
optional plugin, Chromium, Reflex, Python baseline or running Podman prerequisite
is missing; missing prerequisites are not PASS or skipped acceptance.

On this Windows checkout, select the installed Compose provider in this terminal:

```powershell
$env:PODMAN_COMPOSE_PROVIDER = (Resolve-Path .venv/Scripts/podman-compose.exe).Path
```

Confirm `node --version` works. If the existing NVM shim reports an integrity
error, prepend the already installed executable directory to **this terminal's**
PATH, for example the verified local installation:

```powershell
$env:PATH = "C:\Users\Erik Safar\AppData\Local\Author Software\nvm\installs\v24.20.0;" + $env:PATH
node --version
```

This is a local runtime workaround, not a requirement to install that exact Node
version or a global configuration change. Fresh Reflex copies install their own
frontend dependencies and require registry access on first startup.

## Run

From the repository root:

```powershell
$taskRun = Join-Path '.artifacts' ('t18-browser-pytest-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$taskRun/cache" -Force | Out-Null
.\.venv\t13-check\Scripts\python.exe -m pytest tests/e2e -m e2e -v -s `
  --basetemp "$taskRun/temp" -o "cache_dir=$taskRun/cache" `
  --junitxml "$taskRun/result.xml"
```

Always use a fresh pytest temp/cache root: pytest clears `--basetemp` at startup.
The suite prints a separate `.artifacts/t18-browser-<unique-id>` artifact root.
It copies frontend source there, excluding the owner's generated `.web`, state
and cache directories, and prepares the existing matched synthetic model/input
offline. It creates **only** its unique `t18-browser-*` helper database using the
existing persistence Compose file, applies migrations to that fresh database,
then starts its own FastAPI and Reflex processes. Windows uses an owned localhost
SSH forward through the existing Podman machine. All credentials are generated
in memory/process environment; `.env`, owner models and application/Odoo data
remain untouched. Odoo keys/URLs are cleared in the owned service environment.

Readiness is bounded: database/API 60 seconds each, frontend 600 seconds for
initial dependency install/compilation; service commands have a 120-second bound.
Browser assertions/actions have a 45-second bound. Failures retain artifacts;
there is no automatic workflow retry. Each invocation creates a fresh isolated
run, rather than resuming an uncertain failed write against the same database.

Expected: **one passing Chromium test** covering all of these stages:

1. Create demand 10 through the Demo form; compare both saved plans and their
   displayed cost/supplier quantities with the actual backend snapshot.
2. Explicitly approve Alternative 1 with actor/reason/acknowledgement; verify
   unchanged original snapshot and the saved selected-plan decision context.
3. Restart owned FastAPI with the model directory empty, reload the browser and
   reopen by case ID; verify identical stored approval. The #29 extension stops
   FastAPI before PDF viewing: require an alert, preserved approval and no false
   download. Restore it and explicitly retry; readiness exposes a status,
   rendering/download succeeds and bytes/SHA-256 match the backend artifact.
4. Stop owned FastAPI; stored loading must show an error and clear false approval
   success. Restore it and explicitly load again; saved content remains identical.
5. Stop FastAPI before another create; require uncertain-save recovery and blocked
   changed submission. Restore it; explicitly retry the identical retained
   payload/key, then prove that same key/payload is an idempotent replay.

## Artifacts and cleanup

The unique smoke root retains service/migration logs, screenshot(s), Playwright
trace, downloaded PDF, prepared synthetic input/model and a small identity/outcome
record. The pytest root retains JUnit XML. Logs redact generated service/database
secrets; browser artifacts must contain no service token. Do not paste `.env` or
credentials into reports. Traces may contain controlled synthetic request data,
case IDs and actor audit text; they are local ignored artifacts, not thesis prose.

Fixture teardown runs on success or ordinary test/setup failure: stop only owned
process trees, close clients and remove only that unique disposable Compose
project. No named Odoo volume, owner service or saved application database is
removed. Leave the existing Podman machine in its original running state.
The generated frontend dependencies remain in the ignored run directory for
diagnosis; remove an unneeded run directory manually after reviewing evidence.

If pytest is forcibly killed, its teardown cannot run. Use the printed project
name and that run's service logs to identify resources before cleanup; never use
broad Python/Node process kills, default-project `down`, or `down --volumes`.

Run the [required fast checks](../AGENTS.md#commands) before handoff. Required
Quality CI stays unchanged. Hosted browser CI, Ubuntu execution, arbitrary live
Odoo discovery, No-award/scenario browser coverage, mobile/keyboard/visual checks
and unfamiliar-participant validation are separate gates. The dated
[#29 assessment](T18_29_BUYER_ASSESSMENT.md) records the manual desktop/narrow/
keyboard findings and pending human/text-zoom checks separately from this test.

Official tooling references: [Playwright pytest fixtures and tracing](https://playwright.dev/python/docs/test-runners),
[Reflex CLI](https://reflex.dev/docs/api-reference/cli/). The tested local versions
and actual run outcome belong in [the dated handoff](T18_28_HANDOFF.md).
