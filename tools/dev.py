"""One entry point for local development tasks.

    python -m tools.dev check     fast quality gate (format, lint, compile, fast tests, pip)
    python -m tools.dev db-up     start the persistent planning database and migrate it
    python -m tools.dev db-down   stop it (data stays in the named volume)
    python -m tools.dev api       run FastAPI on 127.0.0.1:8000 with reload
    python -m tools.dev ui        run the Reflex frontend (port 3000)
    python -m tools.dev odoo-up   start Odoo and its own database
    python -m tools.dev odoo-down stop Odoo

Settings come from the ignored .env file (see .env.example).
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    "application backend frontend decision_core odoo_adapter optimization_adapter "
    "document_adapter supplier_evaluation persistence migrations tools"
).split()


def _env() -> dict[str, str]:
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.lstrip().startswith("#"):
                env.setdefault(key.strip(), value.strip())
    provider = Path(sys.executable).with_name(
        "podman-compose.exe" if os.name == "nt" else "podman-compose"
    )
    if provider.exists():
        env.setdefault("PODMAN_COMPOSE_PROVIDER", str(provider))
    return env


def _run(*command: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=cwd, env=env or _env())
    if result.returncode:
        sys.exit(result.returncode)


def _compose(file: str, *args: str) -> None:
    _run(shutil.which("podman") or "podman", "compose", "--env-file", ".env", "-f", file, *args)


def _venv_tool(name: str) -> str:
    """Prefer the tool installed next to this interpreter (works without activation)."""
    local = Path(sys.executable).with_name(name + (".exe" if os.name == "nt" else ""))
    return str(local) if local.exists() else shutil.which(name) or name


def check() -> None:
    py = sys.executable
    _run(py, "-m", "ruff", "format", "--check", ".")
    _run(py, "-m", "ruff", "check", ".")
    _run(py, "-m", "compileall", "-q", *PACKAGES)
    # CBC cannot use a temp directory whose path contains spaces.
    with tempfile.TemporaryDirectory(prefix="pdss-", dir=ROOT / ".artifacts") as run:
        env = _env() | {"TEMP": run, "TMP": run}
        _run(
            py,
            "-m",
            "pytest",
            "-m",
            "not integration and not e2e",
            "-q",
            "--basetemp",
            str(Path(run) / "pytest"),
            "-p",
            "no:cacheprovider",
            env=env,
        )
    if importlib.util.find_spec("pip"):
        _run(py, "-m", "pip", "check")
    else:  # uv-created environments ship without pip
        _run("uv", "pip", "check", "--python", py)


def db_up() -> None:
    _compose("infra/app/compose.yaml", "up", "-d", "--wait")
    _run(sys.executable, "-m", "alembic", "upgrade", "head")


COMMANDS = {
    "check": check,
    "db-up": db_up,
    "db-down": lambda: _compose("infra/app/compose.yaml", "stop"),
    "api": lambda: _run(
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ),
    "ui": lambda: _run(_venv_tool("reflex"), "run", cwd=ROOT / "frontend"),
    "odoo-up": lambda: _compose("infra/odoo/compose.yaml", "up", "-d", "db", "odoo"),
    "odoo-down": lambda: _compose("infra/odoo/compose.yaml", "stop"),
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    (ROOT / ".artifacts").mkdir(exist_ok=True)
    COMMANDS[sys.argv[1]]()
