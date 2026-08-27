#!/usr/bin/env python3
"""
Akasha Studio — Desktop Application Launcher
============================================

Run:
  python akasha_app.py
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_STUDIO = _ROOT / "akasha-studio"

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_STUDIO) not in sys.path:
    sys.path.insert(0, str(_STUDIO))

from launcher import launch_studio_app

if __name__ == "__main__":
    launch_studio_app()
