"""Main entry point for JARVIS 2.0 CLI."""

import asyncio
import sys

from .repl import main
from .setup_wizard import needs_setup, run_setup_wizard

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
