# Local development: choose a task, then start its services

Use PowerShell at the repository root. This is the current terminal runbook;
[README](../README.md) owns current capability/status and [the documentation index](README.md)
links designs and historical evidence. Commands below explain their purpose and
expected result. Follow the scenario you need rather than starting the full stack.

## Which processes do I need?

There is one Podman Linux machine and two separate Compose projects. Separate
containers/projects are not separate Podman machines.

| Task | Needed processes | What it proves |
| --- | --- | --- |
| Fast tests, including T15 API | Python only | Business/API contracts; real saved ML/CBC; memory persistence where used |
| Offline ML/MILP demonstration | Python only | Synthetic training, saved reload/inference and allocation |
| PostgreSQL persistence acceptance | Python + disposable `decision-db` | Actual database round-trip, immutability, rollback and concurrency |
| Odoo/RFQ ledger or controlled live contracts | Odoo + its internal `db`; FastAPI/Reflex only for their flows | Documented read-only mappings or the existing RFQ UI |
| Manual T15 API inspection | FastAPI + own planning database + trusted saved model | Controlled HTTP planning/scenario/stored retrieval; Odoo/Reflex unnecessary |

The Odoo Compose project stores ERP data in named volumes. The planning-test project
is disposable and has no named volume. Its tests reset the schema. Keep them separate;
never reuse Odoo's PostgreSQL or a database containing saved application cases for
resetting tests. A persistent application database has not been packaged as a new
local Compose service; this consolidation adds no infrastructure.

## Activate Python and configure once

```powershell
Set-Location "$env:USERPROFILE\personal-projects\odoo-procurement-decision-support"
# Reuse the existing compatible environment; create only if it is absent.
$taskVenv = ".venv\t13-check"
if (-not (Test-Path "$taskVenv\Scripts\python.exe")) {
    py -3.11 -m venv $taskVenv
}
& "$taskVenv\Scripts\Activate.ps1"
python --version
python -m pip install -e ".[frontend,dev]"
```

Expect Python 3.11 and a successful editable installation with no missing dependency.
The older root `.venv` may use another Python version; do not overwrite it or mix
interpreters for saved artifacts. Reactivate this Python 3.11 environment in each
new terminal; installation is only needed initially or when dependencies change.
Reflex manages its web dependencies. Production frontend export additionally needs
the Node.js 22.22 toolchain documented in CI.

```powershell
# Preserve an existing .env; create it only on first setup.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set the values required for your selected task; the example documents each setting.
Generate separate local passwords with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Keep secrets in ignored `.env`. Backend settings load it; shell processes and
Alembic do not automatically load it. Process environment variables override backend
`.env` values. Never print real database URLs or keys into shared logs.

Existing Odoo users/fixtures do not need recreation. For missing business data or
permissions, follow the precise linked manual fixture procedures and confirm the
postconditions. Do not grant broad Purchase/Inventory roles as a shortcut.

## Python-only development loop

For a T15 change, the focused API tests exercise actual saved inference/CBC and
all five scenarios without external services:

```powershell
python -m pytest tests/test_t15_planning_api.py -v
```

Expect successful assertions. An HTTP `201` in a test means a case was stored in its
configured repository; the result status separately indicates optimality/infeasibility.
The fast API tests use an in-memory repository and do not prove real database storage.

To see the existing offline synthetic model and allocation demonstration:

```powershell
python -m supplier_evaluation.cli reproduce
```

This generates data, trains offline, saves/reloads, evaluates and solves. Outputs
stay in ignored `.artifacts/t14/`. The controlled allocation example has EUR 102
minimum cost and a EUR 109 lower-exposure alternative. Later `infer`/`demo` commands
reload the saved model without training. Synthetic accuracy is not real-world validity.

## Start Podman only for a service task

```powershell
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    $env:Path = "$env:LOCALAPPDATA\Programs\Podman;$env:Path"
}
podman machine list
# Run the next command only when the existing machine is stopped.
podman machine start podman-machine-default
$env:PODMAN_COMPOSE_PROVIDER = Join-Path $env:VIRTUAL_ENV "Scripts\podman-compose.exe"
podman compose version
```

Expect the existing Linux machine to be running and the project-local provider to
respond. Do not create another machine to run another Compose project. To run real
persistence tests, continue with the [persistence guide](PERSISTENCE_DEVELOPMENT.md);
no Odoo, separately served FastAPI or Reflex process is needed by those tests.

## Existing Odoo/RFQ UI: three terminals

In terminal 1, with Podman running and `.env` configured:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml up -d db odoo
podman compose --env-file .env -f infra/odoo/compose.yaml ps
podman compose --env-file .env -f infra/odoo/compose.yaml logs --tail=50 odoo
```

