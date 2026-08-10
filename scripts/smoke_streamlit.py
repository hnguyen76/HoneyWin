#!/usr/bin/env python3
"""Start Streamlit headlessly and verify its health and root endpoints."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def main() -> int:
    port = available_port()
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.headless=true",
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--browser.gatherUsageStats=false",
    ]
    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    deadline = time.monotonic() + 35
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                print(f"Streamlit exited before becoming healthy (code {process.returncode}).")
                return 1
            try:
                with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                    health = response.read().decode("utf-8").strip().lower()
                with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                    root_status = response.status
                if health == "ok" and root_status == 200:
                    print(f"Streamlit smoke test passed on port {port}.")
                    return 0
            except (URLError, TimeoutError):
                time.sleep(0.25)
        print("Streamlit did not become healthy within 35 seconds.")
        return 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
