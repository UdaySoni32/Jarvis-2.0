#!/usr/bin/env python3
"""
JARVIS 2.0 - Main Entry Point

Start JARVIS with: jarvis
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.launcher import main as launcher_main

if __name__ == "__main__":
    raise SystemExit(launcher_main(sys.argv[1:]))
