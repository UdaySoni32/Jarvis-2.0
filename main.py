#!/usr/bin/env python3
"""
JARVIS 2.0 - Main Entry Point

Start JARVIS with: python main.py
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.repl import main
from src.cli.setup_wizard import needs_setup, run_setup_wizard

if __name__ == "__main__":
    try:
        # Check if setup is needed
        if needs_setup():
            print("🤖 First-time setup required...\n")
            setup_success = asyncio.run(run_setup_wizard())
            if not setup_success:
                print("\n❌ Setup incomplete. Please run again to configure JARVIS.")
                sys.exit(1)
            print("\n")
        
        # Run main CLI
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
