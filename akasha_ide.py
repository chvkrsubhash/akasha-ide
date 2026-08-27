#!/usr/bin/env python3
"""
Akasha Desktop IDE Launcher
===========================

Run with:
  python akasha_ide.py
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from akasha.ide.app import launch_ide

if __name__ == "__main__":
    launch_ide()
