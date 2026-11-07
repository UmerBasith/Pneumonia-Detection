"""QA end-to-end fixtures: a real PneumoScan server (real ResNet model, GPU if present) on a free port,
with its OWN temporary storage, so the tests never touch the student's history.

Run:  .venv\\Scripts\\python -m pytest tests -q
Set QA_BROWSER_HEADED=1 to watch the Playwright browser.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
SAMPLES = ROOT / "sample_xrays"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _free_port(start: int = 8150, stop: int = 8199) -> int:
    for p in range(start, stop):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError("no free port for the QA server")


def _health(base: str) -> dict | None:
    try:
        with urllib.request.urlopen(base + "/api/health", timeout=2) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


class QAServer:
    """One uvicorn process serving the built frontend + API."""

    def __init__(self, storage: Path, log: Path, extra_env: dict | None = None, port: int | None = None):
        self.storage = storage
        self.log_path = log
        self.port = port or _free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.extra_env = extra_env or {}
        self.proc: subprocess.Popen | None = None

    def start(self, timeout: float = 240.0) -> "QAServer":
        env = {**os.environ, "PNEUMOSCAN_STORAGE": str(self.storage), "PYTHONUTF8": "1", **self.extra_env}
        self._log = open(self.log_path, "ab")
        self.proc = subprocess.Popen(
            [str(PY), "-X", "utf8", "-m", "uvicorn", "app.backend.main:app", "--host", "127.0.0.1",
             "--port", str(self.port), "--log-level", "warning"],
            cwd=str(ROOT), env=env, stdout=self._log, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.proc.poll() is not None:
                raise RuntimeError(f"QA server exited early, see {self.log_path}")
            h = _health(self.base)
            if h and h.get("ready"):
                self.health = h
                return self
            time.sleep(0.5)
        raise RuntimeError("QA server did not become ready")

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(20)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if getattr(self, "_log", None):
            self._log.close()

    def log_text(self) -> str:
        return self.log_path.read_text(encoding="utf-8", errors="replace") if self.log_path.exists() else ""


@pytest.fixture(scope="session")
def qa_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("qa")


@pytest.fixture(scope="session")
def server(qa_dir):
    srv = QAServer(qa_dir / "storage", qa_dir / "server.log").start()
    yield srv
    srv.stop()


@pytest.fixture(scope="session")
def base(server) -> str:
    return server.base


@pytest.fixture(scope="session")
def http(base):
    import httpx

    with httpx.Client(base_url=base, timeout=120) as c:
        yield c


@pytest.fixture(scope="session")
def answer_key() -> dict[str, dict]:
    import csv

    with (SAMPLES / "answer_key.csv").open(encoding="utf-8") as f:
        return {r["filename"]: r for r in csv.DictReader(f)}


# ------------------------------------------------------------------ Playwright
@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(headless=os.environ.get("QA_BROWSER_HEADED") != "1")
        yield b
        b.close()


class PageProbe:
    """Collects console errors/warnings, page errors, failed requests and HTTP >= 400 responses."""

    def __init__(self, page, allow_status: tuple = ()):
        self.page = page
        self.console: list[str] = []
        self.errors: list[str] = []
        self.failed: list[str] = []
        self.bad_status: list[str] = []
        self.allow_status = allow_status
        page.on("console", lambda m: self.console.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: self.errors.append(str(e)))
        page.on("requestfailed", lambda r: self.failed.append(f"{r.method} {r.url} {r.failure}"))
        page.on("response", lambda r: self.bad_status.append(f"{r.status} {r.request.method} {r.url}")
                if r.status >= 400 and r.status not in self.allow_status else None)

    def assert_clean(self, allow_console: tuple[str, ...] = (), allow_failed: tuple[str, ...] = ()):
        console = [c for c in self.console if not any(a in c for a in allow_console)]
        failed = [f for f in self.failed if not any(a in f for a in allow_failed)
                  and "net::ERR_ABORTED" not in f]  # aborted = navigation away / blob revoke, not a failure
        assert not self.errors, f"page errors: {self.errors}"
        assert not console, f"console errors/warnings: {console}"
        assert not failed, f"failed requests: {failed}"
        assert not self.bad_status, f"HTTP errors: {self.bad_status}"


@pytest.fixture()
def new_page(browser, base):
    """new_page(width, height, scheme) -> (page, probe). Every page is checked for errors at the end."""
    made = []

    def make(width: int = 1280, height: int = 720, scheme: str = "light", allow_status: tuple = ()):
        ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme,
                                  accept_downloads=True, base_url=base)
        page = ctx.new_page()
        probe = PageProbe(page, allow_status)
        made.append((ctx, probe))
        return page, probe

    yield make
    for ctx, _ in made:
        ctx.close()


def sample_files() -> list[Path]:
    return sorted(SAMPLES.glob("*.jpeg"))
