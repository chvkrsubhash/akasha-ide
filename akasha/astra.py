#!/usr/bin/env python3
"""
Akasha launcher script — allows 'python akasha.py run hello.akasha'
from the project root or package folder.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from akasha.cli.astra import main

if __name__ == "__main__":
    main()