`up -d` starts/reuses the two containers in the background. `ps` shows status;
`logs` diagnoses startup. Expect healthy PostgreSQL and Odoo HTTP at port 8069
unless configured otherwise. Odoo's database is internal to Compose; the helper
must access Odoo's API rather than that database. Initial Odoo setup is manual;
see the [T0 handoff](T0_HANDOFF.md) and subsequent [T6 fixture/setup](T6_FIXTURE_SETUP.md)
for the validated integration scope, rather than creating arbitrary credentials.

In terminal 2, activate Python 3.11 as above and run:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

FastAPI serves the HTTP API; `--reload` restarts it after source edits. Use another
terminal for checks while this foreground process runs:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Expect `status: ok`. Health proves the API is running, not Odoo/model/database readiness.
OpenAPI is at <http://127.0.0.1:8000/docs>; RFQs are at
<http://127.0.0.1:8000/api/v1/procurement/rfqs>.

In terminal 3, activate the same environment:

```powershell
Push-Location frontend
reflex run
Pop-Location
```

Open the printed URL, normally <http://localhost:3000>. Reflex's state backend uses
8001 and calls FastAPI on 8000. The current page is the RFQ ledger, not the V2
planning cockpit. Check RFQ rendering/refresh, stop FastAPI to inspect the error
state, then restart it and confirm recovery. Record browser evidence separately
from `reflex export --frontend-only --no-zip`, which checks compilation only.

### Controlled live tests are explicit fixture acceptance

Use [T6 fixture setup](T6_FIXTURE_SETUP.md), [T7-S manual setup](T7S_MANUAL_SETUP.md)
and [T7 historical fixture](T7_FIXTURE_SETUP.md) only for their documented local
cases. The respective `RUN_T6_LIVE_CONTRACTS`, `RUN_T7S_LIVE_CONTRACTS` and
`RUN_T7_LIVE_CONTRACTS` settings opt into those gates. They are false by default.
Read-only credentials alone do not establish that the required fixture is present.

With the intended services/credentials/fixtures available, the existing complete
service selection is `python -m pytest -m "integration and not e2e" -v`.
It includes persistence and running-service tests; prepare their dependencies too.
A skipped live contract remains skipped, not accepted. Prefer the focused selection
for the behavior you changed instead of blindly enabling every live flag.

## Manual T15 API inspection

[The T15 handoff](T15_HANDOFF.md) defines the DTOs, token, model, migration and
expected results. [The persistence guide](PERSISTENCE_DEVELOPMENT.md) explains the
safe disposable-database sequence. This manual flow needs a configured own database
and `T12_TRUSTED_CALLER_TOKEN` plus an owner-generated `T15_TRUSTED_MODEL_DIRECTORY`.
Apply migrations explicitly before requests. HTTP never trains or migrates.

The current local `.artifacts/t15/create-request.json` and matching `http-model/`
are ignored review artifacts, not fresh-clone prerequisites. The supported fresh
checkout acceptance route is the focused automated API/database tests, which create
their own matched controlled fixtures. A reusable interactive T15 demo remains the
next increment; do not substitute current dates or observed Odoo data into this model.

## Windows forwarding troubleshooting and cleanup

