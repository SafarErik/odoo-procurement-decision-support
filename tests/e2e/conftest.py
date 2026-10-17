"""Local browser harness: owned processes, fresh frontend and disposable helper DB."""

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import httpx
import pytest
from sqlalchemy import create_engine, text

from tools.t15_demo import prepare_demo

REPO = Path(__file__).resolve().parents[2]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_until(check, label, seconds=60):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.25)
    pytest.fail(f"Timed out waiting for {label}; inspect the smoke run's service logs.")


class SmokeStack:
    def __init__(self):
        self.root = REPO / ".artifacts" / f"t18-browser-{uuid4().hex[:12]}"
        self.root.mkdir(parents=True)
        self.project = self.root.name
        self.env = dict(os.environ)
        self.password = secrets.token_urlsafe(32)
        self.token = secrets.token_urlsafe(32)
        self.env.update(
            TEST_POSTGRES_DB="planning_test",
            TEST_POSTGRES_USER="browser_test",
            TEST_POSTGRES_PASSWORD=self.password,
            TEST_POSTGRES_PORT=str(free_port()),
            API_SERVICE_TOKEN=self.token,
            ODOO_BASE_URL="",
            ODOO_DATABASE="",
            ODOO_API_KEY="",
            ODOO_T7S_API_KEY="",
            RUN_T6_LIVE_CONTRACTS="false",
            RUN_T7_LIVE_CONTRACTS="false",
            RUN_T7S_LIVE_CONTRACTS="false",
            PYTHONPATH=os.pathsep.join((str(self.root), str(REPO))),
            PYTHONUNBUFFERED="1",
            REFLEX_TELEMETRY_ENABLED="false",
        )
        self.api_url = f"http://127.0.0.1:{free_port()}"
        self.reflex_port = free_port()
        self.frontend_url = f"http://127.0.0.1:{free_port()}"
        self.env["BACKEND_BASE_URL"] = self.api_url
        self.processes = []
        self.logs = []
        self.api = None
        self.database_started = False
        self.evidence = {
            "started_at": datetime.now(UTC).isoformat(),
            "project": self.project,
            "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
            ).strip(),
            "python": sys.version,
            "versions": {
                name: importlib.metadata.version(name)
                for name in ("reflex", "pytest-playwright", "playwright", "pulp", "scikit-learn")
            },
            "source_sha256": {
                str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted((REPO / "tests/e2e").glob("*.py"))
            },
            "checks": [],
        }

    def command(self, args, label, cwd=REPO):
        process = self.start(args, label, cwd)
        try:
            status = process.wait(timeout=120)
        except subprocess.TimeoutExpired:
            self.stop(process)
            pytest.fail(f"{label} timed out; owned process tree stopped. Inspect {self.root}")
        if status:
            pytest.fail(f"{label} failed; inspect {self.root / (label + '.log')}")

    def start(self, args, label, cwd=REPO):
        log = (self.root / f"{label}.log").open("a", encoding="utf-8")
        self.logs.append(log)
        process = subprocess.Popen(
            args,
            cwd=cwd,
            env=self.env,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
        self.processes.append(process)
        return process

    def stop(self, process):
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    timeout=20,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True,
                )
            else:
                os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=20)

    def compose(self, *args):
        self.command(
            [
                "podman",
                "compose",
                "-p",
                self.project,
                "-f",
                str(REPO / "infra/persistence/compose.test.yaml"),
                *args,
            ],
            "database",
        )

    def api_ready(self):
        if self.api.poll() is not None:
            pytest.fail(f"FastAPI exited; inspect {self.root / 'api.log'}")
        try:
            return (
                httpx.get(self.api_url + "/api/v1/health", timeout=2, trust_env=False).status_code
                == 200
            )
        except httpx.HTTPError:
            return False

    def start_api(self, *, stored_only=False):
        self.env["SUPPLIER_MODEL_DIRECTORY"] = (
            "" if stored_only else str(self.root / ".artifacts/t15-demo/model")
        )
        self.api = self.start(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                self.api_url.rsplit(":", 1)[1],
            ],
            "api",
        )
        wait_until(self.api_ready, "FastAPI health")

    def setup(self):
        print(f"Browser smoke artifacts: {self.root}", flush=True)
        shutil.copytree(
            REPO / "frontend",
            self.root / "frontend",
            ignore=shutil.ignore_patterns(".web", ".states", ".reflex", "__pycache__"),
        )
        self.evidence["frontend_sha256"] = {
            str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((self.root / "frontend").rglob("*.py"))
        }
        self.payload = prepare_demo(self.root / ".artifacts/t15-demo")
        self.env["PLANNING_LIBRARY_COMPANY_ID"] = self.payload["company_id"]
        self.database_started = True  # Clean up even when Compose startup fails partway.
        self.compose("up", "-d")
        self.database_port = int(self.env["TEST_POSTGRES_PORT"])
        if os.name == "nt":
            machine = json.loads(
                subprocess.check_output(
                    ["podman", "machine", "inspect", "podman-machine-default"], env=self.env
                )
            )[0]
            ssh = machine["SSHConfig"]
            self.database_port = free_port()
            self.start(
                [
                    "ssh",
                    "-i",
                    ssh["IdentityPath"],
                    "-p",
                    str(ssh["Port"]),
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ExitOnForwardFailure=yes",
                    "-N",
                    "-L",
                    f"127.0.0.1:{self.database_port}:127.0.0.1:{self.env['TEST_POSTGRES_PORT']}",
                    f"{ssh['RemoteUsername']}@127.0.0.1",
                ],
                "tunnel",
            )
        self.env["DECISION_DATABASE_URL"] = (
            f"postgresql+psycopg://browser_test:{self.password}@127.0.0.1:"
            f"{self.database_port}/planning_test"
        )
        engine = create_engine(
            self.env["DECISION_DATABASE_URL"], connect_args={"connect_timeout": 2}
        )
        try:

            def database_ready():
                try:
                    with engine.connect() as connection:
                        return connection.execute(text("SELECT 1")).scalar_one() == 1
                except Exception:
                    return False

            wait_until(database_ready, "disposable helper PostgreSQL")
        finally:
            engine.dispose()
        self.command([sys.executable, "-m", "alembic", "upgrade", "head"], "migration")
        self.start_api()
        frontend = self.start(
            [
                sys.executable,
                "-m",
                "reflex",
                "run",
                "--env",
                "dev",
                "--backend-host",
                "127.0.0.1",
                "--backend-port",
                str(self.reflex_port),
                "--frontend-port",
                self.frontend_url.rsplit(":", 1)[1],
            ],
            "reflex",
            self.root / "frontend",
        )

        def frontend_ready():
            if frontend.poll() is not None:
                pytest.fail(f"Reflex exited; inspect {self.root / 'reflex.log'}")
            try:
                return (
                    httpx.get(
                        self.frontend_url + "/planning", timeout=2, trust_env=False
                    ).status_code
                    == 200
                )
            except httpx.HTTPError:
                return False

        wait_until(
            frontend_ready, "Reflex frontend (first dependency install may take minutes)", 600
        )
        self.client = httpx.Client(
            base_url=self.api_url,
            headers={"Authorization": "Bearer " + self.token},
            timeout=45,
            trust_env=False,
        )

    def close(self):
        self.evidence["cleanup"] = "FAILED: inspect teardown errors and service logs."
        try:
            with ExitStack() as cleanup:
                if self.database_started:
                    cleanup.callback(self.compose, "down")
                if hasattr(self, "client"):
                    cleanup.callback(self.client.close)
                for process in self.processes:
                    cleanup.callback(self.stop, process)
            for url in (self.api_url, self.frontend_url, f"http://127.0.0.1:{self.reflex_port}"):
                with socket.socket() as sock:
                    sock.settimeout(1)
                    if sock.connect_ex(("127.0.0.1", int(url.rsplit(":", 1)[1]))) == 0:
                        pytest.fail("An owned service listener remains after teardown.")
            self.evidence["cleanup"] = (
                "Owned processes stopped and disposable Compose project removed; "
                "owner services/data untouched."
            )
        finally:
            for log in self.logs:
                log.close()
            for path in self.root.glob("*.log"):
                value = path.read_text(encoding="utf-8", errors="replace")
                for secret in (self.password, self.token):
                    value = value.replace(secret, "<redacted>")
                path.write_text(value, encoding="utf-8")
            (self.root / "evidence.json").write_text(
                json.dumps(self.evidence, indent=2) + "\n",
                encoding="utf-8",
            )


