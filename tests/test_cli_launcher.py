"""Tests for unified jarvis launcher command flow."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cli import launcher


def test_build_parser_defaults_to_run():
    parser = launcher.build_parser()
    args = parser.parse_args([])
    assert args.command == "run"


def test_build_parser_supports_config_alias():
    parser = launcher.build_parser()
    args = parser.parse_args(["config"])
    assert args.command == "config"


def test_main_setup_runs_bootstrap_config_and_repl(monkeypatch):
    calls = []

    monkeypatch.setattr(
        launcher,
        "_run_quick_setup",
        lambda with_tests=False: calls.append(("quick_setup", with_tests)) or 0,
    )
    monkeypatch.setattr(
        launcher,
        "_run_setup_wizard",
        lambda required_only=False: calls.append(("wizard", required_only)) or True,
    )
    monkeypatch.setattr(
        launcher,
        "_run_repl",
        lambda: calls.append(("repl", None)) or 0,
    )

    result = launcher.main(["setup"])
    assert result == 0
    assert calls == [("quick_setup", False), ("wizard", False), ("repl", None)]


def test_main_setup_with_no_start_skips_repl(monkeypatch):
    calls = []

    monkeypatch.setattr(
        launcher,
        "_run_quick_setup",
        lambda with_tests=False: calls.append(("quick_setup", with_tests)) or 0,
    )
    monkeypatch.setattr(
        launcher,
        "_run_setup_wizard",
        lambda required_only=False: calls.append(("wizard", required_only)) or True,
    )
    monkeypatch.setattr(
        launcher,
        "_run_repl",
        lambda: calls.append(("repl", None)) or 0,
    )

    result = launcher.main(["setup", "--no-start"])
    assert result == 0
    assert calls == [("quick_setup", False), ("wizard", False)]


def test_main_run_invokes_repl(monkeypatch):
    monkeypatch.setattr(launcher, "_run_repl", lambda: 0)
    result = launcher.main(["run"])
    assert result == 0