If the service is healthy in Podman but Windows localhost refuses a connection,
first check the relevant logs and host port. This is a known forwarding issue;
starting duplicate containers or broadening bind addresses does not resolve it.
The persistence guide shows the 55432 -> 55433 localhost tunnel. For default Odoo
port 8069, in a separate foreground terminal:

```powershell
$machine = (podman machine inspect podman-machine-default | ConvertFrom-Json)[0]
ssh.exe -i $machine.SSHConfig.IdentityPath -p $machine.SSHConfig.Port -N `
  -L 127.0.0.1:8069:127.0.0.1:8069 `
  "$($machine.SSHConfig.RemoteUsername)@127.0.0.1"
```

Use an unused local port if 8069 is occupied and update the client URL accordingly.
The tunnel stays alive until Ctrl+C; it is a workaround, not a repaired Podman proxy.

Stop foreground FastAPI, Reflex and any tunnel with Ctrl+C. Stop just the Odoo
project while retaining named volumes:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml down
```

For test-database shutdown, use its separate command in the persistence guide.
Do not use `down --volumes` against the Odoo project during testing.

## Required checks before handoff

```powershell
ruff format --check .
ruff check .
python -m compileall application backend frontend decision_core odoo_adapter optimization_adapter supplier_evaluation persistence migrations
python -m pytest -m "not integration and not e2e" -v
python -m pip check
git diff --check
```

These check formatting, lint, compilable source, fast regressions, installed
dependency consistency and patch whitespace. Actual ML/CBC execution is required;
missing runtimes fail. Run this selection once before handoff and repeat only after
relevant changes or unresolved failures. Python compilation is not a static type check.

When Compose configuration changed, or a service handoff needs configuration validation:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet
podman compose --env-file .env -f infra/persistence/compose.test.yaml config --quiet
```

For the latter set a synthetic `T11_POSTGRES_PASSWORD` as in the persistence guide.
These commands validate configuration only, start no services, and suppress expanded
configuration/secrets. Quality CI runs for pull requests, main pushes and manual
runs; a feature-branch push alone does not trigger that workflow. Container/API CI
is separately path-filtered. Local success does not establish hosted success.

## Cache the GitHub SSH key across restarts

Keep the private key passphrase. The safer solution is to let the Windows OpenSSH
agent store and provide the unlocked key. This repository currently uses the SSH
host alias `github.com-safarerik`.

### One-time setup

Open **PowerShell as Administrator** and configure the Windows agent service:

```powershell
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
Get-Service ssh-agent
```

Close the administrator terminal. In a normal PowerShell window, force Git for
Windows to use the same Windows OpenSSH client as that service:

```powershell
git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
```

This applies to all repositories for the current Windows account. If another
repository deliberately requires a different SSH implementation, use `--local`
instead of `--global` while inside this repository.

Add the existing key. This should ask for its passphrase once:

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" `
    "$env:USERPROFILE\.ssh\id_ed25519_safarerik"
```

Confirm that the agent and GitHub authentication work:

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" -l
ssh -T github.com-safarerik
```

GitHub normally answers that authentication succeeded but shell access is not
provided. That message is expected.

### Quick check after a later restart

```powershell
Get-Service ssh-agent
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" -l
git config --global --get core.sshCommand
ssh -T github.com-safarerik
```

If the agent is running and lists the key, `git pull` and `git push` should not ask
for the passphrase again. If the agent has no identities, add the key again with the
earlier `ssh-add` command. If the key is listed but Git still prompts, verify that
`core.sshCommand` points to `C:/Windows/System32/OpenSSH/ssh.exe`; Git for Windows
may otherwise use a separate bundled SSH agent.

Do not remove the key's passphrase and never commit a private key. To remove this
key from the agent deliberately:

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh-add.exe" -d `
    "$env:USERPROFILE\.ssh\id_ed25519_safarerik"
```

References:

- [Microsoft: Key-based authentication in OpenSSH for Windows](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement)
- [GitHub: Generating an SSH key and resolving Windows agent conflicts](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent?platform=windows)
