"""Start PneumoScan AI: pick a free port (8000-8010), run the server, open the browser.

Used by start.bat. Options:  --no-browser   --port N
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORTS = range(8000, 8011)


def say(msg: str = "") -> None:
    print(f"  {msg}", flush=True)


def health(port: int, timeout: float = 1.0) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def watch(port: int, open_browser: bool) -> None:
    url = f"http://127.0.0.1:{port}/"
    t0 = time.time()
    h = None
    while time.time() - t0 < 90:
        h = health(port)
        if h is not None:
            break
        time.sleep(0.3)
    if h is None:
        say("[ERROR] The server did not answer within 90 seconds. See the messages above.")
        return
    say(f"Server is up:  {url}")
    if open_browser:
        webbrowser.open(url)
        say("Opened the app in your web browser.")
    shown = False
    while time.time() - t0 < 600:
        h = health(port) or {}
        if h.get("ready"):
            mode = h.get("mode")
            if mode == "real":
                say(f"Model ready:   {h.get('model_version')} on {h.get('device')}")
            else:
                say("Model ready:   DEMO MODE - mock model (results are simulated)")
                if h.get("mock_reason"):
                    say(f"               Reason: {h.get('mock_reason')}")
            break
        if h.get("status") == "error":
            say(f"[ERROR] The model failed to load: {h.get('error')}")
            break
        if not shown:
            say("Warming up the model (loading the ResNet weights)...")
            shown = True
        time.sleep(0.5)
    say("")
    say("Keep this window open while you use PneumoScan AI. Press Ctrl+C to stop.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--port", type=int)
    a = ap.parse_args()

    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    # Already running? Just open it.
    for p in PORTS:
        h = health(p, timeout=0.4)
        if h and "app_version" in h:
            say(f"PneumoScan AI is already running at http://127.0.0.1:{p}/")
            if not a.no_browser:
                webbrowser.open(f"http://127.0.0.1:{p}/")
                say("Opened it in your browser. You can close this window.")
            else:
                say("You can close this window.")
            return 0

    candidates = [a.port] if a.port else list(PORTS)
    port = next((p for p in candidates if port_free(p)), None)
    if port is None:
        say(f"[ERROR] No free port between {PORTS.start} and {PORTS.stop - 1}. Close other programs using them and retry.")
        return 1

    try:
        import uvicorn
    except ImportError:
        say("[ERROR] uvicorn is not installed in .venv. Run:  .venv\\Scripts\\python -m pip install -r app\\backend\\requirements.txt")
        return 1

    try:
        from app.backend.main import app

        # The console shows friendly status lines (see watch()); keep raw INFO log lines out of it.
        # Warnings and errors (with tracebacks) are still printed.
        import logging

        logging.getLogger("pneumoscan").setLevel(logging.WARNING)
    except Exception as exc:  # show a clear message instead of a crash dump only
        import traceback

        traceback.print_exc()
        say(f"[ERROR] The server code failed to load: {exc}")
        return 1

    say(f"Starting the server on port {port}...")
    threading.Thread(target=watch, args=(port, not a.no_browser), daemon=True).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        say(f"[ERROR] The server stopped: {exc}")
        return 1
    say("Server stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
