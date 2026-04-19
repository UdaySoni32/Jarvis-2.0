"""Unified command launcher for JARVIS CLI workflows."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUICK_SETUP_SCRIPT = PROJECT_ROOT / "quick_setup.sh"


def _run_quick_setup(with_tests: bool = False) -> int:
    """Run project bootstrap script."""
    if not QUICK_SETUP_SCRIPT.exists():
        print(f"❌ quick_setup.sh not found at {QUICK_SETUP_SCRIPT}")
        return 1

    command = ["bash", str(QUICK_SETUP_SCRIPT)]
    if with_tests:
        command.append("--with-tests")

    result = subprocess.run(command, cwd=str(PROJECT_ROOT))
    return result.returncode


def _run_setup_wizard(required_only: bool = False) -> bool:
    """Run interactive setup wizard."""
    from .setup_wizard import needs_setup, run_setup_wizard

    if required_only and not needs_setup():
        return True

    if required_only:
        print("🤖 First-time setup required...\n")
    else:
        print("🛠️  Running JARVIS configuration wizard...\n")

    setup_success = asyncio.run(run_setup_wizard())
    if not setup_success:
        print("\n❌ Setup incomplete. Please run again to configure JARVIS.")
        return False

    print()
    return True


def _run_repl() -> int:
    """Start TUI REPL, running setup wizard only when needed."""
    from .repl import main as repl_main

    if not _run_setup_wizard(required_only=True):
        return 1

    asyncio.run(repl_main())
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create command parser for jarvis command."""
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS 2.0 TUI launcher and setup command",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="start JARVIS TUI (default)",
    )
    run_parser.set_defaults(command="run")

    setup_parser = subparsers.add_parser(
        "setup",
        help="bootstrap dependencies, configure, and launch TUI",
    )
    setup_parser.add_argument(
        "--with-tests",
        action="store_true",
        help="run quick verification during bootstrap",
    )
    setup_parser.add_argument(
        "--skip-configure",
        action="store_true",
        help="skip setup wizard after bootstrap",
    )
    setup_parser.add_argument(
        "--no-start",
        action="store_true",
        help="complete setup/configure without launching TUI",
    )

    subparsers.add_parser(
        "configure",
        help="run setup wizard only",
    )
    subparsers.add_parser(
        "config",
        help="alias for configure",
    )

    parser.set_defaults(command="run")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for unified jarvis command."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.command == "run":
            return _run_repl()

        if args.command in {"configure", "config"}:
            return 0 if _run_setup_wizard(required_only=False) else 1

        if args.command == "setup":
            code = _run_quick_setup(with_tests=bool(args.with_tests))
            if code != 0:
                return code

            if not args.skip_configure:
                if not _run_setup_wizard(required_only=False):
                    return 1

            if args.no_start:
                return 0

            return _run_repl()

        parser.print_help()
        return 1

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as error:
        print(f"\n❌ Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
