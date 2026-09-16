# Local development and SSH quick start

This guide is the short terminal reference for running the complete local stack
on Windows and avoiding repeated GitHub SSH passphrase prompts after a restart.
Run all commands in PowerShell unless a section says otherwise.

## First-time project setup

Open PowerShell and move to the repository:

```powershell
Set-Location "$env:USERPROFILE\personal-projects\odoo-procurement-decision-support"
```

Create the Python 3.11 environment and install the project if `.venv` does not
already exist:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[frontend,dev]"
```

Create `.env` once:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set separate, random values for `POSTGRES_PASSWORD` and
`ODOO_MASTER_PASSWORD`. You can generate each value with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Never commit `.env`.

After initializing Odoo, create the dedicated internal `Procurement Integration`
user with access to only the current company. Assign a custom
`Procurement RFQ API Reader` group whose sole model access is read-only access to
`purchase.order`; do not assign standard Purchase or Inventory roles. Generate an
API key from that user's preferences and save it only as `ODOO_API_KEY` in `.env`.
Rotate it before expiry and revoke superseded keys after the replacement passes the
live integration test.

## Start everything after a PC restart

Open three PowerShell terminals at the repository root. In each terminal, activate
the virtual environment first:

```powershell
Set-Location "$env:USERPROFILE\personal-projects\odoo-procurement-decision-support"
.\.venv\Scripts\Activate.ps1
```

If PowerShell cannot find Podman, add its normal installation directory for the
current terminal:

```powershell
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    $env:Path = "$env:LOCALAPPDATA\Programs\Podman;$env:Path"
}
```

### Terminal 1: PostgreSQL and Odoo

Start the Podman machine and both containers:

```powershell
podman machine start podman-machine-default
podman compose --env-file .env -f infra/odoo/compose.yaml up -d db odoo
podman compose --env-file .env -f infra/odoo/compose.yaml ps
```

if odoo is running but can't access it:

```powershell
$machine = (podman machine inspect podman-machine-default | ConvertFrom-Json)[0]

ssh.exe `
  -i $machine.SSHConfig.IdentityPath `
  -p $machine.SSHConfig.Port `
  -N `
  -L 127.0.0.1:8069:127.0.0.1:8069 `
  user@127.0.0.1
```


Useful container commands:

```powershell
# Follow all container logs. Press Ctrl+C to stop following them.
podman compose --env-file .env -f infra/odoo/compose.yaml logs -f

# Follow only one service.
podman compose --env-file .env -f infra/odoo/compose.yaml logs -f db
podman compose --env-file .env -f infra/odoo/compose.yaml logs -f odoo

# Start only PostgreSQL when Odoo is not needed.
podman compose --env-file .env -f infra/odoo/compose.yaml up -d db
```

Odoo is available at <http://127.0.0.1:8069> unless `ODOO_HTTP_PORT` was changed.
PostgreSQL is intentionally internal to Compose and is not exposed to the host;
the application must not access the Odoo database directly.

### Terminal 2: FastAPI backend

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Check it at:

- Health endpoint: <http://127.0.0.1:8000/api/v1/health>
- OpenAPI UI: <http://127.0.0.1:8000/docs>

PowerShell health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

### Terminal 3: Reflex frontend

```powershell
Push-Location frontend
reflex run
Pop-Location
```

Open the URL printed by Reflex, normally <http://localhost:3000>. The Reflex state
backend uses port 8001 and calls FastAPI on port 8000.

## Stop everything

Press `Ctrl+C` in the backend and frontend terminals. Then preserve local Odoo and
PostgreSQL data while stopping the containers:

```powershell
podman compose --env-file .env -f infra/odoo/compose.yaml down
```

Do not add `--volumes` unless the named volumes and all local Odoo/PostgreSQL data
should be intentionally deleted.

## Fast checks before pushing

```powershell
ruff format --check .
ruff check .
python -m compileall backend frontend decision_core odoo_adapter
pytest -m "not integration and not e2e" -v
python -m pip check
podman compose --env-file .env -f infra/odoo/compose.yaml config
```

GitHub Actions repeats these checks in a clean environment after a push or pull
request.

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
