#!/usr/bin/env python3
"""
Akasha Studio — Desktop Application Native Window Launcher
==========================================================

Starts the local backend server and launches Akasha Studio in standalone
application window mode (frameless app window without browser URL/toolbars).
"""

import sys
import os
import time
import subprocess
import threading
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app_server import start_server, get_free_port


def find_browser_app_binary() -> str | None:
    """Locate Microsoft Edge or Google Chrome to launch in --app mode."""
    candidates = [
        # Microsoft Edge (Present on all Windows 10/11 PCs)
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        # Google Chrome
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        # Brave Browser
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def launch_studio_app() -> None:
    port = 9100
    try:
        server = start_server(port)
    except OSError:
        port = get_free_port()
        server = start_server(port)

    # Start server thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    app_url = f"http://127.0.0.1:{port}"
    print(f"============================================================")
    print(f"  Akasha Studio (Desktop Edition) v0.1.0")
    print(f"  Server running at: {app_url}")
    print(f"============================================================")

    # Try launching in native standalone App Mode
    browser_bin = find_browser_app_binary()
    if browser_bin:
        user_data_dir = os.path.expandvars(r"%TEMP%\AkashaStudioData")
        cmd = [
            browser_bin,
            f"--app={app_url}",
            f"--user-data-dir={user_data_dir}",
            "--window-size=1240,820",
            "--window-position=80,60",
            "--disable-extensions",
            "--disable-plugins",
        ]
        try:
            proc = subprocess.Popen(cmd)
            proc.wait()
            return
        except Exception:
            pass

    # Fallback to default browser
    import webbrowser
    webbrowser.open(app_url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    launch_studio_app()