@pytest.fixture
def smoke_stack(request):
    if sys.version_info[:2] != (3, 11):
        pytest.fail("Browser smoke requires the documented Python 3.11 runtime.")
    if not request.config.pluginmanager.hasplugin("playwright") or not importlib.util.find_spec(
        "reflex"
    ):
        pytest.fail(
            'Install optional tooling: python -m pip install -e ".[frontend,dev,e2e]"; '
            "python -m playwright install chromium"
        )
    if shutil.which("podman") is None:
        pytest.fail("Podman is required; start the existing machine using the local runbook.")
    if os.name == "nt":
        machine = json.loads(
            subprocess.check_output(["podman", "machine", "inspect", "podman-machine-default"])
        )[0]
        if machine["State"] != "running":
            pytest.fail(
                "Start existing podman-machine-default using the local runbook; "
                "smoke does not create/start machines."
            )
    if request.getfixturevalue("browser_name") != "chromium":
        pytest.fail("This bounded smoke suite supports Chromium only.")
    # Launch before starting services so a missing Chromium install fails immediately.
    request.getfixturevalue("browser")
    stack = SmokeStack()
    try:
        stack.setup()
        yield stack
    finally:
        stack.close()


@pytest.fixture
def smoke_page(smoke_stack, request):
    if request.getfixturevalue("browser_name") != "chromium":
        pytest.fail("This bounded smoke suite supports Chromium only.")
    page = request.getfixturevalue("page")
    page.set_default_timeout(45000)
    page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
    try:
        yield page
    finally:
        try:
            page.screenshot(path=str(smoke_stack.root / "browser.png"), full_page=True)
        finally:
            trace_path = smoke_stack.root / "trace.zip"
            page.context.tracing.stop(path=str(trace_path))
            with ZipFile(trace_path) as trace:
                exposed = any(
                    secret.encode() in trace.read(name)
                    for name in trace.namelist()
                    for secret in (smoke_stack.token, smoke_stack.password)
                )
            if exposed:
                trace_path.unlink()
                pytest.fail("Generated secret found in browser trace; unsafe trace removed.")
